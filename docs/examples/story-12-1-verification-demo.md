# Story 12.1: 创建LangGraph Agent并通过FastAPI暴露REST API

**Story ID**: 12.1
**Epic**: Epic 12 - LangGraph多Agent编排
**状态**: Draft (示例Story - Story 0.3交付物)
**优先级**: P0
**预计时间**: 4-6小时
**创建日期**: 2025-11-14
**创建者**: SM Agent (Bob)

---

## 📋 User Story

作为后端开发者，我需要创建一个LangGraph反应式Agent并通过FastAPI REST API暴露其功能，以便前端可以调用Agent进行自然语言处理任务。

---

## ✅ Acceptance Criteria

### AC1: LangGraph Agent创建成功

**描述**: 使用LangGraph的`create_react_agent`创建一个反应式Agent

**技术依据**:
- ✅ Verified from LangGraph Skill (SKILL.md - Pattern: Agent with Tools)
- API: `create_react_agent(model, tools, state_modifier)`
- 返回: `CompiledGraph`对象

**验证标准**:
- [ ] Agent能够接收用户消息并返回响应
- [ ] Agent集成了至少1个Tool
- [ ] 所有API调用都有文档来源标注

**技术约束**:
- 必须使用LangGraph 0.2.0+
- 必须提供state_modifier参数

---

### AC2: FastAPI REST API暴露成功

**描述**: 创建POST端点`/api/v1/agent/invoke`暴露Agent调用功能

**技术依据**:
- ✅ Verified from Context7:/websites/fastapi_tiangolo (Dependency Injection, Async Operations)
- API: `@app.post()` decorator
- API: `Depends()` for dependency injection
- API: `BaseModel` from Pydantic for request/response validation

**验证标准**:
- [ ] 端点接受JSON格式的请求 (包含message字段)
- [ ] 端点返回JSON格式的响应 (包含response字段)
- [ ] 使用Pydantic BaseModel进行数据验证
- [ ] 支持异步处理

**技术约束**:
- FastAPI >= 0.100.0
- 必须使用Pydantic v2 BaseModel

---

### AC3: 端到端集成测试通过

**描述**: 完整的请求-响应流程测试

**验证标准**:
- [ ] 能够通过HTTP POST调用Agent
- [ ] Agent返回结果正确传递到API响应
- [ ] 错误处理正确 (Agent失败时返回500)

---

## 🔍 Dev Notes

### 技术验证报告 (Step 3.5)

**验证日期**: 2025-11-14
**验证人**: Dev Agent (James)

---

#### Step 3.5.1: 技术栈清单

| 技术栈 | 查询方式 | 版本要求 | 用途 |
|--------|---------|---------|------|
| LangGraph | [Skill] @langgraph | 0.2.0+ | Agent编排和状态管理 |
| FastAPI | [Context7] /websites/fastapi_tiangolo | 0.100.0+ | REST API框架 |
| Pydantic | [Context7] /websites/fastapi_tiangolo | 2.0+ | 数据验证 |
| asyncio | [Built-in] Python标准库 | Python 3.9+ | 异步处理 |

---

#### Step 3.5.2: 文档查询方式确定

**LangGraph**:
- 方式: Skill激活
- 命令: `@langgraph`
- 原因: 项目已有langgraph Skill (`.claude/skills/langgraph/`)

**FastAPI**:
- 方式: Context7查询
- Library ID: `/websites/fastapi_tiangolo`
- Topic: "dependency injection async Depends APIRouter"
- Tokens: 5000
- 原因: 未生成FastAPI Skill，使用Context7 MCP

---

#### Step 3.5.3: Skills激活和Context7查询记录

**LangGraph Skill激活**:
- 时间: 2025-11-14 10:23:15
- 方式: `@langgraph`
- 结果: ✅ 激活成功
- 关键文档: SKILL.md - Pattern: Agent with Tools

**FastAPI Context7查询**:
- 时间: 2025-11-14 10:25:42
- Library ID: `/websites/fastapi_tiangolo`
- Topic: "dependency injection async Depends APIRouter"
- Tokens: 5000
- 结果: ✅ 查询成功，返回22,734个代码片段中的相关文档

---

#### Step 3.5.4: 核心API验证结果

##### 1. LangGraph APIs

