"""Creative annotated-equation slide graphic: the CDR governing equation with
color-coded terms, callout cards (mechanism + one-line meaning + coefficient
formula) connected by elbow connectors, plus BC/IC and the Fisher-KPP
correction note. Term x-positions are measured from the real rendered text
(two-pass), not guessed, so connectors land exactly under each term.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.transforms import Bbox

plt.rcParams.update({"font.family": "DejaVu Sans"})

BLUE, GREEN, RED, INK, GRAY = "#1f5fa8", "#1a8f4a", "#c0392b", "#1a1a2e", "#6b6b6b"
AMBER = "#b8860b"

FIG_W, FIG_H = 13.333, 7.5  # 16:9
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=180)
fig.patch.set_facecolor("white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 13.333); ax.set_ylim(0, 7.5); ax.axis("off")

# ---------------------------------------------------------------- title ---
ax.text(6.6667, 7.12, "The CDR Governing Equation", ha="center", va="center",
        fontsize=24, fontweight="bold", color=INK)
ax.text(6.6667, 6.66, "one equation, three fire-behavior mechanisms",
        ha="center", va="center", fontsize=12.5, color=GRAY, style="italic")

# ---------------------------------------------------------- equation row ---
EQ_Y = 5.55
FS = 27
pieces = [
    (r"$\frac{\partial u}{\partial t}$", INK),
    (r"$\;=\;$", INK),
    (r"$D\nabla^2 u$", BLUE),
    (r"$\;-\;$", INK),
    (r"$\mathbf{v}\cdot\nabla u$", GREEN),
    (r"$\;+\;$", INK),
    (r"$\rho\,\sigma(u)(1-\sigma(u))$", RED),
]

# pass 1: draw off-screen to measure widths precisely, then reposition centered
renderer = fig.canvas.get_renderer()
widths = []
tmp_texts = []
for s, c in pieces:
    t = ax.text(0, EQ_Y, s, fontsize=FS, color=c, ha="left", va="center")
    fig.canvas.draw()
    bb = t.get_window_extent(renderer=renderer)
    bb_data = Bbox(ax.transData.inverted().transform(bb))
    widths.append(bb_data.width)
    tmp_texts.append(t)
for t in tmp_texts:
    t.remove()

total_w = sum(widths)
x = 6.6667 - total_w / 2
term_boxes = []  # (x_center, half_width, color) for the 3 mechanism terms
for (s, c), w in zip(pieces, widths):
    ax.text(x, EQ_Y, s, fontsize=FS, color=c, ha="left", va="center")
    if c in (BLUE, GREEN, RED):
        term_boxes.append((x + w / 2, w / 2, c))
    x += w

labels = ["state change", "diffusion", "", "advection", "", "reaction", ""]
# thin colour underline under each mechanism term
for (xc, hw, c) in term_boxes:
    ax.plot([xc - hw, xc + hw], [EQ_Y - 0.34, EQ_Y - 0.34], color=c, lw=2.4, solid_capstyle="round")

# ---------------------------------------------------------- callout cards ---
CARD_Y_TOP = 4.55
CARD_H = 1.85
cards = [
    dict(term_xc=term_boxes[0][0], color=BLUE, x0=0.35, w=4.0,
         head="DIFFUSION  \u2014  $D$", sub="Vegetation & moisture spread",
         body=r"$D=\mathrm{softplus}\!\left(f_D(\mathrm{NDVI},F)-\mathrm{softplus}(w)\,\mathrm{NDVI}'\right)$",
         basis="Fisher\u2013KPP (1937)  \u2022  Biswas biophysical/climatic group"),
    dict(term_xc=term_boxes[1][0], color=GREEN, x0=4.65, w=4.03,
         head="CONVECTION  \u2014  $\\mathbf{v}$", sub="Terrain-driven upslope transport",
         body=r"$\mathbf{v}=\mathrm{softplus}(c)\cdot\nabla E$",
         basis="Rothermel (1972)  \u2022  Biswas topographic group"),
    dict(term_xc=term_boxes[2][0], color=RED, x0=8.98, w=4.0,
         head="REACTION  \u2014  $\\rho$", sub="Human-ignition risk growth",
         body=r"$\rho=\mathrm{softplus}\!\left(f_\rho(Q,\mathrm{NDVI},S,R)\right)$",
         basis="Logistic-type growth  \u2022  Biswas human-activity group"),
]

for cd in cards:
    box = FancyBboxPatch((cd["x0"], CARD_Y_TOP - CARD_H), cd["w"], CARD_H,
                          boxstyle="round,pad=0.02,rounding_size=0.12",
                          linewidth=1.6, edgecolor=cd["color"], facecolor="#ffffff", zorder=3)
    ax.add_patch(box)
    top_strip = FancyBboxPatch((cd["x0"], CARD_Y_TOP - 0.5), cd["w"], 0.5,
                                boxstyle="round,pad=0,rounding_size=0.12",
                                linewidth=0, facecolor=cd["color"], alpha=0.14, zorder=4)
    ax.add_patch(top_strip)
    cx = cd["x0"] + cd["w"] / 2
    ax.text(cx, CARD_Y_TOP - 0.25, cd["head"], ha="center", va="center",
            fontsize=13.5, fontweight="bold", color=cd["color"], zorder=5)
    ax.text(cx, CARD_Y_TOP - 0.76, cd["sub"], ha="center", va="center",
            fontsize=10, color=INK, style="italic", zorder=5)
    ax.text(cx, CARD_Y_TOP - 1.24, cd["body"], ha="center", va="center",
            fontsize=10.5, color=INK, zorder=5)
    ax.text(cx, CARD_Y_TOP - 1.68, cd["basis"], ha="center", va="center",
            fontsize=8.3, color=GRAY, zorder=5)

    # elbow connector: term underline -> down -> across -> up to card top
    mid_y = EQ_Y - 0.75
    ax.add_patch(FancyArrowPatch((cd["term_xc"], EQ_Y - 0.38), (cd["term_xc"], mid_y),
                                  arrowstyle="-", color=cd["color"], lw=1.6, zorder=2))
    ax.add_patch(FancyArrowPatch((cd["term_xc"], mid_y), (cx, mid_y),
                                  arrowstyle="-", color=cd["color"], lw=1.6, zorder=2))
    ax.add_patch(FancyArrowPatch((cx, mid_y), (cx, CARD_Y_TOP),
                                  arrowstyle="-|>", color=cd["color"], lw=1.6,
                                  mutation_scale=11, zorder=2))

# ------------------------------------------------------- BC / IC strip ---
GAP = 0.15
BC_H = 0.95
bc_top = CARD_Y_TOP - CARD_H - GAP          # top edge of the BC/IC box
bc_bottom = bc_top - BC_H
bc_box = FancyBboxPatch((0.35, bc_bottom), 12.63, BC_H,
                         boxstyle="round,pad=0.02,rounding_size=0.1",
                         linewidth=1.1, edgecolor="#999999", facecolor="#f5f5f5", zorder=3)
ax.add_patch(bc_box)
ax.text(3.2, bc_top - 0.24, r"Boundary:  $\partial u/\partial n = 0$  on  $\partial\Omega$  (no risk flux across India's border)",
        ha="center", va="center", fontsize=10.3, color=INK, zorder=4)
ax.text(9.9, bc_top - 0.24, r"Initial:  $u(x,y,0) = 0$  (no pre-2000 fire history available)",
        ha="center", va="center", fontsize=10.3, color=INK, zorder=4)
ax.plot([6.6667, 6.6667], [bc_top - 0.42, bc_top - 0.06], color="#bbbbbb", lw=1)
ax.plot([0.65, 12.68], [bc_top - 0.46, bc_top - 0.46], color="#dddddd", lw=0.8)
ax.text(6.6667, bc_top - 0.72,
        r"$f_D$ and $f_\rho$ are small neural networks that learn the physical process  •  "
        r"$\mathrm{softplus}$ keeps $D,\rho>0$ and $\mathbf{v}$ always upslope $\Rightarrow$ global well-posedness (proven)",
        ha="center", va="center", fontsize=9.4, color="#444444", zorder=4)

# ------------------------------------------------------- honesty callout ---
AMBER_H = 0.68
amber_top = bc_bottom - GAP
amber_y0 = amber_top  # top edge, box drawn as (amber_y0 - AMBER_H) below
amber_box = FancyBboxPatch((0.35, amber_top - AMBER_H), 12.63, AMBER_H,
                            boxstyle="round,pad=0.02,rounding_size=0.1",
                            linewidth=1.6, edgecolor=AMBER, facecolor="#fff7e6", zorder=3)
ax.add_patch(amber_box)
ax.text(0.75, amber_y0 - 0.22, "\u26a0", ha="left", va="center", fontsize=16, color=AMBER, zorder=4)
ax.text(6.9, amber_y0 - 0.20,
        r"Disclosed correction: reaction acts on the $\mathit{logit}$ $u$, not the probability $s$  $\Rightarrow$  $ds/dt=\rho\,s^2(1-s)^2$  $\;\neq\;$  Fisher" + "\u2013" + r"KPP's  $\rho\,s(1-s)$",
        ha="center", va="center", fontsize=10.4, color="#5c4400", zorder=4)
ax.text(6.9, amber_y0 - 0.52, "(not hidden \u2014 verified and stated explicitly in the methodology audit)",
        ha="center", va="center", fontsize=8.6, color="#8a6d00", style="italic", zorder=4)

fig.savefig(r"D:\FOREST FIRE MAPPING(INDIA)\Manuscript_TGRS\figures\SlideCDR_Equation_Annotated.png",
            facecolor="white", bbox_inches=None, pad_inches=0)
print("saved")
