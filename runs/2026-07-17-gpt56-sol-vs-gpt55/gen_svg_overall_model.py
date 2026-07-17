#!/usr/bin/env python3
"""揭盲后的总览画板 SVG：按真实生产模型 gpt5.6-sol vs gpt5.5 重排。

揭盲映射（2026-07-17 用户提供）：5.6 = 001a/002b/003b/004b/005a/006b，5.5 为另一侧。
输出 svg/overall_model.svg
"""
import json
import math
from pathlib import Path

RUN = Path(__file__).parent
OUT = RUN / "svg"

INK, INK2, GRID = "#1f2329", "#646a73", "#d5d8dd"
C_56, C_55 = "#2a78d6", "#c98500"
RED = "#c0392b"

dims = json.load(open(RUN / "dimensions/scores.json"))
gsb = json.load(open(RUN / "gsb/gsb_results.json"))

LAYERS = ["L1_task", "L2_visual", "L3_temporal", "L4_audio", "L5_narrative", "L6_commercial"]
LABELS = ["L1 任务", "L2 视觉", "L3 时序", "L4 音频", "L5 叙事", "L6 商业"]
CASES = [f"case-00{i}" for i in range(1, 7)]
MAP56 = {"case-001": "a", "case-002": "b", "case-003": "b",
         "case-004": "b", "case-005": "a", "case-006": "b"}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def vec(key):
    ls = dims[key]["layer_scores"]
    return [ls.get(L) or 0 for L in LAYERS]


def avg(v):
    xs = [x for x in v if x]
    return sum(xs) / len(xs) if xs else 0


def radar_svg(cx, cy, R, v56, v55):
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
    for v, c in ((v55, C_55), (v56, C_56)):
        pts = " ".join(f"{pt(i, v[i])[0]:.1f},{pt(i, v[i])[1]:.1f}" for i in range(6))
        el.append(f'<polygon points="{pts}" fill="{c}" fill-opacity="0.18" stroke="{c}" stroke-width="2.5"/>')
        for i in range(6):
            x, y = pt(i, v[i])
            el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c}"/>')
    for i in range(6):
        x, y = pt(i, 5)
        ang = -math.pi / 2 + i * math.pi / 3
        dx, dy = 34 * math.cos(ang), 26 * math.sin(ang)
        anchor = "middle" if abs(math.cos(ang)) < 0.3 else ("start" if math.cos(ang) > 0 else "end")
        el.append(f'<text x="{x + dx:.0f}" y="{y + dy + 6:.0f}" font-size="17" fill="{INK}" text-anchor="middle" font-weight="bold">{LABELS[i]}</text>' if anchor == "middle" else
                  f'<text x="{x + dx:.0f}" y="{y + dy + 6:.0f}" font-size="17" fill="{INK}" text-anchor="{anchor}" font-weight="bold">{LABELS[i]}</text>')
    return el


v56 = [round(sum(vec(f"{c}-{MAP56[c]}")[i] for c in CASES) / 6, 2) for i in range(6)]
v55 = [round(sum(vec(f"{c}-{'b' if MAP56[c] == 'a' else 'a'}")[i] for c in CASES) / 6, 2) for i in range(6)]

# GSB 换算为 5.6 相对 5.5
verdicts = {}
for c in CASES:
    f = gsb[c].get("final_a_vs_b")
    if f == "S" or f is None:
        verdicts[c] = "S"
    else:
        winner_side = "a" if f == "G" else "b"
        verdicts[c] = "G" if winner_side == MAP56[c] else "B"
G = sum(1 for x in verdicts.values() if x == "G")
S = sum(1 for x in verdicts.values() if x == "S")
B = sum(1 for x in verdicts.values() if x == "B")
metrics = f"G/S/B(5.6 vs 5.5) = {G}/{S}/{B} · Net Lift = {(G - B) / 6:+.0%}"
if G + B:
    metrics += f" · Decisive Win Rate = {G / (G + B):.0%}"

