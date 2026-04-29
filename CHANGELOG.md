# Changelog

本项目所有显著改动都会记录在此文件中。
格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2026-04-29

🎉 **首个正式发布版本**

### Added
- 跨平台一键安装脚本 `setup_claude_code.py`,支持 Windows / Linux / macOS
- 自动检查前置依赖(Git、Node.js ≥ 18、npm)
- 自动通过 `npm` 全局安装 `@anthropic-ai/claude-code`
- 隐藏输入 DeepSeek API Key(基于 `getpass`)
- 菜单式选择主模型 / 小快模型,内置 `deepseek-v4-pro` 和 `deepseek-v4-flash`,支持自定义输入
- 永久写入环境变量
  - Windows:`setx` 写入用户级注册表
  - Linux/macOS:写入 `~/.bashrc` 或 `~/.zshrc`,带标记块,可重复执行无副作用
- 安装后自动运行 `claude doctor` 进行环境诊断
- 跨平台 GitHub Actions CI(Ubuntu / Windows / macOS × Python 3.9 / 3.11 / 3.13)
- 完整 README 文档,含一行安装命令、FAQ、安全说明
- MIT License、`.gitignore`、Issue / PR 模板

[1.0.0]: https://github.com/kiki0-zz/claude-code-deepseek-setup/releases/tag/v1.0.0
