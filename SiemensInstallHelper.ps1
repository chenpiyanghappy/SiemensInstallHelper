# =====================================================================
#  西门子专业软件 安装助手  SiemensInstallHelper  v1.0
#  功能：
#    1. 安装前清理无用进程（加速安装、减少干扰）
#    2. 自动分析安装日志，按知识库给出解决建议
#    3. 安装期间实时监控，自动发现并处理报错
#    4. 检查 Automation License Manager（授权服务）是否正常
#  运行环境：Windows 7 / 10 / 11 自带 PowerShell，无需安装任何东西
#  用法：双击同目录的 bat 文件，或在此目录执行 powershell -File SiemensInstallHelper.ps1
# =====================================================================

# 测试模式：-TestMode 时不进入菜单，只加载函数（供自动化测试/二次开发使用）
param([switch]$TestMode)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = '西门子安装助手'

# ---------------------------------------------------------------------
# 配置区
# ---------------------------------------------------------------------

# 安装前可安全结束的第三方软件进程（按需增删；核心系统进程与杀毒绝不碰）
$CleanablePatterns = @(
    'chrome','msedge','firefox','iexplore',              # 浏览器
    'wechat','weixin','wxwork','qq','dingtalk','wemeet','feishu','lark',  # 聊天/会议
    'quark','thunder','xunlei','idman','netdisk','baidunetdisk','onedrive',  # 下载/网盘
    'potplayer','vlc','qqmusic','cloudmusic','kugou','kmplayer','yodao',  # 播放器/音乐
    'wps','et','wpp','wpscloudsvr','officeclicktorun'    # 办公(文档可能没保存，谨慎)
)

# 绝不结束的系统/安全进程（保护名单）
$ProtectedProcesses = @(
    'csrss','winlogon','lsass','services','smss','dwm','explorer','wininit',
    'svchost','fontdrvhost','ctfmon','audiodg','spoolsv','RuntimeBroker','sihost',
    'SearchApp','ShellExperienceHost','StartMenuExperienceHost',
    'MsMpEng','MsMpSvc','NisSrv','SecurityHealthService',
    'HipsDaemon','HipsMain','HipsTray','usysdiag','Lenovo','HdSvc','ISecuritySvc'
)

# 安装日志搜索位置（按顺序找，找到就用；找不到就只监控事件日志）
$InstallLogCandidates = @(
    "$env:TEMP\SIA_*.log",
    "$env:TEMP\Siemens*.log",
    "$env:TEMP\Setup*.log",
    "C:\Windows\Temp\SIA_*.log",
    "C:\Windows\Temp\Siemens*.log"
)

# 日志知识库：正则表达式 -> 诊断建议
$Knowledge = @(
    @{ Pattern = 'not enough (disk )?space|空间不足|0x80070070'; Advice = '磁盘空间不足。请清理 C 盘并释放至少 20GB 后重试。' }
    @{ Pattern = 'access is denied|access denied|拒绝访问|0x80070005'; Advice = '权限不足。请右键安装程序，选择"以管理员身份运行"。' }
    @{ Pattern = 'another instance|another setup|另一个实例|正在运行'; Advice = '已有安装程序或 TIA Portal 在运行。请先关闭它们（可用本工具"清理无用进程"），再重试。' }
    @{ Pattern = 'reboot|restart your computer|重新启动|重启'; Advice = '系统要求重启。请先重启电脑，再继续安装。' }
    @{ Pattern = '0x80070070'; Advice = '磁盘空间不足（错误 0x80070070）。请清理磁盘后重试。' }
    @{ Pattern = '0x80070643|1603|InstallFailure|Installation failed'; Advice = '安装失败（1603 / InstallFailure）。常见原因：权限不足、安装缓存异常、被安全软件拦截。建议：以管理员运行、清空 %TEMP%、重启后重试；仍失败则把日志发给 AI 助手分析。' }
    @{ Pattern = 'SetupUnit|SetupPackage.*Failed|AdsWorkerSetupPackage'; Advice = '某个安装组件包失败（如 HelpViewer_Server）。建议：单独重试该组件，或换安装顺序（先基础包后选件）；日志已记录该组件名。' }
    @{ Pattern = '0x800F0900|\.NET Framework 3\.5|启用 Windows 功能'; Advice = '缺少 .NET Framework 3.5 功能。控制面板 → 程序 → 启用或关闭 Windows 功能 → 勾选 .NET Framework 3.5（含 2.0 和 3.0）→ 确定。' }
    @{ Pattern = 'license|许可证|授权|license manager'; Advice = '授权/许可证问题。安装完成后打开 Automation License Manager 确认授权；如服务异常，运行本工具"检查授权服务"。' }
    @{ Pattern = 'sql server|database'; Advice = 'SQL Server / 数据库组件问题。确认没有残留的 SQL 安装冲突，必要时清理后重装。' }
    @{ Pattern = 'dcom|0x80040154|class not registered'; Advice = 'COM 组件注册问题。多为系统组件缺失，可尝试重启后再装；持续出现需检查系统完整性。' }
    @{ Pattern = 'wincc|scada'; Advice = 'WinCC/SCADA 组件问题。WinCC 组件与系统版本有关，建议按安装说明顺序安装，且避免与旧版混装。' }
    @{ Pattern = 'virus|antivirus|杀毒|安全软件'; Advice = '安全软件可能拦截安装。如确实需要，请暂时在杀毒软件中允许安装程序（不建议完全关闭防护）。' }
    @{ Pattern = 'tia portal|step 7'; Advice = 'TIA Portal / STEP 7 组件相关错误。请确认安装顺序（先基础包后选件），并以管理员运行。' }
)

