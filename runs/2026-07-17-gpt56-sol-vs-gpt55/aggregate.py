#!/usr/bin/env python3
"""汇总 raw/ 原始 Judge 输出 → gate/dimensions/gsb/audience 结构化结果。

双轨：
- 主轨 track=channel（gate2/dim2/gsb2-*）：channel-level 参照（本批为同频道自选选题生成，黄金集 query 错配）
- 附录 track=goldenset（gate/dim/gsb1|2_*）：黄金集 query 参照，保留供审计

合并规则（docs/models.md）：
- L2/L3 维度分 = gemini 与 doubao 同维度分的均值（交叉验证）；其余层只有 gemini；
- 音频类只采信 gemini；
- GSB 换位复评：两次方向一致 → 采纳；反转 → S + swap_consistent=false + needs_human。
"""
import json
import re
import sys
from pathlib import Path
from statistics import mean

RUN = Path(__file__).parent
RAW = RUN / "raw"
CASES = [f"case-00{i}" for i in range(1, 7)]
TOPIC2CASE = json.load(open(RUN / "config.json"))["topic_case_map"]
CASE2TOPIC = {v: k for k, v in TOPIC2CASE.items()}
LAYERS = ["L1_task", "L2_visual", "L3_temporal", "L4_audio", "L5_narrative", "L6_commercial"]


def parse_json_block(text):
    blocks = re.findall(r"```json\s*(.*?)```", text, re.S)
    for b in reversed(blocks):
        for candidate in (b, b[: b.rfind("}") + 1]):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return None


def load(key):
    f = RAW / f"{key}.md"
    if not f.exists():
        return None
    return parse_json_block(f.read_text())


def norm_layer(l):
    if not l:
        return None
    for L in LAYERS:
        if str(l).startswith(L[:2]):
            return L
    return None


videos = [(cid, v) for cid in CASES for v in ("a", "b")]
FLIP = {"G": "B", "B": "G", "S": "S"}


def collect(track):
    gate_sfx = "gate" if track == "goldenset" else "gate2"
    dim_sfx = {"strict": "dim3", "channel": "dim2", "goldenset": "dim"}[track]
    dimvis_sfx = "dimvis2" if track == "strict" else "dimvis"
    gsb_glob = {"strict": ".gsb3-{run}_", "channel": ".gsb2-{run}_", "goldenset": ".gsb{run}_"}[track]

    gate_out = {f"{cid}-{v}": load(f"{cid}-{v}.{gate_sfx}") or {"error": "missing/unparsed"}
                for cid, v in videos}

    dims_out = {}
    for cid, v in videos:
        d = load(f"{cid}-{v}.{dim_sfx}")
        dv = load(f"{cid}-{v}.{dimvis_sfx}")
        entry = {"case_id": cid, "video": v, "topic": CASE2TOPIC[cid],
                 "gemini": d, "doubao_visual": dv if track == "channel" else "见主轨",
                 "layer_scores": {}, "merged_dims": []}
        gem_scores = (d or {}).get("scores", [])
        dv_scores = {(norm_layer(s.get("layer")), s.get("dimension")): s
                     for s in (dv or {}).get("scores", []) if s.get("score") is not None}
        by_layer = {L: [] for L in LAYERS}
        for s in gem_scores:
            L = norm_layer(s.get("layer"))
            if not L or s.get("skipped_no_reference") or s.get("score") is None:
                continue
            sc = float(s["score"])
            src = "gemini"
            cross = dv_scores.get((L, s.get("dimension")))
            if cross and L in ("L2_visual", "L3_temporal"):
                sc = (sc + float(cross["score"])) / 2
                src = "gemini+doubao"
            by_layer[L].append(sc)
            entry["merged_dims"].append({"layer": L, "dimension": s.get("dimension"), "score": round(sc, 2),
                                         "source": src, "fatal_flag": s.get("fatal_flag", False),
                                         "needs_human": s.get("needs_human", False)})
        for (L, dim), s in dv_scores.items():
            if L in ("L2_visual", "L3_temporal") and not any(
                    m["layer"] == L and m["dimension"] == dim for m in entry["merged_dims"]):
                by_layer[L].append(float(s["score"]))
                entry["merged_dims"].append({"layer": L, "dimension": dim, "score": float(s["score"]),
                                             "source": "doubao_only", "needs_human": True})
        entry["layer_scores"] = {L: round(mean(xs), 2) if xs else None for L, xs in by_layer.items()}
        dims_out[f"{cid}-{v}"] = entry

    gsb_out = {}
    for cid in CASES:
        runs = []
        for run_no in (1, 2):
            pat = f"{cid}{gsb_glob.format(run=run_no)}"
            hits = sorted(RAW.glob(pat.replace(".", "?", 0) + "*.md")) if False else \
                   sorted(p for p in RAW.glob(f"{cid}.*.md") if p.name.startswith(pat))
            for f in hits:
                m = re.search(r"_(\w)(\w)$", f.stem)
                j = parse_json_block(f.read_text())
                if j and m:
                    runs.append({"run": run_no, "A": m.group(1), "B": m.group(2), "file": f.name, "result": j})
        entry = {"case_id": cid, "topic": CASE2TOPIC[cid], "runs": runs}
        verdicts = [(r["result"]["gsb"] if r["A"] == "a" else FLIP[r["result"]["gsb"]])
                    for r in runs if r["result"].get("gsb")]
        if len(verdicts) >= 2:
            if verdicts[0] == verdicts[1]:
                entry.update(final_a_vs_b=verdicts[0], swap_consistent=True,
                             needs_human=any(r["result"].get("needs_human") for r in runs))
            else:
                entry.update(final_a_vs_b="S", swap_consistent=False, needs_human=True,
                             note=f"换位反转 {verdicts} → 降级 S")
        else:
            entry.update(final_a_vs_b=verdicts[0] if verdicts else None, swap_consistent=None, needs_human=True)
        gsb_out[cid] = entry
    return gate_out, dims_out, gsb_out