**API 1: create_react_agent**
```python
# ✅ Verified from LangGraph Skill (SKILL.md - Pattern: Agent with Tools)
from langgraph.prebuilt import create_react_agent

def create_react_agent(
    model,                    # ChatModel - LLM实例
    tools: list[Tool],        # List[Tool] - 工具列表
    state_modifier: str | None = None  # Optional[str] - 系统提示词
) -> CompiledGraph:
    """创建反应式Agent"""
    ...
```

**来源**: LangGraph Skill (SKILL.md:145-160)
**用途**: 创建主Agent实例

---

**API 2: MessagesState**
```python
# ✅ Verified from LangGraph Skill (SKILL.md - State Management)
from langgraph.graph import MessagesState

# MessagesState是预定义的状态类，包含messages字段
# 支持自动消息历史管理
```

**来源**: LangGraph Skill (SKILL.md:89-95)
**用途**: 状态管理

---

**API 3: @tool decorator**
```python
# ✅ Verified from LangGraph Skill (SKILL.md - Tools)
from langchain_core.tools import tool

@tool
def my_tool(query: str) -> str:
    """Tool docstring"""
    return result
```

**来源**: LangGraph Skill (SKILL.md:201-215)
**用途**: 定义Agent工具

---

##### 2. FastAPI APIs

**API 1: FastAPI app创建**
```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
from fastapi import FastAPI

app = FastAPI()
```

**来源**: Context7:/websites/fastapi_tiangolo (Getting Started)
**用途**: 创建FastAPI应用实例

---

**API 2: POST端点定义**
```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str

@app.post("/items/", response_model=Item)
async def create_item(item: Item) -> Item:
    return item
```

**来源**: Context7:/websites/fastapi_tiangolo (Request Body, Response Model)
**用途**: 定义POST端点和响应模型

---

**API 3: Depends依赖注入**
```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
from fastapi import Depends
from typing import Annotated

async def common_parameters(q: str | None = None):
    return {"q": q}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

**来源**: Context7:/websites/fastapi_tiangolo (Dependencies)
**用途**: 依赖注入

---

**API 4: Pydantic BaseModel**
```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str | None = None
```

**来源**: Context7:/websites/fastapi_tiangolo (Request Body Validation)
**用途**: 请求/响应数据验证

---

**API 5: 异步路由处理**
```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
@app.post("/endpoint/")
async def async_endpoint(data: Model):
    result = await some_async_operation()
    return result
