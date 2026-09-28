"""Slide graphic: 'Well-Posedness of CDR Equation' -- the 3-step incremental proof
(diffusion -> +convection -> +reaction), each step extending the previous, with
explicit constants derived from this study's own verified data (not assumed).
Sourced from CDR_PINN_Advection_Design.md Sec 5-6 and CDR_PINN_Reaction_Design.md
Sec 5.1-5.2.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({"font.family": "DejaVu Sans"})

BLUE, GREEN, RED, INK, GRAY = "#1f5fa8", "#1a8f4a", "#c0392b", "#1a1a2e", "#6b6b6b"
GOLD = "#b8860b"

FIG_W, FIG_H = 13.333, 7.5
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=180)
fig.patch.set_facecolor("white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 13.333); ax.set_ylim(0, 7.5); ax.axis("off")

ax.text(6.6667, 7.15, "Well-Posedness of the CDR Equation", ha="center", va="center",
        fontsize=25, fontweight="bold", color=INK)
ax.text(6.6667, 6.68, "an incremental proof \u2014 each step extends the previous, with constants from this study's own verified data",
        ha="center", va="center", fontsize=11.5, color=GRAY, style="italic")

CARD_Y_TOP = 6.10
CARD_H = 4.35
GAPX = 0.28
W = (13.333 - 0.7 - 2 * GAPX) / 3
xs = [0.35, 0.35 + W + GAPX, 0.35 + 2 * (W + GAPX)]

cards = [
    dict(color=BLUE, step="STEP 1", title="Diffusion alone",
         claim="Uniform parabolicity",
         math=r"$D(x,y,t)\in[D_{\min},D_{\max}],\;\;D_{\min}>0$",
         why="$D_{net}$: finite MLP on a compact input\ndomain $\\Rightarrow$ Extreme Value Theorem\nbounds its output; softplus keeps it $>0$",
         result="Satisfies the hypothesis\nEvans (2010) Ch. 7 requires for\nlinear parabolic PDEs"),
    dict(color=GREEN, step="STEP 2", title="+ Convection",
         claim="G\u00e5rding's inequality",
         math=r"$B[u,u;t]\geq \alpha\|\nabla u\|^2-\beta\|u\|^2$" + "\n" +
              r"$\alpha=\dfrac{D_{\min}}{2},\quad \beta=\dfrac{V_{\max}^2}{2D_{\min}}$",
         why="Young's inequality bounds the drift\nterm $v\\cdot\\nabla u$;  $V_{\\max}$ from the\nmeasured $77.31^\\circ$ max. slope",
         result="Existence via $u=e^{\\lambda t}\\tilde u$\n($\\lambda>\\beta$) + Galerkin method;\nuniqueness from linearity"),
    dict(color=RED, step="STEP 3", title="+ Reaction",
         claim="Global bound & global Lipschitz",
         math=r"$|R|\leq \dfrac{\rho_{\max}}{4}\;\;\forall u\in\mathbb{R}$" + "\n" +
              r"Lipschitz const. $=\dfrac{\rho_{\max}}{6\sqrt{3}}$",
         why="$\\sigma(u)(1-\\sigma(u))\\in(0,0.25]$ for\nEVERY real $u$ \u2014 bounded no matter\nhow large $u$ grows",
         result="Gr\u00f6nwall's inequality $\\Rightarrow$\nGLOBAL existence/uniqueness\nover the full $T=266$ months"),
]

for i, cd in enumerate(cards):
    x0 = xs[i]
    box = FancyBboxPatch((x0, CARD_Y_TOP - CARD_H), W, CARD_H,
                          boxstyle="round,pad=0.02,rounding_size=0.12",
                          linewidth=1.7, edgecolor=cd["color"], facecolor="white", zorder=3)
    ax.add_patch(box)
    strip = FancyBboxPatch((x0, CARD_Y_TOP - 0.62), W, 0.62,
                            boxstyle="round,pad=0,rounding_size=0.12",
                            linewidth=0, facecolor=cd["color"], alpha=0.15, zorder=4)
    ax.add_patch(strip)
    cx = x0 + W / 2
    ax.text(cx, CARD_Y_TOP - 0.22, cd["step"], ha="center", va="center",
            fontsize=11, fontweight="bold", color=cd["color"], zorder=5)
    ax.text(cx, CARD_Y_TOP - 0.48, cd["title"], ha="center", va="center",
            fontsize=13.5, fontweight="bold", color=INK, zorder=5)

    ax.text(cx, CARD_Y_TOP - 0.92, cd["claim"], ha="center", va="center",
            fontsize=10.8, color=cd["color"], fontweight="bold", style="italic", zorder=5)
    ax.text(cx, CARD_Y_TOP - 1.45, cd["math"], ha="center", va="center",
            fontsize=11.3, color=INK, zorder=5, linespacing=1.7)
    ax.plot([x0 + 0.25, x0 + W - 0.25], [CARD_Y_TOP - 2.10, CARD_Y_TOP - 2.10],
            color="#dddddd", lw=0.8, zorder=4)
    ax.text(cx, CARD_Y_TOP - 2.24, "WHY", ha="center", va="top", fontsize=8, color=GRAY,
            fontweight="bold", zorder=5)
    ax.text(cx, CARD_Y_TOP - 2.46, cd["why"], ha="center", va="top", fontsize=9.0, color="#333333",
            zorder=5, linespacing=1.5)
    ax.text(cx, CARD_Y_TOP - 3.32, "\u21d2", ha="center", va="center", fontsize=15, color=cd["color"], zorder=5)
    ax.text(cx, CARD_Y_TOP - 3.60, cd["result"], ha="center", va="top", fontsize=8.9,
            color=INK, fontweight="bold", zorder=5, linespacing=1.5)

    if i < 2:
        ax.add_patch(FancyArrowPatch((x0 + W + 0.03, CARD_Y_TOP - CARD_H / 2),
                                      (x0 + W + GAPX - 0.03, CARD_Y_TOP - CARD_H / 2),
                                      arrowstyle="-|>", color="#999999", lw=2.2, mutation_scale=16, zorder=6))

# --------------------------------------------------------------- result banner ---
RES_TOP = CARD_Y_TOP - CARD_H - 0.30
RES_H = 1.15
res_box = FancyBboxPatch((0.35, RES_TOP - RES_H), 12.63, RES_H,
                          boxstyle="round,pad=0.02,rounding_size=0.12",
                          linewidth=1.8, edgecolor=GOLD, facecolor="#fff7e6", zorder=3)
ax.add_patch(res_box)
ax.text(6.6667, RES_TOP - 0.38,
        r"RESULT:  a weak solution $u\in H^1(\Omega)$ exists and is unique over the FULL $T=266$-month horizon",
        ha="center", va="center", fontsize=13, fontweight="bold", color="#5c4400", zorder=4)
ax.text(6.6667, RES_TOP - 0.78,
        "Every constant ($D_{\\min}$, $V_{\\max}$, $\\rho_{\\max}$) is computed from this study's own verified data extremes \u2014 proven, not assumed.\n"
        "A generic nonlinear reaction (e.g. a bare cubic) only guarantees local-in-time existence \u2014 this sigmoid-based construction provably cannot blow up.",
        ha="center", va="center", fontsize=9.0, color="#6b5200", style="italic", zorder=4, linespacing=1.5)

fig.savefig(r"D:\FOREST FIRE MAPPING(INDIA)\Manuscript_TGRS\figures\SlideCDR_WellPosedness.png",
            facecolor="white", bbox_inches=None, pad_inches=0)
print("saved")
