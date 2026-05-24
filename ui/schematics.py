"""Schematic drawings — ultra-compact at 30% scale."""

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import math

DARK_BG = '#2b3e50'
SUBSTRATE = '#34495e'
GROUND = '#bdc3c7'
TRACE = '#f39c12'
TEXT_COLOR = '#dfe4ea'


def _make_figure(parent, figsize=(1.8, 1.4), dpi=100):
    fig = Figure(figsize=figsize, dpi=dpi, facecolor=DARK_BG)
    ax = fig.add_subplot(111, facecolor=DARK_BG)
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().pack(fill='both', expand=True, padx=1, pady=1)
    return ax, canvas


def draw_microstrip(parent, w_mm=3.0, h_mm=1.575, t_mm=0.035, er=4.4):
    ax, canvas = _make_figure(parent)
    sc = 1.8; W = w_mm*sc; H = h_mm*sc; mg = 0.4; T = 0.05

    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, H, facecolor=SUBSTRATE, edgecolor='#4a6785', lw=0.8))
    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, 0.06, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))
    ax.add_patch(mpatches.Rectangle((W*0.1, H), W*0.8, T, facecolor=TRACE, edgecolor='#e67e22', lw=0.6))

    ax.text(W/2, H/2, f'er={er}', color=TEXT_COLOR, fontsize=5, ha='center', va='center', alpha=0.6)
    ax.text(W/2, -0.15, 'GND', color=GROUND, fontsize=4, ha='center')
    ax.set_xlim(-mg-0.5, W+mg+0.5)
    ax.set_ylim(-0.4, H+T+0.3)
    ax.set_aspect('equal'); ax.axis('off'); canvas.draw()


def draw_stripline(parent, w_mm=0.5, h_mm=1.6, er=4.4):
    ax, canvas = _make_figure(parent)
    sc = 2.0; W = w_mm*sc; H = h_mm*sc; mg = 0.4; th = 0.05

    ax.add_patch(mpatches.Rectangle((-mg, H/2), W+2*mg, H/2, facecolor=SUBSTRATE, edgecolor='#4a6785', lw=0.8))
    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, H/2, facecolor=SUBSTRATE, edgecolor='#4a6785', lw=0.8))
    ax.add_patch(mpatches.Rectangle((-mg, H), W+2*mg, th, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))
    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, th, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))

    ty = H/2 - 0.03
    ax.add_patch(mpatches.Rectangle((W*0.1, ty), W*0.8, th, facecolor=TRACE, edgecolor='#e67e22', lw=0.6))
    ax.text(W/2, H*0.7, f'er={er}', color=TEXT_COLOR, fontsize=5, ha='center', alpha=0.6)
    ax.text(W/2, -0.1, 'GND', color=GROUND, fontsize=4, ha='center')
    ax.text(W/2, H+0.1, 'GND', color=GROUND, fontsize=4, ha='center')
    ax.set_xlim(-mg-0.5, W+mg+0.5)
    ax.set_ylim(-0.3, H+0.3)
    ax.set_aspect('equal'); ax.axis('off'); canvas.draw()


def draw_cpw(parent, w_mm=0.5, s_mm=0.2, h_mm=1.6, er=4.4):
    ax, canvas = _make_figure(parent)
    sc = 2.0; gap = 0.15; W = w_mm*sc; S = s_mm*sc; H = h_mm*sc; mg = 0.5
    total_w = W + 2*S + 2*gap; yt = 0.9

    ax.add_patch(mpatches.Rectangle((-mg, 0), total_w+2*mg, H, facecolor=SUBSTRATE, edgecolor='#4a6785', lw=0.8))
    lgx = -mg + 0.15; lgw = gap
    ax.add_patch(mpatches.Rectangle((lgx, yt-0.03), lgw+S, 0.05, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))
    tx = lgx + lgw + S
    ax.add_patch(mpatches.Rectangle((tx, yt-0.03), W, 0.05, facecolor=TRACE, edgecolor='#e67e22', lw=0.6))
    rgx = tx + W + S
    ax.add_patch(mpatches.Rectangle((rgx, yt-0.03), gap+S, 0.05, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))
    ax.text(lgx+lgw/2, yt+0.08, 'G', color=GROUND, fontsize=4, ha='center')
    ax.text(rgx+gap/2, yt+0.08, 'G', color=GROUND, fontsize=4, ha='center')
    ax.text(total_w/2, H/2, f'er={er}', color=TEXT_COLOR, fontsize=5, ha='center', alpha=0.5)
    ax.set_xlim(-mg, total_w+mg)
    ax.set_ylim(-0.1, H+0.1)
    ax.set_aspect('equal'); ax.axis('off'); canvas.draw()


