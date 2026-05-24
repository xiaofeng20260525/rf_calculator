"""WiFi / LTE / NR data rate calculator tab."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.data_rate import (
    wifi_rate, wifi_rate_simple,
    lte_rate, nr_rate, nr_max_rate,
    WIFI6_MCS, LTE_MODULATION, NR_MODULATION,
    NR_BW_RB, NR_NUMEROLOGY,
    NR_TDD_PATTERNS, LTE_TDD_CONFIGS,
)

LW = 24
EW = 12


class DataRateTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # 2 rows: WiFi (top) | Cellular (bottom)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_wifi()
        self._build_cellular()

    # ================== WiFi ==================
    def _build_wifi(self):
        sec = ttk.Labelframe(self, text=' WiFi 速率计算 (802.11ac/ax/be) ', padding=10, bootstyle='info')
        sec.grid(row=0, column=0, sticky='nsew', padx=6, pady=5)

        # Top: inputs
        top = ttk.Frame(sec)
        top.pack(fill='x')

        left = ttk.Frame(top, padding=5)
        left.pack(side='left', fill='y')

        gf = ttk.Frame(left)
        gf.pack(fill='x')

        self.wifi_mcs = ttk.StringVar(value='11')
        ttk.Label(gf, text='MCS Index (0-13):', width=LW, anchor='e').grid(
            row=0, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.wifi_mcs,
                     values=[str(i) for i in range(15)], width=8, state='readonly').grid(
            row=0, column=1, sticky='w', padx=3, pady=3)

        self.wifi_bw = ttk.StringVar(value='160')
        ttk.Label(gf, text='带宽 (MHz):', width=LW, anchor='e').grid(
            row=1, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.wifi_bw,
                     values=['20', '40', '80', '160', '320'], width=8, state='readonly').grid(
            row=1, column=1, sticky='w', padx=3, pady=3)

        self.wifi_nss = ttk.StringVar(value='2')
        ttk.Label(gf, text='空间流数 (Nss):', width=LW, anchor='e').grid(
            row=2, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.wifi_nss,
                     values=['1', '2', '4', '8'], width=8, state='readonly').grid(
            row=2, column=1, sticky='w', padx=3, pady=3)

        self.wifi_gi = ttk.StringVar(value='0.8us (Short)')
        ttk.Label(gf, text='Guard Interval:', width=LW, anchor='e').grid(
            row=3, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.wifi_gi,
                     values=['0.8us (Short)', '1.6us (Long)', '3.2us'], width=16, state='readonly').grid(
            row=3, column=1, sticky='w', padx=3, pady=3)

        self.wifi_gen = ttk.StringVar(value='6')
        ttk.Label(gf, text='WiFi Generation:', width=LW, anchor='e').grid(
            row=4, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.wifi_gen,
                     values=['5 (802.11ac)', '6 (802.11ax)', '7 (802.11be)'], width=16, state='readonly').grid(
            row=4, column=1, sticky='w', padx=3, pady=3)

        ttk.Separator(left, bootstyle='secondary').pack(fill='x', pady=6)
        ttk.Button(left, text='计算 WiFi 速率', command=self._calc_wifi, bootstyle='primary', width=16).pack(pady=3)

        self.wifi_result = ttk.Text(left, height=7, width=42, font=('Consolas', 10))
        self.wifi_result.pack(fill='x', pady=5)

        # Right: MCS table
        right = ttk.Frame(top, padding=5)
        right.pack(side='right', fill='both', expand=True)

        tbl = ttk.Labelframe(right, text=' WiFi 6/7 MCS 参考表 ', padding=5, bootstyle='secondary')
        tbl.pack(fill='both', expand=True)
        tt = ttk.Text(tbl, height=12, width=36, font=('Consolas', 8))
        tt.pack(fill='both', expand=True)
        tt.insert('end',
            ' MCS  Modulation  CodeRate  Bits/SS\n'
            ' ' + '─' * 38 + '\n'
            '  0   BPSK         1/2      0.50\n'
            '  1   QPSK         1/2      1.00\n'
            '  2   QPSK         3/4      1.50\n'
            '  3   16QAM        1/2      2.00\n'
            '  4   16QAM        3/4      3.00\n'
            '  5   64QAM        2/3      4.00\n'
            '  6   64QAM        3/4      4.50\n'
            '  7   64QAM        5/6      5.00\n'
            '  8   256QAM       3/4      6.00\n'
            '  9   256QAM       5/6      6.67\n'
            ' 10   1024QAM      3/4      7.50\n'
            ' 11   1024QAM      5/6      8.33\n'
            ' 12   4096QAM(WiFi7)3/4     9.00\n'
            ' 13   4096QAM(WiFi7)5/6    10.00\n')
        tt.config(state='disabled')

    # ================== LTE / NR ==================
    def _build_cellular(self):
        sec = ttk.Labelframe(self, text=' LTE / NR 蜂窝速率计算 ', padding=10, bootstyle='primary')
        sec.grid(row=1, column=0, sticky='nsew', padx=6, pady=5)

        top = ttk.Frame(sec)
        top.pack(fill='x')

        # LTE section
        lte_frame = ttk.Labelframe(top, text=' LTE ', padding=8, bootstyle='info')
        lte_frame.pack(side='left', fill='both', expand=True, padx=3)

        gf = ttk.Frame(lte_frame)
        gf.pack(fill='x')

        self.lte_rb = ttk.StringVar(value='100')
        ttk.Label(gf, text='RB数:', width=10, anchor='e').grid(row=0, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.lte_rb,
                     values=['6 (1.4MHz)', '15 (3MHz)', '25 (5MHz)', '50 (10MHz)', '75 (15MHz)', '100 (20MHz)'],
                     width=18, state='readonly').grid(row=0, column=1, sticky='w', padx=3, pady=3)

        self.lte_mcs = ttk.StringVar(value='28')
        ttk.Label(gf, text='MCS:', width=10, anchor='e').grid(row=1, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.lte_mcs,
                     values=[str(i) for i in range(32)], width=8, state='readonly').grid(
            row=1, column=1, sticky='w', padx=3, pady=3)

        self.lte_layers = ttk.StringVar(value='2')
        ttk.Label(gf, text='MIMO层:', width=10, anchor='e').grid(row=2, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.lte_layers,
                     values=['1', '2', '4'], width=8, state='readonly').grid(
            row=2, column=1, sticky='w', padx=3, pady=3)

        self.lte_tdd = ttk.StringVar(value='FDD (Full DL)')
        ttk.Label(gf, text='TDD/FDD:', width=10, anchor='e').grid(row=3, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf, textvariable=self.lte_tdd,
                     values=list(LTE_TDD_CONFIGS.keys()), width=20, state='readonly').grid(
            row=3, column=1, sticky='w', padx=3, pady=3)

        self.lte_oh = ttk.StringVar(value='25')
        ttk.Label(gf, text='Overhead%:', width=10, anchor='e').grid(row=4, column=0, sticky='e', padx=3, pady=3)
        ttk.Entry(gf, textvariable=self.lte_oh, width=8).grid(row=4, column=1, sticky='w', padx=3, pady=3)

        ttk.Separator(lte_frame, bootstyle='secondary').pack(fill='x', pady=5)
        ttk.Button(lte_frame, text='计算 LTE 速率', command=self._calc_lte, bootstyle='primary', width=16).pack(pady=3)

        self.lte_result = ttk.Text(lte_frame, height=8, width=34, font=('Consolas', 10))
        self.lte_result.pack(fill='x', pady=3)

        # NR section
        nr_frame = ttk.Labelframe(top, text=' NR (5G) ', padding=8, bootstyle='info')
        nr_frame.pack(side='right', fill='both', expand=True, padx=3)

        gf2 = ttk.Frame(nr_frame)
        gf2.pack(fill='x')

        self.nr_bw = ttk.StringVar(value='100')
        ttk.Label(gf2, text='带宽 (MHz):', width=12, anchor='e').grid(row=0, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf2, textvariable=self.nr_bw,
                     values=['5', '10', '15', '20', '25', '30', '40', '50', '60', '80', '90', '100'],
                     width=8, state='readonly').grid(row=0, column=1, sticky='w', padx=3, pady=3)

        self.nr_mcs = ttk.StringVar(value='27')
        ttk.Label(gf2, text='MCS Index:', width=12, anchor='e').grid(row=1, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf2, textvariable=self.nr_mcs,
                     values=[str(i) for i in range(32)], width=8, state='readonly').grid(
            row=1, column=1, sticky='w', padx=3, pady=3)

        self.nr_layers = ttk.StringVar(value='4')
        ttk.Label(gf2, text='MIMO层数:', width=12, anchor='e').grid(row=2, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf2, textvariable=self.nr_layers,
                     values=['1', '2', '4'], width=8, state='readonly').grid(
            row=2, column=1, sticky='w', padx=3, pady=3)

        self.nr_scs = ttk.StringVar(value='30')
        ttk.Label(gf2, text='SCS (kHz):', width=12, anchor='e').grid(row=3, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf2, textvariable=self.nr_scs,
                     values=['15', '30', '60', '120'], width=8, state='readonly').grid(
            row=3, column=1, sticky='w', padx=3, pady=3)

        self.nr_tdd = ttk.StringVar(value='DDDDDDDSU (5ms)')
        ttk.Label(gf2, text='NR TDD配置:', width=12, anchor='e').grid(row=4, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf2, textvariable=self.nr_tdd,
                     values=list(NR_TDD_PATTERNS.keys()), width=20, state='readonly').grid(
            row=4, column=1, sticky='w', padx=3, pady=3)

        self.nr_ca = ttk.StringVar(value='1')
        ttk.Label(gf2, text='CA数:', width=12, anchor='e').grid(row=5, column=0, sticky='e', padx=3, pady=3)
        ttk.Combobox(gf2, textvariable=self.nr_ca,
                     values=['1', '2', '4', '8', '16'], width=8, state='readonly').grid(
            row=5, column=1, sticky='w', padx=3, pady=3)

        self.nr_oh = ttk.StringVar(value='14')
        ttk.Label(gf2, text='Overhead%:', width=12, anchor='e').grid(row=6, column=0, sticky='e', padx=3, pady=3)
        ttk.Entry(gf2, textvariable=self.nr_oh, width=8).grid(row=6, column=1, sticky='w', padx=3, pady=3)

        ttk.Separator(nr_frame, bootstyle='secondary').pack(fill='x', pady=5)
        ttk.Button(nr_frame, text='计算 NR 速率', command=self._calc_nr, bootstyle='primary', width=16).pack(pady=3)

        self.nr_result = ttk.Text(nr_frame, height=8, width=34, font=('Consolas', 10))
        self.nr_result.pack(fill='x', pady=3)

        # Formula
        fm = ttk.Labelframe(sec, text=' 公式 ', padding=4, bootstyle='secondary')
        fm.pack(fill='x', padx=3, pady=(5, 0))
        ft = ttk.Text(fm, height=2, width=80, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=4, pady=3)
        ft.insert('end',
            'WiFi: Rate = N_data_tones × bits/symbol × Nss / T_symbol    |   '
            'LTE: Rate = RB×12×14×Qm×Layers×(1-OH%) / 1ms    |   '
            'NR: Rate = RB×12×Slots/ms×14×Qm×CR×Layers×CA×(1-OH%) × 1000')
        ft.config(state='disabled')

    # ================== Calc methods ==================

    def _calc_wifi(self):
        try:
            mcs = int(self.wifi_mcs.get())
            bw = int(self.wifi_bw.get())
            nss = int(self.wifi_nss.get())
            gi = self.wifi_gi.get()
            gen_txt = self.wifi_gen.get()
            gen = 5
            if '6' in gen_txt or 'ax' in gen_txt:
                gen = 6
            elif '7' in gen_txt or 'be' in gen_txt:
                gen = 7
        except ValueError:
            messagebox.showerror('Error', '请选择有效参数'); return

        r = wifi_rate(mcs, bw, nss, gi, gen)
        if r is None:
            messagebox.showerror('Error', f'MCS={mcs} 不支持此 WiFi 代'); return

        self.wifi_result.delete('1.0', 'end')
        self.wifi_result.insert('end',
            f'  MCS {r["mcs"]:2d}:  {r["modulation"]:8s}  CR≈{r["coding_rate"]:.2f}\n'
            f'  BW = {bw} MHz,  Nss = {nss},  GI = {gi}\n'
            f'  Data Tones = {r["data_tones"]}\n'
            f'  Symbol Time = {r["symbol_time_us"]:.1f} μs\n'
            f'  ─────────────────────────────\n'
            f'  PHY Rate ≈ {r["rate_mbps"]:.1f} Mbps\n'
            f'           = {r["rate_gbps"]:.3f} Gbps\n')

    def _calc_lte(self):
        try:
            rb_txt = self.lte_rb.get().split()[0]
            n_rb = int(rb_txt)
            mcs = int(self.lte_mcs.get())
            layers = int(self.lte_layers.get())
            oh = float(self.lte_oh.get())
            tdd_key = self.lte_tdd.get()
            dl_ratio, desc = LTE_TDD_CONFIGS.get(tdd_key, (1.0, ''))
        except ValueError:
            messagebox.showerror('Error', '请选择有效参数'); return

        r = lte_rate(n_rb, mcs, layers, oh, dl_ratio)
        if r is None:
            messagebox.showerror('Error', f'MCS={mcs} 无效'); return

        self.lte_result.delete('1.0', 'end')
        duplex_mode = 'FDD' if dl_ratio >= 1.0 else 'TDD'
        self.lte_result.insert('end',
            f'  BW ≈ {r["channel_bw_mhz"]:.1f} MHz    RB = {r["n_rb"]}\n'
            f'  MCS {r["mcs"]:2d}: {r["modulation"]:5s}  Qm={r["bits_per_re"]}\n'
            f'  MIMO Layers = {r["mimo_layers"]}\n'
            f'  Duplex = {duplex_mode}  DL Ratio = {dl_ratio*100:.0f}%\n'
            f'  Overhead = {r["overhead_pct"]:.0f}%\n'
            f'  ─────────────────────────────\n'
            f'  PHY Rate ≈ {r["rate_mbps"]:.1f} Mbps\n')
        if dl_ratio < 1.0 and 'rate_mbps_full' in r:
            self.lte_result.insert('end',
                f'  (等效FDD速率 ≈ {r["rate_mbps_full"]:.1f} Mbps)\n')

    def _calc_nr(self):
        try:
            bw = int(self.nr_bw.get())
            mcs = int(self.nr_mcs.get())
            layers = int(self.nr_layers.get())
            scs = int(self.nr_scs.get())
            ca = int(self.nr_ca.get())
            oh = float(self.nr_oh.get())
            tdd_key = self.nr_tdd.get()
            _, dl_ratio = NR_TDD_PATTERNS.get(tdd_key, (1.0, 1.0))
        except ValueError:
            messagebox.showerror('Error', '请选择有效参数'); return

        n_rb = NR_BW_RB.get(bw, int(bw * 2.5))
        r = nr_rate(n_rb, mcs, layers, scs, oh, ca, dl_ratio)
        if r is None:
            messagebox.showerror('Error', f'MCS={mcs} 无效'); return

        self.nr_result.delete('1.0', 'end')
        duplex_mode = 'FDD' if dl_ratio >= 1.0 else 'TDD'
        self.nr_result.insert('end',
            f'  BW = {bw} MHz    RB = {r["n_rb"]}\n'
            f'  MCS {r["mcs"]:2d}:  Qm={r["modulation_order"]}  CR≈{r["target_code_rate"]:.3f}\n'
            f'  SCS = {r["scs_khz"]} kHz    CA×{r["carrier_agg"]}\n'
            f'  MIMO = {r["mimo_layers"]} Layers\n'
            f'  Duplex = {duplex_mode}  DL Ratio = {dl_ratio*100:.0f}%\n'
            f'  Overhead = {r["overhead_pct"]:.0f}%\n'
            f'  ─────────────────────────────\n'
            f'  PHY Rate ≈ {r["rate_mbps"]:.1f} Mbps\n'
            f'           = {r["rate_gbps"]:.4f} Gbps\n')
        if dl_ratio < 1.0 and 'rate_mbps_full_dl' in r:
            self.nr_result.insert('end',
                f'  (等效FDD速率 ≈ {r["rate_mbps_full_dl"]:.1f} Mbps)\n')
