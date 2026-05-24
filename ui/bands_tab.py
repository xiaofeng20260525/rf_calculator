"""3GPP NR/LTE band reference and channel converter tab."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..utils.bands import (
    NR_BANDS, LTE_BANDS, nrarfcn_to_freq, freq_to_nrarfcn,
    search_band_by_freq, get_band_info,
)

LW = 18
EW = 12


class BandsTab(ttk.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Top: Channel converter
        top = ttk.Frame(self, padding=5)
        top.pack(fill='x')

        self._build_converter(top)

        # Bottom: Band tables in notebook
        nb = ttk.Notebook(self, bootstyle='dark')
        nb.pack(fill='both', expand=True, padx=5, pady=5)

        for title, bands, columns in [
            (' NR FR1 ', NR_BANDS,
             ('Band', 'Name', 'UL Low', 'UL High', 'DL Low', 'DL High', 'Mode', 'PC(dBm)')),
            (' LTE ', LTE_BANDS,
             ('Band', 'Name', 'UL Low', 'UL High', 'DL Low', 'DL High', 'Mode', '')),
        ]:
            frm = ttk.Frame(nb)
            nb.add(frm, text=title)
            self._build_table(frm, bands, columns)

        # Search panel
        sf = ttk.Frame(self, padding=5)
        sf.pack(fill='x')
        self._build_search(sf)

    def _build_converter(self, parent):
        cv = ttk.Labelframe(parent, text=' NR-ARFCN ↔ 频率 转换 ', padding=8, bootstyle='info')
        cv.pack(fill='x', padx=3)

        f1 = ttk.Frame(cv)
        f1.pack(fill='x', pady=3)
        ttk.Label(f1, text='NR-ARFCN:', width=LW, anchor='e').pack(side='left', padx=3)
        self.arfcn_var = ttk.StringVar()
        ttk.Entry(f1, textvariable=self.arfcn_var, width=EW).pack(side='left', padx=3)
        ttk.Button(f1, text='→ 频率', command=self._arfcn_to_freq, bootstyle='primary', width=8).pack(side='left', padx=3)
        ttk.Label(f1, text='→').pack(side='left', padx=3)
        self.arfcn_freq_var = ttk.StringVar()
        ttk.Entry(f1, textvariable=self.arfcn_freq_var, width=EW, state='readonly').pack(side='left', padx=3)
        ttk.Label(f1, text='MHz').pack(side='left')

        f2 = ttk.Frame(cv)
        f2.pack(fill='x', pady=3)
        ttk.Label(f2, text='频率 (MHz):', width=LW, anchor='e').pack(side='left', padx=3)
        self.freq_arfcn_var = ttk.StringVar()
        ttk.Entry(f2, textvariable=self.freq_arfcn_var, width=EW).pack(side='left', padx=3)
        ttk.Button(f2, text='→ ARFCN', command=self._freq_to_arfcn, bootstyle='primary', width=8).pack(side='left', padx=3)
        ttk.Label(f2, text='→').pack(side='left', padx=3)
        self.freq_result_var = ttk.StringVar()
        ttk.Entry(f2, textvariable=self.freq_result_var, width=EW, state='readonly').pack(side='left', padx=3)
        ttk.Label(f2, text='(approx)', bootstyle='secondary').pack(side='left', padx=3)

    def _build_table(self, parent, bands, columns):
        """Build a scrollable Treeview table for band data."""
        cols = list(columns)
        tree = ttk.Treeview(parent, columns=cols, show='headings', height=18, bootstyle='dark')
        for c in cols:
            tree.heading(c, text=c, anchor='center')
            if c == 'Name':
                tree.column(c, width=130, anchor='center')
            elif 'Low' in c or 'High' in c:
                tree.column(c, width=75, anchor='center')
            else:
                tree.column(c, width=60, anchor='center')

        # Scrollbar
        sb = ttk.Scrollbar(parent, orient='vertical', command=tree.yview, bootstyle='round')
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        for b in bands:
            if len(b) == 8:
                values = list(b[:6]) + [b[6], str(b[7])]
            else:
                values = list(b)
            tree.insert('', 'end', values=values)

    def _build_search(self, parent):
        sf = ttk.Labelframe(parent, text=' 频率查 Band ', padding=8, bootstyle='secondary')
        sf.pack(fill='x', padx=3, pady=3)

        frm = ttk.Frame(sf)
        frm.pack(fill='x')
        ttk.Label(frm, text='频率 (MHz):', width=LW, anchor='e').pack(side='left', padx=3)
        self.search_freq_var = ttk.StringVar()
        ttk.Entry(frm, textvariable=self.search_freq_var, width=EW).pack(side='left', padx=3)
        ttk.Button(frm, text='搜索', command=self._search, bootstyle='primary', width=8).pack(side='left', padx=5)

        self.search_result = ttk.Text(sf, height=3, width=70, font=('Consolas', 9))
        self.search_result.pack(fill='x', pady=4)

    def _arfcn_to_freq(self):
        try:
            n = int(self.arfcn_var.get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效 NR-ARFCN')
            return
        f = nrarfcn_to_freq(n)
        if f is not None:
            self.arfcn_freq_var.set(f'{f:.3f}')
        else:
            self.arfcn_freq_var.set('无效ARFCN')

    def _freq_to_arfcn(self):
        try:
            f = float(self.freq_arfcn_var.get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效频率')
            return
        n = freq_to_nrarfcn(f)
        if n is not None:
            self.freq_result_var.set(str(n))
        else:
            self.freq_result_var.set('超出范围')

    def _search(self):
        try:
            f = float(self.search_freq_var.get())
        except ValueError:
            messagebox.showerror('Error', '请输入有效频率')
            return
        results = search_band_by_freq(f)
        self.search_result.delete('1.0', 'end')
        if not results:
            self.search_result.insert('end', f'未找到包含 {f} MHz 的频段\n')
        else:
            self.search_result.insert('end', f'包含 {f} MHz 的频段:\n')
            for b in results[:8]:
                ul_range = f'{b[2]}-{b[3]}' if b[2] > 0 else 'N/A'
                info = get_band_info(b[0])
                pc = f' PC={b[7]}dBm' if len(b) > 7 and b[7] else ''
                self.search_result.insert('end',
                    f'  {b[0]:5s} {b[1]:15s}  UL:{ul_range} MHz  DL:{b[4]}-{b[5]} MHz  {b[6]}{pc}\n')
