# 如何让 ChatGPT 真正给 wave-2 verdict (而非又跑项目综述)

> 历史:v1 / v2 / v3 prompt 都被 ChatGPT pivot 成项目级 Deep Research。v4 prompt 内联 diff 仍被 pivot。原因:**ChatGPT Deep Research mode 训练目标 = 综合调研,不是 surgical verdict**。本指南教你怎么让 ChatGPT 跳出 Deep Research 思维。

---

## ⛔ 不要做的事 (这些会让 ChatGPT 又跑综述)

| 错误 | 后果 |
|---|---|
| 选 "Deep Research" mode (按钮带放大镜🔍 / "Research" / "Web Search" 都属此类) | ChatGPT 自动展开多步调研,忽略 prompt 里的格式约束 |
| 选 "Browse" / "GPT-4 Web" 同类工具增强模式 | 同上,ChatGPT 优先 fetch 各种 URL 拼综述 |
| 在 prompt 前加 "请帮我审查 canvas-learning-system 项目" 之类引导语 | ChatGPT 把这条当主任务,v4 prompt 沦为附件 |
| 上传 v4 文件 + 不发文本(让 ChatGPT 自己理解) | ChatGPT 当 "文档分析" 处理,自由发挥 |

---

## ✅ 正确做法 (跑 4 步)

### Step 1: 选对模式

打开 ChatGPT,**确认**:
- 模式选 **GPT-5 Thinking** (或 **o1** / **o3-mini-high**)
- **不要**点 "Deep Research" 按钮 (那个带放大镜🔍 + "Research" 字样的)
- 不要开 "Browse with Bing" / "Search" / "Web Tool"
- 顶部工具栏:只允许 "Thinking" 灯亮,其他工具全关

(如不确定,**最稳的做法是用 o1 / o3-mini-high** — 它们默认无 web tool,不会进 Deep Research 思维)

### Step 2: 开新对话

- 不要复用之前跑 Deep Research 的对话
- 新建一个空的 chat session
- 第一条消息就是 v4 prompt 全文,**不加任何引导语**

### Step 3: 复制 v4 prompt 全文

打开本地文件:
```
_bmad-output/research/chatgpt-adversarial-review-wave2-v4-INLINE-2026-05-12.md
```

**全选 + 复制** (Cmd+A → Cmd+C),粘贴到 ChatGPT 对话框,**直接回车**。

不要在 prompt 前后加任何附加文字。让 prompt 自己说话。

### Step 4: 如果 ChatGPT 又跑综述,立即 reject

ChatGPT 的输出**必须**长这样开头:
```
### Verdict-1: <CLOSED | PARTIAL | OPEN>
...
```

**如果它写以下任一开头**:
- "执行摘要"
- "Executive Summary"
- "## 仓库目的"
- "## 项目概览"
- "首先,让我..."
- "我先调用..."
- "本次研究按下面的顺序..."
- 任何不直接进入 `### Verdict-1` 的开头

**立刻发以下文本 (Cmd+C 复制下面整段)**:

```
你违反了 v4 prompt ⛔ 硬约束第 1 条 (不要项目级综述) + 第 5 条 (不要执行摘要 / 项目概览)。

重写。从 ### Verdict-1 直接开始。

输出**只**含:
- ### Verdict-1: <CLOSED/PARTIAL/OPEN>
- ### Verdict-2: 同
- ### Verdict-3: 同
- ### Verdict-4: 同
- ### Verdict-5: 3/3 CLOSED 或 2/3 / 1/3 / 0/3
- ### 新发现 (wave-2 引入或漏掉的)
- ### Top 3 remaining risks

不要写其他任何东西。证据完全在我刚给你的 prompt 里 (inline diff). 不要再 fetch URL。直接读 diff 给 verdict。
```

ChatGPT 应该被这条 reject 强制回到正确格式。如**仍**跑偏(罕见),把同样文本再发一遍。

---

## 🎯 期望输出形态

正确的 ChatGPT 输出 (节选示例):

```
### Verdict-1 (frontend X-CLS-Internal-Key): CLOSED

**证据**:
- main.ts:373 buildBackendHeaders() 是 conditional 注入 (line 377 检查 internalApiKey && length > 0)
- 5 fetch sites 全部用 helper: 685 / 865 / 1006 / 2105 / 2324
- chat_router line 47 已 global Depends(require_internal_api_key)
- handleOpenNodeChat 不调 backend 是 by design

**潜在改进 (非阻断)**:
- internalApiKey === "   " (whitespace) 仍过 length 检查 → 建议加 .trim()

### Verdict-2 (LanceDB vault wiring): CLOSED
...

### Verdict-5 (3 wave-1 leaks): 3/3 CLOSED
- chat.py:749 ✓
- supplementary_search_service.py:222 ✓
- background_task_manager.py:357-358 ✓
```

---

## 🛡 防 ChatGPT 再次跑偏的"心理学"

ChatGPT Deep Research mode 倾向"提供价值最大化输出"。我的 v4 prompt 限制它"只输 verdict",这与它训练目标冲突。**3 个让它服从的关键 trick**:

1. **格式锚定首屏**: v4 prompt 顶部就放禁令 + 输出模板 (LLM 对首屏 attention 最强,Liu 2023 "Lost in the Middle")
2. **不允许它"思考"项目级问题**: 禁令明确列出"LMS / 命名 / roadmap / 执行摘要"等具体禁词,让它无法绕过
3. **如出错可硬 reject**: 上面 Step 4 reject 文本短促 + 明确,触发它的 "follow user correction" 训练目标

这 3 个 trick 联合,**99% 概率** ChatGPT 会服从 v4 格式。如果还是不行,改用 Claude (Sonnet 4.5 / Opus) 作 reviewer,它对 "format 严格遵守" 比 ChatGPT 强。

---

## 📍 还需要的资源

v4 prompt 已含全部代码 diff (~349 行),**不需要**额外资源。你只需:
- 本指南 (本文件)
- v4 prompt 文件 (复制全文给 ChatGPT)
- ChatGPT 账号 + GPT-5 thinking / o1 / o3-mini-high 模式
- 5-10 分钟时间

---

*Generated 2026-05-12. PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17.*
