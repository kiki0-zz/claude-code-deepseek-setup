#!/usr/bin/env bash
# ==============================================================================
# Claude Code + DeepSeek 一键安装入口 (Linux / macOS)
#
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/install.sh | bash
#
# 或国内加速版:
#   curl -fsSL https://gh-proxy.com/https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/install.sh | bash
#
# 这个脚本做的事:
#   1. 检查 python3 是否存在
#   2. 下载真正的安装脚本 setup_claude_code.py 到临时目录
#   3. 用 python3 启动它 (stdin 重定向到真终端, 保证交互输入正常)
#   4. 退出时清理临时文件
# ==============================================================================

set -e

# ---- 颜色 ----
G='\033[32m'; Y='\033[33m'; R='\033[31m'; B='\033[36m'; BOLD='\033[1m'; END='\033[0m'

ok()    { printf "${G}[ OK ]${END}  %s\n" "$*"; }
info()  { printf "${B}[INFO]${END}  %s\n" "$*"; }
warn()  { printf "${Y}[WARN]${END}  %s\n" "$*"; }
err()   { printf "${R}[FAIL]${END}  %s\n" "$*"; }

# ---- 配置 ----
RAW_URL="https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/setup_claude_code.py"
PROXY_URL="https://gh-proxy.com/${RAW_URL}"

printf "${BOLD}\n"
printf "╔══════════════════════════════════════════════════════════╗\n"
printf "║  Claude Code + DeepSeek  一键安装入口 (Linux/macOS)      ║\n"
printf "╚══════════════════════════════════════════════════════════╝\n"
printf "${END}\n"

# ---- 检查 python3 ----
if ! command -v python3 >/dev/null 2>&1; then
    err "未检测到 python3, 请先安装:"
    echo "    Ubuntu/Debian: sudo apt install -y python3"
    echo "    CentOS/RHEL:   sudo yum install -y python3"
    echo "    macOS:         brew install python3  (或自带)"
    exit 1
fi
ok "python3 已就绪: $(python3 --version)"

# ---- 检查 curl 或 wget ----
if command -v curl >/dev/null 2>&1; then
    DOWNLOADER="curl -fsSL"
elif command -v wget >/dev/null 2>&1; then
    DOWNLOADER="wget -qO-"
else
    err "未检测到 curl 或 wget, 无法下载脚本"
    exit 1
fi

# ---- 下载脚本到临时文件 ----
TMP_FILE="$(mktemp -t claude-code-setup-XXXXXX.py)"
trap 'rm -f "$TMP_FILE"' EXIT

info "正在下载安装脚本..."
if $DOWNLOADER "$RAW_URL" > "$TMP_FILE" 2>/dev/null && [ -s "$TMP_FILE" ]; then
    ok "下载成功 (来源: GitHub 官方)"
else
    warn "GitHub 直连失败, 尝试国内镜像 gh-proxy.com ..."
    if $DOWNLOADER "$PROXY_URL" > "$TMP_FILE" 2>/dev/null && [ -s "$TMP_FILE" ]; then
        ok "下载成功 (来源: gh-proxy.com 国内镜像)"
    else
        err "两个源都下载失败, 请检查网络后重试"
        exit 1
    fi
fi

# 简单校验下载的内容是 Python 脚本 (不是 404 页面)
if ! head -1 "$TMP_FILE" | grep -q "python"; then
    err "下载的内容不是有效的 Python 脚本 (可能是 404), 请检查仓库路径是否正确"
    head -3 "$TMP_FILE"
    exit 1
fi

# ---- 执行 (关键: stdin 重定向到 /dev/tty 保证交互正常) ----
echo
info "启动安装脚本..."
echo "------------------------------------------------------------"
python3 "$TMP_FILE" </dev/tty