el = [f'<text x="40" y="52" font-size="26" fill="{INK}" font-weight="bold">总览：gpt5.6-sol vs gpt5.5（6 题盲评揭盲 · 严格口径）</text>',
      f'<text x="40" y="86" font-size="15" fill="{INK2}">{esc(metrics)} · 盲评后按用户提供映射揭盲（5.6 = 电池a/商业b/隐私b/动物b/历史a/深海b）</text>',
      f'<line x1="42" y1="116" x2="70" y2="116" stroke="{C_56}" stroke-width="3"/>',
      f'<text x="78" y="122" font-size="15" fill="{INK}" font-weight="bold">gpt5.6-sol</text>',
      f'<line x1="180" y1="116" x2="208" y2="116" stroke="{C_55}" stroke-width="3"/>',
      f'<text x="216" y="122" font-size="15" fill="{INK}">gpt5.5</text>']
el += radar_svg(330, 430, 250, v56, v55)

VN = {"G": "5.6 优", "S": "无实质差异", "B": "5.5 优"}
x0, y0, w, rh = 700, 130, 720, 42
rows = [("题目", "GSB", "5.6 侧", "5.6 均分", "5.5 均分")]
for c in CASES:
    s56 = MAP56[c]
    s55 = "b" if s56 == "a" else "a"
    label = VN[verdicts[c]] + ("（转人工）" if gsb[c].get("needs_human") and verdicts[c] == "S" else "")
    rows.append((dims[f"{c}-a"]["topic"], label, s56,
                 f"{avg(vec(f'{c}-{s56}')):.2f}", f"{avg(vec(f'{c}-{s55}')):.2f}"))
rows.append(("六层平均", "", "", f"{avg(v56):.2f}", f"{avg(v55):.2f}"))
H = rh * len(rows)
el.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{H}" fill="none" stroke="{GRID}" stroke-width="1.5"/>')
for r in range(1, len(rows)):
    el.append(f'<line x1="{x0}" y1="{y0 + r * rh}" x2="{x0 + w}" y2="{y0 + r * rh}" stroke="{GRID}" stroke-width="1"/>')
cols = [x0 + int(w * f) for f in (0.42, 0.66, 0.74, 0.87)]
for cx_ in cols:
    el.append(f'<line x1="{cx_}" y1="{y0}" x2="{cx_}" y2="{y0 + H}" stroke="{GRID}" stroke-width="1"/>')
for r, row in enumerate(rows):
    ty = y0 + r * rh + rh // 2 + 6
    hdr = r == 0
    last = r == len(rows) - 1
    weight = ' font-weight="bold"' if hdr or last else ""
    el.append(f'<text x="{x0 + 14}" y="{ty}" font-size="15" fill="{INK}"{weight}>{esc(row[0][:24])}</text>')
    vcol = {"5.6 优": C_56, "5.5 优": C_55}.get(row[1][:5].strip(), INK2)
    el.append(f'<text x="{(cols[0] + cols[1]) // 2}" y="{ty}" font-size="15" fill="{vcol if not hdr else INK}" text-anchor="middle"{weight}>{esc(row[1])}</text>')
    el.append(f'<text x="{(cols[1] + cols[2]) // 2}" y="{ty}" font-size="14" fill="{INK2}" text-anchor="middle">{esc(row[2])}</text>')
    el.append(f'<text x="{(cols[2] + cols[3]) // 2}" y="{ty}" font-size="15" fill="{INK}" text-anchor="middle"{weight}>{esc(row[3])}</text>')
    el.append(f'<text x="{(cols[3] + x0 + w) // 2}" y="{ty}" font-size="15" fill="{INK}" text-anchor="middle"{weight}>{esc(row[4])}</text>')

note_y = y0 + H + 44
for i, line in enumerate((
        "gpt5.6-sol 拿下全部 5 个分出胜负的题：既赢在制作（实拍 b-roll、版画/铜版画艺术方向），",
        "也赢在质量控制（对手侧电池题有空面板/悬浮元素等多处确认画面 bug）。",
        "深海题双方各缺频道覆盖点，换位反转降级 S，转人工复核。")):
    el.append(f'<text x="{x0}" y="{note_y + i * 26}" font-size="14" fill="{INK2}">{esc(line)}</text>')

svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1460 780">'
       f'<rect x="0" y="0" width="1460" height="780" fill="#ffffff" stroke="{GRID}"/>' + "".join(el) + '</svg>')
(OUT / "overall_model.svg").write_text(svg)
print("wrote overall_model.svg", "| G/S/B =", G, S, B, "| 5.6 avg =", f"{avg(v56):.2f}", "| 5.5 avg =", f"{avg(v55):.2f}")
