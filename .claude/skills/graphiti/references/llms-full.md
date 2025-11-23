# Welcome to Zep!

<Tip>
  Connect your <strong>AI coding assistant</strong> to Zep's docs: [MCP server & llms.txt](/coding-with-llms)
</Tip>

Zep is a context engineering platform that systematically assembles personalized context—user preferences, traits, and business data—for reliable agent applications. Zep combines agent memory, Graph RAG, and context assembly capabilities to deliver comprehensive personalized context that reduces hallucinations and improves accuracy.

<CardGroup cols={3}>
  <Card title="Key Concepts" icon="brain" href="/concepts">
    Learn about Zep's context engineering platform, temporal knowledge graphs, and agent memory capabilities.
  </Card>

  <Card title="Quickstart" icon="rocket" href="/quickstart">
    Get up and running with Zep in minutes, whether you code in Python, TypeScript, or Go.
  </Card>

  <Card title="Cookbooks" icon="book-open" href="/cookbook/customize-your-context-block">
    Discover practical recipes and patterns for common use cases with Zep.
  </Card>

  <Card title="SDK Reference" icon="code" href="/sdk-reference">
    Comprehensive API documentation for Zep's SDKs in Python, TypeScript, and Go.
  </Card>

  <Card title="Mem0 Migration" icon="fa-solid fa-arrows-rotate" href="/mem0-to-zep">
    Migrate from Mem0 to Zep in minutes.
  </Card>

  <Card title="Graphiti" icon="fa-solid fa-chart-network" href="/graphiti/graphiti">
    Learn about Graphiti, Zep's open-source temporal knowledge graph framework.
  </Card>
</CardGroup>


# Quickstart

> Get up and running with Zep in minutes

<Frame background="subtle">
  <iframe src="https://www.youtube.com/embed/3caAsexOH9k?vq=hd1080" frameBorder="0" allowFullScreen />
</Frame>

<Callout intent="info">
  Get started with the example in the video using:

  ```bash
  git clone https://github.com/getzep/zep.git && cd zep/examples/python/agent-memory-full-example
  ```
</Callout>

Zep is a context engineering platform that systematically assembles personalized context—user preferences, traits, and business data—for reliable agent applications. Zep combines agent memory, Graph RAG, and context assembly capabilities to deliver comprehensive personalized context that reduces hallucinations and improves accuracy. This quickstart will walk you through Zep's two core capabilities: giving your agent persistent memory of user interactions through Agent Memory, and providing your agent with up-to-date knowledge through Dynamic Graph RAG.

<Tip>
  Looking for a more in-depth understanding? Check out our [Key Concepts](/concepts) page.
</Tip>

<Note>
  Migrating from Mem0? Check out our [Mem0 Migration](/v3/mem0-to-zep) guide.
</Note>

Make sure to [set up your environment](/install-sdks) before getting started.

## Provide your agent with up-to-date user memory (Agent Memory)

### Create user graph

<Warning>
  It is important to provide at least the first name and ideally the last name of the user when calling `user.add`. Otherwise, Zep may not be able to correctly associate the user with references to the user in the data you add. If you don't have this information at the time the user is created, you can add it later with our [update user](/sdk-reference/user/update) method.
</Warning>

<CodeBlocks>
  ```python Python
  # Create a new user
  user_id = "user123"
  new_user = client.user.add(
      user_id=user_id,
      email="user@example.com",
      first_name="Jane",
      last_name="Smith",
  )
  ```

  ```typescript TypeScript
  // Create a new user
  const userId = "user123";
  const user = await client.user.add({
    userId: userId,
    email: "user@example.com",
    firstName: "Jane",
    lastName: "Smith",
  });
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
  )

  // Create a new user
  userId := "user123"
  email := "user@example.com"
  firstName := "Jane"
  lastName := "Smith"

  user, err := client.User.Add(context.TODO(), &v3.CreateUserRequest{
      UserID:    userId,
      Email:     &email,
      FirstName: &firstName,
      LastName:  &lastName,
  })
  if err != nil {
      log.Fatal("Error creating user:", err)
  }

  fmt.Println("User created:", user)
  ```
</CodeBlocks>

### Create thread

<CodeBlocks>
  ```python Python
  import uuid

  # Generate a unique thread ID
  thread_id = uuid.uuid4().hex

  # Create a new thread for the user
  client.thread.create(
      thread_id=thread_id,
      user_id=user_id,
  )
  ```

  ```typescript TypeScript
  import { v4 as uuid } from "uuid";

  // Generate a unique thread ID
  const threadId = uuid();

  // Create a new thread for the user
  await client.thread.create({
    threadId: threadId,
    userId: userId,
  });
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
  )

  // Generate a unique thread ID
  threadId := uuid.New().String()
  // Create a new thread for the user
  thread, err := client.Thread.Create(context.TODO(), &v3.CreateThreadRequest{
      ThreadID: threadId,
      UserID:   userId,
  })
  if err != nil {
      log.Fatal("Error creating thread:", err)
  }

  fmt.Println("Thread created:", thread)
  ```
</CodeBlocks>

### Optional: Customize user summary

You can provide custom instructions for how Zep generates summaries of user data in their knowledge graph. This allows you to tailor the user summary to emphasize information most relevant to your application. Learn more about [user summary instructions](/users#user-summary-instructions).

### Add messages

Add chat messages to a thread using the `thread.add_messages` method. These messages will be stored in the thread history and used to build the user's knowledge graph.

<Warning>
  It is important to provide the name of the user in the name field if possible, to help with graph construction. It's also helpful to provide a meaningful name for the assistant in its name field.
</Warning>

<CodeBlocks>
  ```python Python
  # Define messages to add
  from zep_cloud.types import Message

  messages = [
      Message(
          name="Jane",
          content="Hi, my name is Jane Smith and I work at Acme Corp.",
          role="user",
      ),
      Message(
          name="AI Assistant",
          content="Hello Jane! Nice to meet you. How can I help you with Acme Corp today?",
          role="assistant",
      )
  ]

  # Add messages to the thread
  client.thread.add_messages(thread_id, messages=messages)
  ```

  ```typescript TypeScript
  // Define messages to add
  import type { Message } from "@getzep/zep-cloud/api";

  const messages: Message[] = [
    {
      name: "Jane",
      content: "Hi, my name is Jane Smith and I work at Acme Corp.",
      role: "user",
    },
    {
      name: "AI Assistant",
      content: "Hello Jane! Nice to meet you. How can I help you with Acme Corp today?",
      role: "assistant",
    }
  ];

  // Add messages to the thread
  await client.thread.addMessages(threadId, { messages });
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
  )

  // Define messages to add
  userName := "Jane"
  assistantName := "AI Assistant"
  messages := []*v3.Message{
  {
      Name:    &userName,
      Content: "Hi, my name is Jane Smith and I work at Acme Corp.",
      Role:    "user",
  },
  {
      Name:    &assistantName,
      Content: "Hello Jane! Nice to meet you. How can I help you with Acme Corp today?",
      Role:    "assistant",
  },
  }

  // Add messages to the thread
  _, err = client.Thread.AddMessages(
      context.TODO(),
      threadId,
      &v3.AddThreadMessagesRequest{
          Messages: messages,
      },
  )
  if err != nil {
      log.Fatal("Error adding messages:", err)
  }
  ```
</CodeBlocks>

### Optional: Add business data

You can add business data directly to a user's graph using the `graph.add` method. This data can be in the form of messages, text, or JSON.

<CodeBlocks>
  ```python Python
  # Add JSON data to a user's graph
  import json
  json_data = {
      "employee": {
          "name": "Jane Smith",
          "position": "Senior Software Engineer",
          "department": "Engineering",
          "projects": ["Project Alpha", "Project Beta"]
      }
  }
  client.graph.add(
      user_id=user_id,
      type="json",
      data=json.dumps(json_data)
  )

  # Add text data to a user's graph
  client.graph.add(
      user_id=user_id,
      type="text",
      data="Jane Smith is working on Project Alpha and Project Beta."
  )
  ```

  ```typescript TypeScript
  // Add JSON data to a user's graph
  const jsonData = {
    employee: {
      name: "Jane Smith",
      position: "Senior Software Engineer",
      department: "Engineering",
      projects: ["Project Alpha", "Project Beta"]
    }
  };
  await client.graph.add({
    userId: userId,
    type: "json",
    data: JSON.stringify(jsonData)
  });

  // Add text data to a user's graph
  await client.graph.add({
    userId: userId,
    type: "text",
    data: "Jane Smith is working on Project Alpha and Project Beta."
  });
  ```

  ```go Go
  import (
      "context"
      "encoding/json"
      v3 "github.com/getzep/zep-go/v3"
  )

  // Add JSON data to a user's graph
  type Employee struct {
      Name       string   `json:"name"`
      Position   string   `json:"position"`
      Department string   `json:"department"`
      Projects   []string `json:"projects"`
  }
  jsonData := map[string]Employee{
      "employee": {
          Name:       "Jane Smith",
          Position:   "Senior Software Engineer",
          Department: "Engineering",
          Projects:   []string{"Project Alpha", "Project Beta"},
      },
  }
  jsonBytes, err := json.Marshal(jsonData)
  if err != nil {
      log.Fatal("Error marshaling JSON data:", err)
  }
  jsonString := string(jsonBytes)
  _, err = client.Graph.Add(context.TODO(), &v3.AddDataRequest{
      UserID: &userId,
      Type:   v3.GraphDataTypeJSON,
      Data:   jsonString,
  })
  if err != nil {
      log.Fatal("Error adding JSON data:", err)
  }
  // Add text data to a user's graph
  userData := "Jane Smith is working on Project Alpha and Project Beta."
  _, err = client.Graph.Add(context.TODO(), &v3.AddDataRequest{
      UserID: &userId,
      Type:   v3.GraphDataTypeText,
      Data:   userData,
  })
  if err != nil {
      log.Fatal("Error adding user data:", err)
  }

  ```
</CodeBlocks>

### Retrieve context

Use the `thread.get_user_context` method to retrieve relevant context for a thread. This includes a context block with facts and entities that can be used in your prompt.

Zep's context block can either be in summarized or basic form (summarized by default). Retrieving basic results reduces latency (P95 \< 200 ms). Read more about Zep's context block [here](/retrieving-memory#retrieving-zeps-context-block).

<Tabs>
  <Tab title="Summary (default)">
    <CodeBlocks>
      ```python Python
      # Get memory for the thread
      memory = client.thread.get_user_context(thread_id=thread_id)

      # Access the context block (for use in prompts)
      context_block = memory.context
      print(context_block)
      ```

      ```typescript TypeScript
      // Get memory for the thread
      const memory = await client.thread.getUserContext(threadId);

      // Access the context block (for use in prompts)
      const contextBlock = memory.context;
      console.log(contextBlock);
      ```

      ```go Go
      import (
          "context"
          v3 "github.com/getzep/zep-go/v3"
      )

      // Get memory for the thread
      memory, err := client.Thread.GetUserContext(context.TODO(), threadId, nil)
      if err != nil {
          log.Fatal("Error getting memory:", err)
      }
      // Access the context block (for use in prompts)
      contextBlock := memory.Context
      fmt.Println(contextBlock)
      ```
    </CodeBlocks>

    ```text
    - On 2024-07-30, account Emily0e62 made a failed transaction of $99.99.
    - The transaction failed due to the card with last four digits 1234.
    - The failure reason was 'Card expired' as of 2024-09-15.
    - Emily0e62 is a user account belonging to Emily Painter.
    - On 2024-11-14, user account Emily0e62 was suspended due to payment failure.
    - Since 2024-11-14, Emily Painter (Emily0e62) has experienced issues with logging in.
    - As of the present, account Emily0e62 remains suspended and Emily continues to face login issues due to unresolved payment failure from an expired card.
    ```
  </Tab>

  <Tab title="Basic (fast)">
    <CodeBlocks>
      ```python Python
      # Get memory for the thread
      memory = client.thread.get_user_context(thread_id=thread_id, mode="basic")

      # Access the context block (for use in prompts)
      context_block = memory.context
      print(context_block)
      ```

      ```typescript TypeScript
      // Get memory for the thread
      const memory = await client.thread.getUserContext(threadId, { mode: "basic" });

      // Access the context block (for use in prompts)
      const contextBlock = memory.context;
      console.log(contextBlock);
      ```

      ```go Go
      import (
          "context"
          v3 "github.com/getzep/zep-go/v3"
      )

      mode := "basic"
      // Get memory for the thread
      memory, err := client.Thread.GetUserContext(context.TODO(), threadId, &v3.ThreadGetUserContextRequest{
          Mode: &mode,
      })
      if err != nil {
          log.Fatal("Error getting memory:", err)
      }
      // Access the context block (for use in prompts)
      contextBlock := memory.Context
      fmt.Println(contextBlock)
      ```
    </CodeBlocks>

    ```text
    FACTS and ENTITIES represent relevant context to the current conversation.

    # These are the most relevant facts and their valid date ranges

    # format: FACT (Date range: from - to)

    <FACTS>
      - Emily is experiencing issues with logging in. (2024-11-14 02:13:19+00:00 -
        present) 
      - User account Emily0e62 has a suspended status due to payment failure. 
        (2024-11-14 02:03:58+00:00 - present) 
      - user has the id of Emily0e62 (2024-11-14 02:03:54 - present)
      - The failed transaction used a card with last four digits 1234. (2024-09-15
        00:00:00+00:00 - present)
      - The reason for the transaction failure was 'Card expired'. (2024-09-15
        00:00:00+00:00 - present)
      - user has the name of Emily Painter (2024-11-14 02:03:54 - present) 
      - Account Emily0e62 made a failed transaction of 99.99. (2024-07-30 
        00:00:00+00:00 - 2024-08-30 00:00:00+00:00)
    </FACTS>

    # These are the most relevant entities

    # ENTITY_NAME: entity summary

    <ENTITIES>
      - Emily0e62: Emily0e62 is a user account associated with a transaction,
        currently suspended due to payment failure, and is also experiencing issues
        with logging in. 
      - Card expired: The node represents the reason for the transaction failure, 
        which is indicated as 'Card expired'. 
      - Magic Pen Tool: The tool being used by the user that is malfunctioning. 
      - User: user 
      - Support Agent: Support agent responding to the user's bug report. 
      - SupportBot: SupportBot is the virtual assistant providing support to the user, 
        Emily, identified as SupportBot. 
      - Emily Painter: Emily is a user reporting a bug with the magic pen tool, 
        similar to Emily Painter, who is expressing frustration with the AI art
        generation tool and seeking assistance regarding issues with the PaintWiz app.
    </ENTITIES>
    ```
  </Tab>
</Tabs>

You can also directly [search the user graph](/searching-the-graph) and [assemble the context block](/cookbook/customize-your-context-block) for more customized results.

### View your knowledge graph

Since you've created memory, you can view your knowledge graph by navigating to [the Zep Dashboard](https://app.getzep.com/), then Users > "user123" > View Graph. You can also click the "View Episodes" button to see when data is finished being added to the knowledge graph.

### Explore further

Refer to our [agent memory walk-through](/walkthrough) for a more complete example.

## Provide your agent with up-to-date knowledge (Dynamic Graph RAG)

### Create graph

<CodeBlocks>
  ```python Python
  graph = client.graph.create(
      graph_id="some-graph-id", 
      name="Graph Name",
      description="This is a description."
  )
  ```

  ```typescript TypeScript
  const graph = await client.graph.create({
      graphId: "some-graph-id",
      name: "Graph Name",
      description: "This is a description."
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
  )

  name := "Graph Name"
  description := "This is a description."

  graph, err := client.Graph.Create(context.TODO(), &v3.CreateGraphRequest{
      GraphID:     "some-graph-id",
      Name:        &name,
      Description: &description,
  })
  if err != nil {
      log.Fatal("Error creating graph:", err)
  }

  fmt.Println("Graph created:", graph)
  ```
</CodeBlocks>

### Add data

You can add business data directly to a graph using the `graph.add` method. This data can be in the form of text or JSON.

<CodeBlocks>
  ```python Python
  # Add JSON data to a graph
  import json
  json_data = {
      "employee": {
          "name": "Jane Smith",
          "position": "Senior Software Engineer",
          "department": "Engineering",
          "projects": ["Project Alpha", "Project Beta"]
      }
  }
  graph_id = "engineering_team"
  client.graph.add(
      graph_id=graph_id,
      type="json",
      data=json.dumps(json_data)
  )

  # Add text data to a graph
  client.graph.add(
      graph_id=graph_id,
      type="text",
      data="The engineering team is working on Project Alpha and Project Beta."
  )
  ```

  ```typescript TypeScript
  // Add JSON data to a graph
  const jsonData = {
    employee: {
      name: "Jane Smith",
      position: "Senior Software Engineer",
      department: "Engineering",
      projects: ["Project Alpha", "Project Beta"]
    }
  };
  const graphId = "engineering_team";
  await client.graph.add({
    graphId: graphId,
    type: "json",
    data: JSON.stringify(jsonData)
  });

  // Add text data to a graph
  await client.graph.add({
    graphId: graphId,
    type: "text",
    data: "The engineering team is working on Project Alpha and Project Beta."
  });
  ```

  ```go Go
  import (
      "context"
      "encoding/json"
      v3 "github.com/getzep/zep-go/v3"
  )

  // Add JSON data to a graph
  type Employee struct {
      Name       string   `json:"name"`
      Position   string   `json:"position"`
      Department string   `json:"department"`
      Projects   []string `json:"projects"`
  }
  jsonData := map[string]Employee{
      "employee": {
          Name:       "Jane Smith",
          Position:   "Senior Software Engineer",
          Department: "Engineering",
          Projects:   []string{"Project Alpha", "Project Beta"},
      },
  }
  jsonBytes, err := json.Marshal(jsonData)
  if err != nil {
      log.Fatal("Error marshaling JSON data:", err)
  }
  jsonString := string(jsonBytes)
  graphId := "engineering_team"
  _, err = client.Graph.Add(context.TODO(), &v3.AddDataRequest{
      GraphID: &graphId,
      Type:    v3.GraphDataTypeJSON,
      Data:    jsonString,
  })
  if err != nil {
      log.Fatal("Error adding JSON data:", err)
  }
  // Add text data to a graph
  graphData := "The engineering team is working on Project Alpha and Project Beta."
  _, err = client.Graph.Add(context.TODO(), &v3.AddDataRequest{
      GraphID: &graphId,
      Type:    v3.GraphDataTypeText,
      Data:    graphData,
  })
  if err != nil {
      log.Fatal("Error adding graph data:", err)
  }

  ```
</CodeBlocks>

### Search the graph

Use the `graph.search` method to search for edges, nodes, or episodes in the graph. This is useful for finding specific information about a user or graph.

<CodeBlocks>
  ```python Python
  query = "What projects is Jane working on?"

  # Search for edges in a graph
  edge_results = client.graph.search(
      graph_id=graph_id,
      query=query,
      scope="edges",  # Default is "edges"
      limit=5
  )

  # Search for nodes in a graph
  node_results = client.graph.search(
      graph_id=graph_id,
      query=query,
      scope="nodes",
      limit=5
  )

  # Search for episodes in a graph
  episode_results = client.graph.search(
      graph_id=graph_id,
      query=query,
      scope="episodes",
      limit=5
  )
  ```

  ```typescript TypeScript
  const query = "What projects is Jane working on?";

  // Search for edges in a graph
  const edgeResults = await client.graph.search({
    graphId: graphId,
    query: query,
    scope: "edges",  // Default is "edges"
    limit: 5
  });

  // Search for nodes in a graph
  const nodeResults = await client.graph.search({
    graphId: graphId,
    query: query,
    scope: "nodes",
    limit: 5
  });

  // Search for episodes in a graph
  const episodeResults = await client.graph.search({
    graphId: graphId,
    query: query,
    scope: "episodes",
    limit: 5
  });
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
  )

  query := "What projects is Jane working on?"
  limit := 5

  edgeResults, err := client.Graph.Search(context.TODO(), &v3.GraphSearchQuery{
      GraphID: &graphId,
      Query:   query,
      Scope:   v3.GraphSearchScopeEdges.Ptr(),
      Limit:   &limit,
  })
  if err != nil {
      log.Fatal("Error searching graph:", err)
  }
  fmt.Println("Edge search results:", edgeResults)
  // Search for nodes in a graph
  nodeResults, err := client.Graph.Search(context.TODO(), &v3.GraphSearchQuery{
      GraphID: &graphId,
      Query:   query,
      Scope:   v3.GraphSearchScopeNodes.Ptr(),
      Limit:   &limit,
  })
  if err != nil {
      log.Fatal("Error searching graph:", err)
  }
  fmt.Println("Node search results:", nodeResults)
  // Search for episodes in a graph
  episodeResults, err := client.Graph.Search(context.TODO(), &v3.GraphSearchQuery{
      GraphID: &graphId,
      Query:   query,
      Scope:   v3.GraphSearchScopeEpisodes.Ptr(),
      Limit:   &limit,
  })
  if err != nil {
      log.Fatal("Error searching graph:", err)
  }
  fmt.Println("Episode search results:", episodeResults)
  ```
</CodeBlocks>

### Assemble context block

Using the search results, you can build a context block to include in your prompts. For a complete example with helper functions and code samples, see our [Customize your context block cookbook](/cookbook/customize-your-context-block).

### View your knowledge graph

Since you've created memory, you can view your knowledge graph by navigating to [the Zep Dashboard](https://app.getzep.com/), then Users > "user123" > View Graph. You can also click the "View Episodes" button to see when data is finished being added to the knowledge graph.

## Use Zep as an Agentic Tool

Zep's memory retrieval methods can be used as agentic tools, enabling your agent to query Zep for relevant information.
The example below shows how to create a LangChain LangGraph tool to search for facts in a user's graph.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import AsyncZep

  from langchain_core.tools import tool
  from langchain_openai import ChatOpenAI
  from langgraph.graph import StateGraph, MessagesState
  from langgraph.prebuilt import ToolNode

  zep = AsyncZep(api_key=os.environ.get('ZEP_API_KEY'))

  @tool
  async def search_facts(state: MessagesState, query: str, limit: int = 5):
      """Search for facts in all conversations had with a user.
      
      Args:
          state (MessagesState): The Agent's state.
          query (str): The search query.
          limit (int): The number of results to return. Defaults to 5.
      Returns:
          list: A list of facts that match the search query.
      """
      search_results = await zep.graph.search(
        user_id=state['user_name'], 
        query=query, 
        limit=limit, 
      )

      return [edge.fact for edge in search_results.edges]

  tools = [search_facts]
  tool_node = ToolNode(tools)
  llm = ChatOpenAI(model='gpt-4o-mini', temperature=0).bind_tools(tools)
  ```
</CodeBlocks>

## Next Steps

Now that you've learned the basics of using Zep, you can:

* Learn more about [Key Concepts](/concepts)
* Explore the [Graph API](/adding-data-to-the-graph) for adding and retrieving data
* Understand [Users and Threads](/users) in more detail
* Learn about our [Context Block](/retrieving-memory#retrieving-zeps-context-block) for building better prompts
* Explore [Graph Search](/searching-the-graph) for advanced search capabilities


# Key Concepts

> Understanding Zep's context engineering platform and temporal knowledge graphs.

<Tip>
  Looking to just get coding? Check out our [Quickstart](/quickstart).
</Tip>

Zep is a context engineering platform that systematically assembles personalized context—user preferences, traits, and business data—for reliable agent applications. Zep combines Graph RAG, agent memory, and context assembly capabilities to deliver comprehensive personalized context that reduces hallucinations and improves accuracy.

## Concepts Table

| Concept                                    | Description                                                                                                                                                                                                     | Docs                                                              |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Knowledge Graph                            | Zep's unified knowledge store for agents. Nodes represent entities, edges represent facts/relationships. The graph updates dynamically in response to new data.                                                 | [Docs](/understanding-the-graph)                                  |
| Zep's Context Block                        | Optimized string containing facts and entities from the knowledge graph most relevant to the current thread. Also contains dates when facts became valid and invalid. Provide this to your chatbot as "memory". | [Docs](/retrieving-memory#retrieving-zeps-context-block)          |
| Fact Invalidation                          | When new data invalidates a prior fact, the time the fact became invalid is stored on that fact's edge in the knowledge graph.                                                                                  | [Docs](/facts)                                                    |
| JSON/text/message                          | Types of data that can be ingested into the knowledge graph. Can represent business data, documents, chat messages, emails, etc.                                                                                | [Docs](/adding-data-to-the-graph)                                 |
| Custom Entity/Edge Types                   | Feature allowing use of Pydantic-like classes to customize creation/retrieval of entities and relations in the knowledge graph.                                                                                 | [Docs](/customizing-graph-structure#custom-entity-and-edge-types) |
| Graph                                      | Represents an arbitrary knowledge graph for storing up-to-date knowledge about an object or system. For storing up-to-date knowledge about a user, a user graph should be used.                                 | [Docs](/graph-overview)                                           |
| User Graph                                 | Special type of graph for storing personalized memory for a user of your application.                                                                                                                           | [Docs](/users)                                                    |
| User                                       | A user in Zep represents a user of your application, and has its own User Graph and thread history.                                                                                                             | [Docs](/users)                                                    |
| Threads                                    | Conversation threads of a user. By default, all messages added to any thread of that user are ingested into that user's graph.                                                                                  | [Docs](/threads)                                                  |
| `graph.add` & `thread.add_messages`        | Methods for adding data to a graph and user graph respectively.                                                                                                                                                 | [Docs](/adding-data-to-the-graph) [Docs](/memory#adding-memory)   |
| `graph.search` & `thread.get_user_context` | Low level and high level methods respectively for retrieving from the knowledge graph.                                                                                                                          | [Docs](/searching-the-graph) [Docs](/memory#retrieving-memory)    |
| User Summary Instructions                  | Customize how Zep generates entity summaries for users in their knowledge graph. Up to 5 custom instructions per user to guide summary generation.                                                              | [Docs](/users#user-summary-instructions)                          |
| Agentic Tool                               | Use Zep's memory retrieval methods as agentic tools, enabling your agent to query for relevant information from the user's knowledge graph.                                                                     | [Docs](/quickstart#use-zep-as-an-agentic-tool)                    |

## Use Cases Table

| Use case          | Purpose                                                                  | Implementation                                                                                                                                                                                                                                                                              |
| ----------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dynamic Graph RAG | Provide your agent with up-to-date knowledge of an object/system         | Add/stream all relevant data to a Graph ([docs](/adding-data-to-the-graph)), chunking first if needed ([docs](/adding-data-to-the-graph#data-size-limit-and-chunking)), and retrieve from the graph by constructing a custom context block ([docs](/cookbook/customize-your-context-block)) |
| Agent memory      | Provide your agent with up-to-date knowledge of a user                   | Add/stream user messages and user business data to a User Graph ([docs](/adding-memory)), and retrieve user memory as the context block returned from `thread.get_user_context` ([docs](/retrieving-memory)), and provide this context block to your agent before responding                |
| Voice agents      | Provide up-to-date knowledge with extremely low latency to a voice agent | Similar to other implementations, except incorporating latency optimizations ([docs](/performance))                                                                                                                                                                                         |

## What is Context Engineering?

Context Engineering is the discipline of assembling all necessary information, instructions, and tools around a LLM to help it accomplish tasks reliably. Unlike simple prompt engineering, context engineering involves building dynamic systems that provide the right information in the right format so LLMs can perform consistently.

The core challenge: LLMs are stateless and only know what's in their immediate context window. Context engineering bridges this gap by systematically providing relevant background knowledge, user history, business data, and tool outputs.

Using [business data and/or user chat histories](#business-data-vs-chat-message-data), Zep automatically constructs a [temporal knowledge graph](/graph-overview) to reflect the state of an object/system or a user. The knowledge graph contains entities, relationships, and facts related to your object/system or user. As facts change or are superseded, [Zep updates the graph](#managing-changes-in-facts-over-time) to reflect their new state. Through systematic context engineering, Zep provides your agent with the comprehensive information needed to deliver personalized responses and solve problems. This reduces hallucinations, improves accuracy, and reduces the cost of LLM calls.

<lite-vimeo videoid="1021963693" />

## How Zep Fits Into Your Application

Your application sends Zep business data (JSON, unstructured text) and/or messages. Business data sources may include CRM applications, emails, billing data, or conversations on other communication platforms like Slack.

<Frame>
  <img src="file:a6a7437b-6e89-4e01-ba06-d7ee9bc1b78a" />
</Frame>

Zep automatically fuses this data together on a temporal knowledge graph, building a holistic view of the object/system or user and the relationships between entities. Zep offers a number of APIs for [adding and retrieving memory](#retrieving-memory). In addition to populating a prompt with Zep's engineered context, Zep's search APIs can be used to build [agentic tools](#using-zep-as-an-agentic-tool).

The example below shows Zep's `memory.context` field resulting from a call to `thread.get_user_context()`. This is Zep's engineered context block that can be added to your prompt and contains facts and graph entities relevant to the current conversation with a user. For more about the temporal context of facts, see [Managing changes in facts over time](#managing-changes-in-facts-over-time).

### Context Block

[Zep's Context Block](/retrieving-memory#retrieving-zeps-context-block) is Zep's engineered context string containing relevant facts and entities for the thread. It is always present in the result of `thread.get_user_context()`
call and can be optionally [received with the response of `thread.add_messages()` call](/docs/performance/performance-best-practices#get-the-context-block-string-sooner).

Zep's context block can either be in summarized or basic form (summarized by default). Retrieving basic results reduces latency (P95 \< 200 ms). Read more about Zep's Context Block [here](/retrieving-memory#retrieving-zeps-context-block).

<Tabs>
  <Tab title="Summary (default)">
    <CodeBlocks>
      ```python Python
      # Get memory for the thread
      memory = client.thread.get_user_context(thread_id=thread_id)

      # Access the context block (for use in prompts)
      context_block = memory.context
      print(context_block)
      ```

      ```typescript TypeScript
      // Get memory for the thread
      const memory = await client.thread.getUserContext(threadId);

      // Access the context block (for use in prompts)
      const contextBlock = memory.context;
      console.log(contextBlock);
      ```

      ```go Go
      import (
          "context"
          v3 "github.com/getzep/zep-go/v3"
      )

      // Get memory for the thread
      memory, err := client.Thread.GetUserContext(context.TODO(), threadId, nil)
      if err != nil {
          log.Fatal("Error getting memory:", err)
      }
      // Access the context block (for use in prompts)
      contextBlock := memory.Context
      fmt.Println(contextBlock)
      ```
    </CodeBlocks>

    ```text
    - On 2024-07-30, account Emily0e62 made a failed transaction of $99.99.
    - The transaction failed due to the card with last four digits 1234.
    - The failure reason was 'Card expired' as of 2024-09-15.
    - Emily0e62 is a user account belonging to Emily Painter.
    - On 2024-11-14, user account Emily0e62 was suspended due to payment failure.
    - Since 2024-11-14, Emily Painter (Emily0e62) has experienced issues with logging in.
    - As of the present, account Emily0e62 remains suspended and Emily continues to face login issues due to unresolved payment failure from an expired card.
    ```
  </Tab>

  <Tab title="Basic (fast)">
    <CodeBlocks>
      ```python Python
      # Get memory for the thread
      memory = client.thread.get_user_context(thread_id=thread_id, mode="basic")

      # Access the context block (for use in prompts)
      context_block = memory.context
      print(context_block)
      ```

      ```typescript TypeScript
      // Get memory for the thread
      const memory = await client.thread.getUserContext(threadId, { mode: "basic" });

      // Access the context block (for use in prompts)
      const contextBlock = memory.context;
      console.log(contextBlock);
      ```

      ```go Go
      import (
          "context"
          v3 "github.com/getzep/zep-go/v3"
      )

      mode := "basic"
      // Get memory for the thread
      memory, err := client.Thread.GetUserContext(context.TODO(), threadId, &v3.ThreadGetUserContextRequest{
          Mode: &mode,
      })
      if err != nil {
          log.Fatal("Error getting memory:", err)
      }
      // Access the context block (for use in prompts)
      contextBlock := memory.Context
      fmt.Println(contextBlock)
      ```
    </CodeBlocks>

    ```text
    FACTS and ENTITIES represent relevant context to the current conversation.

    # These are the most relevant facts and their valid date ranges

    # format: FACT (Date range: from - to)

    <FACTS>
      - Emily is experiencing issues with logging in. (2024-11-14 02:13:19+00:00 -
        present) 
      - User account Emily0e62 has a suspended status due to payment failure. 
        (2024-11-14 02:03:58+00:00 - present) 
      - user has the id of Emily0e62 (2024-11-14 02:03:54 - present)
      - The failed transaction used a card with last four digits 1234. (2024-09-15
        00:00:00+00:00 - present)
      - The reason for the transaction failure was 'Card expired'. (2024-09-15
        00:00:00+00:00 - present)
      - user has the name of Emily Painter (2024-11-14 02:03:54 - present) 
      - Account Emily0e62 made a failed transaction of 99.99. (2024-07-30 
        00:00:00+00:00 - 2024-08-30 00:00:00+00:00)
    </FACTS>

    # These are the most relevant entities

    # ENTITY_NAME: entity summary

    <ENTITIES>
      - Emily0e62: Emily0e62 is a user account associated with a transaction,
        currently suspended due to payment failure, and is also experiencing issues
        with logging in. 
      - Card expired: The node represents the reason for the transaction failure, 
        which is indicated as 'Card expired'. 
      - Magic Pen Tool: The tool being used by the user that is malfunctioning. 
      - User: user 
      - Support Agent: Support agent responding to the user's bug report. 
      - SupportBot: SupportBot is the virtual assistant providing support to the user, 
        Emily, identified as SupportBot. 
      - Emily Painter: Emily is a user reporting a bug with the magic pen tool, 
        similar to Emily Painter, who is expressing frustration with the AI art
        generation tool and seeking assistance regarding issues with the PaintWiz app.
    </ENTITIES>
    ```
  </Tab>
</Tabs>

You can then include this context in your system prompt:

| MessageType | Content                                                |
| ----------- | ------------------------------------------------------ |
| `System`    | Your system prompt <br /> <br /> `{Zep context block}` |
| `Assistant` | An assistant message stored in Zep                     |
| `User`      | A user message stored in Zep                           |
| ...         | ...                                                    |
| `User`      | The latest user message                                |


# Coding with LLMs

> Integrate Zep's documentation directly into your AI coding workflow using llms.txt and MCP.

Zep provides tools that give AI coding assistants direct access to Zep's documentation: a real-time MCP server and standardized llms.txt files for enhanced code generation and troubleshooting.

## Docs MCP Server

Zep's Docs MCP server gives AI assistants real-time access to search Zep's complete documentation.

**Server details:**

* URL: `docs-mcp.getzep.com`
* Type: Search-based with HTTP transport
* Capabilities: Real-time documentation search and retrieval

<Callout intent="warning">
  The `/sse` endpoint is deprecated and will be removed soon. Please update to the new `/mcp` endpoint with HTTP transport.
</Callout>

### Setting up the MCP server

<Tabs>
  <Tab title="Claude Code">
    Add the HTTP server using the CLI:

    ```bash
    claude mcp add zep-docs https://docs-mcp.getzep.com/mcp
    ```
  </Tab>

  <Tab title="Cursor">
    Create `.cursor/mcp.json` in your project or `~/.cursor/mcp.json` globally:

    ```json
    {
      "mcpServers": {
        "zep-docs": {
          "url": "https://docs-mcp.getzep.com/mcp"
        }
      }
    }
    ```

    Enable MCP servers in Cursor settings, then add and enable the zep-docs server.
  </Tab>

  <Tab title="Other MCP clients">
    Configure your MCP client with HTTP transport:

    ```
    URL: https://docs-mcp.getzep.com/mcp
    ```
  </Tab>
</Tabs>

### Using the MCP server

Once configured, AI assistants can automatically:

* Search Zep concepts and features
* Find code examples and tutorials
* Access current API documentation
* Retrieve troubleshooting information

## llms.txt

Zep publishes standardized `llms.txt` files containing essential information for AI coding assistants:

* Core concepts and architecture
* Usage patterns and examples
* API reference summaries
* Best practices and troubleshooting
* Framework integration examples

### Accessing llms.txt

Zep provides two versions of the llms.txt file:

**Standard version** (recommended for most use cases):

```
https://help.getzep.com/llms.txt
```

**Comprehensive version** (for advanced use cases):

```
https://help.getzep.com/llms-full.txt
```

The standard version contains curated essentials, while the comprehensive version includes complete documentation but is much larger. Most AI assistants work better with the standard version due to context limitations.


# Install SDKs

> Set up your development environment for Zep

This guide will help you obtain an API key, install the SDK, and initialize the Zep client.

## Obtain an API Key

[Create a free Zep account](https://app.getzep.com/) and you will be prompted to create an API key.

## Install the SDK

### Python

Set up your Python project, ideally with [a virtual environment](https://medium.com/@vkmauryavk/managing-python-virtual-environments-with-uv-a-comprehensive-guide-ac74d3ad8dff), and then:

<Tabs>
  <Tab title="pip">
    ```Bash
    pip install zep-cloud
    ```
  </Tab>

  <Tab title="uv">
    ```Bash
    uv pip install zep-cloud
    ```
  </Tab>
</Tabs>

### TypeScript

Set up your TypeScript project and then:

<Tabs>
  <Tab title="npm">
    ```Bash
    npm install @getzep/zep-cloud
    ```
  </Tab>

  <Tab title="yarn">
    ```Bash
    yarn add @getzep/zep-cloud
    ```
  </Tab>

  <Tab title="pnpm">
    ```Bash
    pnpm install @getzep/zep-cloud
    ```
  </Tab>
</Tabs>

### Go

Set up your Go project and then:

```Bash
go get github.com/getzep/zep-go/v3
```

## Initialize the Client

First, make sure you have a .env file with your API key:

```
ZEP_API_KEY=your_api_key_here
```

After creating your .env file, you'll need to source it in your terminal session:

```bash
source .env
```

Then, initialize the client with your API key:

<CodeBlocks>
  ```python Python
  import os
  from zep_cloud.client import Zep

  API_KEY = os.environ.get('ZEP_API_KEY')

  client = Zep(
      api_key=API_KEY,
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const API_KEY = process.env.ZEP_API_KEY;

  const client = new ZepClient({
    apiKey: API_KEY,
  });
  ```

  ```go Go
  import (
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(os.Getenv("ZEP_API_KEY")),
  )
  ```
</CodeBlocks>

<Info>
  **The Python SDK Supports Async Use**

  The Python SDK supports both synchronous and asynchronous usage. For async operations, import `AsyncZep` instead of `Zep` and remember to `await` client calls in your async code.
</Info>


# Building a Chatbot with Zep

> Familiarize yourself with Zep and the Zep SDKs, culminating in building a simple chatbot.

<Tip>
  For an introduction to Zep's memory layer, Knowledge Graph, and other key concepts, see the [Concepts Guide](/concepts).
</Tip>

<Note>
  A Jupyter notebook version of this guide is [available here](https://github.com/getzep/zep/blob/main/examples/python/quickstart/quickstart.ipynb).
</Note>

In this guide, we'll walk through a simple example of how to use Zep Cloud to build a user-facing chatbot. We're going to upload a number of datasets to Zep, building a graph of data about a user.

Then we'll use the Zep Python SDK to retrieve and search the data.

Finally, we'll build a simple chatbot that uses Zep to retrieve and search data to respond to a user.

## Set Up Your Environment

1. Sign up for a [Zep Cloud](https://www.getzep.com/) account.

2. Ensure you install required dependencies into your Python environment before running this notebook. See [Installing Zep SDKs](sdks.mdx) for more information. Optionally create your environment in a `virtualenv`.

```bash
pip install zep-cloud openai rich python-dotenv
```

3. Ensure that you have a `.env` file in your working directory that includes your `ZEP_API_KEY` and `OPENAI_API_KEY`:

<Note>
  Zep API keys are specific to a project. You can create multiple keys for a
  single project. Visit `Project Settings` in the Zep dashboard to manage your
  API keys.
</Note>

```text
ZEP_API_KEY=<key>
OPENAI_API_KEY=<key>
```

<CodeBlocks>
  ```python Python
  import os
  import json
  import uuid

  from openai import OpenAI
  import rich

  from dotenv import load_dotenv
  from zep_cloud.client import Zep
  from zep_cloud import Message

  load_dotenv()

  zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))

  oai_client = OpenAI(
      api_key=os.getenv("OPENAI_API_KEY"),
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";
  import * as dotenv from "dotenv";
  import { v4 as uuidv4 } from 'uuid';
  import OpenAI from 'openai';

  dotenv.config();

  const zep = new ZepClient({ apiKey: process.env.ZEP_API_KEY });

  const oai_client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });
  ```
</CodeBlocks>

<Info>
  We also provide an 

  [Asynchronous Python client](/install-sdks#initialize-the-client)

  .
</Info>

## Create User and Add a Thread

Users in Zep may have one or more chat threads. These are threads of messages between the user and an agent.

<Tip>
  Include the user's **full name** and **email address** when creating a user.
  This improves Zep's ability to associate data, such as emails or documents,
  with a user.
</Tip>

<CodeBlocks>
  ```python Python
  bot_name = "SupportBot"
  user_name = "Emily"
  user_id = user_name + str(uuid.uuid4())[:4]
  thread_id = str(uuid.uuid4())

  zep.user.add(
      user_id=user_id,
      email=f"{user_name}@painters.com",
      first_name=user_name,
      last_name="Painter",
  )

  zep.thread.create(
      user_id=user_id,
      thread_id=thread_id,
  )
  ```

  ```typescript TypeScript
  const bot_name = "SupportBot";
  const user_name = "Emily";
  const user_id = user_name + uuidv4().substring(0, 4);
  const thread_id = uuidv4();

  await zep.user.add({
    userId: user_id,
    email: `${user_name}@painters.com`,
    firstName: user_name,
    lastName: "Painter",
  });

  await zep.thread.create({
    userId: user_id,
    threadId: thread_id,
  });
  ```
</CodeBlocks>

## Datasets

We're going to use the [memory](/adding-memory#adding-messages) and [graph](/adding-data-to-the-graph) APIs to upload an assortment of data to Zep. These include past dialog with the agent, CRM support cases, and billing data.

<CodeBlocks>
  ```python Python
  support_cases = [
      {
          "subject": "Bug: Magic Pen Tool Drawing Goats Instead of Boats",
          "messages": [
              {
                  "role": "user",
                  "content": "Whenever I use the magic pen tool to draw boats, it ends up drawing goats instead.",
                  "timestamp": "2024-03-16T14:20:00Z",
              },
              {
                  "role": "support_agent",
                  "content": f"Hi {user_name}, that sounds like a bug! Thanks for reporting it. Could you let me know exactly how you're using the tool when this happens?",
                  "timestamp": "2024-03-16T14:22:00Z",
              },
              {
                  "role": "user",
                  "content": "Sure, I select the magic pen, draw a boat shape, and it just replaces the shape with goats.",
                  "timestamp": "2024-03-16T14:25:00Z",
              },
              {
                  "role": "support_agent",
                  "content": "Got it! We'll escalate this to our engineering team. In the meantime, you can manually select the boat shape from the options rather than drawing it with the pen.",
                  "timestamp": "2024-03-16T14:27:00Z",
              },
              {
                  "role": "user",
                  "content": "Okay, thanks. I hope it gets fixed soon!",
                  "timestamp": "2024-03-16T14:30:00Z",
              },
          ],
          "status": "escalated",
      },
  ]

  chat_history = [
      {
          "role": "assistant",
          "name": bot_name,
          "content": f"Hello {user_name}, welcome to PaintWiz support. How can I assist you today?",
          "timestamp": "2024-03-15T10:00:00Z",
      },
      {
          "role": "user",
          "name": user_name,
          "content": "I'm absolutely furious! Your AI art generation is completely broken!",
          "timestamp": "2024-03-15T10:02:00Z",
      },
      {
          "role": "assistant",
          "name": bot_name,
          "content": f"I'm sorry to hear that you're experiencing issues, {user_name}. Can you please provide more details about what's going wrong?",
          "timestamp": "2024-03-15T10:03:00Z",
      },
      {
          "role": "user",
          "name": user_name,
          "content": "Every time I try to draw mountains, your stupid app keeps turning them into fountains! And what's worse, all the people in my drawings have six fingers! It's ridiculous!",
          "timestamp": "2024-03-15T10:05:00Z",
      },
      {
          "role": "assistant",
          "name": bot_name,
          "content": f"I sincerely apologize for the frustration this is causing you, {user_name}. That certainly sounds like a significant glitch in our system. I understand how disruptive this can be to your artistic process. Can you tell me which specific tool or feature you're using when this occurs?",
          "timestamp": "2024-03-15T10:06:00Z",
      },
      {
          "role": "user",
          "name": user_name,
          "content": "I'm using the landscape generator and the character creator. Both are completely messed up. How could you let this happen?",
          "timestamp": "2024-03-15T10:08:00Z",
      },
  ]

  transactions = [
      {
          "date": "2024-07-30",
          "amount": 99.99,
          "status": "Success",
          "account_id": user_id,
          "card_last_four": "1234",
      },
      {
          "date": "2024-08-30",
          "amount": 99.99,
          "status": "Failed",
          "account_id": user_id,
          "card_last_four": "1234",
          "failure_reason": "Card expired",
      },
      {
          "date": "2024-09-15",
          "amount": 99.99,
          "status": "Failed",
          "account_id": user_id,
          "card_last_four": "1234",
          "failure_reason": "Card expired",
      },
  ]

  account_status = {
      "user_id": user_id,
      "account": {
          "account_id": user_id,
          "account_status": {
              "status": "suspended",
              "reason": "payment failure",
          },
      },
  }

  def convert_to_zep_messages(chat_history: list[dict[str, str | None]]) -> list[Message]:
      """
      Convert chat history to Zep messages.

      Args:
      chat_history (list): List of dictionaries containing chat messages.

      Returns:
      list: List of Zep Message objects.
      """
      return [
          Message(
              role=msg["role"],
              name=msg.get("name", None),
              content=msg["content"],
          )
          for msg in chat_history
      ]

  # Zep's high-level API allows us to add a list of messages to a thread.
  zep.thread.add_messages(
      thread_id=thread_id, messages=convert_to_zep_messages(chat_history)
  )

  # The lower-level data API allows us to add arbitrary data to a user's Knowledge Graph.
  for tx in transactions:
      zep.graph.add(user_id=user_id, data=json.dumps(tx), type="json")

      zep.graph.add(
          user_id=user_id, data=json.dumps(account_status), type="json"
      )

  for case in support_cases:
      zep.graph.add(user_id=user_id, data=json.dumps(case), type="json")
  ```

  ```typescript TypeScript
  const support_cases = [
    {
      subject: "Bug: Magic Pen Tool Drawing Goats Instead of Boats",
      messages: [
        {
          role: "user",
          content: "Whenever I use the magic pen tool to draw boats, it ends up drawing goats instead.",
          timestamp: "2024-03-16T14:20:00Z",
        },
        {
          role: "support_agent",
          content: `Hi ${user_name}, that sounds like a bug! Thanks for reporting it. Could you let me know exactly how you're using the tool when this happens?`,
          timestamp: "2024-03-16T14:22:00Z",
        },
        {
          role: "user",
          content: "Sure, I select the magic pen, draw a boat shape, and it just replaces the shape with goats.",
          timestamp: "2024-03-16T14:25:00Z",
        },
        {
          role: "support_agent",
          content: "Got it! We'll escalate this to our engineering team. In the meantime, you can manually select the boat shape from the options rather than drawing it with the pen.",
          timestamp: "2024-03-16T14:27:00Z",
        },
        {
          role: "user",
          content: "Okay, thanks. I hope it gets fixed soon!",
          timestamp: "2024-03-16T14:30:00Z",
        },
      ],
      status: "escalated",
    },
  ];

  const chat_history = [
    {
      role: "assistant",
      name: bot_name,
      content: `Hello ${user_name}, welcome to PaintWiz support. How can I assist you today?`,
      timestamp: "2024-03-15T10:00:00Z",
    },
    {
      role: "user",
      name: user_name,
      content: "I'm absolutely furious! Your AI art generation is completely broken!",
      timestamp: "2024-03-15T10:02:00Z",
    },
    {
      role: "assistant",
      name: bot_name,
      content: `I'm sorry to hear that you're experiencing issues, ${user_name}. Can you please provide more details about what's going wrong?`,
      timestamp: "2024-03-15T10:03:00Z",
    },
    {
      role: "user",
      name: user_name,
      content: "Every time I try to draw mountains, your stupid app keeps turning them into fountains! And what's worse, all the people in my drawings have six fingers! It's ridiculous!",
      timestamp: "2024-03-15T10:05:00Z",
    },
    {
      role: "assistant",
      name: bot_name,
      content: `I sincerely apologize for the frustration this is causing you, ${user_name}. That certainly sounds like a significant glitch in our system. I understand how disruptive this can be to your artistic process. Can you tell me which specific tool or feature you're using when this occurs?`,
      timestamp: "2024-03-15T10:06:00Z",
    },
    {
      role: "user",
      name: user_name,
      content: "I'm using the landscape generator and the character creator. Both are completely messed up. How could you let this happen?",
      timestamp: "2024-03-15T10:08:00Z",
    },
  ];

  const transactions = [
    {
      date: "2024-07-30",
      amount: 99.99,
      status: "Success",
      account_id: user_id,
      card_last_four: "1234",
    },
    {
      date: "2024-08-30",
      amount: 99.99,
      status: "Failed",
      account_id: user_id,
      card_last_four: "1234",
      failure_reason: "Card expired",
    },
    {
      date: "2024-09-15",
      amount: 99.99,
      status: "Failed",
      account_id: user_id,
      card_last_four: "1234",
      failure_reason: "Card expired",
    },
  ];

  const account_status = {
    user_id: user_id,
    account: {
      account_id: user_id,
      account_status: {
        status: "suspended",
        reason: "payment failure",
      },
    },
  };

  /**
   * Convert chat history to Zep messages.
   * 
   * Args:
   * chatHistory (array): Array of objects containing chat messages.
   * 
   * Returns:
   * array: Array of Zep message objects.
   */
  const convertToZepMessages = (chatHistory: any[]) => {
    return chatHistory.map(msg => ({
      role: msg.role,
      name: msg.name || null,
      content: msg.content,
    }));
  };

  // Zep's high-level API allows us to add a list of messages to a thread.
  await zep.thread.addMessages(thread_id, {
    messages: convertToZepMessages(chat_history)
  });

  // The lower-level data API allows us to add arbitrary data to a user's Knowledge Graph.
  for (const tx of transactions) {
    await zep.graph.add({
      userId: user_id,
      type: "json",
      data: JSON.stringify(tx)
    });

    await zep.graph.add({
      userId: user_id,
      type: "json",
      data: JSON.stringify(account_status)
    });
  }

  for (const case_data of support_cases) {
    await zep.graph.add({
      userId: user_id,
      type: "json",
      data: JSON.stringify(case_data)
    });
  }
  ```
</CodeBlocks>

### Wait a minute or two!

<Tip>
  We've batch uploaded a number of datasets that need to be ingested into Zep's
  graph before they can be queried. In ordinary operation, this data would
  stream into Zep and ingestion latency would be negligible.
</Tip>

## Retrieve Data From Zep

We'll start with getting a list of facts, which are stored on the edges of the graph. We'll see the temporal data associated with facts as well as the graph nodes the fact is related to.

<Tip>
  This data is also viewable in the Zep Web application.
</Tip>

<CodeBlocks>
  ```python Python
  all_user_edges = zep.graph.edge.get_by_user_id(user_id=user_id)
  rich.print(all_user_edges[:3])
  ```

  ```typescript TypeScript
  const all_user_edges = await zep.graph.edge.getByUserId(user_id);
  console.log(all_user_edges.slice(0, 3));
  ```
</CodeBlocks>

```text
[
    EntityEdge(
        created_at='2025-02-20T20:31:01.769332Z',
        episodes=['0d3a35c7-ebd3-427d-89a6-1a8dabd2df64'],
        expired_at='2025-02-20T20:31:18.742184Z',
        fact='The transaction failed because the card expired.',
        invalid_at='2024-09-15T00:00:00Z',
        name='HAS_FAILURE_REASON',
        source_node_uuid='06c61c00-9101-474f-9bca-42b4308ec378',
        target_node_uuid='07efd834-f07a-4c3c-9b32-d2fd9362afd5',
        uuid_='fb5ee0df-3aa0-44f3-889d-5bb163971b07',
        valid_at='2024-08-30T00:00:00Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:31:33.771557Z',
        episodes=['60d1d20e-ed6c-4966-b1da-3f4ca274a524'],
        expired_at=None,
        fact='Emily uses the magic pen tool to draw boats.',
        invalid_at=None,
        name='USES_TOOL',
        source_node_uuid='36f5c5c6-eb16-4ebb-9db0-fd34809482f5',
        target_node_uuid='e337522d-3a62-4c45-975d-904e1ba25667',
        uuid_='f9eb0a98-1624-4932-86ca-be75a3c248e5',
        valid_at='2025-02-20T20:29:40.217412Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:30:28.499178Z',
        episodes=['b8e4da4c-dd5e-4c48-bdbc-9e6568cd2d2e'],
        expired_at=None,
        fact="SupportBot understands how disruptive the glitch in the AI art generation can be to Emily's artistic process.",
        invalid_at=None,
        name='UNDERSTANDS',
        source_node_uuid='fd4ab1f0-e19e-40b7-aaec-78bd97571725',
        target_node_uuid='8e5686fc-f175-4da9-8778-ad8d60fc469a',
        uuid_='f8c52a21-e938-46a3-b930-04671d0c018a',
        valid_at='2025-02-20T20:29:39.08846Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    )
]
```

The [`thread.get_user_context` method](/retrieving-memory#retrieving-zeps-context-block) provides an easy way to retrieve memory relevant to the current conversation by using the last 4 messages and their proximity to the User node.

<Tip>
  The `thread.get_user_context` method is a good starting point for retrieving relevant conversation context. It shortcuts passing recent messages to the `graph.search` API and returns a [context block](/retrieving-memory#retrieving-zeps-context-block), raw facts, and historical chat messages, providing everything needed for your agent's prompts.
</Tip>

<CodeBlocks>
  ```python Python
  memory = zep.thread.get_user_context(thread_id=thread_id)
  rich.print(memory.context)
  ```

  ```typescript TypeScript
  const memory = await zep.thread.getUserContext(thread_id);
  console.log(memory.context);
  ```
</CodeBlocks>

```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
<FACTS>
  - SupportBot understands how disruptive the glitch in the AI art generation can be to Emily's artistic process. (2025-02-20 20:29:39 - present)
  - SupportBot sincerely apologizes to Emily for the frustration caused by the issues with the AI art generation. (2025-02-20 20:29:39 - present)
  - Emily has contacted SupportBot for assistance regarding issues she is experiencing. (2025-02-20 20:29:39 - present)
  - The user Emily reported a bug regarding the magic pen tool drawing goats instead of boats. (2024-03-16 14:20:00 - present)
  - The bug report has been escalated to the engineering team. (2024-03-16 14:27:00 - present)
  - Emily is a user of the AI art generation. (2025-02-20 20:29:39 - present)
  - user has the name of Emily Painter (2025-02-20 20:29:39 - present)
  - Emily5e57 is using the landscape generator. (2025-02-20 20:29:39 - 2025-02-20 20:29:39)
  - user has the id of Emily5e57 (2025-02-20 20:29:39 - present)
  - user has the email of Emily@painters.com (2025-02-20 20:29:39 - present)
  - Emily is furious about the stupid app. (2025-02-20 20:29:39 - present)
  - Emily claims that the AI art generation is completely broken. (2025-02-20 20:29:39 - present)
</FACTS>

# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
  - Emily Painter: Emily Painter contacted PaintWiz support for assistance, where she was welcomed by the support bot that inquired about the specific issues she was facing to provide better help.
  - Emily@painters.com: user with the email of Emily@painters.com
  - Emily5e57: Emily5e57, a user of the PaintWiz AI art generation tool, successfully processed a transaction of $99.99 on July 30, 2024, using a card ending in '1234'. However, she is experiencing
significant frustration with the application due to malfunctions, such as the landscape generator incorrectly transforming mountains into fountains and characters being depicted with six fingers. 
These issues have led her to question the reliability of the tool, and she considers it to be completely broken. Emily has reached out to PaintWiz support for assistance, as these problems are 
severely disrupting her artistic process.
  - PaintWiz support: PaintWiz is an AI art generation platform that provides tools for users to create art. Recently, a user named Emily reported significant issues with the service, claiming that
the AI art generation is not functioning properly. The support bot responded to her concerns, apologizing for the disruption to her artistic process and asking for more details about the specific 
tool or feature she was using. This interaction highlights PaintWiz's commitment to customer support, as they actively seek to assist users with their inquiries and problems related to their 
products.
  - SupportBot: A support agent named Emily addressed a user's report about a bug in a drawing application where the magic pen tool incorrectly produced goats instead of boats. After confirming the
issue, she escalated it to the engineering team and suggested a temporary workaround of manually selecting the boat shape. Meanwhile, SupportBot, a virtual assistant for PaintWiz, also assisted 
another user named Emily who was frustrated with the AI art generation feature, acknowledging her concerns and requesting more details to help resolve the problem.
  - AI art generation: Emily, a user, expressed her frustration regarding the AI art generation, stating that it is completely broken.
  - options: The user reported a bug with the magic pen tool, stating that when attempting to draw boats, the tool instead draws goats. The support agent acknowledged the issue and requested more 
details about how the user was utilizing the tool. The user explained that they select the magic pen and draw a boat shape, but it gets replaced with goats. The support agent confirmed they would 
escalate the issue to the engineering team and suggested that the user manually select the boat shape from the options instead of drawing it with the pen. The user expressed hope for a quick 
resolution.
</ENTITIES>
```

<CodeBlocks>
  ```python Python
  rich.print(memory.messages)
  ```

  ```typescript TypeScript
  console.log(memory.messages);
  ```
</CodeBlocks>

```text
[
    Message(
        content='Hello Emily, welcome to PaintWiz support. How can I assist you today?',
        created_at='2025-02-20T20:29:39.08846Z',
        metadata=None,
        name='SupportBot',
        role='assistant',
        token_count=0,
        updated_at='0001-01-01T00:00:00Z',
        uuid_='e2b86f93-84d6-4270-adbc-e421f39b6f90'
    ),
    Message(
        content="I'm absolutely furious! Your AI art generation is completely broken!",
        created_at='2025-02-20T20:29:39.08846Z',
        metadata=None,
        name='Emily',
        role='user',
        token_count=0,
        updated_at='0001-01-01T00:00:00Z',
        uuid_='ec39e501-6dcc-4f8c-b300-f586d66005d8'
    )
]
```

We can also use the [graph API](/searching-the-graph) to search edges/facts for arbitrary text. This API offers more options, including the ability to search node summaries and various re-rankers.

<CodeBlocks>
  ```python Python
  r = zep.graph.search(user_id=user_id, query="Why are there so many goats?", limit=4, scope="edges")
  rich.print(r.edges)
  ```

  ```typescript TypeScript
  const r = await zep.graph.search({
    userId: user_id,
    query: "Why are there so many goats?",
    limit: 4,
    scope: "edges"
  });
  console.log(r.edges);
  ```
</CodeBlocks>

```text
[
    EntityEdge(
        created_at='2025-02-20T20:31:33.771566Z',
        episodes=['60d1d20e-ed6c-4966-b1da-3f4ca274a524'],
        expired_at=None,
        fact='The magic pen tool draws goats instead of boats when used by Emily.',
        invalid_at=None,
        name='DRAWS_INSTEAD_OF',
        source_node_uuid='e337522d-3a62-4c45-975d-904e1ba25667',
        target_node_uuid='9814a57f-53a4-4d4a-ad5a-15331858ce18',
        uuid_='022687b6-ae08-4fef-9d6e-17afb07acdea',
        valid_at='2025-02-20T20:29:40.217412Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:31:33.771528Z',
        episodes=['60d1d20e-ed6c-4966-b1da-3f4ca274a524'],
        expired_at=None,
        fact='The user Emily reported a bug regarding the magic pen tool drawing goats instead of boats.',
        invalid_at=None,
        name='REPORTED_BY',
        source_node_uuid='36f5c5c6-eb16-4ebb-9db0-fd34809482f5',
        target_node_uuid='cff4e758-d1a4-4910-abe7-20101a1f0d77',
        uuid_='5c3124ec-b4a3-4564-a38f-02338e3db4c4',
        valid_at='2024-03-16T14:20:00Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:30:19.910797Z',
        episodes=['ff9eba8b-9e90-4765-a0ce-15eb44410f70'],
        expired_at=None,
        fact='The stupid app generates mountains.',
        invalid_at=None,
        name='GENERATES',
        source_node_uuid='b6e5a0ee-8823-4647-b536-5e6af0ba113a',
        target_node_uuid='43aaf7c9-628c-4bf0-b7cb-02d3e9c1a49c',
        uuid_='3514a3ad-1ed5-42c7-9f70-02834e8904bf',
        valid_at='2025-02-20T20:29:39.08846Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:30:19.910816Z',
        episodes=['ff9eba8b-9e90-4765-a0ce-15eb44410f70'],
        expired_at=None,
        fact='The stupid app keeps turning mountains into fountains.',
        invalid_at=None,
        name='TRANSFORMS_INTO',
        source_node_uuid='43aaf7c9-628c-4bf0-b7cb-02d3e9c1a49c',
        target_node_uuid='0c90b42c-2b9f-4998-aa67-cc968f9002d3',
        uuid_='2f113810-3597-47a4-93c5-96d8002366fa',
        valid_at='2025-02-20T20:29:39.08846Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    )
]
```

## Creating a Simple Chatbot

In the next cells, Emily starts a new chat thread with a support agent and complains that she can't log in. Our simple chatbot will, given relevant facts retrieved from Zep's graph, respond accordingly.

Here, the support agent is provided with Emily's billing information and account status, which Zep retrieves as most relevant to Emily's login issue.

<CodeBlocks>
  ```python Python
  new_thread_id = str(uuid.uuid4())

  emily_message = "Hi, I can't log in!"

  # We start a new thread indicating that Emily has started a new chat with the support agent.
  zep.thread.create(user_id=user_id, thread_id=new_thread_id)

  # We need to add the Emily's message to the thread in order for thread.get_user_context to return
  # relevant facts related to the message
  zep.thread.add_messages(
      thread_id=new_thread_id,
      messages=[Message(role="user", name=user_name, content=emily_message)],
  )
  ```

  ```typescript TypeScript
  const new_thread_id = uuidv4();
  const emily_message = "Hi, I can't log in!";

  // We start a new thread indicating that Emily has started a new chat with the support agent.
  await zep.thread.create({
    userId: user_id,
    threadId: new_thread_id
  });

  // We need to add the Emily's message to the thread in order for thread.get_user_context to return
  // relevant facts related to the message
  await zep.thread.addMessages(new_thread_id, {
    messages: [{
      role: "user",
      name: user_name,
      content: emily_message
    }]
  });
  ```
</CodeBlocks>

<CodeBlocks>
  ```python Python
  system_message = """
  You are a customer support agent. Carefully review the facts about the user below and respond to the user's question.
  Be helpful and friendly.
  """

  memory = zep.thread.get_user_context(thread_id=new_thread_id)

  messages = [
      {
          "role": "system",
          "content": system_message,
      },
      {
          "role": "assistant",
          # The context field is an opinionated string that contains facts and entities relevant to the current conversation.
          "content": memory.context,
      },
      {
          "role": "user",
          "content": emily_message,
      },
  ]

  response = oai_client.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages,
      temperature=0,
  )

  print(response.choices[0].message.content)
  ```

  ```typescript TypeScript
  const system_message = `
  You are a customer support agent. Carefully review the facts about the user below and respond to the user's question.
  Be helpful and friendly.
  `;

  const new_memory = await zep.thread.getUserContext(new_thread_id);

  const messages = [
    {
      role: "system" as const,
      content: system_message,
    },
    {
      role: "assistant" as const,
      // The context field is an opinionated string that contains facts and entities relevant to the current conversation.
      content: new_memory.context || "",
    },
    {
      role: "user" as const,
      content: emily_message,
    },
  ];

  const response = await oai_client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: messages,
    temperature: 0,
  });

  console.log(response.choices[0].message.content);
  ```
</CodeBlocks>

```text
Hi Emily! I'm here to help you. It looks like your account is currently suspended due to a payment failure. This might be the reason you're unable to log in. 

The last transaction on your account failed because the card you were using has expired. If you update your payment information, we can help you get your account reactivated. Would you like assistance with that?
```

Let's look at the Context Block Zep retrieved for the above `thread.get_user_context` call.

<CodeBlocks>
  ```python Python
  rich.print(memory.context)
  ```

  ```typescript TypeScript
  console.log(new_memory.context);
  ```
</CodeBlocks>

```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
<FACTS>
  - Account with ID 'Emily1c2e' has a status of 'suspended'. (2025-02-24 23:24:29 - present)
  - user has the id of Emily1c2e (2025-02-24 23:24:29 - present)
  - User with ID 'Emily1c2e' has an account with ID 'Emily1c2e'. (2025-02-24 23:24:29 - present)
  - The bug report has been escalated to the engineering team. (2024-03-16 14:27:00 - present)
  - user has the name of Emily Painter (2025-02-24 23:24:29 - present)
  - Emily is the person being assisted by SupportBot. (2025-02-24 23:24:28 - present)
  - Emily1c2e is using the character creator. (2025-02-24 23:24:28 - present)
  - The reason for the account status 'suspended' is 'payment failure'. (2025-02-24 23:24:29 - present)
  - SupportBot is part of PaintWiz support. (2025-02-24 23:24:28 - present)
  - user has the email of Emily@painters.com (2025-02-24 23:24:29 - present)
  - Emily is a user of PaintWiz. (2025-02-24 23:24:28 - present)
  - The support agent suggested that Emily manually select the boat shape from the options. (2025-02-24 23:24:29 - 
present)
  - All the people in Emily1c2e's drawings have six fingers. (2025-02-24 23:24:28 - present)
  - Emily1c2e is using the landscape generator. (2025-02-24 23:24:28 - present)
  - Emily is a user of the AI art generation. (2025-02-24 23:24:28 - present)
  - Emily states that the AI art generation is completely broken. (2025-02-24 23:24:28 - present)
  - The magic pen tool draws goats instead of boats when used by Emily. (2025-02-24 23:24:29 - present)
  - Emily1c2e tries to draw mountains. (2025-02-24 23:24:28 - present)
</FACTS>

# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
  - goats: In a recent support interaction, a user reported a bug with the magic pen tool in a drawing application,
where attempting to draw boats resulted in the tool drawing goats instead. The user, Emily, described the issue, 
stating that whenever she selects the magic pen and draws a boat shape, it is replaced with a goat shape. The 
support agent acknowledged the problem and confirmed it would be escalated to the engineering team for resolution. 
In the meantime, the agent suggested that Emily could manually select the boat shape from the available options 
instead of using the pen tool. Emily expressed her hope for a quick fix to the issue.
  - failure_reason: Two transactions failed due to expired cards: one on September 15, 2024, and another on August 
30, 2024, for the amount of $99.99 associated with account ID 'Emily1c2e'.
  - status: User account "Emily1c2e" is suspended due to a payment failure. A transaction of $99.99 on September 
15, 2024, failed because the card ending in "1234" had expired. This card had previously been used successfully for
the same amount on July 30, 2024, but a failure on August 30, 2024, resulted in the account's suspension.
  - bug: A user reported a bug with the magic pen tool, stating that when attempting to draw boats, the tool 
instead draws goats. The support agent acknowledged the issue and requested more details about how the user was 
utilizing the tool. The user explained that they select the magic pen and draw a boat shape, but it gets replaced 
with goats. The support agent confirmed the bug and stated that it would be escalated to the engineering team for 
resolution. In the meantime, they suggested that the user manually select the boat shape from the options instead 
of using the pen. The user expressed hope for a quick fix.
  - user_id: Emily reported a bug with the magic pen tool in a drawing application, where attempting to draw boats 
resulted in goats being drawn instead. A support agent acknowledged the issue and requested more details. Emily 
explained her process, and the agent confirmed the bug, stating it would be escalated to the engineering team. As a
temporary workaround, the agent suggested manually selecting the boat shape. Emily expressed hope for a quick 
resolution. Additionally, it was noted that another user, identified as "Emily1c2e," has a suspended account due to
a payment failure.
  - people: Emily is frustrated with the AI art generation feature of PaintWiz, specifically mentioning that the 
people in her drawings are depicted with six fingers, which she finds ridiculous.
  - character creator: Emily is experiencing significant issues with the character creator feature of the app. She 
reports that when using the landscape generator and character creator, the app is malfunctioning, resulting in 
bizarre outcomes such as people in her drawings having six fingers. Emily expresses her frustration, stating that 
the AI art generation is completely broken and is not functioning as expected.
</ENTITIES>
```


# Users

## Overview

A User represents an individual interacting with your application. Each User can have multiple Threads associated with them, allowing you to track and manage their interactions over time. Additionally, each user has an associated User Graph which stores the memory for that user.

The unique identifier for each user is their `UserID`. This can be any string value, such as a username, email address, or UUID.

In the following sections, you will learn how to manage Users and their associated Threads.

<Note>
  **Users Enable Simple User Privacy Management**

  Deleting a User will delete all Threads and thread artifacts associated with that User with a single API call, making it easy to handle Right To Be Forgotten requests.
</Note>

## Ensuring Your User Data Is Correctly Mapped to the Zep Knowledge Graph

<Tip>
  Adding your user's `email`, `first_name`, and `last_name` ensures that chat messages and business data are correctly mapped to the user node in the Zep knowledge graph.

  For e.g., if business data contains your user's email address, it will be related directly to the user node.
</Tip>

You can associate rich business context with a User:

* `user_id`: A unique identifier of the user that maps to your internal User ID.
* `email`: The user's email.
* `first_name`: The user's first name.
* `last_name`: The user's last name.

## Adding a User

You can add a new user by providing the user details.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(api_key=API_KEY)

  new_user = client.user.add(
      user_id=user_id,
      email="user@example.com",
      first_name="Jane",
      last_name="Smith",
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const user = await client.user.add({
    userId: userId,
    email: "user@example.com",
    firstName: "Jane",
    lastName: "Smith",
  });
  ```

  ```go Go
  import (
  	"context"
  	"log"

  	"github.com/getzep/zep-go/v3"
  	zepclient "github.com/getzep/zep-go/v3/client"
  	"github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(option.WithAPIKey(apiKey))

  newUser, err := client.User.Add(context.TODO(), &zep.CreateUserRequest{
  	UserID:    userID,
  	Email:     zep.String("user@example.com"),
  	FirstName: zep.String("Jane"),
  	LastName:  zep.String("Smith"),
  })
  if err != nil {
  	log.Fatalf("Failed to add user: %v", err)
  }
  ```
</CodeBlocks>

> Learn how to associate [Threads with Users](/threads)

## User Summary Instructions

User summary instructions customize how Zep generates the entity summary for each user in their knowledge graph. You can create up to 5 custom instructions per user, set of users, or project-wide. Each instruction consists of a `name` (unique identifier) and `text` (the instruction content, maximum 100 characters).

### Default instructions

Zep applies the following default instructions to generate user summaries when no custom instructions are specified:

1. What are the user's key personal and lifestyle details?
2. What are the user's important relationships or social connections?
3. What does the user do for work, study, or main pursuits?
4. What are the user's preferences, values, and recurring goals?
5. What procedural or interaction instructions has the user given for how the AI should assist them?

These default instructions ensure comprehensive user summaries that capture essential information across personal, professional, and interaction contexts.

### Custom instructions

Instructions are managed through dedicated methods that allow you to add, list, and delete them. You can apply instructions to specific users by providing user IDs, or set them as project-wide defaults by omitting user IDs.

<Tip>
  **Best practices for writing instructions**: Instructions should be focused and specific, designed to elicit responses that can be answered in a sentence or two. Phrasing instructions as questions is often an effective way to get accurate and succinct responses.
</Tip>

<Note>
  User summary instructions do not apply when using `graph.add_batch()` or `thread.add_messages_batch()`.
</Note>

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep
  from zep_cloud.types import UserInstruction

  client = Zep(api_key=API_KEY)

  # Add instructions for specific users
  client.user.add_user_summary_instructions(
      instructions=[
          UserInstruction(
              name="professional_background",
              text="What are the user's key professional skills and career achievements?",
          )
      ],
      user_ids=[user_id],
  )

  # Add project-wide default instructions (applied to all users without custom instructions)
  client.user.add_user_summary_instructions(
      instructions=[
          UserInstruction(
              name="communication_style",
              text="How does the user prefer to receive information and assistance?",
          )
      ],
  )

  # List instructions for a user
  instructions = client.user.list_user_summary_instructions(user_id=user_id)

  # Delete specific instructions for a user
  client.user.delete_user_summary_instructions(
      instruction_names=["professional_background"],
      user_ids=[user_id],
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Add instructions for specific users
  await client.user.addUserSummaryInstructions({
    instructions: [
      {
        name: "professional_background",
        text: "What are the user's key professional skills and career achievements?",
      }
    ],
    userIds: [userId],
  });

  // Add project-wide default instructions (applied to all users without custom instructions)
  await client.user.addUserSummaryInstructions({
    instructions: [
      {
        name: "communication_style",
        text: "How does the user prefer to receive information and assistance?",
      }
    ],
  });

  // List instructions for a user
  const instructions = await client.user.listUserSummaryInstructions({
    userId: userId,
  });

  // Delete specific instructions for a user
  await client.user.deleteUserSummaryInstructions({
    instructionNames: ["professional_background"],
    userIds: [userId],
  });
  ```

  ```go Go
  import (
  	"context"
  	"log"

  	"github.com/getzep/zep-go/v3"
  	zepclient "github.com/getzep/zep-go/v3/client"
  	"github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(option.WithAPIKey(apiKey))

  // Add instructions for specific users
  _, err := client.User.AddUserSummaryInstructions(context.TODO(), &zep.ApidataAddUserInstructionsRequest{
  	Instructions: []*zep.UserInstruction{
  		{
  			Name: "professional_background",
  			Text: "What are the user's key professional skills and career achievements?",
  		},
  	},
  	UserIDs: []string{userID},
  })
  if err != nil {
  	log.Fatalf("Failed to add user summary instructions: %v", err)
  }

  // Add project-wide default instructions (applied to all users without custom instructions)
  _, err = client.User.AddUserSummaryInstructions(context.TODO(), &zep.ApidataAddUserInstructionsRequest{
  	Instructions: []*zep.UserInstruction{
  		{
  			Name: "communication_style",
  			Text: "How does the user prefer to receive information and assistance?",
  		},
  	},
  })
  if err != nil {
  	log.Fatalf("Failed to add default instructions: %v", err)
  }

  // List instructions for a user
  instructions, err := client.User.ListUserSummaryInstructions(context.TODO(), &zep.ApidataListUserInstructionsRequest{
  	UserID: userID,
  })
  if err != nil {
  	log.Fatalf("Failed to list instructions: %v", err)
  }

  // Delete specific instructions for a user
  _, err = client.User.DeleteUserSummaryInstructions(context.TODO(), &zep.ApidataDeleteUserInstructionsRequest{
  	InstructionNames: []string{"professional_background"},
  	UserIDs:          []string{userID},
  })
  if err != nil {
  	log.Fatalf("Failed to delete instructions: %v", err)
  }
  ```
</CodeBlocks>

### Utilizing user summary

You can utilize the default or custom user summary by retrieving the user node, getting the summary of that node, and including it in your context block. See [this example](/cookbook/customize-your-context-block#example-4-using-user-summary-in-context-block) for a complete implementation.

## Getting a User

You can retrieve a user by their ID.

<CodeBlocks>
  ```python Python
  user = client.user.get("user123")
  ```

  ```typescript TypeScript
  const user = await client.user.get("user123");
  ```

  ```go Go
  user, err := client.User.Get(context.TODO(), "user123")
  if err != nil {
  	log.Fatalf("Failed to get user: %v", err)
  }
  ```
</CodeBlocks>

## Updating a User

You can update a user's details by providing the updated user details.

<CodeBlocks>
  ```python Python
  updated_user = client.user.update(
      user_id=user_id,
      email="updated_user@example.com",
      first_name="Jane",
      last_name="Smith",
  )
  ```

  ```typescript TypeScript
  const updatedUser = await client.user.update(userId, {
    email: "updated_user@example.com",
    firstName: "Jane",
    lastName: "Smith",
    metadata: { foo: "updated_bar" },
  });
  ```

  ```go Go
  updatedUser, err := client.User.Update(context.TODO(), userID, &zep.UpdateUserRequest{
  	Email:     zep.String("updated_user@example.com"),
  	FirstName: zep.String("Jane"),
  	LastName:  zep.String("Smith"),
  	Metadata: map[string]interface{}{
  		"foo": "updated_bar",
  	},
  })
  if err != nil {
  	log.Fatalf("Failed to update user: %v", err)
  }
  ```
</CodeBlocks>

## Deleting a User

You can delete a user by their ID.

<CodeBlocks>
  ```python Python
  client.user.delete("user123")
  ```

  ```typescript TypeScript
  await client.user.delete("user123");
  ```

  ```go Go
  _, err := client.User.Delete(context.TODO(), "user123")
  if err != nil {
  	log.Fatalf("Failed to delete user: %v", err)
  }
  ```
</CodeBlocks>

## Getting a User's Threads

You can retrieve all Threads for a user by their ID.

<CodeBlocks>
  ```python Python
  threads = client.user.get_threads("user123")
  ```

  ```typescript TypeScript
  const threads = await client.user.getThreads("user123");
  ```

  ```go Go
  threads, err := client.User.GetThreads(context.TODO(), "user123")
  if err != nil {
  	log.Fatalf("Failed to get user threads: %v", err)
  }
  ```
</CodeBlocks>

## Listing Users

You can list all users, with optional limit and cursor parameters for pagination.

<CodeBlocks>
  ```python Python
  # List the first 10 users
  result = client.user.list_ordered(page_size=10, page_number=1)
  ```

  ```typescript TypeScript
  // List the first 10 users
  const result = await client.user.listOrdered({
    pageSize: 10,
    pageNumber: 1,
  });
  ```

  ```go Go
  // List the first 10 users
  result, err := client.User.ListOrdered(context.TODO(), &zep.UserListOrderedRequest{
  	PageSize:   zep.Int(10),
  	PageNumber: zep.Int(1),
  })
  if err != nil {
  	log.Fatalf("Failed to list users: %v", err)
  }
  ```
</CodeBlocks>

## Get the User Node

You can also retrieve the user's node from their graph:

<CodeBlocks>
  ```python Python
  results = client.user.get_node(user_id=user_id)
  user_node = results.node
  print(user_node.summary)
  ```

  ```typescript TypeScript
  const results = await client.user.getNode(userId);
  const userNode = results.node;
  console.log(userNode?.summary);
  ```

  ```go Go
  results, err := client.User.GetNode(context.TODO(), userID)
  if err != nil {
  	log.Fatalf("Failed to get user node: %v", err)
  }
  userNode := results.Node
  if userNode != nil && userNode.Summary != nil {
  	log.Printf("User summary: %s", *userNode.Summary)
  }
  ```
</CodeBlocks>

The user node might be used to get a summary of the user or to get facts related to the user (see ["How to find facts relevant to a specific node"](/cookbook/how-to-find-facts-relevant-to-a-specific-node)).

## Default Ontology for Users

User graphs utilize Zep's default ontology, consisting of default entity types and default edge types that affect how the graph is built. You can read more about default and custom graph ontology [here](/graph/customizing-graph-structure).

### Definition

Each user graph comes with default entity and edge types that help classify and structure information extracted from conversations. [View the full default ontology definition](/graph/customizing-graph-structure#default-entity-and-edge-types).

### Disabling Default Ontology

You can disable the default entity and edge types for specific users if you need precise control over your graph structure. [Learn how to disable the default ontology](/graph/customizing-graph-structure#disabling-default-ontology).


# Threads

## Overview

Threads represent a conversation. Each [User](/users) can have multiple threads, and each thread is a sequence of chat messages.

Chat messages are added to threads using [`thread.add_messages`](/adding-memory#adding-messages), which both adds those messages to the thread history and ingests those messages into the user-level knowledge graph. The user knowledge graph contains data from all of that user's threads to create an integrated understanding of the user.

<Note>
  The knowledge graph does not separate the data from different threads, but integrates the data together to create a unified picture of the user. So the [get thread user context](/sdk-reference/thread/get-user-context) endpoint and the associated [`thread.get_user_context`](/retrieving-memory#retrieving-zeps-context-block) method don't return memory derived only from that thread, but instead return whatever user-level memory is most relevant to that thread, based on the thread's most recent messages.
</Note>

## Adding a Thread

`threadIds` are arbitrary identifiers that you can map to relevant business objects in your app, such as users or a
conversation a user might have with your app. Before you create a thread, make sure you have [created a user](/users#adding-a-user) first. Then create a thread with:

<CodeBlocks>
  ```python Python
  client = Zep(
      api_key=API_KEY,
  )
  thread_id = uuid.uuid4().hex # A new thread identifier

  client.thread.create(
      thread_id=thread_id,
      user_id=user_id,
  )
  ```

  ```typescript TypeScript
  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const threadId: string = uuid.v4(); // Generate a new thread identifier

  await client.thread.create({
    threadId: threadId,
    userId: userId,
  });
  ```

  ```go Go
  import (
  	"context"
  	"log"

  	"github.com/getzep/zep-go/v3"
  	zepclient "github.com/getzep/zep-go/v3/client"
  	"github.com/getzep/zep-go/v3/option"
  	"github.com/google/uuid"
  )

  client := zepclient.NewClient(option.WithAPIKey(apiKey))

  threadID := uuid.New().String() // Generate a new thread identifier

  _, err := client.Thread.Create(context.TODO(), &zep.CreateThreadRequest{
  	ThreadID: threadID,
  	UserID:   userID,
  })
  if err != nil {
  	log.Fatalf("Failed to create thread: %v", err)
  }
  ```
</CodeBlocks>

## Getting Messages of a Thread

<CodeBlocks>
  ```python Python
  messages = client.thread.get(thread_id)
  ```

  ```typescript TypeScript
  const messages = await client.thread.get(threadId);
  ```

  ```go Go
  messages, err := client.Thread.Get(context.TODO(), threadID, &zep.ThreadGetRequest{})
  if err != nil {
  	log.Fatalf("Failed to get thread messages: %v", err)
  }
  ```
</CodeBlocks>

## Deleting a Thread

Deleting a thread deletes it and its associated messages. It does not however delete the associated data in the user's knowledge graph. To remove data from the graph, see [deleting data from the graph](/deleting-data-from-the-graph).

<CodeBlocks>
  ```python Python
  client.thread.delete(thread_id)
  ```

  ```typescript TypeScript
  await client.thread.delete(threadId);
  ```

  ```go Go
  _, err := client.Thread.Delete(context.TODO(), threadID)
  if err != nil {
  	log.Fatalf("Failed to delete thread: %v", err)
  }
  ```
</CodeBlocks>

## Listing Threads

You can list all Threads in the Zep Memory Store with page\_size and page\_number parameters for pagination.

<CodeBlocks>
  ```python Python
  # List the first 10 Threads
  result = client.thread.list_all(page_size=10, page_number=1)
  for thread in result.threads:
      print(thread)
  ```

  ```typescript TypeScript
  // List the first 10 Threads
  const { threads } = await client.thread.listAll({
    pageSize: 10,
    pageNumber: 1,
  });
  console.log("First 10 Threads:");
  threads.forEach((thread) => console.log(thread));
  ```

  ```go Go
  // List the first 10 Threads
  result, err := client.Thread.ListAll(context.TODO(), &zep.ThreadListAllRequest{
  	PageSize:   zep.Int(10),
  	PageNumber: zep.Int(1),
  })
  if err != nil {
  	log.Fatalf("Failed to list threads: %v", err)
  }
  for _, thread := range result.Threads {
  	log.Printf("%+v\n", thread)
  }
  ```
</CodeBlocks>

## Automatic Cache Warming

When you create a new thread, Zep automatically warms the cache for that user's graph data in the background. This optimization improves query latency for graph operations on newly created threads by pre-loading the user's data into the hot cache tier.

The warming operation runs asynchronously and does not block the thread creation response. No additional action is required on your part—this happens automatically whenever you create a thread for a user with an existing graph.

For more information about Zep's multi-tier caching architecture and manual cache warming, see [Warming the User Cache](/performance#warming-the-user-cache).


# Adding Memory

> Learn how to add chat history and messages to Zep's memory.

You can add both messages and business data to User Graphs.

## Adding Messages

Add your chat history to Zep using the `thread.add_messages` method. `thread.add_messages` is thread-specific and expects data in chat message format, including a `name` (e.g., user's real name), `role` (AI, human, tool), and message `content`. Zep stores the chat history and builds a user-level knowledge graph from the messages.

<Tip>
  For best results, add chat history to Zep on every chat turn. That is, add both the AI and human messages in a single operation and in the order that the messages were created.
</Tip>

### Basic example

The example below adds messages to Zep's memory for the user in the given thread:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep
  from zep_cloud.types import Message

  zep_client = Zep(
      api_key=API_KEY,
  )

  messages = [
      Message(
          name="Jane",
          role="user",
          content="Who was Octavia Butler?",
      )
  ]

  response = zep_client.thread.add_messages(thread_id, messages=messages)
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";
  import type { Message } from "@getzep/zep-cloud/api";

  const zepClient = new ZepClient({
    apiKey: API_KEY,
  });

  const messages: Message[] = [
      { name: "Jane", role: "user", content: "Who was Octavia Butler?" },
  ];

  const response = await zepClient.thread.addMessages(threadId, { messages });
  ```

  ```go Go
  import (
      v3 "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
  )

  zepClient := zepclient.NewClient(
      option.WithAPIKey("<YOUR_API_KEY>"),
  )
  response, err := zepClient.Thread.AddMessages(
      context.TODO(),
      "threadId",
      &v3.AddThreadMessagesRequest{
          Messages: []*v3.Message{
              {
                  Name: v3.String("Jane"),
                  Role: "user",
                  Content: "Who was Octavia Butler?",
              },
          },
      },
  )
  ```
</CodeBlocks>

You can find additional arguments to `thread.add_messages` in the [SDK reference](/sdk-reference/thread/add-messages). Notably, for latency sensitive applications, you can set `return_context` to true which will make `thread.add_messages` return a context block in the way that `thread.get_user_context` does (discussed below).

### Ignore assistant messages

You can also pass in a list of roles to ignore when adding messages to a User Graph using the `ignore_roles` argument. For example, you may not want assistant messages to be added to the user graph; providing the assistant messages in the `thread.add_messages` call while setting `ignore_roles` to include "assistant" will make it so that only the user messages are ingested into the graph, but the assistant messages are still used to contextualize the user messages. This is important in case the user message itself does not have enough context, such as the message "Yes." Additionally, the assistant messages will still be added to the thread's message history.

<CodeBlocks>
  ```python Python
  response = zep_client.thread.add_messages(
      thread_id,
      messages=messages,
      ignore_roles=["assistant"]
  )
  ```

  ```typescript TypeScript
  const response = await zepClient.thread.addMessages(threadId, {
      messages,
      ignoreRoles: ["assistant"]
  });
  ```

  ```go Go
  response, err := zepClient.Thread.AddMessages(
      context.TODO(),
      "threadId",
      &v3.AddThreadMessagesRequest{
          Messages: messages,
          IgnoreRoles: []string{"assistant"},
      },
  )
  ```
</CodeBlocks>

### Creating messages with metadata

Messages can have metadata attached to store additional information like sentiment scores, source identifiers, processing flags, or other custom data. Metadata is preserved when getting threads, individual messages, and when searching episodes.

<Note>
  Message metadata is currently supported only for thread messages. Messages added via the `graph.add` API do not support metadata. Zep does not support filtering or searching over message metadata.
</Note>

You can attach metadata when creating messages by including a `metadata` field in your message objects:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep
  from zep_cloud.types import Message

  zep_client = Zep(
      api_key=API_KEY,
  )

  messages = [
      Message(
          name="Jane",
          role="user",
          content="I need help with my account.",
          metadata={
              "sentiment": "frustrated",
              "source": "mobile_app",
              "priority": "high"
          }
      )
  ]

  response = zep_client.thread.add_messages(thread_id, messages=messages)
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";
  import type { Message } from "@getzep/zep-cloud/api";

  const zepClient = new ZepClient({
    apiKey: API_KEY,
  });

  const messages: Message[] = [
      {
          name: "Jane",
          role: "user",
          content: "I need help with my account.",
          metadata: {
              sentiment: "frustrated",
              source: "mobile_app",
              priority: "high"
          }
      },
  ];

  const response = await zepClient.thread.addMessages(threadId, { messages });
  ```

  ```go Go
  import (
      v3 "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
  )

  zepClient := zepclient.NewClient(
      option.WithAPIKey("<YOUR_API_KEY>"),
  )
  response, err := zepClient.Thread.AddMessages(
      context.TODO(),
      "threadId",
      &v3.AddThreadMessagesRequest{
          Messages: []*v3.Message{
              {
                  Name: v3.String("Jane"),
                  Role: "user",
                  Content: "I need help with my account.",
                  Metadata: map[string]interface{}{
                      "sentiment": "frustrated",
                      "source":    "mobile_app",
                      "priority":  "high",
                  },
              },
          },
      },
  )
  ```
</CodeBlocks>

### Updating message metadata

You can update the metadata of an existing message using the message UUID. This is useful for adding or modifying metadata after a message has been created, such as updating sentiment analysis results or processing status.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  zep_client = Zep(
      api_key=API_KEY,
  )

  # Update message metadata
  updated_message = zep_client.thread.message.update(
      message_uuid="message-uuid-here",
      metadata={
          "sentiment": "positive",
          "resolved": True,
          "resolution_time": "2m 30s"
      }
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const zepClient = new ZepClient({
    apiKey: API_KEY,
  });

  // Update message metadata
  const updatedMessage = await zepClient.thread.message.update(
      "message-uuid-here",
      {
          metadata: {
              sentiment: "positive",
              resolved: true,
              resolutionTime: "2m 30s"
          }
      }
  );
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
      "github.com/getzep/zep-go/v3/thread"
  )

  zepClient := zepclient.NewClient(
      option.WithAPIKey("<YOUR_API_KEY>"),
  )

  // Update message metadata
  updatedMessage, err := zepClient.Thread.Message.Update(
      context.TODO(),
      "message-uuid-here",
      &thread.ThreadMessageUpdate{
          Metadata: map[string]interface{}{
              "sentiment":       "positive",
              "resolved":        true,
              "resolution_time": "2m 30s",
          },
      },
  )
  if err != nil {
      // Handle error
  }
  ```
</CodeBlocks>

### Setting message timestamps

When creating messages via the API, you should provide the `created_at` timestamp in RFC3339 format. The `created_at` timestamp represents the time when the message was originally sent by the user. Setting the `created_at` timestamp is important to ensure the user's knowledge graph has accurate temporal understanding of user history (since this time is used in our fact invalidation process).

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep
  from zep_cloud.types import Message

  zep_client = Zep(
      api_key=API_KEY,
  )

  messages = [
      Message(
          created_at="2025-06-01T13:11:12Z",
          name="Jane",
          role="user",
          content="What's the weather like today?",
      )
  ]

  response = zep_client.thread.add_messages(thread_id, messages=messages)
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";
  import type { Message } from "@getzep/zep-cloud/api";

  const zepClient = new ZepClient({
    apiKey: API_KEY,
  });

  const messages: Message[] = [
      { 
          createdAt: "2025-06-01T13:11:12Z",
          name: "Jane", 
          role: "user", 
          content: "What's the weather like today?" 
      },
  ];

  const response = await zepClient.thread.addMessages(threadId, { messages });
  ```

  ```go Go
  import (
      v3 "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
  )

  zepClient := zepclient.NewClient(
      option.WithAPIKey("<YOUR_API_KEY>"),
  )
  response, err := zepClient.Thread.AddMessages(
      context.TODO(),
      "threadId",
      &v3.AddThreadMessagesRequest{
          Messages: []*v3.Message{
              {
                  CreatedAt: v3.String("2025-06-01T13:11:12Z"),
                  Name: v3.String("Jane"),
                  Role: "user",
                  Content: "What's the weather like today?",
              },
          },
      },
  )
  ```
</CodeBlocks>

### Message limits

When adding messages to a thread, there are limits on both the number of messages and message size:

* **Messages per call**: You can add at most 30 messages in a single `thread.add_messages` call
* **Message size limit**: Each message can be at most 2,500 characters

If you need to add more than 30 messages or have messages exceeding the character limits, you'll need to split them across multiple API calls or truncate the content accordingly. Our additional recommendations include:

* Have users attach documents rather than paste them into the message, and then process documents separately with `graph.add`
* Reduce the max message size for your users to match our max message size
* Optional: allow users to paste in documents with an auto detection algorithm that turns it into an attachment as opposed to part of the message

### Check when messages are finished processing

You can use the message UUIDs from the response to poll the messages and check when they are finished processing:

```python
response = zep_client.thread.add_messages(thread_id, messages=messages)
message_uuids = response.message_uuids
```

An example of this can be found in the [check data ingestion status cookbook](/cookbook/check-data-ingestion-status).

## Adding Business Data

You can also add JSON or unstructured text as memory to a User Graph using our [Graph API](/adding-data-to-the-graph).

## Customizing Memory Creation

Zep offers two ways to customize how memory is created. You can read more about these features at their guide pages:

* [**Custom entity and edge types**](/customizing-graph-structure#custom-entity-and-edge-types): Feature allowing use of Pydantic-like classes to customize creation/retrieval of entities and relations in the knowledge graph.
* [**User summary instructions**](/users#user-summary-instructions): Customize how Zep generates entity summaries for users in their knowledge graph with up to 5 custom instructions per user.


# Retrieving Memory

> Learn how to retrieve relevant context from a User Graph.

There are two ways to retrieve memory from a User Graph: using Zep's Context Block or searching the graph.

## Retrieving Zep's Context Block

Zep's Context Block is an optimized, automatically assembled string that you can directly provide as context to your agent. Zep's Context Block combines semantic search, full text search, and breadth first search to return context that is highly relevant to the user's current conversation slice, utilizing the past four messages.

The Context Block is returned by the `thread.get_user_context()` method. This method uses the latest messages of the *given thread* to search the (entire) User Graph and then returns the search results in the form of the Context Block.

Note that although `thread.get_user_context()` only requires a thread ID, it is able to return memory derived from any thread of that user. The thread is just used to determine what's relevant.

The `mode` parameter determines what form the Context Block takes (see below).

### Summarized Context Block (default)

This Context Block type returns a short summary of the relevant context. An LLM is used to create the summary, but if the LLM takes too long (more than a second), the basic Context Block is returned instead.

**Benefits:**

* Low token usage
* Easier for LLMs to understand

**Trade-offs:**

* Higher latency
* Some risk of missing important details

Example:

<CodeBlocks>
  ```python Python
  # Get memory for the thread
  memory = client.thread.get_user_context(thread_id=thread_id)

  # Access the context block (for use in prompts)
  context_block = memory.context
  print(context_block)
  ```

  ```typescript TypeScript
  // Get memory for the thread
  const memory = await client.thread.getUserContext(threadId);

  // Access the context block (for use in prompts)
  const contextBlock = memory.context;
  console.log(contextBlock);
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
  )

  // Get memory for the thread
  memory, err := client.Thread.GetUserContext(context.TODO(), threadId, nil)
  if err != nil {
      log.Fatal("Error getting memory:", err)
  }
  // Access the context block (for use in prompts)
  contextBlock := memory.Context
  fmt.Println(contextBlock)
  ```
</CodeBlocks>

```text
- On 2024-07-30, account Emily0e62 made a failed transaction of $99.99.
- The transaction failed due to the card with last four digits 1234.
- The failure reason was 'Card expired' as of 2024-09-15.
- Emily0e62 is a user account belonging to Emily Painter.
- On 2024-11-14, user account Emily0e62 was suspended due to payment failure.
- Since 2024-11-14, Emily Painter (Emily0e62) has experienced issues with logging in.
- As of the present, account Emily0e62 remains suspended and Emily continues to face login issues due to unresolved payment failure from an expired card.
```

### Basic Context Block (faster)

This Context Block type returns the relevant context in a more raw format, but faster.

**Benefits:**

* Lower latency (P95 \< 200ms)
* More detailed information preserved

**Trade-offs:**

* Higher token usage
* May be harder for some LLMs to parse

Example:

<CodeBlocks>
  ```python Python
  # Get memory for the thread
  memory = client.thread.get_user_context(thread_id=thread_id, mode="basic")

  # Access the context block (for use in prompts)
  context_block = memory.context
  print(context_block)
  ```

  ```typescript TypeScript
  // Get memory for the thread
  const memory = await client.thread.getUserContext(threadId, { mode: "basic" });

  // Access the context block (for use in prompts)
  const contextBlock = memory.context;
  console.log(contextBlock);
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
  )

  mode := "basic"
  // Get memory for the thread
  memory, err := client.Thread.GetUserContext(context.TODO(), threadId, &v3.ThreadGetUserContextRequest{
      Mode: &mode,
  })
  if err != nil {
      log.Fatal("Error getting memory:", err)
  }
  // Access the context block (for use in prompts)
  contextBlock := memory.Context
  fmt.Println(contextBlock)
  ```
</CodeBlocks>

```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges

# format: FACT (Date range: from - to)

<FACTS>
  - Emily is experiencing issues with logging in. (2024-11-14 02:13:19+00:00 -
    present) 
  - User account Emily0e62 has a suspended status due to payment failure. 
    (2024-11-14 02:03:58+00:00 - present) 
  - user has the id of Emily0e62 (2024-11-14 02:03:54 - present)
  - The failed transaction used a card with last four digits 1234. (2024-09-15
    00:00:00+00:00 - present)
  - The reason for the transaction failure was 'Card expired'. (2024-09-15
    00:00:00+00:00 - present)
  - user has the name of Emily Painter (2024-11-14 02:03:54 - present) 
  - Account Emily0e62 made a failed transaction of 99.99. (2024-07-30 
    00:00:00+00:00 - 2024-08-30 00:00:00+00:00)
</FACTS>

# These are the most relevant entities

# ENTITY_NAME: entity summary

<ENTITIES>
  - Emily0e62: Emily0e62 is a user account associated with a transaction,
    currently suspended due to payment failure, and is also experiencing issues
    with logging in. 
  - Card expired: The node represents the reason for the transaction failure, 
    which is indicated as 'Card expired'. 
  - Magic Pen Tool: The tool being used by the user that is malfunctioning. 
  - User: user 
  - Support Agent: Support agent responding to the user's bug report. 
  - SupportBot: SupportBot is the virtual assistant providing support to the user, 
    Emily, identified as SupportBot. 
  - Emily Painter: Emily is a user reporting a bug with the magic pen tool, 
    similar to Emily Painter, who is expressing frustration with the AI art
    generation tool and seeking assistance regarding issues with the PaintWiz app.
</ENTITIES>
```

### Getting the Context Block Sooner

You can get the Context Block sooner by passing in the `return_context=True` flag to the `thread.add_messages()` method, but it will always return the basic Context Block type. Read more about this in our [performance guide](/performance#get-the-context-block-sooner).

## Searching the Graph

You can also directly search a User Graph using our highly customizable `graph.search` method and construct a custom context block. Read more about this in our [Searching the Graph](/searching-the-graph) guide.

## Using Memory

### Provide the Context Block in Your System Prompt

Once you've retrieved the [Context Block](/retrieving-memory#retrieving-zeps-context-block), or [constructed your own context block](/cookbook/customize-your-context-block) by [searching the graph](/searching-the-graph), you can include this string in your system prompt:

| MessageType | Content                                                |
| ----------- | ------------------------------------------------------ |
| `System`    | Your system prompt <br /> <br /> `{Zep context block}` |
| `Assistant` | An assistant message stored in Zep                     |
| `User`      | A user message stored in Zep                           |
| ...         | ...                                                    |
| `User`      | The latest user message                                |

### Provide the Last 4 to 6 Messages of the Thread

You should also include the last 4 to 6 messages of the thread when calling your LLM provider. Because Zep's ingestion can take a few minutes, the context block may not include information from the last few messages; and so the context block acts as the "long-term memory," and the last few messages serve as the raw, short-term memory.


# Graph Overview

Zep's temporal knowledge graph powers its context engineering capabilities, including agent memory and Graph RAG. Zep's graph is built on [Graphiti](/graphiti/graphiti/overview), Zep's open-source temporal graph library, which is fully integrated into Zep. Developers do not need to interact directly with Graphiti or understand its underlying implementation.

<Card title="What is a Knowledge Graph?" icon="duotone chart-network">
  A knowledge graph is a network of interconnected facts, such as *"Kendra loves
  Adidas shoes."* Each fact is a *"triplet"* represented by two entities, or
  nodes (*"Kendra", "Adidas shoes"*), and their relationship, or edge
  (*"loves"*).

  <br />

  Knowledge Graphs have been explored extensively for information retrieval.
  What makes Zep unique is its ability to autonomously build temporal knowledge graphs
  while handling changing relationships and maintaining historical context.
</Card>

Zep automatically constructs a temporal knowledge graph for each of your users. The knowledge graph contains entities, relationships, and facts related to your user, while automatically handling changing relationships and facts over time.

Here's an example of how Zep might extract graph data from a chat message, and then update the graph once new information is available:

![graphiti intro slides](file:944922c0-87b1-4b85-8622-6254308407e5)

Each node and edge contains certain attributes - notably, a fact is always stored as an edge attribute. There are also datetime attributes for when the fact becomes valid and when it becomes invalid.

## Graph Data Structure

Zep's graph database stores data in three main types:

1. Entity edges (edges): Represent relationships between nodes and include semantic facts representing the relationship between the edge's nodes.
2. Entity nodes (nodes): Represent entities extracted from episodes, containing summaries of relevant information.
3. Episodic nodes (episodes): Represent raw data stored in Zep, either through chat history or the `graph.add` endpoint.

## Creating a Graph

Before you can work with graph data, you need to create a graph. Each graph is identified by a unique `graph_id` and can optionally include a name and description:

<CodeBlocks>
  ```python Python
  from zep_cloud import Zep

  client = Zep(api_key="YOUR_API_KEY")

  graph = client.graph.create(
      graph_id="unique-graph-id",
      name="Graph Name",
      description="This is a description."
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "zep-cloud";

  const client = new ZepClient({ apiKey: "YOUR_API_KEY" });

  const graph = await client.graph.create({
      graphId: "unique-graph-id",
      name: "Graph Name",
      description: "This is a description."
  });
  ```

  ```go Go
  import (
      "context"
      "fmt"
      "log"
      "github.com/getzep/zep-go/v3"
      v3client "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := v3client.NewClient(
      option.WithAPIKey("YOUR_API_KEY"),
  )

  name := "Graph Name"
  description := "This is a description."

  graph, err := client.Graph.Create(context.TODO(), &v3.CreateGraphRequest{
      GraphID:     "unique-graph-id",
      Name:        &name,
      Description: &description,
  })
  if err != nil {
      log.Fatal("Error creating graph:", err)
  }

  fmt.Println("Graph created:", graph)
  ```
</CodeBlocks>

## Working with the Graph

To learn more about interacting with Zep's graph, refer to the following sections:

* [Adding Data to the Graph](/v3/adding-data-to-the-graph): Learn how to add new data to the graph.
* [Reading Data from the Graph](/v3/reading-data-from-the-graph): Discover how to retrieve information from the graph.
* [Searching the Graph](/v3/searching-the-graph): Explore techniques for efficiently searching the graph.

These guides will help you leverage the full power of Zep's knowledge graph in your applications.


# Zep vs Graph RAG

> How Zep compares to traditional GraphRAG approaches

While traditional GraphRAG excels at static document summarization, Zep is designed for dynamic and frequently updated datasets with continuous data updates, temporal fact tracking, and sub-second query latency. This makes Zep particularly suitable for providing an agent with up-to-date knowledge about an object/system or user.

| Aspect                 | GraphRAG                              | Zep                                              |
| ---------------------- | ------------------------------------- | ------------------------------------------------ |
| Primary Use            | Static document summarization         | Dynamic data management                          |
| Data Handling          | Batch-oriented processing             | Continuous, incremental updates                  |
| Knowledge Structure    | Entity clusters & community summaries | Episodic data, semantic entities, communities    |
| Retrieval Method       | Sequential LLM summarization          | Hybrid semantic, keyword, and graph-based search |
| Adaptability           | Low                                   | High                                             |
| Temporal Handling      | Basic timestamp tracking              | Explicit bi-temporal tracking                    |
| Contradiction Handling | LLM-driven summarization judgments    | Temporal edge invalidation                       |
| Query Latency          | Seconds to tens of seconds            | Typically sub-second latency                     |
| Custom Entity Types    | No                                    | Yes, customizable                                |
| Scalability            | Moderate                              | High, optimized for large datasets               |


# Adding Data to the Graph

## Overview

<Warning>
  Requests to add data to the same graph are completed sequentially to ensure the graph is built correctly, and processing may be slow for large datasets. Use [batch ingestion](#add-batch-data) when adding large datasets such as backfills or document collections.
</Warning>

In addition to incorporating memory through chat history, Zep offers the capability to add data directly to the graph.
Zep supports three distinct data types: message, text, and JSON.

The message type is ideal for adding data in the form of chat messages that are not directly associated with a Zep [Thread's](/threads) chat history. This encompasses any communication with a designated speaker, such as emails or previous chat logs.

The text type is designed for raw text data without a specific speaker attribution. This category includes content from internal documents, wiki articles, or company handbooks. It's important to note that Zep does not process text directly from links or files.

The JSON type may be used to add any JSON document to Zep. This may include REST API responses or JSON-formatted business data.

You can add data to a graph by specifying a `graph_id`, or to a user graph by providing a `user_id`.

## Adding Message Data

Here's an example demonstrating how to add message data to the graph:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  message = "Paul (user): I went to Eric Clapton concert last night"

  new_episode = client.graph.add(
      user_id="user123",    # Optional: You can use graph_id instead of user_id
      type="message",       # Specify type as "message"
      data=message
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const message = "User: I really enjoy working with TypeScript and React";

  const newEpisode = await client.graph.add({
      userId: "user123",  // Optional: You can use graphId instead of userId
      type: "message",
      data: message
  });
  ```

  ```go Go
  import (
      "context"
      "log"

      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(apiKey),
  )

  message := "Paul (user): I went to Eric Clapton concert last night"
  userID := "user123"

  newEpisode, err := client.Graph.Add(context.TODO(), &zep.AddDataRequest{
      UserID: &userID,  // Optional: You can use GraphID instead of UserID
      Type:   zep.GraphDataTypeMessage,
      Data:   message,
  })
  if err != nil {
      log.Fatalf("Failed to add message data: %v", err)
  }
  ```
</CodeBlocks>

## Adding Text Data

Here's an example demonstrating how to add text data to the graph:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  new_episode = client.graph.add(
      user_id="user123",  # Optional: You can use graph_id instead of user_id
      type="text",        # Specify type as "text"
      data="The user is an avid fan of Eric Clapton"
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const newEpisode = await client.graph.add({
      userId: "user123",  // Optional: You can use graphId instead of userId
      type: "text",
      data: "The user is interested in machine learning and artificial intelligence"
  });
  ```

  ```go Go
  import (
      "context"
      "log"

      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(apiKey),
  )

  userID := "user123"

  newEpisode, err := client.Graph.Add(context.TODO(), &zep.AddDataRequest{
      UserID: &userID,  // Optional: You can use GraphID instead of UserID
      Type:   zep.GraphDataTypeText,
      Data:   "The user is an avid fan of Eric Clapton",
  })
  if err != nil {
      log.Fatalf("Failed to add text data: %v", err)
  }
  ```
</CodeBlocks>

## Adding JSON Data

Here's an example demonstrating how to add JSON data to the graph:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep
  import json

  client = Zep(
      api_key=API_KEY,
  )

  json_data = {"name": "Eric Clapton", "age": 78, "genre": "Rock"}
  json_string = json.dumps(json_data)
  new_episode = client.graph.add(
      user_id=user_id,  # Optional: You can use graph_id instead of user_id
      type="json",
      data=json_string,
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const jsonString = '{"name": "Eric Clapton", "age": 78, "genre": "Rock"}';
  const newEpisode = await client.graph.add({
      userId: userId,  // Optional: You can use graphId instead of userId
      type: "json",
      data: jsonString,
  });
  ```

  ```go Go
  import (
      "context"
      "encoding/json"
      "log"

      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(apiKey),
  )

  jsonData := map[string]interface{}{
      "name":  "Eric Clapton",
      "age":   78,
      "genre": "Rock",
  }
  jsonBytes, err := json.Marshal(jsonData)
  if err != nil {
      log.Fatalf("Failed to marshal JSON: %v", err)
  }
  jsonString := string(jsonBytes)

  userID := "user123"

  newEpisode, err := client.Graph.Add(context.TODO(), &zep.AddDataRequest{
      UserID: &userID,  // Optional: You can use GraphID instead of UserID
      Type:   zep.GraphDataTypeJSON,
      Data:   jsonString,
  })
  if err != nil {
      log.Fatalf("Failed to add JSON data: %v", err)
  }
  ```
</CodeBlocks>

## Data Size Limit and Chunking

The `graph.add` endpoint has a data size limit of 10,000 characters when adding data to the graph. If you need to add a document which is more than 10,000 characters, we recommend chunking the document as well as using Anthropic's contextualized retrieval technique. We have an example of this [here](https://blog.getzep.com/building-a-russian-election-interference-knowledge-graph/#:~:text=Chunking%20articles%20into%20multiple%20Episodes%20improved%20our%20results%20compared%20to%20treating%20each%20article%20as%20a%20single%20Episode.%20This%20approach%20generated%20more%20detailed%20knowledge%20graphs%20with%20richer%20node%20and%20edge%20extraction%2C%20while%20single%2DEpisode%20processing%20produced%20only%20high%2Dlevel%2C%20sparse%20graphs.). This example uses Graphiti, but the same patterns apply to Zep as well.

Additionally, we recommend using relatively small chunk sizes, so that Zep is able to capture all of the entities and relationships within a chunk. Using a larger chunk size may result in some entities and relationships not being captured.

## Adding Custom Fact/Node Triplets

You can also add manually specified fact/node triplets to the graph. You need only specify the fact, the target node name, and the source node name. Zep will then create a new corresponding edge and nodes, or use an existing edge/nodes if they exist and seem to represent the same nodes or edge you send as input. And if this new fact invalidates an existing fact, it will mark the existing fact as invalid and add the new fact triplet.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  client.graph.add_fact_triple(
      user_id=user_id,  # Optional: You can use graph_id instead of user_id
      fact="Paul met Eric",
      fact_name="MET",
      target_node_name="Eric Clapton",
      source_node_name="Paul",
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  await client.graph.addFactTriple({
    userId: userId,  // Optional: You can use graphId instead of userId
    fact: "Paul met Eric",
    factName: "MET",
    targetNodeName: "Eric Clapton",
    sourceNodeName: "Paul",
  });
  ```

  ```go Go
  import (
      "context"
      "log"

      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(apiKey),
  )

  userID := "user123"
  sourceNodeName := "Paul"

  _, err := client.Graph.AddFactTriple(context.TODO(), &v3.AddTripleRequest{
      UserID:         &userID,  // Optional: You can use GraphID instead of UserID
      Fact:           "Paul met Eric",
      FactName:       "MET",
      TargetNodeName: "Eric Clapton",
      SourceNodeName: &sourceNodeName,
  })
  if err != nil {
      log.Fatalf("Failed to add fact triple: %v", err)
  }
  ```
</CodeBlocks>

You can also specify the node summaries, edge temporal data, and UUIDs. See the [associated SDK reference](/sdk-reference/graph/add-fact-triple).

## Add Batch Data

You can add data in batches for faster processing when working with large datasets. To learn more about batch processing and implementation details, see [Adding Batch Data](adding-batch-data).

## Cloning Graphs

The `graph.clone` method allows you to create complete copies of graphs with new identifiers. This is useful for scenarios like creating test copies of user data, migrating user graphs to new identifiers, or setting up template graphs for new users.

<Note>
  The target graph must not exist - they will be created as part of the cloning operation. If no target ID is provided, one will be auto-generated and returned in the response.
</Note>

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  # Clone a graph to a new graph ID
  result = client.graph.clone(
      source_graph_id="graph_456",
      target_graph_id="graph_456_copy"  # Optional - will be auto-generated if not provided
  )

  print(f"Cloned graph to graph: {result.graph_id}")
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Clone a graph to a new graph ID
  const result = await client.graph.clone({
      sourceGraphId: "graph_456",
      targetGraphId: "graph_456_copy"  // Optional - will be auto-generated if not provided
  });

  console.log(`Cloned graph to graph: ${result.graphId}`);
  ```

  ```go Go
  import (
      "context"
      "fmt"
      "log"
      
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(apiKey),
  )

  // Clone a graph to a new graph ID
  sourceGraphID := "graph_456"
  targetGraphID := "graph_456_copy"  // Optional - will be auto-generated if not provided

  result, err := client.Graph.Clone(context.TODO(), &v3.CloneGraphRequest{
      SourceGraphID: &sourceGraphID,
      TargetGraphID: &targetGraphID,
  })
  if err != nil {
      log.Fatalf("Failed to clone graph: %v", err)
  }

  fmt.Printf("Cloned graph to graph: %s\n", *result.GraphID)
  ```
</CodeBlocks>

### Cloning User Graphs

Here's an example demonstrating how to clone a user graph:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  # Clone a user graph to a new user ID
  result = client.graph.clone(
      source_user_id="user_123",
      target_user_id="user_123_copy"  # Optional - will be auto-generated if not provided
  )

  print(f"Cloned graph to user: {result.user_id}")
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Clone a user graph to a new user ID
  const result = await client.graph.clone({
      sourceUserId: "user_123",
      targetUserId: "user_123_copy"  // Optional - will be auto-generated if not provided
  });

  console.log(`Cloned graph to user: ${result.userId}`);
  ```

  ```go Go
  import (
      "context"
      "fmt"
      "log"
      
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(apiKey),
  )

  // Clone a user graph to a new user ID
  sourceUserID := "user_123"
  targetUserID := "user_123_copy"  // Optional - will be auto-generated if not provided

  result, err := client.Graph.Clone(context.TODO(), &v3.CloneGraphRequest{
      SourceUserID: &sourceUserID,
      TargetUserID: &targetUserID,
  })
  if err != nil {
      log.Fatalf("Failed to clone graph: %v", err)
  }

  fmt.Printf("Cloned graph to user: %s\n", *result.UserID)
  ```
</CodeBlocks>

### Key Behaviors and Limitations

* **Target Requirements**: The target user or graph must not exist and will be created during the cloning operation
* **Auto-generation**: If no target ID is provided, Zep will auto-generate one and return it in the response
* **Node Modification**: The central user entity node in the cloned graph is updated with the new user ID, and all references in the node summary are updated accordingly

## Managing Your Data on the Graph

The `graph.add` method returns the [episode](/graphiti/graphiti/adding-episodes) that was created in the graph from adding that data. You can use this to maintain a mapping between your data and its corresponding episode in the graph and to delete specific data from the graph using the [delete episode](/deleting-data-from-the-graph#delete-an-episode) method.


# Searching the Graph

<Note title="Custom Context Blocks" icon="link">
  Graph search results should be used in conjunction with [Custom Context Blocks](/cookbook/customize-your-context-block) to create rich, contextual prompts for AI models. Custom context blocks allow you to format and structure the retrieved graph information, combining search results with conversation history and other relevant data to provide comprehensive context for your AI applications.

  Learn how to integrate graph search results into your context generation workflow for more effective AI interactions.
</Note>

## Introduction

Zep's graph search provides powerful hybrid search capabilities that combine semantic similarity with BM25 full-text search to find relevant information across your knowledge graph. This approach leverages the best of both worlds: semantic understanding for conceptual matches and full-text search for exact term matching. Additionally, you can optionally enable breadth-first search to bias results toward information connected to specific starting points in your graph.

### How It Works

* **Semantic similarity**: Converts queries into embeddings to find conceptually similar content
* **BM25 full-text search**: Performs traditional keyword-based search for exact matches
* **Breadth-first search** (optional): Biases results toward information connected to specified starting nodes, useful for contextual relevance
* **Hybrid results**: Combines and reranks results using sophisticated algorithms

### Graph Concepts

* **Nodes**: Connection points representing entities (people, places, concepts) discussed in conversations or added via the Graph API
* **Edges**: Relationships between nodes containing specific facts and interactions

The example below demonstrates a simple search:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query=query,
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: query,
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID: zep.String(userID),
      Query:  query,
  })
  ```
</CodeBlocks>

<Tip title="Best Practices" icon="magnifying-glass">
  Keep queries short: they are truncated at 400 characters. Long queries may increase latency without improving search quality.
  Break down complex searches into smaller, targeted queries. Use precise, contextual queries rather than generic ones
</Tip>

## Configurable Parameters

Zep provides extensive configuration options to fine-tune search behavior and optimize results for your specific use case:

| Parameter                          | Type    | Description                                                                                                                                                                                                                       | Default   | Required |
| ---------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | -------- |
| `graph_id`                         | string  | Search within a graph                                                                                                                                                                                                             | -         | Yes\*    |
| `user_id`                          | string  | Search within a user graph                                                                                                                                                                                                        | -         | Yes\*    |
| `query`                            | string  | Search text (max 400 characters)                                                                                                                                                                                                  | -         | Yes      |
| `scope`                            | string  | Search target: `"edges"`, `"nodes"`, or `"episodes"`                                                                                                                                                                              | `"edges"` | No       |
| `reranker`                         | string  | Reranking method: `"rrf"`, `"mmr"`, `"node_distance"`, `"episode_mentions"`, or `"cross_encoder"`                                                                                                                                 | `"rrf"`   | No       |
| `limit`                            | integer | Maximum number of results to return                                                                                                                                                                                               | `10`      | No       |
| `mmr_lambda`                       | float   | MMR diversity vs relevance balance (0.0-1.0)                                                                                                                                                                                      | -         | No†      |
| `center_node_uuid`                 | string  | Center node for distance-based reranking                                                                                                                                                                                          | -         | No‡      |
| `search_filters`                   | object  | Filter by entity types (`node_labels`), edge types (`edge_types`), exclude entity types (`exclude_node_labels`), exclude edge types (`exclude_edge_types`), or timestamps (`created_at`, `expired_at`, `invalid_at`, `valid_at`§) | -         | No       |
| `bfs_origin_node_uuids`            | array   | Node UUIDs to seed breadth-first searches from                                                                                                                                                                                    | -         | No       |
| ~~`min_fact_rating`~~ (deprecated) | double  | ~~The minimum rating by which to filter relevant facts (range: 0.0-1.0). Can only be used when using `scope="edges"`~~                                                                                                            | -         | No       |

\*Either `user_id` OR `graph_id` is required
†Required when using `mmr` reranker\
‡Required when using `node_distance` reranker\
§Timestamp filtering only applies to edge scope searches

## Search Scopes

Zep supports three different search scopes, each optimized for different types of information retrieval:

### Edges (Default)

Edges represent individual relationships and facts between entities in your graph. They contain specific interactions, conversations, and detailed information. Edge search is ideal for:

* Finding specific details or conversations
* Retrieving precise facts about relationships
* Getting granular information about interactions

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  # Edge search (default scope)
  search_results = client.graph.search(
      user_id=user_id,
      query="What did John say about the project?",
      scope="edges",  # Optional - this is the default
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Edge search (default scope)
  const searchResults = await client.graph.search({
    userId: userId,
    query: "What did John say about the project?",
    scope: "edges", // Optional - this is the default
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  // Edge search (default scope)
  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID: zep.String(userID),
      Query:  "What did John say about the project?",
      Scope:  zep.GraphSearchScopeEdges.Ptr(), // Optional - this is the default
  })
  ```
</CodeBlocks>

### Nodes

Nodes are connection points in the graph that represent entities. Each node maintains a summary of facts from its connections (edges), providing a comprehensive overview. Node search is useful for:

* Understanding broader context around entities
* Getting entity summaries and overviews
* Finding all information related to a specific person, place, or concept

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      graph_id=graph_id,
      query="John Smith",
      scope="nodes",
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    graphId: graphId,
    query: "John Smith",
    scope: "nodes",
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      GraphID: zep.String(graphID),
      Query:   "John Smith",
      Scope:   zep.GraphSearchScopeNodes.Ptr(),
  })
  ```
</CodeBlocks>

### Episodes

Episodes represent individual messages or chunks of data sent to Zep. Episode search allows you to find relevant episodes based on their content, making it ideal for:

* Finding specific messages or data chunks related to your query
* Discovering when certain topics were mentioned
* Retrieving relevant individual interactions
* Understanding the context of specific messages

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="project discussion",
      scope="episodes",
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: "project discussion",
    scope: "episodes",
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID: zep.String(userID),
      Query:  "project discussion",
      Scope:  zep.GraphSearchScopeEpisodes.Ptr(),
  })
  ```
</CodeBlocks>

## Rerankers

Zep provides multiple reranking algorithms to optimize search results for different use cases. Each reranker applies a different strategy to prioritize and order results:

### RRF (Reciprocal Rank Fusion)

<a name="reciprocal-rank-fusion" />

Reciprocal Rank Fusion is the default reranker that intelligently combines results from both semantic similarity and BM25 full-text search. It merges the two result sets by considering the rank position of each result in both searches, creating a unified ranking that leverages the strengths of both approaches.

**When to use**: RRF is ideal for most general-purpose search scenarios where you want balanced results combining conceptual understanding with exact keyword matching.

**Score interpretation**: RRF scores combine semantic similarity and keyword matching by summing reciprocal ranks (1/rank) from both search methods, resulting in higher scores for results that perform well in both approaches. Scores don't follow a fixed 0-1 scale but rather reflect the combined strength across both search types, with higher values indicating better overall relevance.

### MMR (Maximal Marginal Relevance)

<a name="maximal-marginal-re-ranking" />

Maximal Marginal Relevance addresses a common issue in similarity searches: highly similar top results that don't add diverse information to your context. MMR reranks results to balance relevance with diversity, promoting varied but still relevant results over redundant similar ones.

**When to use**: Use MMR when you need diverse information for comprehensive context, such as generating summaries, answering complex questions, or avoiding repetitive results.

**Required parameter**: `mmr_lambda` (0.0-1.0) - Controls the balance between relevance (1.0) and diversity (0.0). A value of 0.5 provides balanced results.

**Score interpretation**: MMR scores balance relevance with diversity based on your mmr\_lambda setting, meaning a moderately relevant but diverse result may score higher than a highly relevant but similar result. Interpret scores relative to your lambda value: with lambda=0.5, moderate scores may indicate valuable diversity rather than poor relevance.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="project status",
      reranker="mmr",
      mmr_lambda=0.5, # Balance diversity vs relevance
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: "project status",
    reranker: "mmr",
    mmrLambda: 0.5, // Balance diversity vs relevance
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:    zep.String(userID),
      Query:     "project status",
      Reranker:  zep.GraphSearchQueryRerankerMmr.Ptr(),
      MmrLambda: zep.Float64(0.5), // Balance diversity vs relevance
  })
  ```
</CodeBlocks>

### Cross Encoder

`cross_encoder` uses a specialized neural model that jointly analyzes the query and each search result together, rather than analyzing them separately. This provides more accurate relevance scoring by understanding the relationship between the query and potential results in a single model pass.

**When to use**: Use cross encoder when you need the highest accuracy in relevance scoring and are willing to trade some performance for better results. Ideal for critical searches where precision is paramount.

**Trade-offs**: Higher accuracy but slower performance compared to other rerankers.

**Score interpretation**: Cross encoder scores follow a sigmoid curve (`0-1` range) where highly relevant results cluster near the top with scores that decay rapidly as relevance decreases. You'll typically see a sharp drop-off between truly relevant results (higher scores) and less relevant ones, making it easy to set meaningful relevance thresholds.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="critical project decision",
      reranker="cross_encoder",
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: "critical project decision",
    reranker: "cross_encoder",
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:   zep.String(userID),
      Query:    "critical project decision",
      Reranker: zep.GraphSearchQueryRerankerCrossEncoder.Ptr(),
  })
  ```
</CodeBlocks>

### Episode Mentions

`episode_mentions` reranks search results based on how frequently nodes or edges have been mentioned across all episodes, including both conversational episodes (chat history) and episodes created via `graph.add`. Results that appear more often across these episodes are prioritized, reflecting their importance and relevance.

**When to use**: Use episode mentions when you want to surface information that has been frequently referenced across conversations or data uploads. Useful for understanding recurring themes, important topics, or frequently mentioned entities across all your graph data.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="team feedback",
      reranker="episode_mentions",
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: "team feedback",
    reranker: "episode_mentions",
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:   zep.String(userID),
      Query:    "team feedback",
      Reranker: zep.GraphSearchQueryRerankerEpisodeMentions.Ptr(),
  })
  ```
</CodeBlocks>

### Node Distance

`node_distance` reranks search results based on graph proximity, prioritizing results that are closer (fewer hops) to a specified center node. This spatial approach to relevance is useful for finding information contextually related to a specific entity or concept.

**When to use**: Use node distance when you want to find information specifically related to a particular entity, person, or concept in your graph. Ideal for exploring the immediate context around a known entity.

**Required parameter**: `center_node_uuid` - The UUID of the node to use as the center point for distance calculations.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="recent activities",
      reranker="node_distance",
      center_node_uuid=center_node_uuid,
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: "recent activities",
    reranker: "node_distance",
    centerNodeUuid: centerNodeUuid,
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:         zep.String(userID),
      Query:          "recent activities",
      Reranker:       zep.GraphSearchQueryRerankerNodeDistance.Ptr(),
      CenterNodeUuid: zep.String(centerNodeUuid),
  })
  ```
</CodeBlocks>

### Reranker Score

Graph search results include a reranker score that provides a measure of relevance for each returned result. This score is available when using any reranker and is returned on any node, edge, or episode from `graph.search`. The reranker score can be used to manually filter results to only include those above a certain relevance threshold, allowing for more precise control over search result quality.

The interpretation of the score depends on which reranker is used. For example, when using the `cross_encoder` reranker, the score follows a sigmoid curve with the score decaying rapidly as relevance decreases. For more information about the score field in the response, see the [SDK reference](https://help.getzep.com/sdk-reference/graph/search#response.body.edges.score).

#### Relevance Score

When using the `cross_encoder` reranker, search results include an additional `relevance` field alongside the `score` field. The `relevance` field is a rank-aligned score in the range \[0, 1] derived from the existing sigmoid-distributed `score` to improve interpretability and thresholding.

**Key characteristics:**

* Range: \[0, 1]
* Only populated when using the `cross_encoder` reranker
* Preserves the ranking order produced by Zep's reranker
* Not a probability; it is a monotonic transform of `score` to reduce saturation near 1
* Use `relevance` for sorting, filtering, and analytics

The `relevance` field provides a more intuitive metric for evaluating search result quality compared to the raw `score`, making it easier to set meaningful thresholds and analyze results.

## Search Filters

Zep allows you to filter search results by specific entity types or edge types, enabling more targeted searches within your graph.

### Entity Type Filtering

Filter search results to only include nodes of specific entity types. This is useful when you want to focus on particular kinds of entities (e.g., only people, only companies, only locations).

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="software engineers",
      scope="nodes",
      search_filters={
          "node_labels": ["Person", "Company"]
      }
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: "software engineers",
    scope: "nodes",
    searchFilters: {
      nodeLabels: ["Person", "Company"]
    }
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchFilters := zep.SearchFilters{NodeLabels: []string{"Person", "Company"}}
  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:        zep.String(userID),
      Query:         "software engineers",
      Scope:         zep.GraphSearchScopeNodes.Ptr(),
      SearchFilters: &searchFilters,
  })
  ```
</CodeBlocks>

### Edge Type Filtering

Filter search results to only include edges of specific relationship types. This helps you find particular kinds of relationships or interactions between entities.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="project collaboration",
      scope="edges",
      search_filters={
          "edge_types": ["WORKS_WITH", "COLLABORATES_ON"]
      }
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const searchResults = await client.graph.search({
    userId: userId,
    query: "project collaboration",
    scope: "edges",
    searchFilters: {
      edgeTypes: ["WORKS_WITH", "COLLABORATES_ON"]
    }
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  searchFilters := zep.SearchFilters{EdgeTypes: []string{"WORKS_WITH", "COLLABORATES_ON"}}
  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:        zep.String(userID),
      Query:         "project collaboration",
      Scope:         zep.GraphSearchScopeEdges.Ptr(),
      SearchFilters: &searchFilters,
  })
  ```
</CodeBlocks>

### Exclusion Filters

Exclusion filters allow you to exclude specific entity types or edge types from your search results. This is useful when you want to filter out certain types of information while keeping all others.

#### Excluding Node Labels

Exclude specific entity types from node or edge search results. When searching edges, nodes connected to the edges are also checked against exclusion filters.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  # Exclude certain entity types from results
  search_results = client.graph.search(
      user_id=user_id,
      query="project information",
      scope="nodes",
      search_filters={
          "exclude_node_labels": ["Assistant", "Document"]
      }
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Exclude certain entity types from results
  const searchResults = await client.graph.search({
    userId: userId,
    query: "project information",
    scope: "nodes",
    searchFilters: {
      excludeNodeLabels: ["Assistant", "Document"]
    }
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  // Exclude certain entity types from results
  searchFilters := zep.SearchFilters{ExcludeNodeLabels: []string{"Assistant", "Document"}}
  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:        zep.String(userID),
      Query:         "project information",
      Scope:         zep.GraphSearchScopeNodes.Ptr(),
      SearchFilters: &searchFilters,
  })
  ```
</CodeBlocks>

#### Excluding Edge Types

Exclude specific edge types from search results. This helps you filter out certain kinds of relationships while keeping all others.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  # Exclude certain edge types from results
  search_results = client.graph.search(
      user_id=user_id,
      query="user activities",
      scope="edges",
      search_filters={
          "exclude_edge_types": ["LOCATED_AT", "OCCURRED_AT"]
      }
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Exclude certain edge types from results
  const searchResults = await client.graph.search({
    userId: userId,
    query: "user activities",
    scope: "edges",
    searchFilters: {
      excludeEdgeTypes: ["LOCATED_AT", "OCCURRED_AT"]
    }
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  // Exclude certain edge types from results
  searchFilters := zep.SearchFilters{ExcludeEdgeTypes: []string{"LOCATED_AT", "OCCURRED_AT"}}
  searchResults, err := client.Graph.Search(context.TODO(), &zep.GraphSearchQuery{
      UserID:        zep.String(userID),
      Query:         "user activities",
      Scope:         zep.GraphSearchScopeEdges.Ptr(),
      SearchFilters: &searchFilters,
  })
  ```
</CodeBlocks>

<Note>
  Exclusion filters can be combined with inclusion filters (`node_labels` and `edge_types`). When both are specified, results must match the inclusion criteria AND not match any exclusion criteria.
</Note>

### Datetime Filtering

Filter search results based on timestamps, enabling temporal-based queries to find information from specific time periods. This feature allows you to search for content based on four different timestamp types, each serving a distinct purpose in tracking the lifecycle of facts in your knowledge graph.

<Note title="Edge Scope Only" icon="warning">
  Datetime filtering only applies to edge scope searches. When using `scope="nodes"` or `scope="episodes"`, datetime filter values are ignored and have no effect on search results.
</Note>

**Available Timestamp Types:**

| Timestamp    | Description                                          | Example Use Case                                       |
| ------------ | ---------------------------------------------------- | ------------------------------------------------------ |
| `created_at` | The time when Zep learned the fact was true          | Finding when information was first added to the system |
| `valid_at`   | The real world time that the fact started being true | Identifying when a relationship or state began         |
| `invalid_at` | The real world time that the fact stopped being true | Finding when a relationship or state ended             |
| `expired_at` | The time that Zep learned that the fact was false    | Tracking when information was marked as outdated       |

For example, for the fact "Alice is married to Bob":

* `valid_at`: The time they got married
* `invalid_at`: The time they got divorced
* `created_at`: The time Zep learned they were married
* `expired_at`: The time Zep learned they were divorced

**Logic Behavior:**

* **Outer array/list**: Uses OR logic - any condition graph can match
* **Inner array/list**: Uses AND logic - all conditions within a graph must match

In the example below, results are returned if they match:

* (created >= 2025-07-01 AND created \< 2025-08-01) OR (created \< 2025-05-01)

**Date Format**: All dates must be in ISO 8601 format with timezone (e.g., "2025-07-01T20:57:56Z")

**Comparison Operators**: Supports `>=`, `<=`, `<`, and `>` for flexible date range queries

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep
  from zep_cloud.types import SearchFilters, DateFilter

  client = Zep(
      api_key=API_KEY,
  )

  # Search for edges created in July 2025 OR before May 2025
  search_results = client.graph.search(
      user_id=user_id,
      query="project discussions",
      scope="edges",
      search_filters=SearchFilters(
          created_at=[
              # First condition graph (AND logic within)
              [DateFilter(comparison_operator=">=", date="2025-07-01T20:57:56Z"), 
               DateFilter(comparison_operator="<", date="2025-08-01T20:57:56Z")],
              # Second condition graph (OR logic with first graph)
              [DateFilter(comparison_operator="<", date="2025-05-01T20:57:56Z")],
          ]
      )
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Search for edges created in July 2025 OR before May 2025
  const searchResults = await client.graph.search({
    userId: userId,
    query: "project discussions",
    scope: "edges",
    searchFilters: {
      createdAt: [
        // First condition graph (AND logic within)
        [
          {comparisonOperator: ">=", date: "2025-07-01T20:57:56Z"},
          {comparisonOperator: "<", date: "2025-08-01T20:57:56Z"}
        ],
        // Second condition graph (OR logic with first graph)
        [
          {comparisonOperator: "<", date: "2025-05-01T20:57:56Z"}
        ]
      ]
    }
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  // Search for edges created in July 2025 OR before May 2025
  searchResults, err := client.Graph.Search(ctx, &zep.GraphSearchQuery{
      UserID: zep.String(userID),
      Query:  "project discussions",
      Scope:  zep.GraphSearchScopeEdges.Ptr(),
      SearchFilters: &zep.SearchFilters{
          CreatedAt: [][]*zep.DateFilter{
              // First condition graph (AND logic within)
              {
                  {
                      ComparisonOperator: zep.ComparisonOperatorGreaterThanEqual,
                      Date:              "2025-07-01T20:57:56Z",
                  },
                  {
                      ComparisonOperator: zep.ComparisonOperatorLessThan,
                      Date:              "2025-08-01T20:57:56Z",
                  },
              },
              // Second condition graph (OR logic with first graph)
              {
                  {
                      ComparisonOperator: zep.ComparisonOperatorLessThan,
                      Date:              "2025-05-01T20:57:56Z",
                  },
              },
          },
      },
  })
  ```
</CodeBlocks>

**Common Use Cases:**

* **Date Range Filtering**: Find facts from specific time periods using any timestamp type
* **Recent Activity**: Search for edges created or expired after a certain date using `>=` operator
* **Historical Data**: Find older information using `<` or `<=` operators on any timestamp
* **Validity Period Analysis**: Use `valid_at` and `invalid_at` together to find facts that were true during specific periods
* **Audit Trail**: Use `created_at` and `expired_at` to track when your system learned about changes
* **Complex Temporal Queries**: Combine multiple date conditions across different timestamp types

## ~~Filtering by Fact Rating~~ (deprecated)

~~The `min_fact_rating` parameter allows you to filter search results based on the relevancy rating of facts stored in your graph edges. When specified, all facts returned will have at least the minimum rating value you set.~~

~~This parameter accepts values between 0.0 and 1.0, where higher values indicate more relevant facts. By setting a minimum threshold, you can ensure that only highly relevant facts are included in your search results.~~

~~**Important**: The `min_fact_rating` parameter can only be used when searching with `scope="edges"` as fact ratings are associated with edge relationships.~~

~~Read more about [fact ratings and how they work](/facts#rating-facts-for-relevancy).~~

## Breadth-First Search (BFS)

The `bfs_origin_node_uuids` parameter enables breadth-first searches starting from specified nodes, which helps make search results more relevant to recent context. This is particularly useful when combined with recent episode IDs to bias search results toward information connected to recent conversations. You can pass episode IDs as BFS node IDs because episodes are represented as nodes under the hood.

**When to use**: Use BFS when you want to find information that's contextually connected to specific starting points in your graph, such as recent episodes or important entities.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  # Get recent episodes to use as BFS origin points
  episodes = client.graph.episode.get_by_user_id(
      user_id=user_id,
      lastn=10
  ).episodes

  episode_uuids = [episode.uuid_ for episode in episodes if episode.role == 'user']

  # Search with BFS starting from recent episodes
  search_results = client.graph.search(
      user_id=user_id,
      query="project updates",
      scope="edges",
      bfs_origin_node_uuids=episode_uuids,
      limit=10
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Get recent episodes to use as BFS origin points
  const episodeResponse = await client.graph.episode.getByUserId(userId, { lastn: 10 });
  const episodeUuids = (episodeResponse.episodes || [])
      .filter((episode) => episode.role === "user")
      .map((episode) => episode.uuid);

  // Search with BFS starting from recent episodes
  const searchResults = await client.graph.search({
    userId: userId,
    query: "project updates",
    scope: "edges",
    bfsOriginNodeUuids: episodeUuids,
    limit: 10,
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  // Get recent episodes to use as BFS origin points
  response, err := client.Graph.Episode.GetByUserID(
      ctx,
      userID,
      &zep.EpisodeGetByUserIDRequest{
          Lastn: zep.Int(10),
      },
  )

  var episodeUUIDs []string
  for _, episode := range response.Episodes {
      if episode.Role != nil && *episode.Role == zep.RoleTypeUserRole {
          episodeUUIDs = append(episodeUUIDs, episode.UUID)
      }
  }

  // Search with BFS starting from recent episodes
  searchResults, err := client.Graph.Search(ctx, &zep.GraphSearchQuery{
      UserID:             zep.String(userID),
      Query:              "project updates",
      Scope:              zep.GraphSearchScopeEdges.Ptr(),
      BfsOriginNodeUUIDs: episodeUUIDs,
      Limit:              zep.Int(10),
  })
  ```
</CodeBlocks>


# Customizing Graph Structure

Zep enables the use of rich, domain-specific data structures in graphs through Entity Types and Edge Types, replacing generic graph nodes and edges with detailed models.

Zep classifies newly created nodes/edges as one of the default or custom types or leaves them unclassified. For example, a node representing a preference is classified as a Preference node, and attributes specific to that type are automatically populated. You may restrict graph queries to nodes/edges of a specific type, such as Preference.

The default entity and edge types are applied to user graphs (not all graphs) by default, but you may define additional custom types as needed.

Each node/edge is classified as a single type only. Multiple classifications are not supported.

## Default Entity and Edge Types

### Definition

Zep provides default entity and edge types that are automatically applied to user graphs (not all graphs). These types help classify and structure the information extracted from conversations.

You can view the exact definition for the default ontology [here](https://github.com/getzep/zep/blob/main/ontology/default_ontology.py).

#### Default Entity Types

The default entity types are:

* **User**: A Zep user specified by role in chat messages. There can only be a single User entity.
* **Assistant**: Represents the AI assistant in the conversation. This entity is a singleton.
* **Preference**: Entities mentioned in contexts expressing user preferences, choices, opinions, or selections. This classification is prioritized over most other classifications.
* **Location**: A physical or virtual place where activities occur or entities exist. Use this classification only after checking if the entity fits other more specific types.
* **Event**: A time-bound activity, occurrence, or experience.
* **Object**: A physical item, tool, device, or possession. Use this classification only as a last resort after checking other types.
* **Topic**: A subject of conversation, interest, or knowledge domain. Use this classification only as a last resort after checking other types.
* **Organization**: A company, institution, group, or formal entity.
* **Document**: Information content in various forms.

#### Default Edge Types

The default edge types are:

* **LOCATED\_AT**: Represents that an entity exists or occurs at a specific location. Connects any entity to a Location.
* **OCCURRED\_AT**: Represents that an event happened at a specific time or location. Connects an Event to any entity.

Default entity and edge types apply to user graphs. All nodes and edges in any user graph will be classified into one of these types or none.

### Adding Data

When we add data to the graph, default entity and edge types are automatically created:

<CodeBlocks>
  ```python
  from zep_cloud.types import Message

  message = {
      "name": "John Doe",
      "role": "user",
      "content": "I really like pop music, and I don't like metal",
  }

  client.thread.add_messages(thread_id=thread_id, messages=[Message(**message)])
  ```

  ```typescript
  const messages = [{
      name: "John Doe",
      role: "user",
      content: "I really like pop music, and I don't like metal",
  }];

  await client.thread.addMessages(threadId, {messages: messages});
  ```

  ```go
  userName := "John Doe"
  messages := []*v3.Message{
      {
          Name:    &userName,
          Content: "I really like pop music, and I don't like metal",
          Role:    "user",
      },
  }

  // Add the messages to the graph
  _, err = zepClient.Thread.AddMessages(
      context.TODO(),
      threadId,
      &v3.AddThreadMessagesRequest{
          Messages: messages,
      },
  )
  if err != nil {
      log.Fatal("Error adding messages:", err)
  }
  ```
</CodeBlocks>

### Searching

When searching nodes in the graph, you may provide a list of types to filter the search by. The provided types are ORed together. Search results will only include nodes that satisfy one of the provided types:

<CodeBlocks>
  ```python
  search_results = client.graph.search(
      user_id=user_id,
      query="the user's music preferences",
      scope="nodes",
      search_filters={
          "node_labels": ["Preference"]
      }
  )
  for i, node in enumerate(search_results.nodes):
      preference = node.attributes
      print(f"Preference {i+1}:{preference}")
  ```

  ```typescript
  const searchResults = await client.graph.search({
    userId: userId,
    query: "the user's music preferences",
    scope: "nodes",
    searchFilters: {
      nodeLabels: ["Preference"],
    },
  });

  if (searchResults.nodes && searchResults.nodes.length > 0) {
    for (let i = 0; i < searchResults.nodes.length; i++) {
      const node = searchResults.nodes[i];
      const preference = node.attributes;
      console.log(`Preference ${i + 1}: ${JSON.stringify(preference)}`);
    }
  }
  ```

  ```go
  searchFilters := v3.SearchFilters{NodeLabels: []string{"Preference"}}
  searchResults, err := client.Graph.Search(
  	ctx,
  	&v3.GraphSearchQuery{
  		UserID:        v3.String(userID),
  		Query:         "the user's music preferences",
  		Scope:         v3.GraphSearchScopeNodes.Ptr(),
  		SearchFilters: &searchFilters,
  	},
  )
  if err != nil {
  	log.Fatal("Error searching graph:", err)
  }

  for i, node := range searchResults.Nodes {
  	// Convert attributes map to JSON for pretty printing
  	attributesJSON, err := json.MarshalIndent(node.Attributes, "", "  ")
  	if err != nil {
  		log.Fatal("Error marshaling attributes:", err)
  	}
  	
  	fmt.Printf("Preference %d:\n%s\n\n", i+1, string(attributesJSON))
  }
  ```
</CodeBlocks>

```text
Preference 1: {'category': 'Music', 'description': 'Pop Music is a genre of music characterized by its catchy melodies and widespread appeal.', 'labels': ['Entity', 'Preference']}
Preference 2: {'category': 'Music', 'description': 'Metal Music is a genre of music characterized by its heavy sound and complex compositions.', 'labels': ['Entity', 'Preference']}
```

### Disabling Default Ontology

In some cases, you may want to disable the default entity and edge types for specific users and only use custom types you define. You can do this by setting the `disable_default_ontology` flag when creating or updating a user.

When `disable_default_ontology` is set to `true`:

* Only custom entity and edge types you define will be used for classification
* The default entity and edge types (User, Assistant, Preference, Location, etc.) will not be applied
* Nodes and edges will only be classified as your custom types or remain unclassified

This is useful when you need precise control over your graph structure and want to ensure only domain-specific types are used.

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  # Create a user with default ontology disabled
  user = client.user.add(
      user_id=user_id,
      first_name="John",
      last_name="Doe",
      email="john.doe@example.com",
      disable_default_ontology=True
  )

  # Or update an existing user to disable default ontology
  client.user.update(
      user_id=user_id,
      disable_default_ontology=True
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Create a user with default ontology disabled
  const user = await client.user.add({
    userId: userId,
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com",
    disableDefaultOntology: true
  });

  // Or update an existing user to disable default ontology
  await client.user.update(userId, {
    disableDefaultOntology: true
  });
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(
      option.WithAPIKey(API_KEY),
  )

  // Create a user with default ontology disabled
  user, err := client.User.Add(
      context.TODO(),
      &zep.CreateUserRequest{
          UserID:                  userID,
          FirstName:              zep.String("John"),
          LastName:               zep.String("Doe"),
          Email:                  zep.String("john.doe@example.com"),
          DisableDefaultOntology: zep.Bool(true),
      },
  )

  // Or update an existing user to disable default ontology
  _, err = client.User.Update(
      context.TODO(),
      userID,
      &zep.UpdateUserRequest{
          DisableDefaultOntology: zep.Bool(true),
      },
  )
  ```
</CodeBlocks>

## Custom Entity and Edge Types

<Note>
  Start with fewer, more generic custom types with minimal fields and simple definitions, then incrementally add complexity as needed. This functionality requires prompt engineering and iterative optimization of the class and field descriptions, so it's best to start simple.
</Note>

### Definition

In addition to the default entity and edge types, you may specify your own custom entity and custom edge types. You need to provide a description of the type and a description for each of the fields. The syntax for this is different for each language.

You may not create more than 10 custom entity types and 10 custom edge types per project. The limit of 10 custom entity types does not include the default types. Each model may have up to 10 fields.

<Warning>
  When creating custom entity or edge types, you may not use the following attribute names (including in Go struct tags), as they conflict with default node attributes: `uuid`, `name`, `graph_id`, `name_embedding`, `summary`, and `created_at`.
</Warning>

<Note>
  Including attributes on custom entity and edge types is an advanced feature designed for precision context engineering where you only want to utilize specific field values when constructing your context block. [See here for an example](cookbook/customize-your-context-block#example-2-utilizing-custom-entity-and-edge-types). Many agent memory use cases can be solved with node summaries and facts alone. Custom attributes should only be added when you need structured field values for precise context retrieval rather than general conversational memory.
</Note>

<CodeBlocks>
  ```python
  from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel, EntityBoolean
  from pydantic import Field

  class Restaurant(EntityModel):
      """
      Represents a specific restaurant.
      """
      cuisine_type: EntityText = Field(description="The cuisine type of the restaurant, for example: American, Mexican, Indian, etc.", default=None)
      dietary_accommodation: EntityText = Field(description="The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc.", default=None)

  class Audiobook(EntityModel):
      """
      Represents an audiobook entity.
      """
      genre: EntityText = Field(description="The genre of the audiobook, for example: self-help, fiction, nonfiction, etc.", default=None)

  class RestaurantVisit(EdgeModel):
      """
      Represents the fact that the user visited a restaurant.
      """
      restaurant_name: EntityText = Field(description="The name of the restaurant the user visited", default=None)

  class AudiobookListen(EdgeModel):
      """
      Represents the fact that the user listened to or played an audiobook.
      """
      audiobook_title: EntityText = Field(description="The title of the audiobook the user listened to or played", default=None)

  class DietaryPreference(EdgeModel):
      """
      Represents the fact that the user has a dietary preference or dietary restriction.
      """
      preference_type: EntityText = Field(description="Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc.", default=None)
      allergy: EntityBoolean = Field(description="Whether this dietary preference represents a user allergy: True or false", default=None)
  ```

  ```typescript
  import { entityFields, EntityType, EdgeType } from "@getzep/zep-cloud";

  const RestaurantSchema: EntityType = {
      description: "Represents a specific restaurant.",
      fields: {
          cuisine_type: entityFields.text("The cuisine type of the restaurant, for example: American, Mexican, Indian, etc."),
          dietary_accommodation: entityFields.text("The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc."),
      },
  };

  const AudiobookSchema: EntityType = {
      description: "Represents an audiobook entity.",
      fields: {
          genre: entityFields.text("The genre of the audiobook, for example: self-help, fiction, nonfiction, etc."),
      },
  };

  const RestaurantVisit: EdgeType = {
      description: "Represents the fact that the user visited a restaurant.",
      fields: {
          restaurant_name: entityFields.text("The name of the restaurant the user visited"),
      },
      sourceTargets: [
          { source: "User", target: "Restaurant" },
      ],
  };

  const AudiobookListen: EdgeType = {
      description: "Represents the fact that the user listened to or played an audiobook.",
      fields: {
          audiobook_title: entityFields.text("The title of the audiobook the user listened to or played"),
      },
      sourceTargets: [
          { source: "User", target: "Audiobook" },
      ],
  };

  const DietaryPreference: EdgeType = {
      description: "Represents the fact that the user has a dietary preference or dietary restriction.",
      fields: {
          preference_type: entityFields.text("Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc."),
          allergy: entityFields.boolean("Whether this dietary preference represents a user allergy: True or false"),
      },
      sourceTargets: [
          { source: "User" },
      ],
  };
  ```

  ```go
  type Restaurant struct {
      zep.BaseEntity `name:"Restaurant" description:"Represents a specific restaurant."`
      CuisineType           string `description:"The cuisine type of the restaurant, for example: American, Mexican, Indian, etc." json:"cuisine_type,omitempty"`
      DietaryAccommodation  string `description:"The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc." json:"dietary_accommodation,omitempty"`
  }

  type Audiobook struct {
      zep.BaseEntity `name:"Audiobook" description:"Represents an audiobook entity."`
      Genre string `description:"The genre of the audiobook, for example: self-help, fiction, nonfiction, etc." json:"genre,omitempty"`
  }

  type RestaurantVisit struct {
      zep.BaseEdge `name:"RESTAURANT_VISIT" description:"Represents the fact that the user visited a restaurant."`
      RestaurantName string `description:"The name of the restaurant the user visited" json:"restaurant_name,omitempty"`
  }

  type AudiobookListen struct {
      zep.BaseEdge `name:"AUDIOBOOK_LISTEN" description:"Represents the fact that the user listened to or played an audiobook."`
      AudiobookTitle string `description:"The title of the audiobook the user listened to or played" json:"audiobook_title,omitempty"`
  }

  type DietaryPreference struct {
      zep.BaseEdge `name:"DIETARY_PREFERENCE" description:"Represents the fact that the user has a dietary preference or dietary restriction."`
      PreferenceType string `description:"Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc." json:"preference_type,omitempty"`
      Allergy        bool   `description:"Whether this dietary preference represents a user allergy: True or false" json:"allergy,omitempty"`
  }
  ```
</CodeBlocks>

### Setting Entity and Edge Types

You can set these custom entity and edge types as the graph ontology for your current [Zep project](/projects). The ontology can be applied either project-wide to all users and graphs, or targeted to specific users and graphs only.

#### Setting Types Project Wide

When no user IDs or graph IDs are provided, the ontology is set for the entire project. All users and graphs within the project will use this ontology. Note that for custom edge types, you can require the source and destination nodes to be a certain type, or allow them to be any type:

<CodeBlocks>
  ```python
  from zep_cloud import EntityEdgeSourceTarget

  client.graph.set_ontology(
      entities={
          "Restaurant": Restaurant,
          "Audiobook": Audiobook,
      },
      edges={
          "RESTAURANT_VISIT": (
              RestaurantVisit,
              [EntityEdgeSourceTarget(source="User", target="Restaurant")]
          ),
          "AUDIOBOOK_LISTEN": (
              AudiobookListen,
              [EntityEdgeSourceTarget(source="User", target="Audiobook")]
          ),
          "DIETARY_PREFERENCE": (
              DietaryPreference,
              [EntityEdgeSourceTarget(source="User")]
          ),
      }
  )
  ```

  ```typescript
  await client.graph.setOntology(
      {
          Restaurant: RestaurantSchema,
          Audiobook: AudiobookSchema,
      },
      {
          RESTAURANT_VISIT: RestaurantVisit,
          AUDIOBOOK_LISTEN: AudiobookListen,
          DIETARY_PREFERENCE: DietaryPreference,
      }
  );
  ```

  ```go
  _, err = client.Graph.SetOntology(
      ctx,
      []zep.EntityDefinition{
          Restaurant{},
          Audiobook{},
      },
      []zep.EdgeDefinitionWithSourceTargets{
          {
              EdgeModel: RestaurantVisit{},
              SourceTargets: []zep.EntityEdgeSourceTarget{
                  {
                      Source: zep.String("User"),
                      Target: zep.String("Restaurant"),
                  },
              },
          },
          {
              EdgeModel: AudiobookListen{},
              SourceTargets: []zep.EntityEdgeSourceTarget{
                  {
                      Source: zep.String("User"),
                      Target: zep.String("Audiobook"),
                  },
              },
          },
          {
              EdgeModel: DietaryPreference{},
              SourceTargets: []zep.EntityEdgeSourceTarget{
                  {
                      Source: zep.String("User"),
                  },
              },
          },
      },
  )
  if err != nil {
      fmt.Printf("Error setting ontology: %v\n", err)
      return
  }
  ```
</CodeBlocks>

#### Setting Types For Specific Graphs

You can also set the ontology for specific users and/or graphs by providing user IDs and graph IDs. When these parameters are provided, the ontology will only apply to the specified users and graphs, while other users and graphs in the project will continue using the previously set ontology (whether that was due to a project-wide setting of ontology or due to a graph-specific setting of ontology):

<CodeBlocks>
  ```python
  from zep_cloud import EntityEdgeSourceTarget

  await client.graph.set_ontology(
      user_ids=["user_1234", "user_5678"],
      graph_ids=["graph_1234", "graph_5678"],
      entities={
          "Restaurant": Restaurant,
          "Audiobook": Audiobook,
      },
      edges={
          "RESTAURANT_VISIT": (
              RestaurantVisit,
              [EntityEdgeSourceTarget(source="User", target="Restaurant")]
          ),
          "AUDIOBOOK_LISTEN": (
              AudiobookListen,
              [EntityEdgeSourceTarget(source="User", target="Audiobook")]
          ),
          "DIETARY_PREFERENCE": (
              DietaryPreference,
              [EntityEdgeSourceTarget(source="User")]
          ),
      }
  )
  ```

  ```typescript
  await client.graph.setOntology(
      {
          Restaurant: RestaurantSchema,
          Audiobook: AudiobookSchema,
      },
      {
          RESTAURANT_VISIT: RestaurantVisit,
          AUDIOBOOK_LISTEN: AudiobookListen,
          DIETARY_PREFERENCE: DietaryPreference,
      },
      {
          userIds: ["user_1234", "user_5678"],
          graphIds: ["graph_1234", "graph_5678"],
      }
  );
  ```

  ```go
  _, err := client.Graph.SetOntology(
      ctx,
      []zep.EntityDefinition{
          Restaurant{},
          Audiobook{},
      },
      []zep.EdgeDefinitionWithSourceTargets{
          {
              EdgeModel: RestaurantVisit{},
              SourceTargets: []zep.EntityEdgeSourceTarget{
                  {
                      Source: zep.String("User"),
                      Target: zep.String("Restaurant"),
                  },
              },
          },
          {
              EdgeModel: AudiobookListen{},
              SourceTargets: []zep.EntityEdgeSourceTarget{
                  {
                      Source: zep.String("User"),
                      Target: zep.String("Audiobook"),
                  },
              },
          },
          {
              EdgeModel: DietaryPreference{},
              SourceTargets: []zep.EntityEdgeSourceTarget{
                  {
                      Source: zep.String("User"),
                  },
              },
          },
      },
      zep.ForUsers([]string{"user_1234", "user_5678"}),
      zep.ForGraphs([]string{"graph_1234", "graph_5678"}),
  )
  if err != nil {
      fmt.Printf("Error setting ontology: %v\n", err)
      return
  }
  ```
</CodeBlocks>

### Adding Data

Now, when you add data to the graph, new nodes and edges are classified into exactly one of the overall set of entity or edge types respectively, or no type:

<CodeBlocks>
  ```python
  from zep_cloud import Message
  import uuid

  messages_thread1 = [
      Message(content="Take me to a lunch place", role="user", name="John Doe"),
      Message(content="How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", role="assistant", name="Assistant"),
      Message(content="Do any of those have vegetarian options? I'm vegetarian", role="user", name="John Doe"),
      Message(content="Yes, Green Leaf Cafe has vegetarian options", role="assistant", name="Assistant"),
      Message(content="Let's go to Green Leaf Cafe", role="user", name="John Doe"),
      Message(content="Navigating to Green Leaf Cafe", role="assistant", name="Assistant"),
  ]

  messages_thread2 = [
      Message(content="Play the 7 habits of highly effective people", role="user", name="John Doe"),
      Message(content="Playing the 7 habits of highly effective people", role="assistant", name="Assistant"),
  ]

  user_id = f"user-{uuid.uuid4()}"
  client.user.add(user_id=user_id, first_name="John", last_name="Doe", email="john.doe@example.com")

  thread1_id = f"thread-{uuid.uuid4()}"
  thread2_id = f"thread-{uuid.uuid4()}"
  client.thread.create(thread_id=thread1_id, user_id=user_id)
  client.thread.create(thread_id=thread2_id, user_id=user_id)

  client.thread.add_messages(thread_id=thread1_id, messages=messages_thread1, ignore_roles=["assistant"])
  client.thread.add_messages(thread_id=thread2_id, messages=messages_thread2, ignore_roles=["assistant"])
  ```

  ```typescript
  import { v4 as uuidv4 } from "uuid";
  import type { Message } from "@getzep/zep-cloud/api";

  const messagesThread1: Message[] = [
      { content: "Take me to a lunch place", role: "user", name: "John Doe" },
      { content: "How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", role: "assistant", name: "Assistant" },
      { content: "Do any of those have vegetarian options? I'm vegetarian", role: "user", name: "John Doe" },
      { content: "Yes, Green Leaf Cafe has vegetarian options", role: "assistant", name: "Assistant" },
      { content: "Let's go to Green Leaf Cafe", role: "user", name: "John Doe" },
      { content: "Navigating to Green Leaf Cafe", role: "assistant", name: "Assistant" },
  ];

  const messagesThread2: Message[] = [
      { content: "Play the 7 habits of highly effective people", role: "user", name: "John Doe" },
      { content: "Playing the 7 habits of highly effective people", role: "assistant", name: "Assistant" },
  ];

  let userId = `user-${uuidv4()}`;
  await client.user.add({ userId, firstName: "John", lastName: "Doe", email: "john.doe@example.com" });

  const thread1Id = `thread-${uuidv4()}`;
  const thread2Id = `thread-${uuidv4()}`;
  await client.thread.create({ threadId: thread1Id, userId });
  await client.thread.create({ threadId: thread2Id, userId });

  await client.thread.addMessages(thread1Id, { messages: messagesThread1, ignoreRoles: ["assistant"] });
  await client.thread.addMessages(thread2Id, { messages: messagesThread2, ignoreRoles: ["assistant"] });
  ```

  ```go
  messagesThread1 := []zep.Message{
      {Content: "Take me to a lunch place", Role: "user", Name: zep.String("John Doe")},
      {Content: "How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", Role: "assistant", Name: zep.String("Assistant")},
      {Content: "Do any of those have vegetarian options? I'm vegetarian", Role: "user", Name: zep.String("John Doe")},
      {Content: "Yes, Green Leaf Cafe has vegetarian options", Role: "assistant", Name: zep.String("Assistant")},
      {Content: "Let's go to Green Leaf Cafe", Role: "user", Name: zep.String("John Doe")},
      {Content: "Navigating to Green Leaf Cafe", Role: "assistant", Name: zep.String("Assistant")},
  }
  messagesThread2 := []zep.Message{
      {Content: "Play the 7 habits of highly effective people", Role: "user", Name: zep.String("John Doe")},
      {Content: "Playing the 7 habits of highly effective people", Role: "assistant", Name: zep.String("Assistant")},
  }
  userID := "user-" + uuid.NewString()
  userReq := &zep.CreateUserRequest{
      UserID:    userID,
      FirstName: zep.String("John"),
      LastName:  zep.String("Doe"),
      Email:     zep.String("john.doe@example.com"),
  }
  _, err := client.User.Add(ctx, userReq)
  if err != nil {
      fmt.Printf("Error creating user: %v\n", err)
      return
  }

  thread1ID := "thread-" + uuid.NewString()
  thread2ID := "thread-" + uuid.NewString()

  thread1Req := &zep.CreateThreadRequest{
      ThreadID: thread1ID,
      UserID:    userID,
  }
  thread2Req := &zep.CreateThreadRequest{
      ThreadID: thread2ID,
      UserID:    userID,
  }
  _, err = client.Thread.Create(ctx, thread1Req)
  if err != nil {
      fmt.Printf("Error creating thread 1: %v\n", err)
      return
  }
  _, err = client.Thread.Create(ctx, thread2Req)
  if err != nil {
      fmt.Printf("Error creating thread 2: %v\n", err)
      return
  }

  msgPtrs1 := make([]*zep.Message, len(messagesThread1))
  for i := range messagesThread1 {
      msgPtrs1[i] = &messagesThread1[i]
  }
  addReq1 := &zep.AddThreadMessagesRequest{
      Messages: msgPtrs1,
      IgnoreRoles: []zep.RoleType{
      zep.RoleTypeAssistantRole,
  },
  }
  _, err = client.Thread.AddMessages(ctx, thread1ID, addReq1)
  if err != nil {
      fmt.Printf("Error adding messages to thread 1: %v\n", err)
      return
  }

  msgPtrs2 := make([]*zep.Message, len(messagesThread2))
  for i := range messagesThread2 {
      msgPtrs2[i] = &messagesThread2[i]
  }
  addReq2 := &zep.AddThreadMessagesRequest{
      Messages: msgPtrs2,
      IgnoreRoles: []zep.RoleType{
      zep.RoleTypeAssistantRole,
  },
  }
  _, err = client.Thread.AddMessages(ctx, thread2ID, addReq2)
  if err != nil {
      fmt.Printf("Error adding messages to thread 2: %v\n", err)
      return
  }
  ```
</CodeBlocks>

### Searching/Retrieving

Now that a graph with custom entity and edge types has been created, you may filter node search results by entity type, or edge search results by edge type.

Below, you can see the examples that were created from our data of each of the entity and edge types that we defined:

<CodeBlocks>
  ```python
  search_results_restaurants = client.graph.search(
      user_id=user_id,
      query="Take me to a restaurant",
      scope="nodes",
      search_filters={
          "node_labels": ["Restaurant"]
      },
      limit=1,
  )
  node = search_results_restaurants.nodes[0]
  print(f"Node name: {node.name}")
  print(f"Node labels: {node.labels}")
  print(f"Cuisine type: {node.attributes.get('cuisine_type')}")
  print(f"Dietary accommodation: {node.attributes.get('dietary_accommodation')}")
  ```

  ```typescript
  let searchResults = await client.graph.search({
      userId: userId,
      query: "Take me to a restaurant",
      scope: "nodes",
      searchFilters: { nodeLabels: ["Restaurant"] },
      limit: 1,
  });
  if (searchResults.nodes && searchResults.nodes.length > 0) {
      const node = searchResults.nodes[0];
      console.log(`Node name: ${node.name}`);
      console.log(`Node labels: ${node.labels}`);
      console.log(`Cuisine type: ${node.attributes?.cuisine_type}`);
      console.log(`Dietary accommodation: ${node.attributes?.dietary_accommodation}`);
  }
  ```

  ```go
  searchFiltersRestaurants := zep.SearchFilters{NodeLabels: []string{"Restaurant"}}
  searchResultsRestaurants, err := client.Graph.Search(
      ctx,
      &zep.GraphSearchQuery{
          UserID:        zep.String(userID),
          Query:         "Take me to a restaurant",
          Scope:         zep.GraphSearchScopeNodes.Ptr(),
          SearchFilters: &searchFiltersRestaurants,
          Limit:         zep.Int(1),
      },
  )
  if err != nil {
      fmt.Printf("Error searching graph (Restaurant node): %v\n", err)
      return
  }
  if len(searchResultsRestaurants.Nodes) > 0 {
      node := searchResultsRestaurants.Nodes[0]
      fmt.Printf("Node name: %s\n", node.Name)
      fmt.Printf("Node labels: %v\n", node.Labels)
      fmt.Printf("Cuisine type: %v\n", node.Attributes["cuisine_type"])
      fmt.Printf("Dietary accommodation: %v\n", node.Attributes["dietary_accommodation"])
  }
  ```
</CodeBlocks>

```text
Node name: Green Leaf Cafe
Node labels: Entity,Restaurant
Cuisine type: undefined
Dietary accommodation: vegetarian
```

<CodeBlocks>
  ```python
  search_results_audiobook_nodes = client.graph.search(
      user_id=user_id,
      query="Play an audiobook",
      scope="nodes",
      search_filters={
          "node_labels": ["Audiobook"]
      },
      limit=1,
  )
  node = search_results_audiobook_nodes.nodes[0]
  print(f"Node name: {node.name}")
  print(f"Node labels: {node.labels}")
  print(f"Genre: {node.attributes.get('genre')}")
  ```

  ```typescript
  searchResults = await client.graph.search({
      userId: userId,
      query: "Play an audiobook",
      scope: "nodes",
      searchFilters: { nodeLabels: ["Audiobook"] },
      limit: 1,
  });
  if (searchResults.nodes && searchResults.nodes.length > 0) {
      const node = searchResults.nodes[0];
      console.log(`Node name: ${node.name}`);
      console.log(`Node labels: ${node.labels}`);
      console.log(`Genre: ${node.attributes?.genre}`);
  }
  ```

  ```go
  searchFiltersAudiobook := zep.SearchFilters{NodeLabels: []string{"Audiobook"}}
  searchResultsAudiobook, err := client.Graph.Search(
      ctx,
      &zep.GraphSearchQuery{
          UserID:        zep.String(userID),
          Query:         "Play an audiobook",
          Scope:         zep.GraphSearchScopeNodes.Ptr(),
          SearchFilters: &searchFiltersAudiobook,
          Limit:         zep.Int(1),
      },
  )
  if err != nil {
      fmt.Printf("Error searching graph (Audiobook node): %v\n", err)
      return
  }
  if len(searchResultsAudiobook.Nodes) > 0 {
      node := searchResultsAudiobook.Nodes[0]
      fmt.Printf("Node name: %s\n", node.Name)
      fmt.Printf("Node labels: %v\n", node.Labels)
      fmt.Printf("Genre: %v\n", node.Attributes["genre"])
  }
  ```
</CodeBlocks>

```text
Node name: 7 habits of highly effective people
Node labels: Entity,Audiobook
Genre: undefined
```

<CodeBlocks>
  ```python
  search_results_visits = client.graph.search(
      user_id=user_id,
      query="Take me to a restaurant",
      scope="edges",
      search_filters={
          "edge_types": ["RESTAURANT_VISIT"]
      },
      limit=1,
  )
  edge = search_results_visits.edges[0]
  print(f"Edge fact: {edge.fact}")
  print(f"Edge type: {edge.name}")
  print(f"Restaurant name: {edge.attributes.get('restaurant_name')}")
  ```

  ```typescript
  searchResults = await client.graph.search({
      userId: userId,
      query: "Take me to a restaurant",
      scope: "edges",
      searchFilters: { edgeTypes: ["RESTAURANT_VISIT"] },
      limit: 1,
  });
  if (searchResults.edges && searchResults.edges.length > 0) {
      const edge = searchResults.edges[0];
      console.log(`Edge fact: ${edge.fact}`);
      console.log(`Edge type: ${edge.name}`);
      console.log(`Restaurant name: ${edge.attributes?.restaurant_name}`);
  }
  ```

  ```go
  searchFiltersVisits := zep.SearchFilters{EdgeTypes: []string{"RESTAURANT_VISIT"}}
  searchResultsVisits, err := client.Graph.Search(
      ctx,
      &zep.GraphSearchQuery{
          UserID:        zep.String(userID),
          Query:         "Take me to a restaurant",
          Scope:         zep.GraphSearchScopeEdges.Ptr(),
          SearchFilters: &searchFiltersVisits,
          Limit:         zep.Int(1),
      },
  )
  if err != nil {
      fmt.Printf("Error searching graph (RESTAURANT_VISIT): %v\n", err)
      return
  }
  if len(searchResultsVisits.Edges) > 0 {
      edge := searchResultsVisits.Edges[0]
      var visit RestaurantVisit
      err := zep.UnmarshalEdgeAttributes(edge.Attributes, &visit)
      if err != nil {
          fmt.Printf("\t\tError converting edge to RestaurantVisit struct: %v\n", err)
      } else {
          fmt.Printf("Edge fact: %s\n", edge.Fact)
          fmt.Printf("Edge type: %s\n", edge.Name)
          fmt.Printf("Restaurant name: %s\n", visit.RestaurantName)
      }
  }
  ```
</CodeBlocks>

```text
Edge fact: User John Doe is going to Green Leaf Cafe
Edge type: RESTAURANT_VISIT
Restaurant name: Green Leaf Cafe
```

<CodeBlocks>
  ```python
  search_results_audiobook_listens = client.graph.search(
      user_id=user_id,
      query="Play an audiobook",
      scope="edges",
      search_filters={
          "edge_types": ["AUDIOBOOK_LISTEN"]
      },
      limit=1,
  )
  edge = search_results_audiobook_listens.edges[0]
  print(f"Edge fact: {edge.fact}")
  print(f"Edge type: {edge.name}")
  print(f"Audiobook title: {edge.attributes.get('audiobook_title')}")
  ```

  ```typescript
  searchResults = await client.graph.search({
      userId: userId,
      query: "Play an audiobook",
      scope: "edges",
      searchFilters: { edgeTypes: ["AUDIOBOOK_LISTEN"] },
      limit: 1,
  });
  if (searchResults.edges && searchResults.edges.length > 0) {
      const edge = searchResults.edges[0];
      console.log(`Edge fact: ${edge.fact}`);
      console.log(`Edge type: ${edge.name}`);
      console.log(`Audiobook title: ${edge.attributes?.audiobook_title}`);
  }
  ```

  ```go
  searchFiltersAudiobookListen := zep.SearchFilters{EdgeTypes: []string{"AUDIOBOOK_LISTEN"}}
  searchResultsAudiobookListen, err := client.Graph.Search(
      ctx,
      &zep.GraphSearchQuery{
          UserID:        zep.String(userID),
          Query:         "Play an audiobook",
          Scope:         zep.GraphSearchScopeEdges.Ptr(),
          SearchFilters: &searchFiltersAudiobookListen,
          Limit:         zep.Int(1),
      },
  )
  if err != nil {
      fmt.Printf("Error searching graph (AUDIOBOOK_LISTEN): %v\n", err)
      return
  }
  if len(searchResultsAudiobookListen.Edges) > 0 {
      edge := searchResultsAudiobookListen.Edges[0]
      var listen AudiobookListen
      err := zep.UnmarshalEdgeAttributes(edge.Attributes, &listen)
      if err != nil {
          fmt.Printf("Error converting edge to AudiobookListen struct: %v\n", err)
      } else {
          fmt.Printf("Edge fact: %s\n", edge.Fact)
          fmt.Printf("Edge type: %s\n", edge.Name)
          fmt.Printf("Audiobook title: %s\n", listen.AudiobookTitle)
      }
  }
  ```
</CodeBlocks>

```text
Edge fact: John Doe requested to play the audiobook '7 habits of highly effective people'
Edge type: AUDIOBOOK_LISTEN
Audiobook title: 7 habits of highly effective people
```

<CodeBlocks>
  ```python
  search_results_dietary_preference = client.graph.search(
      user_id=user_id,
      query="Find some food around here",
      scope="edges",
      search_filters={
          "edge_types": ["DIETARY_PREFERENCE"]
      },
      limit=1,
  )
  edge = search_results_dietary_preference.edges[0]
  print(f"Edge fact: {edge.fact}")
  print(f"Edge type: {edge.name}")
  print(f"Preference type: {edge.attributes.get('preference_type')}")
  print(f"Allergy: {edge.attributes.get('allergy')}")
  ```

  ```typescript
  searchResults = await client.graph.search({
      userId: userId,
      query: "Find some food around here",
      scope: "edges",
      searchFilters: { edgeTypes: ["DIETARY_PREFERENCE"] },
      limit: 1,
  });
  if (searchResults.edges && searchResults.edges.length > 0) {
      const edge = searchResults.edges[0];
      console.log(`Edge fact: ${edge.fact}`);
      console.log(`Edge type: ${edge.name}`);
      console.log(`Preference type: ${edge.attributes?.preference_type}`);
      console.log(`Allergy: ${edge.attributes?.allergy}`);
  }
  ```

  ```go
  searchFiltersDietary := zep.SearchFilters{EdgeTypes: []string{"DIETARY_PREFERENCE"}}
  searchResultsDietary, err := client.Graph.Search(
      ctx,
      &zep.GraphSearchQuery{
          UserID:        zep.String(userID),
          Query:         "Find some food around here",
          Scope:         zep.GraphSearchScopeEdges.Ptr(),
          SearchFilters: &searchFiltersDietary,
          Limit:         zep.Int(1),
      },
  )
  if err != nil {
      fmt.Printf("Error searching graph (DIETARY_PREFERENCE): %v\n", err)
      return
  }
  if len(searchResultsDietary.Edges) > 0 {
      edge := searchResultsDietary.Edges[0]
      var dietary DietaryPreference
      err := zep.UnmarshalEdgeAttributes(edge.Attributes, &dietary)
      if err != nil {
          fmt.Printf("Error converting edge to DietaryPreference struct: %v\n", err)
      } else {
          fmt.Printf("Edge fact: %s\n", edge.Fact)
          fmt.Printf("Edge type: %s\n", edge.Name)
          fmt.Printf("Preference type: %s\n", dietary.PreferenceType)
          fmt.Printf("Allergy: %v\n", dietary.Allergy)
      }
  }
  ```
</CodeBlocks>

```text
Edge fact: User states 'I'm vegetarian' indicating a dietary preference.
Edge type: DIETARY_PREFERENCE
Preference type: vegetarian
Allergy: false
```

Additionally, you can provide multiple types in search filters, and the types will be ORed together:

<CodeBlocks>
  ```python
  search_results_dietary_preference = client.graph.search(
      user_id=user_id,
      query="Find some food around here",
      scope="edges",
      search_filters={
          "edge_types": ["DIETARY_PREFERENCE", "RESTAURANT_VISIT"]
      },
      limit=2,
  )
  for edge in search_results_dietary_preference.edges:
      print(f"Edge fact: {edge.fact}")
      print(f"Edge type: {edge.name}")
      if edge.name == "DIETARY_PREFERENCE":
          print(f"Preference type: {edge.attributes.get('preference_type')}")
          print(f"Allergy: {edge.attributes.get('allergy')}")
      elif edge.name == "RESTAURANT_VISIT":
          print(f"Restaurant name: {edge.attributes.get('restaurant_name')}")
      print("\n")
  ```

  ```typescript
  searchResults = await client.graph.search({
      userId: userId,
      query: "Find some food around here",
      scope: "edges",
      searchFilters: { edgeTypes: ["DIETARY_PREFERENCE", "RESTAURANT_VISIT"] },
      limit: 2,
  });
  if (searchResults.edges && searchResults.edges.length > 0) {
      for (const edge of searchResults.edges) {
          console.log(`Edge fact: ${edge.fact}`);
          console.log(`Edge type: ${edge.name}`);
          if (edge.name === "DIETARY_PREFERENCE") {
              console.log(`Preference type: ${edge.attributes?.preference_type}`);
              console.log(`Allergy: ${edge.attributes?.allergy}`);
          } else if (edge.name === "RESTAURANT_VISIT") {
              console.log(`Restaurant name: ${edge.attributes?.restaurant_name}`);
          }
          console.log("\n");
      }
  }
  ```

  ```go
  searchFiltersDietaryAndRestaurantVisit := zep.SearchFilters{EdgeTypes: []string{"DIETARY_PREFERENCE", "RESTAURANT_VISIT"}}
  searchResultsDietaryAndRestaurantVisit, err := client.Graph.Search(
      ctx,
      &zep.GraphSearchQuery{
          UserID:        zep.String(userID),
          Query:         "Find some food around here",
          Scope:         zep.GraphSearchScopeEdges.Ptr(),
          SearchFilters: &searchFiltersDietaryAndRestaurantVisit,
          Limit:         zep.Int(2),
      },
  )
  if err != nil {
      fmt.Printf("Error searching graph (DIETARY_PREFERENCE and RESTAURANT_VISIT): %v\n", err)
      return
  }
  if len(searchResultsDietaryAndRestaurantVisit.Edges) > 0 {
      for _, edge := range searchResultsDietaryAndRestaurantVisit.Edges {
          switch edge.Name {
          case "DIETARY_PREFERENCE":
              var dietary DietaryPreference
              err := zep.UnmarshalEdgeAttributes(edge.Attributes, &dietary)
              if err != nil {
                  fmt.Printf("Error converting edge to DietaryPreference struct: %v\n", err)
              } else {
                  fmt.Printf("Edge fact: %s\n", edge.Fact)
                  fmt.Printf("Edge type: %s\n", edge.Name)
                  fmt.Printf("Preference type: %s\n", dietary.PreferenceType)
                  fmt.Printf("Allergy: %v\n", dietary.Allergy)
              }
          case "RESTAURANT_VISIT":
              var visit RestaurantVisit
              err := zep.UnmarshalEdgeAttributes(edge.Attributes, &visit)
              if err != nil {
                  fmt.Printf("Error converting edge to RestaurantVisit struct: %v\n", err)
              } else {
                  fmt.Printf("Edge fact: %s\n", edge.Fact)
                  fmt.Printf("Edge type: %s\n", edge.Name)
                  fmt.Printf("Restaurant name: %s\n", visit.RestaurantName)
              }
          default:
              fmt.Printf("Unknown edge type: %s\n", edge.Name)
          }
          fmt.Println()
      }
  }
  ```
</CodeBlocks>

```text
Edge fact: User John Doe is going to Green Leaf Cafe
Edge type: RESTAURANT_VISIT
Restaurant name: Green Leaf Cafe
```

```text
Edge fact: User states 'I'm vegetarian' indicating a dietary preference.
Edge type: DIETARY_PREFERENCE
Preference type: vegetarian
Allergy: false
```

### Important Notes/Tips

Some notes regarding custom entity and edge types:

* The `set_ontology` method overwrites any previously defined custom entity and edge types, so the set of custom entity and edge types is always the list of types provided in the last `set_ontology` method call
* The overall set of entity and edge types for a project includes both the custom entity and edge types you set and the default entity and edge types
* You can overwrite the default entity and edge types by providing custom types with the same names
* Changing the custom entity or edge types will not update previously created nodes or edges. The classification and attributes of existing nodes and edges will stay the same. The only thing that can change existing classifications or attributes is adding data that provides new information.
* When creating custom entity or edge types, avoid using the following attribute names (including in Go struct tags), as they conflict with default attributes: `uuid`, `name`, `graph_id`, `name_embedding`, `summary`, and `created_at`
* **Any custom entity or edge is required to have at least one custom property defined**
* **Tip**: Design custom entity types to represent entities/nouns, and design custom edge types to represent relationships/verbs. Otherwise, your type might be represented in the graph as an edge more often than as a node or vice versa.
* **Tip**: If you have overlapping entity or edge types (e.g. 'Hobby' and 'Hiking'), you can prioritize one type over another by mentioning which to prioritize in the entity or edge type descriptions


# Utilizing Facts and Summaries

> Facts and summaries are extracted from the chat history as a conversation unfolds as well as from business data added to Zep.

## Facts

Facts are precise and time-stamped information stored on [edges](/sdk-reference/graph/edge/get) that capture detailed relationships about specific events. They include `valid_at` and `invalid_at` timestamps, ensuring temporal accuracy and preserving a clear history of changes over time.

### How Zep Updates Facts

When incorporating new data, Zep looks for existing nodes and edges in the graph and decides whether to add new nodes/edges or to update existing ones. An update could mean updating an edge (for example, indicating the previous fact is no longer valid).

Here's an example of how Zep might extract graph data from a chat message, and then update the graph once new information is available:

![graphiti intro slides](file:944922c0-87b1-4b85-8622-6254308407e5)

As shown in the example above, when Kendra initially loves Adidas shoes but later is angry that the shoes broke and states a preference for Puma shoes, Zep attempts to invalidate the fact that Kendra loves Adidas shoes and creates two new facts: "Kendra's Adidas shoes broke" and "Kendra likes Puma shoes".

Zep also looks for dates in all ingested data, such as the timestamp on a chat message or an article's publication date, informing how Zep sets the edge attributes. This assists your agent in reasoning with time.

### The Four Fact Timestamps

Each fact stored on an edge includes four different timestamp attributes that track the lifecycle of that information:

| Edge attribute  | Example                                         |
| :-------------- | :---------------------------------------------- |
| **created\_at** | The time Zep learned that the user got married  |
| **valid\_at**   | The time the user got married                   |
| **invalid\_at** | The time the user got divorced                  |
| **expired\_at** | The time Zep learned that the user got divorced |

The `valid_at` and `invalid_at` attributes for each fact are then included in Zep's Context Block which is given to your agent:

```text
# format: FACT (Date range: from - to)
User account Emily0e62 has a suspended status due to payment failure. (2024-11-14 02:03:58+00:00 - present)
```

## Summaries

Summaries are high-level overviews of entities or concepts stored on [nodes](/sdk-reference/graph/node/get). They provide a broad snapshot of an entity or concept and its relationships to other nodes. Summaries offer an aggregated and concise representation, making it easier to understand key information at a glance.

<Tip title="Choosing Between Facts and Summaries">
  Zep does not recommend relying solely on summaries for grounding LLM responses. While summaries provide a high-level overview, the [Context Block](/retrieving-memory#retrieving-zeps-context-block) should be used since it includes relevant facts (each with valid and invalid timestamps). This ensures that conversations are based on up-to-date and contextually accurate information.
</Tip>

## Adding or Deleting Facts or Summaries

Facts and summaries are generated as part of the ingestion process. If you follow the directions for [adding data to the graph](/adding-data-to-the-graph), new facts and summaries will be created.

Deleting facts and summaries is handled by deleting data from the graph. Facts and summaries will be deleted when you [delete the edge or node](/deleting-data-from-the-graph) they exist on.

***

## \[DEPRECATED] Rating Facts for Relevancy

<Warning>
  **This feature is deprecated.** Fact ratings have been replaced by [user summary instructions](/users#user-summary-instructions), which provide a more flexible and effective way to customize how Zep prioritizes and presents user information.

  We recommend using user summary instructions instead of fact ratings for new implementations.
</Warning>

### Rating Facts for Relevancy

Not all relevant facts are equally important to your specific use-case. For example, a relationship coach app may need to recall important facts about a user's family, but what the user ate for breakfast Friday last week is unimportant.

Fact ratings are a way to help Zep understand the importance of relevant facts to your particular use case. After implementing fact ratings, you can specify a `minRating` when retrieving relevant facts from Zep, ensuring that the memory `context` string contains customized content.

#### Implementing Fact Ratings

The `fact_rating_instruction` framework consists of an instruction and three example facts, one for each of a `high`, `medium`, and `low` rating.  These are passed when [Adding a User graph](/sdk-reference/user/add) or [Adding a graph](/sdk-reference/graph/create) and become a property of the Graph.

#### Example: Fact Rating Implementation

<CodeBlocks>
  ```python Rating Facts for Poignancy
  fact_rating_instruction = """Rate the facts by poignancy. Highly poignant 
  facts have a significant emotional impact or relevance to the user. 
  Facts with low poignancy are minimally relevant or of little emotional
  significance."""
  fact_rating_examples = FactRatingExamples(
      high="The user received news of a family member's serious illness.",
      medium="The user completed a challenging marathon.",
      low="The user bought a new brand of toothpaste.",
  )
  client.user.add(
      user_id=user_id,
      fact_rating_instruction=FactRatingInstruction(
          instruction=fact_rating_instruction,
          examples=fact_rating_examples,
      ),
  )
  ```

  ```python Use Case-Specific Fact Rating
  client.user.add(
      user_id=user_id,
      fact_rating_instruction=FactRatingInstruction(
          instruction="""Rate the facts by how relevant they 
                         are to purchasing shoes.""",
          examples=FactRatingExamples(
              high="The user has agreed to purchase a Reebok running shoe.",
              medium="The user prefers running to cycling.",
              low="The user purchased a dress.",
          ),
      ),
  )
  ```
</CodeBlocks>

All facts are rated on a scale between 0 and 1.

#### Limiting Memory Recall to High-Rating Facts

You can filter the facts that will make it into the context block by setting the `minRating` parameter in [Get User Context](/sdk-reference/thread/get-user-context#request.query.minRating.minRating).

```python
result = client.thread.get_user_context(thread_id, min_rating=0.7)
```


# Debugging

> Debug workflow execution logs for graph operations

Zep provides detailed debugging capabilities to help you troubleshoot and optimize your graph operations. Debug logging captures detailed workflow execution logs that can be invaluable for understanding how your data flows through the system.

## Enabling Debug Logging

Debug logging is enabled from the Project Settings page in your Zep dashboard. Once enabled, debug logging will be active for 60 minutes.

> **Important**: Debug logging will be active for the next 60 minutes. During this time, all workflow executions will have detailed logs captured. You can view these logs in the thread logs dialog for any thread that runs during this period.

## Accessing Debug Logs

Debug logs are available from episode lists for both individual users and graph-wide operations.

<Callout intent="warn">
  **Note**: Debug logs are not supported when adding data or messages in batch operations.
</Callout>

## Viewing Debug Logs

To view debug logs for a specific episode:

1. Navigate to the episode list (either from a user or graph view)
2. Find the episode you want to debug
3. Click on the **Actions** menu for that episode
4. Select **Debug Logs**

This will open a detailed view of the workflow execution logs for that specific episode, showing you:

* Step-by-step execution flow
* Processing timestamps
* Error messages and stack traces
* Performance metrics
* Data transformation details

## Best Practices for Debug Logging

* **Enable selectively**: Only enable debug logging when actively troubleshooting to avoid unnecessary overhead
* **Time-limited threads**: Debug logging automatically disables after 60 minutes to prevent performance impact
* **Review promptly**: Review debug logs within 24 hours. Stale debug logs are removed after 24 hours.


# Adding batch data

> Efficiently add large amounts of data to your graph

The batch add method enables efficient concurrent processing of large amounts of data to your graph. This experimental feature is designed for scenarios where you need to add multiple episodes quickly, such as backfills, document collections, or historical data imports.

<Warning>
  This is an experimental feature. While faster than sequential processing, batch ingestion may result in slightly different graph structure compared to sequential processing due to the concurrent nature of the operation.
</Warning>

## How batch processing works

The batch add method processes episodes concurrently for improved performance while still preserving temporal relationships between episodes. Unlike sequential processing where episodes are handled one at a time, batch processing can handle up to 20 episodes simultaneously.

The batch method works with data with a temporal dimension such as evolving chat histories and can process up to 20 episodes at a time of mixed types (text, json, message).

## When to use batch processing

Batch processing is ideal for:

* Historical data backfills
* Document collection imports
* Large datasets where processing speed is prioritized
* Data with a temporal dimension

Batch processing works for all types of data, including data with a temporal dimension such as evolving chat histories.

## Usage example

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep
  from zep_cloud import EpisodeData
  import json

  client = Zep(
      api_key=API_KEY,
  )

  episodes = [
      EpisodeData(
          data="This is an example text episode.",
          type="text"
      ),
      EpisodeData(
          data=json.dumps({"name": "Eric Clapton", "age": 78, "genre": "Rock"}),
          type="json"
      ),
      EpisodeData(
          data="User: I really enjoyed the concert last night",
          type="message"
      )
  ]

  client.graph.add_batch(episodes=episodes, graph_id=graph_id)
  ```

  ```typescript TypeScript
  import { ZepClient, EpisodeData } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const episodes: EpisodeData[] = [
      {
          data: "This is an example text episode.",
          type: "text"
      },
      {
          data: JSON.stringify({ name: "Eric Clapton", age: 78, genre: "Rock" }),
          type: "json"
      },
      {
          data: "User: I really enjoyed the concert last night",
          type: "message"
      }
  ];

  await client.graph.addBatch({ graphId, episodes });
  ```

  ```go Go
  import (
      "context"
      "encoding/json"
      "log"
      
      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
  )

  jsonData, _ := json.Marshal(map[string]interface{}{
      "name": "Eric Clapton", 
      "age": 78, 
      "genre": "Rock",
  })

  batchReq := &v3.AddDataBatchRequest{
      Episodes: []*v3.EpisodeData{
          {
              Data: "This is an example text episode.",
              Type: v3.GraphDataTypeText,
          },
          {
              Data: string(jsonData),
              Type: v3.GraphDataTypeJSON,
          },
          {
              Data: "User: I really enjoyed the concert last night",
              Type: v3.GraphDataTypeMessage,
          },
      },
      GraphID: &graphID,
  }

  resp, err := client.Graph.AddBatch(context.TODO(), batchReq)
  if err != nil {
      log.Fatalf("Failed to add batch episodes: %v", err)
  }
  ```
</CodeBlocks>

## Adding batch message data to threads

In addition to adding batch data to your graph, you can add batch message data directly into user threads. This functionality is important when you want to maintain the structure of threads for your user data, which can affect how the `thread.get_user_context()` method works since it relies on the past messages of a given thread.

<Note>
  The `thread.add_messages_batch` operation supports a maximum of 30 messages per batch.
</Note>

<CodeBlocks>
  ```python Python
  from zep_cloud import Zep
  from zep_cloud.types import Message, RoleType

  client = Zep(api_key=API_KEY)

  # Create multiple messages for batch addition
  messages = [
      Message(
          content="Hello, I need help with my account",
          role="user",
          name="customer"
      ),
      Message(
          content="I'd be happy to help you with your account. What specific issue are you experiencing?",
          role="assistant"
      ),
      Message(
          content="I can't access my dashboard and keep getting an error",
          role="user",
          name="customer"
      ),
      Message(
          content="Let me help you troubleshoot that. Can you tell me what error message you're seeing?",
          role="assistant"
      )
  ]

  # Add messages in batch to create/populate a thread
  response = client.thread.add_messages_batch(
      thread_id="your_thread_id",
      messages=messages,
      return_context=True
  )
  ```

  ```typescript TypeScript
  import { ZepClient, AddThreadMessagesRequest } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const request: AddThreadMessagesRequest = {
    messages: [
      {
        content: "Hello, I need help with my account",
        role: "user",
        name: "customer"
      },
      {
        content: "I'd be happy to help you with your account. What specific issue are you experiencing?",
        role: "assistant"
      },
      {
        content: "I can't access my dashboard and keep getting an error",
        role: "user",
        name: "customer"
      },
      {
        content: "Let me help you troubleshoot that. Can you tell me what error message you're seeing?",
        role: "assistant"
      }
    ],
    returnContext: true
  };

  // Use addMessagesBatch for concurrent processing (useful for data migrations)
  await client.thread.addMessagesBatch("your_thread_id", request);
  ```

  ```go Go
  import (
      "context"
      "github.com/getzep/zep-go/v3"
  )

  ctx := context.Background()

  // Add messages in batch to create/populate a thread
  _, err := client.Thread.AddMessagesBatch(ctx, "your_thread_id", &zep.AddThreadMessagesRequest{
      Messages: []*zep.Message{
          {
              Content: "Hello, I need help with my account",
              Role:    "user",
              Name:    zep.String("customer"),
          },
          {
              Content: "I'd be happy to help you with your account. What specific issue are you experiencing?",
              Role:    "assistant",
          },
          {
              Content: "I can't access my dashboard and keep getting an error",
              Role:    "user", 
              Name:    zep.String("customer"),
          },
          {
              Content: "Let me help you troubleshoot that. Can you tell me what error message you're seeing?",
              Role:    "assistant",
          },
      },
      ReturnContext: zep.Bool(true),
  })
  if err != nil {
      // Handle error
  }
  ```
</CodeBlocks>

## Important details

* Maximum of 20 episodes per batch
* Episodes can be of mixed types (text, json, message)
* As an experimental feature, may produce slightly different graph structure compared to sequential processing
* Each episode still respects the 10,000 character limit

## Data size and chunking

The same data size limits apply to batch processing as sequential processing. Each episode in the batch is limited to 10,000 characters. For larger documents, chunk them into smaller episodes before adding to the batch.

For chunking strategies and best practices, see the [data size limit and chunking section](/adding-data-to-the-graph#data-size-limit-and-chunking) in the main adding data guide.


# Reading Data from the Graph

Zep provides APIs to read Edges, Nodes, and Episodes from the graph. These elements can be retrieved individually using their `UUID`, or as lists associated with a specific `user_id` or `graph_id`. The latter method returns all objects within the user's or graph's graph.

Examples of each retrieval method are provided below.

## Reading Edges

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  edge = client.graph.edge.get(edgeUuid)
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const edge = await client.graph.edge.get(edgeUuid);
  ```

  ```go Go
  package main

  import (
      "context"
      "fmt"
      "log"

      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  func main() {
      ctx := context.Background()

      zepClient := client.NewClient(option.WithAPIKey(apiKey))

      edge, err := zepClient.Graph.Edge.Get(ctx, edgeUUID)
      if err != nil {
          log.Fatal(err)
      }

      fmt.Printf("Edge: %+v\n", edge)
  }
  ```
</CodeBlocks>

## Reading Nodes

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  node = client.graph.node.get_by_user(userUuid)
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const node = await client.graph.node.getByUser(userUuid);
  ```

  ```go Go
  package main

  import (
      "context"
      "fmt"
      "log"

      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  func main() {
      ctx := context.Background()

      zepClient := client.NewClient(option.WithAPIKey(apiKey))

      nodes, err := zepClient.Graph.Node.GetByUserID(ctx, userUUID, nil)
      if err != nil {
          log.Fatal(err)
      }

      fmt.Printf("Nodes: %+v\n", nodes)
  }
  ```
</CodeBlocks>

## Reading Episodes

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  episode = client.graph.episode.get_by_graph_id(graph_uuid)
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  const episode = client.graph.episode.getByGraphId(graph_uuid);
  ```

  ```go Go
  package main

  import (
      "context"
      "fmt"
      "log"

      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  func main() {
      ctx := context.Background()

      zepClient := client.NewClient(option.WithAPIKey(apiKey))

      episodes, err := zepClient.Graph.Episode.GetByGraphID(ctx, graphUUID, nil)
      if err != nil {
          log.Fatal(err)
      }

      fmt.Printf("Episodes: %+v\n", episodes)
  }
  ```
</CodeBlocks>


# Deleting Data from the Graph

## Delete an Edge

Here's how to delete an edge from a graph:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  client.graph.edge.delete(uuid_="your_edge_uuid")
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  await client.graph.edge.delete("your_edge_uuid");
  ```

  ```go Go
  import (
      "context"
      "log"

      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  ctx := context.TODO()

  zepClient := client.NewClient(option.WithAPIKey(apiKey))

  _, err := zepClient.Graph.Edge.Delete(ctx, "your_edge_uuid")
  if err != nil {
      log.Fatal("Error deleting edge:", err)
  }
  ```
</CodeBlocks>

Note that when you delete an edge, it never deletes the associated nodes, even if it means there will be a node with no edges.

## Delete an Episode

<Note>
  Deleting an episode does not regenerate the names or summaries of nodes shared with other episodes. This episode information may still exist within these nodes. If an episode invalidates a fact, and the episode is deleted, the fact will remain marked as invalidated.
</Note>

When you delete an [episode](/graphiti/graphiti/adding-episodes), it will delete all the edges associated with it, and it will delete any nodes that are only attached to that episode. Nodes that are also attached to another episode will not be deleted.

Here's how to delete an episode from a graph:

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(
      api_key=API_KEY,
  )

  client.graph.episode.delete(uuid_="episode_uuid")
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  await client.graph.episode.delete("episode_uuid");
  ```

  ```go Go
  import (
      "context"
      "log"

      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  ctx := context.TODO()

  zepClient := client.NewClient(option.WithAPIKey(apiKey))

  _, err := zepClient.Graph.Episode.Delete(ctx, "episode_uuid")
  if err != nil {
      log.Fatal("Error deleting episode:", err)
  }
  ```
</CodeBlocks>

## Delete a Node

This feature is coming soon.


# Check Data Ingestion Status

Data added to Zep is processed asynchronously and can take a few seconds to a few minutes to finish processing. In this recipe, we show how to check whether a given data upload request (also known as an [Episode](/graphiti/graphiti/adding-episodes)) is finished processing by polling Zep with the `graph.episode.get` method.

First, let's create a user:

<CodeBlocks>
  ```python
  import os
  import uuid
  import time
  from dotenv import find_dotenv, load_dotenv
  from zep_cloud.client import Zep

  load_dotenv(dotenv_path=find_dotenv())

  client = Zep(api_key=os.environ.get("ZEP_API_KEY"))
  uuid_value = uuid.uuid4().hex[:4]
  user_id = "-" + uuid_value
  client.user.add(
      user_id=user_id,
      first_name = "John",
      last_name = "Doe",
      email="john.doe@example.com"
  )
  ```

  ```typescript
  import { ZepClient } from "@getzep/zep-cloud";
  import * as dotenv from "dotenv";
  import { v4 as uuidv4 } from 'uuid';

  // Load environment variables
  dotenv.config();

  const client = new ZepClient({ apiKey: process.env.ZEP_API_KEY || "" });
  const uuidValue = uuidv4().substring(0, 4);
  const userId = "-" + uuidValue;

  async function main() {
    // Add user
    await client.user.add({
      userId: userId,
      firstName: "John",
      lastName: "Doe",
      email: "john.doe@example.com"
    });
  ```

  ```go
  package main

  import (
  	"context"
  	"fmt"
  	"os"
  	"strings"
  	"time"

  	"github.com/getzep/zep-go/v3"
  	zepclient "github.com/getzep/zep-go/v3/client"
  	"github.com/getzep/zep-go/v3/option"
  	"github.com/google/uuid"
  	"github.com/joho/godotenv"
  )

  func main() {
  	// Load .env file
  	err := godotenv.Load()
  	if err != nil {
  		fmt.Println("Warning: Error loading .env file:", err)
  		// Continue execution as environment variables might be set in the system
  	}

  	// Get API key from environment variable
  	apiKey := os.Getenv("ZEP_API_KEY")
  	if apiKey == "" {
  		fmt.Println("ZEP_API_KEY environment variable is not set")
  		return
  	}

  	// Initialize Zep client
  	client := zepclient.NewClient(
  		option.WithAPIKey(apiKey),
  	)

  	// Create a UUID
  	uuidValue := strings.ToLower(uuid.New().String()[:4])

  	// Create user ID
  	userID := "-" + uuidValue

  	// Create context
  	ctx := context.Background()

  	// Add a user
  	userRequest := &zep.CreateUserRequest{
  		UserID:    zep.String(userID),
  		FirstName: zep.String("John"),
  		LastName:  zep.String("Doe"),
  		Email:     zep.String("john.doe@example.com"),
  	}
  	_, err = client.User.Add(ctx, userRequest)
  	if err != nil {
  		fmt.Printf("Error creating user: %v\n", err)
  		return
  	}
  ```
</CodeBlocks>

Now, let's add some data and immediately try to search for that data; because data added to Zep is processed asynchronously and can take a few seconds to a few minutes to finish processing, our search results do not have the data we just added:

<CodeBlocks>
  ```python
  episode = client.graph.add(
      user_id=user_id,
      type="text", 
      data="The user is an avid fan of Eric Clapton"
  )

  search_results = client.graph.search(
      user_id=user_id,
      query="Eric Clapton",
      scope="nodes",
      limit=1,
      reranker="cross_encoder",
  )

  print(search_results.nodes)
  ```

  ```typescript
    // Add episode to graph
    const episode = await client.graph.add({
      userId: userId,
      type: "text",
      data: "The user is an avid fan of Eric Clapton"
    });

    // Search for nodes related to Eric Clapton
    const searchResults = await client.graph.search({
      userId: userId,
      query: "Eric Clapton",
      scope: "nodes",
      limit: 1,
      reranker: "cross_encoder"
    });

    console.log(searchResults.nodes);
  ```

  ```go
  	// Add a new episode to the graph
  	episode, err := client.Graph.Add(ctx, &zep.AddDataRequest{
  		GraphID: zep.String(userID),
  		Type:    zep.GraphDataTypeText.Ptr(),
  		Data:    zep.String("The user is an avid fan of Eric Clapton"),
  	})
  	if err != nil {
  		fmt.Printf("Error adding episode to graph: %v\n", err)
  		return
  	}

  	// Search for the data
  	searchResults, err := client.Graph.Search(ctx, &zep.GraphSearchQuery{
  		UserID:  zep.String(userID),
  		Query:   "Eric Clapton",
  		Scope:   zep.GraphSearchScopeNodes.Ptr(),
  		Limit:   zep.Int(1),
  		Reranker: zep.RerankerCrossEncoder.Ptr(),
  	})
  	if err != nil {
  		fmt.Printf("Error searching graph: %v\n", err)
  		return
  	}

  	fmt.Println(searchResults.Nodes)
  ```
</CodeBlocks>

```text
None
```

We can check the status of the episode to see when it has finished processing, using the episode returned from the `graph.add` method and the `graph.episode.get` method:

<CodeBlocks>
  ```python
  while True:
      episode = client.graph.episode.get(
          uuid_=episode.uuid_,
      )
      if episode.processed:
          print("Episode processed successfully")
          break
      print("Waiting for episode to process...")
      time.sleep(1)
  ```

  ```typescript
    // Check if episode is processed
    const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
    
    let processedEpisode = await client.graph.episode.get(episode.uuid);
    
    while (!processedEpisode.processed) {
      console.log("Waiting for episode to process...");
      await sleep(1000); // Sleep for 1 second
      processedEpisode = await client.graph.episode.get(episode.uuid);
    }
    
    console.log("Episode processed successfully");
  ```

  ```go
  	// Wait for the episode to be processed
  	for {
  		episodeStatus, err := client.Graph.Episode.Get(
  			ctx,
  			episode.UUID,
  		)
  		if err != nil {
  			fmt.Printf("Error getting episode: %v\n", err)
  			return
  		}

  		if episodeStatus.Processed != nil && *episodeStatus.Processed {
  			fmt.Println("Episode processed successfully")
  			break
  		}

  		fmt.Println("Waiting for episode to process...")
  		time.Sleep(1 * time.Second)
  	}
  ```
</CodeBlocks>

```text
Waiting for episode to process...
Waiting for episode to process...
Waiting for episode to process...
Waiting for episode to process...
Waiting for episode to process...
Episode processed successfully
```

Now that the episode has finished processing, we can search for the data we just added, and this time we get a result:

<CodeBlocks>
  ```python
  search_results = client.graph.search(
      user_id=user_id,
      query="Eric Clapton",
      scope="nodes",
      limit=1,
      reranker="cross_encoder",
  )

  print(search_results.nodes)
  ```

  ```typescript
    // Search again after processing
    const finalSearchResults = await client.graph.search({
      userId: userId,
      query: "Eric Clapton",
      scope: "nodes",
      limit: 1,
      reranker: "cross_encoder"
    });

    console.log(finalSearchResults.nodes);
  }

  // Execute the main function
  main().catch(error => console.error("Error:", error));
  ```

  ```go
  	// Search again after processing
  	searchResults, err = client.Graph.Search(ctx, &zep.GraphSearchQuery{
  		UserID:  zep.String(userID),
  		Query:   "Eric Clapton",
  		Scope:   zep.GraphSearchScopeNodes.Ptr(),
  		Limit:   zep.Int(1),
  		Reranker: zep.RerankerCrossEncoder.Ptr(),
  	})
  	if err != nil {
  		fmt.Printf("Error searching graph: %v\n", err)
  		return
  	}

  	fmt.Println(searchResults.Nodes)
  }
  ```
</CodeBlocks>

```text
[EntityNode(attributes={'category': 'Music', 'labels': ['Entity', 'Preference']}, created_at='2025-04-05T00:17:59.66565Z', labels=['Entity', 'Preference'], name='Eric Clapton', summary='The user is an avid fan of Eric Clapton.', uuid_='98808054-38ad-4cba-ba07-acd5f7a12bc0', graph_id='6961b53f-df05-48bb-9b8d-b2702dd72045')]
```


# Customize Your Context Block

When [searching the graph](/searching-the-graph) instead of [using Zep's Context Block](/retrieving-memory#retrieving-zeps-context-block), you need to use the search results to create a custom context block. In this recipe, we will demonstrate how to build a custom Context Block using the [graph search API](/searching-the-graph). We will also use the [custom entity and edge types feature](/customizing-graph-structure#custom-entity-and-edge-types), though using this feature is optional.

# Add data

First, we define our [custom entity and edge types](/customizing-graph-structure#definition-1), create a user, and add some example data:

<CodeBlocks>
  ```python
  import uuid
  from zep_cloud import Message
  from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel, EntityBoolean
  from zep_cloud import EntityEdgeSourceTarget
  from pydantic import Field

  class Restaurant(EntityModel):
      """
      Represents a specific restaurant.
      """
      cuisine_type: EntityText = Field(description="The cuisine type of the restaurant, for example: American, Mexican, Indian, etc.", default=None)
      dietary_accommodation: EntityText = Field(description="The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc.", default=None)

  class RestaurantVisit(EdgeModel):
      """
      Represents the fact that the user visited a restaurant.
      """
      restaurant_name: EntityText = Field(description="The name of the restaurant the user visited", default=None)

  class DietaryPreference(EdgeModel):
      """
      Represents the fact that the user has a dietary preference or dietary restriction.
      """
      preference_type: EntityText = Field(description="Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc.", default=None)
      allergy: EntityBoolean = Field(description="Whether this dietary preference represents a user allergy: True or false", default=None)

  client.graph.set_ontology(
      entities={
          "Restaurant": Restaurant,
      },
      edges={
          "RESTAURANT_VISIT": (
              RestaurantVisit,
              [EntityEdgeSourceTarget(source="User", target="Restaurant")]
          ),
          "DIETARY_PREFERENCE": (
              DietaryPreference,
              [EntityEdgeSourceTarget(source="User")]
          ),
      }
  )

  messages_thread1 = [
      Message(content="Take me to a lunch place", role="user", name="John Doe"),
      Message(content="How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", role="assistant", name="Assistant"),
      Message(content="Do any of those have vegetarian options? I’m vegetarian", role="user", name="John Doe"),
      Message(content="Yes, Green Leaf Cafe has vegetarian options", role="assistant", name="Assistant"),
      Message(content="Let’s go to Green Leaf Cafe", role="user", name="John Doe"),
      Message(content="Navigating to Green Leaf Cafe", role="assistant", name="Assistant"),
  ]

  messages_thread2 = [
      Message(content="Take me to dessert", role="user", name="John Doe"),
      Message(content="How about getting some ice cream?", role="assistant", name="Assistant"),
      Message(content="I can't have ice cream, I'm lactose intolerant, but I'm craving a chocolate chip cookie", role="user", name="John Doe"),
      Message(content="Sure, there's Insomnia Cookies nearby.", role="assistant", name="Assistant"),
      Message(content="Perfect, let's go to Insomnia Cookies", role="user", name="John Doe"),
      Message(content="Navigating to Insomnia Cookies.", role="assistant", name="Assistant"),
  ]

  user_id = f"user-{uuid.uuid4()}"
  client.user.add(user_id=user_id, first_name="John", last_name="Doe", email="john.doe@example.com")

  thread1_id = f"thread-{uuid.uuid4()}"
  thread2_id = f"thread-{uuid.uuid4()}"
  client.thread.create(thread_id=thread1_id, user_id=user_id)
  client.thread.create(thread_id=thread2_id, user_id=user_id)

  client.thread.add_messages(thread_id=thread1_id, messages=messages_thread1, ignore_roles=["assistant"])
  client.thread.add_messages(thread_id=thread2_id, messages=messages_thread2, ignore_roles=["assistant"])
  ```

  ```typescript
  import { entityFields, EntityType, EdgeType } from "@getzep/zep-cloud/wrapper/ontology";
  import { v4 as uuidv4 } from "uuid";
  import type { Message } from "@getzep/zep-cloud/api";

  const RestaurantSchema: EntityType = {
      description: "Represents a specific restaurant.",
      fields: {
          cuisine_type: entityFields.text("The cuisine type of the restaurant, for example: American, Mexican, Indian, etc."),
          dietary_accommodation: entityFields.text("The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc."),
      },
  };

  const RestaurantVisit: EdgeType = {
      description: "Represents the fact that the user visited a restaurant.",
      fields: {
          restaurant_name: entityFields.text("The name of the restaurant the user visited"),
      },
      sourceTargets: [
          { source: "User", target: "Restaurant" },
      ],
  };

  const DietaryPreference: EdgeType = {
      description: "Represents the fact that the user has a dietary preference or dietary restriction.",
      fields: {
          preference_type: entityFields.text("Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc."),
          allergy: entityFields.boolean("Whether this dietary preference represents a user allergy: True or false"),
      },
      sourceTargets: [
          { source: "User" },
      ],
  };

  await client.graph.setOntology(
      {
          Restaurant: RestaurantSchema,
      },
      {
          RESTAURANT_VISIT: RestaurantVisit,
          DIETARY_PREFERENCE: DietaryPreference,
      }
  );

  const messagesthread1: Message[] = [
      { content: "Take me to a lunch place", role: "user", name: "John Doe" },
      { content: "How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", role: "assistant", name: "Assistant" },
      { content: "Do any of those have vegetarian options? I’m vegetarian", role: "user", name: "John Doe" },
      { content: "Yes, Green Leaf Cafe has vegetarian options", role: "assistant", name: "Assistant" },
      { content: "Let’s go to Green Leaf Cafe", role: "user", name: "John Doe" },
      { content: "Navigating to Green Leaf Cafe", role: "assistant", name: "Assistant" },
  ];

  const messagesthread2: Message[] = [
      { content: "Take me to dessert", role: "user", name: "John Doe" },
      { content: "How about getting some ice cream?", role: "assistant", name: "Assistant" },
      { content: "I can't have ice cream, I'm lactose intolerant, but I'm craving a chocolate chip cookie", role: "user", name: "John Doe" },
      { content: "Sure, there's Insomnia Cookies nearby.", role: "assistant", name: "Assistant" },
      { content: "Perfect, let's go to Insomnia Cookies", role: "user", name: "John Doe" },
      { content: "Navigating to Insomnia Cookies.", role: "assistant", name: "Assistant" },
  ];

  let userId = `user-${uuidv4()}`;
  await client.user.add({ userId, firstName: "John", lastName: "Doe", email: "john.doe@example.com" });

  const thread1Id = `thread-${uuidv4()}`;
  const thread2Id = `thread-${uuidv4()}`;
  await client.thread.create({ threadId: thread1Id, userId });
  await client.thread.create({ threadId: thread2Id, userId });

  await client.thread.addMessages(thread1Id, { messages: messagesthread1, ignoreRoles: ["assistant"] });
  await client.thread.addMessages(thread2Id, { messages: messagesthread2, ignoreRoles: ["assistant"] });
  ```

  ```go
  import (
  	"github.com/getzep/zep-go/v3"
  	"github.com/google/uuid"
  )

  type Restaurant struct {
  	zep.BaseEntity `name:"Restaurant" description:"Represents a specific restaurant."`
  	CuisineType           string `description:"The cuisine type of the restaurant, for example: American, Mexican, Indian, etc." json:"cuisine_type,omitempty"`
  	DietaryAccommodation  string `description:"The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc." json:"dietary_accommodation,omitempty"`
  }

  type RestaurantVisit struct {
  	zep.BaseEdge `name:"RESTAURANT_VISIT" description:"Represents the fact that the user visited a restaurant."`
  	RestaurantName string `description:"The name of the restaurant the user visited" json:"restaurant_name,omitempty"`
  }

  type DietaryPreference struct {
  	zep.BaseEdge `name:"DIETARY_PREFERENCE" description:"Represents the fact that the user has a dietary preference or dietary restriction."`
  	PreferenceType string `description:"Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc." json:"preference_type,omitempty"`
  	Allergy        bool   `description:"Whether this dietary preference represents a user allergy: True or false" json:"allergy,omitempty"`
  }

  _, err = client.Graph.SetOntology(
  	ctx,
  	[]zep.EntityDefinition{
  		Restaurant{},
  	},
  	[]zep.EdgeDefinitionWithSourceTargets{
  		{
  			EdgeModel: RestaurantVisit{},
  			SourceTargets: []zep.EntityEdgeSourceTarget{
  				{
  					Source: zep.String("User"),
  					Target: zep.String("Restaurant"),
  				},
  			},
  		},
  		{
  			EdgeModel: DietaryPreference{},
  			SourceTargets: []zep.EntityEdgeSourceTarget{
  				{
  					Source: zep.String("User"),
  				},
  			},
  		},
  	},
  )
  if err != nil {
  	fmt.Printf("Error setting ontology: %v\n", err)
  	return
  }

  messagesthread1 := []zep.Message{
  	{Content: "Take me to a lunch place", Role: "user", Name: zep.String("John Doe")},
  	{Content: "How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", Role: "assistant", Name: zep.String("Assistant")},
  	{Content: "Do any of those have vegetarian options? I'm vegetarian", Role: "user", Name: zep.String("John Doe")},
  	{Content: "Yes, Green Leaf Cafe has vegetarian options", Role: "assistant", Name: zep.String("Assistant")},
  	{Content: "Let's go to Green Leaf Cafe", Role: "user", Name: zep.String("John Doe")},
  	{Content: "Navigating to Green Leaf Cafe", Role: "assistant", Name: zep.String("Assistant")},
  }
  messagesthread2 := []zep.Message{
  	{Content: "Take me to dessert", Role: "user", Name: zep.String("John Doe")},
  	{Content: "How about getting some ice cream?", Role: "assistant", Name: zep.String("Assistant")},
  	{Content: "I can't have ice cream, I'm lactose intolerant, but I'm craving a chocolate chip cookie", Role: "user", Name: zep.String("John Doe")},
  	{Content: "Sure, there's Insomnia Cookies nearby.", Role: "assistant", Name: zep.String("Assistant")},
  	{Content: "Perfect, let's go to Insomnia Cookies", Role: "user", Name: zep.String("John Doe")},
  	{Content: "Navigating to Insomnia Cookies.", Role: "assistant", Name: zep.String("Assistant")},
  }
  userID := "user-" + uuid.NewString()
  userReq := &zep.CreateUserRequest{
  	UserID:    userID,
  	FirstName: zep.String("John"),
  	LastName:  zep.String("Doe"),
  	Email:     zep.String("john.doe@example.com"),
  }
  _, err = client.User.Add(ctx, userReq)
  if err != nil {
  	fmt.Printf("Error creating user: %v\n", err)
  	return
  }

  thread1ID := "thread-" + uuid.NewString()
  thread2ID := "thread-" + uuid.NewString()

  thread1Req := &zep.CreateThreadRequest{
  	threadID: thread1ID,
  	UserID:    userID,
  }
  thread2Req := &zep.CreateThreadRequest{
  	threadID: thread2ID,
  	UserID:    userID,
  }
  _, err = client.Thread.Create(ctx, thread1Req)
  if err != nil {
  	fmt.Printf("Error creating thread 1: %v\n", err)
  	return
  }
  _, err = client.Thread.Create(ctx, thread2Req)
  if err != nil {
  	fmt.Printf("Error creating thread 2: %v\n", err)
  	return
  }

  msgPtrs1 := make([]*zep.Message, len(messagesthread1))
  for i := range messagesthread1 {
  	msgPtrs1[i] = &messagesthread1[i]
  }
  addReq1 := &zep.AddThreadMessagesRequest{
  	Messages: msgPtrs1,
  	IgnoreRoles: []zep.RoleType{
          zep.RoleTypeAssistantRole,
  	},
  }
  _, err = client.Thread.AddMessages(ctx, thread1ID, addReq1)
  if err != nil {
  	fmt.Printf("Error adding messages to thread 1: %v\n", err)
  	return
  }

  msgPtrs2 := make([]*zep.Message, len(messagesthread2))
  for i := range messagesthread2 {
  	msgPtrs2[i] = &messagesthread2[i]
  }
  addReq2 := &zep.AddThreadMessagesRequest{
  	Messages: msgPtrs2,
  	IgnoreRoles: []zep.RoleType{
  		zep.RoleTypeAssistantRole,
  	},
  }
  _, err = client.Thread.AddMessages(ctx, thread2ID, addReq2)
  if err != nil {
  	fmt.Printf("Error adding messages to thread 2: %v\n", err)
  	return
  }
  ```
</CodeBlocks>

# Example 1: Basic custom context block

## Search

For a basic custom context block, we search the graph for edges and nodes relevant to our custom query string, which typically represents a user message. Note that the default [Context Block](/retrieving-memory#retrieving-zeps-context-block) returned by `thread.get_user_context` uses the past few messages as the query instead.

<Tip>
  These searches can be performed in parallel to reduce latency, using our [async Python client](/quickstart#initialize-the-client), TypeScript promises, or goroutines.
</Tip>

<CodeBlocks>
  ```python
  query = "Find some food around here"

  search_results_nodes = client.graph.search(
      query=query,
      user_id=user_id,
      scope='nodes',
      reranker='cross_encoder',
      limit=10
  )
  search_results_edges = client.graph.search(
      query=query,
      user_id=user_id,
      scope='edges',
      reranker='cross_encoder',
      limit=10
  )
  ```

  ```typescript
  let query = "Find some food around here";

  const searchResultsNodes = await client.graph.search({
      userId: userId,
      query: query,
      scope: "nodes",
      reranker: "cross_encoder",
      limit: 10,
  });

  const searchResultsEdges = await client.graph.search({
      userId: userId,
      query: query,
      scope: "edges",
      reranker: "cross_encoder",
      limit: 10,
  });
  ```

  ```go
  import (
  	"github.com/getzep/zep-go/v2/graph"
  )

  query := "Find some food around here"

  searchResultsNodes, err := client.Graph.Search(
  	ctx,
  	&zep.GraphSearchQuery{
  		UserID:  zep.String(userID),
  		Query:   query,
  		Scope:   zep.GraphSearchScopeNodes.Ptr(),
  		Reranker: zep.RerankerCrossEncoder.Ptr(),
  		Limit:   zep.Int(10),
  	},
  )
  if err != nil {
  	fmt.Printf("Error searching graph (nodes): %v\n", err)
  	return
  }

  searchResultsEdges, err := client.Graph.Search(
  	ctx,
  	&zep.GraphSearchQuery{
  		UserID:  zep.String(userID),
  		Query:   query,
  		Scope:   zep.GraphSearchScopeEdges.Ptr(),
  		Reranker: zep.RerankerCrossEncoder.Ptr(),
  		Limit:   zep.Int(10),
  	},
  )
  if err != nil {
  	fmt.Printf("Error searching graph (edges): %v\n", err)
  	return
  }
  ```
</CodeBlocks>

## Build the context block

Using the search results and a few helper functions, we can build the context block. Note that for nodes, we typically want to unpack the node name and node summary, and for edges we typically want to unpack the fact and the temporal validity information:

<CodeBlocks>
  ```python
  from zep_cloud import EntityEdge, EntityNode

  CONTEXT_STRING_TEMPLATE = """
  FACTS and ENTITIES represent relevant context to the current conversation.
  # These are the most relevant facts and their valid date ranges
  # format: FACT (Date range: from - to)
  # NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
  #       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
  <FACTS>
  {facts}
  </FACTS>

  # These are the most relevant entities
  # ENTITY_NAME: entity summary
  <ENTITIES>
  {entities}
  </ENTITIES>
  """


  def format_fact(edge: EntityEdge) -> str:
      valid_at = edge.valid_at if edge.valid_at is not None else "date unknown"
      invalid_at = edge.invalid_at if edge.invalid_at is not None else "present"
      formatted_fact = f"  - {edge.fact} (Date range: {valid_at} - {invalid_at})"
      return formatted_fact

  def format_entity(node: EntityNode) -> str:
      formatted_entity = f"  - {node.name}: {node.summary}"
      return formatted_entity

  def compose_context_block(edges: list[EntityEdge], nodes: list[EntityNode]) -> str:
      facts = [format_fact(edge) for edge in edges]
      entities = [format_entity(node) for node in nodes]
      return CONTEXT_STRING_TEMPLATE.format(facts='\n'.join(facts), entities='\n'.join(entities))

  edges = search_results_edges.edges
  nodes = search_results_nodes.nodes

  context_block = compose_context_block(edges, nodes)
  print(context_block)
  ```

  ```typescript
  import type { EntityEdge, EntityNode } from "@getzep/zep-cloud/api";

  const CONTEXT_STRING_TEMPLATE_1 = `FACTS and ENTITIES represent relevant context to the current conversation.
  # These are the most relevant facts and their valid date ranges
  # format: FACT (Date range: from - to)
  # NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
  #       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
  <FACTS>
  {facts}
  </FACTS>
  # These are the most relevant entities
  # ENTITY_NAME: entity summary
  <ENTITIES>
  {entities}
  </ENTITIES>`;

  function formatFact(edge: EntityEdge): string {
      const validAt = edge.validAt ?? "date unknown";
      const invalidAt = edge.invalidAt ?? "present";
      return `  - ${edge.fact} (Date range: ${validAt} - ${invalidAt})`;
  }

  function formatEntity(node: EntityNode): string {
      return `  - ${node.name}: ${node.summary}`;
  }

  function composeContextBlock1(edges: EntityEdge[], nodes: EntityNode[]): string {
      const facts = edges.map(formatFact).join('\n');
      const entities = nodes.map(formatEntity).join('\n');
      return CONTEXT_STRING_TEMPLATE_1
          .replace('{facts}', facts)
          .replace('{entities}', entities);
  }

  const edges: EntityEdge[] = searchResultsEdges.edges ?? [];
  const nodes: EntityNode[] = searchResultsNodes.nodes ?? [];

  const contextBlock1 = composeContextBlock1(edges, nodes);
  console.log(contextBlock1);
  ```

  ```go
  import (
  	"strings"
  )

  const CONTEXT_STRING_TEMPLATE_1 = `FACTS and ENTITIES represent relevant context to the current conversation.
  # These are the most relevant facts and their valid date ranges
  # format: FACT (Date range: from - to)
  # NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
  #       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
  <FACTS>
  {facts}
  </FACTS>

  # These are the most relevant entities
  # ENTITY_NAME: entity summary
  <ENTITIES>
  {entities}
  </ENTITIES>
  `

  formatFact := func(edge *zep.EntityEdge) string {
  	validAt := "date unknown"
  	if edge.ValidAt != nil && *edge.ValidAt != "" {
  		validAt = *edge.ValidAt
  	}
  	invalidAt := "present"
  	if edge.InvalidAt != nil && *edge.InvalidAt != "" {
  		invalidAt = *edge.InvalidAt
  	}
  	return fmt.Sprintf("  - %s (Date range: %s - %s)", edge.Fact, validAt, invalidAt)
  }

  formatEntity := func(node *zep.EntityNode) string {
  	return fmt.Sprintf("  - %s: %s", node.Name, node.Summary)
  }

  composeContextBlock1 := func(edges []*zep.EntityEdge, nodes []*zep.EntityNode) string {
  	var facts []string
  	for _, edge := range edges {
  		facts = append(facts, formatFact(edge))
  	}
  	var entities []string
  	for _, node := range nodes {
  		entities = append(entities, formatEntity(node))
  	}
  	result := strings.ReplaceAll(CONTEXT_STRING_TEMPLATE_1, "{facts}", strings.Join(facts, "\n"))
  	result = strings.ReplaceAll(result, "{entities}", strings.Join(entities, "\n"))
  	return result
  }

  edges := searchResultsEdges.Edges
  nodes := searchResultsNodes.Nodes

  contextBlock1 := composeContextBlock1(edges, nodes)
  fmt.Println(contextBlock1)
  ```
</CodeBlocks>

```text
FACTS and ENTITIES represent relevant context to the current conversation.
# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
# NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
#       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
<FACTS>
  - User wants to go to dessert (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe wants to go to a lunch place (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe said 'Perfect, let's go to Insomnia Cookies' indicating he will visit Insomnia Cookies. (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe said 'Let’s go to Green Leaf Cafe' indicating intention to visit (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe is craving a chocolate chip cookie (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe states that he is vegetarian. (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe is lactose intolerant (Date range: 2025-06-16T02:17:25Z - present)
</FACTS>
 
# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
  - lunch place: The entity is a lunch place, but no specific details about its cuisine or dietary accommodations are provided.
  - dessert: The entity 'dessert' refers to a preference related to sweet courses typically served at the end of a meal. The context indicates that the user has expressed an interest in going to a dessert place, but no specific dessert or place has been named. The entity is categorized as a Preference and Entity, but no additional attributes are provided or inferred from the messages.
  - Green Leaf Cafe: Green Leaf Cafe is a restaurant that offers vegetarian options, making it suitable for vegetarian diners.
  - user: The user is John Doe, with the email john.doe@example.com. He has shown interest in visiting Green Leaf Cafe, which offers vegetarian options, and has also expressed a preference for lactose-free options, craving a chocolate chip cookie. The user has decided to go to Insomnia Cookies.
  - vegetarian: The user is interested in lunch places such as Panera Bread, Chipotle, and Green Leaf Cafe. They are specifically looking for vegetarian options at these restaurants.
  - chocolate chip cookie: The entity is a chocolate chip cookie, which the user desires as a snack. The user is lactose intolerant and cannot have ice cream, but is craving a chocolate chip cookie.
  - Insomnia Cookies: Insomnia Cookies is a restaurant that offers cookies, including chocolate chip cookies. The user is interested in a dessert and has chosen to go to Insomnia Cookies. No specific cuisine type or dietary accommodations are mentioned in the messages.
  - lactose intolerant: The entity is a preference indicating lactose intolerance, which is a dietary restriction that prevents the individual from consuming lactose, a sugar found in milk and dairy products. The person is specifically craving a chocolate chip cookie but cannot have ice cream due to lactose intolerance.
  - John Doe: The user is John Doe, with user ID user-34c7a6c1-ded6-4797-9620-8b80a5e7820f, email john.doe@example.com, and role user. He inquired about nearby lunch options and vegetarian choices, and expressed a preference for a chocolate chip cookie due to lactose intolerance.
</ENTITIES>
```

# Example 2: Utilizing custom entity and edge types

## Search

For a custom context block that uses custom entity and edge types, we perform multiple searches (with our custom query string) filtering to the custom entity or edge type we want to include in the context block:

<Tip>
  These searches can be performed in parallel to reduce latency, using our [async Python client](/quickstart#initialize-the-client), TypeScript promises, or goroutines.
</Tip>

<CodeBlocks>
  ```python
  query = "Find some food around here"

  search_results_restaurant_visits = client.graph.search(
      query=query,
      user_id=user_id,
      scope='edges',
      search_filters={
          "edge_types": ["RESTAURANT_VISIT"]
      },
      reranker='cross_encoder',
      limit=10
  )
  search_results_dietary_preferences = client.graph.search(
      query=query,
      user_id=user_id,
      scope='edges',
      search_filters={
          "edge_types": ["DIETARY_PREFERENCE"]
      },
      reranker='cross_encoder',
      limit=10
  )
  search_results_restaurants = client.graph.search(
      query=query,
      user_id=user_id,
      scope='nodes',
      search_filters={
          "node_labels": ["Restaurant"]
      },
      reranker='cross_encoder',
      limit=10
  )
  ```

  ```typescript
  query = "Find some food around here";

  const searchResultsRestaurantVisits = await client.graph.search({
      query,
      userId: userId,
      scope: "edges",
      searchFilters: {
          edgeTypes: ["RESTAURANT_VISIT"]
      },
      reranker: "cross_encoder",
      limit: 10,
  });

  const searchResultsDietaryPreferences = await client.graph.search({
      query,
      userId: userId,
      scope: "edges",
      searchFilters: {
          edgeTypes: ["DIETARY_PREFERENCE"]
      },
      reranker: "cross_encoder",
      limit: 10,
  });

  const searchResultsRestaurants = await client.graph.search({
      query,
      userId: userId,
      scope: "nodes",
      searchFilters: {
          nodeLabels: ["Restaurant"]
      },
      reranker: "cross_encoder",
      limit: 10,
  });
  ```

  ```go
  query := "Find some food around here"

  searchFiltersRestaurantVisits := zep.SearchFilters{EdgeTypes: []string{"RESTAURANT_VISIT"}}
  searchResultsRestaurantVisits, err := client.Graph.Search(
  	ctx,
  	&zep.GraphSearchQuery{
  		UserID:        zep.String(userID),
  		Query:         query,
  		Scope:         zep.GraphSearchScopeEdges.Ptr(),
  		SearchFilters: &searchFiltersRestaurantVisits,
  		Reranker:      zep.RerankerCrossEncoder.Ptr(),
  		Limit:         zep.Int(10),
  	},
  )
  if err != nil {
  	fmt.Printf("Error searching graph (RESTAURANT_VISIT edges): %v\n", err)
  	return
  }

  searchFiltersDietaryPreferences := zep.SearchFilters{EdgeTypes: []string{"DIETARY_PREFERENCE"}}
  searchResultsDietaryPreferences, err := client.Graph.Search(
  	ctx,
  	&zep.GraphSearchQuery{
  		UserID:        zep.String(userID),
  		Query:         query,
  		Scope:         zep.GraphSearchScopeEdges.Ptr(),
  		SearchFilters: &searchFiltersDietaryPreferences,
  		Reranker:      zep.RerankerCrossEncoder.Ptr(),
  		Limit:         zep.Int(10),
  	},
  )
  if err != nil {
  	fmt.Printf("Error searching graph (DIETARY_PREFERENCE edges): %v\n", err)
  	return
  }

  searchFiltersRestaurants := zep.SearchFilters{NodeLabels: []string{"Restaurant"}}
  searchResultsRestaurants, err := client.Graph.Search(
  	ctx,
  	&zep.GraphSearchQuery{
  		UserID:        zep.String(userID),
  		Query:         query,
  		Scope:         zep.GraphSearchScopeNodes.Ptr(),
  		SearchFilters: &searchFiltersRestaurants,
  		Reranker:      zep.RerankerCrossEncoder.Ptr(),
  		Limit:         zep.Int(10),
  	},
  )
  if err != nil {
  	fmt.Printf("Error searching graph (Restaurant nodes): %v\n", err)
  	return
  }
  ```
</CodeBlocks>

## Build the context block

Using the search results and a few helper functions, we can compose the context block. Note that in this example, we focus on unpacking the custom attributes of the nodes and edges, but this is a design choice that you can experiment with for your use case.

Note also that we designed the context block template around the custom entity and edge types that we are unpacking into the context block:

<CodeBlocks>
  ```python
  from zep_cloud import EntityEdge, EntityNode

  CONTEXT_STRING_TEMPLATE = """
  PREVIOUS_RESTAURANT_VISITS, DIETARY_PREFERENCES, and RESTAURANTS represent relevant context to the current conversation.
  # These are the most relevant restaurants the user has previously visited
  # format: restaurant_name: RESTAURANT_NAME
  <PREVIOUS_RESTAURANT_VISITS>
  {restaurant_visits}
  </PREVIOUS_RESTAURANT_VISITS>

  # These are the most relevant dietary preferences of the user, whether they represent an allergy, and their valid date ranges
  # format: allergy: True/False; preference_type: PREFERENCE_TYPE (Date range: from - to)
  <DIETARY_PREFERENCES>
  {dietary_preferences}
  </DIETARY_PREFERENCES>

  # These are the most relevant restaurants the user has discussed previously
  # format: name: RESTAURANT_NAME; cuisine_type: CUISINE_TYPE; dietary_accommodation: DIETARY_ACCOMMODATION
  <RESTAURANTS>
  {restaurants}
  </RESTAURANTS>
  """

  def format_edge_with_attributes(edge: EntityEdge, include_timestamps: bool = True) -> str:
      attrs_str = '; '.join(f"{k}: {v}" for k, v in sorted(edge.attributes.items()))
      if include_timestamps:
          valid_at = edge.valid_at if edge.valid_at is not None else "date unknown"
          invalid_at = edge.invalid_at if edge.invalid_at is not None else "present"
          return f"  - {attrs_str} (Date range: {valid_at} - {invalid_at})"
      return f"  - {attrs_str}"

  def format_node_with_attributes(node: EntityNode) -> str:
      attributes = {k: v for k, v in node.attributes.items() if k != "labels"}
      attrs_str = '; '.join(f"{k}: {v}" for k, v in sorted(attributes.items()))
      base = f"  - name: {node.name}; {attrs_str}"
      return base

  def compose_context_block(restaurant_visit_edges: list[EntityEdge], dietary_preference_edges: list[EntityEdge], restaurant_nodes: list[EntityNode]) -> str:
      restaurant_visits = [format_edge_with_attributes(edge, include_timestamps=False) for edge in restaurant_visit_edges]
      dietary_preferences = [format_edge_with_attributes(edge, include_timestamps=True) for edge in dietary_preference_edges]
      restaurant_nodes = [format_node_with_attributes(node) for node in restaurant_nodes]
      return CONTEXT_STRING_TEMPLATE.format(restaurant_visits='\n'.join(restaurant_visits), dietary_preferences='\n'.join(dietary_preferences), restaurants='\n'.join(restaurant_nodes))


  restaurant_visit_edges = search_results_restaurant_visits.edges
  dietary_preference_edges = search_results_dietary_preferences.edges
  restaurant_nodes = search_results_restaurants.nodes

  context_block = compose_context_block(restaurant_visit_edges, dietary_preference_edges, restaurant_nodes)
  print(context_block)
  ```

  ```typescript
  import type { EntityEdge, EntityNode } from "@getzep/zep-cloud/api";

  const CONTEXT_STRING_TEMPLATE_2 = `PREVIOUS_RESTAURANT_VISITS, DIETARY_PREFERENCES, and RESTAURANTS represent relevant context to the current conversation.
  # These are the most relevant restaurants the user has previously visited
  # format: restaurant_name: RESTAURANT_NAME
  <PREVIOUS_RESTAURANT_VISITS>
  {restaurant_visits}
  </PREVIOUS_RESTAURANT_VISITS>

  # These are the most relevant dietary preferences of the user, whether they represent an allergy, and their valid date ranges
  # format: allergy: True/False; preference_type: PREFERENCE_TYPE (Date range: from - to)
  <DIETARY_PREFERENCES>
  {dietary_preferences}
  </DIETARY_PREFERENCES>

  # These are the most relevant restaurants the user has discussed previously
  # format: name: RESTAURANT_NAME; cuisine_type: CUISINE_TYPE; dietary_accommodation: DIETARY_ACCOMMODATION
  <RESTAURANTS>
  {restaurants}
  </RESTAURANTS>`;

  function formatEdgeWithAttributes(edge: EntityEdge, includeTimestamps = true): string {
      const attrs = Object.entries(edge.attributes ?? {})
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([k, v]) => `${k}: ${v}`)
          .join('; ');
      if (includeTimestamps) {
          const validAt = edge.validAt ?? "date unknown";
          const invalidAt = edge.invalidAt ?? "present";
          return `  - ${attrs} (Date range: ${validAt} - ${invalidAt})`;
      }
      return `  - ${attrs}`;
  }

  function formatNodeWithAttributes(node: EntityNode): string {
      const attributes = Object.entries(node.attributes ?? {})
          .filter(([k]) => k !== "labels")
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([k, v]) => `${k}: ${v}`)
          .join('; ');
      return `  - name: ${node.name}; ${attributes}`;
  }

  function composeContextBlock2(
      restaurantVisitEdges: EntityEdge[],
      dietaryPreferenceEdges: EntityEdge[],
      restaurantNodes: EntityNode[]
  ): string {
      const restaurantVisits = restaurantVisitEdges.map(e => formatEdgeWithAttributes(e, false)).join('\n');
      const dietaryPreferences = dietaryPreferenceEdges.map(e => formatEdgeWithAttributes(e, true)).join('\n');
      const restaurants = restaurantNodes.map(n => formatNodeWithAttributes(n)).join('\n');
      return CONTEXT_STRING_TEMPLATE_2
          .replace('{restaurant_visits}', restaurantVisits)
          .replace('{dietary_preferences}', dietaryPreferences)
          .replace('{restaurants}', restaurants);
  }

  const restaurantVisitEdges: EntityEdge[] = searchResultsRestaurantVisits.edges ?? [];
  const dietaryPreferenceEdges: EntityEdge[] = searchResultsDietaryPreferences.edges ?? [];
  const restaurantNodes: EntityNode[] = searchResultsRestaurants.nodes ?? [];

  const contextBlock2 = composeContextBlock2(restaurantVisitEdges, dietaryPreferenceEdges, restaurantNodes);
  console.log(contextBlock2);
  ```

  ```go
  import (
  	"strings"
  )
  	
  const CONTEXT_STRING_TEMPLATE_2 = `PREVIOUS_RESTAURANT_VISITS, DIETARY_PREFERENCES, and RESTAURANTS represent relevant context to the current conversation.
  # These are the most relevant restaurants the user has previously visited
  # format: restaurant_name: RESTAURANT_NAME
  <PREVIOUS_RESTAURANT_VISITS>
  {restaurant_visits}
  </PREVIOUS_RESTAURANT_VISITS>

  # These are the most relevant dietary preferences of the user, whether they represent an allergy, and their valid date ranges
  # format: allergy: True/False; preference_type: PREFERENCE_TYPE (Date range: from - to)
  <DIETARY_PREFERENCES>
  {dietary_preferences}
  </DIETARY_PREFERENCES>

  # These are the most relevant restaurants the user has discussed previously
  # format: name: RESTAURANT_NAME; cuisine_type: CUISINE_TYPE; dietary_accommodation: DIETARY_ACCOMMODATION
  <RESTAURANTS>
  {restaurants}
  </RESTAURANTS>`

  formatEdgeWithAttributes := func(edge *zep.EntityEdge, includeTimestamps bool) string {
  	attrs := make([]string, 0)
  	for _, k := range []string{"allergy", "preference_type", "restaurant_name"} {
  		if v, ok := edge.Attributes[k]; ok {
  			attrs = append(attrs, fmt.Sprintf("%s: %v", k, v))
  		}
  	}
  	attrsStr := strings.Join(attrs, "; ")
  	if includeTimestamps {
  		validAt := "date unknown"
  		if edge.ValidAt != nil && *edge.ValidAt != "" {
  			validAt = *edge.ValidAt
  		}
  		invalidAt := "present"
  		if edge.InvalidAt != nil && *edge.InvalidAt != "" {
  			invalidAt = *edge.InvalidAt
  		}
  		return fmt.Sprintf("  - %s (Date range: %s - %s)", attrsStr, validAt, invalidAt)
  	}
  	return fmt.Sprintf("  - %s", attrsStr)
  }

  formatNodeWithAttributes := func(node *zep.EntityNode) string {
  	attrs := make([]string, 0)
  	for k, v := range node.Attributes {
  		if k == "labels" {
  			continue
  		}
  		attrs = append(attrs, fmt.Sprintf("%s: %v", k, v))
  	}
  	attrsStr := strings.Join(attrs, "; ")
  	return fmt.Sprintf("  - name: %s; %s", node.Name, attrsStr)
  }

  composeContextBlock2 := func(restaurantVisitEdges []*zep.EntityEdge, dietaryPreferenceEdges []*zep.EntityEdge, restaurantNodes []*zep.EntityNode) string {
  	restaurantVisits := make([]string, 0)
  	for _, edge := range restaurantVisitEdges {
  		restaurantVisits = append(restaurantVisits, formatEdgeWithAttributes(edge, false))
  	}
  	dietaryPreferences := make([]string, 0)
  	for _, edge := range dietaryPreferenceEdges {
  		dietaryPreferences = append(dietaryPreferences, formatEdgeWithAttributes(edge, true))
  	}
  	restaurants := make([]string, 0)
  	for _, node := range restaurantNodes {
  		restaurants = append(restaurants, formatNodeWithAttributes(node))
  	}
  	result := strings.ReplaceAll(CONTEXT_STRING_TEMPLATE_2, "{restaurant_visits}", strings.Join(restaurantVisits, "\n"))
  	result = strings.ReplaceAll(result, "{dietary_preferences}", strings.Join(dietaryPreferences, "\n"))
  	result = strings.ReplaceAll(result, "{restaurants}", strings.Join(restaurants, "\n"))
  	return result
  }

  restaurantVisitEdges := searchResultsRestaurantVisits.Edges
  dietaryPreferenceEdges := searchResultsDietaryPreferences.Edges
  restaurantNodes := searchResultsRestaurants.Nodes

  contextBlock2 := composeContextBlock2(restaurantVisitEdges, dietaryPreferenceEdges, restaurantNodes)
  fmt.Println(contextBlock2)
  ```
</CodeBlocks>

```text
PREVIOUS_RESTAURANT_VISITS, DIETARY_PREFERENCES, and RESTAURANTS represent relevant context to the current conversation.
# These are the most relevant restaurants the user has previously visited
# format: restaurant_name: RESTAURANT_NAME
<PREVIOUS_RESTAURANT_VISITS>
  - restaurant_name: Insomnia Cookies
  - restaurant_name: Green Leaf Cafe
</PREVIOUS_RESTAURANT_VISITS>
 
# These are the most relevant dietary preferences of the user, whether they represent an allergy, and their valid date ranges
# format: allergy: True/False; preference_type: PREFERENCE_TYPE (Date range: from - to)
<DIETARY_PREFERENCES>
  - allergy: False; preference_type: vegetarian (Date range: 2025-06-16T02:17:25Z - present)
  - allergy: False; preference_type: lactose intolerance (Date range: 2025-06-16T02:17:25Z - present)
</DIETARY_PREFERENCES>
 
# These are the most relevant restaurants the user has discussed previously
# format: name: RESTAURANT_NAME; cuisine_type: CUISINE_TYPE; dietary_accommodation: DIETARY_ACCOMMODATION
<RESTAURANTS>
  - name: Green Leaf Cafe; dietary_accommodation: vegetarian
  - name: Insomnia Cookies; 
</RESTAURANTS>
```

# Example 3: Basic custom context block with BFS

## Search

For a more advanced custom context block, we can enhance the search results by using Breadth-First Search (BFS) to make them more relevant to the user's recent history. In this example, we retrieve the past several [episodes](/graphiti/graphiti/adding-episodes) and use those episode IDs as the BFS node IDs. We use BFS here to make the search results more relevant to the user's recent history. You can read more about how BFS works in the [Breadth-First Search section](/searching-the-graph#breadth-first-search-bfs) of our searching the graph documentation.

<Tip>
  These searches can be performed in parallel to reduce latency, using our [async Python client](/quickstart#initialize-the-client), TypeScript promises, or goroutines.
</Tip>

<CodeBlocks>
  ```python
  query = "Find some food around here"

  episodes = client.graph.episode.get_by_user_id(
      user_id=user_id,
      lastn=10
  ).episodes

  episode_uuids = [episode.uuid_ for episode in episodes if episode.role_type == 'user']

  search_results_nodes = client.graph.search(
      query=query,
      user_id=user_id,
      scope='nodes',
      reranker='cross_encoder',
      limit=10,
      bfs_origin_node_uuids=episode_uuids
  )
  search_results_edges = client.graph.search(
      query=query,
      user_id=user_id,
      scope='edges',
      reranker='cross_encoder',
      limit=10,
      bfs_origin_node_uuids=episode_uuids
  )
  ```

  ```typescript
  let query = "Find some food around here";

  let episodeResponse = await client.graph.episode.getByUserId(userId, { lastn: 10 });
  let episodeUuids = (episodeResponse.episodes || [])
      .filter((episode) => episode.roleType === "user")
      .map((episode) => episode.uuid);

  const searchResultsNodes = await client.graph.search({
      userId: userId,
      query: query,
      scope: "nodes",
      reranker: "cross_encoder",
      limit: 10,
      bfsOriginNodeUuids: episodeUuids,
  });

  const searchResultsEdges = await client.graph.search({
      userId: userId,
      query: query,
      scope: "edges",
      reranker: "cross_encoder",
      limit: 10,
      bfsOriginNodeUuids: episodeUuids,
  });
  ```

  ```go
  import (
  	"github.com/getzep/zep-go/v2/graph"
  )

  query := "Find some food around here"

  response, err := client.Graph.Episode.GetByUserID(
  	ctx,
  	userID,
  	&graph.EpisodeGetByUserIDRequest{
  		Lastn: zep.Int(10),
  	},
  )
  if err != nil {
  	fmt.Printf("Error getting episodes: %v\n", err)
  	return
  }

  var episodeUUIDs1 []string
  for _, episode := range response.Episodes {
  	if episode.RoleType != nil && *episode.RoleType == zep.RoleTypeUserRole {
  		episodeUUIDs1 = append(episodeUUIDs1, episode.UUID)
  	}
  }

  searchResultsNodes, err := client.Graph.Search(
  	ctx,
  	&zep.GraphSearchQuery{
  		UserID:  zep.String(userID),
  		Query:   query,
  		Scope:   zep.GraphSearchScopeNodes.Ptr(),
  		Reranker: zep.RerankerCrossEncoder.Ptr(),
  		Limit:   zep.Int(10),
  		BfsOriginNodeUUIDs: episodeUUIDs1,
  	},
  )
  if err != nil {
  	fmt.Printf("Error searching graph (nodes): %v\n", err)
  	return
  }

  searchResultsEdges, err := client.Graph.Search(
  	ctx,
  	&zep.GraphSearchQuery{
  		UserID:  zep.String(userID),
  		Query:   query,
  		Scope:   zep.GraphSearchScopeEdges.Ptr(),
  		Reranker: zep.RerankerCrossEncoder.Ptr(),
  		Limit:   zep.Int(10),
  		BfsOriginNodeUUIDs: episodeUUIDs1,
  	},
  )
  if err != nil {
  	fmt.Printf("Error searching graph (edges): %v\n", err)
  	return
  }
  ```
</CodeBlocks>

## Build the context block

Using the search results and a few helper functions, we can build the context block. Note that for nodes, we typically want to unpack the node name and node summary, and for edges we typically want to unpack the fact and the temporal validity information:

<CodeBlocks>
  ```python
  from zep_cloud import EntityEdge, EntityNode

  CONTEXT_STRING_TEMPLATE = """
  FACTS and ENTITIES represent relevant context to the current conversation.
  # These are the most relevant facts and their valid date ranges
  # format: FACT (Date range: from - to)
  # NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
  #       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
  <FACTS>
  {facts}
  </FACTS>

  # These are the most relevant entities
  # ENTITY_NAME: entity summary
  <ENTITIES>
  {entities}
  </ENTITIES>
  """


  def format_fact(edge: EntityEdge) -> str:
      valid_at = edge.valid_at if edge.valid_at is not None else "date unknown"
      invalid_at = edge.invalid_at if edge.invalid_at is not None else "present"
      formatted_fact = f"  - {edge.fact} (Date range: {valid_at} - {invalid_at})"
      return formatted_fact

  def format_entity(node: EntityNode) -> str:
      formatted_entity = f"  - {node.name}: {node.summary}"
      return formatted_entity

  def compose_context_block(edges: list[EntityEdge], nodes: list[EntityNode]) -> str:
      facts = [format_fact(edge) for edge in edges]
      entities = [format_entity(node) for node in nodes]
      return CONTEXT_STRING_TEMPLATE.format(facts='\n'.join(facts), entities='\n'.join(entities))

  edges = search_results_edges.edges
  nodes = search_results_nodes.nodes

  context_block = compose_context_block(edges, nodes)
  print(context_block)
  ```

  ```typescript
  import type { EntityEdge, EntityNode } from "@getzep/zep-cloud/api";

  const CONTEXT_STRING_TEMPLATE_1 = `FACTS and ENTITIES represent relevant context to the current conversation.
  # These are the most relevant facts and their valid date ranges
  # format: FACT (Date range: from - to)
  # NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
  #       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
  <FACTS>
  {facts}
  </FACTS>
  # These are the most relevant entities
  # ENTITY_NAME: entity summary
  <ENTITIES>
  {entities}
  </ENTITIES>`;

  function formatFact(edge: EntityEdge): string {
      const validAt = edge.validAt ?? "date unknown";
      const invalidAt = edge.invalidAt ?? "present";
      return `  - ${edge.fact} (Date range: ${validAt} - ${invalidAt})`;
  }

  function formatEntity(node: EntityNode): string {
      return `  - ${node.name}: ${node.summary}`;
  }

  function composeContextBlock1(edges: EntityEdge[], nodes: EntityNode[]): string {
      const facts = edges.map(formatFact).join('\n');
      const entities = nodes.map(formatEntity).join('\n');
      return CONTEXT_STRING_TEMPLATE_1
          .replace('{facts}', facts)
          .replace('{entities}', entities);
  }

  const edges: EntityEdge[] = searchResultsEdges.edges ?? [];
  const nodes: EntityNode[] = searchResultsNodes.nodes ?? [];

  const contextBlock1 = composeContextBlock1(edges, nodes);
  console.log(contextBlock1);
  ```

  ```go
  import (
  	"strings"
  )

  const CONTEXT_STRING_TEMPLATE_1 = `FACTS and ENTITIES represent relevant context to the current conversation.
  # These are the most relevant facts and their valid date ranges
  # format: FACT (Date range: from - to)
  # NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
  #       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
  <FACTS>
  {facts}
  </FACTS>

  # These are the most relevant entities
  # ENTITY_NAME: entity summary
  <ENTITIES>
  {entities}
  </ENTITIES>
  `

  formatFact := func(edge *zep.EntityEdge) string {
  	validAt := "date unknown"
  	if edge.ValidAt != nil && *edge.ValidAt != "" {
  		validAt = *edge.ValidAt
  	}
  	invalidAt := "present"
  	if edge.InvalidAt != nil && *edge.InvalidAt != "" {
  		invalidAt = *edge.InvalidAt
  	}
  	return fmt.Sprintf("  - %s (Date range: %s - %s)", edge.Fact, validAt, invalidAt)
  }

  formatEntity := func(node *zep.EntityNode) string {
  	return fmt.Sprintf("  - %s: %s", node.Name, node.Summary)
  }

  composeContextBlock1 := func(edges []*zep.EntityEdge, nodes []*zep.EntityNode) string {
  	var facts []string
  	for _, edge := range edges {
  		facts = append(facts, formatFact(edge))
  	}
  	var entities []string
  	for _, node := range nodes {
  		entities = append(entities, formatEntity(node))
  	}
  	result := strings.ReplaceAll(CONTEXT_STRING_TEMPLATE_1, "{facts}", strings.Join(facts, "\n"))
  	result = strings.ReplaceAll(result, "{entities}", strings.Join(entities, "\n"))
  	return result
  }

  edges := searchResultsEdges.Edges
  nodes := searchResultsNodes.Nodes

  contextBlock1 := composeContextBlock1(edges, nodes)
  fmt.Println(contextBlock1)
  ```
</CodeBlocks>

```text
FACTS and ENTITIES represent relevant context to the current conversation.
# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
# NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)
#       Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)
<FACTS>
  - User wants to go to dessert (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe wants to go to a lunch place (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe said 'Perfect, let's go to Insomnia Cookies' indicating he will visit Insomnia Cookies. (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe said 'Let's go to Green Leaf Cafe' indicating intention to visit (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe is craving a chocolate chip cookie (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe states that he is vegetarian. (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe is lactose intolerant (Date range: 2025-06-16T02:17:25Z - present)
</FACTS>
 
# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
  - lunch place: The entity is a lunch place, but no specific details about its cuisine or dietary accommodations are provided.
  - dessert: The entity 'dessert' refers to a preference related to sweet courses typically served at the end of a meal. The context indicates that the user has expressed an interest in going to a dessert place, but no specific dessert or place has been named. The entity is categorized as a Preference and Entity, but no additional attributes are provided or inferred from the messages.
  - Green Leaf Cafe: Green Leaf Cafe is a restaurant that offers vegetarian options, making it suitable for vegetarian diners.
  - user: The user is John Doe, with the email john.doe@example.com. He has shown interest in visiting Green Leaf Cafe, which offers vegetarian options, and has also expressed a preference for lactose-free options, craving a chocolate chip cookie. The user has decided to go to Insomnia Cookies.
  - vegetarian: The user is interested in lunch places such as Panera Bread, Chipotle, and Green Leaf Cafe. They are specifically looking for vegetarian options at these restaurants.
  - chocolate chip cookie: The entity is a chocolate chip cookie, which the user desires as a snack. The user is lactose intolerant and cannot have ice cream, but is craving a chocolate chip cookie.
  - Insomnia Cookies: Insomnia Cookies is a restaurant that offers cookies, including chocolate chip cookies. The user is interested in a dessert and has chosen to go to Insomnia Cookies. No specific cuisine type or dietary accommodations are mentioned in the messages.
  - lactose intolerant: The entity is a preference indicating lactose intolerance, which is a dietary restriction that prevents the individual from consuming lactose, a sugar found in milk and dairy products. The person is specifically craving a chocolate chip cookie but cannot have ice cream due to lactose intolerance.
  - John Doe: The user is John Doe, with user ID user-34c7a6c1-ded6-4797-9620-8b80a5e7820f, email john.doe@example.com, and role user. He inquired about nearby lunch options and vegetarian choices, and expressed a preference for a chocolate chip cookie due to lactose intolerance.
</ENTITIES>
```

# Example 4: Using user summary in context block

## Get user node

You can retrieve the user node and use its summary to create a simple, personalized context block. This approach is particularly useful when you want to include high-level user information generated from [user summary instructions](/users#user-summary-instructions):

<CodeBlocks>
  ```python Python
  from zep_cloud.client import Zep

  client = Zep(api_key=API_KEY)

  # Get the user node and extract the summary
  user_node_response = client.user.get_node(user_id=user_id)
  user_summary = user_node_response.node.summary if user_node_response.node else None
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({
    apiKey: API_KEY,
  });

  // Get the user node and extract the summary
  const userNodeResponse = await client.user.getNode(userId);
  const userSummary = userNodeResponse.node?.summary;
  ```

  ```go Go
  import (
  	"context"
  	"log"

  	"github.com/getzep/zep-go/v3"
  	zepclient "github.com/getzep/zep-go/v3/client"
  	"github.com/getzep/zep-go/v3/option"
  )

  client := zepclient.NewClient(option.WithAPIKey(apiKey))

  // Get the user node and extract the summary
  userNodeResponse, err := client.User.GetNode(context.TODO(), userID)
  if err != nil {
  	log.Fatalf("Failed to get user node: %v", err)
  }

  var userSummary string
  if userNodeResponse.Node != nil && userNodeResponse.Node.Summary != nil {
  	userSummary = *userNodeResponse.Node.Summary
  }
  ```
</CodeBlocks>

## Build the context block

Using the user summary, you can create a simple context block that provides personalized user information:

<CodeBlocks>
  ```python Python
  # Build a simple context block with user summary
  context_block = f"""USER_SUMMARY represents relevant context about the user.
  # This is a high-level summary of the user
  <USER_SUMMARY>
  {user_summary if user_summary else "No user summary available"}
  </USER_SUMMARY>
  """

  print(context_block)
  ```

  ```typescript TypeScript
  // Build a simple context block with user summary
  const contextBlock = `USER_SUMMARY represents relevant context about the user.
  # This is a high-level summary of the user
  <USER_SUMMARY>
  ${userSummary || "No user summary available"}
  </USER_SUMMARY>
  `;

  console.log(contextBlock);
  ```

  ```go Go
  import "fmt"

  // Build a simple context block with user summary
  summaryText := userSummary
  if summaryText == "" {
  	summaryText = "No user summary available"
  }

  contextBlock := fmt.Sprintf(`USER_SUMMARY represents relevant context about the user.
  # This is a high-level summary of the user
  <USER_SUMMARY>
  %s
  </USER_SUMMARY>
  `, summaryText)

  fmt.Println(contextBlock)
  ```
</CodeBlocks>

```text
USER_SUMMARY represents relevant context about the user.
# This is a high-level summary of the user
<USER_SUMMARY>
John Doe is a software engineer who enjoys hiking and photography. He is vegetarian and lactose intolerant. He prefers detailed technical discussions and values efficiency in communication. He has requested that the AI provide concise answers with code examples when discussing programming topics.
</USER_SUMMARY>
```


# Add User Specific Business Data to User Graphs

This guide demonstrates how to add user-specific business data to a user's knowledge graph. We'll create a user, fetch their business data, and add it to their graph.

First, we will initialize our client and create a new user:

<CodeBlocks>
  ```python Python
  # Initialize the Zep client
  zep_client = Zep(api_key=API_KEY)

  # Add one example user
  user_id_zep = uuid.uuid4().hex
  zep_client.user.add(
      user_id=user_id_zep,
      email="cookbook@example.com"
  )
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";
  import { randomUUID } from "crypto";

  // Initialize the Zep client
  const client = new ZepClient({ apiKey: API_KEY });

  // Add one example user
  const userIdZep = randomUUID().replace(/-/g, "");
  await client.user.add({
      userId: userIdZep,
      email: "cookbook@example.com"
  });
  ```

  ```go Go
  import (
      "context"
      "log"

      "github.com/getzep/zep-go/v3"
      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
      "github.com/google/uuid"
  )

  // Initialize the Zep client
  zepClient := client.NewClient(option.WithAPIKey(API_KEY))

  // Add one example user
  userIDZep := uuid.New().String()
  user, err := zepClient.User.Add(
      context.TODO(),
      &zep.CreateUserRequest{
          UserID: userIDZep,
          Email:  zep.String("cookbook@example.com"),
      },
  )
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  ```
</CodeBlocks>

Then, we will fetch and format the user's business data. Note that the functionality to fetch a users business data will depend on your codebase.

Also note that you could make your Zep user IDs equal to whatever internal user IDs you use to make things easier to manage. Generally, Zep user IDs, thread IDs, Graph IDs, etc. can be arbitrary strings, and can map to your app's data schema.

<CodeBlocks>
  ```python Python
  # Define the function to fetch user business data
  def get_user_business_data(user_id_business):
      # This function returns JSON data for the given user
      # This would vary based on your codebase
      return {}

  # Placeholder for business user id
  user_id_business = "placeholder_user_id"  # This would vary based on your codebase

  # Retrieve the user-specific business data
  user_data_json = get_user_business_data(user_id_business)

  # Convert the business data to a string
  json_string = json.dumps(user_data_json)
  ```

  ```typescript TypeScript
  // Define the function to fetch user business data
  function getUserBusinessData(userIdBusiness: string): Record<string, any> {
      // This function returns JSON data for the given user
      // This would vary based on your codebase
      return {};
  }

  // Placeholder for business user id
  const userIdBusiness = "placeholder_user_id";  // This would vary based on your codebase

  // Retrieve the user-specific business data
  const userDataJson = getUserBusinessData(userIdBusiness);

  // Convert the business data to a string
  const jsonString = JSON.stringify(userDataJson);
  ```

  ```go Go
  import (
      "encoding/json"
  )

  // Define the function to fetch user business data
  func getUserBusinessData(userIDBusiness string) map[string]interface{} {
      // This function returns JSON data for the given user
      // This would vary based on your codebase
      return map[string]interface{}{}
  }

  // Placeholder for business user id
  userIDBusiness := "placeholder_user_id"  // This would vary based on your codebase

  // Retrieve the user-specific business data
  userDataJSON := getUserBusinessData(userIDBusiness)

  // Convert the business data to a string
  jsonBytes, err := json.Marshal(userDataJSON)
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  jsonString := string(jsonBytes)
  ```
</CodeBlocks>

Lastly, we will add the formatted data to the user's graph using the [graph API](/adding-data-to-the-graph):

<CodeBlocks>
  ```python Python
  # Add the JSON data to the user's graph
  zep_client.graph.add(
      user_id=user_id_zep,
      type="json",
      data=json_string,
  )
  ```

  ```typescript TypeScript
  // Add the JSON data to the user's graph
  await client.graph.add({
      userId: userIdZep,
      type: "json",
      data: jsonString,
  });
  ```

  ```go Go
  // Add the JSON data to the user's graph
  episode, err := zepClient.Graph.Add(
      context.TODO(),
      &zep.AddDataRequest{
          UserID: zep.String(userIDZep),
          Type:   zep.GraphDataTypeJSON,
          Data:   jsonString,
      },
  )
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  ```
</CodeBlocks>

Here, we use `type="json"`, but the graph API also supports `type="text"` and `type="message"`. The `type="text"` option is useful for adding background information that is in unstructured text such as internal documents or web copy. The `type="message"` option is useful for adding data that is in a message format but is not your user's chat history, such as emails. [Read more about this here](/adding-data-to-the-graph).

Also, note that when adding data to the graph, you should consider the size of the data you are adding and our payload limits. [Read more about this here](/docs/performance/performance-best-practices#optimizing-memory-operations).

You have now successfully added user-specific business data to a user's knowledge graph, which can be used alongside chat history to create comprehensive user memory.


# Share Memory Across Users Using Graphs

In this recipe, we will demonstrate how to share memory across different users by utilizing graphs. We will set up a user thread, add graph-specific data, and integrate the OpenAI client to show how to use both user and graph memory to enhance the context of a chatbot.

First, we initialize the Zep client, create a user, and create a thread:

<CodeBlocks>
  ```python
  # Initialize the Zep client
  zep_client = Zep(api_key="YOUR_API_KEY")  # Ensure your API key is set appropriately

  # Add one example user
  user_id = uuid.uuid4().hex
  zep_client.user.add(
      user_id=user_id,
      first_name="Alice",
      last_name="Smith",
      email="alice.smith@example.com"
  )

  # Create a new thread for the user
  thread_id = uuid.uuid4().hex
  zep_client.thread.create(
      thread_id=thread_id,
      user_id=user_id,
  )
  ```

  ```typescript
  import { ZepClient } from "@getzep/zep-cloud";
  import { randomUUID } from "crypto";

  // Initialize the Zep client
  const zepClient = new ZepClient({ apiKey: "YOUR_API_KEY" });

  // Add one example user
  const userId = randomUUID().replace(/-/g, "");
  await zepClient.user.add({
      userId: userId,
      firstName: "Alice",
      lastName: "Smith",
      email: "alice.smith@example.com"
  });

  // Create a new thread for the user
  const threadId = randomUUID().replace(/-/g, "");
  await zepClient.thread.create({
      threadId: threadId,
      userId: userId
  });
  ```

  ```go
  import (
      "context"
      "log"

      "github.com/getzep/zep-go/v3"
      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
      "github.com/google/uuid"
  )

  // Initialize the Zep client
  zepClient := client.NewClient(option.WithAPIKey("YOUR_API_KEY"))

  // Add one example user
  userId := uuid.New().String()
  _, err := zepClient.User.Add(context.Background(), &zep.CreateUserRequest{
      UserID:    userId,
      FirstName: zep.String("Alice"),
      LastName:  zep.String("Smith"),
      Email:     zep.String("alice.smith@example.com"),
  })
  if err != nil {
      log.Fatalf("Error: %v", err)
  }

  // Create a new thread for the user
  threadId := uuid.New().String()
  _, err = zepClient.Thread.Create(context.Background(), &zep.CreateThreadRequest{
      ThreadID: threadId,
      UserID:   userId,
  })
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  ```
</CodeBlocks>

Next, we create a new graph and add structured business data to the graph, in the form of a JSON string. This step uses the [Graphs API](/graph-overview).

<CodeBlocks>
  ```python
  graph_id = uuid.uuid4().hex
  zep_client.graph.create(graph_id=graph_id)

  product_json_data = [
      {
          "type": "Sedan",
          "gas_mileage": "25 mpg",
          "maker": "Toyota"
      },
      # ... more cars
  ]

  json_string = json.dumps(product_json_data)
  zep_client.graph.add(
      graph_id=graph_id,
      type="json",
      data=json_string,
  )
  ```

  ```typescript
  const graphId = randomUUID().replace(/-/g, "");
  await zepClient.graph.create({ graphId: graphId });

  const productJsonData = [
      {
          type: "Sedan",
          gas_mileage: "25 mpg",
          maker: "Toyota"
      },
      // ... more cars
  ];

  const jsonString = JSON.stringify(productJsonData);
  await zepClient.graph.add({
      graphId: graphId,
      type: "json",
      data: jsonString
  });
  ```

  ```go
  import "encoding/json"

  graphId := uuid.New().String()
  _, err = zepClient.Graph.Create(context.Background(), &zep.CreateGraphRequest{
      GraphID: graphId,
  })
  if err != nil {
      log.Fatalf("Error: %v", err)
  }

  productJsonData := []map[string]string{
      {
          "type":        "Sedan",
          "gas_mileage": "25 mpg",
          "maker":       "Toyota",
      },
      // ... more cars
  }

  jsonBytes, err := json.Marshal(productJsonData)
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  jsonString := string(jsonBytes)

  _, err = zepClient.Graph.Add(context.Background(), &zep.AddDataRequest{
      GraphID: &graphId,
      Type:    zep.GraphDataTypeJSON,
      Data:    jsonString,
  })
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  ```
</CodeBlocks>

Finally, we initialize the OpenAI client and define a `chatbot_response` function that retrieves user and graph memory, constructs a system/developer message, and generates a contextual response. This leverages the [Threads API](/retrieving-memory#retrieving-zeps-context-block), [graph API](/searching-the-graph), and the OpenAI chat completions endpoint.

<CodeBlocks>
  ```python
  # Initialize the OpenAI client
  oai_client = OpenAI()

  def chatbot_response(user_message, thread_id):
      # Retrieve user memory
      user_memory = zep_client.thread.get_user_context(thread_id)

      # Search the graph using the user message as the query
      results = zep_client.graph.search(graph_id=graph_id, query=user_message, scope="edges")
      relevant_graph_edges = results.edges
      product_context_block = "Below are some facts related to our car inventory that may help you respond to the user: \n"
      for edge in relevant_graph_edges:
          product_context_block += f"{edge.fact}\n"

      # Combine context blocks for the developer message
      developer_message = f"You are a helpful chat bot assistant for a car sales company. Answer the user's message while taking into account the following background information:\n{user_memory.context}\n{product_context_block}"

      # Generate a response using the OpenAI API
      completion = oai_client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
              {"role": "developer", "content": developer_message},
              {"role": "user", "content": user_message}
          ]
      )
      response = completion.choices[0].message.content

      # Add the conversation to memory
      messages = [
          Message(name="Alice", role="user", content=user_message),
          Message(name="AI assistant", role="assistant", content=response)
      ]
      zep_client.thread.add_messages(thread_id, messages=messages)

      return response
  ```

  ```typescript
  import OpenAI from "openai";

  // Initialize the OpenAI client
  const oaiClient = new OpenAI();

  async function chatbotResponse(userMessage: string, threadId: string): Promise<string> {
      // Retrieve user memory
      const userMemory = await zepClient.thread.getUserContext(threadId);

      // Search the graph using the user message as the query
      const results = await zepClient.graph.search({
          graphId: graphId,
          query: userMessage,
          scope: "edges"
      });

      const relevantGraphEdges = results.edges || [];
      let productContextBlock = "Below are some facts related to our car inventory that may help you respond to the user: \n";
      for (const edge of relevantGraphEdges) {
          productContextBlock += `${edge.fact}\n`;
      }

      // Combine context blocks for the developer message
      const developerMessage = `You are a helpful chat bot assistant for a car sales company. Answer the user's message while taking into account the following background information:\n${userMemory.context}\n${productContextBlock}`;

      // Generate a response using the OpenAI API
      const completion = await oaiClient.chat.completions.create({
          model: "gpt-4o-mini",
          messages: [
              { role: "developer", content: developerMessage },
              { role: "user", content: userMessage }
          ]
      });
      const response = completion.choices[0].message.content || "";

      // Add the conversation to memory
      await zepClient.thread.addMessages(threadId, {
          messages: [
              { name: "Alice", role: "user", content: userMessage },
              { name: "AI assistant", role: "assistant", content: response }
          ]
      });

      return response;
  }
  ```

  ```go
  import (
      "context"
      "log"

      "github.com/sashabaranov/go-openai"
  )

  // Initialize the OpenAI client
  oaiClient := openai.NewClient("YOUR_OPENAI_API_KEY")

  func chatbotResponse(userMessage, threadId string) (string, error) {
      ctx := context.Background()

      // Retrieve user memory
      userMemory, err := zepClient.Thread.GetUserContext(ctx, threadId, &zep.ThreadGetUserContextRequest{})
      if err != nil {
          return "", err
      }

      // Search the graph using the user message as the query
      results, err := zepClient.Graph.Search(ctx, &zep.GraphSearchQuery{
          GraphID: &graphId,
          Query:   userMessage,
          Scope:   zep.GraphSearchScopeEdges.Ptr(),
      })
      if err != nil {
          return "", err
      }

      relevantGraphEdges := results.Edges
      productContextBlock := "Below are some facts related to our car inventory that may help you respond to the user: \n"
      for _, edge := range relevantGraphEdges {
          productContextBlock += edge.Fact + "\n"
      }

      // Combine context blocks for the developer message
      developerMessage := "You are a helpful chat bot assistant for a car sales company. Answer the user's message while taking into account the following background information:\n" +
          userMemory.Context + "\n" + productContextBlock

      // Generate a response using the OpenAI API
      completion, err := oaiClient.CreateChatCompletion(ctx, openai.ChatCompletionRequest{
          Model: openai.GPT4oMini,
          Messages: []openai.ChatCompletionMessage{
              {
                  Role:    "developer",
                  Content: developerMessage,
              },
              {
                  Role:    "user",
                  Content: userMessage,
              },
          },
      })
      if err != nil {
          return "", err
      }
      response := completion.Choices[0].Message.Content

      // Add the conversation to memory
      _, err = zepClient.Thread.AddMessages(ctx, threadId, &zep.AddThreadMessagesRequest{
          Messages: []*zep.Message{
              {
                  Name:    zep.String("Alice"),
                  Role:    zep.RoleTypeUserRole,
                  Content: userMessage,
              },
              {
                  Name:    zep.String("AI assistant"),
                  Role:    zep.RoleTypeAssistantRole,
                  Content: response,
              },
          },
      })
      if err != nil {
          return "", err
      }

      return response, nil
  }
  ```
</CodeBlocks>

This recipe demonstrated how to share memory across users by utilizing graphs with Zep. We set up user threads, added structured graph data, and integrated the OpenAI client to generate contextual responses, providing a robust approach to memory sharing across different users.


# Get Most Relevant Facts for an Arbitrary Query

In this recipe, we demonstrate how to retrieve the most relevant facts from the knowledge graph using an arbitrary search query.

First, we perform a [search](/searching-the-graph) on the knowledge graph using a sample query:

<CodeBlocks>
  ```python
  from zep_cloud.client import Zep

  zep_client = Zep(api_key=API_KEY)
  results = zep_client.graph.search(user_id="some user_id", query="Some search query", scope="edges")
  ```

  ```typescript
  import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({ apiKey: process.env.ZEP_API_KEY || "" });
  const results = await client.graph.search({
      userId: "some user_id",
      query: "Some search query",
      scope: "edges"
  });
  ```

  ```go
  package main

  import (
      "context"
      "fmt"
      "log"
      "os"

      "github.com/getzep/zep-go/v3"
      zepclient "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  func main() {
      ctx := context.Background()

      client := zepclient.NewClient(
          option.WithAPIKey(os.Getenv("ZEP_API_KEY")),
      )

      results, err := client.Graph.Search(ctx, &zep.GraphSearchQuery{
          UserID: zep.String("some user_id"),
          Query:  "Some search query",
          Scope:  zep.GraphSearchScopeEdges.Ptr(),
      })
      if err != nil {
          log.Fatalf("Error: %v", err)
      }
  ```
</CodeBlocks>

Then, we get the edges from the search results and construct our fact list. We also include the temporal validity data to each fact string:

<CodeBlocks>
  ```python
  # Build list of formatted facts
  relevant_edges = results.edges
  formatted_facts = []
  for edge in relevant_edges:
      valid_at = edge.valid_at if edge.valid_at is not None else "date unknown"
      invalid_at = edge.invalid_at if edge.invalid_at is not None else "present"
      formatted_fact = f"{edge.fact} (Date range: {valid_at} - {invalid_at})"
      formatted_facts.append(formatted_fact)

  # Print the results
  print("\nFound facts:")
  for fact in formatted_facts:
      print(f"- {fact}")
  ```

  ```typescript
  // Build list of formatted facts
  const relevantEdges = results.edges || [];
  const formattedFacts: string[] = [];

  for (const edge of relevantEdges) {
      const validAt = edge.validAt ?? "date unknown";
      const invalidAt = edge.invalidAt ?? "present";
      const formattedFact = `${edge.fact} (Date range: ${validAt} - ${invalidAt})`;
      formattedFacts.push(formattedFact);
  }

  // Print the results
  console.log("\nFound facts:");
  for (const fact of formattedFacts) {
      console.log(`- ${fact}`);
  }
  ```

  ```go
      // Build list of formatted facts
      relevantEdges := results.Edges
      var formattedFacts []string

      for _, edge := range relevantEdges {
          validAt := "date unknown"
          if edge.ValidAt != nil {
              validAt = *edge.ValidAt
          }

          invalidAt := "present"
          if edge.InvalidAt != nil {
              invalidAt = *edge.InvalidAt
          }

          formattedFact := fmt.Sprintf("%s (Date range: %s - %s)", edge.Fact, validAt, invalidAt)
          formattedFacts = append(formattedFacts, formattedFact)
      }

      // Print the results
      fmt.Println("\nFound facts:")
      for _, fact := range formattedFacts {
          fmt.Printf("- %s\n", fact)
      }
  }
  ```
</CodeBlocks>

We demonstrated how to retrieve the most relevant facts for an arbitrary query using the Zep client. Adjust the query and parameters as needed to tailor the search for your specific use case.


# Find Facts Relevant to a Specific Node

Below, we will go through how to retrieve facts which are related to a specific node in a Zep knowledge graph. First, we will go through some methods for determining the UUID of the node you are interested in. Then, we will go through some methods for retrieving the facts related to that node.

If you are interested in the user's node specifically, we have a convenience method that [returns the user's node](/users#get-the-user-node) which includes the UUID.

An easy way to determine the UUID for other nodes is to use the graph explorer in the [Zep Web app](https://app.getzep.com/).

You can also programmatically retrieve all the nodes for a given user using our [get nodes by user API](/sdk-reference/graph/node/get-by-user-id), and then manually examine the nodes and take note of the UUID of the node of interest:

<CodeBlocks>
  ```python Python
  # Initialize the Zep client
  zep_client = Zep(api_key=API_KEY)
  nodes = zep_client.graph.node.get_by_user_id(user_id="some user ID")
  print(nodes)
  ```

  ```typescript TypeScript
  import { ZepClient } from "@getzep/zep-cloud";

  // Initialize the Zep client
  const client = new ZepClient({ apiKey: API_KEY });
  const nodes = await client.graph.node.getByUserId("some user ID", {});
  console.log(nodes);
  ```

  ```go Go
  import (
      "context"
      "fmt"
      "log"

      "github.com/getzep/zep-go/v3"
      "github.com/getzep/zep-go/v3/client"
      "github.com/getzep/zep-go/v3/option"
  )

  // Initialize the Zep client
  zepClient := client.NewClient(option.WithAPIKey(API_KEY))
  nodes, err := zepClient.Graph.Node.GetByUserID(
      context.TODO(),
      "some user ID",
      &zep.GraphNodesRequest{},
  )
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  fmt.Println(nodes)
  ```
</CodeBlocks>

<CodeBlocks>
  ```python Python
  center_node_uuid = "your chosen center node UUID"
  ```

  ```typescript TypeScript
  const centerNodeUuid = "your chosen center node UUID";
  ```

  ```go Go
  centerNodeUUID := "your chosen center node UUID"
  ```
</CodeBlocks>

Lastly, if your user has a lot of nodes to look through, you can narrow down the search by only looking at the nodes relevant to a specific query, using our [graph search API](/searching-the-graph):

<CodeBlocks>
  ```python Python
  results = zep_client.graph.search(
      user_id="some user ID",
      query="shoe", # To help narrow down the nodes you have to manually search
      scope="nodes"
  )
  relevant_nodes = results.nodes
  print(relevant_nodes)
  ```

  ```typescript TypeScript
  const results = await client.graph.search({
      userId: "some user ID",
      query: "shoe", // To help narrow down the nodes you have to manually search
      scope: "nodes"
  });
  const relevantNodes = results.nodes;
  console.log(relevantNodes);
  ```

  ```go Go
  results, err := zepClient.Graph.Search(
      context.TODO(),
      &zep.GraphSearchQuery{
          UserID: zep.String("some user ID"),
          Query:  "shoe", // To help narrow down the nodes you have to manually search
          Scope:  zep.GraphSearchScopeNodes.Ptr(),
      },
  )
  if err != nil {
      log.Fatalf("Error: %v", err)
  }
  relevantNodes := results.Nodes
  fmt.Println(relevantNodes)
  ```
</CodeBlocks>

<CodeBlocks>
  ```python Python
  center_node_uuid = "your chosen center node UUID"
  ```

  ```typescript TypeScript
  const centerNodeUuid = "your chosen center node UUID";
  ```

  ```go Go
  centerNodeUUID := "your chosen center node UUID"
  ```
</CodeBlocks>

The most straightforward way to get facts related to your node is to retrieve all facts that are connected to your chosen node using the [get edges by user API](/sdk-reference/graph/edge/get-by-user-id):

<CodeBlocks>
  ```python Python
  edges = zep_client.graph.edge.get_by_user_id(user_id="some user ID")
  connected_edges = [edge for edge in edges if edge.source_node_uuid == center_node_uuid or edge.target_node_uuid == center_node_uuid]
  relevant_facts = [edge.fact for edge in connected_edges]
  ```

  ```typescript TypeScript
  const edges = await client.graph.edge.getByUserId("some user ID", {});
  const connectedEdges = edges.filter(
      edge => edge.sourceNodeUuid === centerNodeUuid || edge.targetNodeUuid === centerNodeUuid
  );
  const relevantFacts = connectedEdges.map(edge => edge.fact);
  ```

  ```go Go
  edges, err := zepClient.Graph.Edge.GetByUserID(
      context.TODO(),
      "some user ID",
      &zep.GraphEdgesRequest{},
  )
  if err != nil {
      log.Fatalf("Error: %v", err)
  }

  var connectedEdges []*zep.EntityEdge
  for _, edge := range edges {
      if edge.SourceNodeUUID == centerNodeUUID || edge.TargetNodeUUID == centerNodeUUID {
          connectedEdges = append(connectedEdges, edge)
      }
  }

  var relevantFacts []string
  for _, edge := range connectedEdges {
      relevantFacts = append(relevantFacts, edge.Fact)
  }
  ```
</CodeBlocks>

You can also retrieve facts relevant to your node by using the [graph search API](/searching-the-graph) with the node distance re-ranker:

<CodeBlocks>
  ```python Python
  results = zep_client.graph.search(
      user_id="some user ID",
      query="some query",
      reranker="node_distance",
      center_node_uuid=center_node_uuid,
  )
  relevant_edges = results.edges
  relevant_facts = [edge.fact for edge in relevant_edges]
  ```

  ```typescript TypeScript
  const results = await client.graph.search({
      userId: "some user ID",
      query: "some query",
      reranker: "node_distance",
      centerNodeUuid: centerNodeUuid,
  });
  const relevantEdges = results.edges;
  const relevantFacts = relevantEdges?.map(edge => edge.fact) || [];
  ```

  ```go Go
  results, err := zepClient.Graph.Search(
      context.TODO(),
      &zep.GraphSearchQuery{
          UserID:         zep.String("some user ID"),
          Query:          "some query",
          Reranker:       zep.GraphSearchRerankerNodeDistance.Ptr(),
          CenterNodeUUID: zep.String(centerNodeUUID),
      },
  )
  if err != nil {
      log.Fatalf("Error: %v", err)
  }

  relevantEdges := results.Edges
  var relevantFacts []string
  for _, edge := range relevantEdges {
      relevantFacts = append(relevantFacts, edge.Fact)
  }
  ```
</CodeBlocks>

In this recipe, we went through how to retrieve facts which are related to a specific node in a Zep knowledge graph. We first went through some methods for determining the UUID of the node you are interested in. Then, we went through some methods for retrieving the facts related to that node.


# Performance Optimization Guide

> Best practices for optimizing Zep performance in production

This guide covers best practices for optimizing Zep's performance in production environments.

## Reuse the Zep SDK Client

The Zep SDK client maintains an HTTP connection pool that enables connection reuse, significantly reducing latency by avoiding the overhead of establishing new connections. To optimize performance:

* Create a single client instance and reuse it across your application
* Avoid creating new client instances for each request or function
* Consider implementing a client singleton pattern in your application
* For serverless environments, initialize the client outside the handler function

## Optimizing Memory Operations

The `thread.add_messages` and `thread.get_user_context` methods are optimized for conversational messages and low-latency retrieval. For optimal performance:

* Keep individual messages under 10K characters
* Use `graph.add` for larger documents, tool outputs, or business data
* Consider chunking large documents before adding them to the graph (the `graph.add` endpoint has a 10,000 character limit)
* Remove unnecessary metadata or content before persistence
* For bulk document ingestion, process documents in parallel while respecting rate limits

```python
# Recommended for conversations
zep_client.thread.add_messages(
    thread_id="thread_123",
    message={
        "role": "user",
        "name": "Alice",
        "content": "What's the weather like today?"
    }
)

# Recommended for large documents
await zep_client.graph.add(
    data=document_content,  # Your chunked document content
    user_id=user_id,       # Or graph_id
    type="text"            # Can be "text", "message", or "json"
)
```

### Use the Basic Context Block

Zep's [context block](/retrieving-memory#retrieving-zeps-context-block) can either be in summarized or basic form (summarized by default). Retrieving basic results reduces latency (P95 \< 200 ms) since this bypasses the final summarization step.

<CodeBlocks>
  ```python Python
  # Get memory for the thread
  memory = client.thread.get_user_context(thread_id=thread_id, mode="basic")

  # Access the context block (for use in prompts)
  context_block = memory.context
  print(context_block)
  ```

  ```typescript TypeScript
  // Get memory for the thread
  const memory = await client.thread.getUserContext(threadId, { mode: "basic" });

  // Access the context block (for use in prompts)
  const contextBlock = memory.context;
  console.log(contextBlock);
  ```

  ```go Go
  import (
      "context"
      v3 "github.com/getzep/zep-go/v3"
  )

  mode := "basic"
  // Get memory for the thread
  memory, err := client.Thread.GetUserContext(context.TODO(), threadId, &v3.ThreadGetUserContextRequest{
      Mode: &mode,
  })
  if err != nil {
      log.Fatal("Error getting memory:", err)
  }
  // Access the context block (for use in prompts)
  contextBlock := memory.Context
  fmt.Println(contextBlock)
  ```
</CodeBlocks>

```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges

# format: FACT (Date range: from - to)

<FACTS>
  - Emily is experiencing issues with logging in. (2024-11-14 02:13:19+00:00 -
    present) 
  - User account Emily0e62 has a suspended status due to payment failure. 
    (2024-11-14 02:03:58+00:00 - present) 
  - user has the id of Emily0e62 (2024-11-14 02:03:54 - present)
  - The failed transaction used a card with last four digits 1234. (2024-09-15
    00:00:00+00:00 - present)
  - The reason for the transaction failure was 'Card expired'. (2024-09-15
    00:00:00+00:00 - present)
  - user has the name of Emily Painter (2024-11-14 02:03:54 - present) 
  - Account Emily0e62 made a failed transaction of 99.99. (2024-07-30 
    00:00:00+00:00 - 2024-08-30 00:00:00+00:00)
</FACTS>

# These are the most relevant entities

# ENTITY_NAME: entity summary

<ENTITIES>
  - Emily0e62: Emily0e62 is a user account associated with a transaction,
    currently suspended due to payment failure, and is also experiencing issues
    with logging in. 
  - Card expired: The node represents the reason for the transaction failure, 
    which is indicated as 'Card expired'. 
  - Magic Pen Tool: The tool being used by the user that is malfunctioning. 
  - User: user 
  - Support Agent: Support agent responding to the user's bug report. 
  - SupportBot: SupportBot is the virtual assistant providing support to the user, 
    Emily, identified as SupportBot. 
  - Emily Painter: Emily is a user reporting a bug with the magic pen tool, 
    similar to Emily Painter, who is expressing frustration with the AI art
    generation tool and seeking assistance regarding issues with the PaintWiz app.
</ENTITIES>
```

### Get the Context Block sooner

Additionally, you can request the Context Block directly in the response to the `thread.add_messages()` call.
This optimization eliminates the need for a separate `thread.get_user_context()`, though this method always returns the basic Context Block type.
Read more about our [Context Block](/retrieving-memory#retrieving-zeps-context-block).

In this scenario you can pass in the `return_context=True` flag to the `thread.add_messages()` method.
Zep will perform a user graph search right after persisting the memory and return the context relevant to the recently added memory.

<CodeBlocks>
  ```python Python
  memory_response = await zep_client.thread.add_messages(
      thread_id=thread_id,
      messages=messages,
      return_context=True
  )

  context = memory_response.context
  ```

  ```typescript TypeScript
  const memoryResponse = await zepClient.thread.addMessages(threadId, {
      messages: messages,
      returnContext: true
  });

  const context = memoryResponse.context;
  ```

  ```go Go
  memoryResponse, err := zepClient.Thread.AddMessages(
      context.TODO(),
      threadId,
      &zep.AddThreadMessagesRequest{
          Messages: messages,
          ReturnContext: zep.Bool(true),
      },
  )
  if err != nil {
      // handle error
  }
  contextBlock := memoryResponse.Context
  ```
</CodeBlocks>

<Tip>
  Read more in the 

  [Thread SDK Reference](/sdk-reference/thread/add-messages)
</Tip>

### Searching the Graph Sooner

Instead of using `thread.get_user_context`, you might want to [search the graph](/searching-the-graph) directly with custom parameters and construct your own [custom context block](/cookbook/customize-your-context-block). When doing this, you can search the graph and add data to the graph concurrently.

```python
import asyncio
from zep_cloud.client import AsyncZep
from zep_cloud.types import Message

client = AsyncZep(api_key="your_api_key")

async def add_and_retrieve_from_zep(messages):
    # Concatenate message content to create query string
    query = " ".join([msg.content for msg in messages])
    
    # Execute all operations concurrently
    add_result, edges_result, nodes_result = await asyncio.gather(
        client.thread.add_messages(
            thread_id=thread_id,
            messages=messages
        ),
        client.graph.search(
            user_id=user_id,
            query=query,
            scope="edges"
        ),
        client.graph.search(
            user_id=user_id,
            query=query,
            scope="nodes"
        )
    )
    
    return add_result, edges_result, nodes_result
```

You would then need to construct a custom context block using the search results. Learn more about [customizing your context block](/cookbook/customize-your-context-block).

## Optimizing Search Queries

Zep uses hybrid search combining semantic similarity and BM25 full-text search. For optimal performance:

* Keep your queries concise. Queries are automatically truncated to 8,192 tokens (approximately 32,000 Latin characters)
* Longer queries may not improve search quality and will increase latency
* Consider breaking down complex searches into smaller, focused queries
* Use specific, contextual queries rather than generic ones

Best practices for search:

* Keep search queries concise and specific
* Structure queries to target relevant information
* Use natural language queries for better semantic matching
* Consider the scope of your search (graphs versus user graphs)

```python
# Recommended - concise query
results = await zep_client.graph.search(
    user_id=user_id,  # Or graph_id
    query="project requirements discussion"
)

# Not recommended - overly long query
results = await zep_client.graph.search(
    user_id=user_id,
    query="very long text with multiple paragraphs..."  # Will be truncated
)
```

## Warming the User Cache

Zep has a multi-tier retrieval architecture. The highest tier is a "hot" cache where a user's context retrieval is fastest. After several hours of no activity, a user's data will be moved to a lower tier.

You can hint to Zep that a retrieval may be made soon, allowing Zep to move user data into cache ahead of this retrieval. A good time to do this is when a user logs in to your service or opens your app.

<CodeBlocks>
  ```python Python
  # Warm the user's cache when they log in
  client.user.warm(user_id=user_id)
  ```

  ```typescript TypeScript
  // Warm the user's cache when they log in
  await client.user.warm(userId);
  ```

  ```go Go
  // Warm the user's cache when they log in
  _, err := client.User.Warm(context.TODO(), userId)
  if err != nil {
      log.Printf("Error warming user cache: %v", err)
  }
  ```
</CodeBlocks>

<Tip>
  Read more in the 

  [User SDK Reference](/sdk-reference/user/warm)
</Tip>

## Summary

* Reuse Zep SDK client instances to optimize connection management
* Use appropriate methods for different types of content (`thread.add_messages` for conversations, `graph.add` for large documents)
* Keep search queries focused and under the token limit for optimal performance
* Warm the user cache when users log in or open your app for faster retrieval


# Adding JSON Best Practices

> Best practices for preparing JSON data for ingestion into Zep

Adding JSON to Zep without adequate preparation can lead to unexpected results. For instance, adding a large JSON without dividing it up can lead to a graph with very few nodes. Below, we go over what type of JSON works best with Zep, and techniques you can use to ensure your JSON fits these criteria.

## Key Criteria

At a high level, ingestion of JSON into Zep works best when these criteria are met:

1. **JSON is not too large**: Large JSON should be divided into pieces, adding each piece separately to Zep.
2. **JSON is not deeply nested**: Deeply nested JSON (more than 3 to 4 levels) should be flattened while preserving information.
3. **JSON is understandable in isolation**: The JSON should include all the information needed to understand the data it represents. This might mean adding descriptions or understandable attribute names where relevant.
4. **JSON represents a unified entity**: The JSON should ideally represent a unified entity, with ID, name, and description fields. Zep treats the JSON as a whole as a "first class entity", creating branching entities off of the main JSON entity from the JSON's attributes.

## JSON that is too large

### JSON with too many attributes

**Recommendation**: Split up the properties among several instances of the object. Each instance should duplicate the `id`, `name`, and `description` fields, or similar fields that tie each chunk to the same object, and then have 3 to 4 additional properties.

### JSON with too many list elements

**Recommendation**: Split up the list into its elements, ensuring you add additional fields to contextualize each element if needed. For instance, if the key of the list is "cars", then you should add a field which indicates that the list item is a car.

### JSON with large strings

**Recommendation**: A very long string might be better added to the graph as unstructured text instead of JSON. You may need to add a sentence or two to contextualize the unstructured text with respect to the rest of the JSON, since they would be added separately. And if it is very long, you would want to employ document chunking methods, such as described by Anthropic [here](https://www.anthropic.com/news/contextual-retrieval).

## JSON that is deeply nested

**Recommendation**: For each deeply nested value In the JSON, create a flattened JSON piece for that value specifically. For instance, if your JSON alternates between dictionaries and lists for 5 to 6 levels with a single value at the bottom, then the flattened version would have an attribute for the value, and an attribute to convey any information from each of the keys from the original JSON.

## JSON that is not understandable in isolation

**Recommendation**: Add descriptions or helpful/interpretable attribute names where relevant.

## JSON that is not a unified entity

**Recommendation**: Add an `id`, `name`, and `description` field to the JSON. Additionally, if the JSON essentially represents two or more objects, split it up.

## Dealing with a combination of the above

**Recommendation**: First, deal with the fact that the JSON is too large and/or too deeply nested by iteratively applying these recommendations (described above) from the top down: splitting up attributes, splitting up lists, flattening deeply nested JSON, splitting out any large text documents. For example, if your JSON has a lot of attributes and one of those attributes is a long list, then you should first split up the JSON by the attributes, and then split up the JSON piece that contains the long list by splitting the list elements.

After applying the iterative transformations, you should have a list of candidate JSON, each of which is not too large or too deeply nested. As the last step, you should ensure that each JSON in the list is understandable in isolation and represents a unified entity by applying the recommendations above.


# Quickstart

> Evaluate Zep's memory retrieval and question-answering capabilities

The Zep Eval Harness is an end-to-end evaluation framework for testing Zep's memory retrieval and question-answering capabilities for general conversational scenarios. This guide will walk you through setting up and running the harness to evaluate your Zep implementation.

## Prerequisites

Before getting started, ensure you have:

* **Zep API Key**: Available at [app.getzep.com](https://app.getzep.com)
* **OpenAI API Key**: Obtainable from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
* **UV Package Manager**: The harness uses UV for Python dependency management

## Installation

<Steps>
  ### Clone the repository

  Clone the Zep repository and navigate to the eval harness directory:

  ```bash
  git clone https://github.com/getzep/zep.git
  cd zep/zep-eval-harness
  ```

  ### Install UV

  Install UV package manager for macOS/Linux:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

  For other platforms, visit the [UV installation guide](https://docs.astral.sh/uv/).

  ### Install dependencies

  Install all required dependencies using UV:

  ```bash
  uv sync
  ```

  ### Configure environment variables

  Copy the example environment file and add your API keys:

  ```bash
  cp .env.example .env
  ```

  Edit the `.env` file to include your API keys:

  ```bash
  ZEP_API_KEY=your_zep_api_key_here
  OPENAI_API_KEY=your_openai_api_key_here
  ```
</Steps>

## Data structure

The harness expects data files in the following structure:

### Users file

Location: `data/users.json`

Contains user information with fields: `user_id`, `first_name`, `last_name`, `email`, and optional metadata fields.

### Conversations

Location: `data/conversations/`

Files named `{user_id}_{conversation_id}.json` containing:

* `conversation_id`
* `user_id`
* `messages` array with `role`, `content`, and `timestamp`

### Test cases

Location: `data/test_cases/`

Files named `{user_id}_tests.json` with test structure:

* `id`
* `category`
* `query`
* `golden_answer`
* `requires_telemetry` flag

### Optional telemetry

Location: `data/telemetry/`

Files named `{user_id}_{data_type}.json` containing any JSON data with a `user_id` field.

## Running the evaluation

<Steps>
  ### Ingest data

  Run the ingestion script to load your data into Zep:

  ```bash
  uv run zep_ingest.py
  ```

  For ingestion with a custom ontology:

  ```bash
  uv run zep_ingest.py --custom-ontology
  ```

  <Callout intent="info">
    The ingestion process creates numbered run directories (e.g., `1_20251103T123456`) containing manifest files that document created users, thread IDs, and configuration details.
  </Callout>

  ### Run evaluation

  Evaluate the most recent ingestion run:

  ```bash
  uv run zep_evaluate.py
  ```

  To evaluate a specific run:

  ```bash
  uv run zep_evaluate.py 1
  ```

  <Note>
    Results are saved to `runs/{run_number}/evaluation_results_{timestamp}.json`.
  </Note>
</Steps>

## Understanding the evaluation pipeline

The harness performs four automated steps for each test case:

<Steps>
  ### Search

  Query Zep's knowledge graph using a cross-encoder reranker to retrieve relevant information.

  ### Evaluate context

  Assess whether the retrieved information is sufficient to answer the test question. This produces the **primary metric**:

  * **COMPLETE**: All necessary information present
  * **PARTIAL**: Some relevant information, but incomplete
  * **INSUFFICIENT**: Missing critical information

  ### Generate response

  Use GPT-4o-mini with the retrieved context to generate an answer to the test question.

  ### Grade answer

  Evaluate the generated response against the golden answer using GPT-4o. This produces the **secondary metric**:

  * **CORRECT**: Response matches golden answer
  * **WRONG**: Response does not match golden answer
</Steps>

## Configuration

You can customize the evaluation parameters in `zep_evaluate.py`:

```python
# Search limits
FACTS_LIMIT = 20      # Number of edges to return
ENTITIES_LIMIT = 10   # Number of nodes to return
EPISODES_LIMIT = 0    # Disabled by default

# Reranker options: cross_encoder (default), rrf, or mmr
```

<Tip>
  The context completeness evaluation (step 2) is the primary metric as it measures Zep's core capability: retrieving relevant information. The answer grading (step 4) is secondary since it also depends on the LLM's ability to use that context.
</Tip>

## Output metrics

The evaluation results include:

* **Aggregate scores**: Overall context completeness and answer accuracy rates
* **Per-user breakdown**: Performance metrics for each user
* **Detailed test results**: Individual test case results with context and answers
* **Performance timing**: Processing time for each step

## Best practices

<AccordionGroup>
  <Accordion title="Design fair tests">
    Ensure the answer to each test question is present somewhere in the ingested data. Tests should evaluate Zep's retrieval capabilities, not whether the information exists.
  </Accordion>

  <Accordion title="Account for processing time">
    Graph processing is asynchronous and typically takes 5-20 seconds per message. Episode processing time can vary significantly. Allow sufficient time between ingestion and evaluation.
  </Accordion>

  <Accordion title="Use multiple test categories">
    Categorize your test cases to understand performance across different types of queries (e.g., personal preferences, work history, recent events).
  </Accordion>

  <Accordion title="Monitor context completeness">
    Focus on the context completeness metric as your primary indicator of Zep's performance. If context is consistently incomplete, consider adjusting your data ingestion strategy or search parameters.
  </Accordion>
</AccordionGroup>

## Next steps

* Learn more about [customizing your context block](/cookbook/customize-your-context-block)
* Explore [graph search parameters](/searching-the-graph) to optimize retrieval
* Understand [best practices for memory management](/best-practices/context-assembly)


# Role-Based Access Control

<Warning>
  Early access only. Contact your Zep account team to enable RBAC for your workspace.
</Warning>

<Info>
  Available to [Enterprise Plan](https://www.getzep.com/pricing) customers only.
</Info>

## Overview

Role-based access control (RBAC) lets you grant the right level of access to each teammate while keeping sensitive account actions limited to trusted users. RBAC grants permissions through roles, and every member can hold multiple assignments across the account and individual projects.

## Scopes and authorizations

RBAC permissions are evaluated at two scopes:

* **Account scope:** Covers organization-wide settings such as member management, billing, and account-level API keys, along with full access to every project.
* **Project scope:** Grants permissions for a single project, including its data plane, collaborators, and project-specific API keys, without exposing other projects or global settings.

Authorizations are grouped into the following capability areas. These appear in the dashboard when you review role details.

* `account.view.readonly` — View account-level configuration, billing status, and usage.
* `rbac.account.manage` — Create, update, or delete account-scoped role assignments, including promoting additional Account Owners.
* `rbac.project.manage` — Manage project-scoped assignments and project-level resources (API keys, data ingestion, deletion) for the projects a member administers.

## Roles

The early access catalog includes account-wide roles and project-scoped roles. Assignments can be combined so that, for example, a teammate can be an Account Admin and a Project Viewer on a sensitive project.

<Info>
  Non-Enterprise plans can assign Account Owner and Account Admin roles. Upgrade to Enterprise to unlock project-level roles and granular account roles (Billing Admin, Account Viewer, Project Creator).
</Info>

### Account-level roles

| Role                | Scope   | Intended for                          | Key authorizations                                                                                                                                                                                                                                                                        |
| ------------------- | ------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Account Owner**   | Account | Founders, security administrators     | `account.view.readonly`, `rbac.account.manage`, `rbac.project.manage`<br />Manage billing and plan settings.<br />Create, update, and archive projects.<br />Rotate account and project API keys.<br />Assign or revoke any role, including other Account Owners.                         |
| **Account Admin**   | Account | Day-to-day operators who run projects | `account.view.readonly`, `rbac.project.manage`<br />Create and manage projects and API keys.<br />Ingest or delete memory, documents, and graph data.<br />Assign and revoke project-scoped roles for any project.<br />Cannot remove the last Account Owner or change billing ownership. |
| **Billing Admin**   | Account | Finance or procurement partners       | `billing.manage`<br />View invoices and update payment details.<br />No access to project data or member management.                                                                                                                                                                      |
| **Account Viewer**  | Account | Compliance and audit reviewers        | `account.view.readonly`, `project.data.read`, `apikey.view`<br />Read account details, project metadata, and API keys.<br />Cannot make configuration changes.                                                                                                                            |
| **Project Creator** | Account | Builders who bootstrap new projects   | `project.create`<br />Create new projects from the dashboard.<br />No access to existing projects unless separately assigned.                                                                                                                                                             |

### Project-level roles

| Role               | Scope   | Intended for                                    | Key authorizations                                                                                                                                                                |
| ------------------ | ------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Project Admin**  | Project | Team leads who manage a single project          | `rbac.project.manage` for the assigned project only.<br />Invite or remove project collaborators.<br />Create and rotate project API keys.<br />Ingest and delete project data.   |
| **Project Editor** | Project | Data engineers or agents that need write access | Read and write all project data, including memory, documents, and graph content.<br />Use project API keys to ingest or delete data.<br />Cannot assign roles or manage API keys. |
| **Project Viewer** | Project | Analysts, auditors, or embedded stakeholders    | View project configuration, usage, threads, documents, and graph content.<br />Run read-only queries and exports.<br />Cannot ingest, delete, or manage API keys.                 |

## Managing role assignments

* Use the **Settings ▸ Access Control** page in the Zep Dashboard to add or remove roles. Search for an existing member or invite a new teammate, then assign any combination of account and project roles.
* Filter by project to focus on project-scoped roles, or view the full access matrix to understand overlapping assignments.
* Every member must have at least one Account Owner assigned. Attempts to delete the final Account Owner are rejected.
* The dashboard prevents duplicate assignments for the same member, scope, and project.
* Removing a role hides it from the active list but keeps the history available; you can restore access later by adding the role again.


# Bring Your Own Key (BYOK)

<Warning>
  Early access only. Contact your Zep account team to enable BYOK for your workspace.
</Warning>

<Info>
  Available to [Enterprise Plan](https://www.getzep.com/pricing) customers only.
</Info>

## Overview

Bring Your Own Key (BYOK) gives you full control over the encryption keys that protect your data at rest in Zep Cloud. Instead of relying on provider-managed keys, you generate and manage a Customer Managed Key (CMK) in your own AWS KMS account. Zep uses that key—under a narrowly scoped, auditable permission—to encrypt and decrypt the data that belongs to your organization.

Key highlights:

* **Customer-controlled encryption:** You can rotate, revoke, or disable your CMK at any time, immediately gating access to your encrypted data.
* **Envelope encryption model:** Zep uses your CMK to derive short-lived data encryption keys (DEKs) for each tenant and storage layer, ensuring strong isolation without adding latency to live requests.
* **Comprehensive auditability:** All KMS usage is logged in your AWS CloudTrail. Zep maintains matching provider-side audit logs for shared visibility and compliance reporting.
* **Separation of duties:** Operational staff cannot access both encrypted data and the keys required to decrypt it. Access requires multi-party approvals and is fully logged.

## Getting started

1. **Provision a CMK in AWS KMS.** Use an AWS account you control and enable automatic rotation if required by your policies.
2. **Configure a minimal KMS policy.** Grant Zep’s BYOK service permissions to generate and decrypt data keys on your behalf. The policy is limited to your tenant scope and can be revoked at any time.
3. **Share the CMK ARN with Zep.** Your account team will coordinate a secure exchange and validate connectivity in a non-production environment before rollout.
4. **Monitor key usage.** Enable CloudTrail logging for your CMK. Zep recommends creating alerts for unusual patterns, such as unexpected decrypt attempts or access from unfamiliar regions.
5. **Roll out to production.** Zep will migrate your tenant to BYOK-backed encryption with no downtime. You retain ongoing control through KMS aliases and policy changes.

## FAQ

**Can Zep access my data in plaintext?**\
Routine operations do not require manual access to plaintext data. Automated services decrypt data within isolated, audited environments. In exceptional cases—such as a customer-approved incident investigation—access is governed by strict separation of duties, multi-party approvals, and comprehensive logging. You retain the ability to disable your CMK, which immediately blocks further decryption.

**What happens if I disable or delete my CMK?**\
All encrypted data becomes unreadable. This is by design: the key is the final arbiter of access. Ensure you have internal procedures for emergency restores before disabling or deleting a key.

**Does BYOK introduce latency?**\
No. Zep caches derived data encryption keys securely in memory, so encryption and decryption happen without additional round trips to AWS KMS during live traffic.

**Can I rotate keys without downtime?**\
Yes. You can enable automatic rotation in AWS KMS. Key versions created through rotation are honored automatically, and data encryption keys are re-wrapped in the background. Disabling the key immediately revokes access.

**Is BYOK applied to every data store?**\
Yes. All persistent storage and backups for your tenant use envelope encryption derived from your CMK. Stateless services process data in memory and never persist plaintext content.

**Where is my data stored?**\
Customer data remains within the AWS regions operated by Zep. Data in motion is encrypted with TLS 1.3, and at rest it is encrypted using keys derived from your CMK.

**How do I audit KMS activity?**\
Review the AWS CloudTrail logs generated in your account. Every encrypt, decrypt, and key management action involving your CMK is recorded. Zep maintains corresponding provider-side logs that can be shared under NDA for compliance reviews.

**Who is responsible for key lifecycle management?**\
You own the CMK, including rotation, revocation, and IAM policy management. Zep monitors for key state changes and will notify your administrators if a key action affects service availability.


# Bring Your Own LLM (BYOM)

<Warning>
  Early access only. Contact your Zep account team to enable BYOM for your workspace.
</Warning>

<Info>
  Available to [Enterprise Plan](https://www.getzep.com/pricing) customers only.
</Info>

## Overview

Bring Your Own LLM (BYOM) lets you connect your existing contracts with model providers such as OpenAI, Anthropic, and Google to Zep Cloud. You keep using Zep’s orchestration, memory, and security controls while routing inference through credentials you manage. This approach ensures:

* **Contract continuity:** Apply your negotiated pricing, quotas, and compliance commitments with each LLM vendor.
* **Data governance:** Enforce provider-specific policies for data usage, retention, and residency.
* **Operational flexibility:** Configure the best vendor or model for each project, including fallbacks for high availability.

## Getting started

1. **Collect provider credentials.** Obtain API keys or service accounts for your chosen vendors. Each Zep project can use a different set of credentials, enabling separation between environments.
2. **Add credentials in the Zep dashboard.** Navigate to **Settings ▸ LLM Providers** within a project, select a vendor, and paste the credential. Zep stores the secret securely in an encrypted secrets manager within your project scope.
3. **(Optional) Supply a customer-managed KMS key.** If you require customer-controlled encryption, provide a KMS ARN with `kms:Encrypt`, `kms:Decrypt`, and `kms:DescribeKey` permissions granted to Zep’s runtime roles. Zep validates the key with a test encrypt/decrypt during setup.
4. **Select default and fallback models.** Choose a primary model for the project. Optionally configure fallbacks to maintain continuity if the primary vendor rate limits or experiences an outage.
5. **Monitor usage and quotas.** Use project analytics to track call volume by provider. Configure per-provider rate limits to enforce budget or vendor restrictions.

## FAQ

**Does Zep store our provider keys in its databases?**\
No. Keys are stored securely in an encrypted secrets manager. Values are decrypted in memory only when needed and are never written to Zep databases.

**Can we use different vendors or models per project?**\
Yes. Each project maintains its own provider configuration, including defaults and fallbacks. This is useful for isolating production from staging or testing providers side by side.

**Can we prevent vendors from training on our data?**\
Yes. Use the vendor endpoints and contractual controls that disable data retention or training. Zep routes requests accordingly and sets the necessary flags in each call.

**How is usage billed?**\
You receive invoices from Zep for Zep services only. LLM inference charges come directly from your vendors under your existing contract and pricing.

**What happens if a key is compromised or needs rotation?**\
Add a new credential in the dashboard, mark it as active, then disable the previous one. Requests start using the new credential immediately; no downtime is required.

**How does BYOM affect observability?**\
Requests are tagged by project and provider, so you can attribute usage and costs. Rate limits can be applied per provider to protect budgets and enforce quotas.


# LangGraph Memory Example

> LangGraph is a library created by LangChain for building stateful, multi-agent applications. This example demonstrates using Zep for LangGraph agent memory.

<Info>
  A complete Notebook example of using Zep for LangGraph Memory may be found in the [Zep Python SDK Repository](https://github.com/getzep/zep/blob/main/examples/python/langgraph-agent/agent.ipynb).
</Info>

The following example demonstrates building an agent using LangGraph. Zep is used to personalize agent responses based on information learned from prior conversations.

The agent implements:

* persistance of new chat turns to Zep and recall of relevant Facts using the most recent messages.
* an in-memory MemorySaver to maintain agent state. We use this to add recent chat history to the agent prompt. As an alternative, you could use Zep for this.

<Note>
  You should consider truncating MemorySaver's chat history as by default LangGraph state grows unbounded. We've included this in our example below. See the LangGraph documentation for insight.
</Note>

## Install dependencies

```shell
pip install zep-cloud langchain-openai langgraph ipywidgets python-dotenv
```

## Configure Zep

Ensure that you've configured the following API keys in your environment. We're using Zep's Async client here, but we could also use the non-async equivalent.

```bash
ZEP_API_KEY=your_zep_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

```python
import os
import uuid
import logging
from typing import Annotated, TypedDict

from zep_cloud.client import AsyncZep
from zep_cloud import Message

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, trim_messages
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

# Optional: Load environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Zep client
zep = AsyncZep(api_key=os.environ.get('ZEP_API_KEY'))
```

## Define State and Setup Tools

First, define the state structure for our LangGraph agent:

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    first_name: str
    last_name: str
    thread_id: str
    user_name: str
```

## Using Zep's Search as a Tool

These are examples of simple Tools that search Zep for facts (from edges) or nodes. Since LangGraph tools don't automatically receive the full graph state, we create a function that returns configured tools for a specific user:

```python
def create_zep_tools(user_name: str):
    """Create Zep search tools configured for a specific user."""
    
    @tool
    async def search_facts(query: str, limit: int = 5) -> list[str]:
        """Search for facts in all conversations had with a user.
        
        Args:
            query (str): The search query.
            limit (int): The number of results to return. Defaults to 5.

        Returns:
            list: A list of facts that match the search query.
        """
        result = await zep.graph.search(
            user_id=user_name, query=query, limit=limit, scope="edges"
        )
        facts = [edge.fact for edge in result.edges or []]
        if not facts:
            return ["No facts found for the query."]
        return facts

    @tool
    async def search_nodes(query: str, limit: int = 5) -> list[str]:
        """Search for nodes in all conversations had with a user.
        
        Args:
            query (str): The search query.
            limit (int): The number of results to return. Defaults to 5.

        Returns:
            list: A list of node summaries for nodes that match the search query.
        """
        result = await zep.graph.search(
            user_id=user_name, query=query, limit=limit, scope="nodes"
        )
        summaries = [node.summary for node in result.nodes or []]
        if not summaries:
            return ["No nodes found for the query."]
        return summaries
    
    return [search_facts, search_nodes]

# We'll create the actual tools after we have a user_name
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

## Chatbot Function Explanation

The chatbot uses Zep to provide context-aware responses. Here's how it works:

1. **Context Retrieval**: It retrieves relevant facts for the user's current conversation (thread). Zep uses the most recent messages to determine what facts to retrieve.

2. **System Message**: It constructs a system message incorporating the facts retrieved in 1., setting the context for the AI's response.

3. **Message Persistence**: After generating a response, it asynchronously adds the user and assistant messages to Zep. New Facts are created and existing Facts updated using this new information.

4. **Messages in State**: We use LangGraph state to store the most recent messages and add these to the Agent prompt. We limit the message list to the most recent 3 messages for demonstration purposes.

<Note>
  We could also use Zep to recall the chat history, rather than LangGraph's MemorySaver.

  See [`thread.get_user_context`](/sdk-reference/thread/get-user-context) in the Zep SDK documentation.
</Note>

```python
async def chatbot(state: State):
    memory = await zep.thread.get_user_context(state["thread_id"])

    system_message = SystemMessage(
        content=f"""You are a compassionate mental health bot and caregiver. Review information about the user and their prior conversation below and respond accordingly.
        Keep responses empathetic and supportive. And remember, always prioritize the user's well-being and mental health.

        {memory.context}"""
    )

    messages = [system_message] + state["messages"]

    response = await llm.ainvoke(messages)

    # Add the new chat turn to the Zep graph
    messages_to_save = [
        Message(
            role="user",
            name=state["first_name"] + " " + state["last_name"],
            content=state["messages"][-1].content,
        ),
        Message(role="assistant", content=response.content),
    ]

    await zep.thread.add_messages(
        thread_id=state["thread_id"],
        messages=messages_to_save,
    )

    # Truncate the chat history to keep the state from growing unbounded
    # In this example, we going to keep the state small for demonstration purposes
    # We'll use Zep's Facts to maintain conversation context
    state["messages"] = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=len,
        max_tokens=3,
        start_on="human",
        end_on=("human", "tool"),
        include_system=True,
    )

    logger.info(f"Messages in state: {state['messages']}")

    return {"messages": [response]}
```

## Setting up the Agent

This function creates a complete LangGraph agent configured for a specific user. This approach allows us to properly configure the tools with the user context:

```python
def create_agent(user_name: str):
    """Create a LangGraph agent configured for a specific user."""
    
    # Create tools configured for this user
    tools = create_zep_tools(user_name)
    tool_node = ToolNode(tools)
    llm_with_tools = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)
    
    # Update the chatbot function to use the configured LLM
    async def chatbot_with_tools(state: State):
        memory = await zep.thread.get_user_context(state["thread_id"])

        system_message = SystemMessage(
            content=f"""You are a compassionate mental health bot and caregiver. Review information about the user and their prior conversation below and respond accordingly.
            Keep responses empathetic and supportive. And remember, always prioritize the user's well-being and mental health.

            {memory.context}"""
        )

        messages = [system_message] + state["messages"]

        response = await llm_with_tools.ainvoke(messages)

        # Add the new chat turn to the Zep graph
        messages_to_save = [
            Message(
                role="user",
                name=state["first_name"] + " " + state["last_name"],
                content=state["messages"][-1].content,
            ),
            Message(role="assistant", content=response.content),
        ]

        await zep.thread.add_messages(
            thread_id=state["thread_id"],
            messages=messages_to_save,
        )

        # Truncate the chat history to keep the state from growing unbounded
        state["messages"] = trim_messages(
            state["messages"],
            strategy="last",
            token_counter=len,
            max_tokens=3,
            start_on="human",
            end_on=("human", "tool"),
            include_system=True,
        )

        logger.info(f"Messages in state: {state['messages']}")

        return {"messages": [response]}
    
    # Define the function that determines whether to continue or not
    async def should_continue(state, config):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"
    
    # Build the graph
    graph_builder = StateGraph(State)
    memory = MemorySaver()
    
    graph_builder.add_node("agent", chatbot_with_tools)
    graph_builder.add_node("tools", tool_node)
    
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", should_continue, {"continue": "tools", "end": END})
    graph_builder.add_edge("tools", "agent")
    
    return graph_builder.compile(checkpointer=memory)
```

Our LangGraph agent graph is illustrated below.

![Agent Graph](file:076bec8c-aba7-4928-92db-3d1808fe43e7)

## Running the Agent

We generate a unique user name and thread id, add these to Zep, and create our configured agent:

```python
first_name = "Daniel"
last_name = "Chalef"
user_name = first_name + uuid.uuid4().hex[:4]
thread_id = uuid.uuid4().hex

# Create user and thread in Zep
await zep.user.add(user_id=user_name, first_name=first_name, last_name=last_name)
await zep.thread.create(thread_id=thread_id, user_id=user_name)

# Create the agent configured for this user
graph = create_agent(user_name)


def extract_messages(result, user_name):
    output = ""
    for message in result["messages"]:
        if isinstance(message, AIMessage):
            name = "assistant"
        else:
            name = user_name
        output += f"{name}: {message.content}\n"
    return output.strip()


async def graph_invoke(
    message: str,
    first_name: str,
    last_name: str,
    user_name: str,
    thread_id: str,
    ai_response_only: bool = True,
):
    r = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=message)],
            "first_name": first_name,
            "last_name": last_name,
            "thread_id": thread_id,
            "user_name": user_name,
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    if ai_response_only:
        return r["messages"][-1].content
    else:
        return extract_messages(r, user_name)
```

Let's test the agent with a few messages:

```python
r = await graph_invoke(
    "Hi there?",
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
```

> Hello! How are you feeling today? I'm here to listen and support you.

```python
r = await graph_invoke(
    """
    I'm fine. But have been a bit stressful lately. Mostly work related. 
    But also my dog. I'm worried about her.
    """,
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
```

> I'm sorry to hear that you've been feeling stressed. Work can be a significant source of pressure, and it sounds like your dog might be adding to that stress as well. If you feel comfortable sharing, what specifically has been causing you stress at work and with your dog? I'm here to help you through it.

## Viewing The Context Value

```python
memory = await zep.thread.get_user_context(thread_id=thread_id)

print(memory.context)
```

The context value will look something like this:

```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
<FACTS>
  - Daniel99db is worried about his sick dog. (2025-01-24 02:11:54 - present)
  - Daniel Chalef is worried about his sick dog. (2025-01-24 02:11:54 - present)
  - The assistant asks how the user is feeling. (2025-01-24 02:11:51 - present)
  - Daniel99db has been a bit stressful lately due to his dog. (2025-01-24 02:11:53 - present)
  - Daniel99db has been a bit stressful lately due to work. (2025-01-24 02:11:53 - present)
  - Daniel99db is a user. (2025-01-24 02:11:51 - present)
  - user has the id of Daniel99db (2025-01-24 02:11:50 - present)
  - user has the name of Daniel Chalef (2025-01-24 02:11:50 - present)
</FACTS>
# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
  - worried: Daniel Chalef (Daniel99db) is feeling stressed lately, primarily due to work-related issues and concerns about his sick dog, which has made him worried.
  - Daniel99db: Daniel99db, or Daniel Chalef, is currently experiencing stress primarily due to work-related issues and concerns about his sick dog. Despite these challenges, he has shown a desire for interaction by initiating conversations, indicating his openness to communication.
  - sick: Daniel Chalef, also known as Daniel99db, is feeling stressed lately, primarily due to work-related issues and concerns about his sick dog. He expresses worry about his dog's health.
  - Daniel Chalef: Daniel Chalef, also known as Daniel99db, has been experiencing stress recently, primarily related to work issues and concerns about his sick dog. Despite this stress, he has been feeling generally well and has expressed a desire to connect with others, as indicated by his friendly greeting, "Hi there?".
  - dog: Daniel99db, also known as Daniel Chalef, mentioned that he has been feeling a bit stressed lately, which is related to both work and his dog.
  - work: Daniel Chalef, also known as Daniel99db, has been experiencing stress lately, primarily related to work.
  - feeling: The assistant initiates a conversation by asking how the user is feeling today, indicating a willingness to listen and provide support.
</ENTITIES>
```

```python
r = await graph_invoke(
    "She ate my shoes which were expensive.",
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
```

> That sounds really frustrating, especially when you care so much about your belongings and your dog's health. It's tough when pets get into things they shouldn't, and it can add to your stress. How are you feeling about that situation? Are you able to focus on her health despite the shoe incident?

Let's now test whether the Agent is correctly grounded with facts from the prior conversation.

```python
r = await graph_invoke(
    "What are we talking about?",
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
```

> We were discussing your concerns about your dog being sick and the situation with her eating your expensive shoes. It sounds like you're dealing with a lot right now, and I want to make sure we're addressing what's on your mind. If there's something else you'd like to talk about or if you want to share more about your dog, I'm here to listen.

Let's go even further back to determine whether context is kept by referencing a user message that is not currently in the Agent State. Zep will retrieve Facts related to the user's job.

```python
r = await graph_invoke(
    "What have I said about my job?",
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
```

> You've mentioned that you've been feeling a bit stressed lately, primarily due to work-related issues. If you'd like to share more about what's been going on at work or how it's affecting you, I'm here to listen and support you.


# Autogen memory integration

> Add persistent memory to Microsoft Autogen agents using the zep-autogen package.

The `zep-autogen` package provides seamless integration between Zep and Microsoft Autogen agents. Choose between [user-specific conversation memory](/users) or structured [knowledge graph memory](/graph-overview) for intelligent context retrieval.

## Install dependencies

<CodeBlocks>
  ```bash pip
  pip install zep-autogen zep-cloud autogen-core autogen-agentchat
  ```

  ```bash uv  
  uv add zep-autogen zep-cloud autogen-core autogen-agentchat
  ```

  ```bash poetry
  poetry add zep-autogen zep-cloud autogen-core autogen-agentchat
  ```
</CodeBlocks>

## Environment setup

Set your API keys as environment variables:

```bash
export ZEP_API_KEY="your_zep_api_key"
export OPENAI_API_KEY="your_openai_api_key"
```

## Memory types

**User Memory**: Stores conversation history in [user threads](/users) with automatic context injection\
**Knowledge Graph Memory**: Maintains structured knowledge with [custom entity models](/customizing-graph-structure)

## User memory

<Steps>
  ### Step 1: Setup required imports

  ```python
  import os
  import uuid
  import asyncio
  from autogen_agentchat.agents import AssistantAgent
  from autogen_ext.models.openai import OpenAIChatCompletionClient
  from autogen_core.memory import MemoryContent, MemoryMimeType
  from zep_cloud.client import AsyncZep
  from zep_autogen import ZepUserMemory
  ```

  ### Step 2: Initialize client and create user

  ```python
  # Initialize Zep client
  zep_client = AsyncZep(api_key=os.environ.get("ZEP_API_KEY"))
  user_id = f"user_{uuid.uuid4().hex[:16]}"
  thread_id = f"thread_{uuid.uuid4().hex[:16]}"

  # Create user (required before using memory)
  try:
      await zep_client.user.add(
          user_id=user_id,
          email="alice@example.com",
          first_name="Alice"
      )
  except Exception as e:
      print(f"User might already exist: {e}")

  # Create thread (required for conversation memory)
  try:
      await zep_client.thread.create(thread_id=thread_id, user_id=user_id)
  except Exception as e:
      print(f"Thread creation failed: {e}")
  ```

  ### Step 3: Create memory with configuration

  ```python
  # Create user memory with configuration
  memory = ZepUserMemory(
      client=zep_client,
      user_id=user_id,
      thread_id=thread_id,
      thread_context_mode="summary"  # "summary" or "basic"
  )
  ```

  ### Step 4: Create agent with memory

  ```python
  # Create agent with Zep memory
  agent = AssistantAgent(
      name="MemoryAwareAssistant",
      model_client=OpenAIChatCompletionClient(
          model="gpt-4.1-mini",
          api_key=os.environ.get("OPENAI_API_KEY")
      ),
      memory=[memory],
      system_message="You are a helpful assistant with persistent memory."
  )
  ```

  ### Step 5: Store messages and run conversations

  ```python
  # Helper function to store messages with proper metadata
  async def add_message(message: str, role: str, name: str = None):
      """Store a message in Zep memory following AutoGen standards."""
      metadata = {"type": "message", "role": role}
      if name:
          metadata["name"] = name
      
      await memory.add(MemoryContent(
          content=message,
          mime_type=MemoryMimeType.TEXT,
          metadata=metadata
      ))

  # Example conversation with memory persistence
  user_message = "My name is Alice and I love hiking in the mountains."
  print(f"User: {user_message}")

  # Store user message
  await add_message(user_message, "user", "Alice")

  # Run agent - it will automatically retrieve context via update_context()
  response = await agent.run(task=user_message)
  agent_response = response.messages[-1].content
  print(f"Agent: {agent_response}")

  # Store agent response
  await add_message(agent_response, "assistant")
  ```
</Steps>

<Callout intent="info">
  **Automatic Context Injection**: ZepUserMemory automatically injects relevant conversation history and context via the `update_context()` method. The agent receives up to 10 recent messages plus summarized context from Zep using the specified `thread_context_mode` ("basic" or "summary").
</Callout>

## Knowledge graph memory

<Steps>
  ### Step 1: Define custom entity models

  ```python
  from zep_autogen.graph_memory import ZepGraphMemory
  from zep_cloud.external_clients.ontology import EntityModel, EntityText
  from pydantic import Field

  # Define entity models using Pydantic
  class ProgrammingLanguage(EntityModel):
      """A programming language entity."""
      paradigm: EntityText = Field(
          description="programming paradigm (e.g., object-oriented, functional)",
          default=None
      )
      use_case: EntityText = Field(
          description="primary use cases for this language",
          default=None
      )

  class Framework(EntityModel):
      """A software framework or library."""
      language: EntityText = Field(
          description="the programming language this framework is built for",
          default=None
      )
      purpose: EntityText = Field(
          description="primary purpose of this framework",
          default=None
      )
  ```

  ### Step 2: Setup graph with ontology

  ```python
  from zep_cloud import SearchFilters

  # Set ontology first
  await zep_client.graph.set_ontology(
      entities={
          "ProgrammingLanguage": ProgrammingLanguage,
          "Framework": Framework,
      }
  )

  # Create graph
  graph_id = f"graph_{uuid.uuid4().hex[:16]}"
  try:
      await zep_client.graph.create(
          graph_id=graph_id,
          name="Programming Knowledge Graph"
      )
      print(f"Created graph: {graph_id}")
  except Exception as e:
      print(f"Graph creation failed: {e}")
  ```

  ### Step 3: Initialize graph memory with filters

  ```python
  # Create graph memory with search configuration
  graph_memory = ZepGraphMemory(
      client=zep_client,
      graph_id=graph_id,
      search_filters=SearchFilters(
          node_labels=["ProgrammingLanguage", "Framework"]
      ),
      facts_limit=20,  # Max facts in context injection (default: 20)
      entity_limit=5   # Max entities in context injection (default: 5)
  )
  ```

  ### Step 4: Add data and wait for indexing

  ```python
  # Add structured knowledge
  await graph_memory.add(MemoryContent(
      content="Python is excellent for data science and AI development",
      mime_type=MemoryMimeType.TEXT,
      metadata={"type": "data"}  # "data" stores in graph, "message" stores as episode
  ))

  # Wait for graph processing (required)
  print("Waiting for graph indexing...")
  await asyncio.sleep(30)  # Allow time for knowledge extraction

  <Callout intent="info">
  **Graph Memory Context Injection**: ZepGraphMemory automatically retrieves the last 2 episodes from the graph and uses their content to query for relevant facts (up to `facts_limit`) and entities (up to `entity_limit`). This context is injected as a system message during agent interactions.
  </Callout>
  ```

  ### Step 5: Create agent with graph memory

  ```python
  # Create agent with graph memory
  agent = AssistantAgent(
      name="GraphMemoryAssistant",
      model_client=OpenAIChatCompletionClient(model="gpt-4.1-mini"),
      memory=[graph_memory],
      system_message="You are a technical assistant with programming knowledge."
  )
  ```
</Steps>

## Tools integration

Zep tools allow agents to search and add data directly to memory storage with manual control and structured responses.

<Callout intent="warning">
  **Important**: Tools must be bound to either `graph_id` OR `user_id`, not both. This determines whether they operate on knowledge graphs or user graphs.
</Callout>

### Tool function parameters

**Search Tool Parameters**:

* `query`: str (required) - Search query text
* `limit`: int (optional, default 10) - Maximum results to return
* `scope`: str (optional, default "edges") - Search scope: "edges", "nodes", "episodes"

**Add Tool Parameters**:

* `data`: str (required) - Content to store
* `data_type`: str (optional, default "text") - Data type: "text", "json", "message"

### User graph tools

```python
from zep_autogen import create_search_graph_tool, create_add_graph_data_tool

# Create tools bound to user graph
search_tool = create_search_graph_tool(zep_client, user_id=user_id)
add_tool = create_add_graph_data_tool(zep_client, user_id=user_id)

# Agent with user graph tools
agent = AssistantAgent(
    name="UserKnowledgeAssistant",
    model_client=OpenAIChatCompletionClient(model="gpt-4.1-mini"),
    tools=[search_tool, add_tool],
    system_message="You can search and add data to the user's knowledge graph.",
    reflect_on_tool_use=True  # Enables tool usage reflection
)
```

### Knowledge graph tools

```python
# Create tools bound to knowledge graph
search_tool = create_search_graph_tool(zep_client, graph_id=graph_id)
add_tool = create_add_graph_data_tool(zep_client, graph_id=graph_id)

# Agent with knowledge graph tools
agent = AssistantAgent(
    name="KnowledgeGraphAssistant",
    model_client=OpenAIChatCompletionClient(model="gpt-4.1-mini"),
    tools=[search_tool, add_tool],
    system_message="You can search and add data to the knowledge graph.",
    reflect_on_tool_use=True
)
```

## Query memory

Both memory types support direct querying with different scope parameters.

### User memory queries

```python
# Query user conversation history  
results = await memory.query("What does Alice like?", limit=5)

# Process different result types
for result in results.results:
    content = result.content
    metadata = result.metadata
    
    if 'edge_name' in metadata:
        # Fact/relationship result
        print(f"Fact: {content}")
        print(f"Relationship: {metadata['edge_name']}")
        print(f"Valid: {metadata.get('valid_at', 'N/A')} - {metadata.get('invalid_at', 'present')}")
    elif 'node_name' in metadata:
        # Entity result
        print(f"Entity: {metadata['node_name']}")
        print(f"Summary: {content}")
    else:
        # Episode/message result
        print(f"Message: {content}")
        print(f"Role: {metadata.get('episode_role', 'unknown')}")
    
    print(f"Source: {metadata.get('source')}\n")
```

### Graph memory queries

```python
# Query knowledge graph with scope control
facts_results = await graph_memory.query(
    "Python frameworks", 
    limit=10, 
    scope="edges"  # "edges" (facts), "nodes" (entities), "episodes" (messages)
)

print(f"Found {len(facts_results.results)} facts about Python frameworks:")
for result in facts_results.results:
    print(f"- {result.content}")
    
entities_results = await graph_memory.query(
    "programming languages",
    limit=5,
    scope="nodes"
)

print(f"\nFound {len(entities_results.results)} programming language entities:")
for result in entities_results.results:
    entity_name = result.metadata.get('node_name', 'Unknown')
    print(f"- {entity_name}: {result.content}")
```

### Search result structure

<AccordionGroup>
  <Accordion title="Edge results (facts)">
    ```json
    {
        "content": "fact text",
        "metadata": {
            "source": "graph" | "user_graph",
            "edge_name": "relationship_name",
            "edge_attributes": {...},
            "created_at": "timestamp",
            "valid_at": "timestamp",
            "invalid_at": "timestamp",
            "expired_at": "timestamp"
        }
    }
    ```
  </Accordion>

  <Accordion title="Node results (entities)">
    ```json
    {
        "content": "entity_name:\n entity_summary",
        "metadata": {
            "source": "graph" | "user_graph",
            "node_name": "entity_name",
            "node_attributes": {...},
            "created_at": "timestamp"
        }
    }
    ```
  </Accordion>

  <Accordion title="Episode results (messages)">
    ```json
    {
        "content": "episode_content",
        "metadata": {
            "source": "graph" | "user_graph",
            "episode_type": "source_type",
            "episode_role": "role_type",
            "episode_name": "role_name",
            "created_at": "timestamp"
        }
    }
    ```
  </Accordion>
</AccordionGroup>

## Memory vs tools comparison

<Callout intent="note">
  **Memory Objects** (ZepUserMemory/ZepGraphMemory):

  * Automatic context injection via `update_context()`
  * Attached to agent's memory list
  * Transparent operation - happens automatically
  * Better for consistent memory across interactions

  **Function Tools** (search/add tools):

  * Manual control - agent decides when to use
  * More explicit and observable operations
  * Better for specific search/add operations
  * Works with AutoGen's tool reflection features
  * Provides structured return values

  **Note**: Both approaches can be combined - using memory for automatic context and tools for explicit operations.
</Callout>


# LiveKit voice agents

> Add persistent memory to LiveKit voice agents using the zep-livekit package.

The `zep-livekit` package provides seamless integration between Zep and LiveKit voice agents. Choose between [user-specific conversation memory](/users) or structured [knowledge graph memory](/graph-overview) for intelligent context retrieval in real-time voice interactions.

## Install dependencies

<CodeBlocks>
  ```bash pip
  pip install zep-livekit zep-cloud "livekit-agents[openai,silero]>=1.0.0"
  ```

  ```bash uv  
  uv add zep-livekit zep-cloud "livekit-agents[openai,silero]>=1.0.0"
  ```

  ```bash poetry
  poetry add zep-livekit zep-cloud "livekit-agents[openai,silero]>=1.0.0"
  ```
</CodeBlocks>

<Callout intent="warning">
  **Version Requirements**: This integration requires LiveKit Agents v1.0+ (not v0.x). The examples use the current AgentSession API pattern introduced in v1.0.
</Callout>

## Environment setup

Set your API keys as environment variables:

```bash
export ZEP_API_KEY="your_zep_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export LIVEKIT_URL="your_livekit_url"
export LIVEKIT_API_KEY="your_livekit_api_key"
export LIVEKIT_API_SECRET="your_livekit_secret"
```

## Agent types

**ZepUserAgent**: Uses [user threads](/users) for conversation memory with automatic context injection\
**ZepGraphAgent**: Accesses structured knowledge through [custom entity models](/customizing-graph-structure)

## User memory agent

<Steps>
  ### Step 1: Setup required imports

  ```python
  import asyncio
  import logging
  import os
  from livekit import agents
  from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
  from livekit.plugins import openai, silero
  from zep_cloud.client import AsyncZep
  from zep_livekit import ZepUserAgent
  ```

  ### Step 2: Initialize Zep client and create user

  ```python
  async def entrypoint(ctx: JobContext):
      # Initialize Zep client
      zep_client = AsyncZep(api_key=os.environ.get("ZEP_API_KEY"))
      
      # Create unique user and thread IDs
      participant_name = ctx.room.remote_participants[0].name or "User"
      user_id = f"livekit_{participant_name}_{ctx.room.name}"
      thread_id = f"thread_{ctx.room.name}"
      
      # Create user in Zep (if not exists)
      try:
          await zep_client.user.add(
              user_id=user_id,
              first_name=participant_name
          )
      except Exception as e:
          logging.info(f"User might already exist: {e}")
      
      # Create thread for conversation memory
      try:
          await zep_client.thread.create(thread_id=thread_id, user_id=user_id)
      except Exception as e:
          logging.info(f"Thread might already exist: {e}")
  ```

  ### Step 3: Create agent with memory

  ```python
      # Create agent session with components
      session = agents.AgentSession(
          stt=openai.STT(),
          llm=openai.LLM(model="gpt-4o-mini"),
          tts=openai.TTS(),
          vad=silero.VAD.load(),
      )
      
      # Create Zep memory agent with enhanced configuration
      zep_agent = ZepUserAgent(
          zep_client=zep_client,
          user_id=user_id,
          thread_id=thread_id,
          context_mode="basic",  # or "summary"
          user_message_name=participant_name,
          assistant_message_name="Assistant",
          instructions="You are a helpful voice assistant with persistent memory. "
                      "Remember details from previous conversations and reference them naturally."
      )
      
      # Start the session with the agent
      await session.start(agent=zep_agent, room=ctx.room)
  ```

  ### Step 4: Run the voice assistant

  ```python
      # Voice assistant will now have persistent memory
      logging.info("Voice assistant with Zep memory is running")
      
      # Keep the session running
      await session.aclose()
  ```
</Steps>

<Callout intent="info">
  **Automatic Memory Integration**: ZepUserAgent automatically captures voice conversation turns and injects relevant context from previous conversations, enabling natural continuity across voice sessions.
</Callout>

## ZepUserAgent configuration

The `ZepUserAgent` supports several parameters for customizing memory behavior:

```python
zep_agent = ZepUserAgent(
    zep_client=zep_client,
    user_id="user_123",
    thread_id="thread_456",
    context_mode="basic",  # "basic" or "summary" - how context is assembled
    user_message_name="Alice",  # Name attribution for user messages
    assistant_message_name="Assistant",  # Name attribution for AI messages  
    instructions="Custom system instructions for the agent"
)
```

**Parameters:**

* `context_mode`: Controls how memory context is retrieved (`"basic"` for detailed context, `"summary"` for condensed)
* `user_message_name`: Optional name for attributing user messages in Zep memory
* `assistant_message_name`: Optional name for attributing assistant messages in Zep memory
* `instructions`: System instructions that override the default LiveKit agent instructions

## Knowledge graph agent

<Steps>
  ### Step 1: Define custom entity models

  ```python
  from zep_cloud.external_clients.ontology import EntityModel, EntityText
  from pydantic import Field

  class Person(EntityModel):
      """A person entity for voice interactions."""
      role: EntityText = Field(
          description="person's role or profession",
          default=None
      )
      interests: EntityText = Field(
          description="topics the person is interested in",
          default=None
      )

  class Topic(EntityModel):
      """A conversation topic or subject."""
      category: EntityText = Field(
          description="category of the topic",
          default=None
      )
      importance: EntityText = Field(
          description="importance level of this topic to the user",
          default=None
      )
  ```

  ### Step 2: Setup graph with ontology

  ```python
  from zep_livekit import ZepGraphAgent

  async def setup_graph_agent(ctx: JobContext):
      zep_client = AsyncZep(api_key=os.environ.get("ZEP_API_KEY"))
      
      # Set ontology for structured knowledge
      await zep_client.graph.set_ontology(
          entities={
              "Person": Person,
              "Topic": Topic,
          }
      )
      
      # Create knowledge graph
      graph_id = f"livekit_graph_{ctx.room.name}"
      try:
          await zep_client.graph.create(
              graph_id=graph_id,
              name="LiveKit Voice Knowledge Graph"
          )
      except Exception as e:
          logging.info(f"Graph might already exist: {e}")
  ```

  ### Step 3: Create graph memory agent

  ```python
      # Create agent session with components
      session = agents.AgentSession(
          stt=openai.STT(),
          llm=openai.LLM(model="gpt-4o-mini"),
          tts=openai.TTS(),
          vad=silero.VAD.load(),
      )
      
      # Create Zep graph agent
      zep_agent = ZepGraphAgent(
          zep_client=zep_client,
          graph_id=graph_id,
          facts_limit=15,  # Max facts in context
          entity_limit=8,   # Max entities in context
          search_filters={
              "node_labels": ["Person"]  # Filter to Person entities only
          },
          instructions="You are a knowledgeable voice assistant. Use the provided "
                      "context about entities and facts to give informed responses."
      )
      
      # Start the session with the graph agent
      await session.start(agent=zep_agent, room=ctx.room)
  ```
</Steps>

<Callout intent="info">
  **Search Filters**: The `search_filters` parameter allows you to constrain which entities the agent considers when retrieving context. Use `node_labels` to filter by specific entity types defined in your ontology.
</Callout>

<Callout intent="info">
  **Graph Memory Context**: ZepGraphAgent automatically extracts structured knowledge from voice conversations and injects relevant facts and entities as context for more intelligent responses.
</Callout>

## Room-based memory isolation

LiveKit rooms provide natural memory isolation boundaries:

```python
# Each room gets its own memory context
room_name = ctx.room.name
user_id = f"livekit_user_{room_name}"
thread_id = f"thread_{room_name}"
graph_id = f"graph_{room_name}"

# Memory is isolated per room/session
zep_agent = ZepUserAgent(
    zep_client=zep_client,
    user_id=user_id,
    thread_id=thread_id,
    context_mode="basic",
    user_message_name="User",
    assistant_message_name="Assistant"
)
```

## Voice-specific considerations

**Turn Management**: Voice conversations have different turn dynamics than text chat. Zep automatically handles:

* Overlapping speech detection
* Turn boundary identification
* Context window management for real-time responses

**Memory Persistence**: Key voice interaction details are preserved:

* Speaker identification
* Conversation topics and themes
* User preferences expressed through voice
* Temporal relationships between topics

## Complete example

```python
import asyncio
import logging
import os
from livekit import agents
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
from zep_cloud.client import AsyncZep
from zep_livekit import ZepUserAgent

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Setup Zep integration
    zep_client = AsyncZep(api_key=os.environ.get("ZEP_API_KEY"))
    participant_name = ctx.room.remote_participants[0].name or "User"
    user_id = f"livekit_{participant_name}_{ctx.room.name}"
    thread_id = f"thread_{ctx.room.name}"
    
    # Create user and thread
    try:
        await zep_client.user.add(user_id=user_id, first_name=participant_name)
        await zep_client.thread.create(thread_id=thread_id, user_id=user_id)
    except Exception:
        pass  # Already exists
    
    # Create agent session
    session = agents.AgentSession(
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        vad=silero.VAD.load(),
    )
    
    # Create voice assistant with Zep memory
    zep_agent = ZepUserAgent(
        zep_client=zep_client,
        user_id=user_id,
        thread_id=thread_id,
        context_mode="basic",
        user_message_name=participant_name,
        assistant_message_name="Assistant",
        instructions="You are a helpful voice assistant with persistent memory. "
                    "Remember details from previous conversations."
    )
    
    # Start the session with the agent
    await session.start(agent=zep_agent, room=ctx.room)
    
    logging.info("Voice assistant with Zep memory is running")
    await session.aclose()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Learn more

* [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
* [Zep LiveKit Integration Repository](https://github.com/getzep/zep/tree/main/integrations/python/zep_livekit)
* [LiveKit Python SDK](https://github.com/livekit/python-sdks)


# CrewAI integration

> Add persistent memory and knowledge graphs to CrewAI agents

CrewAI agents equipped with Zep's memory platform can maintain context across conversations, access shared knowledge bases, and make more informed decisions. This integration provides persistent memory storage and intelligent knowledge retrieval for your CrewAI workflows.

## Core benefits

* **Persistent Memory**: Conversations and knowledge persist across sessions
* **Context-Aware Agents**: Agents automatically retrieve relevant context during execution
* **Dual Storage**: User-specific memories and shared organizational knowledge
* **Intelligent Tools**: Search and data addition tools for dynamic knowledge management

## How External Memory Works in CrewAI

External memory in CrewAI operates automatically during crew execution, providing seamless context retrieval and persistence across tasks and executions.

### Automatic Memory Operations

| Operation        | When It Happens            | What Gets Stored/Retrieved                                       |
| ---------------- | -------------------------- | ---------------------------------------------------------------- |
| Memory Retrieval | At the start of each task  | Relevant context based on task description + accumulated context |
| Memory Storage   | After each task completion | Task output text + metadata (task description, messages)         |

**Key Behaviors:**

* **Automatic Retrieval**: When an agent starts a task, CrewAI automatically queries external memory using the query "\{task.description} \{context}" to find relevant historical context
* **Automatic Storage**: When an agent completes a task, CrewAI automatically saves the task output to external memory (if external memory is configured)
* **Cross-Execution Persistence**: External memory persists between crew runs, enabling agents to learn from previous executions
* **Manual Operations**: Developers can also manually add data to external memory or query it directly using the storage interface

This automatic behavior means that once you configure Zep as your external memory provider, your CrewAI agents will seamlessly build context from past interactions and contribute new learnings without additional code.

## Installation

```bash
pip install zep-crewai
```

<Callout intent="info">
  Requires Python 3.10+, Zep CrewAI >=1.1.1, CrewAI >=0.186.0, and a Zep Cloud API key. Get your API key from [app.getzep.com](https://app.getzep.com).
</Callout>

Set up your environment variables:

```bash
export ZEP_API_KEY="your-zep-api-key"
```

## Storage types

### User storage

Use `ZepUserStorage` for personal context and conversation history:

<CodeBlocks>
  ```python Python
  import os
  from zep_cloud.client import Zep
  from zep_crewai import ZepUserStorage
  from crewai import Agent, Crew, Task
  from crewai.memory.external.external_memory import ExternalMemory

  # Initialize Zep client
  zep_client = Zep(api_key=os.getenv("ZEP_API_KEY"))

  # Create user and thread
  zep_client.user.add(user_id="alice_123", first_name="Alice")
  zep_client.thread.create(user_id="alice_123", thread_id="project_456")

  # Set up user storage
  user_storage = ZepUserStorage(
      client=zep_client,
      user_id="alice_123",
      thread_id="project_456",
      mode="summary"  # or "basic" for faster retrieval
  )

  # Create crew with user memory
  crew = Crew(
      agents=[your_agent],
      tasks=[your_task],
      external_memory=ExternalMemory(storage=user_storage)
  )
  ```
</CodeBlocks>

User storage automatically routes data:

* **Messages** (`type: "message"`) → Thread API for conversation context
* **JSON/Text** (`type: "json"` or `type: "text"`) → User Graph for preferences

### Graph storage

Use `ZepGraphStorage` for organizational knowledge that multiple agents can access:

<CodeBlocks>
  ```python Python
  from zep_crewai import ZepGraphStorage

  # Create a graph first
  graph = zep_client.graph.create(
      graph_id="company_knowledge", 
      name="Company Knowledge Graph",
      description="Shared organizational knowledge and insights."
  )

  # Create graph storage for shared knowledge
  graph_storage = ZepGraphStorage(
      client=zep_client,
      graph_id="company_knowledge",
      search_filters={"node_labels": ["Technology", "Project"]}
  )

  # Create crew with graph memory
  crew = Crew(
      agents=[your_agent],
      tasks=[your_task],
      external_memory=ExternalMemory(storage=graph_storage)
  )
  ```
</CodeBlocks>

## Tool integration

Equip your agents with Zep tools for dynamic knowledge management:

<CodeBlocks>
  ```python Python
  from zep_crewai import create_search_tool, create_add_data_tool

  # Create tools for user storage
  user_search_tool = create_search_tool(zep_client, user_id="alice_123")
  user_add_tool = create_add_data_tool(zep_client, user_id="alice_123")

  # Create tools for graph storage
  graph_search_tool = create_search_tool(zep_client, graph_id="knowledge_base")
  graph_add_tool = create_add_data_tool(zep_client, graph_id="knowledge_base")

  # Create agent with tools
  knowledge_agent = Agent(
      role="Knowledge Assistant",
      goal="Manage and retrieve information efficiently",
      tools=[user_search_tool, graph_add_tool],
      backstory="You help maintain and search through relevant knowledge",
      llm="gpt-4o-mini"
  )
  ```
</CodeBlocks>

**Tool parameters:**

Search tool:

* `query`: Natural language search query
* `limit`: Maximum results (default: 10)
* `scope`: Search scope - "edges", "nodes", "episodes", or "all"

Add data tool:

* `data`: Content to store (text, JSON, or message)
* `data_type`: Explicit type - "text", "json", or "message"

## Advanced patterns

### Structured data with ontologies

Define entity models for better knowledge organization:

<CodeBlocks>
  ```python Python
  from pydantic import Field
  from zep_cloud.external_clients.ontology import EntityModel, EntityText

  class ProjectEntity(EntityModel):
      status: EntityText = Field(description="project status")
      priority: EntityText = Field(description="priority level")
      team_size: EntityText = Field(description="team size")

  # Set graph ontology
  zep_client.graph.set_ontology(
      graph_id="projects",
      entities={"Project": ProjectEntity},
      edges={}
  )

  # Use graph with structured entities
  graph_storage = ZepGraphStorage(
      client=zep_client,
      graph_id="projects",
      search_filters={"node_labels": ["Project"]},
      facts_limit=20,
      entity_limit=5
  )
  ```
</CodeBlocks>

### Multi-agent with mixed storage

Combine user and graph storage for comprehensive memory:

<CodeBlocks>
  ```python Python
  # Personal assistant with user-specific memory
  personal_storage = ZepUserStorage(
      client=zep_client,
      user_id="alice_123",
      thread_id="conversation_456"
  )

  personal_agent = Agent(
      role="Personal Assistant",
      tools=[create_search_tool(zep_client, user_id="alice_123")],
      backstory="You know Alice's preferences and conversation history"
  )

  # Team coordinator with shared knowledge
  team_storage = ZepGraphStorage(
      client=zep_client,
      graph_id="team_knowledge"
  )

  team_agent = Agent(
      role="Team Coordinator",
      tools=[create_search_tool(zep_client, graph_id="team_knowledge")],
      backstory="You maintain the team's shared knowledge base"
  )

  # Create crews with different storage types
  personal_crew = Crew(
      agents=[personal_agent],
      tasks=[personal_task],
      external_memory=ExternalMemory(storage=personal_storage)
  )

  team_crew = Crew(
      agents=[team_agent],
      tasks=[team_task],
      external_memory=ExternalMemory(storage=team_storage)
  )
  ```
</CodeBlocks>

### Research and curation workflow

Agents can search existing knowledge and add new discoveries:

<CodeBlocks>
  ```python Python
  # Research agent with search capabilities
  researcher = Agent(
      role="Research Analyst",
      goal="Analyze information from multiple knowledge sources",
      tools=[
          create_search_tool(zep_client, user_id="alice_123"),
          create_search_tool(zep_client, graph_id="research_data")
      ],
      backstory="You analyze both personal and organizational data"
  )

  # Knowledge curator with write access
  curator = Agent(
      role="Knowledge Curator",
      goal="Maintain the organization's knowledge base",
      tools=[
          create_search_tool(zep_client, graph_id="knowledge_base"),
          create_add_data_tool(zep_client, graph_id="knowledge_base")
      ],
      backstory="You maintain and organize company knowledge"
  )

  # Task that demonstrates search and add workflow
  research_task = Task(
      description="""Research current trends in AI frameworks:
      1. Search existing knowledge about AI frameworks
      2. Identify gaps in current knowledge
      3. Add new insights to the knowledge base""",
      expected_output="Summary of research findings and new knowledge added",
      agent=curator
  )
  ```
</CodeBlocks>

## Configuration options

### ZepUserStorage parameters

* `client`: Zep client instance (required)
* `user_id`: User identifier (required)
* `thread_id`: Thread identifier (optional, enables conversation context)
* `mode`: Context mode - "summary" or "basic" (default: "summary")
* `search_filters`: Filter search results by node labels or attributes
* `facts_limit`: Maximum facts for context (default: 20)
* `entity_limit`: Maximum entities for context (default: 5)

### ZepGraphStorage parameters

* `client`: Zep client instance (required)
* `graph_id`: Graph identifier (required)
* `search_filters`: Filter by node labels (e.g., `{"node_labels": ["Technology"]}`)
* `facts_limit`: Maximum facts for context (default: 20)
* `entity_limit`: Maximum entities for context (default: 5)

## Memory routing

The integration automatically routes different data types to appropriate storage:

<CodeBlocks>
  ```python Python
  # Messages go to thread (if thread_id is configured)
  external_memory.save(
      "How can I help you today?",
      metadata={"type": "message", "role": "assistant", "name": "Helper"}
  )

  # JSON data goes to graph
  external_memory.save(
      '{"project": "Alpha", "status": "active", "budget": 50000}',
      metadata={"type": "json"}
  )

  # Text data goes to graph
  external_memory.save(
      "Project Alpha requires Python and React expertise",
      metadata={"type": "text"}
  )
  ```
</CodeBlocks>

## Complete example

Here's a complete example showing personal assistance with conversation memory:

<CodeBlocks>
  ```python Python
  import os
  import time
  from zep_cloud.client import Zep
  from zep_crewai import ZepUserStorage
  from crewai import Agent, Crew, Task, Process
  from crewai.memory.external.external_memory import ExternalMemory

  # Initialize Zep
  zep_client = Zep(api_key=os.getenv("ZEP_API_KEY"))

  # Set up user and thread
  user_id = "alice_123"
  thread_id = "project_planning"

  zep_client.user.add(user_id=user_id, first_name="Alice")
  zep_client.thread.create(user_id=user_id, thread_id=thread_id)

  # Configure user storage
  user_storage = ZepUserStorage(
      client=zep_client,
      user_id=user_id,
      thread_id=thread_id,
      mode="summary"
  )
  external_memory = ExternalMemory(storage=user_storage)

  # Store conversation context
  external_memory.save(
      "I need help planning our Q4 product roadmap with focus on mobile features",
      metadata={"type": "message", "role": "user", "name": "Alice"}
  )

  external_memory.save(
      '{"budget": 500000, "team_size": 12, "deadline": "Q4 2024"}',
      metadata={"type": "json"}
  )

  # Allow time for indexing
  time.sleep(20)

  # Create agent with memory
  planning_agent = Agent(
      role="Product Planning Assistant",
      goal="Help create data-driven product roadmaps",
      backstory="You understand Alice's preferences and project context",
      llm="gpt-4o-mini"
  )

  planning_task = Task(
      description="Create a Q4 roadmap based on Alice's requirements and context",
      expected_output="Detailed roadmap with timeline and resource allocation",
      agent=planning_agent
  )

  # Execute with automatic memory retrieval
  crew = Crew(
      agents=[planning_agent],
      tasks=[planning_task],
      process=Process.sequential,
      external_memory=external_memory
  )

  result = crew.kickoff()

  # Save results back to memory
  external_memory.save(
      str(result),
      metadata={"type": "message", "role": "assistant", "name": "Planning Agent"}
  )
  ```
</CodeBlocks>

## Best practices

### Storage selection

* **Use ZepUserStorage** for personal preferences, conversation history, and user-specific context
* **Use ZepGraphStorage** for shared knowledge, organizational data, and collaborative information

### Memory management

* **Set up ontologies** for structured data organization
* **Use search filters** to target specific node types and improve relevance
* **Combine storage types** for comprehensive memory coverage

### Tool usage

* **Bind tools** to specific users or graphs at creation time
* **Use search scope "all"** sparingly as it's more expensive
* **Add data with appropriate types** (message, json, text) for correct routing
* **Limit search results** appropriately to avoid context bloat

## Next steps

* Explore [customizing graph structure](/customizing-graph-structure) for advanced knowledge organization
* Learn about [searching the graph](/searching-the-graph) and how to search the graph
* See [code examples](https://github.com/getzep/zep/tree/main/integrations/python/zep_crewai/examples) for additional patterns


# NVIDIA NeMo Agent Toolkit

> Use Zep memory with NVIDIA NeMo Agent Toolkit for stateful LLM applications.

The NVIDIA NeMo Agent Toolkit includes a memory module that integrates with Zep to provide long-term memory capabilities for stateful LLM-based applications. This integration enables storage of conversation history, user preferences, and other persistent data across multiple interaction steps.

## Install dependencies

<CodeBlocks>
  ```bash pip
  pip install nvidia-nat-zep-cloud
  ```

  ```bash uv  
  uv add nvidia-nat-zep-cloud
  ```

  ```bash poetry
  poetry add nvidia-nat-zep-cloud
  ```
</CodeBlocks>

## Package information

* **Package**: `nvidia-nat-zep-cloud`
* **Version**: 1.2.1+
* **Python**: `>=3.11, <3.13`
* **Description**: Subpackage for Zep memory integration in NeMo Agent toolkit

## Documentation and examples

For comprehensive documentation and usage examples, refer to the official NVIDIA NeMo Agent Toolkit documentation:

* [Memory Module Documentation](https://docs.nvidia.com/nemo/agent-toolkit/1.2/store-and-retrieve/memory.html)
* [NeMo Agent Toolkit GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit)

## Example implementations

Explore example implementations in the NeMo Agent Toolkit repository:

* `examples/memory/redis`
* `examples/frameworks/semantic_kernel_demo`
* `examples/RAG/simple_rag`

## Learn more

* [NVIDIA NeMo Agent Toolkit Documentation](https://docs.nvidia.com/nemo/agent-toolkit/1.2/store-and-retrieve/memory.html)
* [PyPI Package](https://pypi.org/project/nvidia-nat-zep-cloud/)
* [GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit)


# Zep v2 to v3 migration

> Complete guide for upgrading from v2 to v3

This guide provides a comprehensive overview of migrating from Zep v2 to v3, including conceptual changes, method mappings, and functionality differences.

## Key Conceptual Changes

Zep v3 introduces several naming changes and some feature enhancements that developers familiar with v2 should understand:

### Sessions → Threads

In v2, you worked with **sessions** to manage conversation history. In v3, these are now called **threads**.

### Groups → Graphs

v2's **groups** have been replaced with **graphs** in v3. Groups represented arbitrary knowledge graphs that could hold memory for multiple users, but the name was confusing. We've renamed them to **graphs** for clarity.

### Message Role Changes

The message role structure has been updated:

* `role_type` is now called `role`
* `role` is now called `name`

### Enhanced Context Retrieval

The v3 `getUserContext` method introduces a new `mode` parameter that controls how context is returned:

* `"summary"` (default): Returns context summarized into natural language
* `"basic"`: Returns raw context similar to v2's behavior

This change allows for more flexible context retrieval based on your application's needs.

<Note>
  The naming changes above are not comprehensive. There are also function name changes, which you can find in the detailed migration table below.
</Note>

## Migration Table

<Tabs>
  <Tab title="Python">
    | v2 Method/Variable/Term       | v3 Method/Variable/Term                              |
    | ----------------------------- | ---------------------------------------------------- |
    | `memory.get(session_id)`      | `thread.get_user_context(thread_id, mode="basic")`\* |
    | `memory.add_session`          | `thread.create`                                      |
    | `memory.add`                  | `thread.add_messages`                                |
    | `memory.delete`               | `thread.delete`                                      |
    | `memory.list_sessions`        | `thread.list_all`                                    |
    | `memory.get_session_messages` | `thread.get`                                         |
    | `group.add`                   | `graph.create`                                       |
    | `group.get_all_groups`        | `graph.list_all`                                     |
    | `group.get`                   | `graph.get`                                          |
    | `group.delete`                | `graph.delete`                                       |
    | `group.update`                | `graph.update`                                       |
    | `session`                     | `thread`                                             |
    | `session_id`                  | `thread_id`                                          |
    | `group`                       | `graph`                                              |
    | `group_id`                    | `graph_id`                                           |
    | `role_type`                   | `role`                                               |
    | `role`                        | `name`                                               |

    \*`thread.get_user_context` defaults to `mode="summary"`, which makes it so that the context is summarized into natural language before being returned. Therefore, to replicate the v2 `memory.get` method, `mode` must be set to `"basic"`.
  </Tab>

  <Tab title="TypeScript">
    | v2 Method/Variable/Term     | v3 Method/Variable/Term                                |
    | --------------------------- | ------------------------------------------------------ |
    | `memory.get(sessionId)`     | `thread.getUserContext(threadId, { mode: "basic" })`\* |
    | `memory.addSession`         | `thread.create`                                        |
    | `memory.add`                | `thread.addMessages`                                   |
    | `memory.delete`             | `thread.delete`                                        |
    | `memory.listSessions`       | `thread.listAll`                                       |
    | `memory.getSessionMessages` | `thread.get`                                           |
    | `group.add`                 | `graph.create`                                         |
    | `group.getAllGroups`        | `graph.listAll`                                        |
    | `group.get`                 | `graph.get`                                            |
    | `group.delete`              | `graph.delete`                                         |
    | `group.update`              | `graph.update`                                         |
    | `session`                   | `thread`                                               |
    | `sessionId`                 | `threadId`                                             |
    | `group`                     | `graph`                                                |
    | `groupId`                   | `graphId`                                              |
    | `roleType`                  | `role`                                                 |
    | `role`                      | `name`                                                 |

    \*`thread.getUserContext` defaults to `mode="summary"`, which makes it so that the context is summarized into natural language before being returned. Therefore, to replicate the v2 `memory.get` method, `mode` must be set to `"basic"`.
  </Tab>

  <Tab title="Go">
    | v2 Method/Variable/Term     | v3 Method/Variable/Term                                                           |
    | --------------------------- | --------------------------------------------------------------------------------- |
    | `Memory.Get(sessionId)`     | `Thread.GetUserContext(threadId, &v3.ThreadGetUserContextRequest{Mode: &mode})`\* |
    | `Memory.AddSession`         | `Thread.Create`                                                                   |
    | `Memory.Add`                | `Thread.AddMessages`                                                              |
    | `Memory.Delete`             | `Thread.Delete`                                                                   |
    | `Memory.ListSessions`       | `Thread.ListAll`                                                                  |
    | `Memory.GetSessionMessages` | `Thread.Get`                                                                      |
    | `Group.Add`                 | `Graph.Create`                                                                    |
    | `Group.GetAllGroups`        | `Graph.ListAll`                                                                   |
    | `Group.Get`                 | `Graph.Get`                                                                       |
    | `Group.Delete`              | `Graph.Delete`                                                                    |
    | `Group.Update`              | `Graph.Update`                                                                    |
    | `session`                   | `thread`                                                                          |
    | `SessionID`                 | `ThreadID`                                                                        |
    | `group`                     | `graph`                                                                           |
    | `GroupID`                   | `GraphID`                                                                         |
    | `RoleType`                  | `Role`                                                                            |
    | `Role`                      | `Name`                                                                            |

    \*`Thread.GetUserContext` defaults to `mode="summary"`, which makes it so that the context is summarized into natural language before being returned. Therefore, to replicate the v2 `Memory.Get` method, `mode` must be set to `"basic"`.
  </Tab>
</Tabs>


# Mem0 Migration

> How to migrate from Mem0 to Zep

Zep is a memory layer for AI agents that unifies chat and business data into a dynamic [temporal knowledge graph](/v3/concepts#the-knowledge-graph) for each user. It tracks entities, relationships, and facts as they evolve, enabling you to build prompts with only the most relevant information—reducing hallucinations, improving recall, and lowering LLM costs.

Zep provides high-level APIs like `thread.get_user_context` and deep search with `graph.search`, supports custom entity/edge types, hybrid search, and granular graph updates. Mem0, by comparison, offers basic add/get/search APIs and an optional graph, but lacks built-in data unification, ontology customization, temporal fact management, and fine-grained graph control.

<Note>
  Got lots of data to migrate? [Contact us](mailto:sales@getzep.com) for a discount and increased API limits.
</Note>

## Zep's memory model in one minute

### Unified customer record

* Messages sent via [`thread.add_messages`](memory#adding-memory) go straight into the user's knowledge graph; business objects (JSON, docs, e-mails, CRM rows) flow in through [`graph.add`](/v3/adding-data-to-the-graph). Zep automatically deduplicates entities and keeps every fact's *valid* and *invalid* dates so you always see the latest truth.

### Domain-depth ontology

* You can define Pydantic-style **[custom entity and edge classes](/v3/customizing-graph-structure)** so the graph speaks your business language (Accounts, Policies, Devices, etc.).

### Temporal facts

* Every edge stores when a fact was created, became valid, was invalidated, and (optionally) expired.

### Hybrid & granular search

* [`graph.search`](/v3/searching-the-graph) supports [hybrid BM25 + semantic queries, graph search](/v3/searching-the-graph), with pluggable rerankers (RRF, MMR, cross-encoder) and can target nodes, edges, episodes, or everything at once.

## How Zep differs from Mem0

| Capability                          | **Zep**                                                                                                                                                        | **Mem0**                                                                                                   |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Business-data ingestion**         | Native via [`graph.add`](/v3/adding-data-to-the-graph) (JSON or text); [business facts merge with user graph](/v3/concepts#business-data-vs-chat-message-data) | No direct ingestion API; business data must be rewritten as "memories" or loaded into external graph store |
| **Knowledge-graph storage**         | Built-in [temporal graph](/v3/concepts#managing-changes-in-facts-over-time); zero infra for developers                                                         | Optional "Graph Memory" layer that *requires* Neo4j/Memgraph and extra config                              |
| **Custom ontology**                 | First-class [entity/edge type system](/v3/customizing-graph-structure)                                                                                         | Not exposed; relies on generic nodes/relationships                                                         |
| **Fact life-cycle (valid/invalid)** | [Automatic and queryable](/v3/concepts#managing-changes-in-facts-over-time)                                                                                    | Not documented / not supported                                                                             |
| **User summary customization**      | [User summary instructions](users.mdx#user-summary-instructions) customize entity summaries per user                                                           | Not available                                                                                              |
| **Search**                          | [Hybrid vector + graph search](/v3/searching-the-graph) with multiple rerankers                                                                                | Vector search with filters; basic Cypher queries if graph layer enabled                                    |
| **Graph CRUD**                      | Full [node/edge CRUD](/v3/deleting-data-from-the-graph) & [bulk episode ingest](/v3/adding-data-to-the-graph)                                                  | Add/Delete memories; no low-level edge ops                                                                 |
| **Context block**                   | [Auto-generated, temporal, prompt-ready](/retrieving-memory#retrieving-zeps-context-block)                                                                     | You assemble snippets manually from `search` output                                                        |
| **LLM integration**                 | Returns [ready-made `memory.context`](/retrieving-memory#retrieving-zeps-context-block); easily integrates with agentic tools                                  | Returns raw strings you must format                                                                        |

## SDK support

Zep offers Python, TypeScript, and Go SDKs. See [Installation Instructions](/v3/quickstart) for more details.

## Migrating your code

### Basic flows

| **What you do in Mem0**                                           | **Do this in Zep**                                                                                                                                                                            |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `client.add(messages, user_id=ID)` → stores conversation snippets | `zep.thread.add_messages(thread_id, messages=[...])` – keeps chat sequence **and** updates graph                                                                                              |
| `client.add("json...", user_id=ID)` (not really supported)        | `zep.graph.add(user_id, data=<JSON>)` – drop raw business records right in                                                                                                                    |
| `client.search(query, user_id=ID)` – vector+filter search         | *Easy path*: `zep.thread.get_user_context(thread_id)` returns the `memory.context` + recent messages<br />*Deep path*: `zep.graph.search(user_id, query, reranker="rrf")`                     |
| `client.get_all(user_id=ID)` – list memories                      | `zep.graph.search(user_id, '')` or iterate `graph.get_nodes/edges` for full dump                                                                                                              |
| `client.update(memory_id, ...)` / `delete`                        | `zep.graph.edge.delete(uuid_="edge_uuid")` or `zep.graph.episode.delete(uuid_="episode_uuid")` for granular edits. Facts may not be updated directly; new data automatically invalidates old. |

### Practical tips

* **Thread mapping:** Map Mem0's `user_id` → Zep `user_id`, and create `thread_id` per conversation thread.
* **Business objects:** Convert external records to JSON or text and feed them through `graph.add`; Zep will handle entity linking automatically.
* **Prompting:** Replace your custom "summary builder" with the `memory.context` string; it already embeds temporal ranges and entity summaries.
* **Summary customization:** Use [user summary instructions](users.mdx#user-summary-instructions) to guide how Zep generates entity summaries for each user, tailoring the context to your specific use case.
* **Search tuning:** Start with the default `rrf` reranker; switch to `mmr`, `node_distance`, `cross_encoder`, or `episode_mentions` when you need speed or precision tweaks.

## Side-by-side SDK cheat-sheet

| **Operation**            | Mem0 Method (Python)           | Zep Method (Python)                                  | Notes                                         |
| ------------------------ | ------------------------------ | ---------------------------------------------------- | --------------------------------------------- |
| Add chat messages        | `m.add(messages, user_id=...)` | `zep.thread.add_messages(thread_id, messages)`       | Zep expects *ordered* AI + user msgs per turn |
| Add business record      | *n/a* (work-around)            | `zep.graph.add(user_id, data)`                       | Direct ingestion of JSON/text                 |
| Retrieve context         | `m.search(query,... )`         | `zep.thread.get_user_context(thread_id)`             | Zep auto-selects facts; no prompt assembly    |
| Semantic / hybrid search | `m.search(query, ...)`         | `zep.graph.search(..., reranker=...)`                | Multiple rerankers, node/edge scopes          |
| List memories            | `m.get_all(user_id)`           | `zep.graph.search(user_id, '')`                      | Empty query lists entire graph                |
| Update fact              | `m.update(id, ...)`            | *Not directly supported* - add new data to supersede | Facts are temporal; new data invalidates old  |
| Delete fact              | `m.delete(id)`                 | `zep.graph.edge.delete(uuid_="edge_uuid")`           | Episode deletion removes associated edges     |
| Customize user summaries | *not supported*                | `zep.user.add_user_summary_instructions()`           | Up to 5 custom instructions per user          |

## Where to dig deeper

* [**Quickstart**](/v3/quickstart)
* [**Graph Search guide**](/v3/searching-the-graph)
* [**Entity / Edge customization**](/v3/customizing-graph-structure)
* [**User summary instructions**](users.mdx#user-summary-instructions)
* **Graph CRUD**: [Reading from the Graph](/v3/reading-data-from-the-graph) | [Adding to the Graph](/v3/adding-data-to-the-graph) | [Deleting from the Graph](/v3/deleting-data-from-the-graph)

For any questions, ping the Zep Discord or contact your account manager. Happy migrating!


# FAQ

## Is there a free version of Zep Cloud?

Yes - Zep offers a free tier. See [Pricing](https://www.getzep.com/pricing) for more information.

## What is the API URL for Zep Cloud?

The API URL for Zep Cloud is `https://api.getzep.com`. Note that you do not need to specify the API URL when using the Cloud SDKs.
If a service requests the Zep URL, it is possible it's only compatible with the Zep Community Edition service.

## Does Zep Cloud support multiple spoken languages?

We have official multilingual support on our roadmap, enabling the creation of graphs in a user's own language. Currently, graphs are not explicitly created in the user's language. However, Zep should work well today with any language, provided you're using a multilingual LLM and your own prompts explicitly state that responses to the user should be in their language.

## I can't join my company project, because I have already created an account. What should I do?

You will need to delete your account and then accept the invitation from your company.

## How well does Zep scale?

Zep supports many millions of users per account and retrieval performance is not impacted by dataset size. Retrieving/searching the graph scales in near constant time with the size of the graph. Zep's Metered Billing Plan is subject to rate limits on both API requests and processing concurrency.

## Can I use Zep to replace RAG over static documents?

Zep can be used for retrieval for static documents just like RAG or GraphRAG, although this is not what Zep was designed for. Zep was designed for dynamic, changing data, which RAG and GraphRAG were not designed to do.

## How does the retrieval work for thread.get\_user\_context under the hood?

`thread.get_user_context` does a `graph.search` on nodes, edges, and episodes using the [MMR reranker](/searching-the-graph#mmr-maximal-marginal-relevance). It uses the most recent message as the search query. In addition, it does a `BFS` on the 4 most recent episodes (so it finds all nodes, edges, and episodes created by the 4 most recent episodes and all nodes and edges 2 connections deep).

All of those search results are then used as candidate results which are reranked by the [MMR reranker](/searching-the-graph#mmr-maximal-marginal-relevance). The MMR reranker will compare each search result with the most recent 4 messages to determine how relevant that result is to the current conversation.

## I am seeing information duplicated between different node summaries. Is this normal?

This is a normal and intended feature of Zep. Node summaries are intended to be standalone summaries of the node, which often means describing the relationships that that node has to other nodes. Those same relationships are likely to appear in the summaries of those other nodes.

## Should I use nodes, edges, or episodes when searching the graph and creating a context string?

You can use any combination of nodes, edges, and episodes. There is not a one size fits all solution, and you will likely need to experiment with different approaches to get the best performance for your use case.

## Where is the data stored? What if my client needs it stored in the EU?

We only offer US data residency currently.

## Can I self host Zep? What happened to Zep Community Edition?

Zep Community Edition, which allows you to host Zep locally, is deprecated and no longer supported. See our [announcement post here](https://blog.getzep.com/announcing-a-new-direction-for-zeps-open-source-strategy/).

The alternatives we offer include:

* [Zep Cloud](https://www.getzep.com/): Our hosted solution
* [Graphiti](https://github.com/getzep/graphiti): The open source knowledge graph that powers Zep Cloud

## How do I get Zep to work with n8n?

The Zep n8n integration is no longer supported. We recommend using Zep's SDKs directly instead, see [here](https://help.getzep.com/quickstart).

## Why aren't my episodes processing?

Sometimes episodes may appear to not be processing when they are actually processing slowly. Typically, episodes process in less than 10 seconds, but occasionally they can take a few minutes. Additionally, if you add multiple episodes to a single graph simultaneously, they must process sequentially, which can take time if there are many episodes.

Please confirm the following:

* Are you adding multiple episodes to a single graph all at once? If so, how many? Multiply the number of episodes you are adding to a single graph by 10 seconds for an average case time estimate, or by a few minutes for a worst case time estimate.
* If the above is the case, within the web app, find the most recently processed episode and then look at the next unprocessed episode. Confirm whether that episode remains unprocessed after waiting at least 3-4 minutes (the worst-case processing time). If you see this episode process after some waiting, then your episodes are processing, it just may take some time.
* If neither of the above applies, reach out to our support team on [Discord](https://discord.com/invite/W8Kw6bsgXQ) and let them know what you are seeing.

## How do I get the playground to work with my own data?

The playground is not meant to work with custom data. Instead the playground showcases Zep's functionality with demo data. In order to create a graph with your own custom data, you need to use the Zep SDKs. See our [Quickstart](/quickstart).

## How do I add messages or create memory for a group chat with multiple people?

In order to add messages for a group chat to a Zep knowledge graph, you need to use the `graph.add` method with `type = message` as opposed to `thread.add_messages` (which uses `graph.add` with `type = message` under the hood). You need to use the `graph.add` method so that you are not associating the chat with a single user. Then, to retrieve memory, you need to search the graph and assemble a custom context block ([see cookbook example](https://help.getzep.com/cookbook/customize-your-context-block)).

## What's the difference between Zep and Graphiti?

See our detailed comparison: [Zep vs Graphiti](/zep-vs-graphiti)


# Zep vs Graphiti

> Understanding the key differences between Zep and Graphiti

| Aspect                             | Zep                                                                                           | Graphiti                                                          |
| ---------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **What they are**                  | Fully managed platform for context engineering and AI memory                                  | Open-source graph framework                                       |
| **User & conversation management** | Built-in users, threads, and message storage                                                  | Build your own                                                    |
| **Retrieval & performance**        | Pre-configured, production-ready retrieval with sub-200ms performance at scale                | Custom implementation required; performance depends on your setup |
| **Developer tools**                | Dashboard with graph visualization, debug logs, API logs; SDKs for Python, TypeScript, and Go | Build your own tools                                              |
| **Enterprise features**            | SLAs, support, security guarantees                                                            | Self-managed                                                      |
| **Deployment**                     | Fully managed or in your cloud                                                                | Self-hosted only                                                  |

## When to choose which

**Choose Zep** if you want a turnkey, enterprise-grade platform with security, performance, and support baked in.

**Choose Graphiti** if you want a flexible OSS core and you're comfortable building/operating the surrounding system.


# Get threads

GET https://api.getzep.com/api/v2/threads

Returns all threads.

Reference: https://help.getzep.com/sdk-reference/thread/list-all

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get threads
  version: endpoint_thread.list_all
paths:
  /threads:
    get:
      operationId: list-all
      summary: Get threads
      description: Returns all threads.
      tags:
        - - subpackage_thread
      parameters:
        - name: page_number
          in: query
          description: Page number for pagination, starting from 1
          required: false
          schema:
            type: integer
        - name: page_size
          in: query
          description: Number of threads to retrieve per page.
          required: false
          schema:
            type: integer
        - name: order_by
          in: query
          description: >-
            Field to order the results by: created_at, updated_at, user_id,
            thread_id.
          required: false
          schema:
            type: string
        - name: asc
          in: query
          description: 'Order direction: true for ascending, false for descending.'
          required: false
          schema:
            type: boolean
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: List of threads
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:ThreadListResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:Thread:
      type: object
      properties:
        created_at:
          type: string
        project_uuid:
          type: string
        thread_id:
          type: string
        user_id:
          type: string
        uuid:
          type: string
    type_:ThreadListResponse:
      type: object
      properties:
        response_count:
          type: integer
        threads:
          type: array
          items:
            $ref: '#/components/schemas/type_:Thread'
        total_count:
          type: integer

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.list_all()

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.listAll();

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.ListAll(
	context.TODO(),
	&v3.ThreadListAllRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/threads")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/threads")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/threads', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/threads");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/threads")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Start a new thread.

POST https://api.getzep.com/api/v2/threads
Content-Type: application/json

Start a new thread.

Reference: https://help.getzep.com/sdk-reference/thread/create

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Start a new thread.
  version: endpoint_thread.create
paths:
  /threads:
    post:
      operationId: create
      summary: Start a new thread.
      description: Start a new thread.
      tags:
        - - subpackage_thread
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '201':
          description: The thread object.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:Thread'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                thread_id:
                  type: string
                user_id:
                  type: string
              required:
                - thread_id
                - user_id
components:
  schemas:
    type_:Thread:
      type: object
      properties:
        created_at:
          type: string
        project_uuid:
          type: string
        thread_id:
          type: string
        user_id:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.create(
    thread_id="thread_id",
    user_id="user_id",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.create({
    threadId: "thread_id",
    userId: "user_id"
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.Create(
	context.TODO(),
	&v3.CreateThreadRequest{
		ThreadID: "thread_id",
		UserID:   "user_id",
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/threads")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"thread_id\": \"thread_id\",\n  \"user_id\": \"user_id\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/threads")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"thread_id\": \"thread_id\",\n  \"user_id\": \"user_id\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/threads', [
  'body' => '{
  "thread_id": "thread_id",
  "user_id": "user_id"
}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/threads");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"thread_id\": \"thread_id\",\n  \"user_id\": \"user_id\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = [
  "thread_id": "thread_id",
  "user_id": "user_id"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/threads")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Delete thread

DELETE https://api.getzep.com/api/v2/threads/{threadId}

Deletes a thread.

Reference: https://help.getzep.com/sdk-reference/thread/delete

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete thread
  version: endpoint_thread.delete
paths:
  /threads/{threadId}:
    delete:
      operationId: delete
      summary: Delete thread
      description: Deletes a thread.
      tags:
        - - subpackage_thread
      parameters:
        - name: threadId
          in: path
          description: The ID of the thread for which memory should be deleted.
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.delete(
    thread_id="threadId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.delete("threadId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.Delete(
	context.TODO(),
	"threadId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/threads/threadId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.getzep.com/api/v2/threads/threadId")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.getzep.com/api/v2/threads/threadId', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/threads/threadId");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/threads/threadId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get user context

GET https://api.getzep.com/api/v2/threads/{threadId}/context

Returns most relevant context from the user graph (including memory from any/all past threads) based on the content of the past few messages of the given thread.

Reference: https://help.getzep.com/sdk-reference/thread/get-user-context

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get user context
  version: endpoint_thread.get_user_context
paths:
  /threads/{threadId}/context:
    get:
      operationId: get-user-context
      summary: Get user context
      description: >-
        Returns most relevant context from the user graph (including memory from
        any/all past threads) based on the content of the past few messages of
        the given thread.
      tags:
        - - subpackage_thread
      parameters:
        - name: threadId
          in: path
          description: The ID of the current thread (for which context is being retrieved).
          required: true
          schema:
            type: string
        - name: minRating
          in: query
          description: The minimum rating by which to filter relevant facts.
          required: false
          schema:
            type: number
            format: double
        - name: mode
          in: query
          description: Defaults to summary mode. Use basic for lower latency
          required: false
          schema:
            $ref: '#/components/schemas/type_thread:ThreadGetUserContextRequestMode'
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:ThreadContextResponse'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_thread:ThreadGetUserContextRequestMode:
      type: string
      enum:
        - value: basic
        - value: summary
    type_:ThreadContextResponse:
      type: object
      properties:
        context:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.get_user_context(
    thread_id="threadId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.getUserContext("threadId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.GetUserContext(
	context.TODO(),
	"threadId",
	&v3.ThreadGetUserContextRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/threads/threadId/context")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/threads/threadId/context")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/threads/threadId/context', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/threads/threadId/context");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/threads/threadId/context")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get messages of a thread

GET https://api.getzep.com/api/v2/threads/{threadId}/messages

Returns messages for a thread.

Reference: https://help.getzep.com/sdk-reference/thread/get

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get messages of a thread
  version: endpoint_thread.get
paths:
  /threads/{threadId}/messages:
    get:
      operationId: get
      summary: Get messages of a thread
      description: Returns messages for a thread.
      tags:
        - - subpackage_thread
      parameters:
        - name: threadId
          in: path
          description: Thread ID
          required: true
          schema:
            type: string
        - name: limit
          in: query
          description: Limit the number of results returned
          required: false
          schema:
            type: integer
        - name: cursor
          in: query
          description: Cursor for pagination
          required: false
          schema:
            type: integer
        - name: lastn
          in: query
          description: >-
            Number of most recent messages to return (overrides limit and
            cursor)
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:MessageListResponse'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:Message:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        name:
          type: string
        processed:
          type: boolean
        role:
          $ref: '#/components/schemas/type_:RoleType'
        uuid:
          type: string
      required:
        - content
        - role
    type_:MessageListResponse:
      type: object
      properties:
        messages:
          type: array
          items:
            $ref: '#/components/schemas/type_:Message'
        row_count:
          type: integer
        total_count:
          type: integer

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.get(
    thread_id="threadId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.get("threadId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.Get(
	context.TODO(),
	"threadId",
	&v3.ThreadGetRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/threads/threadId/messages")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/threads/threadId/messages")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/threads/threadId/messages');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/threads/threadId/messages");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/threads/threadId/messages")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Add messages to a thread

POST https://api.getzep.com/api/v2/threads/{threadId}/messages
Content-Type: application/json

Add messages to a thread.

Reference: https://help.getzep.com/sdk-reference/thread/add-messages

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Add messages to a thread
  version: endpoint_thread.add_messages
paths:
  /threads/{threadId}/messages:
    post:
      operationId: add-messages
      summary: Add messages to a thread
      description: Add messages to a thread.
      tags:
        - - subpackage_thread
      parameters:
        - name: threadId
          in: path
          description: The ID of the thread to which messages should be added.
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: >-
            An object, optionally containing user context retrieved for the last
            thread message
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:AddThreadMessagesResponse'
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/type_:AddThreadMessagesRequest'
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:Message:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        name:
          type: string
        processed:
          type: boolean
        role:
          $ref: '#/components/schemas/type_:RoleType'
        uuid:
          type: string
      required:
        - content
        - role
    type_:AddThreadMessagesRequest:
      type: object
      properties:
        ignore_roles:
          type: array
          items:
            $ref: '#/components/schemas/type_:RoleType'
        messages:
          type: array
          items:
            $ref: '#/components/schemas/type_:Message'
        return_context:
          type: boolean
      required:
        - messages
    type_:AddThreadMessagesResponse:
      type: object
      properties:
        context:
          type: string
        message_uuids:
          type: array
          items:
            type: string

```

## SDK Code Examples

```python
from zep_cloud import Message, Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.add_messages(
    thread_id="threadId",
    messages=[
        Message(
            content="content",
            role="norole",
        )
    ],
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.addMessages("threadId", {
    messages: [{
            content: "content",
            role: "norole"
        }]
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.AddMessages(
	context.TODO(),
	"threadId",
	&v3.AddThreadMessagesRequest{
		Messages: []*v3.Message{
			&v3.Message{
				Content: "content",
				Role:    v3.RoleTypeNoRole,
			},
		},
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/threads/threadId/messages")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"messages\": [\n    {\n      \"content\": \"content\",\n      \"role\": \"norole\"\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/threads/threadId/messages")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"messages\": [\n    {\n      \"content\": \"content\",\n      \"role\": \"norole\"\n    }\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/threads/threadId/messages', [
  'body' => '{
  "messages": [
    {
      "content": "content",
      "role": "norole"
    }
  ]
}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/threads/threadId/messages");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"messages\": [\n    {\n      \"content\": \"content\",\n      \"role\": \"norole\"\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["messages": [
    [
      "content": "content",
      "role": "norole"
    ]
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/threads/threadId/messages")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Add messages to a thread in batch

POST https://api.getzep.com/api/v2/threads/{threadId}/messages-batch
Content-Type: application/json

Add messages to a thread in batch mode. This will process messages concurrently, which is useful for data migrations.

Reference: https://help.getzep.com/sdk-reference/thread/add-messages-batch

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Add messages to a thread in batch
  version: endpoint_thread.add_messages_batch
paths:
  /threads/{threadId}/messages-batch:
    post:
      operationId: add-messages-batch
      summary: Add messages to a thread in batch
      description: >-
        Add messages to a thread in batch mode. This will process messages
        concurrently, which is useful for data migrations.
      tags:
        - - subpackage_thread
      parameters:
        - name: threadId
          in: path
          description: The ID of the thread to which messages should be added.
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: >-
            An object, optionally containing user context retrieved for the last
            thread message
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:AddThreadMessagesResponse'
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/type_:AddThreadMessagesRequest'
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:Message:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        name:
          type: string
        processed:
          type: boolean
        role:
          $ref: '#/components/schemas/type_:RoleType'
        uuid:
          type: string
      required:
        - content
        - role
    type_:AddThreadMessagesRequest:
      type: object
      properties:
        ignore_roles:
          type: array
          items:
            $ref: '#/components/schemas/type_:RoleType'
        messages:
          type: array
          items:
            $ref: '#/components/schemas/type_:Message'
        return_context:
          type: boolean
      required:
        - messages
    type_:AddThreadMessagesResponse:
      type: object
      properties:
        context:
          type: string
        message_uuids:
          type: array
          items:
            type: string

```

## SDK Code Examples

```python
from zep_cloud import Message, Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.add_messages_batch(
    thread_id="threadId",
    messages=[
        Message(
            content="content",
            role="norole",
        )
    ],
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.addMessagesBatch("threadId", {
    messages: [{
            content: "content",
            role: "norole"
        }]
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.AddMessagesBatch(
	context.TODO(),
	"threadId",
	&v3.AddThreadMessagesRequest{
		Messages: []*v3.Message{
			&v3.Message{
				Content: "content",
				Role:    v3.RoleTypeNoRole,
			},
		},
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/threads/threadId/messages-batch")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"messages\": [\n    {\n      \"content\": \"content\",\n      \"role\": \"norole\"\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/threads/threadId/messages-batch")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"messages\": [\n    {\n      \"content\": \"content\",\n      \"role\": \"norole\"\n    }\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/threads/threadId/messages-batch', [
  'body' => '{
  "messages": [
    {
      "content": "content",
      "role": "norole"
    }
  ]
}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/threads/threadId/messages-batch");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"messages\": [\n    {\n      \"content\": \"content\",\n      \"role\": \"norole\"\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["messages": [
    [
      "content": "content",
      "role": "norole"
    ]
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/threads/threadId/messages-batch")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Updates a message.

PATCH https://api.getzep.com/api/v2/messages/{messageUUID}
Content-Type: application/json

Updates a message.

Reference: https://help.getzep.com/sdk-reference/thread/message/update

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Updates a message.
  version: endpoint_thread/message.update
paths:
  /messages/{messageUUID}:
    patch:
      operationId: update
      summary: Updates a message.
      description: Updates a message.
      tags:
        - - subpackage_thread
          - subpackage_thread/message
      parameters:
        - name: messageUUID
          in: path
          description: The UUID of the message.
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The updated message.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:Message'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                metadata:
                  type: object
                  additionalProperties:
                    description: Any type
              required:
                - metadata
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:Message:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        name:
          type: string
        processed:
          type: boolean
        role:
          $ref: '#/components/schemas/type_:RoleType'
        uuid:
          type: string
      required:
        - content
        - role

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.message.update(
    message_uuid="messageUUID",
    metadata={"key": "value"},
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.message.update("messageUUID", {
    metadata: {
        "key": "value"
    }
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	thread "github.com/getzep/zep-go/v3/thread"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Thread.Message.Update(
	context.TODO(),
	"messageUUID",
	&thread.ThreadMessageUpdate{
		Metadata: map[string]interface{}{
			"key": "value",
		},
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/messages/messageUUID")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"metadata\": {\n    \"key\": \"value\"\n  }\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.patch("https://api.getzep.com/api/v2/messages/messageUUID")
  .header("Content-Type", "application/json")
  .body("{\n  \"metadata\": {\n    \"key\": \"value\"\n  }\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('PATCH', 'https://api.getzep.com/api/v2/messages/messageUUID', [
  'body' => '{
  "metadata": {
    "key": "value"
  }
}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/messages/messageUUID");
var request = new RestRequest(Method.PATCH);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"metadata\": {\n    \"key\": \"value\"\n  }\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = ["metadata": ["key": "value"]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/messages/messageUUID")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PATCH"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# List User Instructions

GET https://api.getzep.com/api/v2/user-summary-instructions

Lists all user summary instructions for a project, user.

Reference: https://help.getzep.com/sdk-reference/user/list-user-summary-instructions

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List User Instructions
  version: endpoint_user.list_user_summary_instructions
paths:
  /user-summary-instructions:
    get:
      operationId: list-user-summary-instructions
      summary: List User Instructions
      description: Lists all user summary instructions for a project, user.
      tags:
        - - subpackage_user
      parameters:
        - name: user_id
          in: query
          description: User ID to get user-specific instructions
          required: false
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The list of instructions.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:ListUserInstructionsResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:UserInstruction:
      type: object
      properties:
        name:
          type: string
        text:
          type: string
      required:
        - name
        - text
    type_:ListUserInstructionsResponse:
      type: object
      properties:
        instructions:
          type: array
          items:
            $ref: '#/components/schemas/type_:UserInstruction'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.list_user_summary_instructions()

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.listUserSummaryInstructions();

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.ListUserSummaryInstructions(
	context.TODO(),
	&v3.UserListUserSummaryInstructionsRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/user-summary-instructions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/user-summary-instructions")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/user-summary-instructions', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/user-summary-instructions");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/user-summary-instructions")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Add User Instructions

POST https://api.getzep.com/api/v2/user-summary-instructions
Content-Type: application/json

Adds new summary instructions for users graphs without removing existing ones. If user_ids is empty, adds to project-wide default instructions.

Reference: https://help.getzep.com/sdk-reference/user/add-user-summary-instructions

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Add User Instructions
  version: endpoint_user.add_user_summary_instructions
paths:
  /user-summary-instructions:
    post:
      operationId: add-user-summary-instructions
      summary: Add User Instructions
      description: >-
        Adds new summary instructions for users graphs without removing existing
        ones. If user_ids is empty, adds to project-wide default instructions.
      tags:
        - - subpackage_user
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Instructions added successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                instructions:
                  type: array
                  items:
                    $ref: '#/components/schemas/type_:UserInstruction'
                user_ids:
                  type: array
                  items:
                    type: string
              required:
                - instructions
components:
  schemas:
    type_:UserInstruction:
      type: object
      properties:
        name:
          type: string
        text:
          type: string
      required:
        - name
        - text
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import UserInstruction, Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.add_user_summary_instructions(
    instructions=[
        UserInstruction(
            name="name",
            text="text",
        )
    ],
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.addUserSummaryInstructions({
    instructions: [{
            name: "name",
            text: "text"
        }]
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.AddUserSummaryInstructions(
	context.TODO(),
	&v3.AddUserInstructionsRequest{
		Instructions: []*v3.UserInstruction{
			&v3.UserInstruction{
				Name: "name",
				Text: "text",
			},
		},
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/user-summary-instructions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"instructions\": [\n    {\n      \"name\": \"name\",\n      \"text\": \"text\"\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/user-summary-instructions")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"instructions\": [\n    {\n      \"name\": \"name\",\n      \"text\": \"text\"\n    }\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/user-summary-instructions', [
  'body' => '{
  "instructions": [
    {
      "name": "name",
      "text": "text"
    }
  ]
}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/user-summary-instructions");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"instructions\": [\n    {\n      \"name\": \"name\",\n      \"text\": \"text\"\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["instructions": [
    [
      "name": "name",
      "text": "text"
    ]
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/user-summary-instructions")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Delete User Instructions

DELETE https://api.getzep.com/api/v2/user-summary-instructions
Content-Type: application/json

Deletes user summary/instructions for users or project wide defaults.

Reference: https://help.getzep.com/sdk-reference/user/delete-user-summary-instructions

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete User Instructions
  version: endpoint_user.delete_user_summary_instructions
paths:
  /user-summary-instructions:
    delete:
      operationId: delete-user-summary-instructions
      summary: Delete User Instructions
      description: Deletes user summary/instructions for users or project wide defaults.
      tags:
        - - subpackage_user
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Instructions deleted successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                instruction_names:
                  type: array
                  items:
                    type: string
                user_ids:
                  type: array
                  items:
                    type: string
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.delete_user_summary_instructions()

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.deleteUserSummaryInstructions();

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.DeleteUserSummaryInstructions(
	context.TODO(),
	&v3.DeleteUserInstructionsRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/user-summary-instructions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.getzep.com/api/v2/user-summary-instructions")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.getzep.com/api/v2/user-summary-instructions', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/user-summary-instructions");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/user-summary-instructions")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Add User

POST https://api.getzep.com/api/v2/users
Content-Type: application/json

Adds a user.

Reference: https://help.getzep.com/sdk-reference/user/add

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Add User
  version: endpoint_user.add
paths:
  /users:
    post:
      operationId: add
      summary: Add User
      description: Adds a user.
      tags:
        - - subpackage_user
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '201':
          description: The user that was added.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:User'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                disable_default_ontology:
                  type: boolean
                email:
                  type: string
                fact_rating_instruction:
                  $ref: '#/components/schemas/type_:FactRatingInstruction'
                first_name:
                  type: string
                last_name:
                  type: string
                metadata:
                  type: object
                  additionalProperties:
                    description: Any type
                user_id:
                  type: string
              required:
                - user_id
components:
  schemas:
    type_:FactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:FactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:FactRatingExamples'
        instruction:
          type: string
    type_:ModelsFactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:ModelsFactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:ModelsFactRatingExamples'
        instruction:
          type: string
    type_:User:
      type: object
      properties:
        created_at:
          type: string
        deleted_at:
          type: string
        disable_default_ontology:
          type: boolean
        email:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:ModelsFactRatingInstruction'
        first_name:
          type: string
        id:
          type: integer
        last_name:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        project_uuid:
          type: string
        session_count:
          type: integer
        updated_at:
          type: string
        user_id:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.add(
    user_id="user_id",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.add({
    userId: "user_id"
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.Add(
	context.TODO(),
	&v3.CreateUserRequest{
		UserID: "user_id",
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"user_id\": \"user_id\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/users")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"user_id\": \"user_id\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/users', [
  'body' => '{
  "user_id": "user_id"
}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"user_id\": \"user_id\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["user_id": "user_id"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Users

GET https://api.getzep.com/api/v2/users-ordered

Returns all users.

Reference: https://help.getzep.com/sdk-reference/user/list-ordered

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Users
  version: endpoint_user.listOrdered
paths:
  /users-ordered:
    get:
      operationId: list-ordered
      summary: Get Users
      description: Returns all users.
      tags:
        - - subpackage_user
      parameters:
        - name: pageNumber
          in: query
          description: Page number for pagination, starting from 1
          required: false
          schema:
            type: integer
        - name: pageSize
          in: query
          description: Number of users to retrieve per page
          required: false
          schema:
            type: integer
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successfully retrieved list of users
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:UserListResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:ModelsFactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:ModelsFactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:ModelsFactRatingExamples'
        instruction:
          type: string
    type_:User:
      type: object
      properties:
        created_at:
          type: string
        deleted_at:
          type: string
        disable_default_ontology:
          type: boolean
        email:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:ModelsFactRatingInstruction'
        first_name:
          type: string
        id:
          type: integer
        last_name:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        project_uuid:
          type: string
        session_count:
          type: integer
        updated_at:
          type: string
        user_id:
          type: string
        uuid:
          type: string
    type_:UserListResponse:
      type: object
      properties:
        row_count:
          type: integer
        total_count:
          type: integer
        users:
          type: array
          items:
            $ref: '#/components/schemas/type_:User'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.list_ordered()

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.listOrdered();

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.ListOrdered(
	context.TODO(),
	&v3.UserListOrderedRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users-ordered")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/users-ordered")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/users-ordered', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users-ordered");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users-ordered")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get User

GET https://api.getzep.com/api/v2/users/{userId}

Returns a user.

Reference: https://help.getzep.com/sdk-reference/user/get

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get User
  version: endpoint_user.get
paths:
  /users/{userId}:
    get:
      operationId: get
      summary: Get User
      description: Returns a user.
      tags:
        - - subpackage_user
      parameters:
        - name: userId
          in: path
          description: The user_id of the user to get.
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The user that was retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:User'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:ModelsFactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:ModelsFactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:ModelsFactRatingExamples'
        instruction:
          type: string
    type_:User:
      type: object
      properties:
        created_at:
          type: string
        deleted_at:
          type: string
        disable_default_ontology:
          type: boolean
        email:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:ModelsFactRatingInstruction'
        first_name:
          type: string
        id:
          type: integer
        last_name:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        project_uuid:
          type: string
        session_count:
          type: integer
        updated_at:
          type: string
        user_id:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.get(
    user_id="userId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.get("userId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.Get(
	context.TODO(),
	"userId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users/userId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/users/userId")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/users/userId', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users/userId");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users/userId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Delete User

DELETE https://api.getzep.com/api/v2/users/{userId}

Deletes a user.

Reference: https://help.getzep.com/sdk-reference/user/delete

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete User
  version: endpoint_user.delete
paths:
  /users/{userId}:
    delete:
      operationId: delete
      summary: Delete User
      description: Deletes a user.
      tags:
        - - subpackage_user
      parameters:
        - name: userId
          in: path
          description: User ID
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.delete(
    user_id="userId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.delete("userId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.Delete(
	context.TODO(),
	"userId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users/userId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.getzep.com/api/v2/users/userId")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.getzep.com/api/v2/users/userId', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users/userId");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users/userId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Update User

PATCH https://api.getzep.com/api/v2/users/{userId}
Content-Type: application/json

Updates a user.

Reference: https://help.getzep.com/sdk-reference/user/update

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Update User
  version: endpoint_user.update
paths:
  /users/{userId}:
    patch:
      operationId: update
      summary: Update User
      description: Updates a user.
      tags:
        - - subpackage_user
      parameters:
        - name: userId
          in: path
          description: User ID
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The user that was updated.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:User'
        '400':
          description: Bad Request
          content: {}
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                disable_default_ontology:
                  type: boolean
                email:
                  type: string
                fact_rating_instruction:
                  $ref: '#/components/schemas/type_:FactRatingInstruction'
                first_name:
                  type: string
                last_name:
                  type: string
                metadata:
                  type: object
                  additionalProperties:
                    description: Any type
components:
  schemas:
    type_:FactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:FactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:FactRatingExamples'
        instruction:
          type: string
    type_:ModelsFactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:ModelsFactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:ModelsFactRatingExamples'
        instruction:
          type: string
    type_:User:
      type: object
      properties:
        created_at:
          type: string
        deleted_at:
          type: string
        disable_default_ontology:
          type: boolean
        email:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:ModelsFactRatingInstruction'
        first_name:
          type: string
        id:
          type: integer
        last_name:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        project_uuid:
          type: string
        session_count:
          type: integer
        updated_at:
          type: string
        user_id:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.update(
    user_id="userId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.update("userId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.Update(
	context.TODO(),
	"userId",
	&v3.UpdateUserRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users/userId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.patch("https://api.getzep.com/api/v2/users/userId")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('PATCH', 'https://api.getzep.com/api/v2/users/userId', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users/userId");
var request = new RestRequest(Method.PATCH);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users/userId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PATCH"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get User Node

GET https://api.getzep.com/api/v2/users/{userId}/node

Returns a user's node.

Reference: https://help.getzep.com/sdk-reference/user/get-node

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get User Node
  version: endpoint_user.get_node
paths:
  /users/{userId}/node:
    get:
      operationId: get-node
      summary: Get User Node
      description: Returns a user's node.
      tags:
        - - subpackage_user
      parameters:
        - name: userId
          in: path
          description: The user_id of the user to get the node for.
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Response object containing the User node.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:UserNodeResponse'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:EntityNode:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        labels:
          type: array
          items:
            type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        summary:
          type: string
        uuid:
          type: string
      required:
        - created_at
        - name
        - summary
        - uuid
    type_:UserNodeResponse:
      type: object
      properties:
        node:
          $ref: '#/components/schemas/type_:EntityNode'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.get_node(
    user_id="userId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.getNode("userId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.GetNode(
	context.TODO(),
	"userId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users/userId/node")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/users/userId/node")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/users/userId/node', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users/userId/node");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users/userId/node")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get User Threads

GET https://api.getzep.com/api/v2/users/{userId}/threads

Returns all threads for a user.

Reference: https://help.getzep.com/sdk-reference/user/get-threads

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get User Threads
  version: endpoint_user.get_threads
paths:
  /users/{userId}/threads:
    get:
      operationId: get-threads
      summary: Get User Threads
      description: Returns all threads for a user.
      tags:
        - - subpackage_user
      parameters:
        - name: userId
          in: path
          description: User ID
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/type_:Thread'
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:Thread:
      type: object
      properties:
        created_at:
          type: string
        project_uuid:
          type: string
        thread_id:
          type: string
        user_id:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.get_threads(
    user_id="userId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.getThreads("userId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.GetThreads(
	context.TODO(),
	"userId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users/userId/threads")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/users/userId/threads")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/users/userId/threads', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users/userId/threads");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users/userId/threads")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Warm User Cache

GET https://api.getzep.com/api/v2/users/{userId}/warm

Hints Zep to warm a user's graph for low-latency search

Reference: https://help.getzep.com/sdk-reference/user/warm

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Warm User Cache
  version: endpoint_user.warm
paths:
  /users/{userId}/warm:
    get:
      operationId: warm
      summary: Warm User Cache
      description: Hints Zep to warm a user's graph for low-latency search
      tags:
        - - subpackage_user
      parameters:
        - name: userId
          in: path
          description: User ID
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Warm hint accepted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '404':
          description: User or graph not found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.warm(
    user_id="userId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.warm("userId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.User.Warm(
	context.TODO(),
	"userId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/users/userId/warm")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/users/userId/warm")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/users/userId/warm', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/users/userId/warm");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/users/userId/warm")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Add Data

POST https://api.getzep.com/api/v2/graph
Content-Type: application/json

Add data to the graph.

Reference: https://help.getzep.com/sdk-reference/graph/add

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Add Data
  version: endpoint_graph.add
paths:
  /graph:
    post:
      operationId: add
      summary: Add Data
      description: Add data to the graph.
      tags:
        - - subpackage_graph
      parameters: []
      responses:
        '202':
          description: Added episode
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:Episode'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                created_at:
                  type: string
                data:
                  type: string
                graph_id:
                  type: string
                source_description:
                  type: string
                type:
                  $ref: '#/components/schemas/type_:GraphDataType'
                user_id:
                  type: string
              required:
                - data
                - type
components:
  schemas:
    type_:GraphDataType:
      type: string
      enum:
        - value: text
        - value: json
        - value: message
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:Episode:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        processed:
          type: boolean
        relevance:
          type: number
          format: double
        role:
          type: string
        role_type:
          $ref: '#/components/schemas/type_:RoleType'
        score:
          type: number
          format: double
        source:
          $ref: '#/components/schemas/type_:GraphDataType'
        source_description:
          type: string
        thread_id:
          type: string
        uuid:
          type: string
      required:
        - content
        - created_at
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.add(
    data="data",
    type="text",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.add({
    data: "data",
    type: "text"
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Add(
	context.TODO(),
	&v3.AddDataRequest{
		Data: "data",
		Type: v3.GraphDataTypeText,
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"data\": \"data\",\n  \"type\": \"text\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph")
  .header("Content-Type", "application/json")
  .body("{\n  \"data\": \"data\",\n  \"type\": \"text\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph', [
  'body' => '{
  "data": "data",
  "type": "text"
}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"data\": \"data\",\n  \"type\": \"text\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = [
  "data": "data",
  "type": "text"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Add Data in batch mode

POST https://api.getzep.com/api/v2/graph-batch
Content-Type: application/json

Add data to the graph in batch mode, processing episodes concurrently. Use only for data that is insensitive to processing order.

Reference: https://help.getzep.com/sdk-reference/graph/add-batch

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Add Data in batch mode
  version: endpoint_graph.add_batch
paths:
  /graph-batch:
    post:
      operationId: add-batch
      summary: Add Data in batch mode
      description: >-
        Add data to the graph in batch mode, processing episodes concurrently.
        Use only for data that is insensitive to processing order.
      tags:
        - - subpackage_graph
      parameters: []
      responses:
        '202':
          description: Added episodes
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/type_:Episode'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                episodes:
                  type: array
                  items:
                    $ref: '#/components/schemas/type_:EpisodeData'
                graph_id:
                  type: string
                user_id:
                  type: string
              required:
                - episodes
components:
  schemas:
    type_:GraphDataType:
      type: string
      enum:
        - value: text
        - value: json
        - value: message
    type_:EpisodeData:
      type: object
      properties:
        created_at:
          type: string
        data:
          type: string
        source_description:
          type: string
        type:
          $ref: '#/components/schemas/type_:GraphDataType'
      required:
        - data
        - type
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:Episode:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        processed:
          type: boolean
        relevance:
          type: number
          format: double
        role:
          type: string
        role_type:
          $ref: '#/components/schemas/type_:RoleType'
        score:
          type: number
          format: double
        source:
          $ref: '#/components/schemas/type_:GraphDataType'
        source_description:
          type: string
        thread_id:
          type: string
        uuid:
          type: string
      required:
        - content
        - created_at
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import EpisodeData, Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.add_batch(
    episodes=[
        EpisodeData(
            data="data",
            type="text",
        )
    ],
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.addBatch({
    episodes: [{
            data: "data",
            type: "text"
        }]
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.AddBatch(
	context.TODO(),
	&v3.AddDataBatchRequest{
		Episodes: []*v3.EpisodeData{
			&v3.EpisodeData{
				Data: "data",
				Type: v3.GraphDataTypeText,
			},
		},
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph-batch")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"episodes\": [\n    {\n      \"data\": \"data\",\n      \"type\": \"text\"\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph-batch")
  .header("Content-Type", "application/json")
  .body("{\n  \"episodes\": [\n    {\n      \"data\": \"data\",\n      \"type\": \"text\"\n    }\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph-batch', [
  'body' => '{
  "episodes": [
    {
      "data": "data",
      "type": "text"
    }
  ]
}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph-batch");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"episodes\": [\n    {\n      \"data\": \"data\",\n      \"type\": \"text\"\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = ["episodes": [
    [
      "data": "data",
      "type": "text"
    ]
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph-batch")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Add Fact Triple

POST https://api.getzep.com/api/v2/graph/add-fact-triple
Content-Type: application/json

Add a fact triple for a user or group

Reference: https://help.getzep.com/sdk-reference/graph/add-fact-triple

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Add Fact Triple
  version: endpoint_graph.add_fact_triple
paths:
  /graph/add-fact-triple:
    post:
      operationId: add-fact-triple
      summary: Add Fact Triple
      description: Add a fact triple for a user or group
      tags:
        - - subpackage_graph
      parameters: []
      responses:
        '200':
          description: Resulting triple
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:AddTripleResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                created_at:
                  type: string
                expired_at:
                  type: string
                fact:
                  type: string
                fact_name:
                  type: string
                fact_uuid:
                  type: string
                graph_id:
                  type: string
                invalid_at:
                  type: string
                source_node_name:
                  type: string
                source_node_summary:
                  type: string
                source_node_uuid:
                  type: string
                target_node_name:
                  type: string
                target_node_summary:
                  type: string
                target_node_uuid:
                  type: string
                user_id:
                  type: string
                valid_at:
                  type: string
              required:
                - fact
                - fact_name
                - target_node_name
components:
  schemas:
    type_:EntityEdge:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        episodes:
          type: array
          items:
            type: string
        expired_at:
          type: string
        fact:
          type: string
        invalid_at:
          type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        source_node_uuid:
          type: string
        target_node_uuid:
          type: string
        uuid:
          type: string
        valid_at:
          type: string
      required:
        - created_at
        - fact
        - name
        - source_node_uuid
        - target_node_uuid
        - uuid
    type_:EntityNode:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        labels:
          type: array
          items:
            type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        summary:
          type: string
        uuid:
          type: string
      required:
        - created_at
        - name
        - summary
        - uuid
    type_:AddTripleResponse:
      type: object
      properties:
        edge:
          $ref: '#/components/schemas/type_:EntityEdge'
        source_node:
          $ref: '#/components/schemas/type_:EntityNode'
        target_node:
          $ref: '#/components/schemas/type_:EntityNode'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.add_fact_triple(
    fact="fact",
    fact_name="fact_name",
    target_node_name="target_node_name",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.addFactTriple({
    fact: "fact",
    factName: "fact_name",
    targetNodeName: "target_node_name"
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.AddFactTriple(
	context.TODO(),
	&v3.AddTripleRequest{
		Fact:           "fact",
		FactName:       "fact_name",
		TargetNodeName: "target_node_name",
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/add-fact-triple")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"fact\": \"fact\",\n  \"fact_name\": \"fact_name\",\n  \"target_node_name\": \"target_node_name\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/add-fact-triple")
  .header("Content-Type", "application/json")
  .body("{\n  \"fact\": \"fact\",\n  \"fact_name\": \"fact_name\",\n  \"target_node_name\": \"target_node_name\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/add-fact-triple', [
  'body' => '{
  "fact": "fact",
  "fact_name": "fact_name",
  "target_node_name": "target_node_name"
}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/add-fact-triple");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"fact\": \"fact\",\n  \"fact_name\": \"fact_name\",\n  \"target_node_name\": \"target_node_name\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = [
  "fact": "fact",
  "fact_name": "fact_name",
  "target_node_name": "target_node_name"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/add-fact-triple")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Clone graph

POST https://api.getzep.com/api/v2/graph/clone
Content-Type: application/json

Clone a user or group graph.

Reference: https://help.getzep.com/sdk-reference/graph/clone

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Clone graph
  version: endpoint_graph.clone
paths:
  /graph/clone:
    post:
      operationId: clone
      summary: Clone graph
      description: Clone a user or group graph.
      tags:
        - - subpackage_graph
      parameters: []
      responses:
        '202':
          description: >-
            Response object containing graph_id or user_id pointing to the new
            graph
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:CloneGraphResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                source_graph_id:
                  type: string
                source_user_id:
                  type: string
                target_graph_id:
                  type: string
                target_user_id:
                  type: string
components:
  schemas:
    type_:CloneGraphResponse:
      type: object
      properties:
        graph_id:
          type: string
        user_id:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.clone()

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.clone();

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Clone(
	context.TODO(),
	&v3.CloneGraphRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/clone")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/clone")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/clone', [
  'body' => '{}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/clone");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/clone")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Create Graph

POST https://api.getzep.com/api/v2/graph/create
Content-Type: application/json

Creates a new graph.

Reference: https://help.getzep.com/sdk-reference/graph/create

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create Graph
  version: endpoint_graph.create
paths:
  /graph/create:
    post:
      operationId: create
      summary: Create Graph
      description: Creates a new graph.
      tags:
        - - subpackage_graph
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '201':
          description: The added graph
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:Graph'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                description:
                  type: string
                fact_rating_instruction:
                  $ref: '#/components/schemas/type_:FactRatingInstruction'
                graph_id:
                  type: string
                name:
                  type: string
              required:
                - graph_id
components:
  schemas:
    type_:FactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:FactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:FactRatingExamples'
        instruction:
          type: string
    type_:Graph:
      type: object
      properties:
        created_at:
          type: string
        description:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:FactRatingInstruction'
        graph_id:
          type: string
        id:
          type: integer
        name:
          type: string
        project_uuid:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.create(
    graph_id="graph_id",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.create({
    graphId: "graph_id"
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Create(
	context.TODO(),
	&v3.CreateGraphRequest{
		GraphID: "graph_id",
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/create")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"graph_id\": \"graph_id\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/create")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{\n  \"graph_id\": \"graph_id\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/create', [
  'body' => '{
  "graph_id": "graph_id"
}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/create");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"graph_id\": \"graph_id\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = ["graph_id": "graph_id"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/create")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# List all graphs.

GET https://api.getzep.com/api/v2/graph/list-all

Returns all graphs. In order to list users, use user.list_ordered instead

Reference: https://help.getzep.com/sdk-reference/graph/list-all

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List all graphs.
  version: endpoint_graph.list_all
paths:
  /graph/list-all:
    get:
      operationId: list-all
      summary: List all graphs.
      description: >-
        Returns all graphs. In order to list users, use user.list_ordered
        instead
      tags:
        - - subpackage_graph
      parameters:
        - name: pageNumber
          in: query
          description: Page number for pagination, starting from 1.
          required: false
          schema:
            type: integer
        - name: pageSize
          in: query
          description: Number of graphs to retrieve per page.
          required: false
          schema:
            type: integer
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successfully retrieved list of graphs.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:GraphListResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:FactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:FactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:FactRatingExamples'
        instruction:
          type: string
    type_:Graph:
      type: object
      properties:
        created_at:
          type: string
        description:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:FactRatingInstruction'
        graph_id:
          type: string
        id:
          type: integer
        name:
          type: string
        project_uuid:
          type: string
        uuid:
          type: string
    type_:GraphListResponse:
      type: object
      properties:
        graphs:
          type: array
          items:
            $ref: '#/components/schemas/type_:Graph'
        row_count:
          type: integer
        total_count:
          type: integer

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.list_all()

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.listAll();

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.ListAll(
	context.TODO(),
	&v3.GraphListAllRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/list-all")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/list-all")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/list-all', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/list-all");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/list-all")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Search Graph

POST https://api.getzep.com/api/v2/graph/search
Content-Type: application/json

Perform a graph search query.

Reference: https://help.getzep.com/sdk-reference/graph/search

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Search Graph
  version: endpoint_graph.search
paths:
  /graph/search:
    post:
      operationId: search
      summary: Search Graph
      description: Perform a graph search query.
      tags:
        - - subpackage_graph
      parameters: []
      responses:
        '200':
          description: Graph search results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:GraphSearchResults'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                bfs_origin_node_uuids:
                  type: array
                  items:
                    type: string
                center_node_uuid:
                  type: string
                graph_id:
                  type: string
                limit:
                  type: integer
                min_fact_rating:
                  type: number
                  format: double
                min_score:
                  type: number
                  format: double
                mmr_lambda:
                  type: number
                  format: double
                query:
                  type: string
                reranker:
                  $ref: '#/components/schemas/type_:Reranker'
                scope:
                  $ref: '#/components/schemas/type_:GraphSearchScope'
                search_filters:
                  $ref: '#/components/schemas/type_:SearchFilters'
                user_id:
                  type: string
              required:
                - query
components:
  schemas:
    type_:Reranker:
      type: string
      enum:
        - value: rrf
        - value: mmr
        - value: node_distance
        - value: episode_mentions
        - value: cross_encoder
    type_:GraphSearchScope:
      type: string
      enum:
        - value: edges
        - value: nodes
        - value: episodes
    type_:ComparisonOperator:
      type: string
      enum:
        - value: '='
        - value: <>
        - value: '>'
        - value: <
        - value: '>='
        - value: <=
        - value: IS NULL
        - value: IS NOT NULL
    type_:DateFilter:
      type: object
      properties:
        comparison_operator:
          $ref: '#/components/schemas/type_:ComparisonOperator'
        date:
          type: string
      required:
        - comparison_operator
        - date
    type_:SearchFilters:
      type: object
      properties:
        created_at:
          type: array
          items:
            type: array
            items:
              $ref: '#/components/schemas/type_:DateFilter'
        edge_types:
          type: array
          items:
            type: string
        exclude_edge_types:
          type: array
          items:
            type: string
        exclude_node_labels:
          type: array
          items:
            type: string
        expired_at:
          type: array
          items:
            type: array
            items:
              $ref: '#/components/schemas/type_:DateFilter'
        invalid_at:
          type: array
          items:
            type: array
            items:
              $ref: '#/components/schemas/type_:DateFilter'
        node_labels:
          type: array
          items:
            type: string
        valid_at:
          type: array
          items:
            type: array
            items:
              $ref: '#/components/schemas/type_:DateFilter'
    type_:EntityEdge:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        episodes:
          type: array
          items:
            type: string
        expired_at:
          type: string
        fact:
          type: string
        invalid_at:
          type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        source_node_uuid:
          type: string
        target_node_uuid:
          type: string
        uuid:
          type: string
        valid_at:
          type: string
      required:
        - created_at
        - fact
        - name
        - source_node_uuid
        - target_node_uuid
        - uuid
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:GraphDataType:
      type: string
      enum:
        - value: text
        - value: json
        - value: message
    type_:Episode:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        processed:
          type: boolean
        relevance:
          type: number
          format: double
        role:
          type: string
        role_type:
          $ref: '#/components/schemas/type_:RoleType'
        score:
          type: number
          format: double
        source:
          $ref: '#/components/schemas/type_:GraphDataType'
        source_description:
          type: string
        thread_id:
          type: string
        uuid:
          type: string
      required:
        - content
        - created_at
        - uuid
    type_:EntityNode:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        labels:
          type: array
          items:
            type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        summary:
          type: string
        uuid:
          type: string
      required:
        - created_at
        - name
        - summary
        - uuid
    type_:GraphSearchResults:
      type: object
      properties:
        edges:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityEdge'
        episodes:
          type: array
          items:
            $ref: '#/components/schemas/type_:Episode'
        nodes:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityNode'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.search(
    query="query",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.search({
    query: "query"
});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Search(
	context.TODO(),
	&v3.GraphSearchQuery{
		Query: "query",
	},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/search")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"query\": \"query\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/search")
  .header("Content-Type", "application/json")
  .body("{\n  \"query\": \"query\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/search', [
  'body' => '{
  "query": "query"
}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/search");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"query\": \"query\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = ["query": "query"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/search")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Graph

GET https://api.getzep.com/api/v2/graph/{graphId}

Returns a graph.

Reference: https://help.getzep.com/sdk-reference/graph/get

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Graph
  version: endpoint_graph.get
paths:
  /graph/{graphId}:
    get:
      operationId: get
      summary: Get Graph
      description: Returns a graph.
      tags:
        - - subpackage_graph
      parameters:
        - name: graphId
          in: path
          description: The graph_id of the graph to get.
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The graph that was retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:Graph'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:FactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:FactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:FactRatingExamples'
        instruction:
          type: string
    type_:Graph:
      type: object
      properties:
        created_at:
          type: string
        description:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:FactRatingInstruction'
        graph_id:
          type: string
        id:
          type: integer
        name:
          type: string
        project_uuid:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.get(
    graph_id="graphId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.get("graphId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Get(
	context.TODO(),
	"graphId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/graphId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/graphId")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/graphId', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/graphId");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/graphId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Delete Graph

DELETE https://api.getzep.com/api/v2/graph/{graphId}

Deletes a graph. If you would like to delete a user graph, make sure to use user.delete instead.

Reference: https://help.getzep.com/sdk-reference/graph/delete

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete Graph
  version: endpoint_graph.delete
paths:
  /graph/{graphId}:
    delete:
      operationId: delete
      summary: Delete Graph
      description: >-
        Deletes a graph. If you would like to delete a user graph, make sure to
        use user.delete instead.
      tags:
        - - subpackage_graph
      parameters:
        - name: graphId
          in: path
          description: Graph ID
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Deleted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '400':
          description: Bad Request
          content: {}
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.delete(
    graph_id="graphId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.delete("graphId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Delete(
	context.TODO(),
	"graphId",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/graphId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.getzep.com/api/v2/graph/graphId")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.getzep.com/api/v2/graph/graphId', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/graphId");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/graphId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Update Graph.

PATCH https://api.getzep.com/api/v2/graph/{graphId}
Content-Type: application/json

Updates information about a graph.

Reference: https://help.getzep.com/sdk-reference/graph/update

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Update Graph.
  version: endpoint_graph.update
paths:
  /graph/{graphId}:
    patch:
      operationId: update
      summary: Update Graph.
      description: Updates information about a graph.
      tags:
        - - subpackage_graph
      parameters:
        - name: graphId
          in: path
          description: Graph ID
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '201':
          description: The updated graph object
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:Graph'
        '400':
          description: Bad Request
          content: {}
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                description:
                  type: string
                fact_rating_instruction:
                  $ref: '#/components/schemas/type_:FactRatingInstruction'
                name:
                  type: string
components:
  schemas:
    type_:FactRatingExamples:
      type: object
      properties:
        high:
          type: string
        low:
          type: string
        medium:
          type: string
    type_:FactRatingInstruction:
      type: object
      properties:
        examples:
          $ref: '#/components/schemas/type_:FactRatingExamples'
        instruction:
          type: string
    type_:Graph:
      type: object
      properties:
        created_at:
          type: string
        description:
          type: string
        fact_rating_instruction:
          $ref: '#/components/schemas/type_:FactRatingInstruction'
        graph_id:
          type: string
        id:
          type: integer
        name:
          type: string
        project_uuid:
          type: string
        uuid:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.update(
    graph_id="graphId",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.update("graphId");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Update(
	context.TODO(),
	"graphId",
	&v3.UpdateGraphRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/graphId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.patch("https://api.getzep.com/api/v2/graph/graphId")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('PATCH', 'https://api.getzep.com/api/v2/graph/graphId', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/graphId");
var request = new RestRequest(Method.PATCH);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/graphId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PATCH"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Set graph ontology

PUT https://api.getzep.com/api/v2/graph/set-ontology
Content-Type: application/json

Sets custom entity and edge types for your graph. This wrapper method
provides a clean interface for defining your graph schema with custom
entity and edge types.

See the [full documentation](/customizing-graph-structure#setting-entity-and-edge-types) for details.

Reference: https://help.getzep.com/sdk-reference/graph/set-ontology

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Set graph ontology
  version: endpoint_graph.set_ontology
paths:
  /graph/set-ontology:
    put:
      operationId: set-ontology
      summary: Set graph ontology
      description: >-
        Sets custom entity and edge types for your graph. This wrapper method

        provides a clean interface for defining your graph schema with custom

        entity and edge types.


        See the [full
        documentation](/customizing-graph-structure#setting-entity-and-edge-types)
        for details.
      tags:
        - - subpackage_graph
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Ontology set successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                entities:
                  type: object
                  additionalProperties:
                    description: Any type
                edges:
                  type: object
                  additionalProperties:
                    description: Any type
                user_ids:
                  type: array
                  items:
                    type: string
                graph_ids:
                  type: array
                  items:
                    type: string
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud.client import Zep
from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel
from zep_cloud import EntityEdgeSourceTarget
from pydantic import Field

class Restaurant(EntityModel):
    cuisine_type: EntityText = Field(description="The cuisine type", default=None)

class RestaurantVisit(EdgeModel):
    restaurant_name: EntityText = Field(description="Restaurant name", default=None)

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.set_ontology(
    entities={
        "Restaurant": Restaurant,
    },
    edges={
        "RESTAURANT_VISIT": (
            RestaurantVisit,
            [EntityEdgeSourceTarget(source="User", target="Restaurant")]
        ),
    }
)

```

```typescript
import { ZepClient, entityFields, EntityType, EdgeType } from "@getzep/zep-cloud";

const RestaurantSchema: EntityType = {
    description: "Represents a restaurant.",
    fields: {
        cuisine_type: entityFields.text("The cuisine type"),
    },
};

const RestaurantVisit: EdgeType = {
    description: "User visited a restaurant.",
    fields: {
        restaurant_name: entityFields.text("Restaurant name"),
    },
    sourceTargets: [
        { source: "User", target: "Restaurant" },
    ],
};

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.setOntology(
    {
        Restaurant: RestaurantSchema,
    },
    {
        RESTAURANT_VISIT: RestaurantVisit,
    }
);

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

type Restaurant struct {
    v3.BaseEntity `name:"Restaurant" description:"Represents a restaurant."`
    CuisineType string `description:"The cuisine type" json:"cuisine_type,omitempty"`
}

type RestaurantVisit struct {
    v3.BaseEdge `name:"RESTAURANT_VISIT" description:"User visited a restaurant."`
    RestaurantName string `description:"Restaurant name" json:"restaurant_name,omitempty"`
}

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
_, err := client.Graph.SetOntology(
    context.TODO(),
    []v3.EntityDefinition{
        Restaurant{},
    },
    []v3.EdgeDefinitionWithSourceTargets{
        {
            EdgeModel: RestaurantVisit{},
            SourceTargets: []v3.EntityEdgeSourceTarget{
                {Source: v3.String("User"), Target: v3.String("Restaurant")},
            },
        },
    },
)
if err != nil {
    panic(err)
}

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/set-ontology")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Put.new(url)
request["Authorization"] = 'Api-Key <apiKey>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.put("https://api.getzep.com/api/v2/graph/set-ontology")
  .header("Authorization", "Api-Key <apiKey>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('PUT', 'https://api.getzep.com/api/v2/graph/set-ontology', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/set-ontology");
var request = new RestRequest(Method.PUT);
request.AddHeader("Authorization", "Api-Key <apiKey>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Api-Key <apiKey>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/set-ontology")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PUT"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# List graph ontology

GET https://api.getzep.com/api/v2/graph/list-ontology

Retrieves the current entity and edge types configured for your graph.

See the [full documentation](/customizing-graph-structure) for details.

Reference: https://help.getzep.com/sdk-reference/graph/list-ontology

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List graph ontology
  version: endpoint_graph.list_ontology
paths:
  /graph/list-ontology:
    get:
      operationId: list-ontology
      summary: List graph ontology
      description: |-
        Retrieves the current entity and edge types configured for your graph.

        See the [full documentation](/customizing-graph-structure) for details.
      tags:
        - - subpackage_graph
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Current ontology
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:EntityTypeResponse'
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:EntityPropertyType:
      type: string
      enum:
        - value: Text
        - value: Int
        - value: Float
        - value: Boolean
    type_:EntityProperty:
      type: object
      properties:
        description:
          type: string
        name:
          type: string
        type:
          $ref: '#/components/schemas/type_:EntityPropertyType'
      required:
        - description
        - name
        - type
    type_:EntityEdgeSourceTarget:
      type: object
      properties:
        source:
          type: string
        target:
          type: string
    type_:EdgeType:
      type: object
      properties:
        description:
          type: string
        name:
          type: string
        properties:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityProperty'
        source_targets:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityEdgeSourceTarget'
      required:
        - description
        - name
    type_:EntityType:
      type: object
      properties:
        description:
          type: string
        name:
          type: string
        properties:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityProperty'
      required:
        - description
        - name
    type_:EntityTypeResponse:
      type: object
      properties:
        edge_types:
          type: array
          items:
            $ref: '#/components/schemas/type_:EdgeType'
        entity_types:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityType'

```

## SDK Code Examples

```python
from zep_cloud.client import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
ontology = client.graph.list_ontology()
print("Entity types:", ontology.entity_types)
print("Edge types:", ontology.edge_types)

```

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
const ontology = await client.graph.listOntology();
console.log("Entity types:", ontology.entityTypes);
console.log("Edge types:", ontology.edgeTypes);

```

```go
import (
	context "context"
	fmt "fmt"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
ontology, err := client.Graph.ListOntology(context.TODO())
if err != nil {
    panic(err)
}
fmt.Printf("Entity types: %+v\n", ontology.EntityTypes)
fmt.Printf("Edge types: %+v\n", ontology.EdgeTypes)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/list-ontology")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/list-ontology")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/list-ontology', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/list-ontology");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/list-ontology")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Graph Edges

POST https://api.getzep.com/api/v2/graph/edge/graph/{graph_id}
Content-Type: application/json

Returns all edges for a graph.

Reference: https://help.getzep.com/sdk-reference/graph/edge/get-by-graph-id

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Graph Edges
  version: endpoint_graph/edge.get_by_graph_id
paths:
  /graph/edge/graph/{graph_id}:
    post:
      operationId: get-by-graph-id
      summary: Get Graph Edges
      description: Returns all edges for a graph.
      tags:
        - - subpackage_graph
          - subpackage_graph/edge
      parameters:
        - name: graph_id
          in: path
          description: Graph ID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Edges
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/type_:EntityEdge'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/type_:GraphEdgesRequest'
components:
  schemas:
    type_:GraphEdgesRequest:
      type: object
      properties:
        limit:
          type: integer
        uuid_cursor:
          type: string
    type_:EntityEdge:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        episodes:
          type: array
          items:
            type: string
        expired_at:
          type: string
        fact:
          type: string
        invalid_at:
          type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        source_node_uuid:
          type: string
        target_node_uuid:
          type: string
        uuid:
          type: string
        valid_at:
          type: string
      required:
        - created_at
        - fact
        - name
        - source_node_uuid
        - target_node_uuid
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.get_by_graph_id(
    graph_id="graph_id",
)

```

```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.getByGraphId("graph_id", {});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Edge.GetByGraphID(
	context.TODO(),
	"graph_id",
	&v3.GraphEdgesRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/edge/graph/graph_id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/edge/graph/graph_id")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/edge/graph/graph_id', [
  'body' => '{}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/edge/graph/graph_id");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/edge/graph/graph_id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get User Edges

POST https://api.getzep.com/api/v2/graph/edge/user/{user_id}
Content-Type: application/json

Returns all edges for a user.

Reference: https://help.getzep.com/sdk-reference/graph/edge/get-by-user-id

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get User Edges
  version: endpoint_graph/edge.get_by_user_id
paths:
  /graph/edge/user/{user_id}:
    post:
      operationId: get-by-user-id
      summary: Get User Edges
      description: Returns all edges for a user.
      tags:
        - - subpackage_graph
          - subpackage_graph/edge
      parameters:
        - name: user_id
          in: path
          description: User ID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Edges
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/type_:EntityEdge'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/type_:GraphEdgesRequest'
components:
  schemas:
    type_:GraphEdgesRequest:
      type: object
      properties:
        limit:
          type: integer
        uuid_cursor:
          type: string
    type_:EntityEdge:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        episodes:
          type: array
          items:
            type: string
        expired_at:
          type: string
        fact:
          type: string
        invalid_at:
          type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        source_node_uuid:
          type: string
        target_node_uuid:
          type: string
        uuid:
          type: string
        valid_at:
          type: string
      required:
        - created_at
        - fact
        - name
        - source_node_uuid
        - target_node_uuid
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.get_by_user_id(
    user_id="user_id",
)

```

```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.getByUserId("user_id", {});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Edge.GetByUserID(
	context.TODO(),
	"user_id",
	&v3.GraphEdgesRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/edge/user/user_id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/edge/user/user_id")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/edge/user/user_id', [
  'body' => '{}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/edge/user/user_id");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/edge/user/user_id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Edge

GET https://api.getzep.com/api/v2/graph/edge/{uuid}

Returns a specific edge by its UUID.

Reference: https://help.getzep.com/sdk-reference/graph/edge/get

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Edge
  version: endpoint_graph/edge.get
paths:
  /graph/edge/{uuid}:
    get:
      operationId: get
      summary: Get Edge
      description: Returns a specific edge by its UUID.
      tags:
        - - subpackage_graph
          - subpackage_graph/edge
      parameters:
        - name: uuid
          in: path
          description: Edge UUID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Edge
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:EntityEdge'
        '400':
          description: Bad Request
          content: {}
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:EntityEdge:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        episodes:
          type: array
          items:
            type: string
        expired_at:
          type: string
        fact:
          type: string
        invalid_at:
          type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        source_node_uuid:
          type: string
        target_node_uuid:
          type: string
        uuid:
          type: string
        valid_at:
          type: string
      required:
        - created_at
        - fact
        - name
        - source_node_uuid
        - target_node_uuid
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.get(
    uuid_="uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.get("uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Edge.Get(
	context.TODO(),
	"uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/edge/uuid")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/edge/uuid")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/edge/uuid');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/edge/uuid");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/edge/uuid")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Delete Edge

DELETE https://api.getzep.com/api/v2/graph/edge/{uuid}

Deletes an edge by UUID.

Reference: https://help.getzep.com/sdk-reference/graph/edge/delete

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete Edge
  version: endpoint_graph/edge.delete
paths:
  /graph/edge/{uuid}:
    delete:
      operationId: delete
      summary: Delete Edge
      description: Deletes an edge by UUID.
      tags:
        - - subpackage_graph
          - subpackage_graph/edge
      parameters:
        - name: uuid
          in: path
          description: Edge UUID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Edge deleted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.delete(
    uuid_="uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.delete("uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Edge.Delete(
	context.TODO(),
	"uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/edge/uuid")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.getzep.com/api/v2/graph/edge/uuid")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.getzep.com/api/v2/graph/edge/uuid');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/edge/uuid");
var request = new RestRequest(Method.DELETE);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/edge/uuid")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Graph Episodes

GET https://api.getzep.com/api/v2/graph/episodes/graph/{graph_id}

Returns episodes by graph id.

Reference: https://help.getzep.com/sdk-reference/graph/episode/get-by-graph-id

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Graph Episodes
  version: endpoint_graph/episode.get_by_graph_id
paths:
  /graph/episodes/graph/{graph_id}:
    get:
      operationId: get-by-graph-id
      summary: Get Graph Episodes
      description: Returns episodes by graph id.
      tags:
        - - subpackage_graph
          - subpackage_graph/episode
      parameters:
        - name: graph_id
          in: path
          description: Graph ID
          required: true
          schema:
            type: string
        - name: lastn
          in: query
          description: The number of most recent episodes to retrieve.
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: Episodes
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:EpisodeResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:GraphDataType:
      type: string
      enum:
        - value: text
        - value: json
        - value: message
    type_:Episode:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        processed:
          type: boolean
        relevance:
          type: number
          format: double
        role:
          type: string
        role_type:
          $ref: '#/components/schemas/type_:RoleType'
        score:
          type: number
          format: double
        source:
          $ref: '#/components/schemas/type_:GraphDataType'
        source_description:
          type: string
        thread_id:
          type: string
        uuid:
          type: string
      required:
        - content
        - created_at
        - uuid
    type_:EpisodeResponse:
      type: object
      properties:
        episodes:
          type: array
          items:
            $ref: '#/components/schemas/type_:Episode'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get_by_graph_id(
    graph_id="graph_id",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.getByGraphId("graph_id");

```

```go
import (
	context "context"
	graph "github.com/getzep/zep-go/v3/graph"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Episode.GetByGraphID(
	context.TODO(),
	"graph_id",
	&graph.EpisodeGetByGraphIDRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/episodes/graph/graph_id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/episodes/graph/graph_id")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/episodes/graph/graph_id');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/episodes/graph/graph_id");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/episodes/graph/graph_id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get User Episodes

GET https://api.getzep.com/api/v2/graph/episodes/user/{user_id}

Returns episodes by user id.

Reference: https://help.getzep.com/sdk-reference/graph/episode/get-by-user-id

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get User Episodes
  version: endpoint_graph/episode.get_by_user_id
paths:
  /graph/episodes/user/{user_id}:
    get:
      operationId: get-by-user-id
      summary: Get User Episodes
      description: Returns episodes by user id.
      tags:
        - - subpackage_graph
          - subpackage_graph/episode
      parameters:
        - name: user_id
          in: path
          description: User ID
          required: true
          schema:
            type: string
        - name: lastn
          in: query
          description: The number of most recent episodes entries to retrieve.
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: Episodes
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:EpisodeResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:GraphDataType:
      type: string
      enum:
        - value: text
        - value: json
        - value: message
    type_:Episode:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        processed:
          type: boolean
        relevance:
          type: number
          format: double
        role:
          type: string
        role_type:
          $ref: '#/components/schemas/type_:RoleType'
        score:
          type: number
          format: double
        source:
          $ref: '#/components/schemas/type_:GraphDataType'
        source_description:
          type: string
        thread_id:
          type: string
        uuid:
          type: string
      required:
        - content
        - created_at
        - uuid
    type_:EpisodeResponse:
      type: object
      properties:
        episodes:
          type: array
          items:
            $ref: '#/components/schemas/type_:Episode'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get_by_user_id(
    user_id="user_id",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.getByUserId("user_id");

```

```go
import (
	context "context"
	graph "github.com/getzep/zep-go/v3/graph"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Episode.GetByUserID(
	context.TODO(),
	"user_id",
	&graph.EpisodeGetByUserIDRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/episodes/user/user_id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/episodes/user/user_id")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/episodes/user/user_id');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/episodes/user/user_id");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/episodes/user/user_id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Episode

GET https://api.getzep.com/api/v2/graph/episodes/{uuid}

Returns episodes by UUID

Reference: https://help.getzep.com/sdk-reference/graph/episode/get

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Episode
  version: endpoint_graph/episode.get
paths:
  /graph/episodes/{uuid}:
    get:
      operationId: get
      summary: Get Episode
      description: Returns episodes by UUID
      tags:
        - - subpackage_graph
          - subpackage_graph/episode
      parameters:
        - name: uuid
          in: path
          description: Episode UUID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Episode
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:Episode'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:GraphDataType:
      type: string
      enum:
        - value: text
        - value: json
        - value: message
    type_:Episode:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        processed:
          type: boolean
        relevance:
          type: number
          format: double
        role:
          type: string
        role_type:
          $ref: '#/components/schemas/type_:RoleType'
        score:
          type: number
          format: double
        source:
          $ref: '#/components/schemas/type_:GraphDataType'
        source_description:
          type: string
        thread_id:
          type: string
        uuid:
          type: string
      required:
        - content
        - created_at
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get(
    uuid_="uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.get("uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Episode.Get(
	context.TODO(),
	"uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/episodes/uuid")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/episodes/uuid")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/episodes/uuid');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/episodes/uuid");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/episodes/uuid")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Delete Episode

DELETE https://api.getzep.com/api/v2/graph/episodes/{uuid}

Deletes an episode by its UUID.

Reference: https://help.getzep.com/sdk-reference/graph/episode/delete

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Delete Episode
  version: endpoint_graph/episode.delete
paths:
  /graph/episodes/{uuid}:
    delete:
      operationId: delete
      summary: Delete Episode
      description: Deletes an episode by its UUID.
      tags:
        - - subpackage_graph
          - subpackage_graph/episode
      parameters:
        - name: uuid
          in: path
          description: Episode UUID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Episode deleted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:SuccessResponse'
        '400':
          description: Bad Request
          content: {}
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:SuccessResponse:
      type: object
      properties:
        message:
          type: string

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.delete(
    uuid_="uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.delete("uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Episode.Delete(
	context.TODO(),
	"uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/episodes/uuid")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.delete("https://api.getzep.com/api/v2/graph/episodes/uuid")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://api.getzep.com/api/v2/graph/episodes/uuid');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/episodes/uuid");
var request = new RestRequest(Method.DELETE);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/episodes/uuid")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Return any nodes and edges mentioned in an episode

GET https://api.getzep.com/api/v2/graph/episodes/{uuid}/mentions

Returns nodes and edges mentioned in an episode

Reference: https://help.getzep.com/sdk-reference/graph/episode/get-nodes-and-edges

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Return any nodes and edges mentioned in an episode
  version: endpoint_graph/episode.get_nodes_and_edges
paths:
  /graph/episodes/{uuid}/mentions:
    get:
      operationId: get-nodes-and-edges
      summary: Return any nodes and edges mentioned in an episode
      description: Returns nodes and edges mentioned in an episode
      tags:
        - - subpackage_graph
          - subpackage_graph/episode
      parameters:
        - name: uuid
          in: path
          description: Episode uuid
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Edges and nodes mentioned in an episode
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:EpisodeMentions'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:EntityEdge:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        episodes:
          type: array
          items:
            type: string
        expired_at:
          type: string
        fact:
          type: string
        invalid_at:
          type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        source_node_uuid:
          type: string
        target_node_uuid:
          type: string
        uuid:
          type: string
        valid_at:
          type: string
      required:
        - created_at
        - fact
        - name
        - source_node_uuid
        - target_node_uuid
        - uuid
    type_:EntityNode:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        labels:
          type: array
          items:
            type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        summary:
          type: string
        uuid:
          type: string
      required:
        - created_at
        - name
        - summary
        - uuid
    type_:EpisodeMentions:
      type: object
      properties:
        edges:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityEdge'
        nodes:
          type: array
          items:
            $ref: '#/components/schemas/type_:EntityNode'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get_nodes_and_edges(
    uuid_="uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.getNodesAndEdges("uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Episode.GetNodesAndEdges(
	context.TODO(),
	"uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/episodes/uuid/mentions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/episodes/uuid/mentions")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/episodes/uuid/mentions');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/episodes/uuid/mentions");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/episodes/uuid/mentions")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Graph Nodes

POST https://api.getzep.com/api/v2/graph/node/graph/{graph_id}
Content-Type: application/json

Returns all nodes for a graph.

Reference: https://help.getzep.com/sdk-reference/graph/node/get-by-graph-id

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Graph Nodes
  version: endpoint_graph/node.get_by_graph_id
paths:
  /graph/node/graph/{graph_id}:
    post:
      operationId: get-by-graph-id
      summary: Get Graph Nodes
      description: Returns all nodes for a graph.
      tags:
        - - subpackage_graph
          - subpackage_graph/node
      parameters:
        - name: graph_id
          in: path
          description: Graph ID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Nodes
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/type_:EntityNode'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/type_:GraphNodesRequest'
components:
  schemas:
    type_:GraphNodesRequest:
      type: object
      properties:
        limit:
          type: integer
        uuid_cursor:
          type: string
    type_:EntityNode:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        labels:
          type: array
          items:
            type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        summary:
          type: string
        uuid:
          type: string
      required:
        - created_at
        - name
        - summary
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_by_graph_id(
    graph_id="graph_id",
)

```

```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getByGraphId("graph_id", {});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Node.GetByGraphID(
	context.TODO(),
	"graph_id",
	&v3.GraphNodesRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/node/graph/graph_id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/node/graph/graph_id")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/node/graph/graph_id', [
  'body' => '{}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/node/graph/graph_id");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/node/graph/graph_id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get User Nodes

POST https://api.getzep.com/api/v2/graph/node/user/{user_id}
Content-Type: application/json

Returns all nodes for a user

Reference: https://help.getzep.com/sdk-reference/graph/node/get-by-user-id

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get User Nodes
  version: endpoint_graph/node.get_by_user_id
paths:
  /graph/node/user/{user_id}:
    post:
      operationId: get-by-user-id
      summary: Get User Nodes
      description: Returns all nodes for a user
      tags:
        - - subpackage_graph
          - subpackage_graph/node
      parameters:
        - name: user_id
          in: path
          description: User ID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Nodes
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/type_:EntityNode'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/type_:GraphNodesRequest'
components:
  schemas:
    type_:GraphNodesRequest:
      type: object
      properties:
        limit:
          type: integer
        uuid_cursor:
          type: string
    type_:EntityNode:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        labels:
          type: array
          items:
            type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        summary:
          type: string
        uuid:
          type: string
      required:
        - created_at
        - name
        - summary
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_by_user_id(
    user_id="user_id",
)

```

```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getByUserId("user_id", {});

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3 "github.com/getzep/zep-go/v3"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Node.GetByUserID(
	context.TODO(),
	"user_id",
	&v3.GraphNodesRequest{},
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/node/user/user_id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://api.getzep.com/api/v2/graph/node/user/user_id")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.getzep.com/api/v2/graph/node/user/user_id', [
  'body' => '{}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/node/user/user_id");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/node/user/user_id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Entity Edges for a node

GET https://api.getzep.com/api/v2/graph/node/{node_uuid}/entity-edges

Returns all edges for a node

Reference: https://help.getzep.com/sdk-reference/graph/node/get-edges

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Entity Edges for a node
  version: endpoint_graph/node.get_edges
paths:
  /graph/node/{node_uuid}/entity-edges:
    get:
      operationId: get-edges
      summary: Get Entity Edges for a node
      description: Returns all edges for a node
      tags:
        - - subpackage_graph
          - subpackage_graph/node
      parameters:
        - name: node_uuid
          in: path
          description: Node UUID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Edges
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/type_:EntityEdge'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:EntityEdge:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        episodes:
          type: array
          items:
            type: string
        expired_at:
          type: string
        fact:
          type: string
        invalid_at:
          type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        source_node_uuid:
          type: string
        target_node_uuid:
          type: string
        uuid:
          type: string
        valid_at:
          type: string
      required:
        - created_at
        - fact
        - name
        - source_node_uuid
        - target_node_uuid
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_edges(
    node_uuid="node_uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getEdges("node_uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Node.GetEdges(
	context.TODO(),
	"node_uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/node/node_uuid/entity-edges")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/node/node_uuid/entity-edges")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/node/node_uuid/entity-edges');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/node/node_uuid/entity-edges");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/node/node_uuid/entity-edges")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Episodes for a node

GET https://api.getzep.com/api/v2/graph/node/{node_uuid}/episodes

Returns all episodes that mentioned a given node

Reference: https://help.getzep.com/sdk-reference/graph/node/get-episodes

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Episodes for a node
  version: endpoint_graph/node.get_episodes
paths:
  /graph/node/{node_uuid}/episodes:
    get:
      operationId: get-episodes
      summary: Get Episodes for a node
      description: Returns all episodes that mentioned a given node
      tags:
        - - subpackage_graph
          - subpackage_graph/node
      parameters:
        - name: node_uuid
          in: path
          description: Node UUID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Episodes
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:EpisodeResponse'
        '400':
          description: Bad Request
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:RoleType:
      type: string
      enum:
        - value: norole
        - value: system
        - value: assistant
        - value: user
        - value: function
        - value: tool
    type_:GraphDataType:
      type: string
      enum:
        - value: text
        - value: json
        - value: message
    type_:Episode:
      type: object
      properties:
        content:
          type: string
        created_at:
          type: string
        metadata:
          type: object
          additionalProperties:
            description: Any type
        processed:
          type: boolean
        relevance:
          type: number
          format: double
        role:
          type: string
        role_type:
          $ref: '#/components/schemas/type_:RoleType'
        score:
          type: number
          format: double
        source:
          $ref: '#/components/schemas/type_:GraphDataType'
        source_description:
          type: string
        thread_id:
          type: string
        uuid:
          type: string
      required:
        - content
        - created_at
        - uuid
    type_:EpisodeResponse:
      type: object
      properties:
        episodes:
          type: array
          items:
            $ref: '#/components/schemas/type_:Episode'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_episodes(
    node_uuid="node_uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getEpisodes("node_uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Node.GetEpisodes(
	context.TODO(),
	"node_uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/node/node_uuid/episodes")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/node/node_uuid/episodes")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/node/node_uuid/episodes');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/node/node_uuid/episodes");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/node/node_uuid/episodes")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Get Node

GET https://api.getzep.com/api/v2/graph/node/{uuid}

Returns a specific node by its UUID.

Reference: https://help.getzep.com/sdk-reference/graph/node/get

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get Node
  version: endpoint_graph/node.get
paths:
  /graph/node/{uuid}:
    get:
      operationId: get
      summary: Get Node
      description: Returns a specific node by its UUID.
      tags:
        - - subpackage_graph
          - subpackage_graph/node
      parameters:
        - name: uuid
          in: path
          description: Node UUID
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Node
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:EntityNode'
        '400':
          description: Bad Request
          content: {}
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:EntityNode:
      type: object
      properties:
        attributes:
          type: object
          additionalProperties:
            description: Any type
        created_at:
          type: string
        labels:
          type: array
          items:
            type: string
        name:
          type: string
        relevance:
          type: number
          format: double
        score:
          type: number
          format: double
        summary:
          type: string
        uuid:
          type: string
      required:
        - created_at
        - name
        - summary
        - uuid

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get(
    uuid_="uuid",
)

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.get("uuid");

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Graph.Node.Get(
	context.TODO(),
	"uuid",
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/graph/node/uuid")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/graph/node/uuid")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/graph/node/uuid');

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/graph/node/uuid");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/graph/node/uuid")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Retrieves project information

GET https://api.getzep.com/api/v2/projects/info

Retrieve project info based on the provided api key.

Reference: https://help.getzep.com/sdk-reference/project/get

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Retrieves project information
  version: endpoint_project.get
paths:
  /projects/info:
    get:
      operationId: get
      summary: Retrieves project information
      description: Retrieve project info based on the provided api key.
      tags:
        - - subpackage_project
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Api-Key <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/type_:ProjectInfoResponse'
        '400':
          description: Bad Request
          content: {}
        '404':
          description: Not Found
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    type_:ProjectInfo:
      type: object
      properties:
        created_at:
          type: string
        description:
          type: string
        name:
          type: string
        uuid:
          type: string
    type_:ProjectInfoResponse:
      type: object
      properties:
        project:
          $ref: '#/components/schemas/type_:ProjectInfo'

```

## SDK Code Examples

```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.project.get()

```

```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.project.get();

```

```go
import (
	context "context"
	option "github.com/getzep/zep-go/v3/option"
	v3client "github.com/getzep/zep-go/v3/client"
)

client := v3client.NewClient(
	option.WithAPIKey(
		"<YOUR_APIKey>",
	),
)
response, err := client.Project.Get(
	context.TODO(),
)

```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.getzep.com/api/v2/projects/info")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Api-Key <apiKey>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://api.getzep.com/api/v2/projects/info")
  .header("Authorization", "Api-Key <apiKey>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.getzep.com/api/v2/projects/info', [
  'headers' => [
    'Authorization' => 'Api-Key <apiKey>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://api.getzep.com/api/v2/projects/info");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Api-Key <apiKey>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Api-Key <apiKey>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.getzep.com/api/v2/projects/info")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

# Welcome to Graphiti!

<Tip>
  Want to use Graphiti with AI assistants like Claude Desktop or Cursor? Check out the [Knowledge Graph MCP Server](/graphiti/getting-started/mcp-server).
</Tip>

Graphiti is a Python framework for building temporally-aware knowledge graphs designed for AI agents. It enables real-time incremental updates to knowledge graphs without batch recomputation, making it suitable for dynamic environments where relationships and information evolve over time.

<CardGroup cols={3}>
  <Card title="Overview" icon="chart-network" href="/graphiti/getting-started/overview">
    Learn about Graphiti's core concepts and how temporal knowledge graphs work.
  </Card>

  <Card title="Quick Start" icon="rocket" href="/graphiti/getting-started/quick-start">
    Get up and running with Graphiti in minutes including installation, episodes, search, and basic operations.
  </Card>

  <Card title="Knowledge Graph MCP Server" icon="server" href="/graphiti/getting-started/mcp-server">
    Use Graphiti with AI assistants like Claude Desktop or Cursor.
  </Card>

  <Card title="Adding Episodes" icon="file-plus" href="/graphiti/core-concepts/adding-episodes">
    Learn how to add text and JSON episodes to build your knowledge graph.
  </Card>

  <Card title="Searching" icon="magnifying-glass" href="/graphiti/working-with-data/searching">
    Discover hybrid search capabilities combining semantic, keyword, and graph-based retrieval.
  </Card>

  <Card title="Custom Entities" icon="shapes" href="/graphiti/core-concepts/custom-entity-and-edge-types">
    Define domain-specific entity types for more precise knowledge representation.
  </Card>
</CardGroup>


# Overview

> Temporal Knowledge Graphs for Agentic Applications

<Card title="What is a Knowledge Graph?" icon="duotone chart-network">
  Graphiti helps you create and query Knowledge Graphs that evolve over time. A
  knowledge graph is a network of interconnected facts, such as *“Kendra loves
  Adidas shoes.”* Each fact is a *“triplet”* represented by two entities, or
  nodes (*”Kendra”, “Adidas shoes”*), and their relationship, or edge
  (*”loves”*).

  <br />

  Knowledge Graphs have been explored extensively for information retrieval.
  What makes Graphiti unique is its ability to autonomously build a knowledge
  graph while handling changing relationships and maintaining historical
  context.
</Card>

![graphiti intro slides](file:944922c0-87b1-4b85-8622-6254308407e5)

Graphiti builds dynamic, temporally-aware knowledge graphs that represent complex, evolving relationships between entities over time. It ingests both unstructured and structured data, and the resulting graph may be queried using a fusion of time, full-text, semantic, and graph algorithm approaches.

With Graphiti, you can build LLM applications such as:

* Assistants that learn from user interactions, fusing personal knowledge with dynamic data from business systems like CRMs and billing platforms.
* Agents that autonomously execute complex tasks, reasoning with state changes from multiple dynamic sources.

Graphiti supports a wide range of applications in sales, customer service, health, finance, and more, enabling long-term recall and state-based reasoning for both assistants and agents.

## Graphiti and Zep Memory

Graphiti powers the core of [Zep's memory layer](https://www.getzep.com) for LLM-powered Assistants and Agents.

We're excited to open-source Graphiti, believing its potential reaches far beyond memory applications.

## Why Graphiti?

We were intrigued by Microsoft’s GraphRAG, which expanded on RAG text chunking by using a graph to better model a document corpus and making this representation available via semantic and graph search techniques. However, GraphRAG did not address our core problem: It's primarily designed for static documents and doesn't inherently handle temporal aspects of data.

Graphiti is designed from the ground up to handle constantly changing information, hybrid semantic and graph search, and scale:

* **Temporal Awareness:** Tracks changes in facts and relationships over time, enabling point-in-time queries. Graph edges include temporal metadata to record relationship lifecycles.
* **Episodic Processing:** Ingests data as discrete episodes, maintaining data provenance and allowing incremental entity and relationship extraction.
* **Custom Entity Types:** Supports defining domain-specific entity types, enabling more precise knowledge representation for specialized applications.
* **Hybrid Search:** Combines semantic and BM25 full-text search, with the ability to rerank results by distance from a central node e.g. "Kendra".
* **Scalable:** Designed for processing large datasets, with parallelization of LLM calls for bulk processing while preserving the chronology of events.
* **Supports Varied Sources:** Can ingest both unstructured text and structured JSON data.

| Aspect                     | GraphRAG                              | Graphiti                                         |
| -------------------------- | ------------------------------------- | ------------------------------------------------ |
| **Primary Use**            | Static document summarization         | Dynamic data management                          |
| **Data Handling**          | Batch-oriented processing             | Continuous, incremental updates                  |
| **Knowledge Structure**    | Entity clusters & community summaries | Episodic data, semantic entities, communities    |
| **Retrieval Method**       | Sequential LLM summarization          | Hybrid semantic, keyword, and graph-based search |
| **Adaptability**           | Low                                   | High                                             |
| **Temporal Handling**      | Basic timestamp tracking              | Explicit bi-temporal tracking                    |
| **Contradiction Handling** | LLM-driven summarization judgments    | Temporal edge invalidation                       |
| **Query Latency**          | Seconds to tens of seconds            | Typically sub-second latency                     |
| **Custom Entity Types**    | No                                    | Yes, customizable                                |
| **Scalability**            | Moderate                              | High, optimized for large datasets               |

Graphiti is specifically designed to address the challenges of dynamic and frequently updated datasets, making it particularly suitable for applications requiring real-time interaction and precise historical queries.

![graphiti demo slides](file:41430d15-808c-494c-be27-800489d33953)


# Quick Start

> Getting started with Graphiti

<Info>
  For complete working examples, check out the [Graphiti Quickstart Examples](https://github.com/getzep/graphiti/tree/main/examples/quickstart) on GitHub.
</Info>

## Installation

Requirements:

* Python 3.10 or higher
* Neo4j 5.26 or higher or FalkorDB 1.1.2 or higher (see [Graph Database Configuration](/graphiti/configuration/graph-db-configuration) for setup options)
* OpenAI API key (Graphiti defaults to OpenAI for LLM inference and embedding)

<Note>
  The simplest way to install Neo4j is via [Neo4j Desktop](https://neo4j.com/download/). It provides a user-friendly interface to manage Neo4j instances and databases.
</Note>

```bash
pip install graphiti-core
```

or

```bash
uv add graphiti-core
```

### Alternative LLM Providers

<Note>
  While Graphiti defaults to OpenAI, it supports multiple LLM providers including Azure OpenAI, Google Gemini, Anthropic, Groq, and local models via Ollama. For detailed configuration instructions, see our [LLM Configuration](/graphiti/configuration/llm-configuration) guide.
</Note>

### Default to Slower, Low Concurrency; LLM Provider 429 Rate Limit Errors

Graphiti's ingestion pipelines are designed for high concurrency. By default, concurrency is set low to avoid LLM Provider 429 Rate Limit Errors. If you find Graphiti slow, please increase concurrency as described below.

Concurrency controlled by the `SEMAPHORE_LIMIT` environment variable. By default, `SEMAPHORE_LIMIT` is set to `10` concurrent operations to help prevent `429` rate limit errors from your LLM provider. If you encounter such errors, try lowering this value.

If your LLM provider allows higher throughput, you can increase `SEMAPHORE_LIMIT` to boost episode ingestion performance.

### Environment Variables

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

#### Optional Variables

* `GRAPHITI_TELEMETRY_ENABLED`: Set to `false` to disable anonymous telemetry collection

## Getting Started with Graphiti

For a comprehensive overview of Graphiti and its capabilities, check out the [Overview](/graphiti/getting-started/overview) page.

### Required Imports

First, import the necessary libraries for working with Graphiti:

```python
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from logging import INFO

from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
```

### Configuration

<Note>
  Graphiti uses OpenAI by default for LLM inference and embedding. Ensure that an `OPENAI_API_KEY` is set in your environment. Support for multiple LLM providers is available - see our [LLM Configuration](/graphiti/configuration/llm-configuration) guide.

  Graphiti also requires Neo4j connection parameters. Set the following environment variables:

  * `NEO4J_URI`: The URI of your Neo4j database (default: bolt://localhost:7687)
  * `NEO4J_USER`: Your Neo4j username (default: neo4j)
  * `NEO4J_PASSWORD`: Your Neo4j password

  For detailed database setup instructions, see our [Graph Database Configuration](/graphiti/configuration/graph-db-configuration) guide.
</Note>

Set up logging and environment variables for connecting to the Neo4j database:

```python
# Configure logging
logging.basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

load_dotenv()

# Neo4j connection parameters
# Make sure Neo4j Desktop is running with a local DBMS started
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

if not neo4j_uri or not neo4j_user or not neo4j_password:
    raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')
```

### Main Function

Create an async main function to run all Graphiti operations:

```python
async def main():
    # Main function implementation will go here
    pass

if __name__ == '__main__':
    asyncio.run(main())
```

### Initialization

Connect to Neo4j and set up Graphiti indices. This is required before using other Graphiti functionality:

```python
# Initialize Graphiti with Neo4j connection
graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

try:
    # Initialize the graph database with graphiti's indices. This only needs to be done once.
    await graphiti.build_indices_and_constraints()
    
    # Additional code will go here
    
finally:
    # Close the connection
    await graphiti.close()
    print('\nConnection closed')
```

### Adding Episodes

Episodes are the primary units of information in Graphiti. They can be text or structured JSON and are automatically processed to extract entities and relationships. For more detailed information on episodes and bulk loading, see the [Adding Episodes](/graphiti/core-concepts/adding-episodes) page:

```python
# Episodes list containing both text and JSON episodes
episodes = [
    {
        'content': 'Kamala Harris is the Attorney General of California. She was previously '
        'the district attorney for San Francisco.',
        'type': EpisodeType.text,
        'description': 'podcast transcript',
    },
    {
        'content': 'As AG, Harris was in office from January 3, 2011 – January 3, 2017',
        'type': EpisodeType.text,
        'description': 'podcast transcript',
    },
    {
        'content': {
            'name': 'Gavin Newsom',
            'position': 'Governor',
            'state': 'California',
            'previous_role': 'Lieutenant Governor',
            'previous_location': 'San Francisco',
        },
        'type': EpisodeType.json,
        'description': 'podcast metadata',
    },
    {
        'content': {
            'name': 'Gavin Newsom',
            'position': 'Governor',
            'term_start': 'January 7, 2019',
            'term_end': 'Present',
        },
        'type': EpisodeType.json,
        'description': 'podcast metadata',
    },
]

# Add episodes to the graph
for i, episode in enumerate(episodes):
    await graphiti.add_episode(
        name=f'Freakonomics Radio {i}',
        episode_body=episode['content']
        if isinstance(episode['content'], str)
        else json.dumps(episode['content']),
        source=episode['type'],
        source_description=episode['description'],
        reference_time=datetime.now(timezone.utc),
    )
    print(f'Added episode: Freakonomics Radio {i} ({episode["type"].value})')
```

### Basic Search

The simplest way to retrieve relationships (edges) from Graphiti is using the search method, which performs a hybrid search combining semantic similarity and BM25 text retrieval. For more details on search capabilities, see the [Searching the Graph](/graphiti/working-with-data/searching) page:

```python
# Perform a hybrid search combining semantic similarity and BM25 retrieval
print("\nSearching for: 'Who was the California Attorney General?'")
results = await graphiti.search('Who was the California Attorney General?')

# Print search results
print('\nSearch Results:')
for result in results:
    print(f'UUID: {result.uuid}')
    print(f'Fact: {result.fact}')
    if hasattr(result, 'valid_at') and result.valid_at:
        print(f'Valid from: {result.valid_at}')
    if hasattr(result, 'invalid_at') and result.invalid_at:
        print(f'Valid until: {result.invalid_at}')
    print('---')
```

### Center Node Search

For more contextually relevant results, you can use a center node to rerank search results based on their graph distance to a specific node. This is particularly useful for entity-specific queries as described in the [Searching the Graph](/graphiti/working-with-data/searching) page:

```python
# Use the top search result's UUID as the center node for reranking
if results and len(results) > 0:
    # Get the source node UUID from the top result
    center_node_uuid = results[0].source_node_uuid

    print('\nReranking search results based on graph distance:')
    print(f'Using center node UUID: {center_node_uuid}')

    reranked_results = await graphiti.search(
        'Who was the California Attorney General?', center_node_uuid=center_node_uuid
    )

    # Print reranked search results
    print('\nReranked Search Results:')
    for result in reranked_results:
        print(f'UUID: {result.uuid}')
        print(f'Fact: {result.fact}')
        if hasattr(result, 'valid_at') and result.valid_at:
            print(f'Valid from: {result.valid_at}')
        if hasattr(result, 'invalid_at') and result.invalid_at:
            print(f'Valid until: {result.invalid_at}')
        print('---')
else:
    print('No results found in the initial search to use as center node.')
```

### Node Search Using Search Recipes

Graphiti provides predefined search recipes optimized for different search scenarios. Here we use NODE\_HYBRID\_SEARCH\_RRF for retrieving nodes directly instead of edges. For a complete list of available search recipes and reranking approaches, see the [Configurable Search Strategies](/graphiti/working-with-data/searching#configurable-search-strategies) section in the Searching documentation:

```python
# Example: Perform a node search using _search method with standard recipes
print(
    '\nPerforming node search using _search method with standard recipe NODE_HYBRID_SEARCH_RRF:'
)

# Use a predefined search configuration recipe and modify its limit
node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
node_search_config.limit = 5  # Limit to 5 results

# Execute the node search
node_search_results = await graphiti._search(
    query='California Governor',
    config=node_search_config,
)

# Print node search results
print('\nNode Search Results:')
for node in node_search_results.nodes:
    print(f'Node UUID: {node.uuid}')
    print(f'Node Name: {node.name}')
    node_summary = node.summary[:100] + '...' if len(node.summary) > 100 else node.summary
    print(f'Content Summary: {node_summary}')
    print(f"Node Labels: {', '.join(node.labels)}")
    print(f'Created At: {node.created_at}')
    if hasattr(node, 'attributes') and node.attributes:
        print('Attributes:')
        for key, value in node.attributes.items():
            print(f'  {key}: {value}')
    print('---')
```

### Complete Example

For a complete working example that puts all these concepts together, check out the [Graphiti Quickstart Examples](https://github.com/getzep/graphiti/tree/main/examples/quickstart) on GitHub.

## Next Steps

Now that you've learned the basics of Graphiti, you can explore more advanced features:

* [Custom Entity and Edge Types](/graphiti/core-concepts/custom-entity-and-edge-types): Learn how to define and use custom entity and edge types to better model your domain-specific knowledge
* [Communities](/graphiti/core-concepts/communities): Discover how to work with communities, which are groups of related nodes that share common attributes or relationships
* [Advanced Search Techniques](/graphiti/working-with-data/searching): Explore more sophisticated search strategies, including different reranking approaches and configurable search recipes
* [Adding Fact Triples](/graphiti/working-with-data/adding-fact-triples): Learn how to directly add fact triples to your graph for more precise knowledge representation
* [Agent Integration](/graphiti/integrations/lang-graph-agent): Discover how to integrate Graphiti with LLM agents for more powerful AI applications

<Info>
  Make sure to run await statements within an [async function](https://docs.python.org/3/library/asyncio-task.html).
</Info>


# Knowledge Graph MCP Server

> A Knowledge Graph MCP Server for AI Assistants

<Card title="What is the Graphiti MCP Server?" icon="duotone server">
  The Graphiti MCP Server is an experimental implementation that exposes Graphiti's key functionality through the Model Context Protocol (MCP). This enables AI assistants like Claude Desktop and Cursor to interact with Graphiti's knowledge graph capabilities, providing persistent memory and contextual awareness.
</Card>

The Graphiti MCP Server bridges AI assistants with Graphiti's temporally-aware knowledge graphs, allowing assistants to maintain persistent memory across conversations and sessions. By integrating through MCP, assistants can automatically store, retrieve, and reason with information from their interactions.

## Key Features

The MCP server exposes Graphiti's core capabilities:

* **Episode Management**: Add, retrieve, and delete episodes (text, messages, or JSON data)
* **Entity Management**: Search and manage entity nodes and relationships
* **Search Capabilities**: Semantic and hybrid search for facts and node summaries
* **Group Management**: Organize data with group\_id filtering for multi-user scenarios
* **Graph Maintenance**: Clear graphs and rebuild indices as needed

## Quick Start with OpenAI

<Note>
  This quick start assumes you have OpenAI API access. For other LLM providers and detailed configuration options, see the [MCP Server README](https://github.com/getzep/graphiti/blob/main/mcp_server/README.md).
</Note>

### Prerequisites

Before getting started, ensure you have:

1. **Python 3.10+** installed on your system
2. **Neo4j database** (version 5.26 or later) running locally or accessible remotely
3. **OpenAI API key** for LLM operations and embeddings

### Installation

1. Clone the Graphiti repository:

```bash
git clone https://github.com/getzep/graphiti.git
cd graphiti
```

2. Navigate to the MCP server directory and install dependencies:

```bash
cd mcp_server
uv sync
```

### Configuration

Set up your environment variables in a `.env` file:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o-mini

# Neo4j Configuration (adjust as needed)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### Running the Server

Start the MCP server:

```bash
uv run graphiti_mcp_server.py
```

For development with custom options:

```bash
uv run graphiti_mcp_server.py --model gpt-4o-mini --transport sse --group-id my-project
```

## MCP Client Integration

### Claude Desktop

Configure Claude Desktop to connect via the stdio transport:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "stdio",
      "command": "/path/to/uv",
      "args": [
        "run",
        "--directory",
        "/path/to/graphiti/mcp_server",
        "graphiti_mcp_server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENAI_API_KEY": "your_api_key",
        "MODEL_NAME": "gpt-4o-mini",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    }
  }
}
```

### Cursor IDE

For Cursor, use the SSE transport configuration:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Available Tools

Once connected, AI assistants have access to these Graphiti tools:

* `add_memory` - Store episodes and interactions in the knowledge graph
* `search_facts` - Find relevant facts and relationships
* `search_nodes` - Search for entity summaries and information
* `get_episodes` - Retrieve recent episodes for context
* `delete_episode` - Remove episodes from the graph
* `clear_graph` - Reset the knowledge graph entirely

## Docker Deployment

For containerized deployment, use the provided Docker Compose setup:

```bash
docker compose up
```

This starts both Neo4j and the MCP server with SSE transport enabled.

## Next Steps

For comprehensive configuration options, advanced features, and troubleshooting:

* **Full Documentation**: See the complete [MCP Server README](https://github.com/getzep/graphiti/blob/main/mcp_server/README.md)
* **Integration Examples**: Explore client-specific setup guides for Claude Desktop and Cursor
* **Custom Entity Types**: Configure domain-specific entity extraction
* **Multi-tenant Setup**: Use group IDs for organizing data across different contexts

<Warning>
  The MCP server is experimental and under active development. Features and APIs may change between releases.
</Warning>


# LLM Configuration

> Configure Graphiti with different LLM providers

<Note>
  Graphiti works best with LLM services that support Structured Output (such as OpenAI and Gemini). Using other services may result in incorrect output schemas and ingestion failures, particularly when using smaller models.
</Note>

Graphiti defaults to using OpenAI for LLM inference and embeddings, but supports multiple LLM providers including Azure OpenAI, Google Gemini, Anthropic, Groq, and local models via Ollama. This guide covers configuring Graphiti with alternative LLM providers.

## Azure OpenAI

<Warning>
  **Azure OpenAI v1 API Opt-in Required for Structured Outputs**

  Graphiti uses structured outputs via the `client.beta.chat.completions.parse()` method, which requires Azure OpenAI deployments to opt into the v1 API. Without this opt-in, you'll encounter 404 Resource not found errors during episode ingestion.

  To enable v1 API support in your Azure OpenAI deployment, follow Microsoft's guide: [Azure OpenAI API version lifecycle](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/api-version-lifecycle?tabs=key#api-evolution).
</Warning>

Azure OpenAI deployments often require different endpoints for LLM and embedding services, and separate deployments for default and small models.

### Installation

```bash
pip install graphiti-core
```

### Configuration

```python
from openai import AsyncAzureOpenAI
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

# Azure OpenAI configuration - use separate endpoints for different services
api_key = "<your-api-key>"
api_version = "<your-api-version>"
llm_endpoint = "<your-llm-endpoint>"  # e.g., "https://your-llm-resource.openai.azure.com/"
embedding_endpoint = "<your-embedding-endpoint>"  # e.g., "https://your-embedding-resource.openai.azure.com/"

# Create separate Azure OpenAI clients for different services
llm_client_azure = AsyncAzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=llm_endpoint
)

embedding_client_azure = AsyncAzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=embedding_endpoint
)

# Create LLM Config with your Azure deployment names
azure_llm_config = LLMConfig(
    small_model="gpt-4.1-nano",
    model="gpt-4.1-mini",
)

# Initialize Graphiti with Azure OpenAI clients
graphiti = Graphiti(
    "bolt://localhost:7687",
    "neo4j",
    "password",
    llm_client=OpenAIClient(
        config=azure_llm_config,
        client=llm_client_azure
    ),
    embedder=OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model="text-embedding-3-small-deployment"  # Your Azure embedding deployment name
        ),
        client=embedding_client_azure
    ),
    cross_encoder=OpenAIRerankerClient(
        config=LLMConfig(
            model=azure_llm_config.small_model  # Use small model for reranking
        ),
        client=llm_client_azure
    )
)
```

Make sure to replace the placeholder values with your actual Azure OpenAI credentials and deployment names.

### Environment Variables

Azure OpenAI can also be configured using environment variables:

* `AZURE_OPENAI_ENDPOINT` - Azure OpenAI LLM endpoint URL
* `AZURE_OPENAI_DEPLOYMENT_NAME` - Azure OpenAI LLM deployment name
* `AZURE_OPENAI_API_VERSION` - Azure OpenAI API version
* `AZURE_OPENAI_EMBEDDING_API_KEY` - Azure OpenAI Embedding deployment key (if different from `OPENAI_API_KEY`)
* `AZURE_OPENAI_EMBEDDING_ENDPOINT` - Azure OpenAI Embedding endpoint URL
* `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` - Azure OpenAI embedding deployment name
* `AZURE_OPENAI_EMBEDDING_API_VERSION` - Azure OpenAI embedding API version
* `AZURE_OPENAI_USE_MANAGED_IDENTITY` - Use Azure Managed Identities for authentication

## Google Gemini

Google's Gemini models provide excellent structured output support and can be used for LLM inference, embeddings, and cross-encoding/reranking.

### Installation

```bash
pip install "graphiti-core[google-genai]"
```

### Configuration

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client.gemini_client import GeminiClient, LLMConfig
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient

# Google API key configuration
api_key = "<your-google-api-key>"

# Initialize Graphiti with Gemini clients
graphiti = Graphiti(
    "bolt://localhost:7687",
    "neo4j",
    "password",
    llm_client=GeminiClient(
        config=LLMConfig(
            api_key=api_key,
            model="gemini-2.0-flash"
        )
    ),
    embedder=GeminiEmbedder(
        config=GeminiEmbedderConfig(
            api_key=api_key,
            embedding_model="embedding-001"
        )
    ),
    cross_encoder=GeminiRerankerClient(
        config=LLMConfig(
            api_key=api_key,
            model="gemini-2.0-flash-exp"
        )
    )
)
```

The Gemini reranker uses the `gemini-2.0-flash-exp` model by default, which is optimized for cost-effective and low-latency classification tasks.

### Environment Variables

Google Gemini can be configured using:

* `GOOGLE_API_KEY` - Your Google API key

## Anthropic

Anthropic's Claude models can be used for LLM inference with OpenAI embeddings and reranking.

<Warning>
  When using Anthropic for LLM inference, you still need an OpenAI API key for embeddings and reranking functionality. Make sure to set both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` environment variables.
</Warning>

### Installation

```bash
pip install "graphiti-core[anthropic]"
```

### Configuration

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client.anthropic_client import AnthropicClient, LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

# Configure Anthropic LLM with OpenAI embeddings and reranking
graphiti = Graphiti(
    "bolt://localhost:7687",
    "neo4j", 
    "password",
    llm_client=AnthropicClient(
        config=LLMConfig(
            api_key="<your-anthropic-api-key>",
            model="claude-sonnet-4-20250514",
            small_model="claude-3-5-haiku-20241022"
        )
    ),
    embedder=OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            api_key="<your-openai-api-key>",
            embedding_model="text-embedding-3-small"
        )
    ),
    cross_encoder=OpenAIRerankerClient(
        config=LLMConfig(
            api_key="<your-openai-api-key>",
            model="gpt-4.1-nano"  # Use a smaller model for reranking
        )
    )
)
```

### Environment Variables

Anthropic can be configured using:

* `ANTHROPIC_API_KEY` - Your Anthropic API key
* `OPENAI_API_KEY` - Required for embeddings and reranking

## Groq

Groq provides fast inference with various open-source models, using OpenAI for embeddings and reranking.

<Warning>
  When using Groq, avoid smaller models as they may not accurately extract data or output the correct JSON structures required by Graphiti. Use larger, more capable models like Llama 3.1 70B for best results.
</Warning>

### Installation

```bash
pip install "graphiti-core[groq]"
```

### Configuration

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client.groq_client import GroqClient, LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

# Configure Groq LLM with OpenAI embeddings and reranking
graphiti = Graphiti(
    "bolt://localhost:7687",
    "neo4j",
    "password", 
    llm_client=GroqClient(
        config=LLMConfig(
            api_key="<your-groq-api-key>",
            model="llama-3.1-70b-versatile",
            small_model="llama-3.1-8b-instant"
        )
    ),
    embedder=OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            api_key="<your-openai-api-key>",
            embedding_model="text-embedding-3-small"
        )
    ),
    cross_encoder=OpenAIRerankerClient(
        config=LLMConfig(
            api_key="<your-openai-api-key>",
            model="gpt-4.1-nano"  # Use a smaller model for reranking
        )
    )
)
```

### Environment Variables

Groq can be configured using:

* `GROQ_API_KEY` - Your Groq API key
* `OPENAI_API_KEY` - Required for embeddings

## Ollama (Local LLMs)

Ollama enables running local LLMs and embedding models via its OpenAI-compatible API, ideal for privacy-focused applications or avoiding API costs.

<Warning>
  When using Ollama, avoid smaller local models as they may not accurately extract data or output the correct JSON structures required by Graphiti. Use larger, more capable models and ensure they support structured output for reliable knowledge graph construction.
</Warning>

### Installation

First, install and configure Ollama:

```bash
# Install Ollama (visit https://ollama.ai for installation instructions)
# Then pull the models you want to use:
ollama pull deepseek-r1:7b     # LLM
ollama pull nomic-embed-text   # embeddings
```

### Configuration

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

# Configure Ollama LLM client
llm_config = LLMConfig(
    api_key="abc",  # Ollama doesn't require a real API key
    model="deepseek-r1:7b",
    small_model="deepseek-r1:7b",
    base_url="http://localhost:11434/v1",  # Ollama provides this port
)

llm_client = OpenAIClient(config=llm_config)

# Initialize Graphiti with Ollama clients
graphiti = Graphiti(
    "bolt://localhost:7687",
    "neo4j",
    "password",
    llm_client=llm_client,
    embedder=OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            api_key="abc",
            embedding_model="nomic-embed-text",
            embedding_dim=768,
            base_url="http://localhost:11434/v1",
        )
    ),
    cross_encoder=OpenAIRerankerClient(client=llm_client, config=llm_config),
)
```

Ensure Ollama is running (`ollama serve`) and that you have pulled the models you want to use.

## OpenAI Compatible Services

Many LLM providers offer OpenAI-compatible APIs. Use the `OpenAIGenericClient` for these services, which ensures proper schema injection for JSON output since most providers don't support OpenAI's structured output format.

<Warning>
  When using OpenAI-compatible services, avoid smaller models as they may not accurately extract data or output the correct JSON structures required by Graphiti. Choose larger, more capable models that can handle complex reasoning and structured output.
</Warning>

### Installation

```bash
pip install graphiti-core
```

### Configuration

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

# Configure OpenAI-compatible service
llm_config = LLMConfig(
    api_key="<your-api-key>",
    model="<your-main-model>",        # e.g., "mistral-large-latest"
    small_model="<your-small-model>", # e.g., "mistral-small-latest"
    base_url="<your-base-url>",       # e.g., "https://api.mistral.ai/v1"
)

# Initialize Graphiti with OpenAI-compatible service
graphiti = Graphiti(
    "bolt://localhost:7687",
    "neo4j",
    "password",
    llm_client=OpenAIGenericClient(config=llm_config),
    embedder=OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            api_key="<your-api-key>",
            embedding_model="<your-embedding-model>", # e.g., "mistral-embed"
            base_url="<your-base-url>",
        )
    ),
    cross_encoder=OpenAIRerankerClient(
        config=LLMConfig(
            api_key="<your-api-key>",
            model="<your-small-model>",  # Use smaller model for reranking
            base_url="<your-base-url>",
        )
    )
)
```

Replace the placeholder values with your actual service credentials and model names.


# Neo4j Configuration

> Configure Neo4j as the graph provider for Graphiti

Neo4j is the primary graph database backend for Graphiti. Version 5.26 or higher is required for full functionality.

## Neo4j Community Edition

Neo4j Community Edition is free and suitable for development, testing, and smaller production workloads.

### Installation via Neo4j Desktop

The simplest way to install Neo4j is via [Neo4j Desktop](https://neo4j.com/download/), which provides a user-friendly interface to manage Neo4j instances and databases.

1. Download and install Neo4j Desktop
2. Create a new project
3. Add a new database (Local DBMS)
4. Set a password for the `neo4j` user
5. Start the database

### Docker Installation

For containerized deployments:

```bash
docker run \
    --name neo4j-community \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -e NEO4J_PLUGINS='["apoc"]' \
    neo4j:5.26-community
```

### Configuration

Set the following environment variables:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password
```

### Connection in Python

```python
from graphiti_core import Graphiti

graphiti = Graphiti(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)
```

## Neo4j AuraDB (Cloud)

Neo4j AuraDB is a fully managed cloud service that handles infrastructure, backups, and updates automatically.

### Setup

1. Sign up for [Neo4j Aura](https://neo4j.com/cloud/platform/aura-graph-database/)
2. Create a new AuraDB instance
3. Note down the connection URI and credentials
4. Download the connection details or copy the connection string

### Configuration

AuraDB connections use the `neo4j+s://` protocol for secure connections:

```bash
export NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_generated_password
```

### Connection in Python

```python
from graphiti_core import Graphiti

graphiti = Graphiti(
    neo4j_uri="neo4j+s://your-instance.databases.neo4j.io",
    neo4j_user="neo4j",
    neo4j_password="your_generated_password"
)
```

<Note>
  AuraDB instances automatically include APOC procedures. No additional configuration is required for most Graphiti operations.
</Note>

## Neo4j Enterprise Edition

Neo4j Enterprise Edition provides advanced features including clustering, hot backups, and performance optimizations.

### Installation

Enterprise Edition requires a commercial license. Installation options include:

* **Neo4j Desktop**: Add Enterprise Edition license key
* **Docker**: Use `neo4j:5.26-enterprise` image with license
* **Server Installation**: Download from Neo4j website with valid license

### Docker with Enterprise Features

```bash
docker run \
    --name neo4j-enterprise \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -e NEO4J_PLUGINS='["apoc"]' \
    -e NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
    neo4j:5.26-enterprise
```

### Parallel Runtime Configuration

Enterprise Edition supports parallel runtime for improved query performance:

```bash
export USE_PARALLEL_RUNTIME=true
```

<Warning>
  The `USE_PARALLEL_RUNTIME` feature is only available in Neo4j Enterprise Edition and larger AuraDB instances. It is not supported in Community Edition or smaller AuraDB instances.
</Warning>

### Connection in Python

```python
import os
from graphiti_core import Graphiti

# Enable parallel runtime for Enterprise Edition
os.environ['USE_PARALLEL_RUNTIME'] = 'true'

graphiti = Graphiti(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)
```


# FalkorDB Configuration

> Configure FalkorDB as the graph provider for Graphiti

FalkorDB configuration requires version 1.1.2 or higher.

## Installation

Install Graphiti with FalkorDB support:

```bash
pip install graphiti-core[falkordb]
```

or

```bash
uv add graphiti-core[falkordb]
```

## Docker Installation

The simplest way to run FalkorDB is via Docker:

```bash
docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
```

This command:

* Exposes FalkorDB on port 6379 (Redis protocol)
* Provides a web interface on port 3000
* Runs in foreground mode for easy testing

## Configuration

Set the following environment variables for FalkorDB (optional):

```bash
export FALKORDB_HOST=localhost          # Default: localhost
export FALKORDB_PORT=6379              # Default: 6379
export FALKORDB_USERNAME=              # Optional: usually not required
export FALKORDB_PASSWORD=              # Optional: usually not required
```

## Connection in Python

```python
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

# FalkorDB connection using FalkorDriver
falkor_driver = FalkorDriver(
    host='localhost',        # or os.environ.get('FALKORDB_HOST', 'localhost')
    port='6379',            # or os.environ.get('FALKORDB_PORT', '6379')
    username=None,          # or os.environ.get('FALKORDB_USERNAME', None)
    password=None           # or os.environ.get('FALKORDB_PASSWORD', None)
)

graphiti = Graphiti(graph_driver=falkor_driver)
```

<Note>
  FalkorDB uses a dedicated `FalkorDriver` and connects via Redis protocol on port 6379. Unlike Neo4j, authentication is typically not required for local FalkorDB instances.
</Note>


# AWS Neptune Configuration

> Configure Amazon Neptune as the graph provider for Graphiti

Neptune DB is Amazon's fully managed graph database service that supports both property graph and RDF data models. Graphiti integrates with Neptune to provide scalable, cloud-native graph storage with automatic backups, encryption, and high availability.

## Prerequisites

Neptune DB integration requires both Neptune and Amazon OpenSearch Serverless (AOSS) services:

* **Neptune Service**: For graph data storage and Cypher query processing
* **OpenSearch Serverless**: For text search and hybrid retrieval functionality
* **AWS Credentials**: Configured via AWS CLI, environment variables, or IAM roles

For detailed setup instructions, see:

* [AWS Neptune Developer Resources](https://aws.amazon.com/neptune/developer-resources/)
* [Neptune Database Documentation](https://docs.aws.amazon.com/neptune/latest/userguide/)
* [Neptune Analytics Documentation](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/)
* [OpenSearch Serverless Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)

## Setup

1. Create a Neptune Database cluster in the AWS Console or via CloudFormation
2. Create an OpenSearch Serverless collection for text search
3. Configure VPC networking and security groups to allow communication between services
4. Note your Neptune cluster endpoint and OpenSearch collection endpoint

## Configuration

Set the following environment variables:

```bash
export NEPTUNE_HOST=your-neptune-cluster.cluster-xyz.us-west-2.neptune.amazonaws.com
export NEPTUNE_PORT=8182  # Optional, defaults to 8182
export AOSS_HOST=your-collection.us-west-2.aoss.amazonaws.com
```

## Installation

Install the required dependencies:

```bash
pip install graphiti-core[neptune]
```

or

```bash
uv add graphiti-core[neptune]
```

## Connection in Python

```python
import os
from graphiti_core import Graphiti
from graphiti_core.driver.neptune_driver import NeptuneDriver

# Get connection parameters from environment
neptune_uri = os.getenv('NEPTUNE_HOST')
neptune_port = int(os.getenv('NEPTUNE_PORT', 8182))
aoss_host = os.getenv('AOSS_HOST')

# Validate required parameters
if not neptune_uri or not aoss_host:
    raise ValueError("NEPTUNE_HOST and AOSS_HOST environment variables must be set")

# Create Neptune driver
driver = NeptuneDriver(
    host=neptune_uri,        # Required: Neptune cluster endpoint
    aoss_host=aoss_host,     # Required: OpenSearch Serverless collection endpoint
    port=neptune_port        # Optional: Neptune port (defaults to 8182)
)

# Pass the driver to Graphiti
graphiti = Graphiti(graph_driver=driver)
```


# Kuzu DB Configuration

> Configure Kuzu as the graph provider for Graphiti

Kuzu is an embedded graph engine that does not require any additional setup. You can enable the Kuzu driver by installing graphiti with the Kuzu extra:

```bash
pip install graphiti-core[kuzu]
```

## Configuration

Set the following environment variables for Kuzu (optional):

```bash
export KUZU_DB=/path/to/graphiti.kuzu          # Default: :memory:
```

## Connection in Python

```python
from graphiti_core import Graphiti
from graphiti_core.driver.kuzu_driver import KuzuDriver

# Kuzu connection using KuzuDriver
kuzu_driver = KuzuDriver(
    db='/path/to/graphiti.kuzu'        # or os.environ.get('KUZU_DB', ':memory:')
)

graphiti = Graphiti(graph_driver=kuzu_driver)
```


# Adding Episodes

> How to add data to your Graphiti graph

<Note>
  Refer to the [Custom Entity Types](/graphiti/core-concepts/custom-entity-and-edge-types) page for detailed instructions on adding user-defined ontology to your graph.
</Note>

### Adding Episodes

Episodes represent a single data ingestion event. An `episode` is itself a node, and any nodes identified while ingesting the
episode are related to the episode via `MENTIONS` edges.

Episodes enable querying for information at a point in time and understanding the provenance of nodes and their edge relationships.

Supported episode types:

* `text`: Unstructured text data
* `message`: Conversational messages of the format `speaker: message...`
* `json`: Structured data, processed distinctly from the other types

The graph below was generated using the code in the [Quick Start](/graphiti/getting-started/quick-start). Each **podcast** is an individual episode.

![Simple Graph Visualization](https://raw.githubusercontent.com/getzep/graphiti/main/images/simple_graph.svg)

#### Adding a `text` or `message` Episode

Using the `EpisodeType.text` type:

```python
await graphiti.add_episode(
    name="tech_innovation_article",
    episode_body=(
        "MIT researchers have unveiled 'ClimateNet', an AI system capable of predicting "
        "climate patterns with unprecedented accuracy. Early tests show it can forecast "
        "major weather events up to three weeks in advance, potentially revolutionizing "
        "disaster preparedness and agricultural planning."
    ),
    source=EpisodeType.text,
    # A description of the source (e.g., "podcast", "news article")
    source_description="Technology magazine article",
    # The timestamp for when this episode occurred or was created
    reference_time=datetime(2023, 11, 15, 9, 30),
)
```

Using the `EpisodeType.message` type supports passing in multi-turn conversations in the `episode_body`.

The text should be structured in `{role/name}: {message}` pairs.

```python
await graphiti.add_episode(
    name="Customer_Support_Interaction_1",
    episode_body=(
        "Customer: Hi, I'm having trouble with my Allbirds shoes. "
        "The sole is coming off after only 2 months of use.\n"
        "Support: I'm sorry to hear that. Can you please provide your order number?"
    ),
    source=EpisodeType.message,
    source_description="Customer support chat",
    reference_time=datetime(2024, 3, 15, 14, 45),
)
```

#### Adding an Episode using structured data in JSON format

JSON documents can be arbitrarily nested. However, it's advisable to keep documents compact, as they must fit within your LLM's context window.

<Note>
  For large data imports, consider using the `add_episode_bulk` API to
  efficiently add multiple episodes at once.
</Note>

```python
product_data = {
    "id": "PROD001",
    "name": "Men's SuperLight Wool Runners",
    "color": "Dark Grey",
    "sole_color": "Medium Grey",
    "material": "Wool",
    "technology": "SuperLight Foam",
    "price": 125.00,
    "in_stock": True,
    "last_updated": "2024-03-15T10:30:00Z"
}

# Add the episode to the graph
await graphiti.add_episode(
    name="Product Update - PROD001",
    episode_body=product_data,  # Pass the Python dictionary directly
    source=EpisodeType.json,
    source_description="Allbirds product catalog update",
    reference_time=datetime.now(),
)
```

#### Loading Episodes in Bulk

Graphiti offers `add_episode_bulk` for efficient batch ingestion of episodes, significantly outperforming `add_episode` for large datasets. This method is highly recommended for bulk loading.

<Warning>
  Use `add_episode_bulk` only for populating empty graphs or when edge invalidation is not required. The bulk ingestion pipeline does not perform edge invalidation operations.
</Warning>

```python
product_data = [
    {
        "id": "PROD001",
        "name": "Men's SuperLight Wool Runners",
        "color": "Dark Grey",
        "sole_color": "Medium Grey",
        "material": "Wool",
        "technology": "SuperLight Foam",
        "price": 125.00,
        "in_stock": true,
        "last_updated": "2024-03-15T10:30:00Z"
    },
    ...
    {
        "id": "PROD0100",
        "name": "Kids Wool Runner-up Mizzles",
        "color": "Natural Grey",
        "sole_color": "Orange",
        "material": "Wool",
        "technology": "Water-repellent",
        "price": 80.00,
        "in_stock": true,
        "last_updated": "2024-03-17T14:45:00Z"
    }
]

# Prepare the episodes for bulk loading

bulk_episodes = [
RawEpisode(
name=f"Product Update - {product['id']}",
content=json.dumps(product),
source=EpisodeType.json,
source_description="Allbirds product catalog update",
reference_time=datetime.now()
)
for product in product_data
]

await graphiti.add_episode_bulk(bulk_episodes)

```

```
```


# Custom Entity and Edge Types

> Enhancing Graphiti with Custom Ontologies

Graphiti allows you to define custom entity types and edge types to better represent your domain-specific knowledge. This enables more structured data extraction and richer semantic relationships in your knowledge graph.

## Defining Custom Entity and Edge Types

Custom entity types and edge types are defined using Pydantic models. Each model represents a specific type with custom attributes.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Custom Entity Types
class Person(BaseModel):
    """A person entity with biographical information."""
    age: Optional[int] = Field(None, description="Age of the person")
    occupation: Optional[str] = Field(None, description="Current occupation")
    location: Optional[str] = Field(None, description="Current location")
    birth_date: Optional[datetime] = Field(None, description="Date of birth")

class Company(BaseModel):
    """A business organization."""
    industry: Optional[str] = Field(None, description="Primary industry")
    founded_year: Optional[int] = Field(None, description="Year company was founded")
    headquarters: Optional[str] = Field(None, description="Location of headquarters")
    employee_count: Optional[int] = Field(None, description="Number of employees")

class Product(BaseModel):
    """A product or service."""
    category: Optional[str] = Field(None, description="Product category")
    price: Optional[float] = Field(None, description="Price in USD")
    release_date: Optional[datetime] = Field(None, description="Product release date")

# Custom Edge Types
class Employment(BaseModel):
    """Employment relationship between a person and company."""
    position: Optional[str] = Field(None, description="Job title or position")
    start_date: Optional[datetime] = Field(None, description="Employment start date")
    end_date: Optional[datetime] = Field(None, description="Employment end date")
    salary: Optional[float] = Field(None, description="Annual salary in USD")
    is_current: Optional[bool] = Field(None, description="Whether employment is current")

class Investment(BaseModel):
    """Investment relationship between entities."""
    amount: Optional[float] = Field(None, description="Investment amount in USD")
    investment_type: Optional[str] = Field(None, description="Type of investment (equity, debt, etc.)")
    stake_percentage: Optional[float] = Field(None, description="Percentage ownership")
    investment_date: Optional[datetime] = Field(None, description="Date of investment")

class Partnership(BaseModel):
    """Partnership relationship between companies."""
    partnership_type: Optional[str] = Field(None, description="Type of partnership")
    duration: Optional[str] = Field(None, description="Expected duration")
    deal_value: Optional[float] = Field(None, description="Financial value of partnership")
```

## Using Custom Entity and Edge Types

Pass your custom entity types and edge types to the add\_episode method:

```python
entity_types = {
    "Person": Person,
    "Company": Company,
    "Product": Product
}

edge_types = {
    "Employment": Employment,
    "Investment": Investment,
    "Partnership": Partnership
}

edge_type_map = {
    ("Person", "Company"): ["Employment"],
    ("Company", "Company"): ["Partnership", "Investment"],
    ("Person", "Person"): ["Partnership"],
    ("Entity", "Entity"): ["Investment"],  # Apply to any entity type
}

await graphiti.add_episode(
    name="Business Update",
    episode_body="Sarah joined TechCorp as CTO in January 2023 with a $200K salary. TechCorp partnered with DataCorp in a $5M deal.",
    source_description="Business news",
    reference_time=datetime.now(),
    entity_types=entity_types,
    edge_types=edge_types,
    edge_type_map=edge_type_map
)
```

## Searching with Custom Types

You can filter search results to specific entity types or edge types using SearchFilters:

```python
from graphiti_core.search.search_filters import SearchFilters

# Search for only specific entity types
search_filter = SearchFilters(
    node_labels=["Person", "Company"]  # Only return Person and Company entities
)

results = await graphiti.search_(
    query="Who works at tech companies?",
    search_filter=search_filter
)

# Search for only specific edge types
search_filter = SearchFilters(
    edge_types=["Employment", "Partnership"]  # Only return Employment and Partnership edges
)

results = await graphiti.search_(
    query="Tell me about business relationships",
    search_filter=search_filter
)
```

## How Custom Types Work

### Entity Extraction Process

1. **Extraction**: Graphiti extracts entities from text and classifies them using your custom types
2. **Validation**: Each entity is validated against the appropriate Pydantic model
3. **Attribute Population**: Custom attributes are extracted from the text and populated
4. **Storage**: Entities are stored with their custom attributes

### Edge Extraction Process

1. **Relationship Detection**: Graphiti identifies relationships between extracted entities
2. **Type Classification**: Based on the entity types involved and your edge\_type\_map, relationships are classified
3. **Attribute Extraction**: For custom edge types, additional attributes are extracted from the context
4. **Validation**: Edge attributes are validated against the Pydantic model
5. **Storage**: Edges are stored with their custom attributes and relationship metadata

## Edge Type Mapping

The edge\_type\_map parameter defines which edge types can exist between specific entity type pairs:

```python
edge_type_map = {
    ("Person", "Company"): ["Employment"],
    ("Company", "Company"): ["Partnership", "Investment"],
    ("Person", "Person"): ["Partnership"],
    ("Entity", "Entity"): ["Investment"],  # Apply to any entity type
}
```

If an entity pair doesn't have a defined edge type mapping, Graphiti will use default relationship types and the relationship will still be captured with a generic RELATES\_TO type.

## Schema Evolution

Your knowledge graph's schema can evolve over time as your needs change. You can update entity types by adding new attributes to existing types without breaking existing nodes. When you add new attributes, existing nodes will preserve their original attributes while supporting the new ones for future updates. This flexible approach allows your knowledge graph to grow and adapt while maintaining backward compatibility with historical data.

For example, if you initially defined a "Customer" type with basic attributes like name and email, you could later add attributes like "loyalty\_tier" or "acquisition\_channel" without needing to modify or migrate existing customer nodes in your graph.

## Best Practices

### Model Design

* **Clear Descriptions**: Always include detailed descriptions in docstrings and Field descriptions
* **Optional Fields**: Make custom attributes optional to handle cases where information isn't available
* **Appropriate Types**: Use specific types (datetime, int, float) rather than strings when possible
* **Validation**: Consider adding Pydantic validators for complex validation rules
* **Atomic Attributes**: Attributes should be broken down into their smallest meaningful units rather than storing compound information

```python
from pydantic import validator

class Person(BaseModel):
    """A person entity."""
    age: Optional[int] = Field(None, description="Age in years")
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v
```

**Instead of compound information:**

```python
class Customer(BaseModel):
    contact_info: Optional[str] = Field(None, description="Name and email")  # Don't do this
```

**Use atomic attributes:**

```python
class Customer(BaseModel):
    name: Optional[str] = Field(None, description="Customer name")
    email: Optional[str] = Field(None, description="Customer email address")
```

### Naming Conventions

* **Entity Types**: Use PascalCase (e.g., Person, TechCompany)
* **Edge Types**: Use PascalCase for custom types (e.g., Employment, Partnership)
* **Attributes**: Use snake\_case (e.g., start\_date, employee\_count)
* **Descriptions**: Be specific and actionable for the LLM
* **Consistency**: Maintain consistent naming conventions across related entity types

### Edge Type Mapping Strategy

* **Specific Mappings**: Define specific entity type pairs for targeted relationships
* **Fallback to Entity**: Use ("Entity", "Entity") as a fallback for general relationships
* **Balanced Scope**: Don't make edge types too specific or too general
* **Domain Coverage**: Ensure your edge types cover the main relationships in your domain

```python
# Good: Specific and meaningful
edge_type_map = {
    ("Person", "Company"): ["Employment", "Investment"],
    ("Company", "Company"): ["Partnership", "Acquisition"],
    ("Person", "Product"): ["Usage", "Review"],
    ("Entity", "Entity"): ["RELATES_TO"]  # Fallback for unexpected relationships
}

# Avoid: Too granular
edge_type_map = {
    ("CEO", "TechCompany"): ["CEOEmployment"],
    ("Engineer", "TechCompany"): ["EngineerEmployment"],
    # This creates too many specific types
}
```

## Entity Type Exclusion

You can exclude specific entity types from extraction using the excluded\_entity\_types parameter:

```python
await graphiti.add_episode(
    name="Business Update",
    episode_body="The meeting discussed various topics including weather and sports.",
    source_description="Meeting notes",
    reference_time=datetime.now(),
    entity_types=entity_types,
    excluded_entity_types=["Person"]  # Won't extract Person entities
)
```

## Migration Guide

If you're upgrading from a previous version of Graphiti:

* You can add entity types to new episodes, even if existing episodes in the graph did not have entity types. Existing nodes will continue to work without being classified.
* To add types to previously ingested data, you need to re-ingest it with entity types set into a new graph.

## Important Constraints

### Protected Attribute Names

Custom entity type attributes cannot use protected names that are already used by Graphiti's core EntityNode class:

* `uuid`, `name`, `group_id`, `labels`, `created_at`, `summary`, `attributes`, `name_embedding`

Custom entity types and edge types provide powerful ways to structure your knowledge graph according to your domain needs. They enable more precise extraction, better organization, and richer semantic relationships in your data.


# Communities

> How to create and update communities

In Graphiti, communities (represented as `CommunityNode` objects) represent groups of related entity nodes.
Communities can be generated using the `build_communities` method on the graphiti class.

```python
await graphiti.build_communities()
```

Communities are determined using the Leiden algorithm, which groups strongly connected nodes together.
Communities contain a summary field that collates the summaries held on each of its member entities.
This allows Graphiti to provide high-level synthesized information about what the graph contains in addition to the more granular facts stored on edges.

Once communities are built, they can also be updated with new episodes by passing in `update_communities=True` to the `add_episode` method.
If a new node is added to the graph, we will determine which community it should be added to based on the most represented community of the new node's surrounding nodes.
This updating methodology is inspired by the label propagation algorithm for determining communities.
However, we still recommend periodically rebuilding communities to ensure the most optimal grouping.
Whenever the `build_communities` method is called it will remove any existing communities before creating new ones.


# Graph Namespacing

> Using group_ids to create isolated graph namespaces

## Overview

Graphiti supports the concept of graph namespacing through the use of `group_id` parameters. This feature allows you to create isolated graph environments within the same Graphiti instance, enabling multiple distinct knowledge graphs to coexist without interference.

Graph namespacing is particularly useful for:

* **Multi-tenant applications**: Isolate data between different customers or organizations
* **Testing environments**: Maintain separate development, testing, and production graphs
* **Domain-specific knowledge**: Create specialized graphs for different domains or use cases
* **Team collaboration**: Allow different teams to work with their own graph spaces

## How Namespacing Works

In Graphiti, every node and edge can be associated with a `group_id`. When you specify a `group_id`, you're effectively creating a namespace for that data. Nodes and edges with the same `group_id` form a cohesive, isolated graph that can be queried and manipulated independently from other namespaces.

### Key Benefits

* **Data isolation**: Prevent data leakage between different namespaces
* **Simplified management**: Organize and manage related data together
* **Performance optimization**: Improve query performance by limiting the search space
* **Flexible architecture**: Support multiple use cases within a single Graphiti instance

## Using group\_ids in Graphiti

### Adding Episodes with group\_id

When adding episodes to your graph, you can specify a `group_id` to namespace the episode and all its extracted entities:

```python
await graphiti.add_episode(
    name="customer_interaction",
    episode_body="Customer Jane mentioned she loves our new SuperLight Wool Runners in Dark Grey.",
    source=EpisodeType.text,
    source_description="Customer feedback",
    reference_time=datetime.now(),
    group_id="customer_team"  # This namespaces the episode and its entities
)
```

### Adding Fact Triples with group\_id

When manually adding fact triples, ensure both nodes and the edge share the same `group_id`:

```python
from graphiti_core.nodes import EntityNode
from graphiti_core.edges import EntityEdge
import uuid
from datetime import datetime

# Define a namespace for this data
namespace = "product_catalog"

# Create source and target nodes with the namespace
source_node = EntityNode(
    uuid=str(uuid.uuid4()),
    name="SuperLight Wool Runners",
    group_id=namespace  # Apply namespace to source node
)

target_node = EntityNode(
    uuid=str(uuid.uuid4()),
    name="Sustainable Footwear",
    group_id=namespace  # Apply namespace to target node
)

# Create an edge with the same namespace
edge = EntityEdge(
    group_id=namespace,  # Apply namespace to edge
    source_node_uuid=source_node.uuid,
    target_node_uuid=target_node.uuid,
    created_at=datetime.now(),
    name="is_category_of",
    fact="SuperLight Wool Runners is a product in the Sustainable Footwear category"
)

# Add the triplet to the graph
await graphiti.add_triplet(source_node, edge, target_node)
```

### Querying Within a Namespace

When querying the graph, specify the `group_id` to limit results to a particular namespace:

```python
# Search within a specific namespace
search_results = await graphiti.search(
    query="Wool Runners",
    group_id="product_catalog"  # Only search within this namespace
)

# For more advanced node-specific searches, use the _search method with a recipe
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

# Create a search config for nodes only
node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
node_search_config.limit = 5  # Limit to 5 results

# Execute the node search within a specific namespace
node_search_results = await graphiti._search(
    query="SuperLight Wool Runners",
    group_id="product_catalog",  # Only search within this namespace
    config=node_search_config
)
```

## Best Practices for Graph Namespacing

1. **Consistent naming**: Use a consistent naming convention for your `group_id` values
2. **Documentation**: Maintain documentation of your namespace structure and purpose
3. **Granularity**: Choose an appropriate level of granularity for your namespaces
   * Too many namespaces can lead to fragmented data
   * Too few namespaces may not provide sufficient isolation
4. **Cross-namespace queries**: When necessary, perform multiple queries across namespaces and combine results in your application logic

## Example: Multi-tenant Application

Here's an example of using namespacing in a multi-tenant application:

```python
async def add_customer_data(tenant_id, customer_data):
    """Add customer data to a tenant-specific namespace"""
    
    # Use the tenant_id as the namespace
    namespace = f"tenant_{tenant_id}"
    
    # Create an episode for this customer data
    await graphiti.add_episode(
        name=f"customer_data_{customer_data['id']}",
        episode_body=customer_data,
        source=EpisodeType.json,
        source_description="Customer profile update",
        reference_time=datetime.now(),
        group_id=namespace  # Namespace by tenant
    )

async def search_tenant_data(tenant_id, query):
    """Search within a tenant's namespace"""
    
    namespace = f"tenant_{tenant_id}"
    
    # Only search within this tenant's namespace
    return await graphiti.search(
        query=query,
        group_id=namespace
    )
```


# Searching the Graph

> How to retrieve information from your Graphiti graph

The examples below demonstrate two search approaches in the Graphiti library:

1. **Hybrid Search:**

   ```python
   await graphiti.search(query)
   ```

   Combines semantic similarity and BM25 retrieval, reranked using Reciprocal Rank Fusion.

   Example: Does a broad retrieval of facts related to Allbirds Wool Runners and Jane's purchase.

2. **Node Distance Reranking:**

   ```python
   await graphiti.search(query, focal_node_uuid)
   ```

   Extends Hybrid Search above by prioritizing results based on proximity to a specified node in the graph.

   Example: Focuses on Jane-specific information, highlighting her wool allergy.

Node Distance Reranking is particularly useful for entity-specific queries, providing more contextually relevant results. It weights facts by their closeness to the focal node, emphasizing information directly related to the entity of interest.

This dual approach allows for both broad exploration and targeted, entity-specific information retrieval from the knowledge graph.

```python
query = "Can Jane wear Allbirds Wool Runners?"
jane_node_uuid = "123e4567-e89b-12d3-a456-426614174000"

def print_facts(edges):
    print("\n".join([edge.fact for edge in edges]))

# Hybrid Search
results = await graphiti.search(query)
print_facts(results)

> The Allbirds Wool Runners are sold by Allbirds.
> Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole) has a runner silhouette.
> Jane purchased SuperLight Wool Runners.

# Hybrid Search with Node Distance Reranking
await client.search(query, jane_node_uuid)
print_facts(results)

> Jane purchased SuperLight Wool Runners.
> Jane is allergic to wool.
> The Allbirds Wool Runners are sold by Allbirds.
```

## Configurable Search Strategies

Graphiti also provides a low-level search method that is more configurable than the out-of-the-box search.
This search method can be called using `graphiti._search()` and passing in an additional config parameter of type `SearchConfig`.
`SearchConfig` contains 4 fields: one for the limit, and three more configs for each of edges, nodes, and communities.
The `graphiti._search()` method returns a `SearchResults` object containing a list of nodes, edges, and communities.

The `graphiti._search()` method is quite configurable and can be complicated to work with at first.
As such, we also have a `search_config_recipes.py` file that contains a few prebuilt `SearchConfig` recipes for common use cases.

The 15 recipes are the following:

| Search Type                               | Description                                                                                                               |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| COMBINED\_HYBRID\_SEARCH\_RRF             | Performs a hybrid search with RRF reranking over edges, nodes, and communities.                                           |
| COMBINED\_HYBRID\_SEARCH\_MMR             | Performs a hybrid search with MMR reranking over edges, nodes, and communities.                                           |
| COMBINED\_HYBRID\_SEARCH\_CROSS\_ENCODER  | Performs a full-text search, similarity search, and BFS with cross\_encoder reranking over edges, nodes, and communities. |
| EDGE\_HYBRID\_SEARCH\_RRF                 | Performs a hybrid search over edges with RRF reranking.                                                                   |
| EDGE\_HYBRID\_SEARCH\_MMR                 | Performs a hybrid search over edges with MMR reranking.                                                                   |
| EDGE\_HYBRID\_SEARCH\_NODE\_DISTANCE      | Performs a hybrid search over edges with node distance reranking.                                                         |
| EDGE\_HYBRID\_SEARCH\_EPISODE\_MENTIONS   | Performs a hybrid search over edges with episode mention reranking.                                                       |
| EDGE\_HYBRID\_SEARCH\_CROSS\_ENCODER      | Performs a hybrid search over edges with cross encoder reranking.                                                         |
| NODE\_HYBRID\_SEARCH\_RRF                 | Performs a hybrid search over nodes with RRF reranking.                                                                   |
| NODE\_HYBRID\_SEARCH\_MMR                 | Performs a hybrid search over nodes with MMR reranking.                                                                   |
| NODE\_HYBRID\_SEARCH\_NODE\_DISTANCE      | Performs a hybrid search over nodes with node distance reranking.                                                         |
| NODE\_HYBRID\_SEARCH\_EPISODE\_MENTIONS   | Performs a hybrid search over nodes with episode mentions reranking.                                                      |
| NODE\_HYBRID\_SEARCH\_CROSS\_ENCODER      | Performs a hybrid search over nodes with cross encoder reranking.                                                         |
| COMMUNITY\_HYBRID\_SEARCH\_RRF            | Performs a hybrid search over communities with RRF reranking.                                                             |
| COMMUNITY\_HYBRID\_SEARCH\_MMR            | Performs a hybrid search over communities with MMR reranking.                                                             |
| COMMUNITY\_HYBRID\_SEARCH\_CROSS\_ENCODER | Performs a hybrid search over communities with cross encoder reranking.                                                   |

## Supported Reranking Approaches

**Reciprocal Rank Fusion (RRF)** enhances search by combining results from different algorithms, like BM25 and semantic search. Each algorithm's results are ranked, converted to reciprocal scores (1/rank), and summed. This aggregated score determines the final ranking, leveraging the strengths of each method for more accurate retrieval.

**Maximal Marginal Relevance (MMR)** is a search strategy that balances relevance and diversity in results. It selects results that are both relevant to the query and diverse from already chosen ones, reducing redundancy and covering different query aspects. MMR ensures comprehensive and varied search results by iteratively choosing results that maximize relevance while minimizing similarity to previously selected results.

A **Cross-Encoder** is a model that jointly encodes a query and a result, scoring their relevance by considering their combined context. This approach often yields more accurate results compared to methods that encode query and a text separately.

Graphiti supports three cross encoders:

* `OpenAIRerankerClient` (the default) - Uses an OpenAI model to classify relevance and the resulting `logprobs` are used to rerank results.
* `GeminiRerankerClient` - Uses Google's Gemini models to classify relevance for cost-effective and low-latency reranking.
* `BGERerankerClient` - Uses the `BAAI/bge-reranker-v2-m3` model and requires `sentence_transformers` be installed.


# CRUD Operations

> How to access and modify Nodes and Edges

The Graphiti library uses 8 core classes to add data to your graph:

* `Node`
* `EpisodicNode`
* `EntityNode`
* `Edge`
* `EpisodicEdge`
* `EntityEdge`
* `CommunityNode`
* `CommunityEdge`

The generic `Node` and `Edge` classes are abstract base classes, and the other 4 classes inherit from them.
Each of `EpisodicNode`, `EntityNode`, `EpisodicEdge`, and `EntityEdge` have fully supported CRUD operations.

The save method performs a find or create based on the uuid of the object, and will add or update any other data from the class to the graph.
A driver must be provided to the save method. The Entity Node save method is shown below as a sample.

```python
    async def save(self, driver: AsyncDriver):
        result = await driver.execute_query(
            """
        MERGE (n:Entity {uuid: $uuid})
        SET n = {uuid: $uuid, name: $name, name_embedding: $name_embedding, summary: $summary, created_at: $created_at}
        RETURN n.uuid AS uuid""",
            uuid=self.uuid,
            name=self.name,
            summary=self.summary,
            name_embedding=self.name_embedding,
            created_at=self.created_at,
        )

        logger.info(f'Saved Node to neo4j: {self.uuid}')

        return result
```

Graphiti also supports hard deleting nodes and edges using the delete method, which also requires a driver.

```python
    async def delete(self, driver: AsyncDriver):
        result = await driver.execute_query(
            """
        MATCH (n:Entity {uuid: $uuid})
        DETACH DELETE n
        """,
            uuid=self.uuid,
        )

        logger.info(f'Deleted Node: {self.uuid}')

        return result
```

Finally, Graphiti also provides class methods to get nodes and edges by uuid.
Note that because these are class methods they are called using the class rather than an instance of the class.

```python
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str):
        records, _, _ = await driver.execute_query(
            """
        MATCH (n:Entity {uuid: $uuid})
        RETURN
            n.uuid As uuid, 
            n.name AS name, 
            n.created_at AS created_at, 
            n.summary AS summary
        """,
            uuid=uuid,
        )

        nodes: list[EntityNode] = []

        for record in records:
            nodes.append(
                EntityNode(
                    uuid=record['uuid'],
                    name=record['name'],
                    labels=['Entity'],
                    created_at=record['created_at'].to_native(),
                    summary=record['summary'],
                )
            )

        logger.info(f'Found Node: {uuid}')

        return nodes[0]
```


# Adding Fact Triples

> How to add fact triples to your Graphiti graph

A "fact triple" consists of two nodes and an edge between them, where the edge typically contains some fact. You can manually add a fact triple of your choosing to the graph like this:

```python
from graphiti_core.nodes import EpisodeType, EntityNode
from graphiti_core.edges import EntityEdge
import uuid
from datetime import datetime

source_name = "Bob"
target_name = "bananas"
source_uuid = "some existing UUID" # This is an existing node, so we use the existing UUID obtained from Neo4j Desktop
target_uuid = str(uuid.uuid4()) # This is a new node, so we create a new UUID
edge_name = "LIKES"
edge_fact = "Bob likes bananas"


source_node = EntityNode(
    uuid=source_uuid,
    name=source_name,
    group_id=""
)
target_node = EntityNode(
    uuid=target_uuid,
    name=target_name,
    group_id=""
)
edge = EntityEdge(
    group_id="",
    source_node_uuid=source_uuid,
    target_node_uuid=target_uuid,
    created_at=datetime.now(),
    name=edge_name,
    fact=edge_fact
)

await graphiti.add_triplet(source_node, edge, target_node)
```

When you add a fact triple, Graphiti will attempt to deduplicate your passed in nodes and edge with the already existing nodes and edges in the graph. If there are no duplicates, it will add them as new nodes and edges.

Also, you can avoid constructing `EntityEdge` or `EntityNode` objects manually by using the results of a Graphiti search (see [Searching the Graph](/graphiti/graphiti/searching)).


# Using LangGraph and Graphiti

> Building an agent with LangChain's LangGraph and Graphiti

<Note>
  A Jupyter notebook version of this example is available [on GitHub](https://github.com/getzep/graphiti/blob/main/examples/langgraph-agent/agent.ipynb).
</Note>

<Tip>
  Looking for a managed Graphiti service? Check out [Zep Cloud](https://www.getzep.com).

  * Designed as a self-improving memory layer for Agents.
  * No need to run Neo4j or other dependencies.
  * Additional features for startups and enterprises alike.
  * Fast and scalable.
</Tip>

The following example demonstrates building an agent using LangGraph. Graphiti is used to personalize agent responses based on information learned from prior conversations. Additionally, a database of products is loaded into the Graphiti graph, enabling the agent to speak to these products.

The agent implements:

* persistance of new chat turns to Graphiti and recall of relevant Facts using the most recent message.
* a tool for querying Graphiti for shoe information
* an in-memory `MemorySaver` to maintain agent state.

## Install dependencies

```shell
pip install graphiti-core langchain-openai langgraph ipywidgets
```

<Note>
  Ensure that you've followed the [Graphiti installation instructions](/graphiti/getting-started/quick-start). In particular, installation of `neo4j`.
</Note>

```python
import asyncio
import json
import logging
import os
import sys
import uuid
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Annotated

import ipywidgets as widgets
from dotenv import load_dotenv
from IPython.display import Image, display
from typing_extensions import TypedDict

load_dotenv()
```

```python
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()
```

## Configure Graphiti

Ensure that you have `neo4j` running and a database created. You'll need the following environment variables configured:

```bash
NEO4J_URI=
NEO4J_USER=
NEO4J_PASSWORD=
```

```python
# Configure Graphiti

from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.bulk_utils import RawEpisode
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

client = Graphiti(
    neo4j_uri,
    neo4j_user,
    neo4j_password,
)
```

## Generating a database schema

The following is only required for the first run of this notebook or when you'd like to start your database over.

<Warning>
  `clear_data` is destructive and will wipe your entire database.
</Warning>

```python
# Note: This will clear the database
await clear_data(client.driver)
await client.build_indices_and_constraints()
```

## Load Shoe Data into the Graph

Load several shoe and related products into the Graphiti. This may take a while.

<Note>
  This only needs to be done once. If you run `clear_data` you'll need to rerun this step.
</Note>

```python
async def ingest_products_data(client: Graphiti):
    script_dir = Path.cwd().parent
    json_file_path = script_dir / 'data' / 'manybirds_products.json'

    with open(json_file_path) as file:
        products = json.load(file)['products']

    episodes: list[RawEpisode] = [
        RawEpisode(
            name=product.get('title', f'Product {i}'),
            content=str({k: v for k, v in product.items() if k != 'images'}),
            source_description='ManyBirds products',
            source=EpisodeType.json,
            reference_time=datetime.now(),
        )
        for i, product in enumerate(products)
    ]

    await client.add_episode_bulk(episodes)


await ingest_products_data(client)
```

## Create a user node in the Graphiti graph

In your own app, this step could be done later once the user has identified themselves and made their sales intent known. We do this here so we can configure the agent with the user's `node_uuid`.

```python
user_name = 'jess'

await client.add_episode(
    name='User Creation',
    episode_body=(f'{user_name} is interested in buying a pair of shoes'),
    source=EpisodeType.text,
    reference_time=datetime.now(),
    source_description='SalesBot',
)

# let's get Jess's node uuid
nl = await client.get_nodes_by_query(user_name)

user_node_uuid = nl[0].uuid

# and the ManyBirds node uuid
nl = await client.get_nodes_by_query('ManyBirds')
manybirds_node_uuid = nl[0].uuid
```

## Helper Functions and LangChain Imports

```python
def edges_to_facts_string(entities: list[EntityEdge]):
    return '-' + '\n- '.join([edge.fact for edge in entities])
```

```python
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
```

## `get_shoe_data` Tool

The agent will use this to search the Graphiti graph for information about shoes. We center the search on the `manybirds_node_uuid` to ensure we rank shoe-related data over user data.

```python
@tool
async def get_shoe_data(query: str) -> str:
    """Search the graphiti graph for information about shoes"""
    edge_results = await client.search(
        query,
        center_node_uuid=manybirds_node_uuid,
        num_results=10,
    )
    return edges_to_facts_string(edge_results)


tools = [get_shoe_data]
tool_node = ToolNode(tools)
```

## Initialize the LLM and bind tools

```python
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0).bind_tools(tools)
```

### Test the tool node

```python
await tool_node.ainvoke({'messages': [await llm.ainvoke('wool shoes')]})
```

```json
{
    "messages": [
        {
            "content": "-The product 'Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole)' is made of Wool.\n- Women's Tree Breezers Knit - Rugged Beige (Hazy Beige Sole) has sizing options related to women's move shoes half sizes.\n- TinyBirds Wool Runners - Little Kids - Natural Black (Blizzard Sole) is a type of Shoes.\n- The product 'Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole)' belongs to the category Shoes.\n- The product 'Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole)' uses SuperLight Foam technology.\n- TinyBirds Wool Runners - Little Kids - Natural Black (Blizzard Sole) is sold by Manybirds.\n- Jess is interested in buying a pair of shoes.\n- TinyBirds Wool Runners - Little Kids - Natural Black (Blizzard Sole) has the handle TinyBirds-wool-runners-little-kids.\n- ManyBirds Men's Couriers are a type of Shoes.\n- Women's Tree Breezers Knit - Rugged Beige (Hazy Beige Sole) belongs to the Shoes category.",
            "name": "get_shoe_data",
            "tool_call_id": "call_EPpOpD75rdq9jKRBUsfRnfxx"
        }
    ]
}
```

## Chatbot Function Explanation

The chatbot uses Graphiti to provide context-aware responses in a shoe sales scenario. Here's how it works:

1. **Context Retrieval**: It searches the Graphiti graph for relevant information based on the latest message, using the user's node as the center point. This ensures that user-related facts are ranked higher than other information in the graph.

2. **System Message**: It constructs a system message incorporating facts from Graphiti, setting the context for the AI's response.

3. **Knowledge Persistence**: After generating a response, it asynchronously adds the interaction to the Graphiti graph, allowing future queries to reference this conversation.

This approach enables the chatbot to maintain context across interactions and provide personalized responses based on the user's history and preferences stored in the Graphiti graph.

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    user_node_uuid: str


async def chatbot(state: State):
    facts_string = None
    if len(state['messages']) > 0:
        last_message = state['messages'][-1]
        graphiti_query = f'{"SalesBot" if isinstance(last_message, AIMessage) else state["user_name"]}: {last_message.content}'
        # search graphiti using Jess's node uuid as the center node
        # graph edges (facts) further from the Jess node will be ranked lower
        edge_results = await client.search(
            graphiti_query, center_node_uuid=state['user_node_uuid'], num_results=5
        )
        facts_string = edges_to_facts_string(edge_results)

    system_message = SystemMessage(
        content=f"""You are a skillfull shoe salesperson working for ManyBirds. Review information about the user and their prior conversation below and respond accordingly.
        Keep responses short and concise. And remember, always be selling (and helpful!)

        Things you'll need to know about the user in order to close a sale:
        - the user's shoe size
        - any other shoe needs? maybe for wide feet?
        - the user's preferred colors and styles
        - their budget

        Ensure that you ask the user for the above if you don't already know.

        Facts about the user and their conversation:
        {facts_string or 'No facts about the user and their conversation'}"""
    )

    messages = [system_message] + state['messages']

    response = await llm.ainvoke(messages)

    # add the response to the graphiti graph.
    # this will allow us to use the graphiti search later in the conversation
    # we're doing async here to avoid blocking the graph execution
    asyncio.create_task(
        client.add_episode(
            name='Chatbot Response',
            episode_body=f"{state['user_name']}: {state['messages'][-1]}\nSalesBot: {response.content}",
            source=EpisodeType.message,
            reference_time=datetime.now(),
            source_description='Chatbot',
        )
    )

    return {'messages': [response]}
```

## Setting up the Agent

This section sets up the Agent's LangGraph graph:

1. **Graph Structure**: It defines a graph with nodes for the agent (chatbot) and tools, connected in a loop.

2. **Conditional Logic**: The `should_continue` function determines whether to end the graph execution or continue to the tools node based on the presence of tool calls.

3. **Memory Management**: It uses a MemorySaver to maintain conversation state across turns. This is in addition to using Graphiti for facts.

```python
graph_builder = StateGraph(State)

memory = MemorySaver()


# Define the function that determines whether to continue or not
async def should_continue(state, config):
    messages = state['messages']
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return 'end'
    # Otherwise if there is, we continue
    else:
        return 'continue'


graph_builder.add_node('agent', chatbot)
graph_builder.add_node('tools', tool_node)

graph_builder.add_edge(START, 'agent')
graph_builder.add_conditional_edges('agent', should_continue, {'continue': 'tools', 'end': END})
graph_builder.add_edge('tools', 'agent')


graph = graph_builder.compile(checkpointer=memory)
```

Our LangGraph agent graph is illustrated below.

```python
with suppress(Exception):
    display(Image(graph.get_graph().draw_mermaid_png()))
```

![LangGraph Illustration](file:076bec8c-aba7-4928-92db-3d1808fe43e7)

## Running the Agent

Let's test the agent with a single call

```python
await graph.ainvoke(
    {
        'messages': [
            {
                'role': 'user',
                'content': 'What sizes do the TinyBirds Wool Runners in Natural Black come in?',
            }
        ],
        'user_name': user_name,
        'user_node_uuid': user_node_uuid,
    },
    config={'configurable': {'thread_id': uuid.uuid4().hex}},
)
```

```json

{
    "messages": [
        {
            "content": "What sizes do the TinyBirds Wool Runners in Natural Black come in?",
            "id": "6a940637-70a0-4c95-a4d7-4c4846909747",
            "type": "HumanMessage"
        },
        {
            "content": "The TinyBirds Wool Runners in Natural Black are available in the following sizes for little kids: 5T, 6T, 8T, 9T, and 10T. \n\nDo you have a specific size in mind, or are you looking for something else? Let me know your needs, and I can help you find the perfect pair!",
            "additional_kwargs": {
                "refusal": null
            },
            "response_metadata": {
                "token_usage": {
                    "completion_tokens": 76,
                    "prompt_tokens": 314,
                    "total_tokens": 390
                },
                "model_name": "gpt-4o-mini-2024-07-18",
                "system_fingerprint": "fp_f33667828e",
                "finish_reason": "stop",
                "logprobs": null
            },
            "id": "run-d2f79c7f-4d41-4896-88dc-476a8e38bea8-0",
            "usage_metadata": {
                "input_tokens": 314,
                "output_tokens": 76,
                "total_tokens": 390
            },
            "type": "AIMessage"
        }
    ],
    "user_name": "jess",
    "user_node_uuid": "186a845eee4849619d1e625b178d1845"
}
```

## Viewing the Graph

At this stage, the graph would look something like this. The `jess` node is `INTERESTED_IN` the `TinyBirds Wool Runner` node. The image below was generated using Neo4j Desktop.

![Graph State](file:b9359f52-1fbb-4d0a-a750-20bf41f0b34a)

## Running the Agent interactively

The following code will run the agent in a Jupyter notebook event loop. You can modify the code to suite your own needs.

Just enter a message into the box and click submit.

```python
conversation_output = widgets.Output()
config = {'configurable': {'thread_id': uuid.uuid4().hex}}
user_state = {'user_name': user_name, 'user_node_uuid': user_node_uuid}


async def process_input(user_state: State, user_input: str):
    conversation_output.append_stdout(f'\nUser: {user_input}\n')
    conversation_output.append_stdout('\nAssistant: ')

    graph_state = {
        'messages': [{'role': 'user', 'content': user_input}],
        'user_name': user_state['user_name'],
        'user_node_uuid': user_state['user_node_uuid'],
    }

    try:
        async for event in graph.astream(
            graph_state,
            config=config,
        ):
            for value in event.values():
                if 'messages' in value:
                    last_message = value['messages'][-1]
                    if isinstance(last_message, AIMessage) and isinstance(
                        last_message.content, str
                    ):
                        conversation_output.append_stdout(last_message.content)
    except Exception as e:
        conversation_output.append_stdout(f'Error: {e}')


def on_submit(b):
    user_input = input_box.value
    input_box.value = ''
    asyncio.create_task(process_input(user_state, user_input))


input_box = widgets.Text(placeholder='Type your message here...')
submit_button = widgets.Button(description='Send')
submit_button.on_click(on_submit)

conversation_output.append_stdout('Asssistant: Hello, how can I help you find shoes today?')

display(widgets.VBox([input_box, submit_button, conversation_output]))
```


# Telemetry

# Telemetry

Graphiti collects anonymous usage statistics to help us understand how the framework is being used and improve it for everyone. We believe transparency is important, so here's exactly what we collect and why.

## What We Collect

When you initialize a Graphiti instance, we collect:

* **Anonymous identifier**: A randomly generated UUID stored locally in `~/.cache/graphiti/telemetry_anon_id`
* **System information**: Operating system, Python version, and system architecture
* **Graphiti version**: The version you're using
* **Configuration choices**:
  * LLM provider type (OpenAI, Azure, Anthropic, etc.)
  * Database backend (Neo4j, FalkorDB)
  * Embedder provider (OpenAI, Azure, Voyage, etc.)

## What We Don't Collect

We are committed to protecting your privacy. We **never** collect:

* Personal information or identifiers
* API keys or credentials
* Your actual data, queries, or graph content
* IP addresses or hostnames
* File paths or system-specific information
* Any content from your episodes, nodes, or edges

## Why We Collect This Data

This information helps us:

* Understand which configurations are most popular to prioritize support and testing
* Identify which LLM and database providers to focus development efforts on
* Track adoption patterns to guide our roadmap
* Ensure compatibility across different Python versions and operating systems

By sharing this anonymous information, you help us make Graphiti better for everyone in the community.

## View the Telemetry Code

The Telemetry code [may be found here](https://github.com/getzep/graphiti/blob/main/graphiti_core/telemetry/telemetry.py).

## How to Disable Telemetry

Telemetry is **opt-out** and can be disabled at any time. To disable telemetry collection:

### Option 1: Environment Variable

```bash
export GRAPHITI_TELEMETRY_ENABLED=false
```

### Option 2: Set in your shell profile

```bash
# For bash users (~/.bashrc or ~/.bash_profile)
echo 'export GRAPHITI_TELEMETRY_ENABLED=false' >> ~/.bashrc

# For zsh users (~/.zshrc)
echo 'export GRAPHITI_TELEMETRY_ENABLED=false' >> ~/.zshrc
```

### Option 3: Set for a specific Python session

```python
import os
os.environ['GRAPHITI_TELEMETRY_ENABLED'] = 'false'

# Then initialize Graphiti as usual
from graphiti_core import Graphiti
graphiti = Graphiti(...)
```

Telemetry is automatically disabled during test runs (when `pytest` is detected).

## Technical Details

* Telemetry uses PostHog for anonymous analytics collection
* All telemetry operations are designed to fail silently - they will never interrupt your application or affect Graphiti functionality
* The anonymous ID is stored locally and is not tied to any personal information