# ---------------------------------------------------------------------
# 模块 1：清理无用进程
# ---------------------------------------------------------------------

function Clear-UnusedProcesses {
    Write-Host ''
    Write-Host '================ 清理无用进程 ================' -ForegroundColor Cyan
    Write-Host '说明：只结束第三方软件（浏览器/聊天/网盘/播放器等），' -ForegroundColor Yellow
    Write-Host '      系统核心进程与杀毒软件一律不碰。' -ForegroundColor Yellow
    Write-Host '      注意：正在编辑的文档请先保存！' -ForegroundColor Yellow

    $targets = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $p = $_.ProcessName.ToLower()
        ($CleanablePatterns | Where-Object { $p -like "*$_*" }) -and
        -not ($ProtectedProcesses | Where-Object { $p -like "*$_*" })
    }

    if (-not $targets) {
        Write-Host '没有发现可清理的第三方进程。' -ForegroundColor Green
        return
    }

    Write-Host ''
    Write-Host '将结束以下进程：' -ForegroundColor White
    $targets | Sort-Object ProcessName -Unique | ForEach-Object {
        Write-Host ("  - {0} (PID {1})" -f $_.ProcessName, $_.Id)
    }
    Write-Host ''
    $ans = Read-Host '确认结束这些进程？(y/N)'
    if ($ans -ne 'y' -and $ans -ne 'Y') {
        Write-Host '已取消。' -ForegroundColor Gray
        return
    }

    $killed = 0
    foreach ($t in $targets) {
        try {
            Stop-Process -Id $t.Id -Force -ErrorAction Stop
            $killed++
        } catch { }
    }
    Write-Host ("已结束 {0} 个进程。现在可以开始安装西门子软件了。" -f $killed) -ForegroundColor Green
}

# ---------------------------------------------------------------------
# 模块 2：分析安装日志
# ---------------------------------------------------------------------

function Get-InstallLog {
    foreach ($pattern in $InstallLogCandidates) {
        $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
        if ($files) { return $files[0].FullName }
    }
    return $null
}

