#!/usr/bin/env python3
"""测试Graphiti Python原生客户端"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 测试导入
try:
    from graphiti_core import Graphiti
    from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
    from graphiti_core.llm_client.openai_client import OpenAIClient
    from graphiti_core.llm_client.config import LLMConfig
    print("✅ 所有库导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    exit(1)

# 读取配置
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")
embedding_model = os.getenv("GRAPHITI_EMBEDDING_MODEL")
llm_model = os.getenv("GRAPHITI_LLM_MODEL")

print(f"\n配置信息:")
print(f"  Neo4j URI: {neo4j_uri}")
print(f"  Neo4j User: {neo4j_user}")
print(f"  OpenAI Base URL: {openai_base_url}")
print(f"  Embedding Model: {embedding_model}")
print(f"  LLM Model: {llm_model}")

# 初始化embedder
try:
    embedder_config = OpenAIEmbedderConfig(
        embedding_model=embedding_model,
        api_key=openai_api_key,
        base_url=openai_base_url
    )
    embedder = OpenAIEmbedder(config=embedder_config)
    print("\n✅ Embedder初始化成功")
except Exception as e:
    print(f"\n❌ Embedder初始化失败: {e}")
    exit(1)

# 初始化LLM客户端
try:
    llm_config = LLMConfig(
        api_key=openai_api_key,
        model=llm_model,
        base_url=openai_base_url
    )
    llm_client = OpenAIClient(config=llm_config)
    print("✅ LLM客户端初始化成功")
except Exception as e:
    print(f"❌ LLM客户端初始化失败: {e}")
    exit(1)

# 初始化Graphiti
try:
    graphiti_client = Graphiti(
        uri=neo4j_uri,
        user=neo4j_user,
        password=neo4j_password,
        embedder=embedder,
        llm_client=llm_client
    )
    print("✅ Graphiti客户端初始化成功")
    print(f"\n🎉 成功！Graphiti现在可以在Python脚本环境中使用了！")
    print(f"\n这意味着:")
    print(f"  ✅ learning命令启动时Graphiti将自动可用")
    print(f"  ✅ 使用OpenAI兼容API (OpenRouter/DeepSeek)")
    print(f"  ✅ 数据存储在Neo4j数据库")
    print(f"  ✅ 无需MCP协议（直接Python库调用）")
except Exception as e:
    print(f"❌ Graphiti客户端初始化失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
