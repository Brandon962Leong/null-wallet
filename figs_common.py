import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.patches as mp, numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
NAVY, TEAL, GREY, LG, RED, GREEN, AMBER, INK = "#0B1F3A", "#0A9396", "#6B7785", "#E8ECF1", "#C0392B", "#2E8B57", "#E09F3E", "#1B2430"
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 11, "axes.edgecolor": GREY, "axes.labelcolor": INK, "text.color": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100, "savefig.dpi": 200, "savefig.bbox": "tight", "mathtext.fontset": "stix"})
def save(fig, name): fig.savefig(f"figs/{name}.png", facecolor="white"); plt.close(fig)
def box(ax, x, y, w, h, text, fc=NAVY, tc="white", fs=10, bold=True, ec=None, r=0.02, align="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.004,rounding_size={r}", fc=fc, ec=ec or fc, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)
def arrow(ax, p, q, c=GREY, lw=1.6, style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14, color=c, lw=lw, connectionstyle=f"arc3,rad={rad}"))
def canvas(w=13, h=6.5):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); return fig, ax
