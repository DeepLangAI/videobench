#!/usr/bin/env python3
"""VideoBench 评估驱动：gpt5.6-sol vs gpt5.5 盲评（6 题 × a/b）。

阶段（--phase）:
  router   : 12 条 genre_router
  judge    : 12 条 × (gate + dimension(gemini) + dimension_visual(doubao) + audience×2)
  gsb      : 6 对 × 2 位置（随机首序 + 换位复评）
  all      : 依次全部

原始输出落盘 raw/<case>-<v>.<stage>.md（存在且非空即跳过 = 断点续跑）。
"""
import argparse
import base64
import concurrent.futures as cf
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

RUN = Path(__file__).parent
REPO = RUN.parent.parent
RAW = RUN / "raw"
RAW.mkdir(exist_ok=True)

CFG = json.load(open(Path.home() / ".claude/skills/video-triage/scripts/config.json"))
GEMINI = CFG["model"]
DOUBAO = CFG["visual_model"]

SRC = Path("/Users/admin/Downloads/gpt5.6-sol vs gpt5.5")
TOPIC2CASE = {
    "电池热失控·热量传播图解": "case-001",
    "商业结构一个概念怎么被卖爆": "case-002",
    "隐私条款拆解·你到底同意了什么": "case-003",
    "城市里的野生动物·它们怎么活下来的": "case-004",
    "如果历史拐了个弯·反事实推演": "case-005",
    "深海恐惧图解·尺度失控的瞬间": "case-006",
}
CASES = {cid: json.load(open(REPO / f"goldenset/cases/{cid}.json")) for cid in TOPIC2CASE.values()}
OBJECTIVE = {(r["topic"], r["video"]): r for r in json.load(open(RUN / "objective/summary.json"))}

# ---------- prompt 装配 ----------

def _cut(text, start, end=None):
    i = text.index(start) + len(start)
    return text[i: text.index(end, i)] if end else text[i:]

dims_md = (REPO / "docs/dimensions.md").read_text()
DIMS_TABLE = dims_md[dims_md.index("## L1"): dims_md.index("## 范围外")].strip()

router_md = (REPO / "prompts/genre_router.md").read_text()
ROUTER_PROMPT = _cut(router_md, "\n---\n", "\n---\n").strip()

gate_md = (REPO / "prompts/gate_judge.md").read_text()
GATE_TMPL = _cut(gate_md, "\n---\n").strip()

dim_md = (REPO / "prompts/dimension_judge_content_channel.md").read_text()
DIM_TMPL = _cut(dim_md, "\n---\n").strip()

aud_md = (REPO / "prompts/audience_judge.md").read_text()
AUD_TMPL = _cut(aud_md, "\n---\n").strip()

gsb_md = (REPO / "prompts/gsb_judge.md").read_text()
GSB_TMPL = _cut(gsb_md, "\n---\n").strip()

GATE_JSON_SPEC = """

## 输出格式

先写逐条分析，最后输出一个 ```json 代码块，符合 gate_result 语义：
{"rules": [{"rule": 1, "name": "产品或品牌错误", "verdict": "pass|fail|borderline", "evidence": "时间戳+描述+引文，pass 可空"}, ... 共8条],
 "overall": "pass|fail|borderline", "needs_human": true/false, "needs_human_reasons": ["..."]}"""

DIM_JSON_SPEC = """

## 机器可读输出（必须）

正文分析之后，最后输出一个 ```json 代码块，符合 dimension_scores 语义：
{"scores": [{"layer": "L1_task", "dimension": "指令遵循", "method": "judge", "score": 1-5,
   "evidence": [{"timestamp_sec": 12.0, "description": "...", "quote": "OCR/ASR原文(可选)"}],
   "fatal_flag": false, "needs_human": false}, ...每个维度一条，skipped 的维度用 {"layer":..., "dimension":..., "skipped_no_reference": true}],
 "one_line_diagnosis": "…", "intuition_score": 3.5, "tier": "顶级|优秀|及格|差",
 "needs_human_items": [{"reason": "...", "key_fact": "...", "video_quote": "..."}]}"""

