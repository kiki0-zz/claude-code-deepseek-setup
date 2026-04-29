# Claude Code + DeepSeek 一键配置脚本

> 跨平台 (Windows / Linux / macOS) 的 Python 脚本,一键完成 Claude Code 安装 + DeepSeek API 接入,告别手动配置环境变量。

[![CI](https://github.com/kiki0-zz/claude-code-deepseek-setup/actions/workflows/ci.yml/badge.svg)](https://github.com/kiki0-zz/claude-code-deepseek-setup/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

---

## ✨ 特性

- 🔍 **自动检查依赖**:Git、Node.js (≥18)、npm 缺啥提示啥
- 📦 **自动安装** `@anthropic-ai/claude-code`(已装则可选升级)
- 🔐 **隐藏输入 API Key**:防止屏幕/录屏泄漏
- 📋 **菜单选择模型**:主模型 / 小快模型分别配置,支持自定义
- 💾 **永久写入环境变量**
  - Windows → `setx`(用户级注册表)
  - Linux/macOS → `~/.bashrc` 或 `~/.zshrc`(带标记块,可重复执行覆盖)
- 🩺 **自动运行 `claude doctor`** 验证安装

---

## 🚀 快速使用

### 方式 A:一行命令(推荐)

> 自动 clone 仓库 + 运行脚本,适合大多数人。

**Linux / macOS**
```bash
git clone https://github.com/kiki0-zz/claude-code-deepseek-setup.git && cd claude-code-deepseek-setup && python3 setup_claude_code.py
```

**Windows (CMD)**
```cmd
git clone https://github.com/kiki0-zz/claude-code-deepseek-setup.git && cd claude-code-deepseek-setup && python setup_claude_code.py
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/kiki0-zz/claude-code-deepseek-setup.git; cd claude-code-deepseek-setup; python setup_claude_code.py
```

---

### 方式 B:只下载单个脚本(不想要整个仓库)

**Linux / macOS**
```bash
curl -O https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/setup_claude_code.py
python3 setup_claude_code.py
```

**Windows (PowerShell)**
```powershell
iwr https://raw.githubusercontent.com/kiki0-zz/claude-code-deepseek-setup/main/setup_claude_code.py -OutFile setup_claude_code.py
python setup_claude_code.py
```

---

### 接下来按提示操作
1. 粘贴 DeepSeek API Key(去 https://platform.deepseek.com/ 注册获取,**输入时不显示**,正常的)
2. 菜单选择主模型 / 小快模型(推荐 `deepseek-v4-pro` + `deepseek-v4-flash`)
3. 等待 `claude doctor` 自动跑完

### 启动 Claude Code
**关闭并重新打开终端**(让环境变量生效),然后:
```bash
claude
```

进入会话后输入 `/status` 可查看当前模型与端点是否生效 ✅

---

### 🔄 已经 clone 过,想拉取最新版

```bash
cd claude-code-deepseek-setup
git pull
python3 setup_claude_code.py   # Windows 用 python
```

---

## 📋 脚本会写入的环境变量

| 变量名 | 作用 |
|--------|------|
| `ANTHROPIC_BASE_URL` | DeepSeek 的 Anthropic 兼容端点 |
| `ANTHROPIC_AUTH_TOKEN` | 你的 DeepSeek API Key |
| `ANTHROPIC_MODEL` | 主模型(干重活) |
| `ANTHROPIC_SMALL_FAST_MODEL` | 小快模型(干杂活,如生成会话标题) |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | 关闭非必要遥测请求 |
| `DISABLE_TELEMETRY` | 关闭遥测 |
| `CLAUDE_CODE_SKIP_ONBOARDING` | 跳过首次启动的登录引导界面 |

---

## 🤖 推荐模型搭配

| 角色 | 推荐 | 说明 |
|------|------|------|
| 主模型 | `deepseek-v4-pro` | 写代码、规划任务、调用工具 |
| 小快模型 | `deepseek-v4-flash` | 起标题、压缩历史等轻量工作 |

如果 DeepSeek 推出更新模型,在脚本菜单中选「自定义输入」即可。

---

## 🛠️ 前置要求

- **Python 3.7+**(脚本本身仅依赖标准库,无需 pip install)
- **Git**:[Windows 下载](https://git-scm.com/download/win) / `brew install git` / `apt install git`
- **Node.js ≥ 18**:[官网下载](https://nodejs.org/) 或用 [nvm](https://github.com/nvm-sh/nvm)
- **DeepSeek API Key**:[platform.deepseek.com](https://platform.deepseek.com/)

---

## ❓ 常见问题

### Q1: setx 设置完了 echo 还是空的?
A: `setx` 写入的是**永久变量**,但**当前终端窗口看不到**。必须**关掉重开**新终端才会生效。

### Q2: Linux/macOS 跑完没效果?
A: 需要先 `source ~/.bashrc`(或 `~/.zshrc`),或重开终端。

### Q3: npm install 失败 (Linux/macOS)?
A: 可能是 npm 全局目录权限问题。推荐用 [nvm](https://github.com/nvm-sh/nvm) 把 Node 装到用户目录下,避免 sudo。

### Q4: 想切换回官方 Claude API?
A: 删掉这几个环境变量即可:
- Windows:`setx ANTHROPIC_BASE_URL ""` 然后重开终端
- Linux/macOS:删掉 `~/.bashrc` 中带 `claude-code (deepseek)` 标记的整段

### Q5: 想用其他第三方 Anthropic 兼容端点?
A: 修改脚本中 `apply_env` 之前的 `ANTHROPIC_BASE_URL` 默认值即可,或者加成可选参数。

---

## 🔒 安全说明

- ✅ 脚本**不会**把 API Key 上传到任何地方,只本地写入环境变量
- ✅ Key 输入采用 `getpass` 隐藏显示
- ⚠️ 请勿把你本地配置过的 `~/.bashrc` 提交到 GitHub(已通过 `.gitignore` 保护常见敏感文件)

---

## 📄 License

[MIT](./LICENSE)

---

## 🙋 贡献

欢迎 Issue 和 PR!如果你的修改让脚本支持了更多平台/模型/端点,记得在 README 里加一行说明 🙏
