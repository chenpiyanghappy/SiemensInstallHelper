# CHANGELOG

> 本文件记录 SiemensInstallHelper 的**完整技术改动与彩蛋备注**；对外简要版本说明见各 Release 概要。
> 版本命名：`V(大版本).(功能版本).(修复版本)`，规则详见 README。

---

## [未发布 · 小贴士体系] - 2026-10-06

### Added 新增
- **知识小贴士体系**（`tips.py` 全新模块，与主程序解耦）：
  - 双文件架构：`tips.json`（官方内置贴士，只读，随版本发布）+ `user_tips.json`（用户自定义，图形界面增删改查，不碰源码）。
  - 内置 10 条贴士：安装路径 / 安装顺序 / U 盘解压 / 杀软白名单 / 磁盘空间 / .NET 3.5 / VC++ 冲突 / 日志位置 / 待重启 / 授权服务 ALM。
  - 分类体系：安装 / 环境 / 排障 / 工程 / 学习；支持标题 / 内容 / 标签 / 分类关键词搜索。
  - 用户贴士 id 从 1001 起，与内置贴士（1~N）隔离；内置贴士受保护，不可增删改。
  - **高阶能力：一键导出 PR 贡献素材**（`export_contribution`）→ `tips_contribution.json`（JSON 片段）+ `CONTRIBUTING_TIPS.md`（提交说明），供自学 Git 后向 GitHub / CNB 提 PR / MR。
- **GUI 集成**：主窗口新增第五行按钮「⑯ 知识小贴士」，打开管理窗口（列表 + 详情 + 搜索 + 新增 / 编辑 / 删除 / 恢复默认 / 导出贡献素材）；窗口 780×700。
- **CLI 新增**：`tips list / search / add / delete / restore / export`（含参数解析：--title / --content / --category / --tags）。

### Changed 变更
- GUI 窗口高度 660 → 700（容纳第五行按钮）。
- README 更新：功能表 ⑯、快速开始 tips 命令、项目结构（tips.py / tips.json / user_tips.json）、新增「🗂 小贴士怎么用」段。

### 彩蛋备注
- 本版本无新增彩蛋。

---

## [v1.1.0] - 2026-10-04（发布）

### Added 新增
- **卡住预警**（`InstallWatcher` / `stall_tips_text`）：安装日志长时间无更新时自动弹窗，附排查指引（杀软拦截 / 隐藏窗口 / 真卡死），可选「继续等待」或「停止监控」。
- **错误大白话翻译**（`plain_explain`）：将「安装程序错误 / 缺 xxx.dll / 0x7E」等英文报错翻译为**大白话 + 操作步骤**，小白也能看懂怎么修。
- **弹窗指引手动修复**（`build_help_page` / `get_help_script`）：无法自动下载/修复时，弹窗给出**官方下载链接 + 逐步操作**，用户自行处理后继续；监控时提示「复制给同学」互助。
- **【提前合入】基础信息一键复制**：自动采集 TIA Portal 版本 / Windows 版本 / 工具版本（复用 `collect_error_context`），一键复制 Issue 基础信息片段，配合提交报错更省事。
- **【提前合入】环境快照脱敏导出**：离线报错报告（`export_report`）新增**脱敏环境快照**（用户名 / 主机名打码），供提交 Issue 与离线分析。
- **【提前合入】精简版安装前体检**：整合已有检查（运行库 / 授权服务 / 杀软 / 待重启），新增**磁盘剩余空间、安装路径字符**检查，输出风险清单。
- **【提前合入】知识库案例扩充**：内测收集到的真实报错案例并入大白话规则表。
- **【提前合入】反馈收集入口**：求助引导页 / 离线报告增加「这条方案是否有用」反馈模板一键复制（微信 / 邮箱渠道）。
- **【寻找安装程序调优】**：过滤 InstData / Components / SetupPackage 组件安装器与已装产品启动器（StartCenter 等），只保留 `Start.exe / Setup.exe` 总入口（有总入口时不显示组件，一个都没有才保底展示并标注仅供参考）；找不到时给出「解压 / 挂载 ISO / 已装程序不算」引导提示。
- **【预填充 Issue 模板】**：仓库新增 `.github/ISSUE_TEMPLATE/`（报错求助 bug_report.yml + 知识库贡献 knowledge_contribute.yml + config.yml）与 `.gitlab/issue_templates/`（CNB 兼容），打开 New Issue 即完整表单；GUI 新增「⑮ 复制Issue模板」一键复制完整 Markdown 模板（问题描述 / 复现步骤 / 报错信息 / 环境信息 / 日志 / 已尝试）。
- **【英文报错大白话表】**：新增 `PLAIN_TIPS` 翻译表，日志分析时对英文报错顺带输出「【大白话】xxx」，降低英文报错门槛。

