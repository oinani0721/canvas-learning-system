#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Gemini API客户端

包含重试机制、错误处理、速率限制和JSON解析优化

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-26
"""

import asyncio
import json
import time
import re
import random
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import httpx
from loguru import logger


class APIError(Exception):
    """API调用异常"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(APIError):
    """速率限制异常"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests_per_minute: int = 20
    requests_per_hour: int = 200
    burst_limit: int = 5


class EnhancedGeminiClient:
    """增强版Gemini API客户端"""

    def __init__(self,
                 api_key: str,
                 base_url: str = "https://binapi.shop/v1",
                 model: str = "gemini-2.5-flash",
                 retry_config: Optional[RetryConfig] = None,
                 rate_limit_config: Optional[RateLimitConfig] = None):
        """
        初始化增强版Gemini客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 使用的模型名称
            retry_config: 重试配置
            rate_limit_config: 速率限制配置
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

        # 配置重试和速率限制
        self.retry_config = retry_config or RetryConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()

        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

        # 速率限制追踪
        self._request_times = []
        self._rate_limit_lock = asyncio.Lock()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "retry_count": 0,
            "total_response_time": 0.0
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt)
        delay = min(delay, self.retry_config.max_delay)

        if self.retry_config.jitter:
            delay *= (0.5 + random.random() * 0.5)

        return delay

    async def _check_rate_limit(self):
        """检查速率限制"""
        async with self._rate_limit_lock:
            now = time.time()

            # 清理过期的请求记录
            self._request_times = [t for t in self._request_times if now - t < 3600]

            # 检查每分钟限制
            recent_requests = [t for t in self._request_times if now - t < 60]
            if len(recent_requests) >= self.rate_limit_config.requests_per_minute:
                sleep_time = 60 - (now - recent_requests[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit: sleeping {sleep_time:.1f}s for minute limit")
                    await asyncio.sleep(sleep_time)

            # 检查每小时限制
            if len(self._request_times) >= self.rate_limit_config.requests_per_hour:
                sleep_time = 3600 - (now - self._request_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit: sleeping {sleep_time:.1f}s for hour limit")
                    await asyncio.sleep(sleep_time)

            # 检查突发限制
            very_recent_requests = [t for t in self._request_times if now - t < 10]
            if len(very_recent_requests) >= self.rate_limit_config.burst_limit:
                await asyncio.sleep(1.0)

    async def _make_request_with_retry(self,
                                     method: str,
                                     endpoint: str,
                                     **kwargs) -> httpx.Response:
        """带重试机制的API请求"""
        last_exception = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # 检查速率限制
                await self._check_rate_limit()

                # 记录请求时间
                self._request_times.append(time.time())

                # 发送请求
                response = await self.client.request(method, endpoint, **kwargs)

                # 更新统计
                self.stats["total_requests"] += 1

                # 处理速率限制
                if response.status_code == 429:
                    self.stats["rate_limited_requests"] += 1

                    # 尝试解析retry-after头
                    retry_after = None
                    if "retry-after" in response.headers:
                        try:
                            retry_after = int(response.headers["retry-after"])
                        except ValueError:
                            retry_after = 60

                    # 使用 exponential backoff
                    delay = self._calculate_delay(attempt)
                    if retry_after:
                        delay = max(delay, retry_after)

                    logger.warning(f"Rate limited (attempt {attempt + 1}), retrying in {delay:.1f}s")

                    if attempt < self.retry_config.max_retries:
                        self.stats["retry_count"] += 1
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RateLimitError(
                            f"Rate limit exceeded after {self.retry_config.max_retries} retries",
                            retry_after=retry_after
                        )

                # 处理其他错误
                if response.status_code >= 400:
                    error_data = None
                    try:
                        error_data = response.json()
                    except:
                        error_data = {"text": response.text}

                    # 某些错误不需要重试
                    no_retry_codes = {400, 401, 403, 404, 422}
                    if response.status_code in no_retry_codes:
                        raise APIError(
                            f"API error {response.status_code}: {error_data}",
                            status_code=response.status_code,
                            response_data=error_data
                        )

                    # 5xx错误可以重试
                    if attempt < self.retry_config.max_retries:
                        delay = self._calculate_delay(attempt)
                        logger.warning(f"Server error {response.status_code} (attempt {attempt + 1}), retrying in {delay:.1f}s")
                        self.stats["retry_count"] += 1
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise APIError(
                            f"Server error {response.status_code} after {self.retry_config.max_retries} retries",
                            status_code=response.status_code,
                            response_data=error_data
                        )

                # 成功响应
                self.stats["successful_requests"] += 1
                return response

            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Request error (attempt {attempt + 1}): {e}, retrying in {delay:.1f}s")
                    self.stats["retry_count"] += 1
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    raise APIError(f"Request failed after {self.retry_config.max_retries} retries: {e}")

            except Exception as e:
                last_exception = e
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Unexpected error (attempt {attempt + 1}): {e}, retrying in {delay:.1f}s")
                    self.stats["retry_count"] += 1
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    raise APIError(f"Unexpected error after {self.retry_config.max_retries} retries: {e}")

        # 这里不应该到达
        if last_exception:
            raise last_exception
        raise APIError("Request failed for unknown reason")

    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """从响应中提取JSON数据"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试提取markdown代码块中的JSON
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
        ]

        for pattern in json_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1).strip()
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # 如果都失败了，返回原始内容
        return {"raw_content": content}

    async def generate_text(self,
                           prompt: str,
                           max_tokens: Optional[int] = None,
                           temperature: Optional[float] = None) -> str:
        """
        生成文本

        Args:
            prompt: 输入提示
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            生成的文本
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature or 0.7,
            "max_tokens": max_tokens or 4096
        }

        start_time = time.time()

        try:
            response = await self._make_request_with_retry("POST", "/chat/completions", json=payload)

            end_time = time.time()
            response_time = end_time - start_time
            self.stats["total_response_time"] += response_time

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            logger.info(f"Text generation successful: {len(content)} chars, {response_time:.2f}s")
            return content

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            self.stats["total_response_time"] += response_time

            logger.error(f"Text generation failed after {response_time:.2f}s: {e}")
            raise

    async def analyze_concepts(self, text: str) -> Dict[str, Any]:
        """
        分析概念

        Args:
            text: 要分析的文本

        Returns:
            分析结果，包含概念和关系
        """
        prompt = f"""
        分析以下学习内容，提取关键概念和关系：

        {text}

        请以JSON格式返回结果，不要使用markdown代码块：
        {{
            "concepts": [
                {{
                    "name": "概念名称",
                    "definition": "概念定义",
                    "importance": 1-5,
                    "difficulty": "easy/medium/hard"
                }}
            ],
            "relationships": [
                {{
                    "source": "概念1",
                    "target": "概念2",
                    "type": "prerequisite/related_to/uses/example_of"
                }}
            ]
        }}
        """

        start_time = time.time()

        try:
            content = await self.generate_text(prompt, max_tokens=1000, temperature=0.3)

            # 提取JSON
            analysis_result = self._extract_json_from_response(content)

            end_time = time.time()
            response_time = end_time - start_time

            # 验证结果结构
            if "concepts" not in analysis_result:
                analysis_result["concepts"] = []
            if "relationships" not in analysis_result:
                analysis_result["relationships"] = []

            logger.info(f"Concept analysis successful: {len(analysis_result['concepts'])} concepts, {len(analysis_result['relationships'])} relationships, {response_time:.2f}s")

            return analysis_result

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            logger.error(f"Concept analysis failed after {response_time:.2f}s: {e}")

            # 返回基本结构
            return {
                "concepts": [],
                "relationships": [],
                "error": str(e),
                "raw_text": text[:200] + "..." if len(text) > 200 else text
            }

    async def generate_cs70_content(self, topic: str, content_type: str = "explanation") -> Dict[str, Any]:
        """
        生成CS70学习内容

        Args:
            topic: CS70主题
            content_type: 内容类型 (explanation/exercise/summary)

        Returns:
            生成的内容
        """
        type_prompts = {
            "explanation": f"详细解释CS70中的{topic}概念，包括定义、例子和应用",
            "exercise": f"为CS70的{topic}主题创建一个练习题，包含题目、详细解答和关键学习点",
            "summary": f"总结CS70中{topic}的核心要点，适合快速复习"
        }

        prompt = type_prompts.get(content_type, type_prompts["explanation"])

        try:
            content = await self.generate_text(prompt, max_tokens=800, temperature=0.7)

            return {
                "topic": topic,
                "type": content_type,
                "content": content,
                "generated_at": datetime.now().isoformat(),
                "model": self.model
            }

        except Exception as e:
            logger.error(f"CS70 content generation failed for {topic}: {e}")
            return {
                "topic": topic,
                "type": content_type,
                "content": f"Error generating content: {str(e)}",
                "generated_at": datetime.now().isoformat(),
                "model": self.model,
                "error": True
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        stats = self.stats.copy()

        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["failure_rate"] = stats["failed_requests"] / stats["total_requests"]
            stats["rate_limited_rate"] = stats["rate_limited_requests"] / stats["total_requests"]

            if stats["successful_requests"] > 0:
                stats["average_response_time"] = stats["total_response_time"] / stats["successful_requests"]
            else:
                stats["average_response_time"] = 0
        else:
            stats["success_rate"] = 0
            stats["failure_rate"] = 0
            stats["rate_limited_rate"] = 0
            stats["average_response_time"] = 0

        return stats

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "retry_count": 0,
            "total_response_time": 0.0
        }


# 便捷函数
async def create_gemini_client(api_key: str, **kwargs) -> EnhancedGeminiClient:
    """创建Gemini客户端的便捷函数"""
    return EnhancedGeminiClient(api_key=api_key, **kwargs)


# 使用示例
async def example_usage():
    """使用示例"""
    # 配置
    API_KEY = "sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF"

    # 创建客户端
    retry_config = RetryConfig(max_retries=3, base_delay=1.0)
    rate_limit_config = RateLimitConfig(requests_per_minute=15)

    async with EnhancedGeminiClient(
        api_key=API_KEY,
        retry_config=retry_config,
        rate_limit_config=rate_limit_config
    ) as client:

        try:
            # 生成文本
            text = await client.generate_text("什么是命题逻辑？")
            print(f"Generated text: {text}")

            # 分析概念
            analysis = await client.analyze_concepts("命题逻辑和真值表是离散数学的基础")
            print(f"Analysis result: {analysis}")

            # 生成CS70内容
            cs70_content = await client.generate_cs70_content("鸽笼原理", "exercise")
            print(f"CS70 content: {cs70_content}")

            # 查看统计信息
            stats = client.get_stats()
            print(f"Client stats: {stats}")

        except APIError as e:
            print(f"API Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(example_usage())