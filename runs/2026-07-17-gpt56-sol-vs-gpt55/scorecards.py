#!/usr/bin/env python3
"""评分卡：每题一张 PNG = 雷达图(a vs b) + 六层分数表 + 档位/Gate/GSB + 一句话诊断。"""
import json
import math
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUN = Path(__file__).parent
OUT = RUN / "radar"
OUT.mkdir(exist_ok=True)

plt.rcParams["font.family"] = ["Hiragino Sans GB", "PingFang HK", "Songti SC", "STHeiti", "Hiragino Sans"]
plt.rcParams["axes.unicode_minus"] = False

SURFACE = "#fcfcfb"
INK = "#1a1a19"
INK2 = "#5f5e58"
GRID = "#e4e3dd"
C_A, C_B = "#2a78d6", "#eda100"

dims = json.load(open(RUN / "dimensions/scores.json"))
gsb = json.load(open(RUN / "gsb/gsb_results.json"))
gate = json.load(open(RUN / "gate/gate_results.json"))
for cid, adj in json.load(open(RUN / "gsb/adjustments.json")).items():
    if cid in gsb and "final_a_vs_b" in adj:
        gsb[cid]["final_a_vs_b"] = adj["final_a_vs_b"]
        gsb[cid]["needs_human"] = adj.get("needs_human", gsb[cid].get("needs_human"))

LAYERS = ["L1_task", "L2_visual", "L3_temporal", "L4_audio", "L5_narrative", "L6_commercial"]
LABELS = ["L1 任务", "L2 视觉", "L3 时序", "L4 音频", "L5 叙事", "L6 商业"]
CASES = [f"case-00{i}" for i in range(1, 7)]


def vec(key):
    ls = dims[key]["layer_scores"]
    return [ls.get(L) or 0 for L in LAYERS]


def draw_radar(ax, va, vb):
    N = len(LAYERS)
    ang = [i / N * 2 * math.pi + math.pi / 2 for i in range(N)]
    ang_c = ang + ang[:1]
    for r in (1, 2, 3, 4, 5):
        ax.plot(ang_c, [r] * (N + 1), color=GRID, lw=0.8, zorder=1)
    for a in ang:
        ax.plot([a, a], [0, 5], color=GRID, lw=0.8, zorder=1)
    for v, c, label, dz in ((vb, C_B, "b", 0), (va, C_A, "a", 1)):
        vc = v + v[:1]
        ax.plot(ang_c, vc, color=c, lw=2, zorder=3 + dz, label=label)
        ax.fill(ang_c, vc, color=c, alpha=0.12, zorder=2 + dz)
        ax.scatter(ang, v, s=16, color=c, zorder=5 + dz)
    for i, a in enumerate(ang):
        ax.annotate(LABELS[i], (a, 5), textcoords="offset points",
                    xytext=(0, 13 if math.sin(a) > 0.1 else -15 if math.sin(a) < -0.1 else 4),
                    ha="center", fontsize=10, color=INK, fontweight="medium", zorder=6)
    ax.set_ylim(0, 5.35)
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor(SURFACE)
    ax.legend(loc="upper left", bbox_to_anchor=(-0.12, 1.08), frameon=False, fontsize=11)


def gate_str(g):
    o = (g or {}).get("overall", "?")
    return {"pass": "通过", "fail": "FAIL", "borderline": "borderline"}.get(o, "未判")


def score_table(ax, cid):
    ax.axis("off")
    ea, eb = dims[f"{cid}-a"], dims[f"{cid}-b"]
    va, vb = vec(f"{cid}-a"), vec(f"{cid}-b")
    rows = [["", "a", "b"]]
    for i, lab in enumerate(LABELS):
        rows.append([lab, f"{va[i]:.1f}" if va[i] else "—", f"{vb[i]:.1f}" if vb[i] else "—"])
    rows.append(["均分", f"{sum(x for x in va if x)/max(1,sum(1 for x in va if x)):.2f}",
                 f"{sum(x for x in vb if x)/max(1,sum(1 for x in vb if x)):.2f}"])
    rows.append(["档位", (ea.get("gemini") or {}).get("tier") or "—", (eb.get("gemini") or {}).get("tier") or "—"])
    rows.append(["Gate", gate_str(gate.get(f"{cid}-a")), gate_str(gate.get(f"{cid}-b"))])
    tb = ax.table(cellText=rows, loc="center", cellLoc="center", colWidths=[0.4, 0.3, 0.3])
    tb.auto_set_font_size(False)
    tb.set_fontsize(10.5)
    tb.scale(1, 1.45)
    n = len(rows)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_text_props(color=INK)
        if r == 0:
            cell.set_facecolor("#f1f0ea")
            cell.set_text_props(fontweight="bold", color=INK)
            if c == 1: cell.set_text_props(color=C_A, fontweight="bold")
            if c == 2: cell.set_text_props(color="#a06f00", fontweight="bold")
        elif r >= n - 3:
            cell.set_facecolor("#f7f6f1")
            if c == 0: cell.set_text_props(fontweight="bold")
        # 低分标红
        if 1 <= r <= 6 and c > 0:
            try:
                if float(rows[r][c]) < 4.0:
                    cell.set_text_props(color="#c0392b", fontweight="bold")
            except ValueError:
                pass


VERDICT = {"G": "a 优", "S": "无实质差异", "B": "b 优", None: "转人工复核"}

