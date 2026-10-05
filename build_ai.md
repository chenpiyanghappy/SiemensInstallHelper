# build_ai.md —— AI 辅助一键打包指引

> 将本文件**全部内容**复制发送给 AI，AI 按以下步骤完成环境校验、执行打包脚本并生成 EXE。
> 本文件服务于 AI 辅助打包流程，面向开发协作，不面向普通用户。

---

## 目标

基于仓库源码，将 **SiemensInstallHelper** 打包为**免环境依赖的 Windows 单文件 EXE**（拷贝即用，目标电脑无需安装 Python / 任何运行库）。

## 1. 环境校验

在项目根目录依次确认：

```bat
python --version        :: 需 Python 3.8+（64 位）
pip --version           :: pip 可用
```

若未安装 PyInstaller：

```bat
pip install pyinstaller
```

确认项目结构完整（打包入口与依赖必须在同一目录）：

```
SiemensInstallHelper/
├── run_install.py              # 打包入口（无参=GUI，带参=命令行）
├── gui_siemens_install.py      # 图形界面
├── siemens_install.py          # 核心逻辑
├── 启动-西门子安装助手.bat      # 双击启动入口
└── 运行库/                     # 自动下载的 VC++ 运行库（微软官方源）
```

## 2. 执行打包

在项目根目录执行：

```bat
pyinstaller --onefile --windowed --name SiemensInstallHelper run_install.py
```

参数说明：

| 参数 | 作用 |
|---|---|
| `--onefile` | 打包为单个 EXE |
| `--windowed` | 无控制台黑窗（GUI 程序） |
| `--name SiemensInstallHelper` | 产物文件名 |
| `run_install.py` | 打包入口脚本 |

## 3. 产物校验（验收标准）

打包完成后逐项检查：

1. **产物存在**：`dist\SiemensInstallHelper.exe` 已生成；
2. **体积正常**：约 **11 MB** 量级（明显过大则检查是否误打包无关依赖，过小则检查是否有动态导入缺失）；
3. **可启动**：双击能弹出主窗口，无报错、无黑窗闪现；
4. **功能冒烟**：至少验证"清理进程 / 检查运行库 / 日志分析"三个命令入口可运行：
   ```bat
   SiemensInstallHelper.exe clean
   SiemensInstallHelper.exe runtime
   SiemensInstallHelper.exe log
   ```
5. 校验通过后：将 `dist\SiemensInstallHelper.exe` **拷回项目根目录**，覆盖旧版，用于分发。

## 4. 注意事项

- 目标电脑**不需要 Python、不需要额外运行库**（VC++ 运行库由工具运行期自动检测 / 从微软官方源下载）；
- 绿色单文件可能被安全软件误报，README 已内置"防误报提醒"（提示加白名单），打包无需额外处理；
- 如需版本号 / 图标 / 隐藏窗口等定制，可追加 `--version-file`、`--icon` 等参数，需与版本规则（V 大版本.功能版本.修复版本）保持一致；
- 打包属本地可逆操作，执行前建议确认当前源码为最新版本（未提交的改动不影响打包产物）。

---

## 免责声明

本项目参照开源项目 OBS‑Studio 的通行处理规则：从 GitHub 获取的官方预编译版本享有完整技术支持；由用户本地自行编译、通过 AI 打包生成的版本，因本地系统环境、依赖版本、编译参数、用户改动源码等不可控因素较多，我们不提供完整的故障排查支持。若用户能够确认该问题在官方预编译版本上可以稳定复现，则属于源码本身的缺陷，我们仍然会进行修复。第三方重新打包分发（含用户自行编译）的程序，请向对应的打包维护者反馈问题。
