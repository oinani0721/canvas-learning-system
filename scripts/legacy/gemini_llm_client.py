#!/usr/bin/env python3
"""
Gemini LLM客户端适配器

为Graphiti系统提供Gemini API支持

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import time
from typing import Dict, List, Optional, Any
import httpx
from loguru import logger

class GeminiLLMClient:
    """Gemini API客户端适配器"""

    def __init__(self, config: Dict):
        """
        初始化Gemini客户端

        Args:
            config: 包含API配置的字典
        """
        self.api_key = config["api_config"]["api_key"]
        self.base_url = config["api_config"]["base_url"]
        self.model = config["api_config"].get("model", "gemini-pro")
        self.temperature = config["api_config"].get("temperature", 0.7)
        self.max_tokens = config["api_config"].get("max_tokens", 4096)

        # HTTP客户端配置
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        logger.info(f"Gemini LLM客户端初始化完成，模型: {self.model}")

    async def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        生成文本

        Args:
            prompt: 输入提示
            max_tokens: 最大token数量

        Returns:
            生成的文本
        """
        try:
            # 构建请求数据
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }

            # 发送请求
            response = self.client.post("/chat/completions", json=payload)
            response.raise_for_status()

            # 解析响应
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            logger.info(f"Gemini API调用成功，生成文本长度: {len(content)}")
            return content

        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API HTTP错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise

    async def analyze_concepts(self, text: str) -> Dict:
        """
        分析概念关系

        Args:
            text: 要分析的文本

        Returns:
            分析结果
        """
        prompt = f"""
请分析以下文本中的概念和关系：

文本：{text}

请以JSON格式返回分析结果，包含：
1. concepts: 概念列表，每个概念包含name和description
2. relationships: 关系列表，每个关系包含source_concept, target_concept, relationship_type
3. confidence: 置信度分数 (0-1)

返回格式：
{{
    "concepts": [
        {{"name": "概念名", "description": "概念描述"}}
    ],
    "relationships": [
        {{
            "source_concept": "源概念",
            "target_concept": "目标概念",
            "relationship_type": "关系类型",
            "confidence": 0.9
        }}
    ]
}}
"""

        try:
            result = await self.generate_text(prompt)
            # 尝试解析JSON
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Gemini返回的不是有效JSON，使用备用解析")
            # 备用解析逻辑
            return self._parse_fallback_response(result)

    def _parse_fallback_response(self, response: str) -> Dict:
        """备用响应解析"""
        return {
            "concepts": [{"name": "unknown", "description": response[:100]}],
            "relationships": [],
            "confidence": 0.5
        }

    def close(self):
        """关闭客户端"""
        self.client.close()
        logger.info("Gemini LLM客户端已关闭")


class GeminiEmbeddingClient:
    """Gemini嵌入客户端（如果支持的话）"""

    def __init__(self, config: Dict):
        """
        初始化嵌入客户端

        Args:
            config: 包含嵌入配置的字典
        """
        self.api_key = config["embedding_config"]["api_key"]
        self.base_url = config["embedding_config"]["base_url"]
        self.model = config["embedding_config"]["embedding_model"]

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        logger.info(f"Gemini嵌入客户端初始化完成，模型: {self.model}")

    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        try:
            payload = {
                "model": self.model,
                "input": text
            }

            response = self.client.post("/embeddings", json=payload)
            response.raise_for_status()

            result = response.json()
            return result["data"][0]["embedding"]

        except Exception as e:
            logger.error(f"嵌入向量生成失败: {e}")
            # 返回零向量作为备用
            return [0.0] * 1536

    def close(self):
        """关闭客户端"""
        self.client.close()
        logger.info("Gemini嵌入客户端已关闭")