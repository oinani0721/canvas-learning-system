"""
QueryRewriter - LLM-based query rewriting for quality improvement

Uses GPT-3.5-turbo to rewrite queries from different angles when retrieval quality is low.

Story 12.9 AC 9.2: Query rewriter在low质量时触发
- Condition: quality_grade=="low" AND rewrite_count < 2
- LLM: gpt-3.5-turbo
- Prompt: "原始问题未找到高质量结果，请从不同角度重写问题"

Story 12.9 AC 9.4: Rewrite后质量提升
- 测试集: 20个low质量query
- Rewrite后: avg_score提升 ≥ +0.15

✅ Verified from Zero Hallucination Protocol:
- Using documented OpenAI API (gpt-3.5-turbo)
- Prompt engineering based on Story requirements
- Temperature and max_tokens explicitly controlled

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI


class QueryRewriter:
    """
    LLM-based query rewriting for improving retrieval quality

    Uses GPT-3.5-turbo to reformulate queries when initial retrieval
    returns low-quality results.

    Rewriting strategies:
    1. Add clarifying context
    2. Decompose complex queries
    3. Rephrase from different angles
    4. Add domain-specific keywords
    """

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 150,
        api_key: Optional[str] = None
    ):
        """
        Initialize QueryRewriter

        Args:
            model: OpenAI model to use (default: gpt-3.5-turbo)
            temperature: Sampling temperature (0.7 for creative rewrites)
            max_tokens: Max tokens for rewritten query
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Store API key for lazy initialization
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy-initialize OpenAI client"""
        if self._client is None:
            # ✅ Verified from OpenAI Python SDK documentation
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def rewrite_query(
        self,
        original_query: str,
        context: Optional[Dict[str, Any]] = None,
        rewrite_count: int = 0
    ) -> str:
        """
        Rewrite query using LLM

        Story 12.9 AC 9.2: Query rewriter implementation

        Args:
            original_query: Original user query that returned low-quality results
            context: Optional context (canvas_file, weak_concepts, etc.)
            rewrite_count: Current rewrite iteration (0, 1, or 2)

        Returns:
            Rewritten query string
        """
        # Build system prompt based on rewrite iteration
        system_prompt = self._build_system_prompt(rewrite_count, context)

        # Build user prompt with original query
        user_prompt = self._build_user_prompt(original_query, context)

        try:
            # Call OpenAI API
            # ✅ Verified from OpenAI AsyncOpenAI documentation
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                n=1,  # Generate 1 rewrite
            )

            rewritten_query = response.choices[0].message.content.strip()

            # Validate rewritten query is not empty
            if not rewritten_query:
                return self._fallback_rewrite(original_query, rewrite_count)

            return rewritten_query

        except Exception as e:
            # Fallback to rule-based rewrite if LLM fails
            print(f"QueryRewriter LLM call failed: {e}, using fallback")
            return self._fallback_rewrite(original_query, rewrite_count)

    def _build_system_prompt(
        self,
        rewrite_count: int,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build system prompt based on rewrite iteration

        Strategy varies by iteration:
        - Iteration 0 (1st rewrite): Add clarifying context
        - Iteration 1 (2nd rewrite): Decompose or rephrase completely
        """
        base_prompt = """你是一个专业的查询优化助手，专门为Canvas学习系统改写检索查询。

你的任务是将原始查询改写成更有效的形式，以便检索到更相关、更高质量的学习材料。
"""

        if rewrite_count == 0:
            # 1st rewrite: Add clarifying details
            strategy = """
**改写策略 (第1次迭代)**:
1. 添加澄清性上下文 (例如: "在离散数学中，...")
2. 明确查询意图 (概念定义、应用场景、证明方法等)
3. 添加领域关键词

**输出要求**:
- 保持原始查询的核心意图
- 添加2-3个澄清性词语
- 长度: 原查询的1.2-1.5倍
"""
        else:
            # 2nd rewrite: Decompose or completely rephrase
            strategy = """
**改写策略 (第2次迭代)**:
1. 从完全不同的角度重新表述
2. 将复杂查询分解为更具体的子问题
3. 使用同义词和相关术语

**输出要求**:
- 完全改写，但保持核心意图
- 更具体、更聚焦
- 可以是原查询的上位概念或下位概念
"""

        # Add Canvas context if available
        canvas_context = ""
        if context and context.get("canvas_file"):
            canvas_file = context["canvas_file"]
            canvas_context = f"\n**当前学习上下文**: {canvas_file}"

        if context and context.get("weak_concepts"):
            weak_concepts = context["weak_concepts"][:3]  # Top 3 weak concepts
            canvas_context += f"\n**薄弱概念**: {', '.join(weak_concepts)}"

        return base_prompt + strategy + canvas_context

    def _build_user_prompt(
        self,
        original_query: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build user prompt with original query

        Story 12.9 AC 9.2: "原始问题未找到高质量结果，请从不同角度重写问题"
        """
        prompt = f"""原始查询未能找到高质量结果，请改写此查询:

**原始查询**: {original_query}

**改写要求**:
1. 从不同角度重新表述
2. 保持核心查询意图
3. 只输出改写后的查询，不要解释

**改写后的查询**:"""

        return prompt

    def _fallback_rewrite(
        self,
        original_query: str,
        rewrite_count: int
    ) -> str:
        """
        Fallback rule-based rewrite if LLM fails

        Simple strategies:
        - Iteration 0: Add "请详细解释: "
        - Iteration 1: Add "...的核心概念和应用场景"
        """
        if rewrite_count == 0:
            return f"请详细解释: {original_query}"
        else:
            return f"{original_query}的核心概念和应用场景"

    async def batch_rewrite(
        self,
        queries: list[str],
        context: Optional[Dict[str, Any]] = None
    ) -> list[str]:
        """
        Batch rewrite multiple queries

        Args:
            queries: List of queries to rewrite
            context: Shared context for all queries

        Returns:
            List of rewritten queries
        """
        import asyncio

        tasks = [self.rewrite_query(q, context, 0) for q in queries]
        rewritten = await asyncio.gather(*tasks)

        return rewritten