AUD_JSON_SPEC = """

最后输出一个 ```json 代码块：
{"first_3s": "继续看|划走", "first_3s_why": "...", "dropout_sec": 数字或null, "dropout_why": "...",
 "recall": "...", "highlight": "...", "boring": "...",
 "actions": {"like": true/false, "comment": true/false, "share": true/false, "follow": true/false, "favorite": true/false},
 "quote": "原话评价", "completion_tier": "高|中|低"}"""

GSB_JSON_SPEC = """

## 机器可读输出（必须）

先报告两条视频各自的大致时长（用于确认你看到了两条不同的视频），再写逐层分析，最后输出一个 ```json 代码块：
{"duration_check": {"A_sec": 数字, "B_sec": 数字},
 "gate_shortcut": {"applied": true/false, "fatal_side": "A|B|both|none"},
 "dimension_comparison": {"task_alignment": {"verdict": "win|tie|loss", "evidence": "..."},
   "visual": {...}, "temporal": {...}, "audio": {...}, "narrative": {...}, "commercial": {...}},
 "gsb": "G|S|B", "probabilities": {"G": 0.x, "S": 0.x, "B": 0.x},
 "rationale": "...", "confidence": "high|medium|low", "needs_human": true/false}
（verdict 与 G/S/B 均以 A 相对 B 为方向：win/G = A 更好）"""


def task_context_json(cid):
    return json.dumps(CASES[cid], ensure_ascii=False, indent=1)


# 视频选题与黄金集 query 是否对应（2026-07-17 实测：本批为"同频道自选选题"生成，
# 002-005 的 a/b 各自选了与题库 query 无关、彼此也不同的案例；001/006 与频道核心主题一致）
TOPIC_MATCHES_GOLDENSET = {"case-001": True, "case-002": False, "case-003": False,
                           "case-004": False, "case-005": False, "case-006": True}

GENERIC_AUDIENCE = {
    "case-002": "对商业逻辑与品牌营销拆解感兴趣的普通中文观众（非从业者），期待『商业逻辑+轻科普』深度，且要求全片清晰区分【可核实的商业史实/数据】与【品牌宣称】",
    "case-003": "关注个人数据与隐私的普通中文 App 用户，期待把条款翻译成人话、说清『同意』背后到底授权了什么",
    "case-004": "对城市生态与野生动物好奇的中文大众，尤其城市居民；初高中科普深度，期待真实案例+生态学解释",
    "case-005": "对科技史与经济学『路径依赖』话题感兴趣的泛知识类观众（非专业极客），要求清晰区分已证实史实、流行误区与假设推演",
}

# 频道通用覆盖要求（逐字取自 channel.description 的格式条款，不含任何特定选题主体）
GENERIC_MUST_COVER = {
    "case-002": [
        {"point": "拆解一个消费品牌如何把一个抽象概念（时间段/情绪/场景）包装成可持续售卖的产品线", "source": "channelDescription", "must_appear": True},
        {"point": "复盘从概念提出到全线产品矩阵的扩张", "source": "channelDescription", "must_appear": True},
        {"point": "拆解支撑售卖的营销叙事与商业逻辑", "source": "channelDescription", "must_appear": True},
        {"point": "用真实品牌案例复盘（品牌与史实真实）", "source": "channelDescription", "must_appear": True},
    ],
    "case-003": [
        {"point": "挑一款大众常用 App 的隐私政策/用户协议改动作为对象", "source": "channelDescription", "must_appear": True},
        {"point": "逐条把条款翻译成人话", "source": "channelDescription", "must_appear": True},
        {"point": "对比修改前后的条款差异", "source": "channelDescription", "must_appear": True},
        {"point": "说清用户勾选『同意』时到底授权了什么、数据会被怎么用", "source": "channelDescription", "must_appear": True},
    ],
    "case-004": [
        {"point": "讲一种成功适应大城市环境的野生动物", "source": "channelDescription", "must_appear": True},
        {"point": "结合真实案例和生态学解释", "source": "channelDescription", "must_appear": True},
        {"point": "讲清它们的食物、路线、繁殖如何在钢筋水泥里找到生存缝隙", "source": "channelDescription", "must_appear": True},
    ],
    "case-005": [
        {"point": "交代一个真实的技术/标准之争历史岔路口（史实准确）", "source": "channelDescription", "must_appear": True},
        {"point": "假设当年输的那一方赢了，展开反事实推演", "source": "channelDescription", "must_appear": True},
        {"point": "推演今天的日常生活、工作方式、产业格局会有什么不同", "source": "channelDescription", "must_appear": True},
        {"point": "用真实技术史细节支撑推演", "source": "channelDescription", "must_appear": True},
        {"point": "明确区分史实与假设推演（叙事诚实性）", "source": "topic", "must_appear": True},
    ],
}


