---
name: langgraph
description: LangGraph framework for building stateful, multi-actor applications with LLMs. Use for building agent workflows, state machines, graph-based orchestration, and complex LLM applications.
---

# LangGraph Skill

Comprehensive assistance with LangGraph development, the framework for building stateful, multi-actor applications with Large Language Models (LLMs).

## When to Use This Skill

This skill should be triggered when:
- Building agent workflows or state machines with LLMs
- Implementing graph-based orchestration for LLM applications
- Working with stateful multi-step LLM processes
- Creating complex AI agent systems
- Debugging or optimizing LangGraph applications
- Learning LangGraph patterns and best practices

## Quick Reference

### 1. Creating a Basic StateGraph

```python
from langgraph.graph import StateGraph, START, END, MessagesState

# Define your state
class State(MessagesState):
    my_state_value: str

# Create the graph
builder = StateGraph(State)

# Add nodes
def my_node(state: State):
    return {"my_state_value": "processed"}

builder.add_node("my_node", my_node)

# Add edges
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)

# Compile
graph = builder.compile()

# Run
result = graph.invoke({"messages": []})
```

### 2. Adding Retry Policies

```python
from langgraph.types import RetryPolicy
import sqlite3

builder.add_node(
    "query_database",
    query_database,
    retry_policy=RetryPolicy(
        retry_on=sqlite3.OperationalError,
        max_attempts=5
    )
)
```

### 3. Adding Node Caching

```python
from langgraph.types import CachePolicy
from langgraph.cache.memory import InMemoryCache

# Add caching to a node (TTL in seconds)
builder.add_node(
    "expensive_node",
    expensive_function,
    cache_policy=CachePolicy(ttl=120)
)

# Compile with cache backend
graph = builder.compile(cache=InMemoryCache())
```

### 4. Runtime Configuration

```python
from langgraph.runtime import Runtime
from typing import TypedDict

# Define config schema
class ContextSchema(TypedDict):
    my_runtime_value: str

# Create graph with context
builder = StateGraph(State, context_schema=ContextSchema)

# Access config in nodes
def node(state: State, runtime: Runtime[ContextSchema]):
    if runtime.context["my_runtime_value"] == "a":
        return {"my_state_value": 1}
    elif runtime.context["my_runtime_value"] == "b":
        return {"my_state_value": 2}

builder.add_node(node)

# Invoke with runtime config
graph.invoke({}, context={"my_runtime_value": "a"})
```

### 5. Conditional Edges and Tool Usage

```python
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode

def should_continue(state: MessagesState):
    """Route to tools or end based on last message"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Build graph with conditional routing
builder = StateGraph(MessagesState)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")

graph = builder.compile()
```

### 6. Tool Retry Configuration

```python
from langgraph.prebuilt.tool_retry import ToolRetry

tool_retry = ToolRetry(
    max_retries=2,
    tools=["search_api", "database_query"],  # Specific tools to retry
    retry_on=(ConnectionError, TimeoutError),  # Retry on these errors
    on_failure="return_message",  # Or "raise"
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=60.0,
    jitter=True
)
```

### 7. Evaluation with LangSmith

```python
from langsmith import Client

ls_client = Client()

# Clone or create dataset
dataset = ls_client.clone_public_dataset(
    "https://smith.langchain.com/public/..."
)

# Define evaluator
def is_concise(outputs: dict, reference_outputs: dict) -> bool:
    return len(outputs["answer"]) < (3 * len(reference_outputs["answer"]))

# Run evaluation
experiment = ls_client.evaluate(
    chatbot,
    data=dataset,
    evaluators=[is_concise],
    experiment_prefix="my-experiment",
    upload_results=False  # Set to True to upload to LangSmith
)

# Analyze results
results = list(experiment)
```

## Key Concepts

### StateGraph
The core building block for creating stateful workflows. A `StateGraph` defines:
- **State schema**: The structure of data passed between nodes
- **Nodes**: Functions that process and transform state
- **Edges**: Connections between nodes (simple or conditional)

### MessagesState
A special state type optimized for chat/message-based applications. Automatically handles:
- Message list management
- Message appending and updates
- Integration with LangChain chat models

