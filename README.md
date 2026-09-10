<div align="center">

# 西门子安装助手 · SiemensInstallHelper

**免环境依赖 · 双击即用 · 自动处理 TIA Portal / STEP 7 / WinCC / S7-PLCSIM 安装期的各种问题**

> English: A zero-dependency Windows helper that automates the pain points of installing Siemens TIA Portal / STEP 7 / WinCC — cleans conflicting processes, analyzes installer logs, auto-fixes what it can (license service, pending-reboot flags, leftover processes), finds the installer on any disk including USB drives, checks VC++/.NET runtimes, downloads official runtimes, monitors the installation live, and generates offline reports or a guided help page when it cannot fix things itself.

**Language：Python · 平台：Windows 10/11 · 许可：MIT**

*本项目由 AI 辅助开发（AI-assisted project）*

**🌐 国内访问 GitHub 较慢？→ 推荐使用 [腾讯云 CNB 仓库](https://cnb.cool/CPY_personaluse/cpyinternalprojects/SiemensInstallHelper)（国内访问更快）**

</div>

---

## ✨ 功能特性

| # | 功能 | 说明 |
|---|---|---|
| 🛡 | **防误报提醒** | 启动时检测常见安全软件（火绒 / 联想管家 / 360 / 腾讯管家 / 金山 / 百度 / Defender），提示加白名单，避免绿色单文件被误报 |
| ⑪ | **自动寻找安装程序** | 扫描所有磁盘（含 U 盘 / 移动硬盘 / 光盘），智能排序找出安装总入口（`Start.exe` 等），选中后自动提权启动 |
| ② | **智能分析日志** | 自动定位安装日志（SIA_\*.log 等），**能自动修的自动修**：授权服务异常→自动启动、占用安装的进程→自动清理、要求重启→自动处理待重启残留标记（先备份可回滚）；修不了的才弹出**求助引导页** |
| ① | **清理无用进程** | 白名单制：只清浏览器/聊天/网盘等第三方进程，**系统与杀毒进程绝不碰** |
| ③ | **授权检查** | 检查 Automation License Manager（almservice）是否正常，异常时自动启动 |
| ④ | **运行库检查** | 检测 .NET Framework 4.8 / 3.5 / VC++ 运行库是否齐全 |
| ⑥⑦ | **运行库下载安装** | 从**微软官方源**自动下载并静默安装 VC++ 2015-2022（x64/x86） |
| ⑤ | **实时监控** | 安装期间盯着日志，出现报错立即提示并给出建议 |
| ⑧ | **离线报错报告** | 一键生成系统信息+日志+建议的报告 txt，**离网时发给 AI / 开发者即可人工分析** |
| ⑨ | **联网查错引导页** | 自动抓取错误 → 生成**可复制话术模板** → 一键搜索 → GitHub / 腾讯云 CNB 提交入口 |
| 💠 | **高分屏适配** | DPI 感知，4K 高分屏下字体不发虚 |

**零依赖承诺**：exe 用 PyInstaller 打包，**目标电脑不需要装 Python、不需要任何运行库**，拷贝即用。

---

## 🚀 快速开始

### 方式一：直接用 exe（推荐，给同学/非技术用户）

1. 拷贝整个 `SiemensInstallHelper` 文件夹到目标电脑（U 盘即可）
2. 双击 **`SiemensInstallHelper.exe`**（或 `启动-西门子安装助手.bat`）
3. 若杀软弹拦截提示：先在杀软里**添加信任/白名单**，或临时退出后运行（装完记得恢复）
4. 点 **⑪ 寻找安装程序** → 选中安装入口 → 自动提权启动 → 装的过程点 **⑤ 实时监控**

### 方式二：源码运行（需要 Python 3，标准库即可）

```bash
python run_install.py                 # 图形界面
python siemens_install.py clean       # 命令行：清理第三方进程
python siemens_install.py log         # 命令行：智能分析日志
python siemens_install.py find        # 命令行：寻找安装程序
python siemens_install.py runtime     # 检查运行库
python siemens_install.py report      # 导出离线报错报告
```

---

## 🔨 构建 exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name SiemensInstallHelper run_install.py
```

产物在 `dist\SiemensInstallHelper.exe`，拷回项目根目录即可分发。

---

## 📁 项目结构

```
SiemensInstallHelper/
├── SiemensInstallHelper.exe    # 打包好的免环境版（分发用）
├── run_install.py              # 打包入口（无参=GUI，带参=命令行）
├── gui_siemens_install.py      # 图形界面
├── siemens_install.py          # 核心逻辑（寻找安装/分析/修复/运行库/监控/报告）
├── 启动-西门子安装助手.bat      # 双击启动入口
├── 运行库/                     # 自动下载的 VC++ 运行库（微软官方源）
└── backup/                     # 自动生成的注册表/源码备份（可回滚）
```

---

## 🤝 贡献 / 反馈

安装报错种类繁多，欢迎贡献新案例：

- 遇到**没被知识库识别**的新报错：把报错关键词 + 解决办法提交 issue，我们会合并进内置知识库
- 提交入口：
  - **GitHub**：`https://github.com/chenpiyanghappy/SiemensInstallHelper`
  - **腾讯云 CNB**：`https://cnb.cool/CPY_personaluse/cpyinternalprojects/SiemensInstallHelper`
- 建议模板：
  > 系统：Win11 22H2 ｜ 软件：TIA Portal V20 ｜ 报错关键词：`InstallFailure HelpViewer_Server` ｜ 解决办法：……

---

## 🙏 致谢

本项目由 **AI 辅助开发**（豆包 Doubao AI）：参与功能设计、代码编写、Bug 修复、文档整理与发布流程。

---

## ⚖️ 免责声明与合规

- ✅ 本项目**不包含任何授权生成、破解、绕过技术保护措施的功能**，请配合西门子官方正版授权使用
- ✅ 工具只做白名单制进程清理与只读分析；不删除、不移动、不修改任何西门子安装文件
- ✅ 自动修复动作（启动服务 / 清理待重启残留标记）执行前**自动备份**，可回滚
- ⚠️ 本项目按 **MIT** 许可发布（如需要可自行更换），按“现状”提供，不提供任何明示或默示担保；使用后果自负
- ℹ️ 与西门子（Siemens AG）无任何关联，非官方工具

---

<div align="center">

**Made with 💙 by an AI-assisted project — 有问题欢迎提 Issue**

</div>
