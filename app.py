"""RF Calculator - Main application window with ttkbootstrap modern theme."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

from .ui.impedance_tab import ImpedanceTab
from .ui.link_budget_tab import LinkBudgetTab
from .ui.transmission_line_tab import TransmissionLineTab
from .ui.converter_tab import ConverterTab
from .ui.bands_tab import BandsTab
from .ui.system_tab import SystemTab
from .ui.data_rate_tab import DataRateTab


class RFCalculatorApp:
    """Main RF Calculator application."""

    def __init__(self):
        self.root = ttk.Window(themename='darkly', title='RF Calculator - 射频计算工具箱',
                               size=(1350, 950), minsize=(1100, 750))
        self.root.iconname('RF Calculator')

        self._build_menu()
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg='#2b3e50', fg='#dfe4ea', activebackground='#375a7f',
                          activeforeground='white', bd=0)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, bg='#2b3e50', fg='#dfe4ea',
                            activebackground='#375a7f')
        menubar.add_cascade(label=' 文件 ', menu=file_menu)
        file_menu.add_command(label=' 退出 ', command=self.root.quit, accelerator='Ctrl+Q')

        help_menu = tk.Menu(menubar, tearoff=0, bg='#2b3e50', fg='#dfe4ea',
                            activebackground='#375a7f')
        menubar.add_cascade(label=' 帮助 ', menu=help_menu)
        help_menu.add_command(label=' 关于 RF Calculator ', command=self._show_about)

    def _build_header(self):
        header = ttk.Frame(self.root, padding=(20, 15, 20, 10))
        header.pack(fill='x')
        ttk.Label(header, text='RF Calculator', font=('Segoe UI', 20, 'bold'),
                  bootstyle='inverse-primary').pack(side='left')
        ttk.Label(header, text='射频计算工具箱', font=('Segoe UI', 12),
                  bootstyle='inverse-secondary').pack(side='left', padx=15)
        ttk.Separator(self.root, bootstyle='secondary').pack(fill='x', padx=10)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root, bootstyle='dark')
        self.notebook.pack(fill='both', expand=True, padx=15, pady=(10, 5))

        self.impedance_tab = ImpedanceTab(self.notebook)
        self.notebook.add(self.impedance_tab, text='  阻抗匹配 & Smith圆图  ')

        self.link_budget_tab = LinkBudgetTab(self.notebook)
        self.notebook.add(self.link_budget_tab, text='  链路预算 & 级联噪声  ')

        self.tl_tab = TransmissionLineTab(self.notebook)
        self.notebook.add(self.tl_tab, text='  传输线 & PCB计算  ')

        self.converter_tab = ConverterTab(self.notebook)
        self.notebook.add(self.converter_tab, text='  单位换算  ')

        self.system_tab = SystemTab(self.notebook)
        self.notebook.add(self.system_tab, text='  系统分析  ')

        self.bands_tab = BandsTab(self.notebook)
        self.notebook.add(self.bands_tab, text='  频段速查  ')

        self.data_rate_tab = DataRateTab(self.notebook)
        self.notebook.add(self.data_rate_tab, text='  速率计算  ')

    def _build_statusbar(self):
        bar = ttk.Frame(self.root, padding=(15, 6))
        bar.pack(side='bottom', fill='x')
        ttk.Label(bar, text='RF Calculator v2.0  |  Python + ttkbootstrap + Matplotlib',
                  font=('Segoe UI', 8), bootstyle='secondary').pack(side='left')
        ttk.Label(bar, text='阻抗匹配 | 链路预算 | 微带线 | 单位换算 | 系统分析 | 频段速查 | 速率计算',
                  font=('Segoe UI', 8), bootstyle='secondary').pack(side='right')

    def _show_about(self):
        import tkinter.messagebox as mb
        mb.showinfo('关于 RF Calculator',
                    'RF Calculator v2.0\n\n'
                    '手机射频计算工具箱\n\n'
                    '功能模块:\n'
                    '  1. 阻抗匹配 & Smith圆图\n'
                    '  2. 链路预算 & 噪声级联\n'
                    '  3. 传输线 & PCB计算\n'
                    '  4. 单位换算\n'
                    '  5. 系统分析 (IIP3/Desense/PAE)\n'
                    '  6. 3GPP NR/LTE 频段速查\n\n'
                    'Build with Python + ttkbootstrap + Matplotlib')

    def run(self):
        self.root.mainloop()


def main():
    app = RFCalculatorApp()
    app.run()


if __name__ == '__main__':
    main()
