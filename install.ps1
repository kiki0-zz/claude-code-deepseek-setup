# ==============================================================================
# Claude Code + DeepSeek 一键安装入口 (Windows PowerShell)
#
# 推荐用法 (复制整行, 粘到 PowerShell 里回车):
#   Set-ExecutionPolicy -Scope Process Bypass -Force; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; irm https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/install.ps1 | iex
#
# 国内加速 (无需梯子):
#   Set-ExecutionPolicy -Scope Process Bypass -Force; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; irm https://gh-proxy.com/https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/install.ps1 | iex
#
# 为什么需要前两段:
#   1. PowerShell 默认 ExecutionPolicy=Restricted, 不加 Bypass 会静默失败 (光标直接回去)
#   2. PowerShell 5.1 (Win10/11 自带) 默认禁用 TLS1.2, 不开启 irm 也会静默失败
#
# 这个脚本做的事:
#   1. 自动启用 TLS1.2 (脚本内层兜底)
#   2. 检查 / 用 winget 自动安装 Python, Git, Node.js
#   3. 下载真正的安装脚本 setup_claude_code.py 到临时目录 (官方源 + 国内镜像双通道)
#   4. 用 python 启动它
#   5. 退出时清理临时文件
# ==============================================================================

# ---- 关键: 不要用 'Stop', 否则下载失败时整个管道被吞掉, 用户只看到光标回去 ----
$ErrorActionPreference = 'Continue'

