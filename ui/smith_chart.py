"""Smith Chart widget using matplotlib embedded in ttkbootstrap."""

import math
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as patches


# Dark chart color scheme
class SmithChart:
    """Interactive Smith Chart for impedance visualization."""

    def __init__(self, parent_frame, figsize=(5.5, 5.5), dpi=100, dark=True):
        self.dark = dark
        if dark:
            self.bg = '#2b3e50'
            self.fg = '#ced4da'
            self.grid_color = '#375a7f'
            self.grid_alpha = 0.7
            self.res_color = '#3a7bd5'
            self.react_color = '#e74c3c'
            # These are overridden in draw
        else:
            self.bg = 'white'
            self.fg = '#333333'
            self.grid_color = '#888888'
            self.grid_alpha = 0.5
            self.res_color = '#2166ac'
            self.react_color = '#d73027'

        self.figure = Figure(figsize=figsize, dpi=dpi, facecolor=self.bg)
        self.axes = self.figure.add_subplot(111, facecolor=self.bg)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)

        self.z0 = 50.0
        self.markers = []
        self._draw_chart()

    def _draw_chart(self):
        ax = self.axes
        ax.clear()
        ax.set_aspect('equal')
        ax.set_xlim(-1.15, 1.15)
        ax.set_ylim(-1.15, 1.15)
        ax.axis('off')
        ax.set_facecolor(self.bg)

        # Unit circle
        circ = patches.Circle((0, 0), 1, fill=False, edgecolor=self.fg,
                              linewidth=1.8, zorder=2)
        ax.add_patch(circ)

        # Crosshair
        ax.axhline(y=0, color=self.fg, linewidth=0.6, alpha=0.4, zorder=1)
        ax.axvline(x=0, color=self.fg, linewidth=0.6, alpha=0.4, zorder=1)

        # Constant resistance circles
        for r in [0.2, 0.5, 1, 2, 5]:
            cx = r / (1 + r)
            r_radius = 1 / (1 + r)
            c = patches.Circle((cx, 0), r_radius, fill=False,
                               edgecolor=self.res_color, linewidth=0.4, alpha=self.grid_alpha)
            ax.add_patch(c)

        # Constant reactance arcs
        for x in [0.2, 0.5, 1, 2, 5]:
            self._add_x_arc(ax, x, True)
            self._add_x_arc(ax, x, False)

        # Labels
        self._add_labels(ax)
        self.canvas.draw()

    def _add_x_arc(self, ax, x_val, positive):
        if x_val == 0:
            return
        cx = 0
        cy = 1 / x_val if positive else -1 / x_val
        arc_radius = 1 / abs(x_val)

        if positive:
            theta1, theta2 = 0, math.pi
        else:
            theta1, theta2 = math.pi, 2 * math.pi

        # The arc is the top half (positive) or bottom half (negative) of the circle
        arc = patches.Arc((cx, cy), 2 * arc_radius, 2 * arc_radius,
                          fill=False, edgecolor=self.react_color,
                          linewidth=0.4, alpha=self.grid_alpha,
                          theta1=0, theta2=360)
        if arc_radius < 20:
            ax.add_patch(arc)

    def _add_labels(self, ax):
        c = self.fg
        ax.annotate('OPEN', xy=(1, 0), fontsize=9, ha='center', va='bottom',
                    color=c, fontweight='bold', xytext=(0, -12),
                    textcoords='offset points')
        ax.annotate('SHORT', xy=(-1, 0), fontsize=9, ha='center', va='top',
                    color=c, fontweight='bold', xytext=(0, 12),
                    textcoords='offset points')
        ax.annotate('Z₀', xy=(0, 0), fontsize=9, ha='center', va='bottom',
                    color='#00bc8c', fontweight='bold', xytext=(0, -12),
                    textcoords='offset points')
        ax.annotate('+jX', xy=(0.05, 0.6), fontsize=8, ha='center', va='center',
                    color=self.react_color, alpha=0.6, fontstyle='italic')
        ax.annotate('-jX', xy=(0.05, -0.6), fontsize=8, ha='center', va='center',
                    color=self.react_color, alpha=0.6, fontstyle='italic')
        ax.annotate('R', xy=(0.5, 0.04), fontsize=8, ha='center', va='center',
                    color=self.res_color, alpha=0.6, fontstyle='italic')

    def plot_impedance(self, z, label=None, color='#00bc8c', marker_size=100):
        gamma = (z - self.z0) / (z + self.z0)
        self.plot_gamma(gamma, label, color, marker_size)

    def plot_gamma(self, gamma, label=None, color='#00bc8c', marker_size=100):
        x, y = gamma.real, gamma.imag
        marker = self.axes.scatter([x], [y], c=color, s=marker_size, zorder=5,
                                   edgecolors='white', linewidth=0.8)
        self.markers.append(marker)
        if label:
            self.axes.annotate(label, (x, y), fontsize=9, fontweight='bold',
                               textcoords="offset points", xytext=(8, 8),
                               color=color, bbox=dict(boxstyle='round,pad=0.3',
                               facecolor=self.bg, edgecolor=color, alpha=0.8))
        self.canvas.draw()

    def plot_vswr_circle(self, vswr, color='#f39c12', alpha=0.7):
        gamma = (vswr - 1) / (vswr + 1)
        c = patches.Circle((0, 0), gamma, fill=False, edgecolor=color,
                           linewidth=1, linestyle='--', alpha=alpha)
        self.axes.add_patch(c)
        self.canvas.draw()

    def clear_markers(self):
        for m in self.markers:
            m.remove()
        self.markers.clear()
        # Remove non-base annotations and extra patches (keep base grid)
        for child in list(self.axes.get_children()):
            if isinstance(child, matplotlib.text.Annotation):
                fs = child.get_fontsize()
                if fs not in (8, 9):
                    child.remove()
            elif isinstance(child, patches.Circle):
                # Remove VSWR circles and plotted markers (keep base unit circle)
                ls = child.get_linestyle()
                if ls == '--':
                    child.remove()
            elif isinstance(child, matplotlib.collections.PathCollection):
                # Remove scatter markers (already done above)
                pass
        self.canvas.draw()

    def clear_all(self):
        self.markers.clear()
        self._draw_chart()