function Analyze-LogFile {
    param([string]$LogPath)

    if (-not $LogPath -or -not (Test-Path -LiteralPath $LogPath)) {
        Write-Host '未找到安装日志。请把 SIA_*.log 之类的日志放到 %TEMP% 或 C:\Windows\Temp。' -ForegroundColor Yellow
        return
    }

    Write-Host ''
    Write-Host ("================ 分析安装日志：{0} ================" -f (Split-Path $LogPath -Leaf)) -ForegroundColor Cyan

    $content = Get-Content -LiteralPath $LogPath -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not $content) { $content = Get-Content -LiteralPath $LogPath -Encoding Default -ErrorAction SilentlyContinue }
    if (-not $content) { Write-Host '日志读取失败。' -ForegroundColor Red; return }

    $errors = $content | Where-Object { $_ -match 'ERROR|FAILED|Error|失败|错误' }
    Write-Host ("日志共 {0} 行，其中疑似错误 {1} 行。" -f $content.Count, ($errors | Measure-Object).Count) -ForegroundColor White

    if (($errors | Measure-Object).Count -eq 0) {
        Write-Host '未发现明显错误行，日志看起来正常 ✓' -ForegroundColor Green
        return
    }

    Write-Host ''
    Write-Host '--- 最近 8 条错误行 ---' -ForegroundColor White
    $errors | Select-Object -Last 8 | ForEach-Object {
        $line = $_.ToString()
        if ($line.Length -gt 180) { $line = $line.Substring(0, 180) + '...' }
        Write-Host ("  " + $line) -ForegroundColor Red
    }

    Write-Host ''
    Write-Host '--- 诊断建议（知识库匹配）---' -ForegroundColor White
    $hitCount = 0
    foreach ($rule in $Knowledge) {
        if ($content -match $rule.Pattern) {
            Write-Host ("  • " + $rule.Advice) -ForegroundColor Green
            $hitCount++
        }
    }
    if ($hitCount -eq 0) {
        Write-Host '  未命中知识库。建议把上面的错误行复制给 AI 助手分析。' -ForegroundColor Yellow
    }
}

# ---------------------------------------------------------------------
# 模块 4：检查授权服务（Automation License Manager）
# ---------------------------------------------------------------------

function Check-License {
    Write-Host ''
    Write-Host '================ 检查授权服务 (ALM) ================' -ForegroundColor Cyan

    $alm = Get-Service -Name 'almservice' -ErrorAction SilentlyContinue
    if (-not $alm) {
        Write-Host '未发现 Automation License Manager 服务。软件可能尚未安装或未安装完整。' -ForegroundColor Red
        return
    }
    if ($alm.Status -eq 'Running') {
        Write-Host '  ✓ Automation License Manager 服务运行正常' -ForegroundColor Green
    } else {
        Write-Host '  ✗ ALM 服务未运行！尝试启动...' -ForegroundColor Red
        try {
            Start-Service -Name 'almservice' -ErrorAction Stop
            Write-Host '  ✓ 已成功启动 ALM 服务' -ForegroundColor Green
        } catch {
            Write-Host '  ✗ 启动失败，可能需要管理员权限。右键本工具 → 以管理员身份运行。' -ForegroundColor Red
        }
    }
    $proc = Get-Process -Name 'almsrv64x' -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host '  ✓ 授权进程 almsrv64x 运行中' -ForegroundColor Green
    } else {
        Write-Host '  - 授权进程未运行（服务启动后会拉起）' -ForegroundColor Gray
    }
}

# ---------------------------------------------------------------------
# 模块 5：安装期间实时监控
# ---------------------------------------------------------------------

