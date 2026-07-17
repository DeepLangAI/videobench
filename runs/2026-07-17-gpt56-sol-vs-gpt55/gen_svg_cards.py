#!/usr/bin/env python3
"""生成飞书画板可解析的 SVG 评分卡（每题一张 + 总览）。

约束（lark-doc-whiteboard）：只用 rect/circle/polygon/line/polyline/path/text/g，
无渐变/滤镜/clipPath/mask；文本用 <text>，CJK≈1em 宽度换行。
输出 svg/<cid>.svg 与 svg/overall.svg。
"""
import json
import math
from pathlib import Path

RUN = Path(__file__).parent
OUT = RUN / "svg"
OUT.mkdir(exist_ok=True)

INK, INK2, GRID = "#1f2329", "#646a73", "#d5d8dd"
C_A, C_B = "#2a78d6", "#c98500"
RED = "#c0392b"

dims = json.load(open(RUN / "dimensions/scores.json"))
gsb = json.load(open(RUN / "gsb/gsb_results.json"))
gate = json.load(open(RUN / "gate/gate_results.json"))
adj_path = RUN / "gsb/adjustments.json"
if adj_path.exists():
    for cid, a in json.load(open(adj_path)).items():
        if cid in gsb and "final_a_vs_b" in a:
            gsb[cid]["final_a_vs_b"] = a["final_a_vs_b"]
            gsb[cid]["needs_human"] = a.get("needs_human", gsb[cid].get("needs_human"))

LAYERS = ["L1_task", "L2_visual", "L3_temporal", "L4_audio", "L5_narrative", "L6_commercial"]
LABELS = ["L1 任务", "L2 视觉", "L3 时序", "L4 音频", "L5 叙事", "L6 商业"]
CASES = [f"case-00{i}" for i in range(1, 7)]
VERDICT = {"G": "a 优", "S": "无实质差异", "B": "b 优", None: "转人工复核"}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def vec(key):
    ls = dims[key]["layer_scores"]
    return [ls.get(L) or 0 for L in LAYERS]


def avg(v):
    xs = [x for x in v if x]
    return sum(xs) / len(xs) if xs else 0


def radar_svg(cx, cy, R, va, vb):
    """返回雷达图元素列表。轴 0 在正上方，顺时针。"""
    el = []
    def pt(i, r):
        ang = -math.pi / 2 + i * math.pi / 3
        return (cx + R * r / 5 * math.cos(ang), cy + R * r / 5 * math.sin(ang))
    for r in (1, 2, 3, 4, 5):
        pts = " ".join(f"{pt(i, r)[0]:.1f},{pt(i, r)[1]:.1f}" for i in range(6))
        el.append(f'<polygon points="{pts}" fill="none" stroke="{GRID}" stroke-width="1"/>')
    for i in range(6):
        x2, y2 = pt(i, 5)
        el.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GRID}" stroke-width="1"/>')
    for v, c, op in ((vb, C_B, 0.18), (va, C_A, 0.18)):
        pts = " ".join(f"{pt(i, v[i])[0]:.1f},{pt(i, v[i])[1]:.1f}" for i in range(6))
        el.append(f'<polygon points="{pts}" fill="{c}" fill-opacity="{op}" stroke="{c}" stroke-width="2.5"/>')
        for i in range(6):
            x, y = pt(i, v[i])
            el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c}"/>')
    # 轴标签
    for i in range(6):
        x, y = pt(i, 5)
        ang = -math.pi / 2 + i * math.pi / 3
        dx, dy = 34 * math.cos(ang), 26 * math.sin(ang)
        anchor = "middle" if abs(math.cos(ang)) < 0.3 else ("start" if math.cos(ang) > 0 else "end")
        el.append(f'<text x="{x + dx:.0f}" y="{y + dy + 6:.0f}" font-size="17" fill="{INK}" text-anchor="{anchor}" font-weight="bold">{LABELS[i]}</text>')
    return el


def gate_str(g):
    o = (g or {}).get("overall", "?")
    return {"pass": "通过", "fail": "FAIL", "borderline": "border"}.get(o, "未判")


