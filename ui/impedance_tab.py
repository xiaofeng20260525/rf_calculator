"""Impedance matching and Smith Chart tab with formulas and topology diagrams."""

import math
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.impedance import (
    l_match, single_stub_match, z_to_gamma,
)
from ..utils.constants import (
    vswr_to_rl, rl_to_vswr, vswr_to_gamma,
    gamma_to_vswr, gamma_to_rl, rl_to_gamma,
)
from .smith_chart import SmithChart
from .schematics import draw_l_match_topology, draw_stub_topology


class ImpedanceTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=3)
        top.pack(fill='both', expand=True)

        left = ttk.Frame(top, padding=3)
        left.pack(side='left', fill='y', padx=3, pady=3)

        right = ttk.Frame(top)
        right.pack(side='right', fill='both', expand=True, padx=3, pady=3)

        # --- Matching Network ---
        frm = ttk.Labelframe(left, text=' 阻抗匹配网络设计 ', padding=8, bootstyle='info')
        frm.pack(fill='x', pady=(0, 4))

        r0 = ttk.Frame(frm)
        r0.pack(fill='x', pady=2)
        ttk.Label(r0, text='负载阻抗 ZL:', width=14).pack(side='left')
        self.zl_real_var = ttk.StringVar(value='50')
        ttk.Entry(r0, textvariable=self.zl_real_var, width=7).pack(side='left')
        ttk.Label(r0, text=' + j').pack(side='left')
        self.zl_imag_var = ttk.StringVar(value='0')
        ttk.Entry(r0, textvariable=self.zl_imag_var, width=7).pack(side='left', padx=2)
        ttk.Label(r0, text=' Ω').pack(side='left')

        r1 = ttk.Frame(frm)
        r1.pack(fill='x', pady=2)
        ttk.Label(r1, text='频率:', width=14).pack(side='left')
        self.freq_var = ttk.StringVar(value='2450')
        ttk.Entry(r1, textvariable=self.freq_var, width=8).pack(side='left')
        self.freq_unit_var = ttk.StringVar(value='MHz')
        ttk.Combobox(r1, textvariable=self.freq_unit_var, values=['Hz', 'kHz', 'MHz', 'GHz'],
                     width=5, state='readonly', bootstyle='secondary').pack(side='left', padx=3)

        r2 = ttk.Frame(frm)
        r2.pack(fill='x', pady=2)
        ttk.Label(r2, text='系统阻抗 Z₀:', width=14).pack(side='left')
        self.z0_var = ttk.StringVar(value='50')
        ttk.Entry(r2, textvariable=self.z0_var, width=8).pack(side='left')
        ttk.Label(r2, text=' Ω').pack(side='left')

        bf = ttk.Frame(frm)
        bf.pack(fill='x', pady=5)
        ttk.Button(bf, text='L-Match 计算', command=self._calc_l_match, bootstyle='primary').pack(side='left', padx=2)
        ttk.Button(bf, text='Stub 计算', command=self._calc_stub, bootstyle='success').pack(side='left', padx=2)
        ttk.Button(bf, text='Smith图上显示', command=self._plot_on_smith, bootstyle='warning').pack(side='left', padx=2)

        self.match_result = ttk.Text(frm, height=7, width=46, font=('Consolas', 9))
        self.match_result.pack(fill='x', pady=2)

        # Formula inline below results
        fm1 = ttk.Labelframe(frm, text=' L-Match 公式 ', padding=4, bootstyle='secondary')
        fm1.pack(fill='x', pady=2)
        t1 = ttk.Text(fm1, height=5, width=44, font=('Consolas', 9), wrap='none')
        t1.pack(fill='x', padx=2, pady=2)
        t1.insert('end',
            'Q  = √(Z₀/R_L - 1)\n'
            'Xs = Q·R_L - X_L\n'
            'Bp = Q / Z₀\n'
            'L  = Xs / ω     (ω = 2πf)\n'
            'C  = 1 / (ω·Xs)')
        t1.config(state='disabled')

        # --- VSWR Converter ---
        conv = ttk.Labelframe(left, text=' VSWR / Return Loss / Γ 转换 ', padding=8, bootstyle='secondary')
        conv.pack(fill='x', pady=(0, 4))

        cf = ttk.Frame(conv)
        cf.pack(fill='x')
        for i, (label, key) in enumerate([
            ('VSWR:', 'vswr'), ('Return Loss (dB):', 'rl'), ('|Γ|:', 'gamma'),
        ]):
            ttk.Label(cf, text=label, width=16).grid(row=i, column=0, sticky='e', padx=3, pady=3)
            setattr(self, f'{key}_var', ttk.StringVar())
            e = ttk.Entry(cf, textvariable=getattr(self, f'{key}_var'), width=10)
            e.grid(row=i, column=1, padx=3, pady=3)
            e.bind('<KeyRelease>', lambda evt, s=key: self._convert_params(s))

        cfr = ttk.Frame(cf)
        cfr.grid(row=3, column=0, columnspan=2, sticky='w', padx=3, pady=5)
        ttk.Label(cfr, text='Mismatch Loss (dB):', width=16).pack(side='left')
        self.mismatch_var = ttk.StringVar()
        ttk.Entry(cfr, textvariable=self.mismatch_var, width=10, state='readonly').pack(side='left')

        # VSWR formula inline
        fm2 = ttk.Labelframe(conv, text=' 公式 ', padding=4, bootstyle='secondary')
        fm2.pack(fill='x', pady=2)
        t2 = ttk.Text(fm2, height=4, width=44, font=('Consolas', 9), wrap='none')
        t2.pack(fill='x', padx=2, pady=2)
        t2.insert('end',
            'VSWR = (1 + |Γ|) / (1 - |Γ|)\n'
            'RL   = -20·log₁₀(|Γ|)\n'
            '|Γ|  = (VSWR - 1) / (VSWR + 1)\n'
            'ML   = -10·log₁₀(1 - |Γ|²)')
        t2.config(state='disabled')

        # Smith Chart
        self.smith_chart = SmithChart(right, dark=True)

        # --- Bottom: Topology diagrams ---
        bottom = ttk.Frame(self, padding=3)
        bottom.pack(fill='both', expand=True)

        topo_frame = ttk.Labelframe(bottom, text=' 匹配网络拓扑示意 ', padding=5, bootstyle='primary')
        topo_frame.pack(fill='both', expand=True, padx=3)

        topo_tabs = ttk.Notebook(topo_frame, bootstyle='dark')
        topo_tabs.pack(fill='both', expand=True)

        tab1 = ttk.Frame(topo_tabs)
        topo_tabs.add(tab1, text=' L-Match Low-Pass ')
        draw_l_match_topology(tab1, 'low-pass')

        tab2 = ttk.Frame(topo_tabs)
        topo_tabs.add(tab2, text=' L-Match High-Pass ')
        draw_l_match_topology(tab2, 'high-pass')

        tab3 = ttk.Frame(topo_tabs)
        topo_tabs.add(tab3, text=' Single-Stub ')
        draw_stub_topology(tab3, 'shunt-open')

    def _get_freq_hz(self):
        try:
            f = float(self.freq_var.get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效频率数值'); return None
        return f * {'Hz': 1, 'kHz': 1e3, 'MHz': 1e6, 'GHz': 1e9}[self.freq_unit_var.get()]

    def _get_zload(self):
        try:
            return complex(float(self.zl_real_var.get()), float(self.zl_imag_var.get()))
        except ValueError:
            messagebox.showerror('Error', '请输入有效阻抗值'); return None

    def _get_z0(self):
        try: return float(self.z0_var.get())
        except ValueError: return 50.0

    def _calc_l_match(self):
        freq = self._get_freq_hz()
        if freq is None: return
        zl = self._get_zload()
        if zl is None: return
        z0 = self._get_z0()
        solutions = l_match(zl, z0, freq)
        self.match_result.delete('1.0', 'end')
        if not solutions:
            self.match_result.insert('end', '⚠ 无法找到有效L-Match方案\n'); return
        seen = set()
        for sol in solutions:
            key = (sol['series_value'], sol['shunt_value'])
            if key in seen: continue
            seen.add(key)
            self.match_result.insert('end', f'▸ 方案 {len(seen)}: {sol["topology"]}\n')
            self.match_result.insert('end', f'  串联: {sol["series_value"]} ({sol["series"][0]})\n')
            self.match_result.insert('end', f'  并联: {sol["shunt_value"]} ({sol["shunt"][0]})\n\n')

    def _calc_stub(self):
        freq = self._get_freq_hz()
        if freq is None: return
        zl = self._get_zload()
        if zl is None: return
        z0 = self._get_z0()
        solutions = single_stub_match(zl, z0, freq, 'shunt')
        self.match_result.delete('1.0', 'end')
        if not solutions:
            self.match_result.insert('end', '⚠ 无法找到有效Stub匹配方案\n'); return
        for sol in solutions:
            self.match_result.insert('end', f'▸ {sol["type"]}\n')
            self.match_result.insert('end', f'  距负载d: {sol["d_wavelengths"]:.4f}λ = {sol["d_mm_str"]}\n')
            self.match_result.insert('end', f'  Stub长l: {sol["l_wavelengths"]:.4f}λ = {sol["l_mm_str"]}\n')
            self.match_result.insert('end', f'  终端: {sol["stub_end"]}\n\n')

    def _plot_on_smith(self):
        zl = self._get_zload()
        if zl is None: return
        z0 = self._get_z0()
        gamma = z_to_gamma(zl, z0)
        vswr = gamma_to_vswr(abs(gamma))
        rl = gamma_to_rl(abs(gamma))
        self.smith_chart.clear_markers()
        self.smith_chart.plot_impedance(zl, f'{zl.real:.1f}+j{zl.imag:.1f}Ω', color='#00bc8c')
        if vswr < 100:
            self.smith_chart.plot_vswr_circle(vswr, color='#f39c12')
        self.match_result.delete('1.0', 'end')
        self.match_result.insert('end', f'▸ 负载: {zl.real:.2f}+j{zl.imag:.2f}Ω\n')
        self.match_result.insert('end', f'  Γ={gamma.real:.4f}+j{gamma.imag:.4f}  VSWR={vswr:.3f}  RL={rl:.2f}dB\n')

    def _convert_params(self, source):
        try:
            if source == 'vswr':
                vswr = float(self.vswr_var.get())
                rl = vswr_to_rl(vswr); gamma = vswr_to_gamma(vswr)
            elif source == 'rl':
                rl = float(self.rl_var.get())
                vswr = rl_to_vswr(rl); gamma = rl_to_gamma(rl)
            elif source == 'gamma':
                gamma = float(self.gamma_var.get())
                vswr = gamma_to_vswr(gamma); rl = gamma_to_rl(gamma)
            else: return
        except (ValueError, ZeroDivisionError): return
        if source != 'vswr': self.vswr_var.set(f'{vswr:.4f}')
        if source != 'rl': self.rl_var.set(f'{rl:.2f}')
        if source != 'gamma': self.gamma_var.set(f'{gamma:.4f}')
        if abs(gamma) < 1:
            self.mismatch_var.set(f'{-10*math.log10(1-gamma**2):.2f}')
        else:
            self.mismatch_var.set('N/A')
