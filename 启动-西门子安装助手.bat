@echo off
chcp 65001 >nul
title 西门子安装助手
cd /d "%~dp0"
rem 优先使用免 Python 的 exe 版；没有 exe 时退回 PowerShell 版（系统自带，零依赖）
if exist "%~dp0SiemensInstallHelper.exe" (
    start "" "%~dp0SiemensInstallHelper.exe"
    exit
)
if exist "%~dp0SiemensInstallHelper.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0SiemensInstallHelper.ps1"
)
