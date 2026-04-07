# Secrets Setup — Canvas Learning System

> **事件背景**：2026-04-06 发现 Google Gemini API key 明文 commit 进 public GitHub 仓库约 10 天，被 Google Secret Scanner 检测并自动吊销。本文档定义此后的 **key 零经手** 存储方案。

## 设计原则

1. **key 永远不进 git** — `.env`、`.mcp.json` 等配置文件**不持有 key 明文**
2. **key 永远不进对话** — Claude Code、Slack、Email、截图等传输媒介永远不看到 key
3. **key 永远不进 shell history** — 用 `read -s` 或 `pbpaste` 读取，不在 `~/.zsh_history` 里留痕
4. **key 只存在一处** — macOS Keychain（系统级加密存储）
5. **子进程继承父 shell env** — Claude Code 从 zsh 启动，MCP server 是 Claude Code 的子进程，所有 export 的环境变量自动逐层继承

## 一次性设置（你自己在终端执行）

### Step 1 — 去 Google AI Studio 创建新 key

访问 https://aistudio.google.com/apikey，点击 **Create API Key**。

**⚠️ 不要把新 key 贴到任何聊天窗口、commit message、README、截图、paste site**。下一步直接从这个页面复制到 Keychain。

### Step 2 — 存进 macOS Keychain（推荐）

在终端里执行：

```bash
# 1. 静默读取 key 到临时变量（不回显到终端，不留 history）
read -rs -p "Paste new Google API key then Enter: " NEW_KEY

# 2. 写入 Keychain（-U 允许更新已有 item）
security add-generic-password \
  -a "$USER" \
  -s canvas-google-api-key \
  -U \
  -w "$NEW_KEY"

# 3. 立即清空变量 + 清屏（防止 scrollback 残留）
unset NEW_KEY
clear
```

**验证写入成功**（这只显示 key 的前 10 个字符做 sanity check）：

```bash
security find-generic-password -a "$USER" -s canvas-google-api-key -w | head -c 10
# 应该看到 "AIza" 开头的前缀
```

### Step 3 — 在 `~/.zshrc` 末尾追加加载 snippet

打开你的 shell 配置：

```bash
open -e ~/.zshrc  # 或用你喜欢的编辑器
```

粘贴以下 snippet 到文件末尾：

```bash
# ─── Canvas Learning System — MCP secrets from Keychain ───
# Loaded once at shell startup; Claude Code and its MCP server
# child processes inherit these env vars via normal process inheritance.
# See docs/secrets-setup.md for background and key rotation.

if [ "$(uname -s)" = "Darwin" ]; then
  # Gemini key for graphiti-canvas MCP server + backend Phase 2
  if _canvas_google_key=$(security find-generic-password \
       -a "$USER" -s canvas-google-api-key -w 2>/dev/null); then
    export GOOGLE_API_KEY="$_canvas_google_key"
    export AI_API_KEY="$_canvas_google_key"
    unset _canvas_google_key
  fi

  # Context7 API key (optional — only if you use context7 MCP)
  if _canvas_context7_key=$(security find-generic-password \
       -a "$USER" -s canvas-context7-api-key -w 2>/dev/null); then
    export CONTEXT7_API_KEY="$_canvas_context7_key"
    unset _canvas_context7_key
  fi
fi
```

**安全要点**：
- `2>/dev/null` 吞掉"key not found"错误，让没存 key 的 shell 不会报警
- `_canvas_*_key` 临时变量在 `export` 后立即 `unset`，不在 shell 命名空间长期存在
- **整个 snippet 不含任何 key 的明文** — 它只描述"怎么从 Keychain 读"

### Step 4 — 重启 shell 或 `source ~/.zshrc`

```bash
source ~/.zshrc
```

### Step 5 — 验证环境变量已加载

```bash
# 只看前缀，不泄漏完整 key
printenv GOOGLE_API_KEY | head -c 10
printenv AI_API_KEY | head -c 10
# 两个都应该显示 "AIza" 开头
```

### Step 6 — 重启 Claude Code 并验证 MCP

**必须从刚 source 过 .zshrc 的 terminal 里启动 Claude Code**（因为子进程继承父 shell 的环境变量）。启动后：

```
/mcp
```

找到 `graphiti-canvas`，确认状态为 "connected"。

然后在对话里触发一次搜索：

