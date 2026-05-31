"""Transmitter analysis tab: IIP3, PAPR, PAE, harmonics, ACLR."""

import math
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.rf_system import (
    iip3_cascade, oip3_cascade,
    papr, pa_efficiency, drain_efficiency, crest_factor,
    duty_cycle_avg_power, pa_current,
    harmonic_frequencies, harmonic_power, harmonic_path_loss,
    aclr_estimate_from_oip3, aclr_budget,
)

LW = 20; EW = 13


class SystemTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        for r in range(3):
            self.grid_rowconfigure(r, weight=1)
        for c in range(2):
            self.grid_columnconfigure(c, weight=1, uniform='tx')

        self._build_iip3(0, 0)
        self._build_power(0, 1)
        self._build_pae(1, 0)
        self._build_crest(1, 1)
        self._build_harmonics(2, 0)
        self._build_aclr(2, 1)

    # ---- helpers ----
    def _panel(self, r, c, title, bootstyle='info'):
        sec = ttk.Labelframe(self, text=f' {title} ', padding=8, bootstyle=bootstyle)
        sec.grid(row=r, column=c, sticky='nsew', padx=3, pady=3)
        return sec

    def _row(self, parent, label, var_name, default, ew=EW):
        f = ttk.Frame(parent); f.pack(fill='x', pady=2)
        ttk.Label(f, text=label, width=LW, anchor='e').pack(side='left', padx=2)
        var = ttk.StringVar(value=default); setattr(self, var_name, var)
        ttk.Entry(f, textvariable=var, width=ew).pack(side='left', padx=3)
        return var

    def _sep_btn(self, parent, text, cmd):
        ttk.Separator(parent, bootstyle='secondary').pack(fill='x', pady=5)
        ttk.Button(parent, text=text, command=cmd, bootstyle='primary', width=14).pack(pady=2)

    def _result(self, parent, h):
        t = ttk.Text(parent, height=h, width=40, font=('Consolas', 10)); t.pack(fill='x', pady=3); return t

    def _formula(self, parent, lines, h=4):
        fm = ttk.Labelframe(parent, text=' 公式 ', padding=3, bootstyle='secondary'); fm.pack(fill='x')
        ft = ttk.Text(fm, height=h, width=40, font=('Consolas', 8), wrap='none')
        ft.pack(fill='x', padx=3, pady=2); ft.insert('end', lines); ft.config(state='disabled')

    # ==================== IIP3 ====================
    def _build_iip3(self, r, c):
        p = self._panel(r, c, '级联线性度 (IIP3 / OIP3 / IMD3)')
        self._row(p, '各级 IIP3 (dBm):', 'iip3_var', '10, 15, 25', 30)
        self._row(p, '各级 Gain (dB):', 'iip3_gain_var', '12, -3', 30)
        self._sep_btn(p, '计算级联 IIP3', self._calc_iip3)
        self.iip3_result = self._result(p, 9)
        self._formula(p,
            '1/IIP3_total = 1/IIP3_1 + G1/IIP3_2\n'
            '             + G1*G2/IIP3_3 + ...\n'
            'OIP3  = IIP3 + Gain_total\n'
            'IMD3  = 3*P_out - 2*IIP3\n'
            'C/I   = 2*(IIP3 - P_out)')

    # ==================== Power / PAPR ====================
    def _build_power(self, r, c):
        p = self._panel(r, c, '功率 / 占空比 / PAPR', 'primary')
        self._row(p, '峰值功率 (dBm):', 'pwr_peak', '30')
        self._row(p, '平均功率 (dBm):', 'pwr_avg',  '27')
        self._row(p, '占空比 (%):',     'pwr_duty', '50')
        ttk.Separator(p, bootstyle='secondary').pack(fill='x', pady=5)
        bf = ttk.Frame(p); bf.pack(fill='x')
        ttk.Button(bf, text='PAPR <- Peak/Avg', command=self._calc_papr, bootstyle='primary', width=18).pack(side='left', padx=2)
        ttk.Button(bf, text='Avg <- Peak*Duty', command=self._calc_duty_avg, bootstyle='success', width=18).pack(side='left', padx=2)
        self.pwr_result = self._result(p, 5)
        self._formula(p,
            'PAPR = P_peak - P_avg\n'
            'P_avg = P_peak + 10*log10(duty/100)\n'
            'duty% = 10^((P_avg-P_peak)/10) * 100', 3)

    # ==================== PAE ====================
    def _build_pae(self, r, c):
        p = self._panel(r, c, 'PA 效率 (PAE / Drain Efficiency)')
        self._row(p, 'Pout (dBm):', 'pae_pout', '28')
        self._row(p, 'Pin (dBm):',  'pae_pin',  '5')
        self._row(p, 'Pdc (mW):',   'pae_pdc',  '2000')
        self._row(p, 'Vcc (V):',    'pae_vcc',  '3.7')
        self._sep_btn(p, '计算效率', self._calc_pae)
        self.pae_result = self._result(p, 7)
        self._formula(p,
            'PAE = (Pout - Pin) / Pdc * 100%\n'
            'Drain Efficiency = Pout / Pdc * 100%\n'
            'I_dc = Pdc / Vcc  (mA)')

    # ==================== Crest Factor ====================
    def _build_crest(self, r, c):
        p = self._panel(r, c, '典型峰均比 (PAPR) 参考', 'primary')
        ttk.Button(p, text='刷新', command=self._show_crest, bootstyle='secondary', width=8).pack(pady=2)
        self.crest_result = self._result(p, 12)
        self._show_crest()

    # ==================== Harmonics ====================
    def _build_harmonics(self, r, c):
        p = self._panel(r, c, 'TX 谐波计算')
        self._row(p, '基频 f0 (MHz):', 'hm_fund', '2500')
        self._row(p, '输出功率 (dBm):', 'hm_pout', '23')
        self._row(p, 'H2 抑制 (dBc):',  'hm_h2',   '-40')
        self._row(p, 'H3 抑制 (dBc):',  'hm_h3',   '-50')
        self._sep_btn(p, '计算谐波', self._calc_harmonics)
        self.hm_result = self._result(p, 9)
        self._formula(p,
            'Hn_freq = f0 * n\n'
            'Hn_power = Pout + Hn_suppression\n'
            '所需额外滤波 = Hn_power - Limit\n'
            '3GPP UE Limit: -30 dBm (conducted)')

    # ==================== ACLR ====================
    def _build_aclr(self, r, c):
        p = self._panel(r, c, 'ACLR 预算计算', 'primary')
        self._row(p, 'PA 输出功率 (dBm):', 'aclr_pout', '23')
        self._row(p, 'PA OIP3 (dBm):',     'aclr_oip3', '30')
        self._row(p, 'PA ACLR (dBc):',      'aclr_pa',   '-35')
        self._row(p, 'PAPR (dB):',          'aclr_papr', '8.5')
        self._sep_btn(p, '计算 ACLR', self._calc_aclr)
        self.aclr_result = self._result(p, 10)
        self._formula(p,
            'ACLR_est ~= 2*(IIP3 - Pout) - 1.2*PAPR\n'
            'TX_ACLR  = PA_ACLR - Filter_Rejection\n'
            '3GPP LTE: ACLR <= -36 dBc\n'
            '3GPP NR:  ACLR <= -30 dBc')

    # ==================== Calc methods ====================

    def _calc_iip3(self):
        try:
            iip3 = [float(x.strip()) for x in self.iip3_var.get().split(',')]
            gain = [float(x.strip()) for x in self.iip3_gain_var.get().split(',')]
        except ValueError: messagebox.showerror('Error','无效'); return
        gain = gain + [0]*max(0, len(iip3)-len(gain))
        gi = gain[:-1] if len(gain)>=len(iip3) else gain
        i3=iip3_cascade(iip3,gi); o3=oip3_cascade(iip3,gi)
        self.iip3_result.delete('1.0','end')
        self.iip3_result.insert('end',f'  IIP3_total = {i3:.2f} dBm\n  OIP3_total = {o3:.2f} dBm\n  Gain_total = {sum(gain):.2f} dB\n\n  Stages:\n')
        for i in range(len(iip3)):
            gv=f'  Gain={gain[i]}dB' if i<len(gain)-1 else ''
            self.iip3_result.insert('end',f'    S{i+1}: IIP3={iip3[i]:.0f}dBm  {gv}\n')

    def _calc_papr(self):
        try: peak=float(self.pwr_peak.get()); avg=float(self.pwr_avg.get())
        except ValueError: messagebox.showerror('Error','无效'); return
        p=papr(peak,avg)
        self.pwr_result.delete('1.0','end')
        self.pwr_result.insert('end',f'  P_peak={peak:.2f}  P_avg={avg:.2f}  PAPR={p:.2f} dB\n')

    def _calc_duty_avg(self):
        try: peak=float(self.pwr_peak.get()); duty=float(self.pwr_duty.get())
        except ValueError: messagebox.showerror('Error','无效'); return
        avg=duty_cycle_avg_power(peak,duty)
        self.pwr_result.delete('1.0','end')
        self.pwr_result.insert('end',f'  P_peak={peak:.2f}  Duty={duty:.1f}%  P_avg={avg:.2f} dBm\n')

    def _calc_pae(self):
        try: pout=float(self.pae_pout.get()); pin=float(self.pae_pin.get()); pdc=float(self.pae_pdc.get()); vcc=float(self.pae_vcc.get())
        except ValueError: messagebox.showerror('Error','无效'); return
        pae_v=pa_efficiency(pout,pin,pdc); de=drain_efficiency(pout,pdc); i_dc=pa_current(pdc,vcc)
        self.pae_result.delete('1.0','end')
        self.pae_result.insert('end',f'  Gain={pout-pin:.1f}dB  PAE={pae_v:.2f}%  DrainEff={de:.2f}%\n  I_dc={i_dc:.2f}mA  P_RF={10**((pout-30)/10)*1000:.1f}mW\n')

    def _show_crest(self):
        self.crest_result.delete('1.0','end')
        for s,v in [('CW','3.0'),('QPSK','4.0'),('16QAM','5.5'),('64QAM','6.5'),('256QAM','7.5'),('WCDMA','3.5'),('LTE CP','8.5'),('LTE DFTS','6.0'),('NR CP','8.5'),('NR DFTS','6.0'),('NR 256QAM','10.0'),('WiFi6','10.0'),('WiFi7','10.5')]:
            self.crest_result.insert('end',f'  {s:14s} PAPR ~ {v} dB\n')

    def _calc_harmonics(self):
        try: f0=float(self.hm_fund.get()); pout=float(self.hm_pout.get()); h2=float(self.hm_h2.get()); h3=float(self.hm_h3.get())
        except ValueError: messagebox.showerror('Error','无效'); return
        freqs=harmonic_frequencies(f0,[2,3]); hp=harmonic_power(pout,{2:h2,3:h3},[2,3]); limit=-30
        self.hm_result.delete('1.0','end')
        self.hm_result.insert('end',f'  f0 = {f0:.2f} MHz  Pout = {pout:.1f} dBm\n\n')
        for n in [2,3]:
            k=f'H{n}'; need=harmonic_path_loss(hp[f"{k}_dbm"],limit)
            self.hm_result.insert('end',f'  H{n}: f={freqs[k]:.2f}MHz  P={hp[f"{k}_dbm"]:.1f}dBm ({hp[f"{k}_dbc"]:.1f}dBc)\n      需要滤波: {need:.1f}dB (to -30dBm)\n\n')
        self.hm_result.insert('end','  3GPP UE Limit: -30 dBm')

    def _calc_aclr(self):
        try: pout=float(self.aclr_pout.get()); oip3=float(self.aclr_oip3.get()); pa=float(self.aclr_pa.get()); papr_db=float(self.aclr_papr.get())
        except ValueError: messagebox.showerror('Error','无效'); return
        est=aclr_estimate_from_oip3(pout,oip3,papr_db); b=aclr_budget(pout,pa)
        self.aclr_result.delete('1.0','end')
        self.aclr_result.insert('end',
            f'  PA Pout       = {pout:.1f} dBm\n'
            f'  PA OIP3       = {oip3:.1f} dBm\n'
            f'  ACLR(est)     ~ {est:.1f} dBc\n'
            f'  PA ACLR       = {pa:.1f} dBc\n'
            f'  TX ACLR(total)= {b["total_aclr_dbc"]:.1f} dBc\n'
            f'  vs LTE(-36dBc): {"PASS" if b["pass_3gpp_lte"] else "FAIL"}\n'
            f'  vs NR (-30dBc): {"PASS" if b["pass_3gpp_nr"] else "FAIL"}\n')
