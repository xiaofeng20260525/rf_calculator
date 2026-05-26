"""Receiver analysis tab: NF cascade, sensitivity, Desense."""

import math
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.link_budget import (
    noise_figure_cascade, cascade_stages_table,
    receiver_sensitivity, noise_floor, snr_to_ebno,
)
from ..calculators.rf_system import (
    tx_leakage_at_rx, rx_desense, rx_sensitivity_detailed,
)
from ..utils.constants import T0


class RxTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        for r in range(2):
            self.grid_rowconfigure(r, weight=1)
        for c in range(2):
            self.grid_columnconfigure(c, weight=1, uniform='rx')

        self._build_cascade(0, 0)
        self._build_sensitivity(0, 1)
        self._build_desense(1, 0, columnspan=2)

    # ==================== Cascade NF ====================
    def _build_cascade(self, r, c):
        sec = ttk.Labelframe(self, text=' 噪声系数级联 (Friis公式) ', padding=8, bootstyle='info')
        sec.grid(row=r, column=c, sticky='nsew', padx=3, pady=3)

        gf = ttk.Frame(sec); gf.pack(fill='x')
        self.cas_nf_var = ttk.StringVar(value='2, 3, 10')
        self.cas_gain_var = ttk.StringVar(value='15, -3')

        f1 = ttk.Frame(gf); f1.pack(fill='x', pady=3)
        ttk.Label(f1, text='各级 NF (dB):', width=18, anchor='e').pack(side='left', padx=3)
        ttk.Entry(f1, textvariable=self.cas_nf_var, width=32).pack(side='left', padx=3)

        f2 = ttk.Frame(gf); f2.pack(fill='x', pady=3)
        ttk.Label(f2, text='各级 Gain (dB):', width=18, anchor='e').pack(side='left', padx=3)
        ttk.Entry(f2, textvariable=self.cas_gain_var, width=32).pack(side='left', padx=3)

        ttk.Separator(sec, bootstyle='secondary').pack(fill='x', pady=6)
        ttk.Button(sec, text='计算级联 NF', command=self._calc_cascade, bootstyle='primary', width=14).pack(pady=2)

        self.cas_result = ttk.Text(sec, height=9, width=44, font=('Consolas', 10))
        self.cas_result.pack(fill='x', pady=5)

        fm = ttk.Labelframe(sec, text=' 公式 ', padding=3, bootstyle='secondary'); fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=44, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=3, pady=2)
        ft.insert('end',
            'F_total = F1 + (F2-1)/G1 + (F3-1)/(G1*G2) + ...\n'
            'NF_total = 10 * log10(F_total)\n'
            '其中: F = 10^(NF/10),  G = 10^(Gain/10)\n'
            '示例: NF=[2,3,10], Gain=[15,-3] => NF=3.39dB')
        ft.config(state='disabled')

    # ==================== Sensitivity ====================
    def _build_sensitivity(self, r, c):
        sec = ttk.Labelframe(self, text=' 接收灵敏度预算 ', padding=8, bootstyle='info')
        sec.grid(row=r, column=c, sticky='nsew', padx=3, pady=3)

        gf = ttk.Frame(sec); gf.pack(fill='x')

        self.sens_bw = ttk.StringVar(value='10e6')
        self.sens_nf = ttk.StringVar(value='3')
        self.sens_snr = ttk.StringVar(value='1')
        self.sens_temp = ttk.StringVar(value='290')
        self.sens_bitrate = ttk.StringVar(value='1e6')

        for i, (label, var, val) in enumerate([
            ('信号带宽 (Hz):',       self.sens_bw,     '10e6'),
            ('RX 噪声系数 (dB):',    self.sens_nf,     '3'),
            ('所需 SNR (dB):',       self.sens_snr,    '1'),
            ('参考温度 (K):',        self.sens_temp,   '290'),
            ('数据速率 (bps):',      self.sens_bitrate,'1e6'),
        ]):
            f = ttk.Frame(gf); f.pack(fill='x', pady=3)
            ttk.Label(f, text=label, width=20, anchor='e').pack(side='left', padx=3)
            ttk.Entry(f, textvariable=var, width=14).pack(side='left', padx=3)

        ttk.Separator(sec, bootstyle='secondary').pack(fill='x', pady=5)
        ttk.Button(sec, text='计算灵敏度', command=self._calc_sensitivity, bootstyle='primary', width=14).pack(pady=2)

        self.sens_result = ttk.Text(sec, height=9, width=44, font=('Consolas', 10))
        self.sens_result.pack(fill='x', pady=5)

        fm = ttk.Labelframe(sec, text=' 公式 ', padding=3, bootstyle='secondary'); fm.pack(fill='x')
        ft = ttk.Text(fm, height=4, width=44, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=3, pady=2)
        ft.insert('end',
            'kT (热噪声)  = -174 dBm/Hz (@290K)\n'
            'Noise Floor  = kT + 10*log10(BW)\n'
            'Total Noise  = Noise_Floor + NF\n'
            'Sensitivity  = Total_Noise + SNR_min')
        ft.config(state='disabled')

    # ==================== Desense ====================
    def _build_desense(self, r, c, columnspan=1):
        sec = ttk.Labelframe(self, text=' TX-RX 隔离 & Desense 分析 ', padding=8, bootstyle='primary')
        sec.grid(row=r, column=c, columnspan=columnspan, sticky='nsew', padx=3, pady=3)

        body = ttk.Frame(sec); body.pack(fill='both', expand=True)

        left = ttk.Frame(body, padding=5); left.pack(side='left', fill='y')
        gf = ttk.Frame(left); gf.pack(fill='x')

        self.ds_tx = ttk.StringVar(value='23')
        self.ds_iso = ttk.StringVar(value='50')
        self.ds_bw = ttk.StringVar(value='10e6')
        self.ds_nf = ttk.StringVar(value='3')

        for label, var, val in [
            ('TX 发射功率 (dBm):',   self.ds_tx, '23'),
            ('TX-RX 隔离度 (dB):',   self.ds_iso, '50'),
            ('RX 带宽 (Hz):',        self.ds_bw,  '10e6'),
            ('RX 噪声系数 (dB):',    self.ds_nf,  '3'),
        ]:
            f = ttk.Frame(gf); f.pack(fill='x', pady=3)
            ttk.Label(f, text=label, width=22, anchor='e').pack(side='left', padx=3)
            ttk.Entry(f, textvariable=var, width=14).pack(side='left', padx=3)

        ttk.Separator(left, bootstyle='secondary').pack(fill='x', pady=6)
        ttk.Button(left, text='计算 Desense', command=self._calc_desense, bootstyle='primary', width=14).pack(pady=2)

        self.ds_result = ttk.Text(left, height=10, width=46, font=('Consolas', 10))
        self.ds_result.pack(fill='x', pady=5)

        fm = ttk.Labelframe(left, text=' 公式 ', padding=3, bootstyle='secondary'); fm.pack(fill='x')
        ft = ttk.Text(fm, height=5, width=46, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=3, pady=2)
        ft.insert('end',
            'P_leak = P_TX - Isolation_total\n'
            'N = k * T * BW * F  (RX noise floor, W)\n'
            'Desense = 10 * log10(1 + P_leak / N)\n'
            'k = 1.38e-23,  T = 290K\n'
            'F = 10^(NF/10)  (RX noise factor, linear)')
        ft.config(state='disabled')

        right = ttk.Frame(body, padding=5); right.pack(side='right', fill='both', expand=True)

        rt = ttk.Text(right, height=18, width=42, font=('Consolas', 8))
        rt.pack(fill='both', expand=True)
        rt.insert('end',
            '=== Desense 判据参考 ===\n\n'
            ' P_leak << N (低 20dB+)\n'
            '   -> Desense < 0.1 dB\n'
            '   -> 可忽略\n\n'
            ' P_leak ~ N\n'
            '   -> Desense ~ 3 dB\n'
            '   -> 灵敏度减半\n\n'
            ' P_leak >> N\n'
            '   -> Desense 数十 dB\n'
            '   -> 需增加隔离度\n\n'
            '=== 典型隔离度参考 ===\n\n'
            ' SAW Filter:   25-35 dB\n'
            ' BAW Filter:   35-45 dB\n'
            ' Duplexer:     50-55 dB\n'
            ' Ant Switch:   20-30 dB\n'
            ' PCB Layout:   10-20 dB\n\n'
            '=== 泄漏源 ===\n\n'
            ' PA 主信号\n'
            ' PA RX-band Noise\n'
            ' PA 谐波\n'
            ' 电源纹波耦合\n'
            ' MIPI/时钟谐波')
        rt.config(state='disabled')

    # ==================== Calc methods ====================

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
        self.cas_result.insert('end', '  ' + '-' * 44 + '\n')
        for s in stages:
            self.cas_result.insert('end',
                f'  {s["name"]:>7}  {s["nf_db"]:>8.2f}  {s["gain_db"]:>10.2f}  {s["nf_cum_db"]:>10.2f}\n')

    def _calc_sensitivity(self):
        try:
            bw = float(self.sens_bw.get())
            nf = float(self.sens_nf.get())
            snr = float(self.sens_snr.get())
            temp = float(self.sens_temp.get())
            bitrate = float(self.sens_bitrate.get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效数值'); return
        r = rx_sensitivity_detailed(bw, nf, snr, temp)
        self.sens_result.delete('1.0', 'end')
        self.sens_result.insert('end',
            f'  kT (热噪声密度) = {r["kt_dbm_per_hz"]:7.1f} dBm/Hz\n'
            f'  10*log10(BW)    = {r["noise_bw_db"]:7.1f} dB\n'
            f'  Noise Floor     = {r["noise_floor_dbm"]:7.1f} dBm\n'
            f'  + NF            = {r["nf_db"]:7.1f} dB\n'
            f'  Total Noise     = {r["total_noise_dbm"]:7.1f} dBm\n'
            f'  + SNR_min       = {r["snr_min_db"]:7.1f} dB\n'
            f'  Sensitivity     = {r["sensitivity_dbm"]:7.1f} dBm\n')
        if bitrate > 0:
            ebno = snr_to_ebno(snr, bitrate, bw)
            self.sens_result.insert('end', f'\n  Eb/No ≈ {ebno:.2f} dB  (@ Rb={bitrate/1e6:.1f}Mbps)\n')

    def _calc_desense(self):
        try:
            tx = float(self.ds_tx.get())
            iso = float(self.ds_iso.get())
            bw = float(self.ds_bw.get())
            nf = float(self.ds_nf.get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效数值'); return
        leak = tx_leakage_at_rx(tx, iso)
        de = rx_desense(leak, rx_bandwidth_hz=bw, rx_nf_db=nf)
        nf_res = noise_floor(bw)
        nf_linear = 10 ** (nf / 10)
        n_linear = 1.38e-23 * 290 * bw * nf_linear
        p_leak_linear = 10 ** ((leak - 30) / 10)

        self.ds_result.delete('1.0', 'end')
        self.ds_result.insert('end',
            f'  TX Power     = {tx:.1f} dBm\n'
            f'  Isolation    = {iso:.1f} dB\n'
            f'  TX Leak @RX  = {leak:.1f} dBm\n'
            f'  RX Noise (N) = {nf_res["noise_power_dbm"]:.1f} dBm\n'
            f'               = {n_linear:.2e} W\n'
            f'  P_leak       = {p_leak_linear:.2e} W\n'
            f'  P_leak/N     = {p_leak_linear/n_linear:.1f}x\n'
            f'  Desense      = {de:.4f} dB\n')
        if de < 0.1:
            self.ds_result.insert('end', '\n  ✓ Desense 可忽略 (<0.1dB)')
        elif de < 1:
            self.ds_result.insert('end', '\n  △ 轻微 Desense (0.1~1dB)')
        elif de < 6:
            self.ds_result.insert('end', '\n  ⚠ 中等 Desense (1~6dB)')
        else:
            self.ds_result.insert('end', '\n  ✗ 严重 Desense (>6dB)！需增加隔离')
