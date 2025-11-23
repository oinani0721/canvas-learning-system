# Graphiti - Other

**Pages:** 142

---

## Adding batch data

**URL:** llms-txt#adding-batch-data

**Contents:**
- How batch processing works
- When to use batch processing
- Usage example
- Adding batch message data to threads
- Important details
- Data size and chunking

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

## Adding batch message data to threads

In addition to adding batch data to your graph, you can add batch message data directly into user threads. This functionality is important when you want to maintain the structure of threads for your user data, which can affect how the `thread.get_user_context()` method works since it relies on the past messages of a given thread.

<Note>
  The `thread.add_messages_batch` operation supports a maximum of 30 messages per batch.
</Note>

* Maximum of 20 episodes per batch
* Episodes can be of mixed types (text, json, message)
* As an experimental feature, may produce slightly different graph structure compared to sequential processing
* Each episode still respects the 10,000 character limit

## Data size and chunking

The same data size limits apply to batch processing as sequential processing. Each episode in the batch is limited to 10,000 characters. For larger documents, chunk them into smaller episodes before adding to the batch.

For chunking strategies and best practices, see the [data size limit and chunking section](/adding-data-to-the-graph#data-size-limit-and-chunking) in the main adding data guide.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

## Adding batch message data to threads

In addition to adding batch data to your graph, you can add batch message data directly into user threads. This functionality is important when you want to maintain the structure of threads for your user data, which can affect how the `thread.get_user_context()` method works since it relies on the past messages of a given thread.

<Note>
  The `thread.add_messages_batch` operation supports a maximum of 30 messages per batch.
</Note>

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Adding Data to the Graph

**URL:** llms-txt#adding-data-to-the-graph

**Contents:**
- Overview
- Adding Message Data
- Adding Text Data
- Adding JSON Data
- Data Size Limit and Chunking
- Adding Custom Fact/Node Triplets
- Add Batch Data
- Cloning Graphs
  - Cloning User Graphs
  - Key Behaviors and Limitations

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

Here's an example demonstrating how to add text data to the graph:

Here's an example demonstrating how to add JSON data to the graph:

## Data Size Limit and Chunking

The `graph.add` endpoint has a data size limit of 10,000 characters when adding data to the graph. If you need to add a document which is more than 10,000 characters, we recommend chunking the document as well as using Anthropic's contextualized retrieval technique. We have an example of this [here](https://blog.getzep.com/building-a-russian-election-interference-knowledge-graph/#:~:text=Chunking%20articles%20into%20multiple%20Episodes%20improved%20our%20results%20compared%20to%20treating%20each%20article%20as%20a%20single%20Episode.%20This%20approach%20generated%20more%20detailed%20knowledge%20graphs%20with%20richer%20node%20and%20edge%20extraction%2C%20while%20single%2DEpisode%20processing%20produced%20only%20high%2Dlevel%2C%20sparse%20graphs.). This example uses Graphiti, but the same patterns apply to Zep as well.

Additionally, we recommend using relatively small chunk sizes, so that Zep is able to capture all of the entities and relationships within a chunk. Using a larger chunk size may result in some entities and relationships not being captured.

## Adding Custom Fact/Node Triplets

You can also add manually specified fact/node triplets to the graph. You need only specify the fact, the target node name, and the source node name. Zep will then create a new corresponding edge and nodes, or use an existing edge/nodes if they exist and seem to represent the same nodes or edge you send as input. And if this new fact invalidates an existing fact, it will mark the existing fact as invalid and add the new fact triplet.

You can also specify the node summaries, edge temporal data, and UUIDs. See the [associated SDK reference](/sdk-reference/graph/add-fact-triple).

You can add data in batches for faster processing when working with large datasets. To learn more about batch processing and implementation details, see [Adding Batch Data](adding-batch-data).

The `graph.clone` method allows you to create complete copies of graphs with new identifiers. This is useful for scenarios like creating test copies of user data, migrating user graphs to new identifiers, or setting up template graphs for new users.

<Note>
  The target graph must not exist - they will be created as part of the cloning operation. If no target ID is provided, one will be auto-generated and returned in the response.
</Note>

### Cloning User Graphs

Here's an example demonstrating how to clone a user graph:

### Key Behaviors and Limitations

* **Target Requirements**: The target user or graph must not exist and will be created during the cloning operation
* **Auto-generation**: If no target ID is provided, Zep will auto-generate one and return it in the response
* **Node Modification**: The central user entity node in the cloned graph is updated with the new user ID, and all references in the node summary are updated accordingly

## Managing Your Data on the Graph

The `graph.add` method returns the [episode](/graphiti/graphiti/adding-episodes) that was created in the graph from adding that data. You can use this to maintain a mapping between your data and its corresponding episode in the graph and to delete specific data from the graph using the [delete episode](/deleting-data-from-the-graph#delete-an-episode) method.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

## Adding Text Data

Here's an example demonstrating how to add text data to the graph:

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Adding Episodes

**URL:** llms-txt#adding-episodes

**Contents:**
  - Adding Episodes

> How to add data to your Graphiti graph

<Note>
  Refer to the [Custom Entity Types](/graphiti/core-concepts/custom-entity-and-edge-types) page for detailed instructions on adding user-defined ontology to your graph.
</Note>

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

Using the `EpisodeType.message` type supports passing in multi-turn conversations in the `episode_body`.

The text should be structured in `{role/name}: {message}` pairs.

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

**Examples:**

Example 1 (python):
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

Example 2 (python):
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

---

## Adding Fact Triples

**URL:** llms-txt#adding-fact-triples

> How to add fact triples to your Graphiti graph

A "fact triple" consists of two nodes and an edge between them, where the edge typically contains some fact. You can manually add a fact triple of your choosing to the graph like this:

When you add a fact triple, Graphiti will attempt to deduplicate your passed in nodes and edge with the already existing nodes and edges in the graph. If there are no duplicates, it will add them as new nodes and edges.

Also, you can avoid constructing `EntityEdge` or `EntityNode` objects manually by using the results of a Graphiti search (see [Searching the Graph](/graphiti/graphiti/searching)).

**Examples:**

Example 1 (python):
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

---

## Adding JSON Best Practices

**URL:** llms-txt#adding-json-best-practices

**Contents:**
- Key Criteria
- JSON that is too large
  - JSON with too many attributes
  - JSON with too many list elements
  - JSON with large strings
- JSON that is deeply nested
- JSON that is not understandable in isolation
- JSON that is not a unified entity
- Dealing with a combination of the above

> Best practices for preparing JSON data for ingestion into Zep

Adding JSON to Zep without adequate preparation can lead to unexpected results. For instance, adding a large JSON without dividing it up can lead to a graph with very few nodes. Below, we go over what type of JSON works best with Zep, and techniques you can use to ensure your JSON fits these criteria.

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

---

## Adding Memory

**URL:** llms-txt#adding-memory

**Contents:**
- Adding Messages
  - Basic example
  - Ignore assistant messages
  - Creating messages with metadata
  - Updating message metadata
  - Setting message timestamps
  - Message limits
  - Check when messages are finished processing
- Adding Business Data
- Customizing Memory Creation

> Learn how to add chat history and messages to Zep's memory.

You can add both messages and business data to User Graphs.

Add your chat history to Zep using the `thread.add_messages` method. `thread.add_messages` is thread-specific and expects data in chat message format, including a `name` (e.g., user's real name), `role` (AI, human, tool), and message `content`. Zep stores the chat history and builds a user-level knowledge graph from the messages.

<Tip>
  For best results, add chat history to Zep on every chat turn. That is, add both the AI and human messages in a single operation and in the order that the messages were created.
</Tip>

The example below adds messages to Zep's memory for the user in the given thread:

You can find additional arguments to `thread.add_messages` in the [SDK reference](/sdk-reference/thread/add-messages). Notably, for latency sensitive applications, you can set `return_context` to true which will make `thread.add_messages` return a context block in the way that `thread.get_user_context` does (discussed below).

### Ignore assistant messages

You can also pass in a list of roles to ignore when adding messages to a User Graph using the `ignore_roles` argument. For example, you may not want assistant messages to be added to the user graph; providing the assistant messages in the `thread.add_messages` call while setting `ignore_roles` to include "assistant" will make it so that only the user messages are ingested into the graph, but the assistant messages are still used to contextualize the user messages. This is important in case the user message itself does not have enough context, such as the message "Yes." Additionally, the assistant messages will still be added to the thread's message history.

### Creating messages with metadata

Messages can have metadata attached to store additional information like sentiment scores, source identifiers, processing flags, or other custom data. Metadata is preserved when getting threads, individual messages, and when searching episodes.

<Note>
  Message metadata is currently supported only for thread messages. Messages added via the `graph.add` API do not support metadata. Zep does not support filtering or searching over message metadata.
</Note>

You can attach metadata when creating messages by including a `metadata` field in your message objects:

### Updating message metadata

You can update the metadata of an existing message using the message UUID. This is useful for adding or modifying metadata after a message has been created, such as updating sentiment analysis results or processing status.

### Setting message timestamps

When creating messages via the API, you should provide the `created_at` timestamp in RFC3339 format. The `created_at` timestamp represents the time when the message was originally sent by the user. Setting the `created_at` timestamp is important to ensure the user's knowledge graph has accurate temporal understanding of user history (since this time is used in our fact invalidation process).

When adding messages to a thread, there are limits on both the number of messages and message size:

* **Messages per call**: You can add at most 30 messages in a single `thread.add_messages` call
* **Message size limit**: Each message can be at most 2,500 characters

If you need to add more than 30 messages or have messages exceeding the character limits, you'll need to split them across multiple API calls or truncate the content accordingly. Our additional recommendations include:

* Have users attach documents rather than paste them into the message, and then process documents separately with `graph.add`
* Reduce the max message size for your users to match our max message size
* Optional: allow users to paste in documents with an auto detection algorithm that turns it into an attachment as opposed to part of the message

### Check when messages are finished processing

You can use the message UUIDs from the response to poll the messages and check when they are finished processing:

An example of this can be found in the [check data ingestion status cookbook](/cookbook/check-data-ingestion-status).

## Adding Business Data

You can also add JSON or unstructured text as memory to a User Graph using our [Graph API](/adding-data-to-the-graph).

## Customizing Memory Creation

Zep offers two ways to customize how memory is created. You can read more about these features at their guide pages:

* [**Custom entity and edge types**](/customizing-graph-structure#custom-entity-and-edge-types): Feature allowing use of Pydantic-like classes to customize creation/retrieval of entities and relations in the knowledge graph.
* [**User summary instructions**](/users#user-summary-instructions): Customize how Zep generates entity summaries for users in their knowledge graph with up to 5 custom instructions per user.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

You can find additional arguments to `thread.add_messages` in the [SDK reference](/sdk-reference/thread/add-messages). Notably, for latency sensitive applications, you can set `return_context` to true which will make `thread.add_messages` return a context block in the way that `thread.get_user_context` does (discussed below).

### Ignore assistant messages

You can also pass in a list of roles to ignore when adding messages to a User Graph using the `ignore_roles` argument. For example, you may not want assistant messages to be added to the user graph; providing the assistant messages in the `thread.add_messages` call while setting `ignore_roles` to include "assistant" will make it so that only the user messages are ingested into the graph, but the assistant messages are still used to contextualize the user messages. This is important in case the user message itself does not have enough context, such as the message "Yes." Additionally, the assistant messages will still be added to the thread's message history.

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Add episodes to the graph

**URL:** llms-txt#add-episodes-to-the-graph

**Contents:**
  - Basic Search

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
python

**Examples:**

Example 1 (unknown):
```unknown
### Basic Search

The simplest way to retrieve relationships (edges) from Graphiti is using the search method, which performs a hybrid search combining semantic similarity and BM25 text retrieval. For more details on search capabilities, see the [Searching the Graph](/graphiti/working-with-data/searching) page:
```

---

## Add the episode to the graph

**URL:** llms-txt#add-the-episode-to-the-graph

await graphiti.add_episode(
    name="Product Update - PROD001",
    episode_body=product_data,  # Pass the Python dictionary directly
    source=EpisodeType.json,
    source_description="Allbirds product catalog update",
    reference_time=datetime.now(),
)
python
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

**Examples:**

Example 1 (unknown):
```unknown
#### Loading Episodes in Bulk

Graphiti offers `add_episode_bulk` for efficient batch ingestion of episodes, significantly outperforming `add_episode` for large datasets. This method is highly recommended for bulk loading.

<Warning>
  Use `add_episode_bulk` only for populating empty graphs or when edge invalidation is not required. The bulk ingestion pipeline does not perform edge invalidation operations.
</Warning>
```

---

## Add the triplet to the graph

**URL:** llms-txt#add-the-triplet-to-the-graph

**Contents:**
  - Querying Within a Namespace

await graphiti.add_triplet(source_node, edge, target_node)
python

**Examples:**

Example 1 (unknown):
```unknown
### Querying Within a Namespace

When querying the graph, specify the `group_id` to limit results to a particular namespace:
```

---

## Add User Specific Business Data to User Graphs

**URL:** llms-txt#add-user-specific-business-data-to-user-graphs

This guide demonstrates how to add user-specific business data to a user's knowledge graph. We'll create a user, fetch their business data, and add it to their graph.

First, we will initialize our client and create a new user:

Then, we will fetch and format the user's business data. Note that the functionality to fetch a users business data will depend on your codebase.

Also note that you could make your Zep user IDs equal to whatever internal user IDs you use to make things easier to manage. Generally, Zep user IDs, thread IDs, Graph IDs, etc. can be arbitrary strings, and can map to your app's data schema.

Lastly, we will add the formatted data to the user's graph using the [graph API](/adding-data-to-the-graph):

Here, we use `type="json"`, but the graph API also supports `type="text"` and `type="message"`. The `type="text"` option is useful for adding background information that is in unstructured text such as internal documents or web copy. The `type="message"` option is useful for adding data that is in a message format but is not your user's chat history, such as emails. [Read more about this here](/adding-data-to-the-graph).

Also, note that when adding data to the graph, you should consider the size of the data you are adding and our payload limits. [Read more about this here](/docs/performance/performance-best-practices#optimizing-memory-operations).

You have now successfully added user-specific business data to a user's knowledge graph, which can be used alongside chat history to create comprehensive user memory.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

Then, we will fetch and format the user's business data. Note that the functionality to fetch a users business data will depend on your codebase.

Also note that you could make your Zep user IDs equal to whatever internal user IDs you use to make things easier to manage. Generally, Zep user IDs, thread IDs, Graph IDs, etc. can be arbitrary strings, and can map to your app's data schema.

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Agent with knowledge graph tools

**URL:** llms-txt#agent-with-knowledge-graph-tools

**Contents:**
- Query memory
  - User memory queries

agent = AssistantAgent(
    name="KnowledgeGraphAssistant",
    model_client=OpenAIChatCompletionClient(model="gpt-4.1-mini"),
    tools=[search_tool, add_tool],
    system_message="You can search and add data to the knowledge graph.",
    reflect_on_tool_use=True
)
python

**Examples:**

Example 1 (unknown):
```unknown
## Query memory

Both memory types support direct querying with different scope parameters.

### User memory queries
```

---

## Agent with user graph tools

**URL:** llms-txt#agent-with-user-graph-tools

**Contents:**
  - Knowledge graph tools

agent = AssistantAgent(
    name="UserKnowledgeAssistant",
    model_client=OpenAIChatCompletionClient(model="gpt-4.1-mini"),
    tools=[search_tool, add_tool],
    system_message="You can search and add data to the user's knowledge graph.",
    reflect_on_tool_use=True  # Enables tool usage reflection
)
python

**Examples:**

Example 1 (unknown):
```unknown
### Knowledge graph tools
```

---

## and the ManyBirds node uuid

**URL:** llms-txt#and-the-manybirds-node-uuid

**Contents:**
- Helper Functions and LangChain Imports
- `get_shoe_data` Tool
- Initialize the LLM and bind tools
  - Test the tool node
- Chatbot Function Explanation
- Setting up the Agent

nl = await client.get_nodes_by_query('ManyBirds')
manybirds_node_uuid = nl[0].uuid
python
def edges_to_facts_string(entities: list[EntityEdge]):
    return '-' + '\n- '.join([edge.fact for edge in entities])
python
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
python
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
python
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0).bind_tools(tools)
python
await tool_node.ainvoke({'messages': [await llm.ainvoke('wool shoes')]})
json
{
    "messages": [
        {
            "content": "-The product 'Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole)' is made of Wool.\n- Women's Tree Breezers Knit - Rugged Beige (Hazy Beige Sole) has sizing options related to women's move shoes half sizes.\n- TinyBirds Wool Runners - Little Kids - Natural Black (Blizzard Sole) is a type of Shoes.\n- The product 'Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole)' belongs to the category Shoes.\n- The product 'Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole)' uses SuperLight Foam technology.\n- TinyBirds Wool Runners - Little Kids - Natural Black (Blizzard Sole) is sold by Manybirds.\n- Jess is interested in buying a pair of shoes.\n- TinyBirds Wool Runners - Little Kids - Natural Black (Blizzard Sole) has the handle TinyBirds-wool-runners-little-kids.\n- ManyBirds Men's Couriers are a type of Shoes.\n- Women's Tree Breezers Knit - Rugged Beige (Hazy Beige Sole) belongs to the Shoes category.",
            "name": "get_shoe_data",
            "tool_call_id": "call_EPpOpD75rdq9jKRBUsfRnfxx"
        }
    ]
}
python
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
python
graph_builder = StateGraph(State)

memory = MemorySaver()

**Examples:**

Example 1 (unknown):
```unknown
## Helper Functions and LangChain Imports
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
## `get_shoe_data` Tool

The agent will use this to search the Graphiti graph for information about shoes. We center the search on the `manybirds_node_uuid` to ensure we rank shoe-related data over user data.
```

Example 4 (unknown):
```unknown
## Initialize the LLM and bind tools
```

---

## Avoid: Too granular

**URL:** llms-txt#avoid:-too-granular

**Contents:**
- Entity Type Exclusion
- Migration Guide
- Important Constraints
  - Protected Attribute Names

edge_type_map = {
    ("CEO", "TechCompany"): ["CEOEmployment"],
    ("Engineer", "TechCompany"): ["EngineerEmployment"],
    # This creates too many specific types
}
python
await graphiti.add_episode(
    name="Business Update",
    episode_body="The meeting discussed various topics including weather and sports.",
    source_description="Meeting notes",
    reference_time=datetime.now(),
    entity_types=entity_types,
    excluded_entity_types=["Person"]  # Won't extract Person entities
)
```

If you're upgrading from a previous version of Graphiti:

* You can add entity types to new episodes, even if existing episodes in the graph did not have entity types. Existing nodes will continue to work without being classified.
* To add types to previously ingested data, you need to re-ingest it with entity types set into a new graph.

## Important Constraints

### Protected Attribute Names

Custom entity type attributes cannot use protected names that are already used by Graphiti's core EntityNode class:

* `uuid`, `name`, `group_id`, `labels`, `created_at`, `summary`, `attributes`, `name_embedding`

Custom entity types and edge types provide powerful ways to structure your knowledge graph according to your domain needs. They enable more precise extraction, better organization, and richer semantic relationships in your data.

**Examples:**

Example 1 (unknown):
```unknown
## Entity Type Exclusion

You can exclude specific entity types from extraction using the excluded\_entity\_types parameter:
```

---

## Azure OpenAI configuration - use separate endpoints for different services

**URL:** llms-txt#azure-openai-configuration---use-separate-endpoints-for-different-services

api_key = "<your-api-key>"
api_version = "<your-api-version>"
llm_endpoint = "<your-llm-endpoint>"  # e.g., "https://your-llm-resource.openai.azure.com/"
embedding_endpoint = "<your-embedding-endpoint>"  # e.g., "https://your-embedding-resource.openai.azure.com/"

---

## Bring Your Own Key (BYOK)

**URL:** llms-txt#bring-your-own-key-(byok)

**Contents:**
- Overview
- Getting started
- FAQ

<Warning>
  Early access only. Contact your Zep account team to enable BYOK for your workspace.
</Warning>

<Info>
  Available to [Enterprise Plan](https://www.getzep.com/pricing) customers only.
</Info>

Bring Your Own Key (BYOK) gives you full control over the encryption keys that protect your data at rest in Zep Cloud. Instead of relying on provider-managed keys, you generate and manage a Customer Managed Key (CMK) in your own AWS KMS account. Zep uses that key—under a narrowly scoped, auditable permission—to encrypt and decrypt the data that belongs to your organization.

* **Customer-controlled encryption:** You can rotate, revoke, or disable your CMK at any time, immediately gating access to your encrypted data.
* **Envelope encryption model:** Zep uses your CMK to derive short-lived data encryption keys (DEKs) for each tenant and storage layer, ensuring strong isolation without adding latency to live requests.
* **Comprehensive auditability:** All KMS usage is logged in your AWS CloudTrail. Zep maintains matching provider-side audit logs for shared visibility and compliance reporting.
* **Separation of duties:** Operational staff cannot access both encrypted data and the keys required to decrypt it. Access requires multi-party approvals and is fully logged.

1. **Provision a CMK in AWS KMS.** Use an AWS account you control and enable automatic rotation if required by your policies.
2. **Configure a minimal KMS policy.** Grant Zep’s BYOK service permissions to generate and decrypt data keys on your behalf. The policy is limited to your tenant scope and can be revoked at any time.
3. **Share the CMK ARN with Zep.** Your account team will coordinate a secure exchange and validate connectivity in a non-production environment before rollout.
4. **Monitor key usage.** Enable CloudTrail logging for your CMK. Zep recommends creating alerts for unusual patterns, such as unexpected decrypt attempts or access from unfamiliar regions.
5. **Roll out to production.** Zep will migrate your tenant to BYOK-backed encryption with no downtime. You retain ongoing control through KMS aliases and policy changes.

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

---

## Bring Your Own LLM (BYOM)

**URL:** llms-txt#bring-your-own-llm-(byom)

**Contents:**
- Overview
- Getting started
- FAQ

<Warning>
  Early access only. Contact your Zep account team to enable BYOM for your workspace.
</Warning>

<Info>
  Available to [Enterprise Plan](https://www.getzep.com/pricing) customers only.
</Info>

Bring Your Own LLM (BYOM) lets you connect your existing contracts with model providers such as OpenAI, Anthropic, and Google to Zep Cloud. You keep using Zep’s orchestration, memory, and security controls while routing inference through credentials you manage. This approach ensures:

* **Contract continuity:** Apply your negotiated pricing, quotas, and compliance commitments with each LLM vendor.
* **Data governance:** Enforce provider-specific policies for data usage, retention, and residency.
* **Operational flexibility:** Configure the best vendor or model for each project, including fallbacks for high availability.

1. **Collect provider credentials.** Obtain API keys or service accounts for your chosen vendors. Each Zep project can use a different set of credentials, enabling separation between environments.
2. **Add credentials in the Zep dashboard.** Navigate to **Settings ▸ LLM Providers** within a project, select a vendor, and paste the credential. Zep stores the secret securely in an encrypted secrets manager within your project scope.
3. **(Optional) Supply a customer-managed KMS key.** If you require customer-controlled encryption, provide a KMS ARN with `kms:Encrypt`, `kms:Decrypt`, and `kms:DescribeKey` permissions granted to Zep’s runtime roles. Zep validates the key with a test encrypt/decrypt during setup.
4. **Select default and fallback models.** Choose a primary model for the project. Optionally configure fallbacks to maintain continuity if the primary vendor rate limits or experiences an outage.
5. **Monitor usage and quotas.** Use project analytics to track call volume by provider. Configure per-provider rate limits to enforce budget or vendor restrictions.

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

---

## Building a Chatbot with Zep

**URL:** llms-txt#building-a-chatbot-with-zep

**Contents:**
- Set Up Your Environment
- Create User and Add a Thread
- Datasets
  - Wait a minute or two!
- Retrieve Data From Zep

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

3. Ensure that you have a `.env` file in your working directory that includes your `ZEP_API_KEY` and `OPENAI_API_KEY`:

<Note>
  Zep API keys are specific to a project. You can create multiple keys for a
  single project. Visit `Project Settings` in the Zep dashboard to manage your
  API keys.
</Note>

<Info>
  We also provide an

[Asynchronous Python client](/install-sdks#initialize-the-client)

## Create User and Add a Thread

Users in Zep may have one or more chat threads. These are threads of messages between the user and an agent.

<Tip>
  Include the user's **full name** and **email address** when creating a user.
  This improves Zep's ability to associate data, such as emails or documents,
  with a user.
</Tip>

We're going to use the [memory](/adding-memory#adding-messages) and [graph](/adding-data-to-the-graph) APIs to upload an assortment of data to Zep. These include past dialog with the agent, CRM support cases, and billing data.

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

The [`thread.get_user_context` method](/retrieving-memory#retrieving-zeps-context-block) provides an easy way to retrieve memory relevant to the current conversation by using the last 4 messages and their proximity to the User node.

<Tip>
  The `thread.get_user_context` method is a good starting point for retrieving relevant conversation context. It shortcuts passing recent messages to the `graph.search` API and returns a [context block](/retrieving-memory#retrieving-zeps-context-block), raw facts, and historical chat messages, providing everything needed for your agent's prompts.
</Tip>

```text
FACTS and ENTITIES represent relevant context to the current conversation.

**Examples:**

Example 1 (bash):
```bash
pip install zep-cloud openai rich python-dotenv
```

Example 2 (text):
```text
ZEP_API_KEY=<key>
OPENAI_API_KEY=<key>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
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
```

---

## Check Data Ingestion Status

**URL:** llms-txt#check-data-ingestion-status

Data added to Zep is processed asynchronously and can take a few seconds to a few minutes to finish processing. In this recipe, we show how to check whether a given data upload request (also known as an [Episode](/graphiti/graphiti/adding-episodes)) is finished processing by polling Zep with the `graph.episode.get` method.

First, let's create a user:

Now, let's add some data and immediately try to search for that data; because data added to Zep is processed asynchronously and can take a few seconds to a few minutes to finish processing, our search results do not have the data we just added:

We can check the status of the episode to see when it has finished processing, using the episode returned from the `graph.add` method and the `graph.episode.get` method:

Now that the episode has finished processing, we can search for the data we just added, and this time we get a result:

**Examples:**

Example 1 (python):
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

Example 2 (typescript):
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

Example 3 (go):
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

Example 4 (python):
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

---

## Communities

**URL:** llms-txt#communities

> How to create and update communities

In Graphiti, communities (represented as `CommunityNode` objects) represent groups of related entity nodes.
Communities can be generated using the `build_communities` method on the graphiti class.

Communities are determined using the Leiden algorithm, which groups strongly connected nodes together.
Communities contain a summary field that collates the summaries held on each of its member entities.
This allows Graphiti to provide high-level synthesized information about what the graph contains in addition to the more granular facts stored on edges.

Once communities are built, they can also be updated with new episodes by passing in `update_communities=True` to the `add_episode` method.
If a new node is added to the graph, we will determine which community it should be added to based on the most represented community of the new node's surrounding nodes.
This updating methodology is inspired by the label propagation algorithm for determining communities.
However, we still recommend periodically rebuilding communities to ensure the most optimal grouping.
Whenever the `build_communities` method is called it will remove any existing communities before creating new ones.

**Examples:**

Example 1 (python):
```python
await graphiti.build_communities()
```

---

## Configure Anthropic LLM with OpenAI embeddings and reranking

**URL:** llms-txt#configure-anthropic-llm-with-openai-embeddings-and-reranking

**Contents:**
  - Environment Variables
- Groq
  - Installation
  - Configuration

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
bash
pip install "graphiti-core[groq]"
python
from graphiti_core import Graphiti
from graphiti_core.llm_client.groq_client import GroqClient, LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

**Examples:**

Example 1 (unknown):
```unknown
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
```

Example 2 (unknown):
```unknown
### Configuration
```

---

## Configure Graphiti

**URL:** llms-txt#configure-graphiti

**Contents:**
- Generating a database schema

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
python

**Examples:**

Example 1 (unknown):
```unknown
## Generating a database schema

The following is only required for the first run of this notebook or when you'd like to start your database over.

<Warning>
  `clear_data` is destructive and will wipe your entire database.
</Warning>
```

---

## Configure Groq LLM with OpenAI embeddings and reranking

**URL:** llms-txt#configure-groq-llm-with-openai-embeddings-and-reranking

**Contents:**
  - Environment Variables
- Ollama (Local LLMs)
  - Installation

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
bash

**Examples:**

Example 1 (unknown):
```unknown
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
```

---

## Configure logging

**URL:** llms-txt#configure-logging

logging.basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

---

## Configure Ollama LLM client

**URL:** llms-txt#configure-ollama-llm-client

llm_config = LLMConfig(
    api_key="abc",  # Ollama doesn't require a real API key
    model="deepseek-r1:7b",
    small_model="deepseek-r1:7b",
    base_url="http://localhost:11434/v1",  # Ollama provides this port
)

llm_client = OpenAIClient(config=llm_config)

---

## Configure OpenAI-compatible service

**URL:** llms-txt#configure-openai-compatible-service

llm_config = LLMConfig(
    api_key="<your-api-key>",
    model="<your-main-model>",        # e.g., "mistral-large-latest"
    small_model="<your-small-model>", # e.g., "mistral-small-latest"
    base_url="<your-base-url>",       # e.g., "https://api.mistral.ai/v1"
)

---

## Create an edge with the same namespace

**URL:** llms-txt#create-an-edge-with-the-same-namespace

edge = EntityEdge(
    group_id=namespace,  # Apply namespace to edge
    source_node_uuid=source_node.uuid,
    target_node_uuid=target_node.uuid,
    created_at=datetime.now(),
    name="is_category_of",
    fact="SuperLight Wool Runners is a product in the Sustainable Footwear category"
)

---

## Create a search config for nodes only

**URL:** llms-txt#create-a-search-config-for-nodes-only

node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
node_search_config.limit = 5  # Limit to 5 results

---

## Create LLM Config with your Azure deployment names

**URL:** llms-txt#create-llm-config-with-your-azure-deployment-names

azure_llm_config = LLMConfig(
    small_model="gpt-4.1-nano",
    model="gpt-4.1-mini",
)

---

## Create Neptune driver

**URL:** llms-txt#create-neptune-driver

driver = NeptuneDriver(
    host=neptune_uri,        # Required: Neptune cluster endpoint
    aoss_host=aoss_host,     # Required: OpenSearch Serverless collection endpoint
    port=neptune_port        # Optional: Neptune port (defaults to 8182)
)

---

## Create separate Azure OpenAI clients for different services

**URL:** llms-txt#create-separate-azure-openai-clients-for-different-services

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

---

## Create source and target nodes with the namespace

**URL:** llms-txt#create-source-and-target-nodes-with-the-namespace

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

---

## Create the agent configured for this user

**URL:** llms-txt#create-the-agent-configured-for-this-user

**Contents:**
- Viewing The Context Value

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
python
r = await graph_invoke(
    "Hi there?",
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
python
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
python
memory = await zep.thread.get_user_context(thread_id=thread_id)

print(memory.context)
text
FACTS and ENTITIES represent relevant context to the current conversation.

**Examples:**

Example 1 (unknown):
```unknown
Let's test the agent with a few messages:
```

Example 2 (unknown):
```unknown
> Hello! How are you feeling today? I'm here to listen and support you.
```

Example 3 (unknown):
```unknown
> I'm sorry to hear that you've been feeling stressed. Work can be a significant source of pressure, and it sounds like your dog might be adding to that stress as well. If you feel comfortable sharing, what specifically has been causing you stress at work and with your dog? I'm here to help you through it.

## Viewing The Context Value
```

Example 4 (unknown):
```unknown
The context value will look something like this:
```

---

## Create tools bound to knowledge graph

**URL:** llms-txt#create-tools-bound-to-knowledge-graph

search_tool = create_search_graph_tool(zep_client, graph_id=graph_id)
add_tool = create_add_graph_data_tool(zep_client, graph_id=graph_id)

---

## Create tools bound to user graph

**URL:** llms-txt#create-tools-bound-to-user-graph

search_tool = create_search_graph_tool(zep_client, user_id=user_id)
add_tool = create_add_graph_data_tool(zep_client, user_id=user_id)

---

## Create user and thread in Zep

**URL:** llms-txt#create-user-and-thread-in-zep

await zep.user.add(user_id=user_name, first_name=first_name, last_name=last_name)
await zep.thread.create(thread_id=thread_id, user_id=user_name)

---

## CRUD Operations

**URL:** llms-txt#crud-operations

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

Graphiti also supports hard deleting nodes and edges using the delete method, which also requires a driver.

Finally, Graphiti also provides class methods to get nodes and edges by uuid.
Note that because these are class methods they are called using the class rather than an instance of the class.

**Examples:**

Example 1 (python):
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

Example 2 (python):
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

Example 3 (python):
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

---

## Customize Your Context Block

**URL:** llms-txt#customize-your-context-block

When [searching the graph](/searching-the-graph) instead of [using Zep's Context Block](/retrieving-memory#retrieving-zeps-context-block), you need to use the search results to create a custom context block. In this recipe, we will demonstrate how to build a custom Context Block using the [graph search API](/searching-the-graph). We will also use the [custom entity and edge types feature](/customizing-graph-structure#custom-entity-and-edge-types), though using this feature is optional.

---

## Customizing Graph Structure

**URL:** llms-txt#customizing-graph-structure

**Contents:**
- Default Entity and Edge Types
  - Definition
  - Adding Data
  - Searching
  - Disabling Default Ontology
- Custom Entity and Edge Types
  - Definition
  - Setting Entity and Edge Types
  - Adding Data
  - Searching/Retrieving

Zep enables the use of rich, domain-specific data structures in graphs through Entity Types and Edge Types, replacing generic graph nodes and edges with detailed models.

Zep classifies newly created nodes/edges as one of the default or custom types or leaves them unclassified. For example, a node representing a preference is classified as a Preference node, and attributes specific to that type are automatically populated. You may restrict graph queries to nodes/edges of a specific type, such as Preference.

The default entity and edge types are applied to user graphs (not all graphs) by default, but you may define additional custom types as needed.

Each node/edge is classified as a single type only. Multiple classifications are not supported.

## Default Entity and Edge Types

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

When we add data to the graph, default entity and edge types are automatically created:

When searching nodes in the graph, you may provide a list of types to filter the search by. The provided types are ORed together. Search results will only include nodes that satisfy one of the provided types:

### Disabling Default Ontology

In some cases, you may want to disable the default entity and edge types for specific users and only use custom types you define. You can do this by setting the `disable_default_ontology` flag when creating or updating a user.

When `disable_default_ontology` is set to `true`:

* Only custom entity and edge types you define will be used for classification
* The default entity and edge types (User, Assistant, Preference, Location, etc.) will not be applied
* Nodes and edges will only be classified as your custom types or remain unclassified

This is useful when you need precise control over your graph structure and want to ensure only domain-specific types are used.

## Custom Entity and Edge Types

<Note>
  Start with fewer, more generic custom types with minimal fields and simple definitions, then incrementally add complexity as needed. This functionality requires prompt engineering and iterative optimization of the class and field descriptions, so it's best to start simple.
</Note>

In addition to the default entity and edge types, you may specify your own custom entity and custom edge types. You need to provide a description of the type and a description for each of the fields. The syntax for this is different for each language.

You may not create more than 10 custom entity types and 10 custom edge types per project. The limit of 10 custom entity types does not include the default types. Each model may have up to 10 fields.

<Warning>
  When creating custom entity or edge types, you may not use the following attribute names (including in Go struct tags), as they conflict with default node attributes: `uuid`, `name`, `graph_id`, `name_embedding`, `summary`, and `created_at`.
</Warning>

<Note>
  Including attributes on custom entity and edge types is an advanced feature designed for precision context engineering where you only want to utilize specific field values when constructing your context block. [See here for an example](cookbook/customize-your-context-block#example-2-utilizing-custom-entity-and-edge-types). Many agent memory use cases can be solved with node summaries and facts alone. Custom attributes should only be added when you need structured field values for precise context retrieval rather than general conversational memory.
</Note>

### Setting Entity and Edge Types

You can set these custom entity and edge types as the graph ontology for your current [Zep project](/projects). The ontology can be applied either project-wide to all users and graphs, or targeted to specific users and graphs only.

#### Setting Types Project Wide

When no user IDs or graph IDs are provided, the ontology is set for the entire project. All users and graphs within the project will use this ontology. Note that for custom edge types, you can require the source and destination nodes to be a certain type, or allow them to be any type:

#### Setting Types For Specific Graphs

You can also set the ontology for specific users and/or graphs by providing user IDs and graph IDs. When these parameters are provided, the ontology will only apply to the specified users and graphs, while other users and graphs in the project will continue using the previously set ontology (whether that was due to a project-wide setting of ontology or due to a graph-specific setting of ontology):

Now, when you add data to the graph, new nodes and edges are classified into exactly one of the overall set of entity or edge types respectively, or no type:

### Searching/Retrieving

Now that a graph with custom entity and edge types has been created, you may filter node search results by entity type, or edge search results by edge type.

Below, you can see the examples that were created from our data of each of the entity and edge types that we defined:

Additionally, you can provide multiple types in search filters, and the types will be ORed together:

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

**Examples:**

Example 1 (python):
```python
from zep_cloud.types import Message

  message = {
      "name": "John Doe",
      "role": "user",
      "content": "I really like pop music, and I don't like metal",
  }

  client.thread.add_messages(thread_id=thread_id, messages=[Message(**message)])
```

Example 2 (typescript):
```typescript
const messages = [{
      name: "John Doe",
      role: "user",
      content: "I really like pop music, and I don't like metal",
  }];

  await client.thread.addMessages(threadId, {messages: messages});
```

Example 3 (go):
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

Example 4 (python):
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

---

## Custom Edge Types

**URL:** llms-txt#custom-edge-types

**Contents:**
- Using Custom Entity and Edge Types
- Searching with Custom Types

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
python
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
python
from graphiti_core.search.search_filters import SearchFilters

**Examples:**

Example 1 (unknown):
```unknown
## Using Custom Entity and Edge Types

Pass your custom entity types and edge types to the add\_episode method:
```

Example 2 (unknown):
```unknown
## Searching with Custom Types

You can filter search results to specific entity types or edge types using SearchFilters:
```

---

## Custom Entity and Edge Types

**URL:** llms-txt#custom-entity-and-edge-types

**Contents:**
- Defining Custom Entity and Edge Types

> Enhancing Graphiti with Custom Ontologies

Graphiti allows you to define custom entity types and edge types to better represent your domain-specific knowledge. This enables more structured data extraction and richer semantic relationships in your knowledge graph.

## Defining Custom Entity and Edge Types

Custom entity types and edge types are defined using Pydantic models. Each model represents a specific type with custom attributes.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

---

## Custom Entity Types

**URL:** llms-txt#custom-entity-types

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

---

## Debugging

**URL:** llms-txt#debugging

**Contents:**
- Enabling Debug Logging
- Accessing Debug Logs
- Viewing Debug Logs
- Best Practices for Debug Logging

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

---

## Define a namespace for this data

**URL:** llms-txt#define-a-namespace-for-this-data

namespace = "product_catalog"

---

## Define the function that determines whether to continue or not

**URL:** llms-txt#define-the-function-that-determines-whether-to-continue-or-not

**Contents:**
- Running the Agent
- Viewing the Graph
- Running the Agent interactively

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
python
with suppress(Exception):
    display(Image(graph.get_graph().draw_mermaid_png()))
python
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
json

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
python
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

**Examples:**

Example 1 (unknown):
```unknown
Our LangGraph agent graph is illustrated below.
```

Example 2 (unknown):
```unknown
![LangGraph Illustration](file:076bec8c-aba7-4928-92db-3d1808fe43e7)

## Running the Agent

Let's test the agent with a single call
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
## Viewing the Graph

At this stage, the graph would look something like this. The `jess` node is `INTERESTED_IN` the `TinyBirds Wool Runner` node. The image below was generated using Neo4j Desktop.

![Graph State](file:b9359f52-1fbb-4d0a-a750-20bf41f0b34a)

## Running the Agent interactively

The following code will run the agent in a Jupyter notebook event loop. You can modify the code to suite your own needs.

Just enter a message into the box and click submit.
```

---

## Deleting Data from the Graph

**URL:** llms-txt#deleting-data-from-the-graph

**Contents:**
- Delete an Edge
- Delete an Episode
- Delete a Node

Here's how to delete an edge from a graph:

Note that when you delete an edge, it never deletes the associated nodes, even if it means there will be a node with no edges.

<Note>
  Deleting an episode does not regenerate the names or summaries of nodes shared with other episodes. This episode information may still exist within these nodes. If an episode invalidates a fact, and the episode is deleted, the fact will remain marked as invalidated.
</Note>

When you delete an [episode](/graphiti/graphiti/adding-episodes), it will delete all the edges associated with it, and it will delete any nodes that are only attached to that episode. Nodes that are also attached to another episode will not be deleted.

Here's how to delete an episode from a graph:

This feature is coming soon.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

Note that when you delete an edge, it never deletes the associated nodes, even if it means there will be a node with no edges.

## Delete an Episode

<Note>
  Deleting an episode does not regenerate the names or summaries of nodes shared with other episodes. This episode information may still exist within these nodes. If an episode invalidates a fact, and the episode is deleted, the fact will remain marked as invalidated.
</Note>

When you delete an [episode](/graphiti/graphiti/adding-episodes), it will delete all the edges associated with it, and it will delete any nodes that are only attached to that episode. Nodes that are also attached to another episode will not be deleted.

Here's how to delete an episode from a graph:

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Each room gets its own memory context

**URL:** llms-txt#each-room-gets-its-own-memory-context

room_name = ctx.room.name
user_id = f"livekit_user_{room_name}"
thread_id = f"thread_{room_name}"
graph_id = f"graph_{room_name}"

---

## Enable parallel runtime for Enterprise Edition

**URL:** llms-txt#enable-parallel-runtime-for-enterprise-edition

os.environ['USE_PARALLEL_RUNTIME'] = 'true'

graphiti = Graphiti(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)
```

---

## ENTITY_NAME: entity summary

**URL:** llms-txt#entity_name:-entity-summary

<ENTITIES>
  - worried: Daniel Chalef (Daniel99db) is feeling stressed lately, primarily due to work-related issues and concerns about his sick dog, which has made him worried.
  - Daniel99db: Daniel99db, or Daniel Chalef, is currently experiencing stress primarily due to work-related issues and concerns about his sick dog. Despite these challenges, he has shown a desire for interaction by initiating conversations, indicating his openness to communication.
  - sick: Daniel Chalef, also known as Daniel99db, is feeling stressed lately, primarily due to work-related issues and concerns about his sick dog. He expresses worry about his dog's health.
  - Daniel Chalef: Daniel Chalef, also known as Daniel99db, has been experiencing stress recently, primarily related to work issues and concerns about his sick dog. Despite this stress, he has been feeling generally well and has expressed a desire to connect with others, as indicated by his friendly greeting, "Hi there?".
  - dog: Daniel99db, also known as Daniel Chalef, mentioned that he has been feeling a bit stressed lately, which is related to both work and his dog.
  - work: Daniel Chalef, also known as Daniel99db, has been experiencing stress lately, primarily related to work.
  - feeling: The assistant initiates a conversation by asking how the user is feeling today, indicating a willingness to listen and provide support.
</ENTITIES>
python
r = await graph_invoke(
    "She ate my shoes which were expensive.",
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
python
r = await graph_invoke(
    "What are we talking about?",
    first_name,
    last_name,
    user_name,
    thread_id,
)

print(r)
python
r = await graph_invoke(
    "What have I said about my job?",
    first_name,
    last_name,
    user_name,
    thread_id,
)

> You've mentioned that you've been feeling a bit stressed lately, primarily due to work-related issues. If you'd like to share more about what's been going on at work or how it's affecting you, I'm here to listen and support you.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
> That sounds really frustrating, especially when you care so much about your belongings and your dog's health. It's tough when pets get into things they shouldn't, and it can add to your stress. How are you feeling about that situation? Are you able to focus on her health despite the shoe incident?

Let's now test whether the Agent is correctly grounded with facts from the prior conversation.
```

Example 3 (unknown):
```unknown
> We were discussing your concerns about your dog being sick and the situation with her eating your expensive shoes. It sounds like you're dealing with a lot right now, and I want to make sure we're addressing what's on your mind. If there's something else you'd like to talk about or if you want to share more about your dog, I'm here to listen.

Let's go even further back to determine whether context is kept by referencing a user message that is not currently in the Agent State. Zep will retrieve Facts related to the user's job.
```

---

## Episodes list containing both text and JSON episodes

**URL:** llms-txt#episodes-list-containing-both-text-and-json-episodes

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

---

## Example 1: Basic custom context block

**URL:** llms-txt#example-1:-basic-custom-context-block

**Contents:**
- Search
- Build the context block

For a basic custom context block, we search the graph for edges and nodes relevant to our custom query string, which typically represents a user message. Note that the default [Context Block](/retrieving-memory#retrieving-zeps-context-block) returned by `thread.get_user_context` uses the past few messages as the query instead.

<Tip>
  These searches can be performed in parallel to reduce latency, using our [async Python client](/quickstart#initialize-the-client), TypeScript promises, or goroutines.
</Tip>

## Build the context block

Using the search results and a few helper functions, we can build the context block. Note that for nodes, we typically want to unpack the node name and node summary, and for edges we typically want to unpack the fact and the temporal validity information:

```text
FACTS and ENTITIES represent relevant context to the current conversation.

**Examples:**

Example 1 (python):
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

Example 2 (typescript):
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

Example 3 (go):
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

Example 4 (python):
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

---

## Example 2: Utilizing custom entity and edge types

**URL:** llms-txt#example-2:-utilizing-custom-entity-and-edge-types

**Contents:**
- Search
- Build the context block

For a custom context block that uses custom entity and edge types, we perform multiple searches (with our custom query string) filtering to the custom entity or edge type we want to include in the context block:

<Tip>
  These searches can be performed in parallel to reduce latency, using our [async Python client](/quickstart#initialize-the-client), TypeScript promises, or goroutines.
</Tip>

## Build the context block

Using the search results and a few helper functions, we can compose the context block. Note that in this example, we focus on unpacking the custom attributes of the nodes and edges, but this is a design choice that you can experiment with for your use case.

Note also that we designed the context block template around the custom entity and edge types that we are unpacking into the context block:

```text
PREVIOUS_RESTAURANT_VISITS, DIETARY_PREFERENCES, and RESTAURANTS represent relevant context to the current conversation.

**Examples:**

Example 1 (python):
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

Example 2 (typescript):
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

Example 3 (go):
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

Example 4 (python):
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

---

## Example 3: Basic custom context block with BFS

**URL:** llms-txt#example-3:-basic-custom-context-block-with-bfs

**Contents:**
- Search
- Build the context block

For a more advanced custom context block, we can enhance the search results by using Breadth-First Search (BFS) to make them more relevant to the user's recent history. In this example, we retrieve the past several [episodes](/graphiti/graphiti/adding-episodes) and use those episode IDs as the BFS node IDs. We use BFS here to make the search results more relevant to the user's recent history. You can read more about how BFS works in the [Breadth-First Search section](/searching-the-graph#breadth-first-search-bfs) of our searching the graph documentation.

<Tip>
  These searches can be performed in parallel to reduce latency, using our [async Python client](/quickstart#initialize-the-client), TypeScript promises, or goroutines.
</Tip>

## Build the context block

Using the search results and a few helper functions, we can build the context block. Note that for nodes, we typically want to unpack the node name and node summary, and for edges we typically want to unpack the fact and the temporal validity information:

```text
FACTS and ENTITIES represent relevant context to the current conversation.

**Examples:**

Example 1 (python):
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

Example 2 (typescript):
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

Example 3 (go):
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

Example 4 (python):
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

---

## Example 4: Using user summary in context block

**URL:** llms-txt#example-4:-using-user-summary-in-context-block

**Contents:**
- Get user node
- Build the context block

You can retrieve the user node and use its summary to create a simple, personalized context block. This approach is particularly useful when you want to include high-level user information generated from [user summary instructions](/users#user-summary-instructions):

## Build the context block

Using the user summary, you can create a simple context block that provides personalized user information:

```text
USER_SUMMARY represents relevant context about the user.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

## Build the context block

Using the user summary, you can create a simple context block that provides personalized user information:

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Example: Perform a node search using _search method with standard recipes

**URL:** llms-txt#example:-perform-a-node-search-using-_search-method-with-standard-recipes

print(
    '\nPerforming node search using _search method with standard recipe NODE_HYBRID_SEARCH_RRF:'
)

---

## Execute the node search

**URL:** llms-txt#execute-the-node-search

node_search_results = await graphiti._search(
    query='California Governor',
    config=node_search_config,
)

---

## Execute the node search within a specific namespace

**URL:** llms-txt#execute-the-node-search-within-a-specific-namespace

**Contents:**
- Best Practices for Graph Namespacing
- Example: Multi-tenant Application

node_search_results = await graphiti._search(
    query="SuperLight Wool Runners",
    group_id="product_catalog",  # Only search within this namespace
    config=node_search_config
)
python
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

**Examples:**

Example 1 (unknown):
```unknown
## Best Practices for Graph Namespacing

1. **Consistent naming**: Use a consistent naming convention for your `group_id` values
2. **Documentation**: Maintain documentation of your namespace structure and purpose
3. **Granularity**: Choose an appropriate level of granularity for your namespaces
   * Too many namespaces can lead to fragmented data
   * Too few namespaces may not provide sufficient isolation
4. **Cross-namespace queries**: When necessary, perform multiple queries across namespaces and combine results in your application logic

## Example: Multi-tenant Application

Here's an example of using namespacing in a multi-tenant application:
```

---

## Facts with a past end date used to be valid but are NOT CURRENTLY VALID (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - 2024-06-20 14:00:00)" means Jane no longer prefers coffee with milk)

**URL:** llms-txt#facts-with-a-past-end-date-used-to-be-valid-but-are-not-currently-valid-(e.g.,-"jane-prefers-her-coffee-with-milk-(2024-01-15-10:30:00---2024-06-20-14:00:00)"-means-jane-no-longer-prefers-coffee-with-milk)

<FACTS>
  - User wants to go to dessert (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe wants to go to a lunch place (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe said 'Perfect, let's go to Insomnia Cookies' indicating he will visit Insomnia Cookies. (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe said 'Let's go to Green Leaf Cafe' indicating intention to visit (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe is craving a chocolate chip cookie (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe states that he is vegetarian. (Date range: 2025-06-16T02:17:25Z - present)
  - John Doe is lactose intolerant (Date range: 2025-06-16T02:17:25Z - present)
</FACTS>

---

## FalkorDB Configuration

**URL:** llms-txt#falkordb-configuration

**Contents:**
- Installation
- Docker Installation
- Configuration
- Connection in Python

> Configure FalkorDB as the graph provider for Graphiti

FalkorDB configuration requires version 1.1.2 or higher.

Install Graphiti with FalkorDB support:

## Docker Installation

The simplest way to run FalkorDB is via Docker:

* Exposes FalkorDB on port 6379 (Redis protocol)
* Provides a web interface on port 3000
* Runs in foreground mode for easy testing

Set the following environment variables for FalkorDB (optional):

## Connection in Python

```python
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

**Examples:**

Example 1 (bash):
```bash
pip install graphiti-core[falkordb]
```

Example 2 (bash):
```bash
uv add graphiti-core[falkordb]
```

Example 3 (bash):
```bash
docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
```

Example 4 (bash):
```bash
export FALKORDB_HOST=localhost          # Default: localhost
export FALKORDB_PORT=6379              # Default: 6379
export FALKORDB_USERNAME=              # Optional: usually not required
export FALKORDB_PASSWORD=              # Optional: usually not required
```

---

## FalkorDB connection using FalkorDriver

**URL:** llms-txt#falkordb-connection-using-falkordriver

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

---

## FAQ

**URL:** llms-txt#faq

**Contents:**
- Is there a free version of Zep Cloud?
- What is the API URL for Zep Cloud?
- Does Zep Cloud support multiple spoken languages?
- I can't join my company project, because I have already created an account. What should I do?
- How well does Zep scale?
- Can I use Zep to replace RAG over static documents?
- How does the retrieval work for thread.get\_user\_context under the hood?
- I am seeing information duplicated between different node summaries. Is this normal?
- Should I use nodes, edges, or episodes when searching the graph and creating a context string?
- Where is the data stored? What if my client needs it stored in the EU?

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

---

## Find Facts Relevant to a Specific Node

**URL:** llms-txt#find-facts-relevant-to-a-specific-node

Below, we will go through how to retrieve facts which are related to a specific node in a Zep knowledge graph. First, we will go through some methods for determining the UUID of the node you are interested in. Then, we will go through some methods for retrieving the facts related to that node.

If you are interested in the user's node specifically, we have a convenience method that [returns the user's node](/users#get-the-user-node) which includes the UUID.

An easy way to determine the UUID for other nodes is to use the graph explorer in the [Zep Web app](https://app.getzep.com/).

You can also programmatically retrieve all the nodes for a given user using our [get nodes by user API](/sdk-reference/graph/node/get-by-user-id), and then manually examine the nodes and take note of the UUID of the node of interest:

Lastly, if your user has a lot of nodes to look through, you can narrow down the search by only looking at the nodes relevant to a specific query, using our [graph search API](/searching-the-graph):

The most straightforward way to get facts related to your node is to retrieve all facts that are connected to your chosen node using the [get edges by user API](/sdk-reference/graph/edge/get-by-user-id):

You can also retrieve facts relevant to your node by using the [graph search API](/searching-the-graph) with the node distance re-ranker:

In this recipe, we went through how to retrieve facts which are related to a specific node in a Zep knowledge graph. We first went through some methods for determining the UUID of the node you are interested in. Then, we went through some methods for retrieving the facts related to that node.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## format: FACT (Date range: from - to)

**URL:** llms-txt#format:-fact-(date-range:-from---to)

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

---

## format: name: RESTAURANT_NAME; cuisine_type: CUISINE_TYPE; dietary_accommodation: DIETARY_ACCOMMODATION

**URL:** llms-txt#format:-name:-restaurant_name;-cuisine_type:-cuisine_type;-dietary_accommodation:-dietary_accommodation

<RESTAURANTS>
  - name: Green Leaf Cafe; dietary_accommodation: vegetarian
  - name: Insomnia Cookies; 
</RESTAURANTS>
```

---

## format: restaurant_name: RESTAURANT_NAME

**URL:** llms-txt#format:-restaurant_name:-restaurant_name

<PREVIOUS_RESTAURANT_VISITS>
  - restaurant_name: Insomnia Cookies
  - restaurant_name: Green Leaf Cafe
</PREVIOUS_RESTAURANT_VISITS>

---

## For bash users (~/.bashrc or ~/.bash_profile)

**URL:** llms-txt#for-bash-users-(~/.bashrc-or-~/.bash_profile)

echo 'export GRAPHITI_TELEMETRY_ENABLED=false' >> ~/.bashrc

---

## For more advanced node-specific searches, use the _search method with a recipe

**URL:** llms-txt#for-more-advanced-node-specific-searches,-use-the-_search-method-with-a-recipe

from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

---

## For zsh users (~/.zshrc)

**URL:** llms-txt#for-zsh-users-(~/.zshrc)

**Contents:**
  - Option 3: Set for a specific Python session

echo 'export GRAPHITI_TELEMETRY_ENABLED=false' >> ~/.zshrc
python
import os
os.environ['GRAPHITI_TELEMETRY_ENABLED'] = 'false'

**Examples:**

Example 1 (unknown):
```unknown
### Option 3: Set for a specific Python session
```

---

## from dotenv import load_dotenv

**URL:** llms-txt#from-dotenv-import-load_dotenv

---

## Get connection parameters from environment

**URL:** llms-txt#get-connection-parameters-from-environment

neptune_uri = os.getenv('NEPTUNE_HOST')
neptune_port = int(os.getenv('NEPTUNE_PORT', 8182))
aoss_host = os.getenv('AOSS_HOST')

---

## Get Most Relevant Facts for an Arbitrary Query

**URL:** llms-txt#get-most-relevant-facts-for-an-arbitrary-query

In this recipe, we demonstrate how to retrieve the most relevant facts from the knowledge graph using an arbitrary search query.

First, we perform a [search](/searching-the-graph) on the knowledge graph using a sample query:

Then, we get the edges from the search results and construct our fact list. We also include the temporal validity data to each fact string:

We demonstrated how to retrieve the most relevant facts for an arbitrary query using the Zep client. Adjust the query and parameters as needed to tailor the search for your specific use case.

**Examples:**

Example 1 (python):
```python
from zep_cloud.client import Zep

  zep_client = Zep(api_key=API_KEY)
  results = zep_client.graph.search(user_id="some user_id", query="Some search query", scope="edges")
```

Example 2 (typescript):
```typescript
import { ZepClient } from "@getzep/zep-cloud";

  const client = new ZepClient({ apiKey: process.env.ZEP_API_KEY || "" });
  const results = await client.graph.search({
      userId: "some user_id",
      query: "Some search query",
      scope: "edges"
  });
```

Example 3 (go):
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

Example 4 (python):
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

---

## Good: Specific and meaningful

**URL:** llms-txt#good:-specific-and-meaningful

edge_type_map = {
    ("Person", "Company"): ["Employment", "Investment"],
    ("Company", "Company"): ["Partnership", "Acquisition"],
    ("Person", "Product"): ["Usage", "Review"],
    ("Entity", "Entity"): ["RELATES_TO"]  # Fallback for unexpected relationships
}

---

## Graph Namespacing

**URL:** llms-txt#graph-namespacing

**Contents:**
- Overview
- How Namespacing Works
  - Key Benefits
- Using group\_ids in Graphiti
  - Adding Episodes with group\_id
  - Adding Fact Triples with group\_id

> Using group_ids to create isolated graph namespaces

Graphiti supports the concept of graph namespacing through the use of `group_id` parameters. This feature allows you to create isolated graph environments within the same Graphiti instance, enabling multiple distinct knowledge graphs to coexist without interference.

Graph namespacing is particularly useful for:

* **Multi-tenant applications**: Isolate data between different customers or organizations
* **Testing environments**: Maintain separate development, testing, and production graphs
* **Domain-specific knowledge**: Create specialized graphs for different domains or use cases
* **Team collaboration**: Allow different teams to work with their own graph spaces

## How Namespacing Works

In Graphiti, every node and edge can be associated with a `group_id`. When you specify a `group_id`, you're effectively creating a namespace for that data. Nodes and edges with the same `group_id` form a cohesive, isolated graph that can be queried and manipulated independently from other namespaces.

* **Data isolation**: Prevent data leakage between different namespaces
* **Simplified management**: Organize and manage related data together
* **Performance optimization**: Improve query performance by limiting the search space
* **Flexible architecture**: Support multiple use cases within a single Graphiti instance

## Using group\_ids in Graphiti

### Adding Episodes with group\_id

When adding episodes to your graph, you can specify a `group_id` to namespace the episode and all its extracted entities:

### Adding Fact Triples with group\_id

When manually adding fact triples, ensure both nodes and the edge share the same `group_id`:

```python
from graphiti_core.nodes import EntityNode
from graphiti_core.edges import EntityEdge
import uuid
from datetime import datetime

**Examples:**

Example 1 (python):
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

---

## Hybrid Search

**URL:** llms-txt#hybrid-search

results = await graphiti.search(query)
print_facts(results)

> The Allbirds Wool Runners are sold by Allbirds.
> Men's SuperLight Wool Runners - Dark Grey (Medium Grey Sole) has a runner silhouette.
> Jane purchased SuperLight Wool Runners.

---

## Hybrid Search with Node Distance Reranking

**URL:** llms-txt#hybrid-search-with-node-distance-reranking

**Contents:**
- Configurable Search Strategies
- Supported Reranking Approaches

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

---

## Initialize Graphiti with Azure OpenAI clients

**URL:** llms-txt#initialize-graphiti-with-azure-openai-clients

**Contents:**
  - Environment Variables
- Google Gemini
  - Installation
  - Configuration

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
bash
pip install "graphiti-core[google-genai]"
python
from graphiti_core import Graphiti
from graphiti_core.llm_client.gemini_client import GeminiClient, LLMConfig
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient

**Examples:**

Example 1 (unknown):
```unknown
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
```

Example 2 (unknown):
```unknown
### Configuration
```

---

## Initialize Graphiti with Gemini clients

**URL:** llms-txt#initialize-graphiti-with-gemini-clients

**Contents:**
  - Environment Variables
- Anthropic
  - Installation
  - Configuration

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
bash
pip install "graphiti-core[anthropic]"
python
from graphiti_core import Graphiti
from graphiti_core.llm_client.anthropic_client import AnthropicClient, LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

**Examples:**

Example 1 (unknown):
```unknown
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
```

Example 2 (unknown):
```unknown
### Configuration
```

---

## Initialize Graphiti with Neo4j connection

**URL:** llms-txt#initialize-graphiti-with-neo4j-connection

**Contents:**
  - Adding Episodes

graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

try:
    # Initialize the graph database with graphiti's indices. This only needs to be done once.
    await graphiti.build_indices_and_constraints()
    
    # Additional code will go here
    
finally:
    # Close the connection
    await graphiti.close()
    print('\nConnection closed')
python

**Examples:**

Example 1 (unknown):
```unknown
### Adding Episodes

Episodes are the primary units of information in Graphiti. They can be text or structured JSON and are automatically processed to extract entities and relationships. For more detailed information on episodes and bulk loading, see the [Adding Episodes](/graphiti/core-concepts/adding-episodes) page:
```

---

## Initialize Graphiti with Ollama clients

**URL:** llms-txt#initialize-graphiti-with-ollama-clients

**Contents:**
- OpenAI Compatible Services
  - Installation
  - Configuration

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
bash
pip install graphiti-core
python
from graphiti_core import Graphiti
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

**Examples:**

Example 1 (unknown):
```unknown
Ensure Ollama is running (`ollama serve`) and that you have pulled the models you want to use.

## OpenAI Compatible Services

Many LLM providers offer OpenAI-compatible APIs. Use the `OpenAIGenericClient` for these services, which ensures proper schema injection for JSON output since most providers don't support OpenAI's structured output format.

<Warning>
  When using OpenAI-compatible services, avoid smaller models as they may not accurately extract data or output the correct JSON structures required by Graphiti. Choose larger, more capable models that can handle complex reasoning and structured output.
</Warning>

### Installation
```

Example 2 (unknown):
```unknown
### Configuration
```

---

## Initialize Graphiti with OpenAI-compatible service

**URL:** llms-txt#initialize-graphiti-with-openai-compatible-service

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

---

## Initialize Zep client

**URL:** llms-txt#initialize-zep-client

**Contents:**
- Define State and Setup Tools
- Using Zep's Search as a Tool

zep = AsyncZep(api_key=os.environ.get('ZEP_API_KEY'))
python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    first_name: str
    last_name: str
    thread_id: str
    user_name: str
python
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

**Examples:**

Example 1 (unknown):
```unknown
## Define State and Setup Tools

First, define the state structure for our LangGraph agent:
```

Example 2 (unknown):
```unknown
## Using Zep's Search as a Tool

These are examples of simple Tools that search Zep for facts (from edges) or nodes. Since LangGraph tools don't automatically receive the full graph state, we create a function that returns configured tools for a specific user:
```

---

## Install SDKs

**URL:** llms-txt#install-sdks

**Contents:**
- Obtain an API Key
- Install the SDK
  - Python
  - TypeScript
  - Go
- Initialize the Client

> Set up your development environment for Zep

This guide will help you obtain an API key, install the SDK, and initialize the Zep client.

[Create a free Zep account](https://app.getzep.com/) and you will be prompted to create an API key.

Set up your Python project, ideally with [a virtual environment](https://medium.com/@vkmauryavk/managing-python-virtual-environments-with-uv-a-comprehensive-guide-ac74d3ad8dff), and then:

<Tabs>
  <Tab title="pip">
    
  </Tab>

<Tab title="uv">
    
  </Tab>
</Tabs>

Set up your TypeScript project and then:

<Tabs>
  <Tab title="npm">
    
  </Tab>

<Tab title="yarn">
    
  </Tab>

<Tab title="pnpm">
    
  </Tab>
</Tabs>

Set up your Go project and then:

## Initialize the Client

First, make sure you have a .env file with your API key:

After creating your .env file, you'll need to source it in your terminal session:

Then, initialize the client with your API key:

<Info>
  **The Python SDK Supports Async Use**

The Python SDK supports both synchronous and asynchronous usage. For async operations, import `AsyncZep` instead of `Zep` and remember to `await` client calls in your async code.
</Info>

**Examples:**

Example 1 (Bash):
```Bash
pip install zep-cloud
```

Example 2 (Bash):
```Bash
uv pip install zep-cloud
```

Example 3 (Bash):
```Bash
npm install @getzep/zep-cloud
```

Example 4 (Bash):
```Bash
yarn add @getzep/zep-cloud
```

---

## Kuzu connection using KuzuDriver

**URL:** llms-txt#kuzu-connection-using-kuzudriver

kuzu_driver = KuzuDriver(
    db='/path/to/graphiti.kuzu'        # or os.environ.get('KUZU_DB', ':memory:')
)

graphiti = Graphiti(graph_driver=kuzu_driver)
```

---

## Kuzu DB Configuration

**URL:** llms-txt#kuzu-db-configuration

**Contents:**
- Configuration
- Connection in Python

> Configure Kuzu as the graph provider for Graphiti

Kuzu is an embedded graph engine that does not require any additional setup. You can enable the Kuzu driver by installing graphiti with the Kuzu extra:

Set the following environment variables for Kuzu (optional):

## Connection in Python

```python
from graphiti_core import Graphiti
from graphiti_core.driver.kuzu_driver import KuzuDriver

**Examples:**

Example 1 (bash):
```bash
pip install graphiti-core[kuzu]
```

Example 2 (bash):
```bash
export KUZU_DB=/path/to/graphiti.kuzu          # Default: :memory:
```

---

## LangGraph Memory Example

**URL:** llms-txt#langgraph-memory-example

**Contents:**
- Install dependencies
- Configure Zep

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

Ensure that you've configured the following API keys in your environment. We're using Zep's Async client here, but we could also use the non-async equivalent.

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

**Examples:**

Example 1 (shell):
```shell
pip install zep-cloud langchain-openai langgraph ipywidgets python-dotenv
```

Example 2 (bash):
```bash
ZEP_API_KEY=your_zep_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## let's get Jess's node uuid

**URL:** llms-txt#let's-get-jess's-node-uuid

nl = await client.get_nodes_by_query(user_name)

user_node_uuid = nl[0].uuid

---

## LiveKit voice agents

**URL:** llms-txt#livekit-voice-agents

**Contents:**
- Install dependencies
- Environment setup
- Agent types
- User memory agent
- ZepUserAgent configuration
- Knowledge graph agent
- Room-based memory isolation

> Add persistent memory to LiveKit voice agents using the zep-livekit package.

The `zep-livekit` package provides seamless integration between Zep and LiveKit voice agents. Choose between [user-specific conversation memory](/users) or structured [knowledge graph memory](/graph-overview) for intelligent context retrieval in real-time voice interactions.

## Install dependencies

<Callout intent="warning">
  **Version Requirements**: This integration requires LiveKit Agents v1.0+ (not v0.x). The examples use the current AgentSession API pattern introduced in v1.0.
</Callout>

Set your API keys as environment variables:

**ZepUserAgent**: Uses [user threads](/users) for conversation memory with automatic context injection\
**ZepGraphAgent**: Accesses structured knowledge through [custom entity models](/customizing-graph-structure)

<Steps>
  ### Step 1: Setup required imports

### Step 2: Initialize Zep client and create user

### Step 3: Create agent with memory

### Step 4: Run the voice assistant

<Callout intent="info">
  **Automatic Memory Integration**: ZepUserAgent automatically captures voice conversation turns and injects relevant context from previous conversations, enabling natural continuity across voice sessions.
</Callout>

## ZepUserAgent configuration

The `ZepUserAgent` supports several parameters for customizing memory behavior:

* `context_mode`: Controls how memory context is retrieved (`"basic"` for detailed context, `"summary"` for condensed)
* `user_message_name`: Optional name for attributing user messages in Zep memory
* `assistant_message_name`: Optional name for attributing assistant messages in Zep memory
* `instructions`: System instructions that override the default LiveKit agent instructions

## Knowledge graph agent

<Steps>
  ### Step 1: Define custom entity models

### Step 2: Setup graph with ontology

### Step 3: Create graph memory agent

<Callout intent="info">
  **Search Filters**: The `search_filters` parameter allows you to constrain which entities the agent considers when retrieving context. Use `node_labels` to filter by specific entity types defined in your ontology.
</Callout>

<Callout intent="info">
  **Graph Memory Context**: ZepGraphAgent automatically extracts structured knowledge from voice conversations and injects relevant facts and entities as context for more intelligent responses.
</Callout>

## Room-based memory isolation

LiveKit rooms provide natural memory isolation boundaries:

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

<Callout intent="warning">
  **Version Requirements**: This integration requires LiveKit Agents v1.0+ (not v0.x). The examples use the current AgentSession API pattern introduced in v1.0.
</Callout>

## Environment setup

Set your API keys as environment variables:
```

Example 4 (unknown):
```unknown
## Agent types

**ZepUserAgent**: Uses [user threads](/users) for conversation memory with automatic context injection\
**ZepGraphAgent**: Accesses structured knowledge through [custom entity models](/customizing-graph-structure)

## User memory agent

<Steps>
  ### Step 1: Setup required imports
```

---

## LLM Configuration

**URL:** llms-txt#llm-configuration

**Contents:**
- Azure OpenAI
  - Installation
  - Configuration

> Configure Graphiti with different LLM providers

<Note>
  Graphiti works best with LLM services that support Structured Output (such as OpenAI and Gemini). Using other services may result in incorrect output schemas and ingestion failures, particularly when using smaller models.
</Note>

Graphiti defaults to using OpenAI for LLM inference and embeddings, but supports multiple LLM providers including Azure OpenAI, Google Gemini, Anthropic, Groq, and local models via Ollama. This guide covers configuring Graphiti with alternative LLM providers.

<Warning>
  **Azure OpenAI v1 API Opt-in Required for Structured Outputs**

Graphiti uses structured outputs via the `client.beta.chat.completions.parse()` method, which requires Azure OpenAI deployments to opt into the v1 API. Without this opt-in, you'll encounter 404 Resource not found errors during episode ingestion.

To enable v1 API support in your Azure OpenAI deployment, follow Microsoft's guide: [Azure OpenAI API version lifecycle](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/api-version-lifecycle?tabs=key#api-evolution).
</Warning>

Azure OpenAI deployments often require different endpoints for LLM and embedding services, and separate deployments for default and small models.

```python
from openai import AsyncAzureOpenAI
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

**Examples:**

Example 1 (bash):
```bash
pip install graphiti-core
```

---

## load_dotenv()

**URL:** llms-txt#load_dotenv()

---

## Make sure Neo4j Desktop is running with a local DBMS started

**URL:** llms-txt#make-sure-neo4j-desktop-is-running-with-a-local-dbms-started

**Contents:**
  - Main Function
  - Initialization

neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

if not neo4j_uri or not neo4j_user or not neo4j_password:
    raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')
python
async def main():
    # Main function implementation will go here
    pass

if __name__ == '__main__':
    asyncio.run(main())
python

**Examples:**

Example 1 (unknown):
```unknown
### Main Function

Create an async main function to run all Graphiti operations:
```

Example 2 (unknown):
```unknown
### Initialization

Connect to Neo4j and set up Graphiti indices. This is required before using other Graphiti functionality:
```

---

## Memory is isolated per room/session

**URL:** llms-txt#memory-is-isolated-per-room/session

**Contents:**
- Voice-specific considerations
- Complete example
- Learn more

zep_agent = ZepUserAgent(
    zep_client=zep_client,
    user_id=user_id,
    thread_id=thread_id,
    context_mode="basic",
    user_message_name="User",
    assistant_message_name="Assistant"
)
python
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

* [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
* [Zep LiveKit Integration Repository](https://github.com/getzep/zep/tree/main/integrations/python/zep_livekit)
* [LiveKit Python SDK](https://github.com/livekit/python-sdks)

**Examples:**

Example 1 (unknown):
```unknown
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
```

---

## Neo4j Configuration

**URL:** llms-txt#neo4j-configuration

**Contents:**
- Neo4j Community Edition
  - Installation via Neo4j Desktop
  - Docker Installation
  - Configuration
  - Connection in Python
- Neo4j AuraDB (Cloud)
  - Setup
  - Configuration
  - Connection in Python
- Neo4j Enterprise Edition

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

Set the following environment variables:

### Connection in Python

## Neo4j AuraDB (Cloud)

Neo4j AuraDB is a fully managed cloud service that handles infrastructure, backups, and updates automatically.

1. Sign up for [Neo4j Aura](https://neo4j.com/cloud/platform/aura-graph-database/)
2. Create a new AuraDB instance
3. Note down the connection URI and credentials
4. Download the connection details or copy the connection string

AuraDB connections use the `neo4j+s://` protocol for secure connections:

### Connection in Python

<Note>
  AuraDB instances automatically include APOC procedures. No additional configuration is required for most Graphiti operations.
</Note>

## Neo4j Enterprise Edition

Neo4j Enterprise Edition provides advanced features including clustering, hot backups, and performance optimizations.

Enterprise Edition requires a commercial license. Installation options include:

* **Neo4j Desktop**: Add Enterprise Edition license key
* **Docker**: Use `neo4j:5.26-enterprise` image with license
* **Server Installation**: Download from Neo4j website with valid license

### Docker with Enterprise Features

### Parallel Runtime Configuration

Enterprise Edition supports parallel runtime for improved query performance:

<Warning>
  The `USE_PARALLEL_RUNTIME` feature is only available in Neo4j Enterprise Edition and larger AuraDB instances. It is not supported in Community Edition or smaller AuraDB instances.
</Warning>

### Connection in Python

```python
import os
from graphiti_core import Graphiti

**Examples:**

Example 1 (bash):
```bash
docker run \
    --name neo4j-community \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -e NEO4J_PLUGINS='["apoc"]' \
    neo4j:5.26-community
```

Example 2 (bash):
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password
```

Example 3 (python):
```python
from graphiti_core import Graphiti

graphiti = Graphiti(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)
```

Example 4 (bash):
```bash
export NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_generated_password
```

---

## Neo4j connection parameters

**URL:** llms-txt#neo4j-connection-parameters

---

## NOTE: Facts ending in "present" are currently valid (e.g., "Jane prefers her coffee with milk (2024-01-15 10:30:00 - present)" means Jane currently prefers coffee with milk)

**URL:** llms-txt#note:-facts-ending-in-"present"-are-currently-valid-(e.g.,-"jane-prefers-her-coffee-with-milk-(2024-01-15-10:30:00---present)"-means-jane-currently-prefers-coffee-with-milk)

---

## Note: This will clear the database

**URL:** llms-txt#note:-this-will-clear-the-database

**Contents:**
- Load Shoe Data into the Graph
- Create a user node in the Graphiti graph

await clear_data(client.driver)
await client.build_indices_and_constraints()
python
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
python
user_name = 'jess'

await client.add_episode(
    name='User Creation',
    episode_body=(f'{user_name} is interested in buying a pair of shoes'),
    source=EpisodeType.text,
    reference_time=datetime.now(),
    source_description='SalesBot',
)

**Examples:**

Example 1 (unknown):
```unknown
## Load Shoe Data into the Graph

Load several shoe and related products into the Graphiti. This may take a while.

<Note>
  This only needs to be done once. If you run `clear_data` you'll need to rerun this step.
</Note>
```

Example 2 (unknown):
```unknown
## Create a user node in the Graphiti graph

In your own app, this step could be done later once the user has identified themselves and made their sales intent known. We do this here so we can configure the agent with the user's `node_uuid`.
```

---

## Not recommended - overly long query

**URL:** llms-txt#not-recommended---overly-long-query

**Contents:**
- Warming the User Cache
- Summary

results = await zep_client.graph.search(
    user_id=user_id,
    query="very long text with multiple paragraphs..."  # Will be truncated
)
python Python
  # Warm the user's cache when they log in
  client.user.warm(user_id=user_id)
  typescript TypeScript
  // Warm the user's cache when they log in
  await client.user.warm(userId);
  go Go
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

* Reuse Zep SDK client instances to optimize connection management
* Use appropriate methods for different types of content (`thread.add_messages` for conversations, `graph.add` for large documents)
* Keep search queries focused and under the token limit for optimal performance
* Warm the user cache when users log in or open your app for faster retrieval

**Examples:**

Example 1 (unknown):
```unknown
## Warming the User Cache

Zep has a multi-tier retrieval architecture. The highest tier is a "hot" cache where a user's context retrieval is fastest. After several hours of no activity, a user's data will be moved to a lower tier.

You can hint to Zep that a retrieval may be made soon, allowing Zep to move user data into cache ahead of this retrieval. A good time to do this is when a user logs in to your service or opens your app.

<CodeBlocks>
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown

```

---

## NVIDIA NeMo Agent Toolkit

**URL:** llms-txt#nvidia-nemo-agent-toolkit

**Contents:**
- Install dependencies
- Package information
- Documentation and examples
- Example implementations
- Learn more

> Use Zep memory with NVIDIA NeMo Agent Toolkit for stateful LLM applications.

The NVIDIA NeMo Agent Toolkit includes a memory module that integrates with Zep to provide long-term memory capabilities for stateful LLM-based applications. This integration enables storage of conversation history, user preferences, and other persistent data across multiple interaction steps.

## Install dependencies

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

* [NVIDIA NeMo Agent Toolkit Documentation](https://docs.nvidia.com/nemo/agent-toolkit/1.2/store-and-retrieve/memory.html)
* [PyPI Package](https://pypi.org/project/nvidia-nat-zep-cloud/)
* [GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit)

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

---

## Optional: Load environment variables from .env file

**URL:** llms-txt#optional:-load-environment-variables-from-.env-file

---

## Pass the driver to Graphiti

**URL:** llms-txt#pass-the-driver-to-graphiti

graphiti = Graphiti(graph_driver=driver)
```

---

## Perform a hybrid search combining semantic similarity and BM25 retrieval

**URL:** llms-txt#perform-a-hybrid-search-combining-semantic-similarity-and-bm25-retrieval

print("\nSearching for: 'Who was the California Attorney General?'")
results = await graphiti.search('Who was the California Attorney General?')

---

## Prepare the episodes for bulk loading

**URL:** llms-txt#prepare-the-episodes-for-bulk-loading

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

**Examples:**

Example 1 (unknown):
```unknown

```

---

## Print node search results

**URL:** llms-txt#print-node-search-results

**Contents:**
  - Complete Example
- Next Steps

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

For a complete working example that puts all these concepts together, check out the [Graphiti Quickstart Examples](https://github.com/getzep/graphiti/tree/main/examples/quickstart) on GitHub.

Now that you've learned the basics of Graphiti, you can explore more advanced features:

* [Custom Entity and Edge Types](/graphiti/core-concepts/custom-entity-and-edge-types): Learn how to define and use custom entity and edge types to better model your domain-specific knowledge
* [Communities](/graphiti/core-concepts/communities): Discover how to work with communities, which are groups of related nodes that share common attributes or relationships
* [Advanced Search Techniques](/graphiti/working-with-data/searching): Explore more sophisticated search strategies, including different reranking approaches and configurable search recipes
* [Adding Fact Triples](/graphiti/working-with-data/adding-fact-triples): Learn how to directly add fact triples to your graph for more precise knowledge representation
* [Agent Integration](/graphiti/integrations/lang-graph-agent): Discover how to integrate Graphiti with LLM agents for more powerful AI applications

<Info>
  Make sure to run await statements within an [async function](https://docs.python.org/3/library/asyncio-task.html).
</Info>

---

## Print search results

**URL:** llms-txt#print-search-results

**Contents:**
  - Center Node Search

print('\nSearch Results:')
for result in results:
    print(f'UUID: {result.uuid}')
    print(f'Fact: {result.fact}')
    if hasattr(result, 'valid_at') and result.valid_at:
        print(f'Valid from: {result.valid_at}')
    if hasattr(result, 'invalid_at') and result.invalid_at:
        print(f'Valid until: {result.invalid_at}')
    print('---')
python

**Examples:**

Example 1 (unknown):
```unknown
### Center Node Search

For more contextually relevant results, you can use a center node to rerank search results based on their graph distance to a specific node. This is particularly useful for entity-specific queries as described in the [Searching the Graph](/graphiti/working-with-data/searching) page:
```

---

## Process different result types

**URL:** llms-txt#process-different-result-types

**Contents:**
  - Graph memory queries

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
python

**Examples:**

Example 1 (unknown):
```unknown
### Graph memory queries
```

---

## Query knowledge graph with scope control

**URL:** llms-txt#query-knowledge-graph-with-scope-control

**Contents:**
  - Search result structure
- Memory vs tools comparison

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
json
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
    json
    {
        "content": "entity_name:\n entity_summary",
        "metadata": {
            "source": "graph" | "user_graph",
            "node_name": "entity_name",
            "node_attributes": {...},
            "created_at": "timestamp"
        }
    }
    json
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

**Examples:**

Example 1 (unknown):
```unknown
### Search result structure

<AccordionGroup>
  <Accordion title="Edge results (facts)">
```

Example 2 (unknown):
```unknown
</Accordion>

  <Accordion title="Node results (entities)">
```

Example 3 (unknown):
```unknown
</Accordion>

  <Accordion title="Episode results (messages)">
```

---

## Query user conversation history

**URL:** llms-txt#query-user-conversation-history

results = await memory.query("What does Alice like?", limit=5)

---

## Quickstart

**URL:** llms-txt#quickstart

**Contents:**
- Prerequisites
- Installation
- Data structure
  - Users file
  - Conversations
  - Test cases
  - Optional telemetry
- Running the evaluation
- Understanding the evaluation pipeline
- Configuration

> Evaluate Zep's memory retrieval and question-answering capabilities

The Zep Eval Harness is an end-to-end evaluation framework for testing Zep's memory retrieval and question-answering capabilities for general conversational scenarios. This guide will walk you through setting up and running the harness to evaluate your Zep implementation.

Before getting started, ensure you have:

* **Zep API Key**: Available at [app.getzep.com](https://app.getzep.com)
* **OpenAI API Key**: Obtainable from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
* **UV Package Manager**: The harness uses UV for Python dependency management

<Steps>
  ### Clone the repository

Clone the Zep repository and navigate to the eval harness directory:

Install UV package manager for macOS/Linux:

For other platforms, visit the [UV installation guide](https://docs.astral.sh/uv/).

### Install dependencies

Install all required dependencies using UV:

### Configure environment variables

Copy the example environment file and add your API keys:

Edit the `.env` file to include your API keys:

The harness expects data files in the following structure:

Location: `data/users.json`

Contains user information with fields: `user_id`, `first_name`, `last_name`, `email`, and optional metadata fields.

Location: `data/conversations/`

Files named `{user_id}_{conversation_id}.json` containing:

* `conversation_id`
* `user_id`
* `messages` array with `role`, `content`, and `timestamp`

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

For ingestion with a custom ontology:

<Callout intent="info">
    The ingestion process creates numbered run directories (e.g., `1_20251103T123456`) containing manifest files that document created users, thread IDs, and configuration details.
  </Callout>

Evaluate the most recent ingestion run:

To evaluate a specific run:

<Note>
    Results are saved to `runs/{run_number}/evaluation_results_{timestamp}.json`.
  </Note>
</Steps>

## Understanding the evaluation pipeline

The harness performs four automated steps for each test case:

Query Zep's knowledge graph using a cross-encoder reranker to retrieve relevant information.

Assess whether the retrieved information is sufficient to answer the test question. This produces the **primary metric**:

* **COMPLETE**: All necessary information present
  * **PARTIAL**: Some relevant information, but incomplete
  * **INSUFFICIENT**: Missing critical information

### Generate response

Use GPT-4o-mini with the retrieved context to generate an answer to the test question.

Evaluate the generated response against the golden answer using GPT-4o. This produces the **secondary metric**:

* **CORRECT**: Response matches golden answer
  * **WRONG**: Response does not match golden answer
</Steps>

You can customize the evaluation parameters in `zep_evaluate.py`:

**Examples:**

Example 1 (bash):
```bash
git clone https://github.com/getzep/zep.git
  cd zep/zep-eval-harness
```

Example 2 (bash):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Example 3 (bash):
```bash
uv sync
```

Example 4 (bash):
```bash
cp .env.example .env
```

---

## Quick Start

**URL:** llms-txt#quick-start

**Contents:**
- Installation
  - Alternative LLM Providers
  - Default to Slower, Low Concurrency; LLM Provider 429 Rate Limit Errors
  - Environment Variables
- Getting Started with Graphiti
  - Required Imports
  - Configuration

> Getting started with Graphiti

<Info>
  For complete working examples, check out the [Graphiti Quickstart Examples](https://github.com/getzep/graphiti/tree/main/examples/quickstart) on GitHub.
</Info>

* Python 3.10 or higher
* Neo4j 5.26 or higher or FalkorDB 1.1.2 or higher (see [Graph Database Configuration](/graphiti/configuration/graph-db-configuration) for setup options)
* OpenAI API key (Graphiti defaults to OpenAI for LLM inference and embedding)

<Note>
  The simplest way to install Neo4j is via [Neo4j Desktop](https://neo4j.com/download/). It provides a user-friendly interface to manage Neo4j instances and databases.
</Note>

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

#### Optional Variables

* `GRAPHITI_TELEMETRY_ENABLED`: Set to `false` to disable anonymous telemetry collection

## Getting Started with Graphiti

For a comprehensive overview of Graphiti and its capabilities, check out the [Overview](/graphiti/getting-started/overview) page.

First, import the necessary libraries for working with Graphiti:

<Note>
  Graphiti uses OpenAI by default for LLM inference and embedding. Ensure that an `OPENAI_API_KEY` is set in your environment. Support for multiple LLM providers is available - see our [LLM Configuration](/graphiti/configuration/llm-configuration) guide.

Graphiti also requires Neo4j connection parameters. Set the following environment variables:

* `NEO4J_URI`: The URI of your Neo4j database (default: bolt://localhost:7687)
  * `NEO4J_USER`: Your Neo4j username (default: neo4j)
  * `NEO4J_PASSWORD`: Your Neo4j password

For detailed database setup instructions, see our [Graph Database Configuration](/graphiti/configuration/graph-db-configuration) guide.
</Note>

Set up logging and environment variables for connecting to the Neo4j database:

**Examples:**

Example 1 (bash):
```bash
pip install graphiti-core
```

Example 2 (bash):
```bash
uv add graphiti-core
```

Example 3 (bash):
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Example 4 (python):
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

---

## Reading Data from the Graph

**URL:** llms-txt#reading-data-from-the-graph

**Contents:**
- Reading Edges
- Reading Nodes
- Reading Episodes

Zep provides APIs to read Edges, Nodes, and Episodes from the graph. These elements can be retrieved individually using their `UUID`, or as lists associated with a specific `user_id` or `graph_id`. The latter method returns all objects within the user's or graph's graph.

Examples of each retrieval method are provided below.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

## Reading Nodes

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Recommended - concise query

**URL:** llms-txt#recommended---concise-query

results = await zep_client.graph.search(
    user_id=user_id,  # Or graph_id
    query="project requirements discussion"
)

---

## Recommended for conversations

**URL:** llms-txt#recommended-for-conversations

zep_client.thread.add_messages(
    thread_id="thread_123",
    message={
        "role": "user",
        "name": "Alice",
        "content": "What's the weather like today?"
    }
)

---

## Recommended for large documents

**URL:** llms-txt#recommended-for-large-documents

**Contents:**
  - Use the Basic Context Block

await zep_client.graph.add(
    data=document_content,  # Your chunked document content
    user_id=user_id,       # Or graph_id
    type="text"            # Can be "text", "message", or "json"
)
python Python
  # Get memory for the thread
  memory = client.thread.get_user_context(thread_id=thread_id, mode="basic")

# Access the context block (for use in prompts)
  context_block = memory.context
  print(context_block)
  typescript TypeScript
  // Get memory for the thread
  const memory = await client.thread.getUserContext(threadId, { mode: "basic" });

// Access the context block (for use in prompts)
  const contextBlock = memory.context;
  console.log(contextBlock);
  go Go
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
  text
FACTS and ENTITIES represent relevant context to the current conversation.

**Examples:**

Example 1 (unknown):
```unknown
### Use the Basic Context Block

Zep's [context block](/retrieving-memory#retrieving-zeps-context-block) can either be in summarized or basic form (summarized by default). Retrieving basic results reduces latency (P95 \< 200 ms) since this bypasses the final summarization step.

<CodeBlocks>
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeBlocks>
```

---

## Required

**URL:** llms-txt#required

OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o-mini

---

## Reranker options: cross_encoder (default), rrf, or mmr

**URL:** llms-txt#reranker-options:-cross_encoder-(default),-rrf,-or-mmr

**Contents:**
- Output metrics
- Best practices
- Next steps

<Tip>
  The context completeness evaluation (step 2) is the primary metric as it measures Zep's core capability: retrieving relevant information. The answer grading (step 4) is secondary since it also depends on the LLM's ability to use that context.
</Tip>

The evaluation results include:

* **Aggregate scores**: Overall context completeness and answer accuracy rates
* **Per-user breakdown**: Performance metrics for each user
* **Detailed test results**: Individual test case results with context and answers
* **Performance timing**: Processing time for each step

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

* Learn more about [customizing your context block](/cookbook/customize-your-context-block)
* Explore [graph search parameters](/searching-the-graph) to optimize retrieval
* Understand [best practices for memory management](/best-practices/context-assembly)

---

## Retrieving Memory

**URL:** llms-txt#retrieving-memory

**Contents:**
- Retrieving Zep's Context Block
  - Summarized Context Block (default)
  - Basic Context Block (faster)

> Learn how to retrieve relevant context from a User Graph.

There are two ways to retrieve memory from a User Graph: using Zep's Context Block or searching the graph.

## Retrieving Zep's Context Block

Zep's Context Block is an optimized, automatically assembled string that you can directly provide as context to your agent. Zep's Context Block combines semantic search, full text search, and breadth first search to return context that is highly relevant to the user's current conversation slice, utilizing the past four messages.

The Context Block is returned by the `thread.get_user_context()` method. This method uses the latest messages of the *given thread* to search the (entire) User Graph and then returns the search results in the form of the Context Block.

Note that although `thread.get_user_context()` only requires a thread ID, it is able to return memory derived from any thread of that user. The thread is just used to determine what's relevant.

The `mode` parameter determines what form the Context Block takes (see below).

### Summarized Context Block (default)

This Context Block type returns a short summary of the relevant context. An LLM is used to create the summary, but if the LLM takes too long (more than a second), the basic Context Block is returned instead.

* Low token usage
* Easier for LLMs to understand

* Higher latency
* Some risk of missing important details

### Basic Context Block (faster)

This Context Block type returns the relevant context in a more raw format, but faster.

* Lower latency (P95 \< 200ms)
* More detailed information preserved

* Higher token usage
* May be harder for some LLMs to parse

```text
FACTS and ENTITIES represent relevant context to the current conversation.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>
```

Example 4 (unknown):
```unknown
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
```

---

## Role-Based Access Control

**URL:** llms-txt#role-based-access-control

**Contents:**
- Overview
- Scopes and authorizations
- Roles
  - Account-level roles
  - Project-level roles
- Managing role assignments

<Warning>
  Early access only. Contact your Zep account team to enable RBAC for your workspace.
</Warning>

<Info>
  Available to [Enterprise Plan](https://www.getzep.com/pricing) customers only.
</Info>

Role-based access control (RBAC) lets you grant the right level of access to each teammate while keeping sensitive account actions limited to trusted users. RBAC grants permissions through roles, and every member can hold multiple assignments across the account and individual projects.

## Scopes and authorizations

RBAC permissions are evaluated at two scopes:

* **Account scope:** Covers organization-wide settings such as member management, billing, and account-level API keys, along with full access to every project.
* **Project scope:** Grants permissions for a single project, including its data plane, collaborators, and project-specific API keys, without exposing other projects or global settings.

Authorizations are grouped into the following capability areas. These appear in the dashboard when you review role details.

* `account.view.readonly` — View account-level configuration, billing status, and usage.
* `rbac.account.manage` — Create, update, or delete account-scoped role assignments, including promoting additional Account Owners.
* `rbac.project.manage` — Manage project-scoped assignments and project-level resources (API keys, data ingestion, deletion) for the projects a member administers.

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

---

## Searching the Graph

**URL:** llms-txt#searching-the-graph

> How to retrieve information from your Graphiti graph

The examples below demonstrate two search approaches in the Graphiti library:

1. **Hybrid Search:**

Combines semantic similarity and BM25 retrieval, reranked using Reciprocal Rank Fusion.

Example: Does a broad retrieval of facts related to Allbirds Wool Runners and Jane's purchase.

2. **Node Distance Reranking:**

Extends Hybrid Search above by prioritizing results based on proximity to a specified node in the graph.

Example: Focuses on Jane-specific information, highlighting her wool allergy.

Node Distance Reranking is particularly useful for entity-specific queries, providing more contextually relevant results. It weights facts by their closeness to the focal node, emphasizing information directly related to the entity of interest.

This dual approach allows for both broad exploration and targeted, entity-specific information retrieval from the knowledge graph.

```python
query = "Can Jane wear Allbirds Wool Runners?"
jane_node_uuid = "123e4567-e89b-12d3-a456-426614174000"

def print_facts(edges):
    print("\n".join([edge.fact for edge in edges]))

**Examples:**

Example 1 (python):
```python
await graphiti.search(query)
```

Example 2 (python):
```python
await graphiti.search(query, focal_node_uuid)
```

---

## Search for only specific edge types

**URL:** llms-txt#search-for-only-specific-edge-types

**Contents:**
- How Custom Types Work
  - Entity Extraction Process
  - Edge Extraction Process
- Edge Type Mapping
- Schema Evolution
- Best Practices
  - Model Design
  - Naming Conventions
  - Edge Type Mapping Strategy

search_filter = SearchFilters(
    edge_types=["Employment", "Partnership"]  # Only return Employment and Partnership edges
)

results = await graphiti.search_(
    query="Tell me about business relationships",
    search_filter=search_filter
)
python
edge_type_map = {
    ("Person", "Company"): ["Employment"],
    ("Company", "Company"): ["Partnership", "Investment"],
    ("Person", "Person"): ["Partnership"],
    ("Entity", "Entity"): ["Investment"],  # Apply to any entity type
}
python
from pydantic import validator

class Person(BaseModel):
    """A person entity."""
    age: Optional[int] = Field(None, description="Age in years")
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v
python
class Customer(BaseModel):
    contact_info: Optional[str] = Field(None, description="Name and email")  # Don't do this
python
class Customer(BaseModel):
    name: Optional[str] = Field(None, description="Customer name")
    email: Optional[str] = Field(None, description="Customer email address")
python

**Examples:**

Example 1 (unknown):
```unknown
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
```

Example 2 (unknown):
```unknown
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
```

Example 3 (unknown):
```unknown
**Instead of compound information:**
```

Example 4 (unknown):
```unknown
**Use atomic attributes:**
```

---

## Search for only specific entity types

**URL:** llms-txt#search-for-only-specific-entity-types

search_filter = SearchFilters(
    node_labels=["Person", "Company"]  # Only return Person and Company entities
)

results = await graphiti.search_(
    query="Who works at tech companies?",
    search_filter=search_filter
)

---

## Search limits

**URL:** llms-txt#search-limits

FACTS_LIMIT = 20      # Number of edges to return
ENTITIES_LIMIT = 10   # Number of nodes to return
EPISODES_LIMIT = 0    # Disabled by default

---

## Search within a specific namespace

**URL:** llms-txt#search-within-a-specific-namespace

search_results = await graphiti.search(
    query="Wool Runners",
    group_id="product_catalog"  # Only search within this namespace
)

---

## Set up logging

**URL:** llms-txt#set-up-logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

---

## Share Memory Across Users Using Graphs

**URL:** llms-txt#share-memory-across-users-using-graphs

In this recipe, we will demonstrate how to share memory across different users by utilizing graphs. We will set up a user thread, add graph-specific data, and integrate the OpenAI client to show how to use both user and graph memory to enhance the context of a chatbot.

First, we initialize the Zep client, create a user, and create a thread:

Next, we create a new graph and add structured business data to the graph, in the form of a JSON string. This step uses the [Graphs API](/graph-overview).

Finally, we initialize the OpenAI client and define a `chatbot_response` function that retrieves user and graph memory, constructs a system/developer message, and generates a contextual response. This leverages the [Threads API](/retrieving-memory#retrieving-zeps-context-block), [graph API](/searching-the-graph), and the OpenAI chat completions endpoint.

This recipe demonstrated how to share memory across users by utilizing graphs with Zep. We set up user threads, added structured graph data, and integrated the OpenAI client to generate contextual responses, providing a robust approach to memory sharing across different users.

**Examples:**

Example 1 (python):
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

Example 2 (typescript):
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

Example 3 (go):
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

Example 4 (python):
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

---

## Telemetry

**URL:** llms-txt#telemetry

**Contents:**
- What We Collect
- What We Don't Collect
- Why We Collect This Data
- View the Telemetry Code
- How to Disable Telemetry
  - Option 1: Environment Variable
  - Option 2: Set in your shell profile

Graphiti collects anonymous usage statistics to help us understand how the framework is being used and improve it for everyone. We believe transparency is important, so here's exactly what we collect and why.

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

### Option 2: Set in your shell profile

**Examples:**

Example 1 (bash):
```bash
export GRAPHITI_TELEMETRY_ENABLED=false
```

---

## Then initialize Graphiti as usual

**URL:** llms-txt#then-initialize-graphiti-as-usual

**Contents:**
- Technical Details

from graphiti_core import Graphiti
graphiti = Graphiti(...)
```

Telemetry is automatically disabled during test runs (when `pytest` is detected).

* Telemetry uses PostHog for anonymous analytics collection
* All telemetry operations are designed to fail silently - they will never interrupt your application or affect Graphiti functionality
* The anonymous ID is stored locally and is not tied to any personal information

---

## Then pull the models you want to use:

**URL:** llms-txt#then-pull-the-models-you-want-to-use:

**Contents:**
  - Configuration

ollama pull deepseek-r1:7b     # LLM
ollama pull nomic-embed-text   # embeddings
python
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

**Examples:**

Example 1 (unknown):
```unknown
### Configuration
```

---

## These are the most relevant entities

**URL:** llms-txt#these-are-the-most-relevant-entities

---

## These are the most relevant facts and their valid date ranges

**URL:** llms-txt#these-are-the-most-relevant-facts-and-their-valid-date-ranges

---

## These are the most relevant restaurants the user has discussed previously

**URL:** llms-txt#these-are-the-most-relevant-restaurants-the-user-has-discussed-previously

---

## These are the most relevant restaurants the user has previously visited

**URL:** llms-txt#these-are-the-most-relevant-restaurants-the-user-has-previously-visited

---

## This is a high-level summary of the user

**URL:** llms-txt#this-is-a-high-level-summary-of-the-user

<USER_SUMMARY>
John Doe is a software engineer who enjoys hiking and photography. He is vegetarian and lactose intolerant. He prefers detailed technical discussions and values efficiency in communication. He has requested that the AI provide concise answers with code examples when discussing programming topics.
</USER_SUMMARY>
```

---

## Threads

**URL:** llms-txt#threads

**Contents:**
- Overview
- Adding a Thread
- Getting Messages of a Thread
- Deleting a Thread
- Listing Threads
- Automatic Cache Warming

Threads represent a conversation. Each [User](/users) can have multiple threads, and each thread is a sequence of chat messages.

Chat messages are added to threads using [`thread.add_messages`](/adding-memory#adding-messages), which both adds those messages to the thread history and ingests those messages into the user-level knowledge graph. The user knowledge graph contains data from all of that user's threads to create an integrated understanding of the user.

<Note>
  The knowledge graph does not separate the data from different threads, but integrates the data together to create a unified picture of the user. So the [get thread user context](/sdk-reference/thread/get-user-context) endpoint and the associated [`thread.get_user_context`](/retrieving-memory#retrieving-zeps-context-block) method don't return memory derived only from that thread, but instead return whatever user-level memory is most relevant to that thread, based on the thread's most recent messages.
</Note>

`threadIds` are arbitrary identifiers that you can map to relevant business objects in your app, such as users or a
conversation a user might have with your app. Before you create a thread, make sure you have [created a user](/users#adding-a-user) first. Then create a thread with:

## Getting Messages of a Thread

Deleting a thread deletes it and its associated messages. It does not however delete the associated data in the user's knowledge graph. To remove data from the graph, see [deleting data from the graph](/deleting-data-from-the-graph).

You can list all Threads in the Zep Memory Store with page\_size and page\_number parameters for pagination.

## Automatic Cache Warming

When you create a new thread, Zep automatically warms the cache for that user's graph data in the background. This optimization improves query latency for graph operations on newly created threads by pre-loading the user's data into the hot cache tier.

The warming operation runs asynchronously and does not block the thread creation response. No additional action is required on your part—this happens automatically whenever you create a thread for a user with an existing graph.

For more information about Zep's multi-tier caching architecture and manual cache warming, see [Warming the User Cache](/performance#warming-the-user-cache).

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

## Getting Messages of a Thread

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## Users

**URL:** llms-txt#users

**Contents:**
- Overview
- Ensuring Your User Data Is Correctly Mapped to the Zep Knowledge Graph
- Adding a User
- User Summary Instructions
  - Default instructions
  - Custom instructions
  - Utilizing user summary
- Getting a User
- Updating a User
- Deleting a User

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

You can add a new user by providing the user details.

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

### Utilizing user summary

You can utilize the default or custom user summary by retrieving the user node, getting the summary of that node, and including it in your context block. See [this example](/cookbook/customize-your-context-block#example-4-using-user-summary-in-context-block) for a complete implementation.

You can retrieve a user by their ID.

You can update a user's details by providing the updated user details.

You can delete a user by their ID.

## Getting a User's Threads

You can retrieve all Threads for a user by their ID.

You can list all users, with optional limit and cursor parameters for pagination.

You can also retrieve the user's node from their graph:

The user node might be used to get a summary of the user or to get facts related to the user (see ["How to find facts relevant to a specific node"](/cookbook/how-to-find-facts-relevant-to-a-specific-node)).

## Default Ontology for Users

User graphs utilize Zep's default ontology, consisting of default entity types and default edge types that affect how the graph is built. You can read more about default and custom graph ontology [here](/graph/customizing-graph-structure).

Each user graph comes with default entity and edge types that help classify and structure information extracted from conversations. [View the full default ontology definition](/graph/customizing-graph-structure#default-entity-and-edge-types).

### Disabling Default Ontology

You can disable the default entity and edge types for specific users if you need precise control over your graph structure. [Learn how to disable the default ontology](/graph/customizing-graph-structure#disabling-default-ontology).

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
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
```

Example 4 (unknown):
```unknown

```

---

## Use a predefined search configuration recipe and modify its limit

**URL:** llms-txt#use-a-predefined-search-configuration-recipe-and-modify-its-limit

node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
node_search_config.limit = 5  # Limit to 5 results

---

## Use the top search result's UUID as the center node for reranking

**URL:** llms-txt#use-the-top-search-result's-uuid-as-the-center-node-for-reranking

**Contents:**
  - Node Search Using Search Recipes

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
python

**Examples:**

Example 1 (unknown):
```unknown
### Node Search Using Search Recipes

Graphiti provides predefined search recipes optimized for different search scenarios. Here we use NODE\_HYBRID\_SEARCH\_RRF for retrieving nodes directly instead of edges. For a complete list of available search recipes and reranking approaches, see the [Configurable Search Strategies](/graphiti/working-with-data/searching#configurable-search-strategies) section in the Searching documentation:
```

---

## Using LangGraph and Graphiti

**URL:** llms-txt#using-langgraph-and-graphiti

**Contents:**
- Install dependencies
- Configure Graphiti

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

<Note>
  Ensure that you've followed the [Graphiti installation instructions](/graphiti/getting-started/quick-start). In particular, installation of `neo4j`.
</Note>

## Configure Graphiti

Ensure that you have `neo4j` running and a database created. You'll need the following environment variables configured:

**Examples:**

Example 1 (shell):
```shell
pip install graphiti-core langchain-openai langgraph ipywidgets
```

Example 2 (python):
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

Example 3 (python):
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

Example 4 (bash):
```bash
NEO4J_URI=
NEO4J_USER=
NEO4J_PASSWORD=
```

---

## Utilizing Facts and Summaries

**URL:** llms-txt#utilizing-facts-and-summaries

**Contents:**
- Facts
  - How Zep Updates Facts
  - The Four Fact Timestamps

> Facts and summaries are extracted from the chat history as a conversation unfolds as well as from business data added to Zep.

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

---

## Validate required parameters

**URL:** llms-txt#validate-required-parameters

if not neptune_uri or not aoss_host:
    raise ValueError("NEPTUNE_HOST and AOSS_HOST environment variables must be set")

---

## We'll create the actual tools after we have a user_name

**URL:** llms-txt#we'll-create-the-actual-tools-after-we-have-a-user_name

**Contents:**
- Chatbot Function Explanation
- Setting up the Agent
- Running the Agent

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
python
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
python
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
python
first_name = "Daniel"
last_name = "Chalef"
user_name = first_name + uuid.uuid4().hex[:4]
thread_id = uuid.uuid4().hex

**Examples:**

Example 1 (unknown):
```unknown
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
```

Example 2 (unknown):
```unknown
## Setting up the Agent

This function creates a complete LangGraph agent configured for a specific user. This approach allows us to properly configure the tools with the user context:
```

Example 3 (unknown):
```unknown
Our LangGraph agent graph is illustrated below.

![Agent Graph](file:076bec8c-aba7-4928-92db-3d1808fe43e7)

## Running the Agent

We generate a unique user name and thread id, add these to Zep, and create our configured agent:
```

---

## Zep v2 to v3 migration

**URL:** llms-txt#zep-v2-to-v3-migration

**Contents:**
- Key Conceptual Changes
  - Sessions → Threads
  - Groups → Graphs
  - Message Role Changes
  - Enhanced Context Retrieval
- Migration Table

> Complete guide for upgrading from v2 to v3

This guide provides a comprehensive overview of migrating from Zep v2 to v3, including conceptual changes, method mappings, and functionality differences.

## Key Conceptual Changes

Zep v3 introduces several naming changes and some feature enhancements that developers familiar with v2 should understand:

### Sessions → Threads

In v2, you worked with **sessions** to manage conversation history. In v3, these are now called **threads**.

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

---

## Zep vs Graphiti

**URL:** llms-txt#zep-vs-graphiti

**Contents:**
- When to choose which

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

---

## Zep vs Graph RAG

**URL:** llms-txt#zep-vs-graph-rag

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

---