function Watch-Installation {
    Write-Host ''
    Write-Host '================ 实时监控安装（自动分析报错） ================' -ForegroundColor Cyan
    Write-Host '监控内容：新出现的系统错误事件 + 安装日志新增错误行。' -ForegroundColor Yellow
    Write-Host '按 Q 退出监控（安装完成后记得回来按 Q）。' -ForegroundColor Yellow
    Write-Host ''

    $logPath = Get-InstallLog
    if ($logPath) {
        Write-Host ("监控安装日志：{0}" -f $logPath) -ForegroundColor Gray
    } else {
        Write-Host '（未找到安装日志，将只监控系统事件日志）' -ForegroundColor Gray
    }

    $lastLine = 0
    if ($logPath) {
        $lastLine = (Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue | Measure-Object).Count
    }

    $firstRun = $true
    while ($true) {
        # 允许按键退出（Q）
        if ($Host.UI.RawUI.KeyAvailable) {
            $key = $Host.UI.RawUI.ReadKey('NoEcho, IncludeKeyDown')
            if ($key.Character -match 'q|Q') {
                Write-Host ''
                Write-Host '已停止监控。' -ForegroundColor Gray
                return
            }
        }

        # 1) 检查安装日志新增错误
        if ($logPath) {
            $nowCount = (Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue | Measure-Object).Count
            if ($nowCount -gt $lastLine) {
                $newLines = Get-Content -LiteralPath $logPath | Select-Object -Skip $lastLine
                $badLines = $newLines | Where-Object { $_ -match 'ERROR|FAILED|Error|失败|错误' }
                if ($badLines) {
                    Write-Host ''
                    Write-Host ("[发现新错误 " + (Get-Date -Format 'HH:mm:ss') + "]") -ForegroundColor Red
                    $badLines | ForEach-Object {
                        $l = $_.ToString(); if ($l.Length -gt 200) { $l = $l.Substring(0, 200) + '...' }
                        Write-Host ("  " + $l) -ForegroundColor Red
                    }
                    # 知识库匹配
                    $joined = $newLines -join ' '
                    foreach ($rule in $Knowledge) {
                        if ($joined -match $rule.Pattern) {
                            Write-Host ("  → 建议：" + $rule.Advice) -ForegroundColor Green
                            break
                        }
                    }
                    Write-Host '  → 完整建议可运行菜单"分析日志"。' -ForegroundColor Gray
                }
                $lastLine = $nowCount
            }
        }

        # 2) 检查系统事件日志新增错误（最近 60 秒）
        $since = (Get-Date).AddSeconds(-60)
        $newEvents = Get-WinEvent -FilterHashtable @{ LogName = 'System'; Level = 1, 2; StartTime = $since } -MaxEvents 20 -ErrorAction SilentlyContinue
        foreach ($ev in $newEvents) {
            $msg = $ev.Message
            $isSiemens = $msg -match 'Siemens|SIMATIC|TIA|SCS|WinCC|almservice|MSI|安装'
            if ($isSiemens) {
                Write-Host ''
                Write-Host ("[系统事件 " + $ev.TimeCreated.ToString('HH:mm:ss') + " 事件" + $ev.Id + "]") -ForegroundColor Red
                $short = $msg; if ($short.Length -gt 200) { $short = $short.Substring(0, 200) + '...' }
                Write-Host ("  " + $short) -ForegroundColor Red
                foreach ($rule in $Knowledge) {
                    if ($msg -match $rule.Pattern) {
                        Write-Host ("  → 建议：" + $rule.Advice) -ForegroundColor Green
                        break
                    }
                }
            }
        }

        if ($firstRun) {
            Write-Host ("[监控已启动 " + (Get-Date -Format 'HH:mm:ss') + "] 每 5 秒检查一次...") -ForegroundColor Gray
            $firstRun = $false
        }
        Start-Sleep -Seconds 5
    }
}

# ---------------------------------------------------------------------
# 主菜单
# ---------------------------------------------------------------------

if ($TestMode) {
    Write-Host '[测试模式] 函数已加载，不进入菜单。' -ForegroundColor Gray
    return
}

function Show-Menu {
    Write-Host ''
    Write-Host '╔════════════════════════════════════════════╗'
    Write-Host '║  西门子专业软件 安装助手  v1.0             ║'
    Write-Host '║  零依赖 · Windows 自带 PowerShell 运行      ║'
    Write-Host '╚════════════════════════════════════════════╝'
    Write-Host ''
    Write-Host '  1. 清理无用进程（安装前加速）' -ForegroundColor White
    Write-Host '  2. 分析安装日志（自动诊断）' -ForegroundColor White
    Write-Host '  3. 检查授权服务 (ALM)' -ForegroundColor White
    Write-Host '  4. 实时监控安装（自动发现报错）' -ForegroundColor White
    Write-Host '  5. 全部自动处理（1+3）' -ForegroundColor White
    Write-Host '  Q. 退出' -ForegroundColor White
    Write-Host ''
}

$running = $true
while ($running) {
    Show-Menu
    $choice = Read-Host '请选择'
    switch ($choice) {
        '1' { Clear-UnusedProcesses }
        '2' { Analyze-LogFile (Get-InstallLog) }
        '3' { Check-License }
        '4' { Watch-Installation }
        '5' {
            Write-Host ''; Write-Host '===== 全部自动处理 =====' -ForegroundColor Cyan
            Clear-UnusedProcesses
            Check-License
        }
        'q' { $running = $false }
        'Q' { $running = $false }
        default { Write-Host '无效选择，请重新输入。' -ForegroundColor Red }
    }
}
Write-Host ''
Write-Host '谢谢使用，再见！'