def draw_l_match_topology(parent, topology='low-pass'):
    ax, canvas = _make_figure(parent, figsize=(2.0, 1.2))
    ym = 0; xs, x1, x2, x3 = -1.5, -0.6, 0.2, 1.2
    ax.plot([xs, x1, x2, x3], [ym, ym, ym, ym], color=TEXT_COLOR, lw=1.2)
    cs = '#00bc8c'
    if topology == 'low-pass':
        for j in range(3):
            ax.add_patch(mpatches.Arc((x1+0.08+j*0.15, ym), 0.18, 0.14, angle=0, theta1=90, theta2=270, color=cs, lw=1))
    else:
        ax.plot([x1+0.06, x1+0.06], [ym-0.1, ym+0.1], color='#e74c3c', lw=1.2)
        ax.plot([x1+0.25, x1+0.25], [ym-0.1, ym+0.1], color='#e74c3c', lw=1.2)
    ax.plot([x2, x2], [ym, -0.4], color=TEXT_COLOR, lw=1.2)
    if topology == 'low-pass':
        ax.plot([x2-0.1, x2-0.1], [-0.3, -0.12], color='#e74c3c', lw=1.2)
        ax.plot([x2+0.1, x2+0.1], [-0.3, -0.12], color='#e74c3c', lw=1.2)
    else:
        for j in range(2):
            ax.add_patch(mpatches.Arc((x2, -0.2+j*0.12), 0.18, 0.14, angle=0, theta1=0, theta2=180, color=cs, lw=1))
    ax.plot([x2-0.3, x2+0.3], [-0.42, -0.42], color=GROUND, lw=1)
    ax.plot([x2-0.15, x2+0.15], [-0.52, -0.52], color=GROUND, lw=0.8)
    ax.scatter([xs, x3], [ym, ym], c='#3498db', s=15, zorder=3)
    ax.set_xlim(-1.8, 1.8); ax.set_ylim(-0.8, 0.4)
    ax.set_aspect('equal'); ax.axis('off'); canvas.draw()


def draw_stub_topology(parent, stub_type='shunt-open'):
    ax, canvas = _make_figure(parent, figsize=(2.2, 1.3))
    ym = 0; xl, xst, xsrc = 1.6, 0.1, -1.6
    ax.plot([xsrc, xst, xl], [ym, ym, ym], color=TEXT_COLOR, lw=1.2)
    ax.plot([xst, xst], [ym, -0.1], color=TEXT_COLOR, lw=1.2)
    ax.plot([xst-0.06, xst+0.06], [-0.1, -0.55], color='#00bc8c', lw=1.2)
    ax.plot([xst-0.06, xst+0.06], [-0.55, -0.55], color='#00bc8c', lw=1.2)
    ax.scatter([xl], [ym], c='#3498db', s=15, zorder=3)
    ax.set_xlim(-2.0, 2.0); ax.set_ylim(-0.9, 0.3)
    ax.set_aspect('equal'); ax.axis('off'); canvas.draw()


def draw_microstrip_loss(parent, w_mm=3.0, h_mm=1.575, tand=0.02, roughness_um=0.4):
    ax, canvas = _make_figure(parent, figsize=(1.8, 1.3))
    sc = 1.6; W = w_mm*sc; H = h_mm*sc; mg = 0.3; T = 0.04
    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, H, facecolor=SUBSTRATE, edgecolor='#4a6785', lw=0.8))
    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, 0.05, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))
    ax.add_patch(mpatches.Rectangle((W*0.1, H), W*0.8, T, facecolor=TRACE, edgecolor='#e67e22', lw=0.6))
    for px in [W*0.3, W*0.5, W*0.7]:
        ax.annotate('', xy=(px, H+T), xytext=(px, H+T+0.08),
                    arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=0.8))
    ax.text(W/2, H+T+0.18, 'ac', color='#e74c3c', fontsize=4, ha='center')
    ax.text(W/2, H*0.55, 'ad', color='#3498db', fontsize=4, ha='center')
    ax.text(W/2, -0.1, 'GND', color=GROUND, fontsize=4, ha='center')
    ax.set_xlim(-mg-0.3, W+mg+0.3)
    ax.set_ylim(-0.3, H+T+0.35)
    ax.set_aspect('equal'); ax.axis('off'); canvas.draw()


def draw_stripline_loss(parent, w_mm=0.5, h_mm=1.6, tand=0.02, roughness_um=0.4):
    ax, canvas = _make_figure(parent, figsize=(1.8, 1.3))
    sc = 1.8; W = w_mm*sc; H = h_mm*sc; mg = 0.3; th = 0.04
    ax.add_patch(mpatches.Rectangle((-mg, H/2), W+2*mg, H/2, facecolor=SUBSTRATE, edgecolor='#4a6785', lw=0.8))
    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, H/2, facecolor=SUBSTRATE, edgecolor='#4a6785', lw=0.8))
    ax.add_patch(mpatches.Rectangle((-mg, H), W+2*mg, th, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))
    ax.add_patch(mpatches.Rectangle((-mg, 0), W+2*mg, th, facecolor=GROUND, edgecolor='#95a5a6', lw=0.4))
    ty = H/2 - 0.02
    ax.add_patch(mpatches.Rectangle((W*0.1, ty), W*0.8, th, facecolor=TRACE, edgecolor='#e67e22', lw=0.6))
    for px in [W*0.3, W*0.5, W*0.7]:
        ax.annotate('', xy=(px, ty+th), xytext=(px, ty+th+0.1),
                    arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=0.8))
    ax.text(W/2, ty+th+0.18, 'ac', color='#e74c3c', fontsize=4, ha='center')
    ax.text(W/2, H*0.7, 'ad', color='#3498db', fontsize=4, ha='center')
    ax.text(W/2, -0.1, 'GND', color=GROUND, fontsize=4, ha='center')
    ax.text(W/2, H+0.1, 'GND', color=GROUND, fontsize=4, ha='center')
    ax.set_xlim(-mg-0.3, W+mg+0.3)
    ax.set_ylim(-0.3, H+0.3)
    ax.set_aspect('equal'); ax.axis('off'); canvas.draw()