results = {}
for track in ("strict", "channel", "goldenset"):
    gate_out, dims_out, gsb_out = collect(track)
    results[track] = {"gate": gate_out, "dims": dims_out, "gsb": gsb_out}
    sub = {"strict": "", "channel": "_round1_annex", "goldenset": "_goldenset_annex"}[track]
    (RUN / "gate").mkdir(exist_ok=True)
    (RUN / "dimensions").mkdir(exist_ok=True)
    (RUN / "gsb").mkdir(exist_ok=True)
    (RUN / f"gate/gate_results{sub}.json").write_text(json.dumps(gate_out, ensure_ascii=False, indent=1))
    (RUN / f"dimensions/scores{sub}.json").write_text(json.dumps(dims_out, ensure_ascii=False, indent=1))
    (RUN / f"gsb/gsb_results{sub}.json").write_text(json.dumps(gsb_out, ensure_ascii=False, indent=1))

aud_out = {f"{cid}-{v}": [load(f"{cid}-{v}.aud{i}") for i in (1, 2)] for cid, v in videos}
(RUN / "audience").mkdir(exist_ok=True)
(RUN / "audience/audience.json").write_text(json.dumps(aud_out, ensure_ascii=False, indent=1))

for track in ("strict", "channel", "goldenset"):
    gate_out, dims_out, gsb_out = (results[track][k] for k in ("gate", "dims", "gsb"))
    print(f"\n######## track = {track} ########")
    print("=== Gate ===")
    for k, g in gate_out.items():
        print(f"{k}: {g.get('overall', '?')}  needs_human={g.get('needs_human')}")
    print("=== 六层分 (merged) ===")
    for k, e in dims_out.items():
        print(k, e["layer_scores"], "tier:", (e.get("gemini") or {}).get("tier"))
    print("=== GSB (a vs b) ===")
    finals = []
    for cid, e in gsb_out.items():
        conf = [r["result"].get("confidence") for r in e["runs"]]
        print(f"{cid} {e['topic'][:14]}: {e.get('final_a_vs_b')} swap_consistent={e.get('swap_consistent')} conf={conf} {e.get('note','')}")
        if e.get("final_a_vs_b"):
            finals.append(e["final_a_vs_b"])
    n = len(finals)
    if n:
        G, S, B = (finals.count(x) for x in "GSB")
        dwr = f"{G/(G+B):.0%}" if G + B else "N/A(全S)"
        print(f"G/S/B = {G}/{S}/{B}  NetLift={(G-B)/n:+.0%}  DecisiveWinRate={dwr}")
