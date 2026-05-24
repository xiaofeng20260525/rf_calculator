"""Unit converter tab: dBm, dBW, W, dBμV, Vrms, dB ↔ linear, etc."""

import math
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..utils.constants import (
    dbm_to_watt, watt_to_dbm,
    dbm_to_dbw, dbw_to_dbm, dbw_to_watt, watt_to_dbw,
    dbm_to_dbuv, dbuv_to_dbm, dbuv_to_vrms, vrms_to_dbuv,
    dbm_to_dbmv, dbmv_to_dbm, dbuv_to_dbmv, dbmv_to_dbuv,
    vrms_to_vpeak, vpeak_to_vrms, vrms_to_vpp, vpp_to_vrms,
    watt_to_vrms, vrms_to_watt,
    db_to_linear, linear_to_db,
)

F_CONVERT = (
    '=== 功率换算 ===\n'
    'P(W)   = 10^((P(dBm) - 30) / 10)\n'
    'P(dBm) = 10·log₁₀(P(W)) + 30\n'
    'P(dBW) = P(dBm) - 30\n'
    '\n'
    '=== 电压换算 (@ Z₀) ===\n'
    'Vrms  = √(P(W) · Z₀)\n'
    'dBμV  = 20·log₁₀(Vrms × 10⁶)\n'
    '      = 20·log₁₀(Vrms) + 120\n'
    'dBmV  = dBμV - 60\n'
    'dBμV  = P(dBm) + 90 + 10·log₁₀(Z₀)\n'
    '  @50Ω:  dBμV = dBm + 107.0\n'
    '  @75Ω:  dBμV = dBm + 108.8\n'
    '\n'
    '=== 峰值电压 ===\n'
    'Vpeak = Vrms × √2\n'
    'Vpp   = 2 × Vpeak = 2·√2 × Vrms\n'
    '\n'
    '=== dB ↔ 线性 ===\n'
    'Ratio = 10^(dB/10)     [功率]\n'
    'Ratio = 10^(dB/20)     [电压]\n'
    'dB    = 10·log₁₀(Ratio) [功率]\n'
    'dB    = 20·log₁₀(Ratio) [电压]'
)


class ConverterTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._updating = False
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self, padding=3)
        main.pack(fill='both', expand=True)

        top = ttk.Frame(main, padding=10)
        top.pack(fill='both', expand=True)

        left = ttk.Frame(top)
        left.pack(side='left', fill='both', expand=True, padx=5)
        right = ttk.Frame(top)
        right.pack(side='right', fill='both', expand=True, padx=5)

        # --- Power ---
        pwr = ttk.Labelframe(left, text=' 功率换算 (Power) ', padding=12, bootstyle='info')
        pwr.pack(fill='x', pady=(0, 8))
        self._build_power(pwr)

        # --- dB / Linear ---
        rat = ttk.Labelframe(left, text=' dB ↔ 线性比值 ', padding=12, bootstyle='primary')
        rat.pack(fill='x', pady=(0, 8))
        self._build_ratio(rat)

        # --- Quick Reference ---
        ref = ttk.Labelframe(left, text=' 常用换算速查 ', padding=12, bootstyle='secondary')
        ref.pack(fill='x')
        self._build_ref(ref)

        # --- Voltage ---
        volt = ttk.Labelframe(right, text=' 电压换算 (Voltage) @ 参考阻抗 ', padding=12, bootstyle='info')
        volt.pack(fill='x', pady=(0, 8))
        self._build_voltage(volt)

        # --- Power ↔ Voltage @ Z ---
        imp = ttk.Labelframe(right, text=' 功率 ↔ 电压 (指定阻抗) ', padding=12, bootstyle='primary')
        imp.pack(fill='x', pady=(0, 8))
        self._build_impedance(imp)

        # --- Bottom: Formula panel ---
        bottom = ttk.Frame(main, padding=5)
        bottom.pack(fill='both', expand=True)

        fm = ttk.Labelframe(bottom, text=' 换算公式参考 ', padding=5, bootstyle='info')
        fm.pack(fill='both', expand=True, padx=3)

        t = ttk.Text(fm, font=('Consolas', 9), wrap='none', height=20)
        t.pack(fill='both', expand=True, padx=5, pady=5)
        t.insert('end', F_CONVERT)
        t.config(state='disabled')

    def _build_power(self, parent):
        self.pwr_vars = {}
        for i, (label, key) in enumerate([
            ('dBm:', 'dbm'), ('dBW:', 'dbw'),
            ('W (瓦特):', 'watt'), ('mW (毫瓦):', 'mw'),
        ]):
            ttk.Label(parent, text=label, width=14, font=('Segoe UI', 10)).grid(
                row=i, column=0, sticky='e', padx=3, pady=4)
            self.pwr_vars[key] = ttk.StringVar()
            ttk.Entry(parent, textvariable=self.pwr_vars[key], width=22).grid(
                row=i, column=1, padx=3, pady=4)
            # Use <FocusOut> instead of <KeyRelease> to avoid recursive issues
            getattr(self, f'_bind_pwr_{key}') if False else None

        # We need to bind each entry to _on_power_input with its key
        for key in self.pwr_vars:
            entry = parent.grid_slaves(row=list(self.pwr_vars.keys()).index(key), column=1)[0]
            entry.bind('<KeyRelease>', lambda e, k=key: self._on_power_input(k))

        bf = ttk.Frame(parent)
        bf.grid(row=4, column=0, columnspan=2, pady=6)
        for label, val in [('0 dBm', 0), ('10 dBm', 10), ('20 dBm', 20),
                           ('30 dBm', 30), ('-10 dBm', -10), ('-30 dBm', -30)]:
            ttk.Button(bf, text=label, width=8,
                       command=lambda v=val: self._set_power('dbm', v),
                       bootstyle='outline-secondary').pack(side='left', padx=2)

    def _bind_pwr_entries(self):
        """Entry bindings are set up in _build_power via grid_slaves."""
        pass

    def _build_ratio(self, parent):
        ttk.Label(parent, text='dB 值:', width=14, font=('Segoe UI', 10)).grid(
            row=0, column=0, sticky='e', padx=3, pady=4)
        self.db_var = ttk.StringVar()
        ttk.Entry(parent, textvariable=self.db_var, width=22).grid(row=0, column=1, padx=3, pady=4)
        parent.grid_slaves(row=0, column=1)[0].bind('<KeyRelease>', lambda e: self._on_db_input())

        ttk.Label(parent, text='线性比值:', width=14, font=('Segoe UI', 10)).grid(
            row=1, column=0, sticky='e', padx=3, pady=4)
        self.linear_var = ttk.StringVar()
        ttk.Entry(parent, textvariable=self.linear_var, width=22).grid(row=1, column=1, padx=3, pady=4)
        parent.grid_slaves(row=1, column=1)[0].bind('<KeyRelease>', lambda e: self._on_linear_input())

        bf = ttk.Frame(parent)
        bf.grid(row=2, column=0, columnspan=2, pady=6)
        for db_val in [3, 6, 10, 20, -3, -6, -10]:
            ttk.Button(bf, text=f'{db_val} dB', width=7,
                       command=lambda v=db_val: self._set_db(v),
                       bootstyle='outline-secondary').pack(side='left', padx=2)

    def _build_voltage(self, parent):
        # Z0 selector
        zr = ttk.Frame(parent)
        zr.pack(fill='x', pady=(0, 5))
        ttk.Label(zr, text='参考阻抗 Z₀:').pack(side='left', padx=2)
        self.volt_z0_var = ttk.StringVar(value='50')
        ttk.Entry(zr, textvariable=self.volt_z0_var, width=6).pack(side='left', padx=3)
        ttk.Label(zr, text='Ω', font=('Segoe UI', 10, 'bold')).pack(side='left')
        ttk.Button(zr, text='50Ω', width=4, command=lambda: self.volt_z0_var.set('50'),
                   bootstyle='outline-info').pack(side='left', padx=3)
        ttk.Button(zr, text='75Ω', width=4, command=lambda: self.volt_z0_var.set('75'),
                   bootstyle='outline-info').pack(side='left', padx=1)

        ef = ttk.Frame(parent)
        ef.pack(fill='x')

        self.volt_vars = {}
        for i, (label, key) in enumerate([
            ('dBμV:', 'dbuv'), ('dBmV:', 'dbmv'),
            ('Vrms:', 'vrms'), ('Vpeak (峰值):', 'vpeak'), ('Vpp (峰峰值):', 'vpp'),
        ]):
            ttk.Label(ef, text=label, width=16, font=('Segoe UI', 10)).grid(
                row=i, column=0, sticky='e', padx=3, pady=3)
            self.volt_vars[key] = ttk.StringVar()
            ttk.Entry(ef, textvariable=self.volt_vars[key], width=22).grid(
                row=i, column=1, padx=3, pady=3)
            ef.grid_slaves(row=i, column=1)[0].bind(
                '<KeyRelease>', lambda e, k=key: self._on_voltage_input(k))

        bf = ttk.Frame(ef)
        bf.grid(row=5, column=0, columnspan=2, pady=6)
        for label, val in [('0 dBμV', 0), ('60 dBμV', 60), ('107 dBμV', 107), ('120 dBμV', 120)]:
            ttk.Button(bf, text=label, width=10,
                       command=lambda v=val: self._set_voltage('dbuv', v),
                       bootstyle='outline-secondary').pack(side='left', padx=2)

    def _build_impedance(self, parent):
        f = ttk.Frame(parent)
        f.pack(fill='x')

        ttk.Label(f, text='阻抗 Z₀ (Ω):', width=16, font=('Segoe UI', 10)).grid(
            row=0, column=0, sticky='e', padx=3, pady=3)
        self.imp_z0_var = ttk.StringVar(value='50')
        ttk.Entry(f, textvariable=self.imp_z0_var, width=22).grid(row=0, column=1, padx=3, pady=3)

        ttk.Label(f, text='功率 (dBm):', width=16, font=('Segoe UI', 10)).grid(
            row=1, column=0, sticky='e', padx=3, pady=3)
        self.imp_dbm_var = ttk.StringVar()
        e1 = ttk.Entry(f, textvariable=self.imp_dbm_var, width=22)
        e1.grid(row=1, column=1, padx=3, pady=3)
        e1.bind('<KeyRelease>', lambda e: self._on_imp_dbm())

        ttk.Label(f, text='功率 (W):', width=16, font=('Segoe UI', 10)).grid(
            row=2, column=0, sticky='e', padx=3, pady=3)
        self.imp_watt_var = ttk.StringVar()
        e2 = ttk.Entry(f, textvariable=self.imp_watt_var, width=22)
        e2.grid(row=2, column=1, padx=3, pady=3)
        e2.bind('<KeyRelease>', lambda e: self._on_imp_watt())

        ttk.Label(f, text='Vrms:', width=16, font=('Segoe UI', 10)).grid(
            row=3, column=0, sticky='e', padx=3, pady=3)
        self.imp_vrms_var = ttk.StringVar()
        e3 = ttk.Entry(f, textvariable=self.imp_vrms_var, width=22)
        e3.grid(row=3, column=1, padx=3, pady=3)
        e3.bind('<KeyRelease>', lambda e: self._on_imp_vrms())

        ttk.Label(f, text='Vpeak:', width=16, font=('Segoe UI', 10)).grid(
            row=4, column=0, sticky='e', padx=3, pady=3)
        self.imp_vpeak_var = ttk.StringVar()
        ttk.Entry(f, textvariable=self.imp_vpeak_var, width=22, state='readonly').grid(row=4, column=1, padx=3, pady=3)

        ttk.Label(f, text='I (mA, RMS):', width=16, font=('Segoe UI', 10)).grid(
            row=5, column=0, sticky='e', padx=3, pady=3)
        self.imp_irms_var = ttk.StringVar()
        ttk.Entry(f, textvariable=self.imp_irms_var, width=22, state='readonly').grid(row=5, column=1, padx=3, pady=3)

        ttk.Button(parent, text='计算', command=self._calc_impedance_all, bootstyle='primary').pack(pady=5)

    def _build_ref(self, parent):
        t = ttk.Text(parent, height=9, width=50, font=('Consolas', 9))
        t.pack(fill='both', expand=True)
        t.insert('end', '  dBm       W          Vrms(50Ω)   Vrms(75Ω)\n')
        t.insert('end', '  ' + '─' * 50 + '\n')
        for dbm, w, v50, v75 in [
            (-30, '1 μW', '7.07 mV', '8.66 mV'),
            (-20, '10 μW', '22.4 mV', '27.4 mV'),
            (-10, '100 μW', '70.7 mV', '86.6 mV'),
            (0, '1 mW', '224 mV', '274 mV'),
            (10, '10 mW', '707 mV', '866 mV'),
            (20, '100 mW', '2.24 V', '2.74 V'),
            (30, '1 W', '7.07 V', '8.66 V'),
            (40, '10 W', '22.4 V', '27.4 V'),
            (50, '100 W', '70.7 V', '86.6 V'),
        ]:
            t.insert('end', f'  {dbm:>4}   {w:>8s}   {v50:>10s}   {v75:>10s}\n')
        t.config(state='disabled')

    def _get_z0(self, var):
        try:
            return float(var.get())
        except ValueError:
            return 50.0

    # --- Power ---
    def _on_power_input(self, source):
        if self._updating:
            return
        self._updating = True
        try:
            val = float(self.pwr_vars[source].get())
        except ValueError:
            self._updating = False; return

        try:
            dbm_map = {
                'dbm': val, 'dbw': dbw_to_dbm(val),
                'watt': watt_to_dbm(val), 'mw': watt_to_dbm(val / 1000),
            }
            dbm = dbm_map.get(source, 0)
            if math.isinf(dbm):
                self._updating = False; return

            self.pwr_vars['dbm'].set(f'{dbm:.4f}')
            self.pwr_vars['dbw'].set(f'{dbm_to_dbw(dbm):.4f}')
            w = dbm_to_watt(dbm)
            self.pwr_vars['watt'].set(f'{w:.6e}')
            self.pwr_vars['mw'].set(f'{w * 1000:.6e}')
        except (ValueError, OverflowError):
            pass
        self._updating = False

    def _set_power(self, key, val):
        self.pwr_vars[key].set(str(val))
        self._on_power_input(key)

    # --- Voltage ---
    def _on_voltage_input(self, source):
        if self._updating:
            return
        self._updating = True
        try:
            val = float(self.volt_vars[source].get())
        except ValueError:
            self._updating = False; return

        try:
            vrms_map = {
                'dbuv': dbuv_to_vrms(val), 'dbmv': dbuv_to_vrms(dbmv_to_dbuv(val)),
                'vrms': val, 'vpeak': vpeak_to_vrms(val), 'vpp': vpp_to_vrms(val),
            }
            vrms = vrms_map.get(source, 0)
            if vrms <= 0:
                self._updating = False; return

            dbuv = vrms_to_dbuv(vrms)
            self.volt_vars['dbuv'].set(f'{dbuv:.2f}')
            self.volt_vars['dbmv'].set(f'{dbuv_to_dbmv(dbuv):.2f}')
            self.volt_vars['vrms'].set(f'{vrms:.6e}')
            self.volt_vars['vpeak'].set(f'{vrms_to_vpeak(vrms):.6e}')
            self.volt_vars['vpp'].set(f'{vrms_to_vpp(vrms):.6e}')
        except (ValueError, OverflowError):
            pass
        self._updating = False

    def _set_voltage(self, key, val):
        self.volt_vars[key].set(str(val))
        self._on_voltage_input(key)

    # --- dB / Linear ---
    def _on_db_input(self):
        if self._updating:
            return
        self._updating = True
        try:
            self.linear_var.set(f'{db_to_linear(float(self.db_var.get())):.6e}')
        except ValueError:
            pass
        self._updating = False

    def _on_linear_input(self):
        if self._updating:
            return
        self._updating = True
        try:
            self.db_var.set(f'{linear_to_db(float(self.linear_var.get())):.4f}')
        except ValueError:
            pass
        self._updating = False

    def _set_db(self, val):
        self.db_var.set(str(val))
        self._on_db_input()

    # --- Impedance ---
    def _on_imp_dbm(self):
        if self._updating:
            return
        self._updating = True
        try:
            dbm = float(self.imp_dbm_var.get())
            z0 = self._get_z0(self.imp_z0_var)
            w = dbm_to_watt(dbm)
            vrms = watt_to_vrms(w, z0)
            self.imp_watt_var.set(f'{w:.6e}')
            self.imp_vrms_var.set(f'{vrms:.6e}')
            self.imp_vpeak_var.set(f'{vrms_to_vpeak(vrms):.6e}')
            self.imp_irms_var.set(f'{vrms / z0 * 1000:.4f}')
        except ValueError:
            pass
        self._updating = False

    def _on_imp_watt(self):
        if self._updating:
            return
        self._updating = True
        try:
            w = float(self.imp_watt_var.get())
            z0 = self._get_z0(self.imp_z0_var)
            dbm = watt_to_dbm(w)
            vrms = watt_to_vrms(w, z0)
            self.imp_dbm_var.set(f'{dbm:.4f}')
            self.imp_vrms_var.set(f'{vrms:.6e}')
            self.imp_vpeak_var.set(f'{vrms_to_vpeak(vrms):.6e}')
            self.imp_irms_var.set(f'{vrms / z0 * 1000:.4f}')
        except ValueError:
            pass
        self._updating = False

    def _on_imp_vrms(self):
        if self._updating:
            return
        self._updating = True
        try:
            vrms = float(self.imp_vrms_var.get())
            z0 = self._get_z0(self.imp_z0_var)
            w = vrms_to_watt(vrms, z0)
            dbm = watt_to_dbm(w)
            self.imp_dbm_var.set(f'{dbm:.4f}')
            self.imp_watt_var.set(f'{w:.6e}')
            self.imp_vpeak_var.set(f'{vrms_to_vpeak(vrms):.6e}')
            self.imp_irms_var.set(f'{vrms / z0 * 1000:.4f}')
        except ValueError:
            pass
        self._updating = False

    def _calc_impedance_all(self):
        if self.imp_dbm_var.get():
            self._on_imp_dbm()
        elif self.imp_watt_var.get():
            self._on_imp_watt()
        elif self.imp_vrms_var.get():
            self._on_imp_vrms()