### Nodes
Individual processing steps in your graph. Nodes can:
- Transform state
- Call LLMs or tools
- Make decisions
- Access runtime configuration

### Edges
Connections between nodes that control flow:
- **Simple edges**: Always transition to the next node
- **Conditional edges**: Route based on state or logic
- **Special nodes**: `START` and `END` mark entry/exit points

### Policies
- **RetryPolicy**: Handle transient failures with exponential backoff
- **CachePolicy**: Cache node results to avoid redundant computation

### Runtime Context
Configuration values passed at runtime (not in state):
- LLM selection
- System prompts
- Feature flags
- API keys or endpoints

## Common Patterns

### Pattern: Agent with Tools
```python
from langgraph.prebuilt import create_react_agent

# Quick way to create an agent with tools
agent = create_react_agent(
    model,
    tools=[search_tool, calculator_tool],
    state_modifier="You are a helpful assistant."
)

result = agent.invoke({"messages": [("user", "What's 2+2?")]})
```

### Pattern: Multi-Step Workflow
```python
builder = StateGraph(State)

builder.add_node("step1", process_input)
builder.add_node("step2", enrich_data)
builder.add_node("step3", generate_output)

builder.add_edge(START, "step1")
builder.add_edge("step1", "step2")
builder.add_edge("step2", "step3")
builder.add_edge("step3", END)

workflow = builder.compile()
```

### Pattern: Parallel Processing
```python
from langgraph.graph import Send

def fan_out(state):
    """Send to multiple nodes in parallel"""
    return [
        Send("process_a", state),
        Send("process_b", state),
        Send("process_c", state)
    ]

builder.add_conditional_edges("start", fan_out)
```

## Working with This Skill

### For Beginners
1. Start with the basic `StateGraph` example above
2. Understand the difference between state, nodes, and edges
3. Experiment with simple linear workflows before adding conditions
4. Use `MessagesState` for chat-based applications

### For Intermediate Users
1. Add retry policies for reliability
2. Implement caching for expensive operations
3. Use runtime configuration for flexibility
4. Explore conditional edges for dynamic routing

### For Advanced Users
1. Build complex agent systems with multiple LLMs
2. Implement custom checkpointers for persistence
3. Use parallel processing with `Send`
4. Integrate LangSmith for evaluation and monitoring
5. Implement custom tool retry logic

## Reference Files

This skill includes 952 pages of comprehensive documentation in `references/`:

- **llms-txt.md** - Complete LangGraph documentation including:
  - StateGraph API reference
  - Runtime configuration
  - Tool integration patterns
  - Caching and retry strategies
  - Evaluation with LangSmith
  - Async/await patterns
  - Best practices and examples

Use `view references/llms-txt.md` to access detailed information on any topic.

## Troubleshooting

### Common Issues

**Problem: "State not updating between nodes"**
- Ensure nodes return dictionaries with state updates
- Check that state keys match your schema
- Verify edges are correctly connected

**Problem: "Tool calls not working"**
- Confirm tools are properly bound to the model
- Check that `ToolNode` is added to the graph
- Verify conditional edges route to the tool node

**Problem: "Graph execution hangs"**
- Check for missing END edges
- Verify conditional edges always return valid next steps
- Add timeout policies to prevent infinite loops

**Problem: "Retry policy not triggering"**
- Ensure `retry_on` exception types match actual errors
- Check `max_attempts` is > 1
- Verify the retry policy is attached to the correct node

## Resources

### Official Documentation
- Full API reference in `references/llms-txt.md`
- 952 pages of examples, guides, and patterns

### Recommended Learning Path
1. Basic StateGraph creation → See example #1 above
2. Adding nodes and edges → See Multi-Step Workflow pattern
3. Conditional routing → See example #5 above
4. Tool integration → See Agent with Tools pattern
5. Advanced features (retry, caching, runtime config)

## Notes

- This skill was enhanced by Claude from official LangGraph documentation
- All code examples are extracted from real documentation
- Reference files contain 952 pages of detailed content
- Examples include best practices and production-ready patterns

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper: `python cli/doc_scraper.py --config configs/langgraph.json`
2. Optionally enhance again: `python cli/enhance_skill_local.py output/langgraph/`
3. Package the updated skill: `python cli/package_skill.py output/langgraph/`
