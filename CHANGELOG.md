# Changelog

本项目所有显著改动都会记录在此文件中。
格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

---

## [1.0.1] - 2026-05-07

🛠 **Windows 一键安装可用性修复**

### 修复 (Fixed)
- **`install.ps1` 在 Windows 上静默失败**:`irm ... | iex` 执行后光标直接回到提示符,无任何输出。根因有二:
  1. `$ErrorActionPreference='Stop'` 把下载阶段的所有异常吞掉
  2. PowerShell 5.1(Win10/11 自带版本)默认禁用 TLS1.2,`Invoke-RestMethod` 直接拿不到 HTTPS 内容
  现已将 `ErrorActionPreference` 改为 `Continue` 并在脚本内层强开 TLS1.2,同时在 README 顶部给出"Bypass + TLS1.2 + irm"三段式命令以绕开 `ExecutionPolicy=Restricted`
- 文件编码改为 **UTF-8 with BOM**,修复 PowerShell 5.1 解析中文字符串报错的问题

### 新增 (Added)
- **Windows 自动安装基础依赖**:`install.ps1` 检测到缺 Python / Git / Node.js 时,通过 `winget`(用户作用域)静默安装,新手无需任何手动配置
  | 依赖 | winget Id |
  |------|-----------|
  | Python 3.12 | `Python.Python.3.12` |
  | Git | `Git.Git` |
  | Node.js LTS(自带 npm) | `OpenJS.NodeJS.LTS` |
- 安装完依赖后**从注册表合并最新 PATH 到当前会话**,无需重开终端
- `setup_claude_code.py` 也补上同样能力(`winget_install()` + `refresh_path_from_registry()`),让直接 `python setup_claude_code.py` 跑的用户同样享受自动装依赖
- README 新增 **Q0 FAQ** 解释"为什么单行 `irm | iex` 没反应",并明确推荐 Win10 1809+ / Win11 用户使用三段式命令

### 改进 (Changed)
- `install.ps1` 下载阶段改为先尝试 GitHub 官方源(10s 超时),失败自动切到 `gh-proxy.com` 镜像(20s 超时),且失败时打印明确诊断建议而非静默退出
- 安装失败时给出可复制的 winget 兜底命令,降低新手排错成本

[1.0.1]: https://github.com/kiki0-zz/claude-code-deepseek-setup/releases/tag/v1.0.1

---

## [1.0.0] - 2026-04-29

🎉 **首个正式发布版本**

### 核心功能
- 跨平台一键安装脚本 `setup_claude_code.py`,支持 Windows / Linux / macOS
- 自动检查前置依赖(Git、Node.js ≥ 18、npm)
- 自动通过 `npm` 全局安装 `@anthropic-ai/claude-code`
- 隐藏输入 DeepSeek API Key(基于 `getpass`)
- 菜单式选择主模型 / 小快模型,内置 `deepseek-v4-pro` 和 `deepseek-v4-flash`,支持自定义输入
- 永久写入环境变量
  - Windows:`setx` 写入用户级注册表
  - Linux/macOS:写入 `~/.bashrc` 或 `~/.zshrc`,带标记块,可重复执行无副作用
- 安装后自动运行 `claude doctor` 进行环境诊断

### 国内用户优化 🇨🇳
- 启动时自动 ping `npmjs.org`,响应慢/失败时询问是否切换到阿里云镜像
- 安装完成后**自动还原** npm registry,不污染用户系统
- README 提供 `gh-proxy.com` clone 加速方案

### 错误诊断
- npm 安装失败时自动识别错误类型(权限 / 网络 / 未知),给出针对性解决方案
- 提示用户**不要用 sudo 跑脚本**(避免环境变量写到 root)

### 工程化
- 跨平台 GitHub Actions CI(Ubuntu / Windows / macOS × Python 3.9 / 3.11 / 3.13)
- 完整 README、CHANGELOG、Issue / PR 模板
- MIT License、`.gitignore`

[1.0.0]: https://github.com/kiki0-zz/claude-code-deepseek-setup/releases/tag/v1.0.0