def table_svg(x0, y0, cid, w=330, rh=34):
    el = []
    va, vb = vec(f"{cid}-a"), vec(f"{cid}-b")
    rows = [("", "a", "b")]
    for i, lab in enumerate(LABELS):
        rows.append((lab, f"{va[i]:.1f}" if va[i] else "—", f"{vb[i]:.1f}" if vb[i] else "—"))
    rows.append(("均分", f"{avg(va):.2f}", f"{avg(vb):.2f}"))
    ta = (dims[f"{cid}-a"].get("gemini") or {}).get("tier") or "—"
    tb = (dims[f"{cid}-b"].get("gemini") or {}).get("tier") or "—"
    rows.append(("档位", ta, tb))
    rows.append(("Gate", gate_str(gate.get(f"{cid}-a")), gate_str(gate.get(f"{cid}-b"))))
    H = rh * len(rows)
    el.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{H}" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
    for r in range(1, len(rows)):
        el.append(f'<line x1="{x0}" y1="{y0 + r * rh}" x2="{x0 + w}" y2="{y0 + r * rh}" stroke="{GRID}" stroke-width="1"/>')
    c1, c2 = x0 + int(w * 0.44), x0 + int(w * 0.72)
    el.append(f'<line x1="{c1}" y1="{y0}" x2="{c1}" y2="{y0 + H}" stroke="{GRID}" stroke-width="1"/>')
    el.append(f'<line x1="{c2}" y1="{y0}" x2="{c2}" y2="{y0 + H}" stroke="{GRID}" stroke-width="1"/>')
    for r, (lab, sa, sb) in enumerate(rows):
        ty = y0 + r * rh + rh // 2 + 6
        if r == 0:
            el.append(f'<text x="{(x0 + c1) // 2}" y="{ty}" font-size="15" fill="{INK}" text-anchor="middle"> </text>')
            el.append(f'<text x="{(c1 + c2) // 2}" y="{ty}" font-size="16" fill="{C_A}" text-anchor="middle" font-weight="bold">a</text>')
            el.append(f'<text x="{(c2 + x0 + w) // 2}" y="{ty}" font-size="16" fill="{C_B}" text-anchor="middle" font-weight="bold">b</text>')
            continue
        el.append(f'<text x="{x0 + 12}" y="{ty}" font-size="15" fill="{INK}">{lab}</text>')
        for val, cx_ in ((sa, (c1 + c2) // 2), (sb, (c2 + x0 + w) // 2)):
            color = INK
            weight = ""
            try:
                if float(val) < 4.0:
                    color, weight = RED, ' font-weight="bold"'
            except ValueError:
                if val == "FAIL":
                    color, weight = RED, ' font-weight="bold"'
            el.append(f'<text x="{cx_}" y="{ty}" font-size="15" fill="{color}" text-anchor="middle"{weight}>{esc(str(val))}</text>')
    return el


def wrap(s, n):
    s = s or ""
    return [s[i:i + n] for i in range(0, len(s), n)]


def diag_svg(x0, y0, cid, width_chars=17):
    el = []
    y = y0
    for v, c, name in (("a", C_A, "a 诊断"), ("b", C_B, "b 诊断")):
        d = (dims[f"{cid}-{v}"].get("gemini") or {}).get("one_line_diagnosis") or ""
        el.append(f'<text x="{x0}" y="{y}" font-size="16" fill="{c}" font-weight="bold">{name}</text>')
        y += 26
        for line in wrap(d, width_chars)[:7]:
            el.append(f'<text x="{x0}" y="{y}" font-size="13.5" fill="{INK2}">{esc(line)}</text>')
            y += 21
        y += 18
    return el


for cid in CASES:
    topic = dims[f"{cid}-a"]["topic"]
    g = gsb[cid]
    v = VERDICT.get(g.get("final_a_vs_b"))
    flags = []
    if g.get("final_a_vs_b") is None:
        pass
    elif not g.get("swap_consistent"):
        flags.append("换位不稳定")
    if g.get("needs_human"):
        flags.append("needs_human")
    sub = f"GSB 判定：{v}" + (f"（{'，'.join(flags)}）" if flags else "") + " · 分数 1–5 · 严格口径（顶级锚定+AI味/PPT味计扣）"
    el = [f'<text x="40" y="52" font-size="26" fill="{INK}" font-weight="bold">{esc(topic)}</text>',
          f'<text x="40" y="86" font-size="15" fill="{INK2}">{esc(sub)}</text>',
          # 图例
          f'<line x1="42" y1="116" x2="70" y2="116" stroke="{C_A}" stroke-width="3"/>',
          f'<text x="78" y="122" font-size="15" fill="{INK}">a</text>',
          f'<line x1="104" y1="116" x2="132" y2="116" stroke="{C_B}" stroke-width="3"/>',
          f'<text x="140" y="122" font-size="15" fill="{INK}">b</text>']
    el += radar_svg(330, 430, 250, vec(f"{cid}-a"), vec(f"{cid}-b"))
    el += table_svg(700, 130, cid)
    el += diag_svg(1090, 160, cid)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1460 780">'
           f'<rect x="0" y="0" width="1460" height="780" fill="#ffffff" stroke="{GRID}"/>' + "".join(el) + '</svg>')
    (OUT / f"{cid}.svg").write_text(svg)
    print("wrote", cid)

# 总览
finals = [gsb[c].get("final_a_vs_b") for c in CASES]
G, S, B = (sum(1 for f in finals if f == x) for x in "GSB")
nh = sum(1 for f in finals if f is None)
nd = sum(1 for f in finals if f)
avg_a = [sum(vec(f"{c}-a")[i] for c in CASES) / 6 for i in range(6)]
avg_b = [sum(vec(f"{c}-b")[i] for c in CASES) / 6 for i in range(6)]
metrics = f"G/S/B(a vs b) = {G}/{S}/{B}" + (f"，转人工 {nh}" if nh else "")
if nd:
    metrics += f" · Net Lift = {(G - B) / nd:+.0%}"
if G + B:
    metrics += f" · Decisive Win = {G / (G + B):.0%}"
el = [f'<text x="40" y="52" font-size="26" fill="{INK}" font-weight="bold">总览：a vs b 六层质量向量（6 题盲评 · 严格口径）</text>',
      f'<text x="40" y="86" font-size="15" fill="{INK2}">{esc(metrics)} · 盲评：a/b 与模型版本映射未揭盲</text>',
      f'<line x1="42" y1="116" x2="70" y2="116" stroke="{C_A}" stroke-width="3"/>',
      f'<text x="78" y="122" font-size="15" fill="{INK}">a</text>',
      f'<line x1="104" y1="116" x2="132" y2="116" stroke="{C_B}" stroke-width="3"/>',
      f'<text x="140" y="122" font-size="15" fill="{INK}">b</text>']
el += radar_svg(330, 430, 250, [round(x, 2) for x in avg_a], [round(x, 2) for x in avg_b])
# 逐题判决表
x0, y0, w, rh = 700, 150, 700, 42
rows = [("题目", "GSB", "a 均分", "b 均分")]
for c in CASES:
    rows.append((dims[f"{c}-a"]["topic"], VERDICT.get(gsb[c].get("final_a_vs_b")),
                 f"{avg(vec(f'{c}-a')):.2f}", f"{avg(vec(f'{c}-b')):.2f}"))
H = rh * len(rows)
el.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{H}" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
for r in range(1, len(rows)):
    el.append(f'<line x1="{x0}" y1="{y0 + r * rh}" x2="{x0 + w}" y2="{y0 + r * rh}" stroke="{GRID}" stroke-width="1"/>')
cols = [x0 + int(w * f) for f in (0.52, 0.72, 0.86)]
for cx_ in cols:
    el.append(f'<line x1="{cx_}" y1="{y0}" x2="{cx_}" y2="{y0 + H}" stroke="{GRID}" stroke-width="1"/>')
for r, row in enumerate(rows):
    ty = y0 + r * rh + rh // 2 + 6
    weight = ' font-weight="bold"' if r == 0 else ""
    el.append(f'<text x="{x0 + 14}" y="{ty}" font-size="15" fill="{INK}"{weight}>{esc(row[0][:24])}</text>')
    vcol = {"a 优": C_A, "b 优": C_B, "转人工复核": RED}.get(row[1], INK2)
    el.append(f'<text x="{(cols[0] + cols[1]) // 2}" y="{ty}" font-size="15" fill="{vcol if r else INK}" text-anchor="middle"{weight}>{esc(row[1])}</text>')
    el.append(f'<text x="{(cols[1] + cols[2]) // 2}" y="{ty}" font-size="15" fill="{INK}" text-anchor="middle"{weight}>{esc(row[2])}</text>')
    el.append(f'<text x="{(cols[2] + x0 + w) // 2}" y="{ty}" font-size="15" fill="{INK}" text-anchor="middle"{weight}>{esc(row[3])}</text>')
svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1460 780">'
       f'<rect x="0" y="0" width="1460" height="780" fill="#ffffff" stroke="{GRID}"/>' + "".join(el) + '</svg>')
(OUT / "overall.svg").write_text(svg)
print("wrote overall")