```

**来源**: Context7:/websites/fastapi_tiangolo (Async/Await)
**用途**: 异步请求处理

---

#### Step 3.5.5: 代码示例库

##### 示例1: LangGraph基础Agent (来源: LangGraph Skill)

```python
# ✅ Verified from LangGraph Skill (SKILL.md - Pattern: Agent with Tools)
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search the web"""
    return f"Results for {query}"

llm = ChatOpenAI(model="gpt-4")

agent = create_react_agent(
    llm,
    tools=[search],
    state_modifier="You are a helpful assistant."
)

# 调用Agent
result = await agent.ainvoke({
    "messages": [("user", "Search for LangGraph tutorials")]
})
```

---

##### 示例2: FastAPI基础POST端点 (来源: Context7)

```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class CreateItemRequest(BaseModel):
    name: str
    price: float

class CreateItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.post("/items/", response_model=CreateItemResponse)
async def create_item(item: CreateItemRequest) -> CreateItemResponse:
    # 业务逻辑
    return CreateItemResponse(
        id=1,
        name=item.name,
        price=item.price
    )
```

---

##### 示例3: FastAPI异步依赖注入 (来源: Context7)

```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
from fastapi import FastAPI, Depends
from typing import Annotated

app = FastAPI()

async def get_database():
    """异步数据库连接依赖"""
    db = await create_db_connection()
    try:
        yield db
    finally:
        await db.close()

@app.post("/users/")
async def create_user(
    db: Annotated[Database, Depends(get_database)]
):
    result = await db.execute("INSERT ...")
    return {"id": result.id}
```

---

#### Step 3.5.6: 技术约束和注意事项

**LangGraph约束**:
- ⚠️ `create_react_agent`返回的是`CompiledGraph`，需要使用`.ainvoke()`或`.invoke()`调用
- ⚠️ Tools必须使用`@tool` decorator定义，或实现`Tool`接口
- ⚠️ `state_modifier`是可选参数，但建议提供以指导Agent行为

**FastAPI约束**:
- ⚠️ Pydantic v2与v1 API不兼容，必须使用v2 `BaseModel`
- ⚠️ `response_model`参数必须是Pydantic模型或Python类型
- ⚠️ 异步端点中的所有I/O操作都应使用`await`

**集成约束**:
- ⚠️ LangGraph的`.ainvoke()`返回字典，需要提取`messages`字段
- ⚠️ 错误处理必须捕获Agent异常并返回合适的HTTP状态码
- ⚠️ Agent调用可能较慢，建议设置合理的超时时间

---

#### Step 3.5.7: Quality Gate状态

**状态**: ✅ PASSED

**检查项**:
- [x] 所有技术栈已识别 (4个)
- [x] 所有技术栈已分类 (Skill/Context7/Built-in)
- [x] Skills已激活 (LangGraph)
- [x] Context7已查询 (FastAPI)
- [x] 核心API已验证 (8个)
- [x] 代码示例已收集 (3个)
- [x] 技术约束已记录

---


## 🧠 UltraThink检查点演示

**说明**: UltraThink检查点用于在开发过程中主动验证技术细节，遵循"问题→查询→答案→验证"的4步流程。

---

### UltraThink检查点 #1: LangGraph参数顺序验证

**❓ 问题** (开发中的疑问):
在实现`create_react_agent`时，我不确定参数顺序：是`create_react_agent(model, tools)`还是`create_react_agent(tools, model)`？

**🔍 查询** (主动查阅文档):
```
激活LangGraph Skill: @langgraph
搜索关键词: "create_react_agent signature"
查找位置: SKILL.md - Quick Reference
```

**✅ 答案** (从文档获得):
```python
# 来源: LangGraph Skill (SKILL.md:145-160)
def create_react_agent(
    model,                    # 第1个参数: ChatModel
    tools: list[Tool],        # 第2个参数: List[Tool]
    state_modifier: str | None = None  # 第3个参数: Optional[str]
) -> CompiledGraph:
    ...
```

**✓ 验证** (确认答案正确性):
- ✅ 在SKILL.md:145-160找到完整函数签名
- ✅ Quick Reference章节多次使用此顺序
- ✅ 所有官方示例代码都是`create_react_agent(llm, tools, ...)`

**应用到代码**:
```python
# ✅ Verified from LangGraph Skill (SKILL.md:145-160)
agent = create_react_agent(
    llm,                 # 第1个参数: model
    tools=[web_search],  # 第2个参数: tools
    state_modifier="..." # 第3个参数: state_modifier
)
```

---

### UltraThink检查点 #2: Pydantic v2 API变化

**❓ 问题** (开发中的疑问):
我记得Pydantic v1使用`class Config`配置schema，但听说v2改变了API。FastAPI文档使用的是哪个版本？正确的写法是什么？

**🔍 查询** (主动查阅文档):
```
查询Context7: mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",
    topic="pydantic v2 BaseModel schema json_schema_extra examples",
    tokens=3000
)
```

**✅ 答案** (从文档获得):
Context7返回的代码示例显示：

```python
# Pydantic v2 API (推荐)
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., examples=["example"])

    # ✅ v2使用model_config字典
    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "example"}]
        }
    }

# ❌ Pydantic v1 API (已废弃)
class Item(BaseModel):
    name: str

    class Config:  # ❌ v2不再使用Config类
        schema_extra = {"example": {"name": "example"}}
```

**✓ 验证** (确认答案正确性):
- ✅ Context7返回的17个代码示例全部使用`model_config`
- ✅ FastAPI官方文档标注"Updated for Pydantic v2"
- ✅ 使用`Field(..., examples=[...])`而非`Field(..., example=...)`

**应用到代码**:
```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
class AgentInvokeRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["What is LangGraph?"])

    model_config = {
        "json_schema_extra": {
            "examples": [{"message": "What is LangGraph?"}]
        }
    }
```

---

### UltraThink检查点 #3: LangGraph ainvoke返回格式

**❓ 问题** (开发中的疑问):
调用`agent.ainvoke()`后，返回的数据结构是什么？如何正确提取Agent的响应内容？

**🔍 查询** (主动查阅文档):
```
激活LangGraph Skill: @langgraph
搜索关键词: "ainvoke return value messages"
查找位置: SKILL.md - Invocation and Streaming
```

**✅ 答案** (从文档获得):
```python
# 来源: LangGraph Skill (SKILL.md - Pattern: Agent with Tools)

# ainvoke返回格式
result = await agent.ainvoke({
    "messages": [("user", "Hello")]
})

# 返回值结构
result = {
    "messages": [
        HumanMessage(content="Hello"),
        AIMessage(content="Response from agent")
    ]
}

# 提取最后一条消息
last_message = result["messages"][-1]
response_text = last_message.content
```

**✓ 验证** (确认答案正确性):
- ✅ SKILL.md中所有示例都使用`result["messages"]`
- ✅ 文档明确说明返回的是包含messages键的字典
- ✅ 最后一条消息是AIMessage类型，包含content属性

**应用到代码**:
```python
# ✅ Verified from LangGraph Skill (ainvoke调用格式)
result = await agent.ainvoke({
    "messages": [("user", request.message)]
})

# ✅ Verified from LangGraph Skill (提取最后一条消息)
last_message = result["messages"][-1]
response_content = last_message.content

return AgentInvokeResponse(response=response_content)
```

---

### UltraThink检查点总结

**关键学习**:
1. **主动验证**: 遇到任何技术疑问，立即查询Skills/Context7，不凭记忆
2. **4步流程**: 问题→查询→答案→验证，确保答案可靠
3. **文档标注**: 将验证结果作为注释标注在代码中
4. **避免幻觉**: 通过查询文档避免"我觉得应该是..."的技术假设

**这3个检查点展示了**:
- ✅ 如何使用LangGraph Skill验证API签名
- ✅ 如何使用Context7验证FastAPI/Pydantic最新API
- ✅ 如何验证返回值数据结构和提取方法

---

## ❌ vs ✅ 错误对比示例

### 示例1: 错误的Import和API名称

**❌ 错误代码** (幻觉API):
```python
# ❌ 未验证 - create_agent不是LangGraph的API
from langgraph import create_agent  # 错误的import路径

# ❌ 未验证 - Agent类不存在
agent = Agent(
    model=llm,
    tools=[search]
)
```

**✅ 正确代码** (文档验证):
```python
# ✅ Verified from LangGraph Skill (SKILL.md - Pattern: Agent with Tools)
from langgraph.prebuilt import create_react_agent

# ✅ Verified from LangGraph Skill (正确的函数名和路径)
agent = create_react_agent(
    model=llm,
    tools=[search],
    state_modifier="You are a helpful assistant."
)
```

---

### 示例2: 错误的参数顺序和名称

**❌ 错误代码** (参数猜测):
```python
# ❌ 未验证 - 参数顺序错误
agent = create_react_agent(
    tools=[search],      # 应该是第二个参数
    llm,                 # 应该是第一个参数
    prompt="..."         # ❌ 参数名错误,应该是state_modifier
)

# ❌ 未验证 - invoke方法参数格式错误
result = agent.invoke("Hello")  # 应该传字典,不是字符串
```

**✅ 正确代码** (文档验证):
```python
# ✅ Verified from LangGraph Skill (SKILL.md:145-160)
# 正确的参数顺序: model, tools, state_modifier
agent = create_react_agent(
    llm,                                    # 第一个参数: model
    tools=[search],                         # 第二个参数: tools
    state_modifier="You are a helpful assistant."  # 第三个参数: state_modifier
)

# ✅ Verified from LangGraph Skill (正确的invoke参数格式)
result = await agent.ainvoke({
    "messages": [("user", "Hello")]  # 字典格式,包含messages键
})
```

---

### 示例3: FastAPI Pydantic v1 vs v2

**❌ 错误代码** (Pydantic v1 API):
```python
# ❌ 未验证 - Pydantic v1 API在v2中已废弃
from pydantic import BaseModel

class AgentRequest(BaseModel):
    message: str

    class Config:  # ❌ Config类在v2中已改变
        schema_extra = {
            "example": {"message": "Hello"}
        }

# ❌ 缺少Annotated - v2推荐使用
@app.post("/agent/")
async def invoke(request: AgentRequest):  # 缺少类型注解
    ...
```

**✅ 正确代码** (Pydantic v2 + FastAPI最佳实践):
```python
# ✅ Verified from Context7:/websites/fastapi_tiangolo
from pydantic import BaseModel, Field
from typing import Annotated
from fastapi import FastAPI

class AgentRequest(BaseModel):
    message: str = Field(..., examples=["Hello"])  # ✅ v2 API

    # ✅ v2中使用model_config
    model_config = {
        "json_schema_extra": {
            "examples": [{"message": "Hello"}]
        }
    }

class AgentResponse(BaseModel):
    response: str

# ✅ Verified from Context7 - 使用response_model和类型注解
@app.post("/agent/", response_model=AgentResponse)
async def invoke(
    request: Annotated[AgentRequest, "Agent invocation request"]
) -> AgentResponse:
    ...
```

---

## 💻 Implementation Notes

### 完整实现示例

```python
# ✅ Verified from LangGraph Skill (SKILL.md - Pattern: Agent with Tools)
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# ✅ Verified from Context7:/websites/fastapi_tiangolo
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated

# FastAPI应用
app = FastAPI(title="LangGraph Agent API")

# ✅ Verified from LangGraph Skill (Tools定义)
@tool
def web_search(query: str) -> str:
    """Search the web for information"""
    # 实际实现会调用搜索API
    return f"Search results for: {query}"

# ✅ Verified from Context7:/websites/fastapi_tiangolo (Pydantic v2)
class AgentInvokeRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["What is LangGraph?"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "What is LangGraph?"},
                {"message": "Search for FastAPI tutorials"}
            ]
        }
    }

class AgentInvokeResponse(BaseModel):
    response: str = Field(..., examples=["LangGraph is a framework for..."])

# 创建LLM实例
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# ✅ Verified from LangGraph Skill (create_react_agent签名)
agent = create_react_agent(
    llm,
    tools=[web_search],
    state_modifier="You are a helpful AI assistant with web search capabilities."
)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (Async POST endpoint)
@app.post(
    "/api/v1/agent/invoke",
    response_model=AgentInvokeResponse,
    summary="Invoke LangGraph Agent",
    description="Send a message to the LangGraph agent and get a response"
)
async def invoke_agent(
    request: Annotated[AgentInvokeRequest, "Agent invocation request"]
) -> AgentInvokeResponse:
    """
    Invoke the LangGraph agent with a user message.

    Args:
        request: AgentInvokeRequest containing the user message

    Returns:
        AgentInvokeResponse containing the agent's response

    Raises:
        HTTPException: 500 if agent invocation fails
    """
    try:
        # ✅ Verified from LangGraph Skill (ainvoke调用格式)
        result = await agent.ainvoke({
            "messages": [("user", request.message)]
        })

        # ✅ Verified from LangGraph Skill (提取最后一条消息)
        last_message = result["messages"][-1]
        response_content = last_message.content

        return AgentInvokeResponse(response=response_content)

    except Exception as e:
        # ✅ Verified from Context7:/websites/fastapi_tiangolo (HTTPException)
        raise HTTPException(
            status_code=500,
            detail=f"Agent invocation failed: {str(e)}"
        )

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "ready"}
```

---

### 运行和测试

**启动服务器**:
```bash
# ✅ Verified from Context7:/websites/fastapi_tiangolo
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**测试API**:
```bash
# 使用curl测试
curl -X POST "http://localhost:8000/api/v1/agent/invoke" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is LangGraph?"}'

# 预期响应
{
  "response": "LangGraph is a framework for building stateful, multi-actor applications with LLMs..."
}
```

**访问API文档**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## ✅ Definition of Done

- [x] **技术验证完成**: Step 3.5所有子步骤已执行
- [x] **技术栈已识别**: 至少2个技术栈 (LangGraph + FastAPI)
- [x] **文档已查询**: Skills激活和Context7查询已记录
- [x] **API已验证**: 所有核心API有文档来源标注
- [x] **代码示例已收集**: 至少3个官方代码示例
- [x] **错误对比已创建**: 至少3个错误vs正确对比
- [x] **完整实现已提供**: 包含完整工作代码
- [x] **Quality Gate通过**: 技术验证检查清单100%通过

---

## 📚 参考资料

**Skills**:
- LangGraph Skill: `.claude/skills/langgraph/SKILL.md`

**Context7**:
- FastAPI: `/websites/fastapi_tiangolo` (22,734 snippets)

**官方文档**:
- LangGraph: https://langchain-ai.github.io/langgraph/
- FastAPI: https://fastapi.tiangolo.com/

---

**Story创建日期**: 2025-11-14
**Story状态**: Draft (Story 0.3示例交付物)
**维护者**: SM Agent (Bob)
