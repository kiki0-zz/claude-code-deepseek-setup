# Changelog

本项目所有显著改动都会记录在此文件中。
格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

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
