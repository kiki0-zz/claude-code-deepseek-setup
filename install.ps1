# ==============================================================================
# Claude Code + DeepSeek 一键安装入口 (Windows PowerShell)
#
# 用法:
#   irm https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/install.ps1 | iex
#
# 国内加速:
#   irm https://gh-proxy.com/https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/install.ps1 | iex
#
# 这个脚本做的事:
#   1. 检查 python 是否存在
#   2. 下载真正的安装脚本 setup_claude_code.py 到临时目录
#   3. 用 python 启动它
#   4. 退出时清理临时文件
# ==============================================================================

$ErrorActionPreference = 'Stop'

# ---- 颜色输出函数 ----
function Write-Ok    { param([string]$Msg) Write-Host "[ OK ]  $Msg" -ForegroundColor Green }
function Write-Info  { param([string]$Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Cyan }
function Write-Warn  { param([string]$Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "[FAIL]  $Msg" -ForegroundColor Red }

# ---- 配置 ----
$RawUrl   = 'https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/setup_claude_code.py'
$ProxyUrl = "https://gh-proxy.com/$RawUrl"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor White
Write-Host "║  Claude Code + DeepSeek  一键安装入口 (Windows)          ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor White
Write-Host ""

# ---- 检查 python ----
$pythonCmd = $null
foreach ($cmd in @('python', 'python3', 'py')) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $pythonCmd = $cmd
        break
    }
}

if (-not $pythonCmd) {
    Write-Err "未检测到 Python, 请先安装:"
    Write-Host "    https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "    (安装时务必勾选 'Add Python to PATH')"
    exit 1
}

$pyVer = & $pythonCmd --version 2>&1
Write-Ok "Python 已就绪: $pyVer (使用命令: $pythonCmd)"

# ---- 下载脚本到临时文件 ----
$tmpFile = Join-Path $env:TEMP "claude-code-setup-$([guid]::NewGuid().ToString('N').Substring(0,8)).py"

Write-Info "正在下载安装脚本..."
$downloaded = $false

# 尝试 GitHub 官方源
try {
    Invoke-WebRequest -Uri $RawUrl -OutFile $tmpFile -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ((Get-Item $tmpFile).Length -gt 0) {
        Write-Ok "下载成功 (来源: GitHub 官方)"
        $downloaded = $true
    }
} catch {
    Write-Warn "GitHub 直连失败: $($_.Exception.Message)"
}

# 失败则尝试国内镜像
if (-not $downloaded) {
    Write-Warn "尝试国内镜像 gh-proxy.com ..."
    try {
        Invoke-WebRequest -Uri $ProxyUrl -OutFile $tmpFile -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        if ((Get-Item $tmpFile).Length -gt 0) {
            Write-Ok "下载成功 (来源: gh-proxy.com 国内镜像)"
            $downloaded = $true
        }
    } catch {
        Write-Err "镜像源也失败: $($_.Exception.Message)"
    }
}

if (-not $downloaded) {
    Write-Err "两个源都下载失败, 请检查网络后重试"
    if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force }
    exit 1
}

# 简单校验下载的内容
$firstLine = Get-Content $tmpFile -TotalCount 1
if ($firstLine -notmatch 'python') {
    Write-Err "下载的内容不是有效的 Python 脚本, 可能仓库路径有误"
    Get-Content $tmpFile -TotalCount 3
    Remove-Item $tmpFile -Force
    exit 1
}

# ---- 执行 ----
Write-Host ""
Write-Info "启动安装脚本..."
Write-Host ("-" * 60)

try {
    & $pythonCmd $tmpFile
} finally {
    # 清理临时文件
    if (Test-Path $tmpFile) {
        Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue
    }
}
