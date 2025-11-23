# Graphiti - Api

**Pages:** 49

---

## Add Data

**URL:** llms-txt#add-data

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph
Content-Type: application/json

Add data to the graph.

Reference: https://help.getzep.com/sdk-reference/graph/add

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.add({
    data: "data",
    type: "text"
});
```

Example 4 (go):
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

---

## Add Data in batch mode

**URL:** llms-txt#add-data-in-batch-mode

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph-batch
Content-Type: application/json

Add data to the graph in batch mode, processing episodes concurrently. Use only for data that is insensitive to processing order.

Reference: https://help.getzep.com/sdk-reference/graph/add-batch

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
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

Example 4 (go):
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

---

## Add Fact Triple

**URL:** llms-txt#add-fact-triple

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/add-fact-triple
Content-Type: application/json

Add a fact triple for a user or group

Reference: https://help.getzep.com/sdk-reference/graph/add-fact-triple

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.addFactTriple({
    fact: "fact",
    factName: "fact_name",
    targetNodeName: "target_node_name"
});
```

Example 4 (go):
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

---

## Add messages to a thread

**URL:** llms-txt#add-messages-to-a-thread

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/threads/{threadId}/messages
Content-Type: application/json

Add messages to a thread.

Reference: https://help.getzep.com/sdk-reference/thread/add-messages

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
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

Example 4 (go):
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

---

## Add messages to a thread in batch

**URL:** llms-txt#add-messages-to-a-thread-in-batch

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/threads/{threadId}/messages-batch
Content-Type: application/json

Add messages to a thread in batch mode. This will process messages concurrently, which is useful for data migrations.

Reference: https://help.getzep.com/sdk-reference/thread/add-messages-batch

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
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

Example 4 (go):
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

---

## Add User

**URL:** llms-txt#add-user

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/users
Content-Type: application/json

Reference: https://help.getzep.com/sdk-reference/user/add

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.add(
    user_id="user_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.add({
    userId: "user_id"
});
```

Example 4 (go):
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

---

## Add User Instructions

**URL:** llms-txt#add-user-instructions

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/user-summary-instructions
Content-Type: application/json

Adds new summary instructions for users graphs without removing existing ones. If user_ids is empty, adds to project-wide default instructions.

Reference: https://help.getzep.com/sdk-reference/user/add-user-summary-instructions

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
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

Example 4 (go):
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

---

## Clone graph

**URL:** llms-txt#clone-graph

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/clone
Content-Type: application/json

Clone a user or group graph.

Reference: https://help.getzep.com/sdk-reference/graph/clone

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.clone()
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.clone();
```

Example 4 (go):
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

---

## Create Graph

**URL:** llms-txt#create-graph

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/create
Content-Type: application/json

Reference: https://help.getzep.com/sdk-reference/graph/create

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.create(
    graph_id="graph_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.create({
    graphId: "graph_id"
});
```

Example 4 (go):
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

---

## Delete Edge

**URL:** llms-txt#delete-edge

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.getzep.com/api/v2/graph/edge/{uuid}

Deletes an edge by UUID.

Reference: https://help.getzep.com/sdk-reference/graph/edge/delete

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.delete(
    uuid_="uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.delete("uuid");
```

Example 4 (go):
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

---

## Delete Episode

**URL:** llms-txt#delete-episode

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.getzep.com/api/v2/graph/episodes/{uuid}

Deletes an episode by its UUID.

