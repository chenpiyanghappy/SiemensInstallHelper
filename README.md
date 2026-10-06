<div align="center">

# 西门子安装助手 · SiemensInstallHelper

**免环境依赖 · 双击即用 · 自动处理 TIA Portal / STEP 7 / WinCC / S7-PLCSIM 安装期的各种问题**

> **当前版本：v1.0**（v1.1「安装护航」功能已开发完成，正在内测，正式版随代码发布）

> English: A zero-dependency Windows helper that automates the pain points of installing Siemens TIA Portal / STEP 7 / WinCC — cleans conflicting processes, analyzes installer logs, auto-fixes what it can (license service, pending-reboot flags, leftover processes), finds the installer on any disk including USB drives, checks VC++/.NET runtimes, downloads official runtimes, monitors the installation live, and generates offline reports or a guided help page when it cannot fix things itself.

**Language：Python · 平台：Windows 10/11 · 许可：MIT**

*本项目由 AI 辅助开发（AI-assisted project）*

**🌐 国内访问 GitHub 较慢？→ 推荐使用 [腾讯云 CNB 仓库](https://cnb.cool/chenpiyanghappy/SiemensInstallHelper)（国内访问更快）**

</div>

---

## ✨ 功能特性

| # | 功能 | 说明 |
|---|---|---|
| 🛡 | **防误报提醒** | 启动时检测常见安全软件（火绒 / 联想管家 / 360 / 腾讯管家 / 金山 / 百度 / Defender），提示加白名单，避免绿色单文件被误报 |
| ⑪ | **自动寻找安装程序** | 扫描所有磁盘（含 U 盘 / 移动硬盘 / 光盘），**只保留安装包总入口（`Start.exe / Setup.exe`）**，自动过滤 InstData/Components 组件安装器与已装程序启动器，选中后自动提权启动 |
| ② | **智能分析日志** | 自动定位安装日志（SIA_\*.log 等），**能自动修的自动修**：授权服务异常→自动启动、占用安装的进程→自动清理、要求重启→自动处理待重启残留标记（先备份可回滚）；修不了的才弹出**求助引导页** |
| ① | **清理无用进程** | 白名单制：只清浏览器/聊天/网盘等第三方进程，**系统与杀毒进程绝不碰** |
| ③ | **授权检查** | 检查 Automation License Manager（almservice）是否正常，异常时自动启动 |
| ④ | **运行库检查** | 检测 .NET Framework 4.8 / 3.5 / VC++ 运行库是否齐全 |
| ⑥⑦ | **运行库下载安装** | 从**微软官方源**自动下载并静默安装 VC++ 2015-2022（x64/x86） |
| ⑤ | **实时监控 + 卡住预警** | 安装期间盯着日志，出现报错立即提示并给出建议；**日志长时间无更新时自动弹窗预警**，附排查指引（杀软拦截 / 隐藏窗口 / 真卡死），可选继续等待或停止监控 |
| 🆕 | **错误大白话翻译** | 把"安装程序错误 / 缺 xxx.dll / 0x7E"等翻译成**大白话 + 操作步骤**（缺 VC++ 运行库 / 需重启 / 权限不足…），小白也能看懂怎么修 |
| 🆕 | **弹窗指引手动修复** | 无法自动下载/修复时，弹窗给出**官方下载链接 + 逐步操作**，用户自己下载安装后继续；监控时还会提示"复制给同学"互助 |
| ⑧ | **离线报错报告** | 一键生成系统信息 + **脱敏环境快照** + 日志 + 建议的报告 txt，**离网时发给 AI / 开发者即可人工分析** |
| ⑨ | **联网查错引导页** | 自动抓取错误 → 生成**可复制话术模板** → 一键搜索 → GitHub / 腾讯云 CNB 提交入口 |
| ⑫ | **复制基础信息** | 自动采集 TIA 版本 / 系统版本 / 工具版本，一键复制，提交 Issue 直接粘贴 |
| ⑬ | **安装前体检** | 安装前 9 项体检：管理员权限 / 磁盘空间 / 内存 / .NET / VC++ / 授权服务 / 待重启标记 / 杀软 / 安装路径建议 |
| ⑭ | **复制反馈模板** | 一键复制「这条方案是否有用」反馈模板（微信 / 邮箱渠道） |
| ⑮ | **复制Issue模板** | 一键生成完整预填充 Issue（问题描述 / 复现步骤 / 报错 / 环境 / 日志 / 已尝试），粘贴到 GitHub / CNB 即提交 |
| ⑯ | **知识小贴士** | 内置安装/环境/排障贴士 + **用户自定义**（GUI 增删改，不碰源码）；一键导出 **PR 贡献素材**（自学 Git 后可向仓库提交） |
| 💠 | **高分屏适配** | DPI 感知，4K 高分屏下字体不发虚 |

**零依赖承诺**：exe 用 PyInstaller 打包，**目标电脑不需要装 Python、不需要任何运行库**，拷贝即用。

---

## 📚 文档

- [📄 免责声明（DISCLAIMER）](docs/免责声明.md) — 非官方工具声明 / 用途边界 / 风险自负
- [❓ 提问的艺术（How to Ask）](docs/提问的艺术.md) — 提问模板 / 提 PR 流程 / 邮箱联系 / 沟通公约

---

## 🏷 版本命名规则

`V(大版本).(功能版本).(修复版本)`

| 段位 | 什么时候改 |
|------|-----------|
| **大版本** | 有**非常重磅**的功能更新时（如 v2.0 合并为"西门子百宝箱"） |
| **功能版本** | 普通新功能更新时 |
| **修复版本** | 修复 Bug 时 |

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
python siemens_install.py basic-info  # 复制基础信息（写剪贴板）
python siemens_install.py snapshot    # 导出脱敏环境快照
python siemens_install.py preflight   # 安装前体检
python siemens_install.py feedback    # 复制反馈模板（写剪贴板）
python siemens_install.py issue-template  # 复制预填充 Issue 模板（写剪贴板）
python siemens_install.py tips list   # 小贴士：列出全部
python siemens_install.py tips search <关键词>  # 小贴士：搜索
python siemens_install.py tips add --title "标题" --content "内容" --category 安装 --tags a,b  # 新增
python siemens_install.py tips delete <id>  # 删除用户贴士
python siemens_install.py tips export # 导出 PR 贡献素材（默认输出到 贡献素材/ 目录）
```

---

## 📌 版本命名规则

版本号格式：**`V(大版本).(功能版本).(修复版本)`**

- **大版本**：有非常重磅的功能更新时才改（如 2.0 更名 SiBox / SiChest 百宝箱）
- **功能版本**：普通新功能更新
- **修复版本**：修 Bug

**正式版**在版本号前加平台前缀，用于区分下载源、隔离各平台对象存储地址（防止爬虫拼接链接薅流量）：

| 平台 | 前缀 | 示例 |
|---|---|---|
| GitHub | `CNPROGit` | `CNPROGit-V1.1.0` |
| 腾讯云 CNB 制品 | `CNPROCNB` | `CNPROCNB-V1.1.0`（仅 zip 类；EXE 不支持，跳转 GitHub） |
| 官网 | `CNPROWeb` | `CNPROWeb-V1.1.0` |

测试版 / 开发版不遵循平台前缀。每个版本单独新建文件夹，双平台 tag / 附件名版本号部分保持一致。

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
├── siemens_install.py          # 核心逻辑（寻找安装/分析/修复/运行库/监控/报告/体检/模板）
├── tips.py                     # 知识小贴士：内置 tips.json + 用户 user_tips.json 管理、导出贡献素材
├── tips.json                   # 官方内置贴士（只读，随版本发布）
├── user_tips.json              # 用户自定义贴士（GUI 增删改，首次使用自动生成）
├── CHANGELOG.md                # 完整技术改动与彩蛋备注（对外概要见各 Release）
├── 启动-西门子安装助手.bat      # 双击启动入口
├── 运行库/                     # 自动下载的 VC++ 运行库（微软官方源）
├── docs/                       # 功能规划 / Release 概要 / 新功能说明等
├── .github/ISSUE_TEMPLATE/     # GitHub Issue 预填充模板（报错求助 + 知识库贡献）
├── .gitlab/issue_templates/    # CNB（GitLab 兼容）Issue 模板
└── backup/                     # 自动生成的注册表/源码备份（可回滚）
```

---

## 🗂 小贴士怎么用

- **浏览**：点「⑯ 知识小贴士」→ 左侧列表选贴士，右侧看详情；顶部可搜索关键词
- **自定义**：点「＋ 新增贴士」添加你自己的经验（标题/分类/内容/标签）；「✎ 编辑」「－ 删除」管理自己的贴士；内置贴士只读，不可改删
- **恢复默认**：「↺ 恢复默认」清空全部自定义贴士，回到仅内置状态
- **向仓库贡献**：「⇪ 导出贡献素材」一键生成 `tips_contribution.json` + `CONTRIBUTING_TIPS.md`（含提交说明），自学 Git 后即可向 GitHub / CNB 提 Pull Request / 合并请求，管理员审核后并入内置贴士库

---

## 🤝 贡献 / 反馈

安装报错种类繁多，欢迎贡献新案例。**GitHub / CNB 的 New Issue 页面已内置预填充模板**（报错求助 / 知识库贡献），配合工具的 **⑫ 复制基础信息 / ⑮ 复制Issue模板**，粘贴环境信息即可，不用自己组织格式。

- 遇到**没被知识库识别**的新报错：用「知识库贡献」模板提交报错关键词 + 解决办法，管理员核对后并入内置知识库
- 提交入口：
  - **GitHub**：`https://github.com/chenpiyanghappy/SiemensInstallHelper`
  - **腾讯云 CNB**：`https://cnb.cool/chenpiyanghappy/SiemensInstallHelper`
- 建议模板：
  > 系统：Win11 22H2 ｜ 软件：TIA Portal V20 ｜ 报错关键词：`InstallFailure HelpViewer_Server` ｜ 解决办法：……

---

## 🙏 致谢

本项目由 **AI 辅助开发**（豆包 Doubao AI）：参与功能设计、代码编写、Bug 修复、文档整理与发布流程。

---

## 💡 为什么同时留存「原始报错 + 中文解读」

- **原始底层日志 / 错误码 / 官方支持链接**：留给技术人员深度排查，避免中文转述丢失关键细节
- **面向用户的中文大白话 + 可执行操作指引**：不假设用户懂 DLL / .NET / 运行库，直接告诉"现在发生了什么、下一步点什么"
- 工业软件底层报错常保留英文（如缺 xxx.dll），工具会翻译含义并解释官方链接用途，而不是把英文弹窗原样抛给用户

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

---

国内的同学可以到腾讯云 **CNB 仓库**反馈问题，访问更快：

腾讯云 CNB 仓库地址：[点击此处](https://cnb.cool/chenpiyanghappy/SiemensInstallHelper)