def task_context_json_channel(cid):
    """channel-level 降级参照：去掉题库 query；must_cover 只留 source=channelDescription；
    选题与频道核心主题不符的 case 连 key_facts/research_notes 一并去掉（属另一期选题的事实表）。"""
    c = CASES[cid]
    ctx = {
        "case_id": cid + "-channel-ref",
        "mode": "with_reference_channel_level",
        "profile": c["profile"],
        "channel": c["channel"],
        "query": None,
        "reference_note": (
            "本批成片为『给定频道、自选本期选题』生成：具体选题(query)不在参照内，视频选题以其自身内容为准，"
            "不得因『选题不是某个特定题目』而判跑题。评估锚点：1) 频道 description 的格式与内容要求"
            "（下方 must_cover 均源自频道描述，可正常硬判）；2) 视频自设选题是否讲对、讲清、讲诚实、讲完整。"
            + ("本 case 附带的 key_facts/research_notes 与该频道核心主题一致，照常使用（未经人工核验，冲突记 needs_human 不 fatal）。"
               if TOPIC_MATCHES_GOLDENSET[cid] else
               "本 case 无事实表参照：成片中的可核验断言无法比对，只能检查内部自洽与常识性硬伤，事实类疑点一律 needs_human，不得硬判 fatal。")
        ),
        "must_cover": (
            # 选题匹配的 case：channelDescription 项本就通用，直接用
            [m for m in c["must_cover"] if m.get("source") == "channelDescription"]
            if TOPIC_MATCHES_GOLDENSET[cid] else
            # 选题不匹配的 case：黄金集 must_cover 文本内嵌了另一期选题主体（雅诗兰黛/Dvorak 等），
            # 会与"选题自选"注释自相矛盾 → 用频道 description 的通用格式要求替代
            GENERIC_MUST_COVER[cid]
        ),
        # 黄金集 target_audience 内嵌了另一期选题的具体内容（三星用户/郊狼定义/Dvorak 专利层次等）
        # → 选题不匹配的 case 用频道级通用受众，避免再次诱导"跑题"误判
        "target_audience": (c.get("target_audience") if TOPIC_MATCHES_GOLDENSET[cid]
                            else GENERIC_AUDIENCE[cid]),
        "platform_requirements": c.get("platform_requirements"),
    }
    if TOPIC_MATCHES_GOLDENSET[cid]:
        ctx["key_facts"] = c["key_facts"]
        ctx["research_notes"] = c.get("research_notes")
    return json.dumps(ctx, ensure_ascii=False, indent=1)


def evidence_json(topic, v):
    o = OBJECTIVE[(topic, v)]
    return json.dumps({
        "native_video_input": True,
        "note": "视频已原生输入本次请求，请完整观看（含音频）后作答；以下为客观检查轨结果，与你的观察冲突时以客观轨为准",
        "objective_metrics": {k: o[k] for k in ("playable", "duration_sec", "resolution", "aspect_ratio", "fps", "bitrate_kbps", "has_audio_track", "audio_codec", "integrated_lufs")},
    }, ensure_ascii=False, indent=1)

# ---------- 网关调用 ----------

def b64uri(path):
    return "data:video/mp4;base64," + base64.b64encode(Path(path).read_bytes()).decode()


def video_part(model, uri, fps=0.5):
    if "gemini" in model:
        return {"type": "image_url", "image_url": {"url": uri}}
    return {"type": "video_url", "video_url": {"url": uri, "fps": fps}}