Reference: https://help.getzep.com/sdk-reference/graph/episode/delete

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.delete(
    uuid_="uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.delete("uuid");
```

Example 4 (go):
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

---

## Delete Graph

**URL:** llms-txt#delete-graph

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.getzep.com/api/v2/graph/{graphId}

Deletes a graph. If you would like to delete a user graph, make sure to use user.delete instead.

Reference: https://help.getzep.com/sdk-reference/graph/delete

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.delete(
    graph_id="graphId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.delete("graphId");
```

Example 4 (go):
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

---

## Delete thread

**URL:** llms-txt#delete-thread

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.getzep.com/api/v2/threads/{threadId}

Reference: https://help.getzep.com/sdk-reference/thread/delete

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.delete(
    thread_id="threadId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.delete("threadId");
```

Example 4 (go):
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

---

## Delete User

**URL:** llms-txt#delete-user

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.getzep.com/api/v2/users/{userId}

Reference: https://help.getzep.com/sdk-reference/user/delete

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.delete(
    user_id="userId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.delete("userId");
```

Example 4 (go):
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

---

## Delete User Instructions

**URL:** llms-txt#delete-user-instructions

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.getzep.com/api/v2/user-summary-instructions
Content-Type: application/json

Deletes user summary/instructions for users or project wide defaults.

Reference: https://help.getzep.com/sdk-reference/user/delete-user-summary-instructions

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.delete_user_summary_instructions()
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.deleteUserSummaryInstructions();
```

Example 4 (go):
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

---

## format: allergy: True/False; preference_type: PREFERENCE_TYPE (Date range: from - to)

**URL:** llms-txt#format:-allergy:-true/false;-preference_type:-preference_type-(date-range:-from---to)

<DIETARY_PREFERENCES>
  - allergy: False; preference_type: vegetarian (Date range: 2025-06-16T02:17:25Z - present)
  - allergy: False; preference_type: lactose intolerance (Date range: 2025-06-16T02:17:25Z - present)
</DIETARY_PREFERENCES>

---

## Get Edge

**URL:** llms-txt#get-edge

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/edge/{uuid}

Returns a specific edge by its UUID.

Reference: https://help.getzep.com/sdk-reference/graph/edge/get

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.get(
    uuid_="uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.get("uuid");
```

Example 4 (go):
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

---

## Get Entity Edges for a node

**URL:** llms-txt#get-entity-edges-for-a-node

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/node/{node_uuid}/entity-edges

Returns all edges for a node

Reference: https://help.getzep.com/sdk-reference/graph/node/get-edges

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_edges(
    node_uuid="node_uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getEdges("node_uuid");
```

Example 4 (go):
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

---

## Get Episodes for a node

**URL:** llms-txt#get-episodes-for-a-node

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/node/{node_uuid}/episodes

Returns all episodes that mentioned a given node

Reference: https://help.getzep.com/sdk-reference/graph/node/get-episodes

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_episodes(
    node_uuid="node_uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getEpisodes("node_uuid");
```

Example 4 (go):
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

---

## Get Episode

**URL:** llms-txt#get-episode

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/episodes/{uuid}

Returns episodes by UUID

Reference: https://help.getzep.com/sdk-reference/graph/episode/get

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get(
    uuid_="uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.get("uuid");
```

Example 4 (go):
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

---

## Get Graph

**URL:** llms-txt#get-graph

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/{graphId}

Reference: https://help.getzep.com/sdk-reference/graph/get

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.get(
    graph_id="graphId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.get("graphId");
```

Example 4 (go):
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

---

## Get Graph Edges

**URL:** llms-txt#get-graph-edges

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/edge/graph/{graph_id}
Content-Type: application/json

Returns all edges for a graph.

Reference: https://help.getzep.com/sdk-reference/graph/edge/get-by-graph-id

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.get_by_graph_id(
    graph_id="graph_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.getByGraphId("graph_id", {});
```

Example 4 (go):
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

---

## Get Graph Episodes

**URL:** llms-txt#get-graph-episodes

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/episodes/graph/{graph_id}

Returns episodes by graph id.

Reference: https://help.getzep.com/sdk-reference/graph/episode/get-by-graph-id

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get_by_graph_id(
    graph_id="graph_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.getByGraphId("graph_id");
```

Example 4 (go):
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

---

## Get Graph Nodes

**URL:** llms-txt#get-graph-nodes

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/node/graph/{graph_id}
Content-Type: application/json

Returns all nodes for a graph.

Reference: https://help.getzep.com/sdk-reference/graph/node/get-by-graph-id

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_by_graph_id(
    graph_id="graph_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getByGraphId("graph_id", {});
```

Example 4 (go):
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

---

## Get messages of a thread

**URL:** llms-txt#get-messages-of-a-thread

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/threads/{threadId}/messages

Returns messages for a thread.

Reference: https://help.getzep.com/sdk-reference/thread/get

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.get(
    thread_id="threadId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.get("threadId");
```

Example 4 (go):
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

---

## Get Node

**URL:** llms-txt#get-node

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/node/{uuid}

Returns a specific node by its UUID.

Reference: https://help.getzep.com/sdk-reference/graph/node/get

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get(
    uuid_="uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.get("uuid");
```

Example 4 (go):
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

---

## Get threads

**URL:** llms-txt#get-threads

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/threads

Reference: https://help.getzep.com/sdk-reference/thread/list-all

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.list_all()
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.listAll();
```

Example 4 (go):
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

---

## Get Users

**URL:** llms-txt#get-users

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/users-ordered

Reference: https://help.getzep.com/sdk-reference/user/list-ordered

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.list_ordered()
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.listOrdered();
```

Example 4 (go):
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

---

## Get User

**URL:** llms-txt#get-user

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/users/{userId}

Reference: https://help.getzep.com/sdk-reference/user/get

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.get(
    user_id="userId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.get("userId");
```

Example 4 (go):
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

---

## Get user context

**URL:** llms-txt#get-user-context

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/threads/{threadId}/context

Returns most relevant context from the user graph (including memory from any/all past threads) based on the content of the past few messages of the given thread.

Reference: https://help.getzep.com/sdk-reference/thread/get-user-context

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.thread.get_user_context(
    thread_id="threadId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.getUserContext("threadId");
```

Example 4 (go):
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

---

## Get User Edges

**URL:** llms-txt#get-user-edges

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/edge/user/{user_id}
Content-Type: application/json

Returns all edges for a user.

Reference: https://help.getzep.com/sdk-reference/graph/edge/get-by-user-id

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.edge.get_by_user_id(
    user_id="user_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.edge.getByUserId("user_id", {});
```

Example 4 (go):
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

---

## Get User Episodes

**URL:** llms-txt#get-user-episodes

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/episodes/user/{user_id}

Returns episodes by user id.

Reference: https://help.getzep.com/sdk-reference/graph/episode/get-by-user-id

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get_by_user_id(
    user_id="user_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.getByUserId("user_id");
```

Example 4 (go):
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

---

## Get User Nodes

**URL:** llms-txt#get-user-nodes

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/node/user/{user_id}
Content-Type: application/json

Returns all nodes for a user

Reference: https://help.getzep.com/sdk-reference/graph/node/get-by-user-id

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.node.get_by_user_id(
    user_id="user_id",
)
```

Example 3 (typescript):
```typescript
import { ZepClient, Zep } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.node.getByUserId("user_id", {});
```

Example 4 (go):
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

---

## Get User Node

**URL:** llms-txt#get-user-node

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/users/{userId}/node

Returns a user's node.

Reference: https://help.getzep.com/sdk-reference/user/get-node

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.get_node(
    user_id="userId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.getNode("userId");
```

Example 4 (go):
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

---

## Get User Threads

**URL:** llms-txt#get-user-threads

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/users/{userId}/threads

Returns all threads for a user.

Reference: https://help.getzep.com/sdk-reference/user/get-threads

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.get_threads(
    user_id="userId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.getThreads("userId");
```

Example 4 (go):
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

---

## Google API key configuration

**URL:** llms-txt#google-api-key-configuration

api_key = "<your-google-api-key>"

---

## List all graphs.

**URL:** llms-txt#list-all-graphs.

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/list-all

Returns all graphs. In order to list users, use user.list_ordered instead

Reference: https://help.getzep.com/sdk-reference/graph/list-all

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.list_all()
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.listAll();
```

Example 4 (go):
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

---

## List graph ontology

**URL:** llms-txt#list-graph-ontology

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/list-ontology

Retrieves the current entity and edge types configured for your graph.

See the [full documentation](/customizing-graph-structure) for details.

Reference: https://help.getzep.com/sdk-reference/graph/list-ontology

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud.client import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
ontology = client.graph.list_ontology()
print("Entity types:", ontology.entity_types)
print("Edge types:", ontology.edge_types)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
const ontology = await client.graph.listOntology();
console.log("Entity types:", ontology.entityTypes);
console.log("Edge types:", ontology.edgeTypes);
```

Example 4 (go):
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

---

## List User Instructions

**URL:** llms-txt#list-user-instructions

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/user-summary-instructions

Lists all user summary instructions for a project, user.

Reference: https://help.getzep.com/sdk-reference/user/list-user-summary-instructions

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.list_user_summary_instructions()
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.listUserSummaryInstructions();
```

Example 4 (go):
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

---

## Retrieves project information

**URL:** llms-txt#retrieves-project-information

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/projects/info

Retrieve project info based on the provided api key.

Reference: https://help.getzep.com/sdk-reference/project/get

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.project.get()
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.project.get();
```

Example 4 (go):
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

---

## Return any nodes and edges mentioned in an episode

**URL:** llms-txt#return-any-nodes-and-edges-mentioned-in-an-episode

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/graph/episodes/{uuid}/mentions

Returns nodes and edges mentioned in an episode

Reference: https://help.getzep.com/sdk-reference/graph/episode/get-nodes-and-edges

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.episode.get_nodes_and_edges(
    uuid_="uuid",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.episode.getNodesAndEdges("uuid");
```

Example 4 (go):
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

---

## Search Graph

**URL:** llms-txt#search-graph

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/graph/search
Content-Type: application/json

Perform a graph search query.

Reference: https://help.getzep.com/sdk-reference/graph/search

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.search(
    query="query",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.search({
    query: "query"
});
```

Example 4 (go):
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

---

## Set graph ontology

**URL:** llms-txt#set-graph-ontology

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PUT https://api.getzep.com/api/v2/graph/set-ontology
Content-Type: application/json

Sets custom entity and edge types for your graph. This wrapper method
provides a clean interface for defining your graph schema with custom
entity and edge types.

See the [full documentation](/customizing-graph-structure#setting-entity-and-edge-types) for details.

Reference: https://help.getzep.com/sdk-reference/graph/set-ontology

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
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

Example 4 (go):
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

---

## Start a new thread.

**URL:** llms-txt#start-a-new-thread.

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.getzep.com/api/v2/threads
Content-Type: application/json

Reference: https://help.getzep.com/sdk-reference/thread/create

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.create({
    threadId: "thread_id",
    userId: "user_id"
});
```

Example 4 (go):
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

---

## These are the most relevant dietary preferences of the user, whether they represent an allergy, and their valid date ranges

**URL:** llms-txt#these-are-the-most-relevant-dietary-preferences-of-the-user,-whether-they-represent-an-allergy,-and-their-valid-date-ranges

---

## Updates a message.

**URL:** llms-txt#updates-a-message.

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.getzep.com/api/v2/messages/{messageUUID}
Content-Type: application/json

Reference: https://help.getzep.com/sdk-reference/thread/message/update

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
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

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.thread.message.update("messageUUID", {
    metadata: {
        "key": "value"
    }
});
```

Example 4 (go):
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

---

## Update Graph.

**URL:** llms-txt#update-graph.

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.getzep.com/api/v2/graph/{graphId}
Content-Type: application/json

Updates information about a graph.

Reference: https://help.getzep.com/sdk-reference/graph/update

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.graph.update(
    graph_id="graphId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.graph.update("graphId");
```

Example 4 (go):
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

---

## Update User

**URL:** llms-txt#update-user

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.getzep.com/api/v2/users/{userId}
Content-Type: application/json

Reference: https://help.getzep.com/sdk-reference/user/update

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.update(
    user_id="userId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.update("userId");
```

Example 4 (go):
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

---

## Warm User Cache

**URL:** llms-txt#warm-user-cache

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.getzep.com/api/v2/users/{userId}/warm

Hints Zep to warm a user's graph for low-latency search

Reference: https://help.getzep.com/sdk-reference/user/warm

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
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

Example 2 (python):
```python
from zep_cloud import Zep

client = Zep(
    api_key="YOUR_API_KEY",
)
client.user.warm(
    user_id="userId",
)
```

Example 3 (typescript):
```typescript
import { ZepClient } from "zep-cloud";

const client = new ZepClient({ apiKey: "YOUR_API_KEY" });
await client.user.warm("userId");
```

Example 4 (go):
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

---