> 搜索 Graphiti 里的 canvas-dev group 最近的决策

如果返回结果而不是 403，说明新 key 生效。

## Context7 的 key 也同步处理

Context7 key 没在 git 历史里出现，但仍然应该走相同流程（预防 + 对称）：

```bash
read -rs -p "Paste Context7 API key then Enter: " NEW_KEY
security add-generic-password -a "$USER" -s canvas-context7-api-key -U -w "$NEW_KEY"
unset NEW_KEY
clear
```

Shell snippet（Step 3）已经包含了它的加载逻辑。

## 日常使用

设置完一次后，所有 terminal 启动时自动从 Keychain 读 key 到环境变量。Claude Code 和所有子进程无感继承。你不需要做任何事情。

## Key rotation（每 6-12 个月建议做一次）

```bash
# 1. 去 Google AI Studio 生成新 key（旧的可以吊销也可以并存）
# 2. 在 Keychain 里更新
read -rs -p "Paste rotated Google API key: " NEW_KEY
security add-generic-password -a "$USER" -s canvas-google-api-key -U -w "$NEW_KEY"
unset NEW_KEY
clear
# 3. source ~/.zshrc 或重启所有 terminal + Claude Code
```

## 删除 Keychain 里的 key（例如账号停用时）

```bash
security delete-generic-password -a "$USER" -s canvas-google-api-key
security delete-generic-password -a "$USER" -s canvas-context7-api-key
```

## 为什么不用其他方案

| 方案 | 为什么不用 |
|---|---|
| `.env` 文件明文 | 一旦被 `git add .` 或 pattern match 失误就泄漏（这次就是这么发生的） |
| `.mcp.json` 的 `env` 字段 | 仍然是明文文件，只是换个名字 |
| 1Password CLI (`op`) | 需要 1Password 订阅，且每次 shell 启动都要解锁 vault |
| Bitwarden CLI (`bw`) | 同 1Password，且 session timeout 管理麻烦 |
| **macOS Keychain** ✅ | 系统级加密、无订阅、解锁跟随系统登录、`security` 命令原生可用 |

## 如果某天需要在非 macOS 机器（如 Linux 容器）开发

非 Darwin 的 shell snippet 会跳过 Keychain 读取（`if [ Darwin ]` 保护），此时建议：
- 用 `pass`（GPG-based password store）
- 或用 `gopass`
- 或在 shell 启动时 `read -s` 交互输入（每次都输）

**绝不**用明文 `.env` 或 `.mcp.json`。

## 历史 key 泄漏事件的完整处理请见

- 工作区清理：已完成（2026-04-06，本次 commit 前）
- Git 历史重写：待 user 授权（`[等授权] Git 历史重写清理` task）

---

## INTERNAL_API_KEY — 设备级内部 API key（FR-KG-04 Phase 2，2026-04-07）

`/api/v1/sync/batch` 等敏感后端写入端点要求 `X-CLS-Internal-Key` header（详见
`backend/app/security.py` 的 `require_internal_api_key` fail-closed 矩阵）。

### 后端配置

在 `backend/.env` 添加：

```env
# 设备级内部 API key — 必须与前端 VITE_INTERNAL_API_KEY 匹配
INTERNAL_API_KEY=<random-string-here>
```

生成随机 key 推荐：

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### 前端配置

在 `frontend/.env` 添加同一个值：

```env
VITE_INTERNAL_API_KEY=<same-random-string-as-backend>
```

### Fail-closed 行为

| `DEBUG` | `INTERNAL_API_KEY` | 行为 |
|---------|--------------------|------|
| `True`  | empty              | 警告放行（开发便利） |
| `True`  | configured         | 严格校验 |
| `False` | empty              | **503 fail-closed**（防生产裸奔） |
| `False` | configured         | 严格校验 |

main.tsx 在 `VITE_INTERNAL_API_KEY` 缺失时打印 console 警告。

### 与 Google API key 的区别

INTERNAL_API_KEY 是**设备生成**的随机字符串，**不是云服务 key**：
- 不需要去任何后台创建
- 不需要 Keychain 存储（loopback 信任边界，安全等级低于云 key）
- 可以放在 `.env` 文件，但仍**不要 commit 到 git**（已在 `.gitignore`）
- 多设备间复制粘贴或重新生成都没成本
- Pre-commit secret-scan：待新建（下一步 task）
