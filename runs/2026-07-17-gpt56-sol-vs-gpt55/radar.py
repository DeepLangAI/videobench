#!/usr/bin/env python3
"""六层维度雷达图：每题 a vs b 对比 + 全局平均，输出 PNG 到 radar/。"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN = Path(__file__).parent
OUT = RUN / "radar"
OUT.mkdir(exist_ok=True)

plt.rcParams["font.family"] = ["Hiragino Sans GB", "PingFang HK", "Songti SC", "STHeiti", "Hiragino Sans"]
plt.rcParams["axes.unicode_minus"] = False

SURFACE = "#fcfcfb"
INK = "#1a1a19"
INK2 = "#5f5e58"
GRID = "#e4e3dd"
C_A, C_B = "#2a78d6", "#eda100"  # dataviz 校验通过（黄对比度 WARN → 图例+数值直标补偿）

dims = json.load(open(RUN / "dimensions/scores.json"))
gsb = json.load(open(RUN / "gsb/gsb_results.json"))
for cid, adj in json.load(open(RUN / "gsb/adjustments.json")).items():
    if cid in gsb and "final_a_vs_b" in adj:
        gsb[cid]["final_a_vs_b"] = adj["final_a_vs_b"]
        gsb[cid]["needs_human"] = adj.get("needs_human", gsb[cid].get("needs_human"))
        gsb[cid]["adjusted"] = True
LAYERS = ["L1_task", "L2_visual", "L3_temporal", "L4_audio", "L5_narrative", "L6_commercial"]
LABELS = ["L1 任务", "L2 视觉", "L3 时序", "L4 音频", "L5 叙事", "L6 商业"]
CASES = [f"case-00{i}" for i in range(1, 7)]


def vec(key):
    ls = dims[key]["layer_scores"]
    return [ls.get(L) or 0 for L in LAYERS]


def draw(ax, va, vb, title, subtitle):
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
        ax.scatter(ang, v, s=18, color=c, zorder=5 + dz)
    # 数值直标（黄对比度 WARN 的补救：文字用 ink，不用系列色）
    for i, a in enumerate(ang):
        va_i, vb_i = va[i], vb[i]
        for v, c, off in ((va_i, C_A, 0.42), (vb_i, C_B, -0.38)):
            ax.annotate(f"{v:.1f}", (a, v), textcoords="offset points",
                        xytext=(0, off * 16), ha="center", fontsize=7.5, color=INK2, zorder=6)
        ax.annotate(LABELS[i], (a, 5), textcoords="offset points",
                    xytext=(0, 14 if math.sin(a) > 0.1 else -16 if math.sin(a) < -0.1 else 4),
                    ha="center", fontsize=10, color=INK, fontweight="medium", zorder=6)
    ax.set_ylim(0, 5.4)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor(SURFACE)
    ax.set_title(title + "\n", fontsize=13, color=INK, fontweight="bold", pad=26)
    ax.text(0.5, -0.10, subtitle, transform=ax.transAxes, ha="center", fontsize=9, color=INK2)


for cid in CASES:
    topic = dims[f"{cid}-a"]["topic"]
    g = gsb[cid]
    verdict = {"G": "a 优", "S": "无实质差异", "B": "b 优"}.get(g.get("final_a_vs_b"), "转人工")
    stab = "（跨轨冲突）" if g.get("final_a_vs_b") is None else (
        "" if g.get("swap_consistent") else "（换位不稳定）")
    if g.get("needs_human") and g.get("final_a_vs_b"):
        stab += "（needs_human）"
    fig = plt.figure(figsize=(6.4, 6.6), facecolor=SURFACE)
    ax = fig.add_subplot(111, polar=True)
    draw(ax, vec(f"{cid}-a"), vec(f"{cid}-b"), topic, f"GSB：{verdict}{stab} · 1–5 分 · {cid}")
    ax.legend(loc="upper right", bbox_to_anchor=(1.18, 1.12), frameon=False, fontsize=11)
    fig.savefig(OUT / f"{cid}.png", dpi=180, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print("wrote", cid)

# 全局平均
avg_a = [sum(vec(f"{c}-a")[i] for c in CASES) / len(CASES) for i in range(6)]
avg_b = [sum(vec(f"{c}-b")[i] for c in CASES) / len(CASES) for i in range(6)]
fig = plt.figure(figsize=(6.4, 6.6), facecolor=SURFACE)
ax = fig.add_subplot(111, polar=True)
finals = [gsb[c].get("final_a_vs_b") for c in CASES if gsb[c].get("final_a_vs_b")]
G, S, B = (finals.count(x) for x in "GSB")
n = len(finals)
nh = sum(1 for c in CASES if not gsb[c].get("final_a_vs_b"))
sub = f"6 题平均 · G/S/B(a vs b)={G}/{S}/{B}，转人工 {nh} · Net Lift={(G-B)/n:+.0%}"
if G + B:
    sub += f" · Decisive Win={G/(G+B):.0%}"
draw(ax, [round(x, 2) for x in avg_a], [round(x, 2) for x in avg_b], "全局平均：a vs b 六层质量向量", sub)
ax.legend(loc="upper right", bbox_to_anchor=(1.18, 1.12), frameon=False, fontsize=11)
fig.savefig(OUT / "overall.png", dpi=180, bbox_inches="tight", facecolor=SURFACE)
print("wrote overall")
