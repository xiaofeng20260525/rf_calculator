"""Link budget and system cascade tab — clean aligned layout."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.link_budget import (
    free_space_path_loss, link_budget, receiver_sensitivity,
    noise_figure_cascade, noise_floor, snr_to_ebno,
    max_range, cascade_stages_table,
)


LW = 22  # uniform label width


class LinkBudgetTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # 2x2 grid
        for r in range(2):
            self.grid_rowconfigure(r, weight=1)
        for c in range(2):
            self.grid_columnconfigure(c, weight=1)

        self._build_link_budget(0, 0)
        self._build_cascade(0, 1)
        self._build_rx(1, 0)
        self._build_fspl(1, 1)

    # ===================== Link Budget =====================
    def _build_link_budget(self, row, col):
        lb = ttk.Labelframe(self, text=' 链路预算 ', padding=12, bootstyle='info')
        lb.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

        self.lb_vars = {}
        gf = ttk.Frame(lb)
        gf.pack(fill='x')

        items = [
            ('发射功率 (dBm)',     'tx_power',      '30'),
            ('TX天线增益 (dBi)',   'tx_ant_gain',   '2'),
            ('TX线缆损耗 (dB)',    'tx_cable_loss', '1'),
            ('频率',               'freq',          '2450'),
            ('距离',               'distance',      '1000'),
            ('RX天线增益 (dBi)',   'rx_ant_gain',   '2'),
            ('RX线缆损耗 (dB)',    'rx_cable_loss', '1'),
            ('额外裕量 (dB)',      'margin',        '0'),
            ('RX灵敏度 (dBm)',     'rx_sens',       '-90'),
        ]

        for i, (label, key, default) in enumerate(items):
            ttk.Label(gf, text=f'{label}:', width=LW, anchor='e').grid(
                row=i, column=0, sticky='e', padx=4, pady=3)
            self.lb_vars[key] = ttk.StringVar(value=default)
            ttk.Entry(gf, textvariable=self.lb_vars[key], width=13).grid(
                row=i, column=1, sticky='w', padx=4, pady=3)

        # Frequency unit (row 3)
        self.lb_freq_unit = ttk.StringVar(value='MHz')
        ttk.Combobox(gf, textvariable=self.lb_freq_unit,
                     values=['Hz', 'kHz', 'MHz', 'GHz'], width=5,
                     state='readonly', bootstyle='secondary').grid(
            row=3, column=2, padx=3)

        # Distance unit (row 4)
        self.lb_dist_unit = ttk.StringVar(value='m')
        ttk.Combobox(gf, textvariable=self.lb_dist_unit,
                     values=['m', 'km'], width=4,
                     state='readonly', bootstyle='secondary').grid(
            row=4, column=2, padx=3)

        ttk.Separator(lb, bootstyle='secondary').pack(fill='x', pady=8)

        bf = ttk.Frame(lb)
        bf.pack(fill='x')
        ttk.Button(bf, text='计算链路预算', command=self._calc_link_budget,
                   bootstyle='primary', width=14).pack(side='left', padx=3)
        ttk.Button(bf, text='计算最大距离', command=self._calc_max_range,
                   bootstyle='warning', width=14).pack(side='left', padx=3)

        self.lb_result = ttk.Text(lb, height=7, width=40, font=('Consolas', 10))
        self.lb_result.pack(fill='x', pady=8)

        # Formula
        fm = ttk.Labelframe(lb, text=' 公式 ', padding=6, bootstyle='secondary')
        fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=40, font=('Consolas', 9), wrap='none')
        ft.pack(fill='x', padx=4, pady=4)
        ft.insert('end',
            'EIRP = Ptx + Gtx - Ltx_cable\n'
            'FSPL = 20·log₁₀(4π·d / λ)\n'
            '     = 32.44 + 20·log₁₀(d_km) + 20·log₁₀(f_MHz)\n'
            'Prx  = EIRP - FSPL + Grx - Lrx_cable - Margin')
        ft.config(state='disabled')

    # ===================== Cascade NF =====================
    def _build_cascade(self, row, col):
        cas = ttk.Labelframe(self, text=' 噪声系数级联 (Friis公式) ', padding=12, bootstyle='info')
        cas.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

        c1 = ttk.Frame(cas)
        c1.pack(fill='x', pady=2)
        ttk.Label(c1, text='各级 NF (dB):', width=LW, anchor='e').pack(side='left', padx=4)
        self.cas_nf_var = ttk.StringVar(value='2, 3, 10')
        ttk.Entry(c1, textvariable=self.cas_nf_var, width=32).pack(side='left', padx=4)

        c2 = ttk.Frame(cas)
        c2.pack(fill='x', pady=2)
        ttk.Label(c2, text='各级 Gain (dB):', width=LW, anchor='e').pack(side='left', padx=4)
        self.cas_gain_var = ttk.StringVar(value='15, -3')
        ttk.Entry(c2, textvariable=self.cas_gain_var, width=32).pack(side='left', padx=4)

        ttk.Separator(cas, bootstyle='secondary').pack(fill='x', pady=8)
        ttk.Button(cas, text='计算级联', command=self._calc_cascade,
                   bootstyle='primary', width=14).pack(pady=4)

        self.cas_result = ttk.Text(cas, height=9, width=40, font=('Consolas', 10))
        self.cas_result.pack(fill='x', pady=8)

        fm = ttk.Labelframe(cas, text=' 公式 ', padding=6, bootstyle='secondary')
        fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=40, font=('Consolas', 9), wrap='none')
        ft.pack(fill='x', padx=4, pady=4)
        ft.insert('end',
            'F_total = F₁ + (F₂-1)/G₁ + (F₃-1)/(G₁·G₂) + ...\n'
            'NF_total = 10·log₁₀(F_total)\n'
            '其中: F = 10^(NF/10),  G = 10^(Gain/10)\n'
            '示例: NF=[2,3,10]dB, Gain=[15,-3]dB → NF_total=3.39dB')
        ft.config(state='disabled')

    # ===================== RX Sensitivity =====================
    def _build_rx(self, row, col):
        rx = ttk.Labelframe(self, text=' 接收机灵敏度 / SNR ', padding=12, bootstyle='primary')
        rx.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

        self.rx_vars = {}
        rxf = ttk.Frame(rx)
        rxf.pack(fill='x')
        for i, (label, key, default) in enumerate([
            ('带宽 (Hz)',          'bw',      '10e6'),
            ('噪声系数 (dB)',      'nf',      '3'),
            ('所需 SNRmin (dB)',   'snr_min', '10'),
            ('数据速率 (bps)',     'bitrate', '1e6'),
        ]):
            ttk.Label(rxf, text=f'{label}:', width=LW, anchor='e').grid(
                row=i, column=0, sticky='e', padx=4, pady=3)
            self.rx_vars[key] = ttk.StringVar(value=default)
            ttk.Entry(rxf, textvariable=self.rx_vars[key], width=13).grid(
                row=i, column=1, sticky='w', padx=4, pady=3)

        ttk.Separator(rx, bootstyle='secondary').pack(fill='x', pady=8)
        ttk.Button(rx, text='计算', command=self._calc_rx,
                   bootstyle='primary', width=14).pack(pady=4)

        self.rx_result = ttk.Text(rx, height=5, width=40, font=('Consolas', 10))
        self.rx_result.pack(fill='x', pady=8)

        fm = ttk.Labelframe(rx, text=' 公式 ', padding=6, bootstyle='secondary')
        fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=40, font=('Consolas', 9), wrap='none')
        ft.pack(fill='x', padx=4, pady=4)
        ft.insert('end',
            'Noise Floor = -174 + 10·log₁₀(BW)        [dBm]\n'
            'Sensitivity = Noise Floor + NF + SNRmin   [dBm]\n'
            'Eb/No = SNR + 10·log₁₀(BW / R_b)          [dB]\n'
            '示例: BW=10MHz, NF=3dB, SNR=10dB → Sens=-91dBm')
        ft.config(state='disabled')

    # ===================== FSPL =====================
    def _build_fspl(self, row, col):
        fspl = ttk.Labelframe(self, text=' 自由空间路径损耗 (FSPL) ', padding=12, bootstyle='primary')
        fspl.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

        f1 = ttk.Frame(fspl)
        f1.pack(fill='x', pady=2)
        ttk.Label(f1, text='频率:', width=LW, anchor='e').pack(side='left', padx=4)
        self.fspl_freq_var = ttk.StringVar(value='2450')
        ttk.Entry(f1, textvariable=self.fspl_freq_var, width=13).pack(side='left', padx=4)
        self.fspl_freq_unit = ttk.StringVar(value='MHz')
        ttk.Combobox(f1, textvariable=self.fspl_freq_unit,
                     values=['Hz', 'kHz', 'MHz', 'GHz'], width=5,
                     state='readonly', bootstyle='secondary').pack(side='left', padx=3)

        f2 = ttk.Frame(fspl)
        f2.pack(fill='x', pady=2)
        ttk.Label(f2, text='距离:', width=LW, anchor='e').pack(side='left', padx=4)
        self.fspl_dist_var = ttk.StringVar(value='1')
        ttk.Entry(f2, textvariable=self.fspl_dist_var, width=13).pack(side='left', padx=4)
        self.fspl_dist_unit = ttk.StringVar(value='km')
        ttk.Combobox(f2, textvariable=self.fspl_dist_unit,
                     values=['m', 'km'], width=4,
                     state='readonly', bootstyle='secondary').pack(side='left', padx=3)

        ttk.Separator(fspl, bootstyle='secondary').pack(fill='x', pady=8)
        ttk.Button(fspl, text='计算 FSPL', command=self._calc_fspl,
                   bootstyle='primary', width=14).pack(pady=4)

        self.fspl_result = ttk.Text(fspl, height=3, width=40, font=('Consolas', 10))
        self.fspl_result.pack(fill='x', pady=8)

        fm = ttk.Labelframe(fspl, text=' 公式 ', padding=6, bootstyle='secondary')
        fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=40, font=('Consolas', 9), wrap='none')
        ft.pack(fill='x', padx=4, pady=4)
        ft.insert('end',
            'FSPL = (4π·d / λ)²\n'
            'FSPL(dB) = 20·log₁₀(4π·d / λ)\n'
            '        = 32.44 + 20·log₁₀(d_km) + 20·log₁₀(f_MHz)\n'
            'λ = c / f,    c ≈ 3×10⁸ m/s')
        ft.config(state='disabled')

    # ===================== Calc methods =====================
    def _get_freq_hz(self, var, unit_var):
        try:
            return float(var.get()) * {'Hz': 1, 'kHz': 1e3, 'MHz': 1e6, 'GHz': 1e9}[unit_var.get()]
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
        except ValueError:
            messagebox.showerror('Error', '请输入有效数值'); return
        freq_hz = self._get_freq_hz(self.lb_vars['freq'], self.lb_freq_unit)
        if freq_hz is None: return
        dist_m = dist * 1000 if self.lb_dist_unit.get() == 'km' else dist
        r = link_budget(tx_power, tx_gain, dist_m, freq_hz, rx_gain, tx_loss, rx_loss, margin)
        self.lb_result.delete('1.0', 'end')
        self.lb_result.insert('end',
            f'  EIRP     = {r["tx_eirp_dbm"]:.2f}  dBm\n'
            f'  FSPL     = {r["fspl_db"]:.2f}  dB\n'
            f'  Prx      = {r["rx_power_dbm"]:.2f}  dBm\n'
            f'           = {r["rx_power_watt"]*1e9:.4f}  nW\n'
            f'           = {r["rx_power_watt"]*1e6:.4f}  μW\n')

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
            f'  Max Range = {d_m:.1f} m\n'
            f'            = {d_m/1e3:.3f} km\n'
            f'            = {d_m/1609:.3f} miles\n')

    def _calc_rx(self):
        try:
            bw = float(self.rx_vars['bw'].get())
            nf = float(self.rx_vars['nf'].get())
            snr_min = float(self.rx_vars['snr_min'].get())
            bitrate = float(self.rx_vars['bitrate'].get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效数值'); return
        sens = receiver_sensitivity(bw, nf, snr_min)
        nfres = noise_floor(bw)
        self.rx_result.delete('1.0', 'end')
        self.rx_result.insert('end',
            f'  Noise Floor = {nfres["noise_power_dbm"]:.2f} dBm\n'
            f'  Sensitivity = {sens:.2f} dBm\n')
        if bitrate > 0:
            ebno = snr_to_ebno(snr_min, bitrate, bw)
            self.rx_result.insert('end', f'  Eb/No       = {ebno:.2f} dB\n')

    def _calc_cascade(self):
        try:
            nf_list = [float(x.strip()) for x in self.cas_nf_var.get().split(',')]
            gain_list = [float(x.strip()) for x in self.cas_gain_var.get().split(',')]
        except ValueError:
            messagebox.showerror('Error', '请输入有效的逗号分隔数值'); return
        if len(nf_list) < 2:
            messagebox.showerror('Error', '至少需要2级'); return
        gain_list = gain_list + [0] * max(0, len(nf_list) - len(gain_list))
        nf_total = noise_figure_cascade(nf_list, gain_list)
        stages = cascade_stages_table(nf_list, gain_list)
        self.cas_result.delete('1.0', 'end')
        self.cas_result.insert('end', f'  Total NF = {nf_total:.2f} dB\n\n')
        self.cas_result.insert('end', f'  {"Stage":>7}  {"NF(dB)":>8}  {"Gain(dB)":>10}  {"NFcum(dB)":>10}\n')
        self.cas_result.insert('end', '  ' + '─' * 44 + '\n')
        for s in stages:
            self.cas_result.insert('end',
                f'  {s["name"]:>7}  {s["nf_db"]:>8.2f}  {s["gain_db"]:>10.2f}  {s["nf_cum_db"]:>10.2f}\n')

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
            f'  FSPL = {fspl_db:.2f} dB\n')
