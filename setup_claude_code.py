#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 一键安装与 DeepSeek API 配置脚本
================================================
跨平台支持: Windows / Linux / macOS

功能:
  1. 检查前置依赖 (Git, Node.js >= 18, npm)
  2. 全局安装 @anthropic-ai/claude-code (如未安装)
  3. 交互式输入 DeepSeek API Key (隐藏输入)
  4. 菜单选择主模型 / 小快模型
  5. 写入永久环境变量 (Windows: setx;  Linux/macOS: ~/.bashrc 或 ~/.zshrc)
  6. 运行 claude doctor 验证

用法:
    python setup_claude_code.py
"""

import os
import sys
import time
import shutil
import platform
import subprocess
import urllib.request
from getpass import getpass
from pathlib import Path

# ---------------------------------------------------------------------------
# 终端彩色输出 (Windows 10+ / Linux / macOS 均支持 ANSI)
# ---------------------------------------------------------------------------
class C:
    R = "\033[31m"      # red
    G = "\033[32m"      # green
    Y = "\033[33m"      # yellow
    B = "\033[36m"      # cyan
    BOLD = "\033[1m"
    END = "\033[0m"

def info(msg):  print(f"{C.B}[INFO]{C.END}  {msg}")
def ok(msg):    print(f"{C.G}[ OK ]{C.END}  {msg}")
def warn(msg):  print(f"{C.Y}[WARN]{C.END}  {msg}")
def err(msg):   print(f"{C.R}[FAIL]{C.END}  {msg}")
def title(msg):
    bar = "=" * 60
    print(f"\n{C.BOLD}{bar}\n  {msg}\n{bar}{C.END}")


# ---------------------------------------------------------------------------
# 平台识别
# ---------------------------------------------------------------------------
SYSTEM = platform.system()       # 'Windows' | 'Linux' | 'Darwin'
IS_WIN = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"


# ---------------------------------------------------------------------------
# 通用命令执行封装
# ---------------------------------------------------------------------------
def run(cmd, check=False, capture=False, shell=None):
    """执行命令; 返回 (returncode, stdout)。"""
    if shell is None:
        shell = IS_WIN  # Windows 下用 shell=True 才能找到 .cmd 包装器
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            text=True,
            capture_output=capture,
        )
        return result.returncode, (result.stdout or "")
    except FileNotFoundError:
        return 127, ""
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.stdout or "")


def have(cmd):
    """检查可执行命令是否在 PATH 中。"""
    return shutil.which(cmd) is not None


def refresh_path_from_registry():
    """
    Windows 专用: 从注册表重新读取 PATH 并合并到当前进程,
    用于刚通过 winget 装完工具后立即识别新命令 (否则需要重开终端)。
    """
    if not IS_WIN:
        return
    try:
        import winreg  # 标准库, 仅 Windows 可用
        paths = []
        # 系统级
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as k:
                paths.append(winreg.QueryValueEx(k, "Path")[0])
        except OSError:
            pass
        # 用户级
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                paths.append(winreg.QueryValueEx(k, "Path")[0])
        except OSError:
            pass
        if paths:
            os.environ["PATH"] = ";".join(p for p in paths if p) + ";" + os.environ.get("PATH", "")
    except Exception:
        pass  # 拿不到就算了, 不影响主流程


# Windows winget 自动安装的依赖映射: 命令名 -> (winget Id, 友好名)
WINGET_PACKAGES = {
    "git":  ("Git.Git",           "Git"),
    "node": ("OpenJS.NodeJS.LTS", "Node.js LTS"),
}


def winget_install(cmd_name):
    """
    用 winget 静默安装某个依赖, 装完后刷新 PATH 并重新探测。
    返回 True/False 表示是否成功。
    """
    if not IS_WIN or not have("winget"):
        return False
    pkg = WINGET_PACKAGES.get(cmd_name)
    if not pkg:
        return False
    winget_id, display = pkg

    info(f"正在用 winget 自动安装 {display} ({winget_id}) ...")
    info("  (首次使用 winget 可能弹窗要求同意条款, 选 Y 即可)")
    code, _ = run(
        f'winget install --id {winget_id} --exact --silent '
        f'--accept-package-agreements --accept-source-agreements --scope user',
        shell=True,
    )
    refresh_path_from_registry()
    if have(cmd_name):
        ok(f"{display} 安装成功")
        return True
    warn(f"{display} 安装命令已执行 (winget exit={code}), 但当前会话仍找不到命令")
    warn("请关闭并重新打开终端后再跑一次本脚本")
    return False


# ---------------------------------------------------------------------------
# 国内网络优化: npm 镜像探测与切换
# ---------------------------------------------------------------------------
NPM_OFFICIAL_REGISTRY = "https://registry.npmjs.org/"
NPM_CN_MIRROR         = "https://registry.npmmirror.com/"

def is_npmjs_slow(timeout=4.0):
    """探测 npmjs.org 是否慢/不可达。返回 True 表示建议切镜像。"""
    url = "https://registry.npmjs.org/-/ping"
    info(f"正在探测 {url} (timeout={timeout}s) ...")
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "claude-code-setup"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(64)  # 只读一点点, 避免下载大数据
        cost = time.time() - start
        if cost > 3.0:
            warn(f"npmjs.org 响应较慢 ({cost:.1f}s), 建议使用国内镜像")
            return True
        ok(f"npmjs.org 响应正常 ({cost:.1f}s)")
        return False
    except Exception as e:
        cost = time.time() - start
        warn(f"无法访问 npmjs.org ({cost:.1f}s): {type(e).__name__}")
        return True


def get_npm_registry():
    """读取当前 npm registry 设置。"""
    code, out = run(["npm", "config", "get", "registry"], capture=True)
    return out.strip() if code == 0 else ""


def set_npm_registry(url):
    """切换 npm registry。"""
    code, _ = run(["npm", "config", "set", "registry", url], capture=True)
    return code == 0


def maybe_switch_to_cn_mirror():
    """
    检测网络, 如果慢则询问用户是否切换到国内镜像。
    返回 (是否切换了, 原 registry) 元组, 用于稍后还原。
    """
    title("Step 1.5 / 5  网络环境探测 (npm 镜像)")

    original = get_npm_registry()
    info(f"当前 npm registry: {original}")

    # 已经是国内镜像, 不用动
    if "npmmirror" in original or "taobao" in original or "cnpmjs" in original:
        ok("已使用国内镜像, 跳过探测")
        return False, original

    if not is_npmjs_slow():
        return False, original

    print()
    print(f"{C.Y}检测到访问 npmjs.org 较慢, 推荐切换到阿里云镜像 (registry.npmmirror.com){C.END}")
    print(f"{C.Y}该镜像与官方源完全同步, 安装完成后脚本会自动还原.{C.END}")
    ans = input(f"是否切换? [Y/n]: ").strip().lower()
    if ans == "n":
        warn("用户拒绝切换, 继续使用原 registry (可能会很慢或失败)")
        return False, original

    if set_npm_registry(NPM_CN_MIRROR):
        ok(f"已临时切换到 {NPM_CN_MIRROR}")
        return True, original
    else:
        err("切换失败, 继续使用原 registry")
        return False, original


def restore_npm_registry(original):
    """还原 npm registry 到原值, 不污染用户系统。"""
    if set_npm_registry(original or NPM_OFFICIAL_REGISTRY):
        ok(f"已还原 npm registry: {original or NPM_OFFICIAL_REGISTRY}")
    else:
        warn(f"还原 npm registry 失败, 请手动执行: npm config set registry {original or NPM_OFFICIAL_REGISTRY}")


# ---------------------------------------------------------------------------
# Step 1: 依赖检查
# ---------------------------------------------------------------------------
def check_dependencies():
    title("Step 1 / 5  检查前置依赖")

    # Windows 上若 winget 可用, 缺啥就先静默装啥, 一次到位
    win_auto = IS_WIN and have("winget")
    if win_auto:
        info("检测到 winget, 缺失依赖将自动安装 (无需手动下载)")

    missing = []

    # Git
    if not have("git") and win_auto:
        winget_install("git")
    if have("git"):
        _, out = run(["git", "--version"], capture=True)
        ok(f"Git 已安装: {out.strip()}")
    else:
        err("未检测到 Git")
        missing.append("git")

    # Node.js
    if not have("node") and win_auto:
        winget_install("node")
    if have("node"):
        _, out = run(["node", "-v"], capture=True)
        ver = out.strip().lstrip("v")
        major = int(ver.split(".")[0]) if ver else 0
        if major >= 18:
            ok(f"Node.js 已安装: v{ver}")
        else:
            err(f"Node.js 版本过低 (v{ver}),需要 >= 18")
            missing.append("node>=18")
    else:
        err("未检测到 Node.js")
        missing.append("node")

    # npm (随 Node.js 一起来, 一般不会单独缺)
    if have("npm"):
        _, out = run(["npm", "-v"], capture=True)
        ok(f"npm 已安装: v{out.strip()}")
    else:
        err("未检测到 npm")
        missing.append("npm")

    if missing:
        print()
        err("以下依赖缺失或不满足: " + ", ".join(missing))
        print()
        if IS_WIN:
            if have("winget"):
                print("  自动安装失败, 请手动执行 (任选一行):")
                print("    winget install --id Git.Git -e")
                print("    winget install --id OpenJS.NodeJS.LTS -e")
                print("  装完后【关闭并重新打开】终端, 再跑本脚本。")
            else:
                print("  • Git:     https://git-scm.com/download/win")
                print("  • Node.js: https://nodejs.org/  (选 LTS 版本即可)")
        elif IS_MAC:
            print("  • 推荐用 Homebrew: brew install git node")
        else:
            print("  • Debian/Ubuntu: sudo apt install -y git nodejs npm")
            print("  • 若仓库版 Node 过旧, 推荐用 nvm: https://github.com/nvm-sh/nvm")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Step 2: 安装 Claude Code
# ---------------------------------------------------------------------------
def diagnose_npm_failure(stderr_text):
    """
    分析 npm install 的 stderr, 给出针对性解决方案。
    返回错误类型: 'permission' | 'network' | 'unknown'
    """
    lower = (stderr_text or "").lower()

    # 1. 权限问题 (EACCES, EPERM, permission denied)
    perm_keywords = ["eacces", "eperm", "permission denied", "operation not permitted"]
    if any(k in lower for k in perm_keywords):
        print()
        err("🔍 诊断: npm 全局目录权限不足 (EACCES/EPERM)")
        print()
        print(f"{C.Y}原因{C.END}: 默认 npm 全局目录 (如 /usr/lib/node_modules) 需要 root 权限,")
        print(f"      普通用户无法写入。这是 Linux 上最常见的 npm 坑。")
        print()
        print(f"{C.G}{C.BOLD}推荐解决方案 (二选一, 不要用 sudo!){C.END}")
        print()
        print(f"  {C.BOLD}方案 A: 把 npm 全局目录改到家目录 (最快, 一次配置){C.END}")
        print( "    mkdir -p ~/.npm-global")
        print( "    npm config set prefix ~/.npm-global")
        print( "    echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc")
        print( "    source ~/.bashrc")
        print( "    # 然后重新跑本脚本即可")
        print()
        print(f"  {C.BOLD}方案 B: 用 nvm 管理 Node (一劳永逸, 推荐长期方案){C.END}")
        print( "    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash")
        print( "    source ~/.bashrc")
        print( "    nvm install --lts && nvm use --lts")
        print( "    # 然后重新跑本脚本即可")
        print()
        print(f"{C.R}❌ 不要用 sudo 跑本脚本{C.END} —— 会把环境变量写到 root 的 ~/.bashrc, 你的普通用户用不到。")
        return "permission"

    # 2. 网络问题
    net_keywords = ["etimedout", "econnrefused", "network", "fetch failed",
                    "tunneling socket", "getaddrinfo", "enotfound"]
    if any(k in lower for k in net_keywords):
        print()
        err("🔍 诊断: 网络访问 npm 仓库失败")
        print()
        print(f"{C.G}{C.BOLD}解决方案:{C.END}")
        print( "  1. 切换到国内镜像 (安装完后建议自己再切回去):")
        print( "       npm config set registry https://registry.npmmirror.com")
        print( "       # 重新跑本脚本")
        print()
        print( "  2. 或检查代理设置 (有梯子的话):")
        print( "       npm config set proxy http://127.0.0.1:7890")
        print( "       npm config set https-proxy http://127.0.0.1:7890")
        return "network"

    # 3. 其他未知错误
    print()
    err("🔍 诊断: 未识别的 npm 错误, 请把上面的完整报错信息提交 Issue:")
    print(f"   {C.B}https://github.com/kiki0-zz/claude-code-deepseek-setup/issues{C.END}")
    return "unknown"


def install_claude_code():
    title("Step 2 / 5  安装 Claude Code")

    if have("claude"):
        _, out = run(["claude", "--version"], capture=True)
        ok(f"Claude Code 已安装: {out.strip()}")
        ans = input(f"{C.Y}是否重新安装/升级到最新版? [y/N]: {C.END}").strip().lower()
        if ans != "y":
            return

    info("正在执行: npm install -g @anthropic-ai/claude-code")
    # 用 capture=True 捕获 stderr 用于诊断, 同时实时打印给用户看
    try:
        result = subprocess.run(
            "npm install -g @anthropic-ai/claude-code",
            shell=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        output = result.stdout or ""
        # 实时输出, 让用户看到 npm 进度
        print(output)
        code = result.returncode
    except Exception as e:
        err(f"执行 npm 命令时异常: {e}")
        sys.exit(1)

    if code != 0:
        err(f"npm 全局安装失败 (exit code {code})")
        diagnose_npm_failure(output)
        sys.exit(1)

    if have("claude"):
        _, out = run(["claude", "--version"], capture=True)
        ok(f"Claude Code 安装完成: {out.strip()}")
    else:
        warn("已执行安装, 但当前 PATH 暂未识别到 claude 命令。")
        warn("可能原因: npm 全局 bin 目录不在 PATH 中。")
        warn("请运行 'npm config get prefix' 查看 npm 全局目录,")
        warn("把其中的 bin 子目录加到 PATH 后重开终端即可。")


# ---------------------------------------------------------------------------
# Step 3: 交互输入 API Key + 选择模型
# ---------------------------------------------------------------------------
# DeepSeek V4 系列 (2026-04 起为主推模型, 旧的 V3/R1 已下线)
# 如官方又推出更新模型, 可在「自定义」中输入名称。
MODEL_OPTIONS = [
    ("deepseek-v4-pro",   "DeepSeek-V4 Pro    旗舰模型, 复杂编程任务 (主模型推荐)"),
    ("deepseek-v4-flash", "DeepSeek-V4 Flash  轻量快速, 便宜 (小快模型推荐)"),
]

def choose_model(role):
    """role 仅用于提示文本: '主模型' 或 '小快模型'。"""
    print(f"\n{C.BOLD}请选择 {role}:{C.END}")
    for i, (name, desc) in enumerate(MODEL_OPTIONS, 1):
        print(f"  {i}. {C.G}{name:22}{C.END}  {desc}")
    print(f"  {len(MODEL_OPTIONS) + 1}. 自定义输入 (填入官方文档中的最新模型名)")

    default_idx = 1  # 默认 deepseek-chat
    while True:
        raw = input(f"输入序号 [默认 {default_idx}]: ").strip()
        if raw == "":
            return MODEL_OPTIONS[default_idx - 1][0]
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(MODEL_OPTIONS):
                return MODEL_OPTIONS[idx - 1][0]
            if idx == len(MODEL_OPTIONS) + 1:
                custom = input("请输入自定义模型名: ").strip()
                if custom:
                    return custom
        warn("输入无效,请重试。")


def collect_config():
    title("Step 3 / 5  配置 DeepSeek API")

    # API Key (隐藏输入)
    print("请粘贴你的 DeepSeek API Key (输入时不会显示, 粘贴后直接回车):")
    while True:
        key = getpass("API Key: ").strip()
        if not key:
            warn("Key 不能为空。")
            continue
        if not key.startswith("sk-"):
            warn("DeepSeek Key 通常以 'sk-' 开头, 请确认是否正确。")
            again = input("仍要使用此 Key? [y/N]: ").strip().lower()
            if again != "y":
                continue
        break

    main_model  = choose_model("主模型 (ANTHROPIC_MODEL)")
    small_model = choose_model("小快模型 (ANTHROPIC_SMALL_FAST_MODEL)")

    config = {
        "ANTHROPIC_BASE_URL":            "https://api.deepseek.com/anthropic",
        "ANTHROPIC_AUTH_TOKEN":          key,
        "ANTHROPIC_MODEL":               main_model,
        "ANTHROPIC_SMALL_FAST_MODEL":    small_model,
        # 可选: 关闭遥测, 避免误报
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_TELEMETRY":             "1",
        # 跳过首次启动引导界面
        "CLAUDE_CODE_SKIP_ONBOARDING":   "1",
    }

    print(f"\n{C.BOLD}即将写入以下环境变量:{C.END}")
    for k, v in config.items():
        show = v if k != "ANTHROPIC_AUTH_TOKEN" else (v[:6] + "***" + v[-4:])
        print(f"  {k:42} = {show}")

    confirm = input(f"\n{C.Y}确认写入? [Y/n]: {C.END}").strip().lower()
    if confirm == "n":
        warn("已取消。")
        sys.exit(0)
    return config


# ---------------------------------------------------------------------------
# Step 4: 写入环境变量
# ---------------------------------------------------------------------------
def apply_env_windows(config):
    """Windows: 用 setx 写入用户级永久环境变量。"""
    fail = []
    for k, v in config.items():
        # setx 单值上限 1024 字符,Key 远小于此,放心
        code, _ = run(f'setx {k} "{v}"', capture=True)
        if code == 0:
            ok(f"已写入 {k}")
        else:
            err(f"写入失败 {k}")
            fail.append(k)
    if fail:
        sys.exit(1)
    print()
    warn("Windows 注意: setx 写入的变量仅对【新打开】的终端生效。")
    warn("请关闭当前窗口后, 重新开一个 CMD/PowerShell 再运行 claude。")


def apply_env_unix(config):
    """Linux/macOS: 写入对应 shell 的 rc 文件。"""
    home = Path.home()
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell or IS_MAC:
        rc = home / ".zshrc"
    else:
        rc = home / ".bashrc"

    marker_begin = "# >>> claude-code (deepseek) >>>"
    marker_end   = "# <<< claude-code (deepseek) <<<"

    # 读取现有内容并剔除旧块
    content = rc.read_text(encoding="utf-8") if rc.exists() else ""
    if marker_begin in content and marker_end in content:
        before = content.split(marker_begin)[0].rstrip()
        after  = content.split(marker_end)[1].lstrip()
        content = (before + "\n" + after).rstrip() + "\n"

    # 拼接新块
    block = [marker_begin]
    for k, v in config.items():
        # 单引号防止特殊字符被 shell 解析
        block.append(f"export {k}='{v}'")
        ok(f"已配置 {k}")
    block.append(marker_end)

    new_content = (content.rstrip() + "\n\n" + "\n".join(block) + "\n").lstrip("\n")
    rc.write_text(new_content, encoding="utf-8")
    ok(f"环境变量已写入 {rc}")
    print()
    warn(f"请执行  source {rc}  或重开终端后, 再运行 claude。")


def apply_env(config):
    title("Step 4 / 5  写入环境变量")
    if IS_WIN:
        apply_env_windows(config)
    else:
        apply_env_unix(config)

    # 同时给当前 Python 进程注入,方便接下来跑 claude doctor
    for k, v in config.items():
        os.environ[k] = v


# ---------------------------------------------------------------------------
# Step 5: 验证
# ---------------------------------------------------------------------------
def verify():
    title("Step 5 / 5  运行 claude doctor 进行环境诊断")
    if not have("claude"):
        warn("当前 shell 未识别 claude 命令, 跳过诊断。请重开终端后手动运行: claude doctor")
        return
    info("执行: claude doctor")
    print("-" * 60)
    run("claude doctor")
    print("-" * 60)
    ok("诊断完成。")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Windows 10+ 启用 ANSI 颜色
    if IS_WIN:
        os.system("")

    print(f"{C.BOLD}\n╔══════════════════════════════════════════════════════════╗")
    print(  f"║   Claude Code  +  DeepSeek API  一键配置脚本             ║")
    print(  f"║   平台: {SYSTEM:<48} ║")
    print(  f"╚══════════════════════════════════════════════════════════╝{C.END}")

    try:
        check_dependencies()

        # Step 1.5: 国内网络优化 (探测 + 询问是否切镜像)
        switched, original_registry = maybe_switch_to_cn_mirror()
        try:
            install_claude_code()
        finally:
            # 不管装成功与否, 都要把 registry 还原, 避免污染用户系统
            if switched:
                restore_npm_registry(original_registry)

        cfg = collect_config()
        apply_env(cfg)
        verify()

        title("✅ 全部完成")
        print("下一步:")
        if IS_WIN:
            print("  1. 关闭当前终端, 重新打开一个 CMD 或 PowerShell")
            print("  2. 执行: claude")
        else:
            print("  1. 执行: source ~/.bashrc   (或 ~/.zshrc)")
            print("  2. 执行: claude")
        print("\n进入会话后输入 /status 可查看当前模型与端点是否生效。\n")
    except KeyboardInterrupt:
        print()
        warn("用户中断, 已退出。")
        sys.exit(130)


if __name__ == "__main__":
    main()