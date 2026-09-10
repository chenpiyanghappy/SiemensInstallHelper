#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西门子安装助手 · 打包入口
==========================
无参数启动 → 图形界面（推荐）
带参数运行 → 命令行模式（clean / log / license / runtime / watch）
供 PyInstaller 打包为单文件 exe 使用。
"""

import sys


def main():
    if len(sys.argv) > 1:
        from siemens_install import main as cli_main
        cli_main()
    else:
        from gui_siemens_install import run_gui
        run_gui()


if __name__ == "__main__":
    main()
