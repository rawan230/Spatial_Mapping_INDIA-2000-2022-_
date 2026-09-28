"""Combined slide graphic: CDR governing equation + the three physics-head MLP
architectures (Diffusion, Advection, Reaction), drawn exactly as implemented in
Physics_Informed_FireRisk_Model/cdr_pinn/model.py (DiffusivityHead, AdvectionHead,
ReactionHead). 16:9, ready to drop into one PowerPoint slide.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

plt.rcParams.update({"font.family": "DejaVu Sans"})

FIG_W, FIG_H = 14.0, 7.9
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=170)
fig.patch.set_facecolor("white")

COL = {"diff": "#2166ac", "adv": "#1a7a35", "react": "#c0392b",
       "in": "#eaf2fb", "hid": "#eeeeee", "out_fill": "#ffffff"}

# ------------------------------------------------------------------ #
# Top banner: title + governing equation + 3-way group mapping
# ------------------------------------------------------------------ #
ax_top = fig.add_axes([0.0, 0.80, 1.0, 0.20])
ax_top.axis("off")
ax_top.text(0.5, 0.86, "CDR Governing Equation \u2192 Physics-Head Architectures",
            ha="center", va="top", fontsize=19, fontweight="bold")
ax_top.text(0.5, 0.46,
            r"$\frac{\partial u}{\partial t} = D\,\nabla^2 u \;-\; \mathbf{v}\cdot\nabla u \;+\; \rho\,\sigma(u)\left(1-\sigma(u)\right)$",
            ha="center", va="center", fontsize=17)
ax_top.text(0.165, 0.04, "Diffusion $D$ \u2190 vegetation + climate  (Fisher\u2013KPP)",
            ha="center", va="center", fontsize=10.5, color=COL["diff"], fontweight="bold")
ax_top.text(0.5, 0.04, "Advection $\\mathbf{v}$ \u2190 terrain  (Rothermel 1972, upslope)",
            ha="center", va="center", fontsize=10.5, color=COL["adv"], fontweight="bold")
ax_top.text(0.835, 0.04, "Reaction $\\rho$ \u2190 human activity  (logistic ignition)",
            ha="center", va="center", fontsize=10.5, color=COL["react"], fontweight="bold")
ax_top.axhline(0.16, color="#cccccc", lw=0.8, xmin=0.02, xmax=0.98)


def draw_mlp(ax, color, title, in_labels, hidden_sizes, hidden_act, post_lines, out_label):
    """Draw a fully-connected MLP: input labels -> hidden layers (circles) -> output,
    with a post-processing note stacked below the network."""
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.text(5, 9.7, title, ha="center", va="top", fontsize=13.5, fontweight="bold", color=color)

    n_in = len(in_labels)
    layer_x = [1.3, 4.0, 6.7, 9.1]  # input, hidden1, hidden2, output
    max_n = max(n_in, *hidden_sizes, 1)
    y_top, y_bot = 8.6, 1.3
    span = y_top - y_bot

    def ys(n):
        if n == 1:
            return [(y_top + y_bot) / 2]
        step = span / (max_n - 1) if max_n > 1 else 0
        total_h = step * (n - 1)
        start = (y_top + y_bot) / 2 + total_h / 2
        return [start - i * step for i in range(n)]

    in_y = ys(n_in)
    h1_y = ys(hidden_sizes[0])
    h2_y = ys(hidden_sizes[1])
    out_y = ys(1)

    r_in, r_hid, r_out = 0.34, 0.24, 0.4

    # connections (draw first, behind nodes)
    for ya in in_y:
        for yb in h1_y:
            ax.add_line(Line2D([layer_x[0] + r_in, layer_x[1] - r_hid], [ya, yb],
                                color=color, alpha=0.14, lw=0.6, zorder=1))
    for ya in h1_y:
        for yb in h2_y:
            ax.add_line(Line2D([layer_x[1] + r_hid, layer_x[2] - r_hid], [ya, yb],
                                color=color, alpha=0.14, lw=0.6, zorder=1))
    for ya in h2_y:
        for yb in out_y:
            ax.add_line(Line2D([layer_x[2] + r_hid, layer_x[3] - r_out], [ya, yb],
                                color=color, alpha=0.30, lw=0.9, zorder=1))

    # input nodes + labels
    for y, lab in zip(in_y, in_labels):
        ax.add_patch(Circle((layer_x[0], y), r_in, facecolor=COL["in"], edgecolor=color, lw=1.3, zorder=2))
        ax.text(layer_x[0] - 0.55, y, lab, ha="right", va="center", fontsize=9.2)

    # hidden layers
    for y in h1_y:
        ax.add_patch(Circle((layer_x[1], y), r_hid, facecolor=COL["hid"], edgecolor="#888888", lw=0.9, zorder=2))
    for y in h2_y:
        ax.add_patch(Circle((layer_x[2], y), r_hid, facecolor=COL["hid"], edgecolor="#888888", lw=0.9, zorder=2))
    # output node
    for y in out_y:
        ax.add_patch(Circle((layer_x[3], y), r_out, facecolor=color, edgecolor=color, lw=1.3, alpha=0.85, zorder=3))
        ax.text(layer_x[3], y, "z", ha="center", va="center", fontsize=9.5, color="white", fontweight="bold", zorder=4)

    # single-line header row above the network (avoids any collision with the box below)
    header_y = y_top + 0.62
    ax.text(layer_x[0], header_y, "Inputs", ha="center", va="center", fontsize=8.4, color="#555555")
    ax.text(layer_x[1], header_y, f"H1: {hidden_sizes[0]} ({hidden_act})", ha="center", va="center", fontsize=7.8, color="#555555")
    ax.text(layer_x[2], header_y, f"H2: {hidden_sizes[1]} ({hidden_act})", ha="center", va="center", fontsize=7.8, color="#555555")
    ax.text(layer_x[3], header_y, "Output", ha="center", va="center", fontsize=8.4, color="#555555")

    # post-processing box under the network
    box_y0 = 0.05
    ax.add_patch(Rectangle((0.4, box_y0), 9.2, 1.0, facecolor="#f7f7f7", edgecolor=color, lw=1.0, zorder=2))
    for i, line in enumerate(post_lines):
        ax.text(5, box_y0 + 0.72 - i * 0.42, line, ha="center", va="center", fontsize=9.6)


# ------------------------------------------------------------------ #
# Three panels: Diffusion (full MLP), Advection (not an MLP), Reaction (full MLP)
# ------------------------------------------------------------------ #
ax_d = fig.add_axes([0.015, 0.02, 0.315, 0.76])
draw_mlp(ax_d, COL["diff"], "Diffusion head  $D(x,y,t)$",
         in_labels=["NDVI mean", "Forest frac."],
         hidden_sizes=(12, 12), hidden_act="tanh",
         post_lines=[r"$z \leftarrow z - \mathrm{softplus}(w)\cdot\mathrm{NDVI}'$",
                     r"$D = \mathrm{softplus}(z) \;>\; 0$"],
         out_label="z")

# Advection: deliberately NOT an MLP -- draw its own simple diagram
ax_a = fig.add_axes([0.345, 0.02, 0.31, 0.76])
ax_a.set_xlim(0, 10); ax_a.set_ylim(0, 10); ax_a.axis("off")
ax_a.text(5, 9.7, "Advection head  $\\mathbf{v}(x,y)$", ha="center", va="top",
          fontsize=13.5, fontweight="bold", color=COL["adv"])
ax_a.add_patch(Circle((2.0, 5.3), 0.85, facecolor=COL["in"], edgecolor=COL["adv"], lw=1.5))
ax_a.text(2.0, 5.3, r"$\nabla E$", ha="center", va="center", fontsize=13)
ax_a.text(2.0, 6.55, "Elevation\ngradient", ha="center", va="center", fontsize=9, color="#555555")
ax_a.annotate("", xy=(4.55, 5.3), xytext=(2.95, 5.3),
              arrowprops=dict(arrowstyle="-|>", color=COL["adv"], lw=2.2))
ax_a.add_patch(Circle((5.4, 5.3), 0.62, facecolor=COL["adv"], edgecolor=COL["adv"], lw=1.3, alpha=0.85))
ax_a.text(5.4, 5.3, "$\\times c$", ha="center", va="center", fontsize=11, color="white", fontweight="bold")
ax_a.annotate("", xy=(7.9, 5.3), xytext=(6.1, 5.3),
              arrowprops=dict(arrowstyle="-|>", color=COL["adv"], lw=2.2))
ax_a.text(8.6, 5.3, r"$\mathbf{v}$", ha="center", va="center", fontsize=15, fontweight="bold", color=COL["adv"])
ax_a.text(5.4, 3.85, "$c = \\mathrm{softplus}(c_{\\mathrm{raw}})$", ha="center", fontsize=10.5)
ax_a.text(5.4, 3.2, "1 learned scalar parameter\n(no hidden layers)", ha="center", fontsize=9.3, color="#555555")
ax_a.add_patch(Rectangle((0.4, 0.05), 9.2, 1.5, facecolor="#f7f7f7", edgecolor=COL["adv"], lw=1.0))
ax_a.text(5, 1.15, "Direction fixed by physics (always upslope,\nRothermel 1972) \u2014 only strength $c$ is learned",
          ha="center", va="center", fontsize=9.6)

ax_r = fig.add_axes([0.675, 0.02, 0.315, 0.76])
draw_mlp(ax_r, COL["react"], "Reaction head  $\\rho(x,y,t)$",
         in_labels=["Dryness", "NDVI mean", "Slope", "Dist. to roads"],
         hidden_sizes=(12, 12), hidden_act="tanh",
         post_lines=[r"$\rho = \mathrm{softplus}(z) \;>\; 0$",
                     r"$R = \rho\cdot\sigma(u)(1-\sigma(u))$"],
         out_label="z")

fig.savefig(r"D:\FOREST FIRE MAPPING(INDIA)\Manuscript_TGRS\figures\SlideCDR_MLP_Architecture.png",
            facecolor="white", bbox_inches="tight", pad_inches=0.15)
print("saved")