for cid in CASES:
    topic = dims[f"{cid}-a"]["topic"]
    g = gsb[cid]
    v = VERDICT[g.get("final_a_vs_b")]
    flags = []
    if g.get("final_a_vs_b") is None:
        flags.append("跨轨冲突")
    elif not g.get("swap_consistent"):
        flags.append("换位不稳定")
    if g.get("needs_human") and g.get("final_a_vs_b"):
        flags.append("needs_human")
    flag_s = f"（{'，'.join(flags)}）" if flags else ""

    fig = plt.figure(figsize=(12.6, 6.2), facecolor=SURFACE)
    fig.suptitle(f"{topic}", fontsize=17, fontweight="bold", color=INK, x=0.05, ha="left", y=0.97)
    fig.text(0.05, 0.895, f"GSB 判定：{v}{flag_s} · 分数 1–5（双模型合并，密度锚定口径） · {cid}",
             fontsize=11, color=INK2)
    ax1 = fig.add_axes([0.03, 0.06, 0.42, 0.76], polar=True)
    draw_radar(ax1, vec(f"{cid}-a"), vec(f"{cid}-b"))
    ax2 = fig.add_axes([0.47, 0.14, 0.24, 0.68])
    score_table(ax2, cid)
    # 一句话诊断
    da = (dims[f"{cid}-a"].get("gemini") or {}).get("one_line_diagnosis") or ""
    db = (dims[f"{cid}-b"].get("gemini") or {}).get("one_line_diagnosis") or ""
    ax3 = fig.add_axes([0.72, 0.06, 0.27, 0.8]); ax3.axis("off")
    ax3.text(0, 0.98, "a 诊断", fontsize=11, fontweight="bold", color=C_A, va="top")
    ax3.text(0, 0.90, textwrap.fill(da, 16), fontsize=9.5, color=INK, va="top", linespacing=1.5)
    ax3.text(0, 0.46, "b 诊断", fontsize=11, fontweight="bold", color="#a06f00", va="top")
    ax3.text(0, 0.38, textwrap.fill(db, 16), fontsize=9.5, color=INK, va="top", linespacing=1.5)
    fig.savefig(OUT / f"card-{cid}.png", dpi=170, facecolor=SURFACE)
    plt.close(fig)
    print("wrote card", cid)

# ---------- 总览卡 ----------
avg_a = [sum(vec(f"{c}-a")[i] for c in CASES) / len(CASES) for i in range(6)]
avg_b = [sum(vec(f"{c}-b")[i] for c in CASES) / len(CASES) for i in range(6)]
finals = [gsb[c].get("final_a_vs_b") for c in CASES]
G, S, B = (sum(1 for f in finals if f == x) for x in "GSB")
nh = sum(1 for f in finals if f is None)
nd = sum(1 for f in finals if f)

fig = plt.figure(figsize=(12.6, 6.2), facecolor=SURFACE)
fig.suptitle("总览：a vs b（6 题盲评 · VideoBench 六层维度）", fontsize=17, fontweight="bold",
             color=INK, x=0.05, ha="left", y=0.97)
fig.text(0.05, 0.895,
         f"G/S/B(a vs b) = {G}/{S}/{B}，转人工 {nh} · Net Lift = {(G-B)/nd:+.0%} · "
         f"Decisive Win Rate = {G/(G+B):.0%} · 盲评：a/b 与模型版本的映射未揭盲",
         fontsize=11, color=INK2)
ax1 = fig.add_axes([0.03, 0.06, 0.42, 0.76], polar=True)
draw_radar(ax1, [round(x, 2) for x in avg_a], [round(x, 2) for x in avg_b])
ax2 = fig.add_axes([0.46, 0.10, 0.53, 0.72]); ax2.axis("off")
rows = [["题目", "GSB", "换位", "a 均分", "b 均分"]]
for cid in CASES:
    va, vb = vec(f"{cid}-a"), vec(f"{cid}-b")
    g = gsb[cid]
    swap = ("跨轨冲突" if g.get("final_a_vs_b") is None
            else "一致" if g.get("swap_consistent") else "反转")
    rows.append([dims[f"{cid}-a"]["topic"], VERDICT[g.get("final_a_vs_b")], swap,
                 f"{sum(x for x in va if x)/max(1,sum(1 for x in va if x)):.2f}",
                 f"{sum(x for x in vb if x)/max(1,sum(1 for x in vb if x)):.2f}"])
tb = ax2.table(cellText=rows, loc="center", cellLoc="center", colWidths=[0.40, 0.22, 0.12, 0.13, 0.13])
tb.auto_set_font_size(False)
tb.set_fontsize(10.5)
tb.scale(1, 1.8)
for (r, c), cell in tb.get_celld().items():
    cell.set_edgecolor(GRID)
    cell.set_text_props(color=INK)
    if r == 0:
        cell.set_facecolor("#f1f0ea"); cell.set_text_props(fontweight="bold")
    elif c == 1:
        t = rows[r][1]
        cell.set_text_props(fontweight="bold",
                            color=C_A if t == "a 优" else "#a06f00" if t == "b 优" else "#c0392b" if "人工" in t else INK2)
fig.savefig(OUT / "card-overall.png", dpi=170, facecolor=SURFACE)
print("wrote card overall")
print("done")