### Changed 变更
- 错误上下文采集（`collect_error_context`）字段扩充，贡献话术（`build_contrib_block`）随基础信息同步升级。
- 求助引导页（`build_help_page`）生成逻辑完善，兼容离线/在线两种排查路径。
- 文档体系：新增 `CHANGELOG.md`、`docs/FEATURE_PLAN.md`；README 更新至 v1.1，内测转正式。
- GUI 新增第四行按钮：⑫ 复制基础信息 / ⑬ 安装前体检 / ⑭ 复制反馈模板 / ⑮ 复制Issue模板；窗口 780×660。
- CLI 新增命令：`basic-info` / `snapshot` / `preflight` / `feedback` / `issue-template`（均会写入剪贴板）。
- 离线报告（`export_report`）附加脱敏环境快照段与反馈渠道行。

### Fixed 修复
- 内测期修复项以 git 提交记录为准（v1.1 内测 → 正式版之间）。

### 彩蛋备注
- 本版本无新增彩蛋；彩蛋机制按维护者策略从后续版本引入，详情见对应版本彩蛋备注。

---

## [v1.0.0] - 2026-09-11（首发）

### Added 新增
- **防误报提醒**（`check_security_software`）：启动时检测常见杀软（火绒 / 联想管家 / 360 / 腾讯管家 / 金山 / 百度 / Defender），提示加白名单，避免绿色单文件被误报。
- **自动寻找安装程序**（`find_installers` / `launch_installer`）：扫描所有磁盘（含 U 盘 / 移动硬盘 / 光盘），智能排序找出安装总入口（`Start.exe` 等），选中后自动提权启动。
- **智能分析日志**（`analyze_log` / `analyze_and_fix` / `auto_fix`）：自动定位安装日志（`SIA_*.log`），**能自动修的自动修**：授权服务异常 → 自动启动；占用安装的进程 → 自动清理；要求重启 → 自动处理待重启残留标记（先备份可回滚）。
- **清理无用进程**（`clean_processes`）：白名单制，只清浏览器 / 聊天 / 网盘等第三方进程，**系统与杀毒进程绝不碰**。
- **授权检查**（`check_license` / `fix_license_auto`）：检查 Automation License Manager（almservice）是否正常，异常时自动启动。
- **运行库检查**（`check_runtime` / `check_runtime_silent`）：检测 .NET Framework 4.8 / 3.5、VC++ 运行库是否齐全。
- **运行库下载安装**（`download_runtime` / `install_runtime`）：从**微软官方源**自动下载并静默安装 VC++ 2015-2022（x64 / x86）。
- **实时监控**（`InstallWatcher` 初版）：安装期间盯日志，出现报错立即提示并给出建议。
- **离线报错报告**（`export_report`）：一键生成系统信息 + 日志 + 建议的报告 txt，离网时发给 AI / 开发者人工分析。
- **联网查错引导页**（`build_contrib_block` / `open_help_page`）：自动抓取错误 → 生成可复制话术模板 → 一键搜索 → GitHub / CNB 提交入口。
- **高分屏适配**：DPI 感知，4K 高分屏下字体不发虚。

### 彩蛋备注
- 无。

---

## 维护说明

- 每个功能版本发布时：先更新本文件（完整技术改动 + 彩蛋备注），再写对外 Release 概要（简明适度）。
- 对外概要拒绝「修复了一些已知问题」式一句话；本文件保持完整可追溯。
