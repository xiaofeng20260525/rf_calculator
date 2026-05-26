"""Link budget and free-space path loss tab."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.link_budget import (
    free_space_path_loss, link_budget, max_range,
)


class LinkBudgetTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        for r in range(1):
            self.grid_rowconfigure(r, weight=1)
        for c in range(2):
            self.grid_columnconfigure(c, weight=1, uniform='lb')

        self._build_link_budget(0, 0)
        self._build_fspl(0, 1)

    # ==================== Link Budget ====================
    def _build_link_budget(self, r, c):
        sec = ttk.Labelframe(self, text=' 链路预算 ', padding=8, bootstyle='info')
        sec.grid(row=r, column=c, sticky='nsew', padx=3, pady=3)

        self.lb_vars = {}
        gf = ttk.Frame(sec); gf.pack(fill='x')

        items = [
            ('TX 功率 (dBm):',      'tx_power',      '30'),
            ('TX 天线增益 (dBi):',   'tx_ant_gain',   '2'),
            ('TX 线缆损耗 (dB):',    'tx_cable_loss', '1'),
            ('频率:',               'freq',          '2450'),
            ('距离:',               'distance',      '1000'),
            ('RX 天线增益 (dBi):',   'rx_ant_gain',   '2'),
            ('RX 线缆损耗 (dB):',    'rx_cable_loss', '1'),
            ('额外裕量 (dB):',      'margin',        '0'),
            ('RX 灵敏度 (dBm):',    'rx_sens',       '-90'),
        ]

        for i, (label, key, default) in enumerate(items):
            ttk.Label(gf, text=label, width=20, anchor='e').grid(row=i, column=0, sticky='e', padx=4, pady=3)
            self.lb_vars[key] = ttk.StringVar(value=default)
            ttk.Entry(gf, textvariable=self.lb_vars[key], width=13).grid(row=i, column=1, sticky='w', padx=4, pady=3)

        self.lb_freq_unit = ttk.StringVar(value='MHz')
        ttk.Combobox(gf, textvariable=self.lb_freq_unit, values=['Hz','kHz','MHz','GHz'],
                     width=5, state='readonly', bootstyle='secondary').grid(row=3, column=2, padx=3)

        self.lb_dist_unit = ttk.StringVar(value='m')
        ttk.Combobox(gf, textvariable=self.lb_dist_unit, values=['m','km'],
                     width=4, state='readonly', bootstyle='secondary').grid(row=4, column=2, padx=3)

        ttk.Separator(sec, bootstyle='secondary').pack(fill='x', pady=8)
        bf = ttk.Frame(sec); bf.pack(fill='x')
        ttk.Button(bf, text='计算链路预算', command=self._calc_link_budget, bootstyle='primary', width=14).pack(side='left', padx=3)
        ttk.Button(bf, text='计算最大距离', command=self._calc_max_range, bootstyle='warning', width=14).pack(side='left', padx=3)

        self.lb_result = ttk.Text(sec, height=10, width=44, font=('Consolas', 10))
        self.lb_result.pack(fill='x', pady=8)

        fm = ttk.Labelframe(sec, text=' 公式 ', padding=3, bootstyle='secondary'); fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=44, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=3, pady=2)
        ft.insert('end',
            'EIRP = Ptx + Gtx - Ltx_cable\n'
            'FSPL = 20 * log10(4*pi*d / lambda)\n'
            '     = 32.44 + 20*log10(d_km) + 20*log10(f_MHz)\n'
            'Prx  = EIRP - FSPL + Grx - Lrx_cable - Margin')
        ft.config(state='disabled')

    # ==================== FSPL ====================
    def _build_fspl(self, r, c):
        sec = ttk.Labelframe(self, text=' 自由空间路径损耗 (FSPL) ', padding=8, bootstyle='primary')
        sec.grid(row=r, column=c, sticky='nsew', padx=3, pady=3)

        gf = ttk.Frame(sec); gf.pack(fill='x')

        f1 = ttk.Frame(gf); f1.pack(fill='x', pady=4)
        ttk.Label(f1, text='频率:', width=12, anchor='e').pack(side='left', padx=3)
        self.fspl_freq_var = ttk.StringVar(value='2450')
        ttk.Entry(f1, textvariable=self.fspl_freq_var, width=13).pack(side='left', padx=3)
        self.fspl_freq_unit = ttk.StringVar(value='MHz')
        ttk.Combobox(f1, textvariable=self.fspl_freq_unit, values=['Hz','kHz','MHz','GHz'],
                     width=5, state='readonly', bootstyle='secondary').pack(side='left', padx=3)

        f2 = ttk.Frame(gf); f2.pack(fill='x', pady=4)
        ttk.Label(f2, text='距离:', width=12, anchor='e').pack(side='left', padx=3)
        self.fspl_dist_var = ttk.StringVar(value='1')
        ttk.Entry(f2, textvariable=self.fspl_dist_var, width=13).pack(side='left', padx=3)
        self.fspl_dist_unit = ttk.StringVar(value='km')
        ttk.Combobox(f2, textvariable=self.fspl_dist_unit, values=['m','km'],
                     width=4, state='readonly', bootstyle='secondary').pack(side='left', padx=3)

        ttk.Separator(sec, bootstyle='secondary').pack(fill='x', pady=8)
        ttk.Button(sec, text='计算 FSPL', command=self._calc_fspl, bootstyle='primary', width=14).pack(pady=2)

        self.fspl_result = ttk.Text(sec, height=5, width=44, font=('Consolas', 10))
        self.fspl_result.pack(fill='x', pady=8)

        fm = ttk.Labelframe(sec, text=' 公式 ', padding=3, bootstyle='secondary'); fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=44, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=3, pady=2)
        ft.insert('end',
            'FSPL = (4*pi*d / lambda)^2\n'
            'FSPL(dB) = 20 * log10(4*pi*d / lambda)\n'
            '        = 32.44 + 20*log10(d_km) + 20*log10(f_MHz)\n'
            'lambda = c / f,   c = 3e8 m/s')
        ft.config(state='disabled')

        # Quick reference table
        ref = ttk.Labelframe(sec, text=' 速查: FSPL 典型值 ', padding=3, bootstyle='secondary'); ref.pack(fill='x', pady=3)
        rt = ttk.Text(ref, height=6, width=44, font=('Consolas', 8))
        rt.pack(fill='x', padx=3, pady=2)
        rt.insert('end',
            '  距离          1GHz      2.4GHz     5GHz      10GHz\n'
            '  ' + '-' * 52 + '\n'
            '  1 m           32 dB     40 dB     46 dB     52 dB\n'
            '  10 m          52 dB     60 dB     66 dB     72 dB\n'
            '  100 m         72 dB     80 dB     86 dB     92 dB\n'
            '  1 km          92 dB    100 dB    106 dB    112 dB\n'
            '  10 km        112 dB    120 dB    126 dB    132 dB')
        rt.config(state='disabled')

    # ==================== Calc methods ====================

    def _get_freq_hz(self, var, unit_var):
        try:
            return float(var.get()) * {'Hz':1,'kHz':1e3,'MHz':1e6,'GHz':1e9}[unit_var.get()]
        except ValueError:
            return None

    def _calc_link_budget(self):
        try:
            tx_power = float(self.lb_vars['tx_power'].get())
            tx_gain = float(self.lb_vars['tx_ant_gain'].get())
            tx_loss = float(self.lb_vars['tx_cable_loss'].get())
            rx_gain = float(self.lb_vars['rx_ant_gain'].get())
            rx_loss = float(self.lb_vars['rx_cable_loss'].get())
            margin = float(self.lb_vars['margin'].get())
            dist = float(self.lb_vars['distance'].get())
            rx_sens = float(self.lb_vars['rx_sens'].get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效数值'); return

        freq_hz = self._get_freq_hz(self.lb_vars['freq'], self.lb_freq_unit)
        if freq_hz is None: return
        dist_m = dist * 1000 if self.lb_dist_unit.get() == 'km' else dist

        result = link_budget(tx_power, tx_gain, dist_m, freq_hz, rx_gain, tx_loss, rx_loss, margin)
        d_range = max_range(tx_power, tx_gain, freq_hz, rx_gain, rx_sens, tx_loss, rx_loss, margin)

        self.lb_result.delete('1.0', 'end')
        self.lb_result.insert('end',
            f'  EIRP    = {result["tx_eirp_dbm"]:.2f} dBm\n'
            f'  FSPL    = {result["fspl_db"]:.2f} dB\n'
            f'  Prx     = {result["rx_power_dbm"]:.2f} dBm\n'
            f'          = {result["rx_power_watt"]*1e9:.4f} nW\n'
            f'          = {result["rx_power_watt"]*1e6:.4f} uW\n\n'
            f'  Max Range (基于 {rx_sens}dBm 灵敏度):\n'
            f'  {d_range:.1f} m  = {d_range/1e3:.3f} km\n')

    def _calc_max_range(self):
        try:
            tx_power = float(self.lb_vars['tx_power'].get())
            tx_gain = float(self.lb_vars['tx_ant_gain'].get())
            tx_loss = float(self.lb_vars['tx_cable_loss'].get())
            rx_gain = float(self.lb_vars['rx_ant_gain'].get())
            rx_loss = float(self.lb_vars['rx_cable_loss'].get())
            margin = float(self.lb_vars['margin'].get())
            rx_sens = float(self.lb_vars['rx_sens'].get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效数值'); return

        freq_hz = self._get_freq_hz(self.lb_vars['freq'], self.lb_freq_unit)
        if freq_hz is None: return
        d_m = max_range(tx_power, tx_gain, freq_hz, rx_gain, rx_sens, tx_loss, rx_loss, margin)
        self.lb_result.delete('1.0', 'end')
        self.lb_result.insert('end',
            f'  Max Range:\n'
            f'  {d_m:.1f} m  =  {d_m/1e3:.3f} km\n'
            f'  = {d_m/1609:.3f} miles\n')

    def _calc_fspl(self):
        try:
            dist = float(self.fspl_dist_var.get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效数值'); return
        freq_hz = self._get_freq_hz(self.fspl_freq_var, self.fspl_freq_unit)
        if freq_hz is None: return
        dist_m = dist * 1000 if self.fspl_dist_unit.get() == 'km' else dist
        fspl_db = free_space_path_loss(dist_m, freq_hz)
        self.fspl_result.delete('1.0', 'end')
        self.fspl_result.insert('end',
            f'  d = {dist_m:.2f} m\n'
            f'  f = {freq_hz/1e6:.3f} MHz\n'
            f'  lambda = {3e8/freq_hz*1e3:.2f} mm\n'
            f'  FSPL = {fspl_db:.2f} dB\n')
