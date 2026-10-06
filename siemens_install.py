#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西门子专业软件 安装助手  SiemensInstallHelper  v2.2
==================================================
功能：
  0.5 自动寻找安装程序（含外置磁盘/U盘/光盘），提权启动
  1.  安装前清理无用进程（白名单制，系统与杀毒绝不碰）
  2.  自动分析安装日志（自动找日志，知识库给建议）
  2.5 智能分析：能自动修的自动修（授权服务/残留进程/待重启标记），修不了的弹求助引导页
  3.  检查 Automation License Manager（授权服务）
  4.  运行库检查（.NET / VC++）
  5.  实时监控安装日志（InstallWatcher）
  6.  运行库自动下载 / 安装（微软官方源）
  7.  导出报错报告（离线求助用）
  8.  联网查错：求助引导页（话术模板/搜索/GitHub/腾讯云CNB 提交入口）
  防误报：启动时检测常见杀软并提醒（绿色单文件可能被误报）
零依赖：仅用 Python 标准库 + Windows 自带命令（tasklist/taskkill/sc/reg）
"""
import os
import sys
import re
import ctypes
import subprocess
import tempfile
import datetime

# 工具所在目录（源码/exe 均兼容）
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_FILE = os.path.join(BASE_DIR, "siemens_install.log")

# ---------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------

# 可安全结束的第三方软件进程
CLEANABLE_PATTERNS = [
    "chrome", "msedge", "firefox", "iexplore",
    "wechat", "weixin", "wxwork", "qq", "dingtalk", "wemeet", "feishu", "lark",
    "quark", "thunder", "xunlei", "idman", "netdisk", "baidunetdisk", "onedrive",
    "potplayer", "vlc", "qqmusic", "cloudmusic", "kugou", "kmplayer", "yodao",
    "wps", "et", "wpp", "wpscloudsvr", "officeclicktorun",
]

# 绝不结束的系统/安全进程
PROTECTED_PROCESSES = [
    "csrss", "winlogon", "lsass", "services", "smss", "dwm", "explorer",
    "wininit", "svchost", "fontdrvhost", "ctfmon", "audiodg", "spoolsv",
    "RuntimeBroker", "sihost", "SearchApp", "ShellExperienceHost",
    "StartMenuExperienceHost", "MsMpEng", "MsMpSvc", "NisSrv",
    "SecurityHealthService", "HipsDaemon", "HipsMain", "HipsTray",
    "usysdiag", "Lenovo", "HdSvc", "ISecuritySvc",
]

# 安装日志搜索位置（glob 模式）
LOG_PATTERNS = [
    os.path.join(tempfile.gettempdir(), "SIA_*.log"),
    os.path.join(tempfile.gettempdir(), "Siemens*.log"),
    os.path.join(tempfile.gettempdir(), "Setup*.log"),
    os.path.join("C:\\Windows\\Temp", "SIA_*.log"),
    os.path.join("C:\\Windows\\Temp", "Siemens*.log"),
]

# 日志知识库：正则 -> 建议
KNOWLEDGE = [
    (r"not enough (disk )?space|空间不足|0x80070070",
     "磁盘空间不足。请清理 C 盘并释放至少 20GB 后重试。"),
    (r"access is denied|access denied|拒绝访问|0x80070005",
     "权限不足。请右键安装程序，选择“以管理员身份运行”。"),
    (r"another instance|another setup|另一个实例|正在运行",
     "已有安装程序或 TIA Portal 在运行。请先关闭它们（可用本工具“清理无用进程”），再重试。"),
    (r"reboot|restart your computer|重新启动|重启",
     "系统要求重启。请先重启电脑，再继续安装。"),
    (r"0x80070070",
     "磁盘空间不足（错误 0x80070070）。请清理磁盘后重试。"),
    (r"0x80070643|1603|InstallFailure|Installation failed",
     "安装失败（1603 / InstallFailure）。常见原因：权限不足、安装缓存异常、被安全软件拦截。建议：以管理员运行、清空 %TEMP%、重启后重试；仍失败则把日志发给 AI 助手分析。"),
    (r"SetupUnit|SetupPackage.*Failed|AdsWorkerSetupPackage",
     "某个安装组件包失败（如 HelpViewer_Server）。建议：单独重试该组件，或换安装顺序（先基础包后选件）；日志已记录该组件名。"),
    (r"0x800F0900|\.NET Framework 3\.5|启用 Windows 功能",
     "缺少 .NET Framework 3.5 功能。控制面板 → 程序 → 启用或关闭 Windows 功能 → 勾选 .NET Framework 3.5（含 2.0 和 3.0）→ 确定。"),
    (r"license|许可证|授权|license manager",
     "授权/许可证问题。安装完成后打开 Automation License Manager 确认授权；如服务异常，运行本工具“检查授权服务”。"),
    (r"sql server|database",
     "SQL Server / 数据库组件问题。确认没有残留的 SQL 安装冲突，必要时清理后重装。"),
    (r"dcom|0x80040154|class not registered",
     "COM 组件注册问题。多为系统组件缺失，可尝试重启后再装；持续出现需检查系统完整性。"),
    (r"wincc|scada",
     "WinCC/SCADA 组件问题。WinCC 组件与系统版本有关，建议按安装说明顺序安装，且避免与旧版混装。"),
    (r"virus|antivirus|杀毒|安全软件",
     "安全软件可能拦截安装。如确实需要，请暂时在杀毒软件中允许安装程序（不建议完全关闭防护）。"),
    (r"tia portal|step 7",
     "TIA Portal / STEP 7 组件相关错误。请确认安装顺序（先基础包后选件），并以管理员运行。"),
    (r"1722|RPC 服务器不可用|0x800706BA",
     "Windows Installer 服务异常（1722/RPC）。打开 services.msc 确认 Windows Installer 与 Remote Procedure Call 服务已启动；或命令行执行 msiexec /unregister 后 msiexec /regserver 修复。"),
    (r"0x80070570|文件或目录损坏|corrupt",
     "安装文件损坏（0x80070570）。安装包可能下载/解压不完整：建议把压缩包先拷到本地磁盘再解压（U盘解压易出错），解压后校验大小；仍失败则重新下载。"),
    (r"error 1925|error 1935|1925|1935",
     "系统组件安装失败（1925/1935）。多为系统文件或运行库损坏：先重装 VC++ 运行库与 .NET（可用本工具⑥⑦），再以管理员重装；仍失败建议运行 DISM /RestoreHealth 修复系统。"),
    (r"error 1920|failed to start service|无法启动服务",
     "某个系统服务启动失败（1920）。常见原因是权限不足或依赖服务被禁用：以管理员身份重试，检查服务依赖项是否正常。"),
    (r"registry.*(denied|error)|无法写入注册表|0x80070005.*registry",
     "注册表写入被拒绝。多为权限不足或被安全软件注册表防护拦截：以管理员运行、临时关闭注册表保护（装完记得恢复）。"),
    (r"0x80070422|windows update.*(service|fail)|无法启动 Windows Update",
     "Windows Update 服务未运行（0x80070422）。services.msc 中将 Windows Update 设为自动并启动；装 TIA 前建议先完成系统更新。"),
    (r"1602|1612|install source|找不到安装源",
     "找不到安装源（1602/1612）。安装介质被移动或未挂载：确认安装包完整在位，或重新装载 ISO/解压目录后重试。"),
    (r"0x80070020|being used by another process|正在被占用",
     "文件被其他进程占用（0x80070020）。先关闭所有安装程序与 TIA（可用本工具①清理进程），仍失败则重启电脑后再装。"),
    (r"plcsim|仿真",
     "PLCSIM 仿真组件问题。PLCSIM / PLCSIM Advanced 需单独安装，且版本必须与 TIA 匹配；建议先装主程序（Start.exe 总入口）再装仿真组件。"),
]

# 常见英文报错 → 中文大白话翻译表（配合知识库使用，降低英文报错门槛）
PLAIN_TIPS = [
    (r"is not recognized|不是有效",
     "程序无法识别该文件/命令，多半是路径不对或文件缺失。"),
    (r"could not (create|find|open|load)|无法创建|找不到文件",
     "程序无法创建/找到/打开某个文件，多半是权限不足或路径不存在。"),
    (r"insufficient|not enough",
     "资源不足（磁盘/内存/权限），清理后重试。"),
    (r"timed out|timeout",
     "操作超时，组件加载或网络较慢，可稍后重试。"),
    (r"dependency.*(missing|not found)|缺少.*依赖",
     "缺少组件依赖，先装运行库（VC++ / .NET）再重试。"),
    (r"failed to (start|initial|connect)|初始化失败|连接失败",
     "启动/初始化/连接失败，检查相关服务状态后重试。"),
    (r"corrupt|损坏|invalid",
     "文件损坏或无效，重新解压/下载安装包。"),
    (r"not registered|未注册",
     "组件未注册，重启后重试，或修复系统组件。"),
    (r"denied|permission",
     "权限被拒绝，请以管理员身份运行。"),
]

# 错误行识别：匹配错误关键词，但排除 "no error / 0 errors / without error" 等正常文本
_ERROR_RE = re.compile(r"ERROR|FAILED|Error|失败|错误", re.IGNORECASE)
_NO_ERROR_RE = re.compile(r"no error|0 error|without error|errors?\s*[:=]\s*0|noerrors", re.IGNORECASE)


def is_error_line(line):
    """判断一行日志是否为错误行（排除 no error/0 errors 等正常文本）。"""
    if not _ERROR_RE.search(line):
        return False
    if _NO_ERROR_RE.search(line):
        return False
    return True


# 常见杀毒/安全软件进程（用于防误报提醒）
SECURITY_PROCS = [
    ("360安全卫士", ("360tray", "360safe", "360rp", "qhsafetray", "qhactivedefense")),
    ("腾讯电脑管家", ("qqpctray", "qqpcrtp", "qmagenta", "qqpcprotect")),
    ("金山毒霸", ("kismain", "kxetray", "kavstart", "ksafetray")),
    ("百度安全卫士", ("baidusd", "baidusdtray", "baiduprotect")),
    ("Windows Defender", ("msmpeng", "msmpsvc", "nissrv")),
]
# 联想电脑管家与火绒：联想管家内置火绒引擎（hips* 进程），需联动判断归属
LENOVO_PROC_PATTERNS = ("lenovo", "hdservice", "hdssvc", "isecuritysvc",
                        "lenovoapphelper", "lenovoconsole", "lenovosmart")
HUORONG_PROC_PATTERNS = ("hipsmain", "hipstray", "hipsdaemon", "usysdiag")

def check_security_software():
    """检测正在运行的常见杀毒/安全软件。返回检测到的名字列表（只读）。

    联想电脑管家内置火绒引擎：检测到 hips* 进程时，
    若联想管家进程也在运行则归为「联想电脑管家」，否则归为「火绒安全」。
    """
    found = []
    try:
        procs = set(n for _, n in get_processes())
    except Exception:
        return found

    lenovo_on = any(pat in p for p in procs for pat in LENOVO_PROC_PATTERNS)
    huorong_on = any(pat in p for p in procs for pat in HUORONG_PROC_PATTERNS)
    if lenovo_on:
        found.append("联想电脑管家（内置火绒引擎）" if huorong_on else "联想电脑管家")
    elif huorong_on:
        found.append("火绒安全")

    for name, pats in SECURITY_PROCS:
        if any(pat in p for p in procs for pat in pats):
            found.append(name)
    return found


def log(msg):
    """记录到日志文件（追加），同时打印。"""
    line = msg
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin(args):
    """以管理员权限重新启动自己（触发 UAC）。兼容源码与 exe 打包。"""
    if getattr(sys, "frozen", False):
        exe = sys.executable
        workdir = BASE_DIR
        cmdline = '"%s" %s' % (exe, args)
    else:
        script = os.path.abspath(__file__)
        exe = sys.executable
        workdir = os.path.dirname(script)
        cmdline = '"%s" "%s" %s' % (sys.executable, script, args)
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, cmdline, workdir, 1)
        log("已请求管理员权限（请在弹出的 UAC 窗口点击“是”）...")
        return True
    except Exception as e:
        log("提权失败: %s" % e)
        return False


# ---------------------------------------------------------------------
# 0.5 自动寻找安装程序（含外置磁盘 / U盘 / 移动硬盘 / 光盘）
# ---------------------------------------------------------------------

# 目录关键词（命中则高度怀疑是西门子安装包目录）
INSTALL_DIR_KEYS = ("tia", "portal", "step7", "simatic", "wincc", "s7", "博途",
                    "安装包", "install", "siemens")
# 安装启动器文件名（西门子 TIA 典型是 Start.exe）
INSTALL_LAUNCHERS = {"start.exe", "setup.exe", "install.exe", "autorun.exe",
                     "setup64.exe", "start64.exe", "install64.exe", "setup_x64.exe"}
# 扫描时跳过的系统/无关目录（加速 + 安全）
INSTALL_SKIP_DIRS = {"windows", "program files", "program files (x86)", "programdata",
                     "$recycle.bin", "system volume information", ".git", "node_modules",
                     "appdata", "recovery", "windows.old", "syswow64",
                     "python3", "python", "anaconda", "perfgen", "temp", "tmp"}

# 组件/内部安装器特征目录：命中基本判定不是总入口，大幅降权
# （不包含 disk_/dvd：官方镜像的 Disk1\Setup.exe 是总入口，不能误伤）
COMPONENT_DIR_KEYS = ("instdata", "components", "setuppackage",
                      "support", "driver", "redist", "runtime",
                      "licence", "crack", "patch", "common files", "prereq")
# 组件类文件名特征：SetupPackage.exe 这类组件安装器，不是总入口
COMPONENT_FILE_KEYS = ("setuppackage", "component", "_inst", "prerequisite", "redist")
# 明确不是安装包入口的程序 exe（已安装产品的启动器/卸载器等，直接跳过）
NON_LAUNCHER_EXES = {
    "startcenter.exe", "installrootcertificate.exe", "installationmanager.exe",
    "installreport.exe", "installshield.exe", "setupfactory.exe",
}


def list_drives():
    """列出所有磁盘根目录，含外置磁盘/光盘。返回 [(盘符, 类型), ...]。"""
    import ctypes
    drives = []
    bit = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bit & (1 << i):
            letter = "%s:\\" % chr(65 + i)
            t = ctypes.windll.kernel32.GetDriveTypeW(letter)
            label = {2: "可移动磁盘(USB/外置)", 3: "本地磁盘", 5: "光盘"}.get(t, "其他")
            if t in (2, 3, 5):
                drives.append((letter, label))
    return drives


def _walk_pruned(root, skip_parts, max_depth=4, boost_dirs=()):
    """剪枝式目录遍历：跳过系统/无关目录、限制深度；
    命中关键词目录（boost_dirs）允许多深入 3 层。"""
    root = root.rstrip("\\/") + "\\"  # 保证 E:\ 形式，避免盘符后丢反斜杠

    def rec(dirpath, depth, boosted):
        if depth > max_depth + (3 if boosted else 0):
            return
        try:
            entries = list(os.scandir(dirpath))
        except OSError:
            return
        dirs, files = [], []
        for e in entries:
            try:
                if e.is_dir(follow_symlinks=False):
                    name = e.name.lower()
                    if name not in skip_parts and not name.startswith("$"):
                        dirs.append(e)
                elif e.is_file(follow_symlinks=False):
                    files.append(e.name)
            except OSError:
                pass
        yield dirpath, files
        for d in dirs:
            dname = d.name.lower()
            next_boost = boosted or any(k in dname for k in boost_dirs)
            yield from rec(d.path, depth + 1, next_boost)

    yield from rec(root, 0, False)


def find_installers(max_results=15):
    """自动寻找西门子安装程序（扫描所有磁盘，含 U盘/移动硬盘/光盘）。

    返回 [(评分, exe绝对路径), ...]，按匹配度降序。
    只做只读扫描，不自动启动任何程序。
    """
    log("")
    log("=" * 50)
    log("自动寻找安装程序（扫描所有磁盘，含外置磁盘）")
    log("=" * 50)
    drives = list_drives()
    log("发现磁盘: %s" % "、".join("%s(%s)" % (d, t) for d, t in drives))

    found = {}
    for root, label in drives:
        log("  正在扫描 %s %s ..." % (root, label))
        try:
            for dirpath, filenames in _walk_pruned(root, INSTALL_SKIP_DIRS,
                                                   boost_dirs=INSTALL_DIR_KEYS):
                dlower = dirpath.lower()
                dirscore = sum(2 for k in INSTALL_DIR_KEYS if k in dlower)
                for fn in filenames:
                    fl = fn.lower()
                    # 明确不是安装包入口的程序 exe：直接跳过（已装产品启动器/卸载器）
                    if fl in NON_LAUNCHER_EXES or fl.startswith(("uninstall", "unins")):
                        continue
                    if fl in INSTALL_LAUNCHERS:
                        score = 3          # 精确启动器名（start.exe / setup.exe ...）
                    elif fl.startswith(("setup", "start", "install")) and fl.endswith(".exe"):
                        score = 1          # 泛化 setup 类（如 SetupPackage.exe），弱于精确名
                    else:
                        continue
                    if fl in ("start.exe", "setup.exe", "install.exe", "autorun.exe"):
                        score += 2
                    score += min(dirscore, 8)
                    # 组件安装器特征：文件名或目录命中（InstData/Components/SetupPackage 等）
                    is_component = (any(k in fl for k in COMPONENT_FILE_KEYS)
                                    or any(k in dlower for k in COMPONENT_DIR_KEYS))
                    if any(k in fl for k in COMPONENT_FILE_KEYS):
                        score -= 6
                    if any(k in dlower for k in COMPONENT_DIR_KEYS):
                        score -= 6
                    # 已安装程序目录（TIA 装完后的 Automation/Bin 结构）进一步降权
                    if "automation" in dlower and any(k in dlower for k in
                                                      ("portal", "step7", "wincc", "simatic")):
                        score -= 5
                    if "\\bin\\" in dlower:
                        score -= 3
                    # 浅层优先：越靠近磁盘根目录，越可能是安装包总入口
                    depth = dirpath[len(root):].count(os.sep)
                    score -= min(depth, 5)
                    key = (dirpath, fn)
                    if key not in found or score > found[key][0]:
                        found[key] = (score, is_component)
        except Exception as e:
            log("  扫描 %s 出错: %s" % (root, e))

    ranked = sorted(((s, os.path.join(d, f), c) for (d, f), (s, c) in found.items()),
                    key=lambda x: -x[0])
    # 有真正的总入口（Start/Setup 类）时只展示总入口；
    # 一个总入口都没有，才保底展示组件安装器（InstData 里的 Setup）供参考
    main = [(s, p) for s, p, c in ranked if not c]
    comp = [(s, p) for s, p, c in ranked if c]
    has_main = bool(main)
    top = (main or comp)[:max_results]
    if not top:
        log("未找到安装包入口（Setup.exe / Start.exe 这类总入口）。")
        log("请确认：")
        log("  1. 安装包已解压完整（或 ISO 镜像已挂载成盘符）")
        log("  2. 安装包位于任意磁盘中（含 U 盘/移动硬盘/光盘）")
        log("  3. 已安装到电脑里的 TIA 程序（如 StartCenter）不算安装包入口，不会被列出")
    elif has_main:
        log("找到 %d 个疑似安装程序（按匹配度排序）：" % len(top))
        for i, (s, p) in enumerate(top, 1):
            log("  [%d] %s" % (i, p))
    else:
        log("未找到安装包总入口，以下为组件安装器（仅供参考，不一定需要运行）：")
        for i, (s, p) in enumerate(top, 1):
            log("  [%d] %s" % (i, p))
    return top


def launch_installer(path):
    """提权启动找到的安装程序（会弹 UAC，请点“是”）。"""
    if not path or not os.path.exists(path):
        log("文件不存在: %s" % path)
        return False
    log("")
    log("正在启动安装程序（需要管理员权限，UAC 弹窗请点“是”）:")
    log("  " + path)
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", path, None,
                                            os.path.dirname(path), 1)
        log("已发起启动。安装期间可点『⑤ 实时监控』盯着日志。")
        return True
    except Exception as e:
        log("启动失败: %s（可手动右键→以管理员身份运行）" % e)
        return False


# ---------------------------------------------------------------------
# 1. 清理无用进程
# ---------------------------------------------------------------------

def get_processes():
    """返回 [(pid, name_lower), ...] 使用 tasklist。"""
    out = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, errors="ignore",
    ).stdout
    procs = []
    for line in out.splitlines():
        # "image.exe","pid","session",...
        parts = line.split('","')
        if len(parts) >= 2:
            name = parts[0].strip('"').lower()
            if name.endswith(".exe"):
                name = name[:-4]
            pid = parts[1].strip('"')
            if pid.isdigit():
                procs.append((int(pid), name))
    return procs


def clean_processes(confirm_callback=None):
    """清理第三方无用进程。confirm_callback(名单) 返回 True/False。"""
    log("")
    log("=" * 50)
    log("清理无用进程（只清第三方软件，系统与杀毒绝不碰）")
    log("=" * 50)

    all_procs = get_processes()
    targets = []
    seen = set()
    for pid, name in all_procs:
        if name in seen:
            continue
        hit_clean = any(p in name for p in CLEANABLE_PATTERNS)
        hit_protect = any(p in name for p in PROTECTED_PROCESSES)
        if hit_clean and not hit_protect:
            seen.add(name)
            targets.append((pid, name))

    if not targets:
        log("没有发现可清理的第三方进程。")
        return 0

    log("将结束以下进程：")
    for pid, name in targets:
        log("  - %s (PID %d)" % (name, pid))

    if confirm_callback is not None:
        ok = confirm_callback(targets)
    else:
        ok = True
    if not ok:
        log("已取消。")
        return 0

    killed, failed = 0, 0
    for pid, name in targets:
        r = subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            killed += 1
        else:
            failed += 1
            if not is_admin():
                log("  有进程需要管理员权限才能结束（%s），请以管理员运行本工具" % name)
                break
    log("已结束 %d 个进程（%d 个未能结束）。现在可以开始安装了。" % (killed, failed))
    return killed


# ---------------------------------------------------------------------
# 2. 分析安装日志
# ---------------------------------------------------------------------

def find_log():
    """自动寻找安装程序抛出的错误日志。

    1) 先按已知位置匹配（SIA_*.log 等常见位置）；
    2) 找不到时扩展搜索：在常见日志目录里按关键词（sia/siemens/setup/tia/
       step7/wincc/portal/install）找最新的日志文件。
    3) 还是找不到，把可能的日志位置告诉用户。
    """
    import glob
    # 1) 已知位置（最常见）
    for pattern in LOG_PATTERNS:
        files = glob.glob(pattern)
        if files:
            files.sort(key=os.path.getmtime, reverse=True)
            return files[0]

    # 2) 扩展搜索：常见日志目录 + 西门子目录，按文件名关键词匹配
    keywords = ("sia_", "siemens", "setup", "tia", "step7", "wincc",
                "portal", "install", "installer", "msi")
    roots = [
        os.path.join(tempfile.gettempdir(), "*.log"),
        os.path.join("C:\\Windows\\Temp", "*.log"),
        os.path.join("C:\\ProgramData\\Siemens", "**", "*.log"),
        os.path.join("C:\\ProgramData\\Siemens AG", "**", "*.log"),
        os.path.join("C:\\Program Files (x86)\\Common Files\\Siemens", "**", "*.log"),
        os.path.join("C:\\Program Files\\Siemens", "**", "*.log"),
    ]
    candidates = []
    for pat in roots:
        try:
            for f in glob.glob(pat, recursive=True):
                base = os.path.basename(f).lower()
                if any(k in base for k in keywords):
                    try:
                        candidates.append(f)
                    except OSError:
                        pass
        except Exception:
            pass
    if candidates:
        candidates.sort(key=os.path.getmtime, reverse=True)
        return candidates[0]
    return None


def analyze_log(path=None):
    """分析安装日志，按知识库给出建议。"""
    log("")
    log("=" * 50)
    if not path:
        path = find_log()
    if not path or not os.path.exists(path):
        log("未找到安装日志。请把 SIA_*.log 之类的日志放到 %TEMP% 或 C:\\Windows\\Temp。")
        return None
    log("分析安装日志：" + os.path.basename(path))
    log("=" * 50)

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        log("日志读取失败: %s" % e)
        return None

    lines = content.splitlines()
    errors = [l for l in lines if is_error_line(l)]
    log("日志共 %d 行，其中疑似错误 %d 行。" % (len(lines), len(errors)))

    if not errors:
        log("未发现明显错误行，日志看起来正常 ✓")
        return {"errors": 0, "advice": []}

    log("")
    log("--- 最近 8 条错误行 ---")
    for l in errors[-8:]:
        log("  " + (l if len(l) <= 180 else l[:180] + "..."))

    log("")
    log("--- 诊断建议（知识库匹配）---")
    advice = []
    for pattern, text in KNOWLEDGE:
        if re.search(pattern, content, re.IGNORECASE):
            advice.append(text)
            log("  • " + text)
    # 英文报错 → 中文大白话（降门槛）
    for pattern, tip in PLAIN_TIPS:
        if re.search(pattern, content, re.IGNORECASE):
            plain = "【大白话】" + tip
            if plain not in advice:
                advice.append(plain)
                log("  • " + plain)
    if not advice:
        log("  未命中知识库。建议把上面的错误行复制给 AI 助手分析。")
    log("")
    return {"errors": len(errors), "advice": advice}


# ---------------------------------------------------------------------
# 2.5 智能分析：能自动修的自动修，修不了的才弹引导页
# ---------------------------------------------------------------------

# 可自动修复的规则：正则 -> (动作名, 处理说明)
# 动作: clean=清理白名单第三方进程；license=检查并尝试启动授权服务；
#       reboot=处理“需要重启计算机”提示
AUTO_FIX_RULES = [
    (r"another instance|another setup|另一个实例|正在运行",
     ("clean", "发现其他程序占用安装，已自动清理可安全结束的第三方进程")),
    (r"license|许可证|授权|license manager",
     ("license", "授权服务异常，已自动检查并尝试启动 Automation License Manager")),
    (r"reboot|restart your computer|restart|重新启动|需要重启|要求重启|重启",
     ("reboot", "安装程序要求重启，已自动处理待重启标记")),
]
AUTO_FIX_PATTERNS = [r[0] for r in AUTO_FIX_RULES]


def check_pending_reboot():
    """检查系统是否存在“待重启”标记。
    返回 [(类型, 描述), ...]；类型: session=安装残留 / wu=Windows更新 / cbs=组件服务。
    """
    import winreg
    found = []

    # 来源1: Session Manager 的 PendingFileRenameOperations（上次安装/卸载残留，最常见）
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\Session Manager") as k:
            try:
                v, _ = winreg.QueryValueEx(k, "PendingFileRenameOperations")
                if v:
                    found.append(("session", "存在‘文件重命名待处理’残留标记"
                                            "（常见于上次安装/卸载未完成）"))
            except FileNotFoundError:
                pass
    except OSError:
        pass

    # 来源2: Windows 更新要求重启（真实待重启，不建议自动清理）
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update") as k:
            winreg.QueryValueEx(k, "RebootRequired")
            found.append(("wu", "Windows 更新未完成，要求先重启"))
    except OSError:
        pass

    # 来源3: 组件服务（CBS）要求重启（真实待重启，不建议自动清理）
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing") as k:
            winreg.QueryValueEx(k, "RebootPending")
            found.append(("cbs", "系统组件服务要求重启"))
    except OSError:
        pass

    return found


def fix_reboot():
    """处理‘需要重启计算机’：
    - 安装残留类标记（Session Manager）：备份后自动清除，可直接安装；
    - 真实系统更新/组件服务类：不自动清，提示先重启。
    返回 (是否全部处理完, 仍需用户处理的消息列表)。
    """
    log("  检查系统待重启状态 ...")
    found = check_pending_reboot()
    if not found:
        log("  ✓ 未发现待重启标记，可直接安装。")
        return True, []

    done_msgs, remain_msgs = [], []
    for kind, desc in found:
        if kind == "session":
            # 先备份整个键，再删除残留值（可回滚）
            try:
                import datetime
                bak_dir = os.path.join(BASE_DIR, "backup")
                os.makedirs(bak_dir, exist_ok=True)
                bak = os.path.join(bak_dir, "pending_reboot_%s.reg" %
                                   datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
                subprocess.run(
                    ["reg", "export",
                     r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager",
                     bak, "/y"],
                    capture_output=True, text=True, errors="ignore")
                r = subprocess.run(
                    ["reg", "delete",
                     r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager",
                     "/v", "PendingFileRenameOperations", "/f"],
                    capture_output=True, text=True, errors="ignore")
                if r.returncode == 0:
                    done_msgs.append("已清除残留的‘文件重命名待处理’标记"
                                     "（已备份到 %s，可随时恢复）" % bak)
                else:
                    remain_msgs.append("清除待重启标记失败（需要管理员权限）：%s" % desc)
            except Exception as e:
                remain_msgs.append("清除待重启标记出错：%s" % e)
        else:
            remain_msgs.append("%s —— 请先重启电脑后再继续安装" % desc)

    for m in done_msgs:
        log("  ✓ " + m)
    for m in remain_msgs:
        log("  • " + m)
    return (not remain_msgs), remain_msgs


def fix_license_auto():
    """自动修复授权服务（只尝试启动，不动其他配置）。返回是否已正常运行。"""
    r = subprocess.run(["sc", "query", "almservice"],
                       capture_output=True, text=True, errors="ignore")
    state = ""
    for line in r.stdout.splitlines():
        if "STATE" in line:
            state = line.strip()
    if "RUNNING" in state:
        return True
    if not r.stdout.strip():
        return False  # 服务不存在（可能未安装完成）
    log("  尝试启动 almservice ...")
    r2 = subprocess.run(["sc", "start", "almservice"],
                        capture_output=True, text=True, errors="ignore")
    return ("RUNNING" in " ".join(r2.stdout)) or r2.returncode == 0


def auto_fix(content):
    """根据日志内容执行可自动修复的动作。
    返回 (已自动处理说明列表, 未解决建议列表)。"""
    fixed, remaining = [], []
    done = set()
    for pattern, (action, desc) in AUTO_FIX_RULES:
        if not re.search(pattern, content, re.IGNORECASE):
            continue
        if action in done:
            continue
        done.add(action)
        if action == "clean":
            n = clean_processes()  # 白名单静默清理（系统/杀毒不碰）
            if n > 0:
                fixed.append("已自动结束 %d 个占用安装的第三方进程" % n)
            else:
                remaining.append("检测到其他程序正在运行，但未发现可安全清理的进程；"
                                 "请手动关闭正在运行的软件后重试。")
        elif action == "license":
            if fix_license_auto():
                fixed.append("已自动修复授权服务（Automation License Manager 已运行）")
            else:
                remaining.append("授权服务异常且自动修复未成功：请以管理员身份运行本工具后"
                                 "点『③ 检查授权』，或手动打开 Automation License Manager 检查。")
        elif action == "reboot":
            all_done, msgs = fix_reboot()
            if all_done:
                fixed.append("已自动处理‘需要重启计算机’问题"
                             "（若为安装残留标记已清除，可直接继续安装）")
            else:
                remaining.extend(msgs)
    # 知识库中其余建议（未配置自动修复的）保留为未解决
    for pattern, text in KNOWLEDGE:
        if re.search(pattern, content, re.IGNORECASE):
            if pattern not in AUTO_FIX_PATTERNS:
                remaining.append(text)
    # 去重（保持顺序）
    seen, uniq = set(), []
    for x in remaining:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return fixed, uniq


def analyze_and_fix(path=None):
    """智能分析入口：能自动修的自动修，修不了的自动生成并打开求助引导页。"""
    import webbrowser
    log("")
    log("=" * 50)
    log("智能分析（能自动修复的自动处理，修不了的再求助）")
    log("=" * 50)
    if not path:
        path = find_log()
    if not path or not os.path.exists(path):
        log("未找到安装日志。已自动搜索：%TEMP%、C:\\Windows\\Temp、")
        log("  C:\\ProgramData\\Siemens、C:\\Program Files\\Siemens 等常见位置。")
        log("  仍找不到时：请先运行一次安装程序让它生成日志（SIA_*.log 会出现在")
        log("  %TEMP% 或 C:\\Windows\\Temp），再回来点『② 智能分析』；")
        log("  或把日志文件手动放到桌面后告诉助手。")
        return {"status": "no_log"}

    log("分析安装日志：" + os.path.basename(path))
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        log("日志读取失败: %s" % e)
        return {"status": "error", "msg": str(e)}

    lines = content.splitlines()
    errors = [l for l in lines if is_error_line(l)]
    log("日志共 %d 行，其中疑似错误 %d 行。" % (len(lines), len(errors)))

    if not errors:
        log("未发现明显错误行，日志看起来正常 ✓ 无需求助。")
        return {"status": "ok", "errors": 0, "advice": []}

    log("")
    log("--- 最近 8 条错误行 ---")
    for l in errors[-8:]:
        log("  " + (l if len(l) <= 180 else l[:180] + "..."))

    log("")
    log("--- 自动处理 ---")
    fixed, remaining = auto_fix(content)
    for f in fixed:
        log("  ✓ " + f)
    if not fixed and remaining:
        log("  （没有可直接自动修复的项目）")

    if remaining:
        log("")
        log("--- 仍需处理的问题 ---")
        for r in remaining:
            log("  • " + r)
        log("")
        log("以上问题需要人工/AI 协助，正在为您生成求助引导页...")
        page, _script = build_help_page()
        try:
            webbrowser.open("file:///" + page.replace("\\", "/"))
            log("✓ 求助引导页已打开：%s" % page)
        except Exception as e:
            log("打开引导页失败: %s（请手动打开 %s）" % (e, page))
        return {"status": "help", "fixed": fixed, "remaining": remaining,
                "page": page}
    else:
        log("")
        log("✓ 可自动处理的问题已全部处理完毕，无需弹出求助引导页。")
        return {"status": "done", "fixed": fixed, "errors": len(errors)}


# ---------------------------------------------------------------------
# 3. 检查授权服务 (ALM)
# ---------------------------------------------------------------------

def check_license():
    log("")
    log("=" * 50)
    log("检查授权服务 (ALM)")
    log("=" * 50)
    r = subprocess.run(["sc", "query", "almservice"],
                       capture_output=True, text=True, errors="ignore")
    state = ""
    for line in r.stdout.splitlines():
        if "STATE" in line:
            state = line.strip()
    if not r.stdout.strip():
        log("未发现 Automation License Manager 服务。软件可能尚未安装或安装不完整。")
        return
    if "RUNNING" in state:
        log("  ✓ Automation License Manager 服务运行正常")
    else:
        log("  ✗ ALM 服务未运行！尝试启动...")
        if is_admin():
            r2 = subprocess.run(["sc", "start", "almservice"],
                                capture_output=True, text=True)
            if "RUNNING" in " ".join(r2.stdout) or r2.returncode == 0:
                log("  ✓ 已成功启动 ALM 服务")
            else:
                log("  ✗ 启动失败: %s" % r2.stdout.strip())
        else:
            log("  ✗ 需要管理员权限启动服务，正在请求...")
            relaunch_as_admin("license")
            return
    # 检查授权进程
    procs = get_processes()
    found = any(n == "almsrv64x" for _, n in procs)
    log("  ✓ 授权进程 almsrv64x 运行中" if found else "  - 授权进程未运行（服务启动后会拉起）")
    log("")


# ---------------------------------------------------------------------
# 4. 运行库检查（.NET / VC++ 等）
# ---------------------------------------------------------------------

def check_runtime():
    import winreg
    log("")
    log("=" * 50)
    log("运行库检查（.NET / VC++）")
    log("=" * 50)

    results = []

    def reg_read(path, name, hive=winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, path) as k:
                v, _ = winreg.QueryValueEx(k, name)
                return v
        except Exception:
            return None

    # .NET Framework 4.x（4.8.1 Release >= 528372；4.8 >= 528040）
    rel = reg_read(r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full", "Release")
    if rel:
        if int(rel) >= 528372:
            results.append((".NET Framework 4.8.1", "✓ 已安装"))
        elif int(rel) >= 528040:
            results.append((".NET Framework 4.8", "✓ 已安装"))
        else:
            results.append((".NET Framework 4.x", "✗ 版本较低 (Release=%s)" % rel))
    else:
        results.append((".NET Framework 4.8", "✗ 未检测到"))

    # .NET Framework 3.5（功能启用与否）
    ndp35 = reg_read(r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v3.5", "Install")
    results.append((".NET Framework 3.5", "✓ 已启用" if ndp35 else "✗ 未启用（建议开启）"))

    # VC++ 运行库（x64 与 x86 两个视角的卸载表）
    vc_names = []
    for view in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, view) as k:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(k, i)
                        i += 1
                    except OSError:
                        break
                    try:
                        with winreg.OpenKey(k, sub) as sk:
                            dn, _ = winreg.QueryValueEx(sk, "DisplayName")
                            if dn and "Visual C++" in dn and "Redistributable" in dn:
                                vc_names.append(dn.strip())
                    except Exception:
                        pass
        except OSError:
            pass
    vc_names = sorted(set(vc_names))
    if vc_names:
        results.append(("VC++ 运行库", "✓ 已装 %d 个: %s" % (len(vc_names), "；".join(vc_names))))
    else:
        results.append(("VC++ 运行库", "✗ 未检测到（建议安装 2015-2022）"))

    for name, status in results:
        log("  %s: %s" % (name, status))
    log("")
    log("提示：西门子软件常见需要 .NET Framework 4.8、.NET 3.5、VC++ 2015-2022 运行库。")
    log("      缺哪个就去微软官网下载对应版本安装即可（本工具不代下载第三方安装包）。")
    log("")
    return results


# ---------------------------------------------------------------------
# 5. 实时监控安装日志
# ---------------------------------------------------------------------

class InstallWatcher:
    """监控安装日志新增错误行。GUI 用 after 轮询调用 poll()。"""

    def __init__(self):
        self.path = None
        self.last_line = 0
        self.reset()

    def reset(self):
        self.path = find_log()
        self.last_line = 0
        if self.path:
            try:
                with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
                    self.last_line = len(f.read().splitlines())
            except Exception:
                self.last_line = 0

    def poll(self):
        """返回新增错误行列表 + 建议。没有新错误返回空。"""
        if not self.path or not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
        except Exception:
            return []
        if len(lines) <= self.last_line:
            return []
        new_lines = lines[self.last_line:]
        self.last_line = len(lines)
        bad = [l for l in new_lines if is_error_line(l)]
        if not bad:
            return []
        content = "\n".join(new_lines)
        advice = ""
        for pattern, text in KNOWLEDGE:
            if re.search(pattern, content, re.IGNORECASE):
                advice = text
                break
        return bad + (["  → 建议：" + advice] if advice else [])


# ---------------------------------------------------------------------
# 6. 运行库自动下载 / 安装（微软官方源）
# ---------------------------------------------------------------------

RUNTIME_DIR = os.path.join(BASE_DIR, "运行库")

# 常用运行库清单
# 每条: (名称, 类型, 地址, 文件名, 静默安装参数)
#   类型 "download" = 自动下载（微软官方直链）
#   类型 "web"      = 打开官方下载页（微软页面需登录/JS 流程，无法直链，给网页）
RUNTIME_DOWNLOADS = [
    ("VC++ 2015-2022 运行库 (x64)", "download",
     "https://aka.ms/vs/17/release/vc_redist.x64.exe",
     "vc_redist.x64.exe", "/install /quiet /norestart"),
    ("VC++ 2015-2022 运行库 (x86)", "download",
     "https://aka.ms/vs/17/release/vc_redist.x86.exe",
     "vc_redist.x86.exe", "/install /quiet /norestart"),
    (".NET Framework 4.8", "web",
     "https://dotnet.microsoft.com/download/dotnet-framework/net48",
     "", ""),
]


def download_runtime(progress_cb=None):
    """自动下载常用运行库（微软官方源）。download 类直链下载，web 类打开官方页。"""
    import urllib.request
    log("")
    log("=" * 50)
    log("自动下载运行库（微软官方源）")
    log("=" * 50)
    os.makedirs(RUNTIME_DIR, exist_ok=True)

    for name, rtype, url, fname, _args in RUNTIME_DOWNLOADS:
        if rtype == "web":
            log("  %s: 需要浏览器下载，正在打开官方页..." % name)
            import webbrowser
            try:
                webbrowser.open(url)
            except Exception as e:
                log("    打开失败: %s（手动访问 %s）" % (e, url))
            continue

        target = os.path.join(RUNTIME_DIR, fname)
        if os.path.exists(target) and os.path.getsize(target) > 1024 * 1024:
            log("  %s: 已存在（%s），跳过下载。" % (name, fname))
            if progress_cb:
                try:
                    progress_cb(name, -1, -1)
                except Exception:
                    pass
            continue

        log("  正在下载 %s ..." % name)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp, \
                    open(target + ".tmp", "wb") as out:
                total = int(resp.headers.get("Content-Length") or 0)
                done = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    if progress_cb:
                        try:
                            progress_cb(name, done, total)
                        except Exception:
                            pass
            os.replace(target + ".tmp", target)
            log("  ✓ %s 下载完成（%.1f MB）" % (name, os.path.getsize(target) / 1048576))
        except Exception as e:
            log("  ✗ %s 下载失败: %s" % (name, e))
            try:
                os.remove(target + ".tmp")
            except OSError:
                pass
    log("")
    log("下载完成。可点『⑦ 安装运行库』静默安装，或手动双击『运行库』文件夹里的 exe。")
    log("")


def install_runtime(which=None):
    """静默安装已下载的运行库。which 为序号（0 起）或 None=全部。
    需要管理员权限；非管理员时提示提权。"""
    log("")
    log("=" * 50)
    log("安装运行库（静默安装）")
    log("=" * 50)
    if not is_admin():
        log("需要管理员权限安装运行库，正在请求提权（UAC 请点“是”）...")
        relaunch_as_admin("install-runtime")
        return False

    items = [i for i, (n, t, u, f, a) in enumerate(RUNTIME_DOWNLOADS)
             if t == "download"]
    if which is not None:
        items = [which]

    installed = 0
    for idx in items:
        name, rtype, url, fname, args = RUNTIME_DOWNLOADS[idx]
        target = os.path.join(RUNTIME_DIR, fname)
        if not os.path.exists(target):
            log("  ✗ %s 尚未下载，先点『⑥ 下载运行库』" % name)
            continue
        log("  正在静默安装 %s ..." % name)
        r = subprocess.run([target] + (args.split() if args else []),
                           capture_output=True, text=True, timeout=600)
        if r.returncode in (0, 3010):
            log("  ✓ %s 安装完成（退出码 %s）" % (name, r.returncode))
            installed += 1
        else:
            log("  ✗ %s 安装失败（退出码 %s）" % (name, r.returncode))
    log("")
    log("共安装 %d 个运行库。部分组件可能提示重启，建议重启一次再继续装西门子。")
    log("")
    return installed > 0


# ---------------------------------------------------------------------
# 6.5 v1.1 新功能：基础信息 / 环境快照 / 安装前体检 / 反馈 / Issue 模板
# ---------------------------------------------------------------------

TOOL_VERSION = "v1.1.0"
FEEDBACK_WECHAT = "chenpiyanghappy"
FEEDBACK_EMAIL = "chenpiyang20070426@gmail.com"


def copy_to_clipboard(text):
    """把文本复制到 Windows 剪贴板（clip.exe + UTF-16LE，兼容无 GUI 环境）。"""
    import subprocess
    data = (text or "").encode("utf-16-le")
    try:
        p = subprocess.Popen(["clip.exe"], stdin=subprocess.PIPE,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        p.communicate(data)
        return True
    except Exception:
        return False


def _mem_info():
    """内存信息 (总GB, 可用GB)，失败返回 (None, None)。"""
    try:
        import psutil
        vm = psutil.virtual_memory()
        return vm.total / 2**30, vm.available / 2**30
    except Exception:
        try:
            import ctypes
            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = _MS()
            ms.dwLength = ctypes.sizeof(_MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                return ms.ullTotalPhys / 2**30, ms.ullAvailPhys / 2**30
        except Exception:
            pass
    return None, None


def _mask_name(name):
    """主机名/用户名脱敏：保留前 2 位，其余打码。"""
    if not name:
        return "(未知)"
    if len(name) <= 2:
        return name[:1] + "**"
    return name[:2] + "*" * max(len(name) - 2, 1)


def _extract_tia_version(disp):
    """从注册表 DisplayName 提取 TIA 版本号（避开 32/64 架构位与 SP 号）。"""
    m = re.search(r"V(1[0-9]|[2-9][0-9])\.0", disp)
    if m:
        return m.group(1) + ".0"
    m = re.search(r"V(1[0-9]|[2-9][0-9])\b", disp)
    if m:
        return m.group(1)
    m = re.search(r"\b([1-9][0-9])\.0\b", disp)
    if m and int(m.group(1)) not in (32, 64):
        return m.group(1) + ".0"
    return None


def detect_tia_versions():
    """检测本机已安装的 TIA/西门子组件。返回 [(DisplayName, 版本), ...]。"""
    import winreg
    found = []
    keys = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    hit_kw = ("tia", "simatic", "wincc", "step 7", "step7", "portal",
              "plcsim", "startdrive", "博途", "siemens")
    for hive, sub in keys:
        try:
            k = winreg.OpenKey(hive, sub)
        except OSError:
            continue
        try:
            n = winreg.QueryInfoKey(k)[0]
            for i in range(n):
                try:
                    sk = winreg.OpenKey(k, winreg.EnumKey(k, i))
                    name = winreg.QueryValueEx(sk, "DisplayName")[0]
                    if any(w in name.lower() for w in hit_kw):
                        ver = _extract_tia_version(name)
                        found.append((name, ver))
                except OSError:
                    pass
        finally:
            winreg.CloseKey(k)
    return found


def collect_basic_info():
    """采集基础信息：工具版本 / 系统版本 / TIA 组件版本。"""
    import platform
    return {
        "tool": TOOL_VERSION,
        "os": platform.platform(),
        "tia": detect_tia_versions(),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def build_basic_info_block(ctx=None):
    """生成基础信息 Markdown 块（粘贴到 Issue / 反馈时用，概括不啰嗦）。"""
    if ctx is None:
        ctx = collect_basic_info()
    lines = ["### 基础信息（工具自动采集）", ""]
    lines.append("- 工具版本：%s" % ctx["tool"])
    lines.append("- 操作系统：%s" % ctx["os"])
    tia = ctx["tia"]
    if tia:
        # 20 与 20.0 视为同一版本，统一为不带 .0 形式展示
        def _norm(v):
            return v[:-2] if v.endswith(".0") else v
        portal = sorted({_norm(v) for n, v in tia if v and re.search(r"tia|portal", n, re.I)})
        other = sorted({_norm(v) for n, v in tia if v and not re.search(r"tia|portal", n, re.I)})
        parts = []
        if portal:
            parts.append("TIA Portal V" + "、V".join(portal))
        if other:
            parts.append("其他西门子组件 V" + "、V".join(other))
        lines.append("- 西门子组件：" + "；".join(parts))
    else:
        lines.append("- 西门子组件：（未检测到）")
    lines.append("- 采集时间：%s" % ctx["time"])
    return "\n".join(lines)


def copy_basic_info_block():
    """复制基础信息块到剪贴板。返回 (是否成功, 文本)。"""
    text = build_basic_info_block()
    ok = copy_to_clipboard(text)
    log("基础信息已复制到剪贴板 ✓（可直接粘贴到 Issue / 反馈）")
    log("")
    return ok, text


def collect_env_snapshot():
    """采集环境快照（主机名/用户名已脱敏打码）。"""
    import platform
    import socket
    snap = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os": platform.platform(),
        "host": _mask_name(socket.gethostname()),
        "user": _mask_name(os.environ.get("USERNAME", "")),
        "mem": _mem_info(),
        "disks": [],
        "dotnet": [],
        "alm": "未知",
        "pending_reboot": [],
    }
    try:
        import shutil
        for d in list_drives():
            try:
                total, used, free = shutil.disk_usage(d[0])
                snap["disks"].append("%s 总%.0fG 剩%.0fG" %
                                     (d[0], total / 2**30, free / 2**30))
            except Exception:
                pass
    except Exception:
        pass
    try:
        snap["dotnet"] = ["%s %s" % (n, s) for n, s in check_runtime_silent()]
    except Exception:
        pass
    try:
        r = subprocess.run(["sc", "query", "almservice"], capture_output=True,
                           text=True, errors="ignore")
        for line in r.stdout.splitlines():
            if "STATE" in line:
                snap["alm"] = line.strip()
                break
    except Exception:
        pass
    try:
        snap["pending_reboot"] = check_pending_reboot()
    except Exception:
        pass
    return snap


def export_env_snapshot():
    """导出脱敏环境快照 txt。返回文件路径。"""
    log("")
    log("=" * 50)
    log("导出环境快照（脱敏，主机名/用户名已打码）")
    log("=" * 50)
    snap = collect_env_snapshot()
    lines = ["西门子安装助手 · 环境快照（脱敏）", "时间: %s" % snap["time"], ""]
    lines.append("【系统】%s" % snap["os"])
    lines.append("【主机】%s  【用户】%s" % (snap["host"], snap["user"]))
    if snap["mem"][0]:
        lines.append("【内存】总 %.1f GB / 可用 %.1f GB" % (snap["mem"][0], snap["mem"][1]))
    if snap["disks"]:
        lines.append("【磁盘】")
        for d in snap["disks"]:
            lines.append("  " + d)
    if snap["dotnet"]:
        lines.append("【运行库】")
        for r in snap["dotnet"]:
            lines.append("  " + r)
    lines.append("【授权服务】%s" % snap["alm"])
    if snap["pending_reboot"]:
        lines.append("【待重启标记】")
        for _t, desc in snap["pending_reboot"]:
            lines.append("  " + desc)
    else:
        lines.append("【待重启标记】无")
    fname = os.path.join(BASE_DIR, "环境快照_%s.txt" %
                         datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log("快照已导出: %s" % fname)
    log("此文件已脱敏，可直接发给开发者 / AI 助手分析环境问题。")
    log("")
    return fname


def check_env_preflight():
    """安装前体检：返回 [(level, 名称, 状态, 建议)]，level ∈ ok/warn/danger/tip。"""
    import shutil
    items = []

    # 1 管理员权限
    if is_admin():
        items.append(("ok", "管理员权限", "已以管理员运行", "正常"))
    else:
        items.append(("danger", "管理员权限", "非管理员", "建议右键→以管理员身份运行本工具"))

    # 2 磁盘空间
    try:
        total, used, free = shutil.disk_usage("C:\\")
        gb = free / 2**30
        if gb >= 20:
            items.append(("ok", "C盘空间", "剩余 %.1f GB" % gb, "≥20GB，充足"))
        else:
            items.append(("danger", "C盘空间", "剩余 %.1f GB" % gb, "建议清理出 ≥20GB 再安装"))
    except Exception:
        items.append(("warn", "C盘空间", "检测失败", "无法读取磁盘占用"))

    # 3 内存
    total, avail = _mem_info()
    if total and total >= 8:
        items.append(("ok", "内存", "总 %.1f GB / 可用 %.1f GB" % (total, avail), "≥8GB，正常"))
    elif total:
        items.append(("warn", "内存", "总 %.1f GB" % total, "建议 ≥8GB（TIA 较吃内存）"))
    else:
        items.append(("warn", "内存", "检测失败", "建议 ≥8GB"))

    # 4 .NET
    try:
        rt = dict(check_runtime_silent())
        dotnet = " ".join(k for k in rt if "net" in k.lower())
        if "4" in dotnet or any("4.8" in v for v in rt.values()):
            items.append(("ok", ".NET", "已安装", "正常"))
        else:
            items.append(("warn", ".NET", "未检测到 4.x", "建议安装 .NET 4.8（本工具⑥⑦可辅助）"))
    except Exception:
        items.append(("warn", ".NET", "检测失败", ""))

    # 5 VC++ 运行库
    try:
        rt = dict(check_runtime_silent())
        vc = [k for k in rt if "vc" in k.lower() or "visual c" in k.lower()]
        if len(vc) >= 5:
            items.append(("ok", "VC++ 运行库", "已装 %d 个" % len(vc), "正常"))
        elif vc:
            items.append(("warn", "VC++ 运行库", "仅 %d 个" % len(vc), "建议用⑥⑦补齐常用版本"))
        else:
            items.append(("warn", "VC++ 运行库", "未检测到", "建议用⑥⑦安装"))
    except Exception:
        items.append(("warn", "VC++ 运行库", "检测失败", ""))

    # 6 ALM 授权服务
    try:
        r = subprocess.run(["sc", "query", "almservice"], capture_output=True,
                           text=True, errors="ignore")
        running = "RUNNING" in r.stdout.upper()
        items.append(("ok" if running else "danger", "授权服务 ALM",
                      "运行中" if running else "未运行/异常",
                      "正常" if running else "安装后运行③检查授权并尝试启动服务"))
    except Exception:
        items.append(("warn", "授权服务 ALM", "检测失败", ""))

    # 7 待重启标记
    try:
        pr = check_pending_reboot()
        if pr:
            items.append(("danger", "待重启标记", "存在（%s）" % pr[0][0],
                          "建议先重启电脑再安装，否则容易报错"))
        else:
            items.append(("ok", "待重启标记", "无", "正常"))
    except Exception:
        items.append(("warn", "待重启标记", "检测失败", ""))

    # 8 杀毒软件
    try:
        sec = check_security_software()
        if sec:
            items.append(("tip", "安全软件", "运行中: %s" % "、".join(sec),
                          "如安装被拦截，请把安装包/工具加入信任（不建议完全关闭防护）"))
        else:
            items.append(("ok", "安全软件", "未检测到", "正常"))
    except Exception:
        pass

    # 9 安装路径建议
    items.append(("tip", "安装路径", "默认 C:\\Program Files",
                  "建议保持默认路径，避免中文/空格目录导致兼容问题"))

    # 汇总输出
    log("")
    log("=" * 50)
    log("安装前体检（%d 项）" % len(items))
    log("=" * 50)
    for level, name, state, advice in items:
        mark = {"ok": "✓", "warn": "⚠", "danger": "✗", "tip": "i"}.get(level, "·")
        log("%s [%s] %s：%s" % (mark, name, state, advice))
    log("")
    return items


def build_feedback_block():
    """生成反馈模板（粘贴给开发者 / 发微信 / 发邮件用）。"""
    return "\n".join([
        "【方案反馈】西门子安装助手 这条方案对你有用吗？",
        "",
        "  ① 问题是否解决：是 / 否 / 部分解决",
        "  ② 哪个功能帮助最大（如：智能分析 / 授权检查 / 寻找安装程序）:",
        "  ③ 遇到的问题（可选）:",
        "  ④ 希望补充的功能（可选）:",
        "",
        "反馈渠道（任选其一，直接粘贴上面的①②③④回复即可）：",
        "  微信: " + FEEDBACK_WECHAT,
        "  邮箱: " + FEEDBACK_EMAIL,
    ])


def copy_feedback_block():
    """复制反馈模板到剪贴板。返回 (是否成功, 文本)。"""
    text = build_feedback_block()
    ok = copy_to_clipboard(text)
    log("反馈模板已复制到剪贴板 ✓（粘贴给开发者即可）")
    log("")
    return ok, text


def build_issue_template(ctx=None):
    """生成完整的预填充 Issue 模板（Markdown），粘贴到 GitHub/CNB 提交 Issue。"""
    if ctx is None:
        ctx = collect_error_context()
    lines = []
    lines.append("### 问题描述")
    lines.append("（用一两句话描述安装时发生了什么，比如：安装 TIA V20 主程序时弹出报错并回滚）")
    lines.append("")
    lines.append("### 复现步骤")
    lines.append("1. 以管理员身份运行安装包总入口（Start.exe / Setup.exe）")
    lines.append("2. 安装到第几步出现异常？")
    lines.append("3. 异常提示 / 行为：")
    lines.append("")
    lines.append("### 预期行为")
    lines.append("（比如：应继续安装至 100% 完成）")
    lines.append("")
    lines.append("### 实际行为 / 报错信息")
    if ctx["errors"]:
        lines.append("```")
        for e in ctx["errors"][:8]:
            lines.append(e[:200])
        lines.append("```")
    else:
        lines.append("（未捕获到日志错误，请附上日志文件）")
    lines.append("")
    lines.append("### 环境信息")
    lines.append(build_basic_info_block())
    lines.append("")
    lines.append("### 日志文件")
    if ctx["log_path"]:
        lines.append("日志路径：%s" % ctx["log_path"])
    else:
        lines.append("日志路径：（未找到）SIA_*.log 通常位于 %TEMP% 或 C:\\Windows\\Temp")
    lines.append("请把日志文件一并上传附件。")
    lines.append("")
    lines.append("### 已尝试")
    lines.append("- [ ] 以管理员身份运行")
    lines.append("- [ ] 重启后重试")
    lines.append("- [ ] 关闭杀毒软件 / 添加信任")
    lines.append("")
    lines.append("---")
    lines.append("模板由西门子安装助手自动生成；补充【问题描述】【复现步骤】后即可提交。")
    return "\n".join(lines)


def copy_issue_template():
    """复制完整 Issue 模板到剪贴板。返回 (是否成功, 文本)。"""
    text = build_issue_template()
    ok = copy_to_clipboard(text)
    log("Issue 模板已复制到剪贴板 ✓")
    log("打开 GitHub/CNB 仓库 → Issues → New Issue，直接粘贴即可。")
    log("")
    return ok, text


# ---------------------------------------------------------------------
# 7. 导出报错报告（离线求助用）
# ---------------------------------------------------------------------

def export_report():
    """导出报错报告 txt：系统信息 + 授权 + 运行库 + 日志错误 + 知识库建议。"""
    import platform
    log("")
    log("=" * 50)
    log("导出报错报告（离线发给 AI/开发者分析用）")
    log("=" * 50)
    ctx = collect_error_context()

    lines = []
    lines.append("=" * 56)
    lines.append("西门子安装报错报告  %s" % ctx["time"])
    lines.append("=" * 56)
    lines.append("")
    lines.append("【系统信息】")
    lines.append("  OS: %s" % ctx["os"])
    # v1.1：附加脱敏环境快照（主机名/用户名打码，可放心外发）
    try:
        snap = collect_env_snapshot()
        lines.append("")
        lines.append("【环境快照（已打码）】")
        lines.append("  主机: %s  用户: %s" % (snap["host"], snap["user"]))
        if snap["mem"][0]:
            lines.append("  内存: 总 %.1f GB / 可用 %.1f GB" % (snap["mem"][0], snap["mem"][1]))
        for d in snap["disks"]:
            lines.append("  磁盘: " + d)
        lines.append("  授权服务: %s" % snap["alm"])
        if snap["pending_reboot"]:
            for _t, desc in snap["pending_reboot"]:
                lines.append("  待重启标记: " + desc)
    except Exception:
        pass
    try:
        import psutil  # 非必需，失败则跳过
        vm = psutil.virtual_memory()
        lines.append("  内存: 总 %.1f GB / 可用 %.1f GB" % (vm.total / 2**30, vm.available / 2**30))
        du = psutil.disk_usage("C:\\")
        lines.append("  C盘: 总 %.1f GB / 剩余 %.1f GB" % (du.total / 2**30, du.free / 2**30))
    except Exception:
        try:
            import shutil
            total, used, free = shutil.disk_usage("C:\\")
            lines.append("  C盘: 总 %.1f GB / 剩余 %.1f GB" % (total / 2**30, free / 2**30))
        except Exception:
            pass
    lines.append("")
    lines.append("【授权服务】")
    try:
        r = subprocess.run(["sc", "query", "almservice"],
                           capture_output=True, text=True, errors="ignore")
        for line in r.stdout.splitlines():
            if "STATE" in line:
                lines.append("  " + line.strip())
    except Exception:
        pass
    lines.append("")
    lines.append("【运行库】")
    try:
        for n, s in check_runtime_silent():
            lines.append("  %s: %s" % (n, s))
    except Exception:
        pass
    lines.append("")
    lines.append("【日志错误行】")
    if ctx["errors"]:
        for e in ctx["errors"]:
            lines.append("  " + e[:220])
    else:
        lines.append("  （未捕获到）")
    if ctx["log_path"]:
        lines.append("")
        lines.append("【日志文件】%s" % ctx["log_path"])
    lines.append("")
    lines.append("【知识库建议】")
    if ctx["advice"]:
        for a in ctx["advice"]:
            lines.append("  • " + a)
    else:
        lines.append("  （未命中）")
    lines.append("")
    lines.append("请把本文件连同安装日志一起发给 AI 助手/开发者，即可人工分析。")
    lines.append("")
    lines.append("【方案反馈】这条方案/工具对你有用吗？如果解决了问题，或希望补充功能，")
    lines.append("欢迎回复：微信 %s / 邮箱 %s" % (FEEDBACK_WECHAT, FEEDBACK_EMAIL))

    fname = os.path.join(BASE_DIR, "报错报告_%s.txt" %
                         datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log("报告已生成: %s" % fname)
    log("把该 txt 发给你信任的 AI 助手/开发者即可获得人工分析。")
    log("")
    return fname


def check_runtime_silent():
    """check_runtime 的静默版：只返回 [(名称, 状态)]，不打印。"""
    import winreg

    def reg_read(path, name, hive=winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, path) as k:
                v, _ = winreg.QueryValueEx(k, name)
                return v
        except Exception:
            return None

    results = []
    rel = reg_read(r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full", "Release")
    if rel and int(rel) >= 528372:
        results.append((".NET Framework 4.8.1", "✓ 已安装"))
    elif rel and int(rel) >= 528040:
        results.append((".NET Framework 4.8", "✓ 已安装"))
    else:
        results.append((".NET Framework 4.8", "✗ 未检测到"))
    ndp35 = reg_read(r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v3.5", "Install")
    results.append((".NET Framework 3.5", "✓ 已启用" if ndp35 else "✗ 未启用"))
    vc_names = []
    for view in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, view) as k:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(k, i)
                        i += 1
                    except OSError:
                        break
                    try:
                        with winreg.OpenKey(k, sub) as sk:
                            dn, _ = winreg.QueryValueEx(sk, "DisplayName")
                            if dn and "Visual C++" in dn and "Redistributable" in dn:
                                vc_names.append(dn.strip())
                    except Exception:
                        pass
        except OSError:
            pass
    results.append(("VC++ 运行库",
                    "✓ 已装 %d 个" % len(set(vc_names)) if vc_names else "✗ 未检测到"))
    return results


# ---------------------------------------------------------------------
# 8. 联网查错 + 求助引导页 + 话术模板
# ---------------------------------------------------------------------

# 代码仓库地址（用于引导用户提交 Issue / PR 贡献知识库）
# 国内访问 GitHub 可能打不开，建议同时配置国内仓库（腾讯云 CNB）。
# 填好后，引导页会自动列出多个提交入口，并检测 GitHub 可达性给出提示。
# 例如:
#   REPOS = {
#       "github":  "https://github.com/yourname/siemens-tools",      # GitHub（国外）
#       "cnb":     "https://cnb.cool/yourname/siemens-tools",         # 腾讯云 CNB 云原生构建（国内）
#   }
REPOS = {
    "github":  "https://github.com/chenpiyanghappy/SiemensInstallHelper",
    "cnb":     "https://cnb.cool/chenpiyanghappy/SiemensInstallHelper",
}


def check_github_reachable(timeout=3):
    """探测 GitHub 在当前网络下是否可访问（超时短，失败按不可达处理）。"""
    import urllib.request
    try:
        req = urllib.request.Request("https://github.com",
                                     method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:
        return False


def build_contrib_block():
    """根据 REPOS 配置生成引导页"贡献知识库"区块 HTML。"""
    entries = [
        ("GitHub", REPOS.get("github")),
        ("腾讯云 CNB", REPOS.get("cnb")),
    ]
    entries = [(n, u) for n, u in entries if u]

    if not entries:
        return """
        <div class="card">
          <h3>③ 贡献你的发现（可选）</h3>
          <p class="tip">开发者还没有配置代码仓库。如果你有新的报错案例，把上面的话术+日志发给安装工具的提供者即可。</p>
        </div>
        """

    btns = "".join(
        '<a class="btn" target="_blank" href="{u}/issues/new">提交 Issue（{n}）</a>'.format(u=u, n=n)
        for n, u in entries)

    # 检测 GitHub 可达性，给出引导提示
    tip = ""
    has_github = any(n == "GitHub" for n, _ in entries)
    has_cn = any(n != "GitHub" for n, _ in entries)
    if has_github:
        reach = check_github_reachable()
        if reach:
            tip = "<p class='tip'>✓ 检测到 GitHub 当前可访问。</p>"
        elif has_cn:
            tip = ("<p class='tip'>⚠ 检测到当前网络访问 GitHub 可能不通（国内常见），"
                   "请优先使用下方<b>国内仓库</b>入口。</p>")
        else:
            tip = ("<p class='tip'>⚠ 检测到当前网络访问 GitHub 可能不通（国内常见），"
                   "如提交失败请把话术发给工具提供者。</p>")
    elif has_cn:
        tip = "<p class='tip'>✓ 已配置国内仓库入口，国内网络可正常访问。</p>"

    return """
    <div class="card">
      <h3>③ 贡献你的发现（可选）</h3>
      <p>如果你这次遇到的报错很特别，或找到了解决办法，欢迎提交给开发者，帮助完善知识库：</p>
      {tip}
      {btns}
      <p class="tip">提交时请附上：报错关键词（能匹配到的文字）+ 解决办法。开发者会合并进工具的知识库。</p>
    </div>
    """.format(tip=tip, btns=btns)


def collect_error_context():
    """收集报错上下文（最近错误行、系统信息、授权、运行库、建议）。"""
    import platform
    import datetime
    ctx = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os": "%s (%s)" % (platform.platform(), platform.version()),
        "errors": [],
        "log_path": None,
        "advice": [],
        "runtime": [],
    }
    path = find_log()
    if path and os.path.exists(path):
        ctx["log_path"] = path
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            ctx["errors"] = [l for l in content.splitlines()
                             if is_error_line(l)][:8]
            for pattern, text in KNOWLEDGE:
                if re.search(pattern, content, re.IGNORECASE):
                    ctx["advice"].append(text)
        except Exception:
            pass
    try:
        rt = check_runtime_silent()
        ctx["runtime"] = ["%s %s" % (n, s) for n, s in rt]
    except Exception:
        pass
    return ctx


def get_help_script(ctx=None):
    """生成通用求助话术模板（方便用户直接复制去问 AI / 发 issue）。"""
    if ctx is None:
        ctx = collect_error_context()
    lines = []
    lines.append("【问题】西门子专业软件安装失败，求帮助分析")
    lines.append("")
    lines.append("【系统信息】")
    lines.append(ctx["os"])
    lines.append("")
    lines.append("【错误信息】")
    if ctx["errors"]:
        for e in ctx["errors"]:
            lines.append("  " + e[:200])
    else:
        lines.append("  （未捕获到日志错误，请看下方日志文件）")
    lines.append("")
    if ctx["log_path"]:
        lines.append("【日志文件】%s" % ctx["log_path"])
        lines.append("（建议把该文件也一起发过来）")
        lines.append("")
    lines.append("【已安装环境】")
    for r in ctx["runtime"]:
        lines.append("  " + r)
    lines.append("")
    lines.append("【自动分析建议】")
    if ctx["advice"]:
        for a in ctx["advice"]:
            lines.append("  • " + a)
    else:
        lines.append("  （无）")
    lines.append("")
    lines.append("【已尝试】")
    lines.append("  1. 以管理员身份运行安装程序")
    lines.append("  2. 重启电脑后重试")
    lines.append("")
    lines.append("请帮我看看这个错误可能是什么原因、应该怎么解决？")
    return "\n".join(lines)


def build_help_page(ctx=None):
    """生成本地求助引导页 HTML，返回 (html_path, 话术文本)。

    引导页包含：复制话术、打开搜索、GitHub 提交入口。
    """
    import html as htmlmod
    import datetime
    if ctx is None:
        ctx = collect_error_context()
    script = get_help_script(ctx)
    esc = htmlmod.escape

    err_html = ""
    for e in ctx["errors"]:
        err_html += "<div class='err'>%s</div>" % esc(e[:220])
    if not err_html:
        err_html = "<div class='err'>（未捕获到日志错误）</div>"

    adv_html = ""
    for a in ctx["advice"]:
        adv_html += "<li>%s</li>" % esc(a)
    if not adv_html:
        adv_html = "<li>（未命中知识库）</li>"

    rt_html = "".join("<li>%s</li>" % esc(r) for r in ctx["runtime"]) or "<li>（未检测）</li>"

    gh_block = build_contrib_block()

    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>西门子安装求助引导</title>
<style>
  body {{ font-family: "Microsoft YaHei", sans-serif; max-width: 860px; margin: 24px auto; padding: 0 16px; background: #f5f7fa; color: #222; }}
  h1 {{ color: #2b5b9c; }}
  h2 {{ margin-top: 28px; color: #333; }}
  .steps {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0; }}
  .step {{ flex: 1 1 200px; background: #fff; border: 1px solid #dfe3ea; border-radius: 10px; padding: 12px; }}
  .step b {{ color: #2b5b9c; }}
  .card {{ background: #fff; border: 1px solid #dfe3ea; border-radius: 10px; padding: 16px; margin: 12px 0; }}
  .err {{ background: #fdecea; color: #b42318; border-radius: 6px; padding: 6px 10px; margin: 6px 0; font-family: Consolas, monospace; font-size: 13px; word-break: break-all; }}
  .btn {{ display: inline-block; margin: 6px 8px 6px 0; padding: 10px 18px; background: #2b5b9c; color: #fff; border-radius: 8px; text-decoration: none; font-size: 14px; }}
  .btn.gray {{ background: #7f8c8d; }}
  .tip {{ color: #666; font-size: 13px; }}
  textarea {{ width: 100%; box-sizing: border-box; height: 280px; font-family: Consolas, monospace; font-size: 13px; border: 1px solid #dfe3ea; border-radius: 8px; padding: 10px; background: #fbfcfe; }}
  li {{ margin: 4px 0; }}
</style>
</head>
<body>
  <h1>西门子安装 · 求助引导</h1>
  <p class="tip">生成时间：{time} ｜ 系统：{os}</p>

  <div class="steps">
    <div class="step"><b>① 复制话术</b><br>点下面按钮，把求助内容复制到剪贴板</div>
    <div class="step"><b>② 发给 AI / 搜索</b><br>粘贴给 AI 助手问，或用搜索按钮查官方/社区</div>
    <div class="step"><b>③ 提交给开发者</b><br>把新报错贡献到知识库（GitHub 提 issue）</div>
  </div>

  <div class="card">
    <h2>一键复制求助话术</h2>
    <p class="tip">复制后粘贴给 AI 助手（如豆包）、发到技术社区，或提交 GitHub issue 即可。</p>
    <textarea id="script" readonly>{script}</textarea>
    <br>
    <button class="btn" onclick="copyScript()">📋 复制话术</button>
    <a class="btn gray" target="_blank" id="searchLink" href="#">🔍 在 Bing 搜索这个错误</a>
    <span id="copyTip" class="tip"></span>
  </div>

  <div class="card">
    <h2>报错详情（自动抓取）</h2>
    <p>最近错误行：</p>
    {errors}
    <p>知识库自动建议：</p>
    <ul>{advice}</ul>
    <p>已安装环境：</p>
    <ul>{runtime}</ul>
    <p class="tip">日志文件：{logpath}</p>
  </div>

  {gh}

  <script>
  function copyScript() {{
    var ta = document.getElementById('script');
    var tip = document.getElementById('copyTip');
    ta.focus(); ta.select();
    var ok = false;
    try {{ ok = document.execCommand('copy'); }} catch(e) {{}}
    if (!ok && navigator.clipboard) {{
      navigator.clipboard.writeText(ta.value).then(function(){{ tip.textContent = '✓ 已复制到剪贴板'; }});
      return;
    }}
    tip.textContent = ok ? '✓ 已复制到剪贴板' : '复制失败，请手动全选复制';
  }}
  // 搜索链接带上错误关键词
  (function() {{
    var err = '';
    var els = document.querySelectorAll('.err');
    if (els.length) err = els[0].textContent.trim().slice(0, 120);
    var q = encodeURIComponent(err + ' TIA Portal 西门子 解决办法');
    document.getElementById('searchLink').href = 'https://www.bing.com/search?q=' + q;
  }})();
  </script>
</body>
</html>
""".format(
        time=esc(ctx["time"]), os=esc(ctx["os"]),
        script=esc(script), errors=err_html, advice=adv_html,
        runtime=rt_html, logpath=esc(ctx["log_path"] or "（未找到）"),
        gh=gh_block,
    )

    fname = os.path.join(BASE_DIR, "求助引导_%s.html" %
                         datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    with open(fname, "w", encoding="utf-8") as f:
        f.write(page)
    return fname, script


def open_help_page():
    """生成求助引导页并打开浏览器（联网查错入口）。"""
    import webbrowser
    log("")
    log("正在生成求助引导页（包含可直接复制的话术模板）...")
    path, script = build_help_page()
    log("引导页已生成: %s" % path)
    log("已自动复制功能：打开页面后点『复制话术』即可粘贴去问 AI 助手。")
    try:
        webbrowser.open("file:///" + path.replace("\\", "/"))
    except Exception as e:
        log("打开浏览器失败: %s（请手动打开上面的文件）" % e)
    return path


# ---------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("用法: siemens_install.py [clean|log|license|runtime|watch|download|install-runtime|report|search|find|basic-info|snapshot|preflight|feedback|issue-template|tips]")
        print("  或运行 run_install.py 打开图形界面")
        return
    cmd = sys.argv[1].lower()
    # 防误报提醒：命令行模式启动时提示一次
    try:
        sec = check_security_software()
        if sec:
            print("检测到运行中的安全软件：%s" % "、".join(sec))
            print("提示：本工具为绿色单文件，个别杀软可能误报；")
            print("      如被拦截请添加信任，或临时退出杀软后运行（装完记得重新开启）。")
            print("")
    except Exception:
        pass
    if cmd == "clean":
        clean_processes()
    elif cmd == "find":
        results = find_installers()
        if results:
            print("如需启动某个安装程序，请在图形界面中选择（自动提权）。")
    elif cmd == "log":
        analyze_and_fix()
    elif cmd == "license":
        check_license()
    elif cmd == "runtime":
        check_runtime()
    elif cmd == "download":
        download_runtime()
    elif cmd == "install-runtime":
        t = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
        install_runtime(t)
    elif cmd == "report":
        export_report()
    elif cmd == "basic-info":
        copy_basic_info_block()
        print(build_basic_info_block())
    elif cmd == "snapshot":
        export_env_snapshot()
    elif cmd == "preflight":
        check_env_preflight()
    elif cmd == "feedback":
        copy_feedback_block()
        print(build_feedback_block())
    elif cmd == "issue-template":
        copy_issue_template()
        print(build_issue_template())
    elif cmd == "tips":
        import tips as _tips
        _tips.tips_cli(sys.argv[2:])
    elif cmd == "search":
        open_help_page()
    elif cmd == "watch":
        w = InstallWatcher()
        w.reset()
        print("监控中（Ctrl+C 退出）...")
        try:
            while True:
                import time
                hits = w.poll()
                for h in hits:
                    print(h)
                time.sleep(5)
        except KeyboardInterrupt:
            print("已停止监控。")
    else:
        print("未知命令: %s" % cmd)


if __name__ == "__main__":
    main()