# ---- 内层兜底: 启用 TLS1.2 (PowerShell 5.1 默认只开 SSL3/TLS1.0, irm 会静默失败) ----
try {
    [Net.ServicePointManager]::SecurityProtocol = `
        [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {}

# ---- 颜色输出函数 ----
function Write-Ok    { param([string]$Msg) Write-Host "[ OK ]  $Msg" -ForegroundColor Green }
function Write-Info  { param([string]$Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Cyan }
function Write-Warn  { param([string]$Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "[FAIL]  $Msg" -ForegroundColor Red }
function Write-Step  { param([string]$Msg) Write-Host ""; Write-Host "==== $Msg ====" -ForegroundColor White }

# ---- 配置 ----
$RawUrl   = 'https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/setup_claude_code.py'
$ProxyUrl = "https://gh-proxy.com/$RawUrl"

Write-Host ""
Write-Host "================================================================" -ForegroundColor White
Write-Host "  Claude Code + DeepSeek  Windows 一键安装入口                   " -ForegroundColor White
Write-Host "================================================================" -ForegroundColor White
Write-Host ""

# ============================================================================
# 工具函数: 把当前进程的 PATH 与系统 PATH 合并刷新, 让刚装完的工具立即可用
# (winget 装完不重启终端时, where.exe 找不到新装的命令, 必须手动刷)
# ============================================================================
function Update-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = ($machine, $user -join ';')
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# ============================================================================
# Step 1: 检查 winget (Win10 1809+ / Win11 自带; 老系统会缺)
# ============================================================================
Write-Step "Step 1/4  环境检查"

$hasWinget = Test-Command 'winget'
if ($hasWinget) {
    Write-Ok "winget 已就绪, 缺失依赖将自动安装"
} else {
    Write-Warn "未检测到 winget (一般是 Win10 1809 之前的版本)"
    Write-Warn "脚本将跳过自动安装, 缺少依赖时会给出下载链接让你手动装"
}

# ============================================================================
# Step 2: 用 winget 自动安装 Python / Git / Node.js
# ============================================================================
Write-Step "Step 2/4  安装基础依赖 (Python, Git, Node.js)"

# 通用安装函数: 检测命令是否存在, 不存在就 winget install
function Install-IfMissing {
    param(
        [string]$CmdName,    # 安装后用来探测是否成功的命令 (如 'python', 'git', 'node')
        [string]$WingetId,   # winget 的 Id, 如 'Python.Python.3.12'
        [string]$DisplayName # 给用户看的友好名字
    )

    if (Test-Command $CmdName) {
        $verLine = ''
        try { $verLine = (& $CmdName --version 2>&1 | Select-Object -First 1) } catch {}
        Write-Ok "$DisplayName 已安装: $verLine"
        return $true
    }

    if (-not $hasWinget) {
        Write-Err "$DisplayName 未安装, 且当前系统不支持 winget"
        switch ($CmdName) {
            'python' { Write-Host "    手动下载: https://www.python.org/downloads/ (安装时务必勾选 'Add Python to PATH')" -ForegroundColor Yellow }
            'git'    { Write-Host "    手动下载: https://git-scm.com/download/win" -ForegroundColor Yellow }
            'node'   { Write-Host "    手动下载: https://nodejs.org/ (选 LTS 版本)" -ForegroundColor Yellow }
        }
        return $false
    }

    Write-Info "正在用 winget 安装 $DisplayName ($WingetId) ..."
    Write-Info "  (首次使用 winget 可能弹出协议, 输入 Y 同意即可)"

    # --silent: 静默安装  --accept-*: 同意条款  --scope user: 装到用户目录, 不需要管理员
    $args = @(
        'install', '--id', $WingetId,
        '--exact',
        '--silent',
        '--accept-package-agreements',
        '--accept-source-agreements',
        '--scope', 'user'
    )
    & winget @args
    $exit = $LASTEXITCODE

    # winget 退出码: 0=成功, -1978335189(0x8A15002B)=已是最新, 其他都按失败处理但再探测一次
    Update-SessionPath

    if (Test-Command $CmdName) {
        $verLine = ''
        try { $verLine = (& $CmdName --version 2>&1 | Select-Object -First 1) } catch {}
        Write-Ok "$DisplayName 安装成功: $verLine"
        return $true
    } else {
        Write-Err "$DisplayName 安装后仍找不到命令 (winget exit=$exit)"
        Write-Warn "可能需要关闭并重开 PowerShell 让 PATH 生效, 然后再跑一次本命令"
        return $false
    }
}

# Python: 优先走 python, 老机器装个 3.12
$pyOk = $false
foreach ($c in @('python', 'python3', 'py')) {
    if (Test-Command $c) {
        $script:pythonCmd = $c
        $verLine = ''
        try { $verLine = (& $c --version 2>&1 | Select-Object -First 1) } catch {}
        Write-Ok "Python 已安装: $verLine (命令: $c)"
        $pyOk = $true
        break
    }
}
if (-not $pyOk) {
    $pyOk = Install-IfMissing -CmdName 'python' -WingetId 'Python.Python.3.12' -DisplayName 'Python 3.12'
    if ($pyOk) { $script:pythonCmd = 'python' }
}

# Git
$gitOk  = Install-IfMissing -CmdName 'git'  -WingetId 'Git.Git'              -DisplayName 'Git'

# Node.js LTS (自带 npm)
$nodeOk = Install-IfMissing -CmdName 'node' -WingetId 'OpenJS.NodeJS.LTS'    -DisplayName 'Node.js LTS'

if (-not $pyOk) {
    Write-Host ""
    Write-Err "Python 未就绪, 无法继续。请手动安装后重试。"
    exit 1
}
if (-not ($gitOk -and $nodeOk)) {
    Write-Host ""
    Write-Warn "部分依赖未装齐, 后续 Python 脚本可能再次提示。继续尝试..."
}

# ============================================================================
# Step 3: 下载 setup_claude_code.py (官方源 + 国内镜像双通道)
# ============================================================================
Write-Step "Step 3/4  下载安装脚本"

$tmpFile = Join-Path $env:TEMP "claude-code-setup-$([guid]::NewGuid().ToString('N').Substring(0,8)).py"

function Try-Download {
    param([string]$Url, [string]$Label, [int]$TimeoutSec = 15)
    Write-Info "尝试下载: $Label"
    try {
        Invoke-WebRequest -Uri $Url -OutFile $tmpFile -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        if ((Test-Path $tmpFile) -and (Get-Item $tmpFile).Length -gt 0) {
            Write-Ok "下载成功 ($Label)"
            return $true
        }
        Write-Warn "下载文件为空 ($Label)"
        return $false
    } catch {
        Write-Warn "$Label 失败: $($_.Exception.Message)"
        return $false
    }
}

$downloaded = (Try-Download -Url $RawUrl   -Label 'GitHub 官方源'      -TimeoutSec 10) -or `
              (Try-Download -Url $ProxyUrl -Label 'gh-proxy.com 镜像' -TimeoutSec 20)

if (-not $downloaded) {
    Write-Err "两个源都下载失败, 请检查网络后重试"
    Write-Host ""
    Write-Host "排查建议:" -ForegroundColor Yellow
    Write-Host "  1. 是否能在浏览器打开 https://gh-proxy.com/ ?"
    Write-Host "  2. 公司网络/防火墙是否拦截 raw.githubusercontent.com ?"
    Write-Host "  3. 试试关掉 VPN/代理 软件再跑 (有些代理会拦 PowerShell 请求)"
    if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue }
    exit 1
}

# 简单校验下载的内容是不是 python 脚本 (防止下到 404 HTML 页)
$firstLines = Get-Content $tmpFile -TotalCount 5 -ErrorAction SilentlyContinue
$joined = ($firstLines -join "`n").ToLower()
if ($joined -notmatch 'python' -and $joined -notmatch 'claude') {
    Write-Err "下载的内容不像 Python 脚本, 仓库路径可能有误。前 5 行内容:"
    $firstLines | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue
    exit 1
}

# ============================================================================
# Step 4: 启动 Python 脚本
# ============================================================================
Write-Step "Step 4/4  启动安装脚本"

try {
    & $script:pythonCmd $tmpFile
    $pyExit = $LASTEXITCODE
} catch {
    Write-Err "执行 Python 脚本时异常: $($_.Exception.Message)"
    $pyExit = 1
} finally {
    if (Test-Path $tmpFile) {
        Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue
    }
}

exit $pyExit
