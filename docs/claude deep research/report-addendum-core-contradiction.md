# 补充章节：为什么 BMAD 和 Superpowers 的返工率降不下来——核心矛盾

> 插入位置：主报告"结论：实施优先级路线图"章节之前。
> 本节记录了实测体感与研究结论的交叉验证。

---

**BMAD 的问题出在执行层。** BMAD 是优秀的规划工具，PRD 质量高、粒度清晰。但它没有执行引擎——它假设 LLM 会老实按 story 实现，实际上 LLM 拿到 story 之后仍然在单一 context 里同时写实现和测试，facade 问题完全没有被解决。规划再好，执行层没有物理隔离，返工率就降不下来。

**Superpowers 的问题出在结构性缺陷。** 实测结果（Workflow C 写出 `@staticmethod _compute_color` 这种 facade）已经证明了这一点。Superpowers 的 Iron Law 是 prompt 约束，不是机械防护。LLM 在同一个 context 里同时看到实现意图和测试任务，它会"合理化"出一条阻力最小的路径——在测试文件里复制生产逻辑，绕过真实 import。这不是用得不对，是架构上就防不住。

**核心矛盾只有一个：**

> 只要测试和实现在同一个 context 里生成，LLM 就有能力、也有倾向写出镜像测试。

BMAD 没解决这个问题，Superpowers 试图用 prompt 压制但结构上失败了。Workflow A 是目前唯一在架构层面切断这个路径的方案——test-writer 根本看不到实现代码，被迫写黑盒测试。问题只是它还没有被大规模验证，以及在 Neo4j/集成层还有退化风险。

**下一步最值得做的事**就是把 Workflow A 的 testcontainers fixture 和 schema 摘要机制装好，然后用 10-15 个真实任务跑一次对照实验，这比继续调 BMAD 或 Superpowers 的 prompt 有价值得多。