def call(model, content, max_tokens=6000, retries=2, timeout=900):
    payload = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens}
    req_data = json.dumps(payload).encode()
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            CFG["base_url"].rstrip("/") + "/v1/chat/completions", data=req_data,
            headers={"Authorization": "Bearer " + CFG["api_key"], "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.load(r)
            if "choices" in resp:
                txt = resp["choices"][0]["message"]["content"]
                if txt and txt.strip():
                    return txt
            last = json.dumps(resp, ensure_ascii=False)[:2000]
        except Exception as e:
            body = ""
            if hasattr(e, "read"):
                try:
                    body = e.read().decode(errors="replace")[:1500]
                except Exception:
                    pass
            last = f"{type(e).__name__}: {e} {body}"
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(last or "empty response")


def run_stage(key, model, content, max_tokens=6000):
    """key: e.g. case-001-a.router；落盘 raw/<key>.md"""
    out = RAW / f"{key}.md"
    if out.exists() and out.stat().st_size > 50:
        return f"[skip] {key}"
    t0 = time.time()
    try:
        txt = call(model, content, max_tokens)
        out.write_text(txt)
        return f"[ok] {key} {time.time()-t0:.0f}s {len(txt)}ch"
    except Exception as e:
        (RAW / f"{key}.err").write_text(str(e))
        return f"[ERR] {key}: {str(e)[:200]}"


def parse_json_block(text):
    import re
    blocks = re.findall(r"```json\s*(.*?)```", text, re.S)
    for b in reversed(blocks):
        try:
            return json.loads(b)
        except json.JSONDecodeError:
            continue
    # 宽松兜底：找最后一个 { 开头的平衡块
    return None


def router_result(cid, v):
    f = RAW / f"{cid}-{v}.router.md"
    if not f.exists():
        return None
    return parse_json_block(f.read_text())

# ---------- 阶段任务 ----------

VIDEOS = [(topic, cid, v) for topic, cid in TOPIC2CASE.items() for v in ("a", "b")]


def jobs_router():
    for topic, cid, v in VIDEOS:
        uri = b64uri(SRC / topic / f"{v}.mp4")
        yield (f"{cid}-{v}.router", GEMINI,
               [video_part(GEMINI, uri), {"type": "text", "text": ROUTER_PROMPT}], 2000)


def jobs_judge():
    for topic, cid, v in VIDEOS:
        uri = b64uri(SRC / topic / f"{v}.mp4")
        tc, ev = task_context_json(cid), evidence_json(topic, v)
        rt = router_result(cid, v) or {}
        rt_json = json.dumps(rt, ensure_ascii=False, indent=1)

        gate = GATE_TMPL.replace("{{task_context_json}}", tc).replace("{{evidence_json}}", ev) + GATE_JSON_SPEC
        yield (f"{cid}-{v}.gate", GEMINI, [video_part(GEMINI, uri), {"type": "text", "text": gate}], 5000)

        dim = (DIM_TMPL.replace("{{task_context_json}}", tc).replace("{{evidence_json}}", ev)
               .replace("{{docs/dimensions.md 中 L1–L6 的维度表}}", DIMS_TABLE)
               .replace("{{genre_router_json}}", rt_json) + DIM_JSON_SPEC)
        yield (f"{cid}-{v}.dim", GEMINI, [video_part(GEMINI, uri), {"type": "text", "text": dim}], 10000)

        dimvis = ("你是版式与动效方向的资深审片总监（专业诊断通道，交叉验证员）。你只能看到抽帧画面、听不到音频："
                  "**只评 L2 视觉层与 L3 时序层**，严禁对配音、音乐、音画同步做任何猜测。\n\n<task_context>\n" + tc +
                  "\n</task_context>\n\n<dimension_definitions>\n" + DIMS_TABLE +
                  "\n</dimension_definitions>\n\n这是知识解说频道的视频。按 L2（清晰度/美学/主体质量/文字质量）与 L3（人物一致性/物体恒常性/运动自然/无闪烁）逐维打分 1-5，"
                  "每个分数至少一条带时间戳的证据；图表可读性、错别字、语义断行、模板化版式、PPT式动效都要挑；"
                  "评判锚定'在同类知识频道商业作品中处于什么档位'。最后输出 ```json 代码块："
                  '{"scores": [{"layer": "L2_visual", "dimension": "清晰度", "score": 4, "evidence": [{"timestamp_sec": 3, "description": "..."}]}, ...], "one_line_diagnosis": "...", "tier": "顶级|优秀|及格|差"}')
        yield (f"{cid}-{v}.dimvis", DOUBAO, [video_part(DOUBAO, uri, fps=0.5), {"type": "text", "text": dimvis}], 8000)

        personas = [
            (rt.get("target_audience") or CASES[cid].get("target_audience") or "对该主题好奇但非专业的普通观众",
             rt.get("viewing_context") or "在B站/知识区信息流里闲逛，想看点有意思又有收获的东西"),
            ("刷到什么看什么的泛路人观众，对这个主题没有特别兴趣", "睡前刷短视频/信息流打发时间"),
        ]
        for i, (persona, ctx) in enumerate(personas, 1):
            aud = AUD_TMPL.replace("{{persona}}", persona).replace("{{viewing_context}}", ctx) + AUD_JSON_SPEC
            yield (f"{cid}-{v}.aud{i}", GEMINI, [video_part(GEMINI, uri), {"type": "text", "text": aud}], 3000)


def jobs_judge2():
    """channel-reference 修正轨：只重跑 gate 与 dim（router/dimvis/audience 不依赖错配参照，复用）"""
    for topic, cid, v in VIDEOS:
        uri = b64uri(SRC / topic / f"{v}.mp4")
        tc, ev = task_context_json_channel(cid), evidence_json(topic, v)
        rt = router_result(cid, v) or {}
        rt_json = json.dumps(rt, ensure_ascii=False, indent=1)

        gate = GATE_TMPL.replace("{{task_context_json}}", tc).replace("{{evidence_json}}", ev) + GATE_JSON_SPEC
        yield (f"{cid}-{v}.gate2", GEMINI, [video_part(GEMINI, uri), {"type": "text", "text": gate}], 5000)

        dim = (DIM_TMPL.replace("{{task_context_json}}", tc).replace("{{evidence_json}}", ev)
               .replace("{{docs/dimensions.md 中 L1–L6 的维度表}}", DIMS_TABLE)
               .replace("{{genre_router_json}}", rt_json) + DIM_JSON_SPEC)
        yield (f"{cid}-{v}.dim2", GEMINI, [video_part(GEMINI, uri), {"type": "text", "text": dim}], 16000)


def jobs_gsb2():
    """channel-reference 修正轨 GSB：同频道两条候选成片（选题可不同）比较"""
    positions = json.load(open(RUN / "gsb" / "positions.json"))
    for topic, cid in TOPIC2CASE.items():
        first, second = positions[cid]
        for run_no, (x, y) in enumerate(((first, second), (second, first)), 1):
            tc = task_context_json_channel(cid)
            prompt = (GSB_TMPL.replace("{{task_context_json}}", tc)
                      .replace("{{evidence_A_json}}", evidence_json(topic, x))
                      .replace("{{evidence_B_json}}", evidence_json(topic, y)) + GSB_JSON_SPEC)
            prompt = ("本次请求原生输入两条视频：**第一条是视频A，第二条是视频B**。两条都是同一知识频道下的候选成片，"
                      "本期选题由生成方自选，两条选题可能不同——这不构成缺陷，不得因『选题不同/不是某特定题目』判负。"
                      "比较的是：哪条更符合频道 description 的格式与质量要求、把各自的选题讲得更对/更清/更诚实、对该频道目标观众更有价值。\n\n"
                      + prompt)
            content = [video_part(GEMINI, b64uri(SRC / topic / f"{x}.mp4")),
                       video_part(GEMINI, b64uri(SRC / topic / f"{y}.mp4")),
                       {"type": "text", "text": prompt}]
            yield (f"{cid}.gsb2-{run_no}_{x}{y}", GEMINI, content, 8000)


LEDGER = json.load(open(RUN / "objective/frame_review_ledger.json"))

CALIBRATION = """
## 档位校准（本轮最重要，必须执行）

**人类标注人已确认首轮评分系统性虚高**，本轮按以下锚点重评：

- **5 分锚点**：人类标注确认的顶级商业作品水准（如顶级 motion-design showcase：镜头化叙事、丰富动效设计、层级分明、无模板感、可直接对外发布代表品牌）。5 分 = 行业顶级样板，本批预计极少或没有。
- **先验**：幻灯片式 AI 生成知识片的 L2 美学 / L5 叙事多数应落在 **2.5–3.5**；"版式干净不出错"只是 3 分水平，**不是** 4 分。4 分以上必须给出"哪里接近顶级"的具体证据；给 4.5+ 需要能通过"放进顶级作品集不违和"的检验。
- **AI 味 / PPT 味是本档明确扣分项**（人类标注人要求），作为证据计入现有维度（L2 美学/文字质量、L5 节奏/信息层级，不新设维度行）：
  - **PPT 味**：单屏静置 >8s、仅淡入/平移的翻页式转场、满屏卡片与 chip 标签堆砌、无镜头语言/无视觉引导；
  - **AI 味**：千篇一律的模板配色（深底+高饱和点缀色+圆角 chip）、装饰图标堆砌、空洞罗列式文案、同一素材反复复用、低对比小字。
- **密度锚定强制执行**：每一层先列出"确认问题清单"（含时间戳，PPT味/AI味证据算"明显问题"），再按密度定分：致命≥1 或明显≥5 → ≤2；明显 3–4 条 → 3；明显 ≤2 条 → 4；基本无问题且有顶级证据 → 5。**先数问题，后给分，不允许先有分再找理由。**

## 已确认问题台账（密集抽帧人工复核，客观优先）

以下是对本条视频逐帧复核后**已确认**的问题与优点，你必须将其纳入证据与计数；你的观察与台账冲突时以台账为准；你可以补充台账没有的新发现（需带时间戳）：

{{ledger_json}}
"""


def jobs_judge3():
    """严格口径重评：dim3(gemini 全维度) + dimvis2(doubao fps=1 视觉bug猎手)"""
    for topic, cid, v in VIDEOS:
        uri = b64uri(SRC / topic / f"{v}.mp4")
        tc, ev = task_context_json_channel(cid), evidence_json(topic, v)
        rt = router_result(cid, v) or {}
        rt_json = json.dumps(rt, ensure_ascii=False, indent=1)
        ledger = json.dumps(LEDGER[f"{cid}-{v}"], ensure_ascii=False, indent=1)
        calib = CALIBRATION.replace("{{ledger_json}}", ledger)

        dim = (DIM_TMPL.replace("{{task_context_json}}", tc).replace("{{evidence_json}}", ev)
               .replace("{{docs/dimensions.md 中 L1–L6 的维度表}}", DIMS_TABLE)
               .replace("{{genre_router_json}}", rt_json) + calib + DIM_JSON_SPEC)
        yield (f"{cid}-{v}.dim3", GEMINI, [video_part(GEMINI, uri), {"type": "text", "text": dim}], 16000)

        dimvis = ("你是版式与动效方向的资深审片总监兼视觉 QC（交叉验证员）。你只能看抽帧画面、听不到音频：只评 L2 视觉与 L3 时序，"
                  "严禁猜测音频。本轮是严格复核轮：人类标注人确认首轮评分虚高。\n" + calib +
                  "\n\n重点猎捕画面 bug：空面板、错位/悬浮元素、被裁切的孤立线条、残影/半透明未完成态、元素叠压、闪烁、跳变。"
                  "每屏停留时长也要报（>8s 静置计 PPT 味明显问题）。"
                  "评分按上面的密度锚定表执行。最后输出 ```json 代码块："
                  '{"scores": [{"layer": "L2_visual", "dimension": "清晰度|美学|主体质量|文字质量", "score": 1-5, "evidence": [{"timestamp_sec": 3, "description": "..."}]}, '
                  '{"layer": "L3_temporal", "dimension": "物体恒常性|运动自然|无闪烁", "score": 1-5, "evidence": [...]}], '
                  '"new_bugs": [{"timestamp_sec": 12, "description": "台账之外的新发现"}], "one_line_diagnosis": "...", "tier": "顶级|优秀|及格|差"}')
        yield (f"{cid}-{v}.dimvis2", DOUBAO, [video_part(DOUBAO, uri, fps=1.0), {"type": "text", "text": dimvis}], 8000)


def jobs_gsb3():
    """严格口径 GSB 复核：注入双方台账 + AI味/PPT味权重纪律，换位复评"""
    positions = json.load(open(RUN / "gsb" / "positions.json"))
    for topic, cid in TOPIC2CASE.items():
        first, second = positions[cid]
        for run_no, (x, y) in enumerate(((first, second), (second, first)), 1):
            tc = task_context_json_channel(cid)
            lx = json.dumps(LEDGER[f"{cid}-{x}"], ensure_ascii=False, indent=1)
            ly = json.dumps(LEDGER[f"{cid}-{y}"], ensure_ascii=False, indent=1)
            prompt = (GSB_TMPL.replace("{{task_context_json}}", tc)
                      .replace("{{evidence_A_json}}", evidence_json(topic, x) + "\n\n<confirmed_issues_A>（密集抽帧人工复核台账，客观优先）\n" + lx + "\n</confirmed_issues_A>")
                      .replace("{{evidence_B_json}}", evidence_json(topic, y) + "\n\n<confirmed_issues_B>（密集抽帧人工复核台账，客观优先）\n" + ly + "\n</confirmed_issues_B>"))
            prompt = ("本次请求原生输入两条视频：**第一条是视频A，第二条是视频B**。两条都是同一知识频道下的候选成片，选题由生成方自选、可以不同——选题不同本身不构成缺陷。\n"
                      "本轮为严格复核轮：**AI 味与 PPT 味计入用户价值比较**（单屏静置>8s、翻页式转场、模板卡片堆砌、素材复用、罗列式文案都是真实观众会划走的理由）；"
                      "已确认的画面 bug（见各自台账）必须计入。确认的台账证据 > 你的主观印象。\n\n"
                      + prompt + GSB_JSON_SPEC)
            content = [video_part(GEMINI, b64uri(SRC / topic / f"{x}.mp4")),
                       video_part(GEMINI, b64uri(SRC / topic / f"{y}.mp4")),
                       {"type": "text", "text": prompt}]
            yield (f"{cid}.gsb3-{run_no}_{x}{y}", GEMINI, content, 8000)


def jobs_gsb():
    rng = random.Random(20260717)
    order_file = RUN / "gsb" / "positions.json"
    order_file.parent.mkdir(exist_ok=True)
    if order_file.exists():
        positions = json.load(open(order_file))
    else:
        positions = {cid: rng.choice([["a", "b"], ["b", "a"]]) for cid in sorted(TOPIC2CASE.values())}
        order_file.write_text(json.dumps(positions, ensure_ascii=False, indent=1))
    for topic, cid in TOPIC2CASE.items():
        first, second = positions[cid]
        for run_no, (x, y) in enumerate(((first, second), (second, first)), 1):
            tc = task_context_json(cid)
            prompt = (GSB_TMPL.replace("{{task_context_json}}", tc)
                      .replace("{{evidence_A_json}}", evidence_json(topic, x))
                      .replace("{{evidence_B_json}}", evidence_json(topic, y)) + GSB_JSON_SPEC)
            prompt = ("本次请求原生输入两条视频：**第一条是视频A，第二条是视频B**。请各自完整观看（含音频）后，按下述协议评审。\n\n"
                      + prompt)
            content = [video_part(GEMINI, b64uri(SRC / topic / f"{x}.mp4")),
                       video_part(GEMINI, b64uri(SRC / topic / f"{y}.mp4")),
                       {"type": "text", "text": prompt}]
            yield (f"{cid}.gsb{run_no}_{x}{y}", GEMINI, content, 8000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["router", "judge", "gsb", "judge2", "gsb2", "judge3", "gsb3", "all"], default="all")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default=None, help="仅跑 key 含此子串的任务")
    args = ap.parse_args()

    gens = {"router": [jobs_router], "judge": [jobs_judge], "gsb": [jobs_gsb],
            "judge2": [jobs_judge2], "gsb2": [jobs_gsb2],
            "judge3": [jobs_judge3], "gsb3": [jobs_gsb3],
            "all": [jobs_router, jobs_judge, jobs_gsb]}[args.phase]
    for gen in gens:
        jobs = [j for j in gen() if not args.only or args.only in j[0]]
        pending = [j for j in jobs if not ((RAW / f"{j[0]}.md").exists() and (RAW / f"{j[0]}.md").stat().st_size > 50)]
        print(f"== phase {gen.__name__}: {len(jobs)} jobs, {len(pending)} to run", flush=True)
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            for r in ex.map(lambda j: run_stage(*j), jobs):
                print(r, flush=True)


if __name__ == "__main__":
    main()
