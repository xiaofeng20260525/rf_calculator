"""Transmission line tab — scrollable canvas, all visible, 2-col aligned."""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..calculators.transmission_line import (
    microstrip_impedance, microstrip_width,
    stripline_impedance, stripline_width,
    cpw_impedance, skin_depth,
    guided_wavelength, quarter_wave_length,
    microstrip_total_loss, stripline_total_loss,
)
from ..utils.constants import (
    C0, ER_FR4, ER_ROGERS_4350, ER_ROGERS_4003,
    H_062, H_031, H_020, CU_1OZ, CU_CONDUCTIVITY,
)
from .schematics import (
    draw_microstrip, draw_stripline, draw_cpw,
    draw_microstrip_loss, draw_stripline_loss,
)


class TransmissionLineTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        canvas = tk.Canvas(self, highlightthickness=0, bg='#2b3e50')
        vsb = ttk.Scrollbar(self, orient='vertical', command=canvas.yview, bootstyle='round')
        inner = ttk.Frame(canvas)
        win_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)
        canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', lambda ev: canvas.yview_scroll(-int(ev.delta/120), 'units')))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))

        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        # Rows — each is a frame with 2 equal grid columns
        row1 = ttk.Frame(inner, padding=2); row1.pack(fill='x')
        row1.grid_columnconfigure(0, weight=1, uniform='tlr')
        row1.grid_columnconfigure(1, weight=1, uniform='tlr')
        self._build_ms(row1, 0, 0); self._build_sl(row1, 0, 1)

        row2 = ttk.Frame(inner, padding=2); row2.pack(fill='x')
        row2.grid_columnconfigure(0, weight=1, uniform='tlr')
        row2.grid_columnconfigure(1, weight=1, uniform='tlr')
        self._build_cpw(row2, 0, 0); self._build_wl(row2, 0, 1)

        row3 = ttk.Frame(inner, padding=2); row3.pack(fill='x')
        row3.grid_columnconfigure(0, weight=1, uniform='tlr')
        row3.grid_columnconfigure(1, weight=1, uniform='tlr')
        self._build_trace_loss(row3, 0, 0); self._build_tl_ref(row3, 0, 1)

    # ==================== helpers ====================

    def _panel(self, parent, r, c, title, bootstyle='info'):
        sec = ttk.Labelframe(parent, text=f' {title} ', padding=6, bootstyle=bootstyle)
        sec.grid(row=r, column=c, sticky='nsew', padx=3, pady=3)
        return sec

    def _input(self, parent, label, var_name, default, width=10, combo_vals=None):
        f = tk.Frame(parent, bg='#2b3e50'); f.pack(fill='x', pady=1)
        ttk.Label(f, text=label, width=11, anchor='e').pack(side='left', padx=2)
        var = tk.StringVar(value=default); setattr(self, var_name, var)
        if combo_vals:
            ttk.Combobox(f, textvariable=var, values=combo_vals, width=width+2,
                         state='readonly', bootstyle='secondary').pack(side='left', padx=2)
        else:
            ttk.Entry(f, textvariable=var, width=width).pack(side='left', padx=2)
        return var

    def _sep(self, parent): ttk.Separator(parent, bootstyle='secondary').pack(fill='x', pady=5)
    def _result(self, parent, h):
        t = ttk.Text(parent, height=h, width=36, font=('Consolas', 9)); t.pack(fill='x', pady=2); return t

    def _formula(self, parent, lines, h=3):
        fm = ttk.Labelframe(parent, text=' Formula ', padding=2, bootstyle='secondary')
        ft = ttk.Text(fm, height=h, width=36, font=('Consolas', 7), wrap='none')
        ft.pack(fill='x', padx=2, pady=2); ft.insert('end', lines); ft.config(state='disabled')
        return fm

    def _get_freq(self, v, u):
        try: return float(v.get())*{'Hz':1,'kHz':1e3,'MHz':1e6,'GHz':1e9}[u.get()]
        except: return None

    # ==================== Microstrip ====================
    def _build_ms(self, parent, r, c):
        sec = self._panel(parent, r, c, 'Microstrip')
        body = tk.Frame(sec, bg='#2b3e50'); body.pack(fill='both', expand=True)
        L = tk.Frame(body, bg='#2b3e50'); L.pack(side='left', fill='both', expand=True, padx=2)
        R = tk.Frame(body, bg='#2b3e50'); R.pack(side='right', padx=2)

        self.ms_er_var = tk.StringVar(value=str(ER_FR4)); self.ms_er_custom = tk.StringVar()
        self.ms_h_var = tk.StringVar(value=str(H_062));  self.ms_h_custom = tk.StringVar()
        self.ms_t_var = tk.StringVar(value='0');          self.ms_w_var = tk.StringVar(value='3.0')
        self.ms_z0_tgt = tk.StringVar(value='50')

        for label, v, cv, vals in [
            ('Er:', self.ms_er_var, self.ms_er_custom, [str(ER_FR4),str(ER_ROGERS_4350),str(ER_ROGERS_4003),'']),
            ('h(mm):', self.ms_h_var, self.ms_h_custom, [str(H_062),str(H_031),str(H_020),'']),
        ]:
            f = tk.Frame(L, bg='#2b3e50'); f.pack(fill='x', pady=0)
            ttk.Label(f, text=label, width=11, anchor='e').pack(side='left', padx=1)
            ttk.Combobox(f, textvariable=v, values=vals, width=10, state='readonly', bootstyle='secondary').pack(side='left')
            ttk.Entry(f, textvariable=cv, width=5).pack(side='left', padx=1)

        self._input(L, 't(mm):',  'ms_t', '0')
        self._input(L, 'W(mm):',  'ms_w', '3.0')

        self._sep(L)
        f = tk.Frame(L, bg='#2b3e50'); f.pack(fill='x')
        ttk.Button(f, text='W->Zo', command=self._calc_ms_z0, bootstyle='primary', width=6).pack(side='left', padx=1)
        ttk.Button(f, text='Zo->W', command=self._calc_ms_w, bootstyle='success', width=6).pack(side='left', padx=1)
        ttk.Label(f, text='Zo=').pack(side='left', padx=(2,0))
        ttk.Entry(f, textvariable=self.ms_z0_tgt, width=4).pack(side='left')

        self.ms_result = self._result(L, 3); self.ms_result.pack(fill='x', pady=2)
        self._formula(L, 'Er_eff=(Er+1)/2+(Er-1)/2*[1/sqrt(1+12h/W)+0.04(1-W/h)^2]\nZo=60/sqrt(Er_eff)*ln(8h/W+W/4h)\nZo=120pi/[sqrt(Er_eff)*(W/h+1.393+0.667*ln(W/h+1.444))]').pack(fill='x')
        draw_microstrip(R)

    # ==================== Stripline ====================
    def _build_sl(self, parent, r, c):
        sec = self._panel(parent, r, c, 'Stripline', 'primary')
        body = tk.Frame(sec, bg='#2b3e50'); body.pack(fill='both', expand=True)
        L = tk.Frame(body, bg='#2b3e50'); L.pack(side='left', fill='both', expand=True, padx=2)
        R = tk.Frame(body, bg='#2b3e50'); R.pack(side='right', padx=2)

        self.sl_er_var = tk.StringVar(value=str(ER_FR4))
        self.sl_h_var = tk.StringVar(value='1.6')
        self.sl_w_var = tk.StringVar(value='0.5')
        self.sl_z0_tgt = tk.StringVar(value='50')

        self._input(L, 'Er:',    'sl_er', str(ER_FR4))
        self._input(L, 'h(mm):', 'sl_h', '1.6')
        self._input(L, 'W(mm):', 'sl_w', '0.5')

        self._sep(L)
        f = tk.Frame(L, bg='#2b3e50'); f.pack(fill='x')
        ttk.Button(f, text='W->Zo', command=self._calc_sl_z0, bootstyle='primary', width=6).pack(side='left', padx=1)
        ttk.Button(f, text='Zo->W', command=self._calc_sl_w, bootstyle='success', width=6).pack(side='left', padx=1)
        ttk.Label(f, text='Zo=').pack(side='left', padx=(2,0))
        ttk.Entry(f, textvariable=self.sl_z0_tgt, width=4).pack(side='left')

        self.sl_result = self._result(L, 2); self.sl_result.pack(fill='x', pady=2)
        self._formula(L, 'Zo=60/sqrt(Er)*ln(4h/pi*W) W/h<0.35\nZo=94.15/[sqrt(Er)*(W/h+0.441)]\nEr_eff=Er (uniform)').pack(fill='x')
        draw_stripline(R)

    # ==================== CPW ====================
    def _build_cpw(self, parent, r, c):
        sec = self._panel(parent, r, c, 'CPW')
        body = tk.Frame(sec, bg='#2b3e50'); body.pack(fill='both', expand=True)
        L = tk.Frame(body, bg='#2b3e50'); L.pack(side='left', fill='both', expand=True, padx=2)
        R = tk.Frame(body, bg='#2b3e50'); R.pack(side='right', padx=2)

        self.cpw_w_var = tk.StringVar(value='0.5'); self.cpw_s_var = tk.StringVar(value='0.2')
        self.cpw_h_var = tk.StringVar(value='1.6'); self.cpw_er_var = tk.StringVar(value=str(ER_FR4))

        self._input(L, 'W(mm):', 'cpw_w', '0.5'); self._input(L, 'S(mm):', 'cpw_s', '0.2')
        self._input(L, 'h(mm):', 'cpw_h', '1.6'); self._input(L, 'Er:', 'cpw_er', str(ER_FR4))

        self._sep(L)
        ttk.Button(L, text='Calc Zo', command=self._calc_cpw, bootstyle='primary', width=8).pack(pady=0)
        self.cpw_result = self._result(L, 1); self.cpw_result.pack(fill='x', pady=2)
        self._formula(L, 'k=W/(W+2S) k\'=sqrt(1-k^2)\nZo=30pi/sqrt(Er_eff)*K(k\')/K(k)\nEr_eff=(Er+1)/2').pack(fill='x')
        draw_cpw(R)

    # ==================== Wavelength ====================
    def _build_wl(self, parent, r, c):
        sec = self._panel(parent, r, c, 'Wavelength & Skin Depth', 'primary')
        body = tk.Frame(sec, bg='#2b3e50'); body.pack(fill='both', expand=True)
        L = tk.Frame(body, bg='#2b3e50'); L.pack(side='left', fill='both', expand=True, padx=2)
        R = tk.Frame(body, bg='#2b3e50'); R.pack(side='right', fill='both', expand=True, padx=2)

        self.wl_freq_var = tk.StringVar(value='2450'); self.wl_freq_unit = tk.StringVar(value='MHz')
        self.wl_er_var = tk.StringVar(value='3.5')

        f = tk.Frame(L, bg='#2b3e50'); f.pack(fill='x', pady=0)
        ttk.Label(f, text='Freq:', width=11, anchor='e').pack(side='left', padx=1)
        ttk.Entry(f, textvariable=self.wl_freq_var, width=8).pack(side='left', padx=1)
        ttk.Combobox(f, textvariable=self.wl_freq_unit, values=['Hz','kHz','MHz','GHz'],
                     width=4, state='readonly', bootstyle='secondary').pack(side='left', padx=1)

        f2 = tk.Frame(L, bg='#2b3e50'); f2.pack(fill='x', pady=0)
        ttk.Label(f2, text='Er_eff:', width=11, anchor='e').pack(side='left', padx=1)
        ttk.Entry(f2, textvariable=self.wl_er_var, width=8).pack(side='left', padx=1)

        self._sep(L)
        ttk.Button(L, text='Calc', command=self._calc_wl, bootstyle='primary', width=8).pack(pady=0)
        self.wl_result = self._result(L, 3); self.wl_result.pack(fill='x', pady=1)
        self._formula(L, 'lambda0=c/f  lambdag=lambda0/sqrt(Er_eff)\nlambda/4=lambdag/4  delta=1/sqrt(pi*f*mu0*sigma)\nCu: sigma=5.8e7 mu0=4pi*1e-7').pack(fill='x')

        ref = ttk.Labelframe(R, text=' Ref ', padding=2, bootstyle='secondary'); ref.pack(fill='both', expand=True)
        rt = ttk.Text(ref, height=8, width=24, font=('Consolas', 7)); rt.pack(fill='both', expand=True)
        rt.insert('end', f'Er: FR4={ER_FR4} R4350={ER_ROGERS_4350}\n R4003={ER_ROGERS_4003}\nh: 62mil={H_062} 31={H_031} 20={H_020}\nCu:1oz={CU_1OZ}mm\n\nVSWR  RL    |G|\n1.5   14.0  0.20\n2.0    9.5  0.33\n3.0    6.0  0.50')
        rt.config(state='disabled')

    # ==================== Trace Loss ====================
    def _build_trace_loss(self, parent, r, c):
        sec = self._panel(parent, r, c, 'Trace Loss (ac + ad)')
        body = tk.Frame(sec, bg='#2b3e50'); body.pack(fill='both', expand=True)
        L = tk.Frame(body, bg='#2b3e50'); L.pack(side='left', fill='both', expand=True, padx=2)
        R = tk.Frame(body, bg='#2b3e50'); R.pack(side='right', padx=2)

        self.loss_type = tk.StringVar(value='Microstrip'); self.loss_er = tk.StringVar(value=str(ER_FR4))
        self.loss_ereff = tk.StringVar(value='3.8'); self.loss_tand = tk.StringVar(value='0.02 (FR4)')
        self.loss_freq = tk.StringVar(value='2450'); self.loss_freq_unit = tk.StringVar(value='MHz')
        self.loss_w = tk.StringVar(value='3.0'); self.loss_h = tk.StringVar(value='1.575')
        self.loss_z0 = tk.StringVar(value='50'); self.loss_len = tk.StringVar(value='50')

        self._input(L, 'Type:',   'loss_type', 'Microstrip', combo_vals=['Microstrip', 'Stripline'])
        self._input(L, 'Er:',     'loss_er', str(ER_FR4))
        self._input(L, 'Er_eff:', 'loss_ereff', '3.8')
        self._input(L, 'tanD:',   'loss_tand', '0.02 (FR4)',
                    combo_vals=['0.02 (FR4)','0.0037 (R4350B)','0.0027 (R4003C)','0.0013 (R3003)','0.0004 (PTFE)'])

        f = tk.Frame(L, bg='#2b3e50'); f.pack(fill='x', pady=0)
        ttk.Label(f, text='Freq:', width=11, anchor='e').pack(side='left', padx=1)
        ttk.Entry(f, textvariable=self.loss_freq, width=8).pack(side='left', padx=1)
        ttk.Combobox(f, textvariable=self.loss_freq_unit, values=['Hz','kHz','MHz','GHz'],
                     width=4, state='readonly', bootstyle='secondary').pack(side='left', padx=1)

        self._input(L, 'W(mm):',   'loss_w', '3.0'); self._input(L, 'h(mm):', 'loss_h', '1.575')
        self._input(L, 'Zo(ohm):', 'loss_z0', '50'); self._input(L, 'Len(mm):', 'loss_len', '50')

        self._sep(L)
        ttk.Button(L, text='Calc Loss', command=self._calc_trace_loss, bootstyle='primary', width=9).pack(pady=0)
        self.loss_result = self._result(L, 8); self.loss_result.pack(fill='x', pady=1)
        self._formula(L,
            'ac=8.686*Rs/(Zo*Weff) [dB/m]\nRs=sqrt(pi*f*mu0/sigma)\nad=27.3*Er/sqrt(Er_eff)*(Er_eff-1)/(Er-1)*tanD/lambda0\nKr=1+2/pi*atan(1.4(Rrms/delta)^2)').pack(fill='x')

        self.loss_sch = tk.Frame(R, bg='#2b3e50'); self.loss_sch.pack()
        draw_microstrip_loss(self.loss_sch, 3.0, 1.575)

    # ==================== TL Ref ====================
    def _build_tl_ref(self, parent, r, c):
        sec = self._panel(parent, r, c, 'Reference & VSWR Quick', 'primary')
        body = tk.Frame(sec, bg='#2b3e50', padx=3, pady=3); body.pack(fill='both', expand=True)
        rt = ttk.Text(body, height=14, width=34, font=('Consolas', 7)); rt.pack(fill='both', expand=True)
        rt.insert('end',
            '=== Substrates ===\n'
            f'FR4:       Er={ER_FR4} tanD=.020\n'
            f'R4350B:    Er={ER_ROGERS_4350} tanD=.0037\n'
            f'R4003C:    Er={ER_ROGERS_4003} tanD=.0027\n'
            f'R3003:     Er=3.00 tanD=.0013\n'
            f'PTFE:      Er=2.10 tanD=.0004\n\n'
            '=== Thickness ===\n'
            f'62mil={H_062}mm 31={H_031} 20={H_020}\n'
            f'Cu 1oz={CU_1OZ}mm\n\n'
            '=== VSWR Quick ===\n'
            'VSWR  RL(dB)  |G|\n'
            '1.0   inf     .00\n'
            '1.5   14.0    .20\n'
            '2.0    9.5    .33\n'
            '3.0    6.0    .50\n'
            '5.0    3.5    .67\n\n'
            '=== Skin Depth(Cu) ===\n'
            '1GHz 2.1um  2.4G 1.3um\n'
            '5GHz 0.9um  10G  0.7um')
        rt.config(state='disabled')

    # ==================== Calc methods (unchanged) ====================

    def _get_er_ms(self):
        c=self.ms_er_custom.get().strip(); return float(c) if c else float(self.ms_er_var.get())
    def _get_h_ms(self):
        c=self.ms_h_custom.get().strip(); return float(c) if c else float(self.ms_h_var.get())

    def _calc_ms_z0(self):
        try: w,t=float(self.ms_w_var.get()),float(self.ms_t_var.get())
        except: messagebox.showerror('Error','Invalid'); return
        er,h=self._get_er_ms(),self._get_h_ms(); z0,ereff=microstrip_impedance(w,h,er,t)
        self.ms_result.delete('1.0','end')
        self.ms_result.insert('end',f' W={w:.3f} h={h:.3f}\n Er_eff={ereff:.3f}\n Zo={z0:.2f} Ohm\n')

    def _calc_ms_w(self):
        try: z0t,t=float(self.ms_z0_tgt.get()),float(self.ms_t_var.get())
        except: messagebox.showerror('Error','Invalid'); return
        er,h=self._get_er_ms(),self._get_h_ms(); w,ereff=microstrip_width(z0t,h,er,t)
        self.ms_result.delete('1.0','end')
        self.ms_result.insert('end',f' Zo={z0t:.1f} h={h:.3f}\n W={w:.3f} mm\n Er_eff={ereff:.3f}\n')

    def _calc_sl_z0(self):
        try: w,h,er=float(self.sl_w_var.get()),float(self.sl_h_var.get()),float(self.sl_er_var.get())
        except: messagebox.showerror('Error','Invalid'); return
        self.sl_result.delete('1.0','end')
        self.sl_result.insert('end',f' W={w:.3f} h={h:.3f}\n Zo={stripline_impedance(w,h,er):.2f} Ohm\n')

    def _calc_sl_w(self):
        try: z0t,h,er=float(self.sl_z0_tgt.get()),float(self.sl_h_var.get()),float(self.sl_er_var.get())
        except: messagebox.showerror('Error','Invalid'); return
        self.sl_result.delete('1.0','end')
        self.sl_result.insert('end',f' Zo={z0t:.1f} h={h:.3f}\n W={stripline_width(z0t,h,er):.3f} mm\n')

    def _calc_cpw(self):
        try: w,s,h,er=float(self.cpw_w_var.get()),float(self.cpw_s_var.get()),float(self.cpw_h_var.get()),float(self.cpw_er_var.get())
        except: messagebox.showerror('Error','Invalid'); return
        self.cpw_result.delete('1.0','end')
        self.cpw_result.insert('end',f' W={w:.3f} S={s:.3f}\n Zo~{cpw_impedance(w,s,h,er):.2f} Ohm\n')

    def _calc_wl(self):
        f=self._get_freq(self.wl_freq_var,self.wl_freq_unit)
        if not f: return
        try: er_eff=float(self.wl_er_var.get())
        except: messagebox.showerror('Error','Invalid Er_eff'); return
        l0=C0/f; lg=guided_wavelength(f,er_eff); qw=quarter_wave_length(f,er_eff); d=skin_depth(f)
        self.wl_result.delete('1.0','end')
        self.wl_result.insert('end',f' f={f/1e6:.3f}MHz\n lambda0={l0*1e3:.2f}mm\n lambdag={lg*1e3:.2f}mm\n lambda/4={qw*1e3:.2f}mm\n delta(Cu)={d*1e6:.2f}um\n')

    def _calc_trace_loss(self):
        try:
            f=self._get_freq(self.loss_freq,self.loss_freq_unit)
            if not f: return
            lt=self.loss_type.get(); er=float(self.loss_er.get()); ereff=float(self.loss_ereff.get())
            tand=float(self.loss_tand.get().split()[0])
            w=float(self.loss_w.get()); h=float(self.loss_h.get()); z0=float(self.loss_z0.get()); L=float(self.loss_len.get())
        except: messagebox.showerror('Error','Invalid'); return
        r=microstrip_total_loss(w,h,z0,ereff,er,f,tand,L) if lt=='Microstrip' else stripline_total_loss(w,h,z0,er,f,tand,L)
        self.loss_result.delete('1.0','end')
        self.loss_result.insert('end',
            f' {lt} @ {r["freq_mhz"]:.0f}MHz tanD={tand} Zo={z0:.0f}Ohm L={L:.1f}mm\n\n'
            f' Conductor ac:\n  {r["conductor_loss_db_per_mm"]*1000:.2f} dB/m = {r["conductor_loss_db_per_mm"]:.4f} dB/mm\n\n'
            f' Dielectric ad:\n  {r["dielectric_loss_db_per_mm"]*1000:.2f} dB/m = {r["dielectric_loss_db_per_mm"]:.4f} dB/mm\n\n'
            f' Total Loss:\n  {r["total_loss_db_per_cm"]:.4f} dB/cm  |  {r["total_loss_db_per_mm"]*1000:.2f} dB/m\n'
            f'  {r["total_loss_db"]:.4f} dB (full len)\n'
            f' delta={r["skin_depth_um"]:.1f}um Kr={r["roughness_factor"]:.3f}\n')
        for wdg in self.loss_sch.winfo_children(): wdg.destroy()
        draw_microstrip_loss(self.loss_sch,w,h,tand) if lt=='Microstrip' else draw_stripline_loss(self.loss_sch,w,h,tand)
