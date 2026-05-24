"""RF system analysis tab — clean grid-aligned layout."""

import math
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.rf_system import (
    iip3_cascade, oip3_cascade,
    tx_leakage_at_rx, rx_desense, rx_sensitivity_detailed,
    papr, pa_efficiency, drain_efficiency, crest_factor,
    duty_cycle_avg_power, pa_current,
    harmonic_frequencies, harmonic_power, harmonic_path_loss,
    aclr_estimate_from_iip3, aclr_budget,
)

LW = 20  # uniform label width for all sections
EW = 13  # uniform entry width


class SystemTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # 4 rows x 2 columns — uniform grid layout
        for r in range(4):
            self.grid_rowconfigure(r, weight=1, uniform='sys_row')
        for c in range(2):
            self.grid_columnconfigure(c, weight=1, uniform='sys_col')

        self._build_iip3(0, 0)
        self._build_desense(0, 1)
        self._build_sensitivity(1, 0)
        self._build_power(1, 1)
        self._build_pae(2, 0)
        self._build_crest(2, 1)
        self._build_harmonics(3, 0)
        self._build_aclr(3, 1)

    # ---- Helpers ----

    def _panel(self, row, col, title, bootstyle='info'):
        sec = ttk.Labelframe(self, text=f' {title} ', padding=8, bootstyle=bootstyle)
        sec.grid(row=row, column=col, sticky='nsew', padx=3, pady=3)
        return sec

    def _row(self, parent, label, var_name, default, widget_cb=None):
        """Create a uniformly aligned input row. Returns the StringVar."""
        f = ttk.Frame(parent)
        f.pack(fill='x', pady=2)
        ttk.Label(f, text=label, width=LW, anchor='e').pack(side='left', padx=2)
        var = ttk.StringVar(value=default)
        setattr(self, var_name, var)
        if widget_cb:
            widget_cb(f, var)
        else:
            ttk.Entry(f, textvariable=var, width=EW).pack(side='left', padx=3)
        return var

    def _combo(self, parent, label, var_name, default, values):
        f = ttk.Frame(parent)
        f.pack(fill='x', pady=2)
        ttk.Label(f, text=label, width=LW, anchor='e').pack(side='left', padx=2)
        var = ttk.StringVar(value=default)
        setattr(self, var_name, var)
        ttk.Combobox(f, textvariable=var, values=values, width=EW+2,
                     state='readonly', bootstyle='secondary').pack(side='left', padx=3)
        return var

    def _sep_btn(self, parent, text, cmd):
        ttk.Separator(parent, bootstyle='secondary').pack(fill='x', pady=5)
        ttk.Button(parent, text=text, command=cmd, bootstyle='primary', width=14).pack(pady=2)

    def _result(self, parent, height):
        t = ttk.Text(parent, height=height, width=40, font=('Consolas', 10))
        t.pack(fill='x', pady=3)
        return t

    def _formula(self, parent, lines, height=4):
        fm = ttk.Labelframe(parent, text=' 公式 ', padding=3, bootstyle='secondary')
        fm.pack(fill='x')
        ft = ttk.Text(fm, height=height, width=40, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=3, pady=2)
        ft.insert('end', lines)
        ft.config(state='disabled')

    # ==================== IIP3 ====================
    def _build_iip3(self, r, c):
        p = self._panel(r, c, '级联线性度 (IIP3 / OIP3 / IMD3)')
        self._row(p, '各级 IIP3 (dBm):', 'iip3_var', '10, 15, 25',
                 lambda f, v: ttk.Entry(f, textvariable=v, width=28).pack(side='left', padx=3))
        self._row(p, '各级 Gain (dB):', 'iip3_gain_var', '12, -3',
                 lambda f, v: ttk.Entry(f, textvariable=v, width=28).pack(side='left', padx=3))
        self._sep_btn(p, '计算级联 IIP3', self._calc_iip3)
        self.iip3_result = self._result(p, 7)
        self._formula(p,
            '1/IIP3_total = 1/IIP3_1 + G₁/IIP3_2\n'
            '             + G₁·G₂/IIP3_3 + ...\n'
            'OIP3  = IIP3 + Gain_total\n'
            'IMD3  = 3·P_out - 2·IIP3\n'
            'C/I   = 2·(IIP3 - P_out)')

    # ==================== Desense ====================
    def _build_desense(self, r, c):
        p = self._panel(r, c, 'TX-RX 隔离 & Desense 分析')
        self._row(p, 'TX 发射功率 (dBm):', 'ds_pwr', '23')
        self._row(p, 'TX↔RX 隔离度 (dB):', 'ds_iso', '50')
        self._row(p, 'RX 带宽 (Hz):',        'ds_bw',  '10e6')
        self._row(p, 'RX 噪声系数 (dB):',    'ds_nf',  '3')
        self._sep_btn(p, '计算 Desense', self._calc_desense)
        self.ds_result = self._result(p, 7)
        self._formula(p,
            'P_leak = P_TX − Isolation\n'
            'Desense = 10·log₁₀(1 + P_leak/N)\n'
            'N = k·T·B·F  (RX底噪, W)\n'
            'k = 1.38×10⁻²³,  T = 290 K')

    # ==================== Sensitivity ====================
    def _build_sensitivity(self, r, c):
        p = self._panel(r, c, '灵敏度预算', 'primary')
        self._row(p, '信号带宽 (Hz):',     'sens_bw',   '10e6')
        self._row(p, 'RX 噪声系数 (dB):',  'sens_nf',   '3')
        self._row(p, '所需 SNR (dB):',     'sens_snr',  '1')
        self._row(p, '参考温度 (K):',      'sens_temp', '290')
        self._sep_btn(p, '计算灵敏度', self._calc_sensitivity)
        self.sens_result = self._result(p, 7)
        self._formula(p,
            'kT (热噪声)  = −174 dBm/Hz (@290K)\n'
            'Noise Floor  = kT + 10·log₁₀(BW)\n'
            'Total Noise  = Noise_Floor + NF\n'
            'Sensitivity  = Total_Noise + SNR_min')

    # ==================== Power / PAPR ====================
    def _build_power(self, r, c):
        p = self._panel(r, c, '功率 / 占空比 / PAPR', 'primary')
        self._row(p, '峰值功率 (dBm):', 'pwr_peak', '30')
        self._row(p, '平均功率 (dBm):', 'pwr_avg',  '27')
        self._row(p, '占空比 (%):',     'pwr_duty', '50')
        ttk.Separator(p, bootstyle='secondary').pack(fill='x', pady=5)
        bf = ttk.Frame(p); bf.pack(fill='x')
        ttk.Button(bf, text='PAPR ← Peak/Avg', command=self._calc_papr,
                   bootstyle='primary', width=18).pack(side='left', padx=2)
        ttk.Button(bf, text='Avg ← Peak×Duty', command=self._calc_duty_avg,
                   bootstyle='success', width=18).pack(side='left', padx=2)
        self.pwr_result = self._result(p, 4)
        self._formula(p,
            'PAPR = P_peak − P_avg\n'
            'P_avg = P_peak + 10·log₁₀(duty/100)\n'
            'duty% = 10^((P_avg−P_peak)/10) × 100', 3)

    # ==================== PAE ====================
    def _build_pae(self, r, c):
        p = self._panel(r, c, 'PA 效率 (PAE / Drain Efficiency)')
        self._row(p, '输出功率 Pout (dBm):', 'pae_pout', '28')
        self._row(p, '输入功率 Pin (dBm):',  'pae_pin',  '5')
        self._row(p, 'DC 功率 Pdc (mW):',    'pae_pdc',  '2000')
        self._row(p, '供电电压 Vcc (V):',    'pae_vcc',  '3.7')
        self._sep_btn(p, '计算效率', self._calc_pae)
        self.pae_result = self._result(p, 6)
        self._formula(p,
            'PAE = (Pout − Pin) / Pdc × 100%\n'
            'Drain_Efficiency = Pout / Pdc × 100%\n'
            'I_dc = Pdc / Vcc  (mA)')

    # ==================== Crest Factor ====================
    def _build_crest(self, r, c):
        p = self._panel(r, c, '典型峰均比 (PAPR) 参考', 'primary')
        ttk.Button(p, text='刷新', command=self._show_crest,
                   bootstyle='secondary', width=8).pack(pady=2)
        self.crest_result = self._result(p, 10)
        self._show_crest()

    # ==================== Harmonics ====================
    def _build_harmonics(self, r, c):
        p = self._panel(r, c, 'TX 谐波计算')
        self._row(p, '基频 f₀ (MHz):',    'hm_fund', '2500')
        self._row(p, '输出功率 (dBm):',    'hm_pout', '23')
        self._row(p, 'H2 抑制 (dBc):',     'hm_h2',   '-40')
        self._row(p, 'H3 抑制 (dBc):',     'hm_h3',   '-50')
        self._sep_btn(p, '计算谐波', self._calc_harmonics)
        self.hm_result = self._result(p, 8)
        self._formula(p,
            'Hn_freq = f₀ × n\n'
            'Hn_power = Pout + Hn_suppression\n'
            '所需额外滤波 = Hn_power − Limit\n'
            '3GPP UE Limit: −30 dBm (conducted)')

    # ==================== ACLR ====================
    def _build_aclr(self, r, c):
        p = self._panel(r, c, 'ACLR 预算计算', 'primary')
        self._row(p, 'PA 输出功率 (dBm):', 'aclr_pout', '23')
        self._row(p, 'PA IIP3 (dBm):',     'aclr_iip3', '30')
        self._row(p, 'PA 自身 ACLR (dBc):','aclr_pa',   '-35')
        self._row(p, 'PAPR (dB):',          'aclr_papr','8.5')
        self._sep_btn(p, '计算 ACLR', self._calc_aclr)
        self.aclr_result = self._result(p, 8)
        self._formula(p,
            'ACLR_est ≈ 2·(IIP3 − Pout) − 1.2·PAPR\n'
            'TX_ACLR  = PA_ACLR − Filter_Rejection\n'
            '3GPP LTE: ACLR ≤ −36 dBc\n'
            '3GPP NR:  ACLR ≤ −30 dBc')

    # ==================== Calc Methods ====================

    def _calc_iip3(self):
        try:
            iip3 = [float(x.strip()) for x in self.iip3_var.get().split(',')]
            gain = [float(x.strip()) for x in self.iip3_gain_var.get().split(',')]
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        gain = gain + [0]*max(0, len(iip3)-len(gain))
        gi = gain[:-1] if len(gain)>=len(iip3) else gain
        i3 = iip3_cascade(iip3, gi); o3 = oip3_cascade(iip3, gi)
        self.iip3_result.delete('1.0','end')
        self.iip3_result.insert('end',
            f'  Cascaded IIP3 = {i3:.2f} dBm\n'
            f'  Cascaded OIP3 = {o3:.2f} dBm\n'
            f'  Total Gain     = {sum(gain):.2f} dB\n\n  Stages:\n')
        for i in range(len(iip3)):
            gv = f'  Gain={gain[i]}dB' if i<len(gain)-1 else ''
            self.iip3_result.insert('end', f'    S{i+1}: IIP3={iip3[i]:.0f} dBm  {gv}\n')

    def _calc_desense(self):
        try:
            tx=float(self.ds_pwr.get()); iso=float(self.ds_iso.get())
            bw=float(self.ds_bw.get()); nf=float(self.ds_nf.get())
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        leak=tx_leakage_at_rx(tx,iso); de=rx_desense(leak, rx_bandwidth_hz=bw, rx_nf_db=nf)
        self.ds_result.delete('1.0','end')
        self.ds_result.insert('end',
            f'  TX Power     = {tx:.1f} dBm\n'
            f'  Isolation    = {iso:.1f} dB\n'
            f'  TX Leak @ RX = {leak:.1f} dBm\n'
            f'  ─────────────────────\n'
            f'  Desense      = {de:.4f} dB\n')
        if de<0.1: self.ds_result.insert('end','\n  ✓ 可忽略 (<0.1dB)')
        elif de<1: self.ds_result.insert('end','\n  △ 轻微 Desense')
        else: self.ds_result.insert('end','\n  ⚠ 严重！需增加隔离')

    def _calc_sensitivity(self):
        try:
            bw=float(self.sens_bw.get()); nf=float(self.sens_nf.get())
            snr=float(self.sens_snr.get()); t=float(self.sens_temp.get())
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        r=rx_sensitivity_detailed(bw,nf,snr,t)
        self.sens_result.delete('1.0','end')
        self.sens_result.insert('end',
            f'  kT           = {r["kt_dbm_per_hz"]:7.1f} dBm/Hz\n'
            f'  10·log₁₀(BW) = {r["noise_bw_db"]:7.1f} dB\n'
            f'  Noise Floor  = {r["noise_floor_dbm"]:7.1f} dBm\n'
            f'  + NF         = {r["nf_db"]:7.1f} dB\n'
            f'  Total Noise  = {r["total_noise_dbm"]:7.1f} dBm\n'
            f'  + SNR_min    = {r["snr_min_db"]:7.1f} dB\n'
            f'  ─────────────────────────\n'
            f'  Sensitivity  = {r["sensitivity_dbm"]:7.1f} dBm\n')

    def _calc_papr(self):
        try: peak=float(self.pwr_peak.get()); avg=float(self.pwr_avg.get())
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        p=papr(peak,avg)
        self.pwr_result.delete('1.0','end')
        self.pwr_result.insert('end',
            f'  P_peak  = {peak:.2f} dBm\n'
            f'  P_avg   = {avg:.2f} dBm\n'
            f'  PAPR    = {p:.2f} dB\n')

    def _calc_duty_avg(self):
        try: peak=float(self.pwr_peak.get()); duty=float(self.pwr_duty.get())
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        avg=duty_cycle_avg_power(peak,duty)
        self.pwr_result.delete('1.0','end')
        self.pwr_result.insert('end',
            f'  P_peak      = {peak:.2f} dBm\n'
            f'  10log(duty) = {10*math.log10(duty/100):.2f} dB\n'
            f'  P_avg       = {avg:.2f} dBm\n')

    def _calc_pae(self):
        try:
            pout=float(self.pae_pout.get()); pin=float(self.pae_pin.get())
            pdc=float(self.pae_pdc.get()); vcc=float(self.pae_vcc.get())
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        pae_v=pa_efficiency(pout,pin,pdc); de=drain_efficiency(pout,pdc)
        i_dc=pa_current(pdc,vcc)
        self.pae_result.delete('1.0','end')
        self.pae_result.insert('end',
            f'  Gain       = {pout-pin:.1f} dB\n'
            f'  PAE        = {pae_v:.2f} %\n'
            f'  Drain Eff  = {de:.2f} %\n'
            f'  I_dc       = {i_dc:.2f} mA\n'
            f'  P_RF_out   = {10**((pout-30)/10)*1000:.1f} mW\n')

    def _show_crest(self):
        self.crest_result.delete('1.0','end')
        refs = [
            ('CW', '3.0'), ('QPSK', '4.0'), ('16QAM', '5.5'),
            ('64QAM', '6.5'), ('256QAM', '7.5'), ('WCDMA', '3.5'),
            ('LTE CP-OFDM', '8.5'), ('LTE DFT-s', '6.0'),
            ('NR CP-OFDM', '8.5'), ('NR DFT-s', '6.0'),
            ('NR 256QAM', '10.0'), ('WiFi 6', '10.0'), ('WiFi 7', '10.5'),
        ]
        for sig, v in refs:
            self.crest_result.insert('end', f'  {sig:16s}  PAPR ≈ {v} dB\n')

    def _calc_harmonics(self):
        try:
            f0=float(self.hm_fund.get()); pout=float(self.hm_pout.get())
            h2=float(self.hm_h2.get()); h3=float(self.hm_h3.get())
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        freqs=harmonic_frequencies(f0,[2,3])
        hp=harmonic_power(pout,{2:h2,3:h3},[2,3])
        limit=-30
        self.hm_result.delete('1.0','end')
        self.hm_result.insert('end',
            f'  基频 f₀ = {f0:.2f} MHz\n'
            f'  输出 Pout = {pout:.1f} dBm\n\n')
        for n in [2,3]:
            key=f'H{n}'
            self.hm_result.insert('end',
                f'  H{n}: f = {freqs[key]:.2f} MHz\n'
                f'       P = {hp[f"{key}_dbm"]:.1f} dBm  ({hp[f"{key}_dbc"]:.1f} dBc)\n')
            need=harmonic_path_loss(hp[f"{key}_dbm"],limit)
            self.hm_result.insert('end',
                f'       所需滤波: {need:.1f} dB (to meet −30 dBm)\n\n')
        self.hm_result.insert('end', '  3GPP UE Harmonic Limit: −30 dBm')

    def _calc_aclr(self):
        try:
            pout=float(self.aclr_pout.get()); iip3=float(self.aclr_iip3.get())
            pa=float(self.aclr_pa.get()); papr_db=float(self.aclr_papr.get())
        except ValueError: messagebox.showerror('Error','请输入有效数值'); return
        est=aclr_estimate_from_iip3(pout,iip3,papr_db)
        b=aclr_budget(pout,pa)
        self.aclr_result.delete('1.0','end')
        self.aclr_result.insert('end',
            f'  PA Pout       = {pout:.1f} dBm\n'
            f'  PA IIP3       = {iip3:.1f} dBm\n'
            f'  ACLR(从IIP3估) ≈ {est:.1f} dBc\n'
            f'  PA自身ACLR    = {pa:.1f} dBc\n'
            f'  ─────────────────────\n'
            f'  TX链路ACLR总  = {b["total_aclr_dbc"]:.1f} dBc\n'
            f'  vs LTE (−36)  : {"✓ Pass" if b["pass_3gpp_lte"] else "✗ Fail"}\n'
            f'  vs NR  (−30)  : {"✓ Pass" if b["pass_3gpp_nr"] else "✗ Fail"}\n')
