#!/usr/bin/env python3
"""RF Calculator - 射频计算工具箱

Usage:
    python main.py
"""

import sys
import os

_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from rf_calculator.app import main

if __name__ == '__main__':
    main()
