# How MCP and Tools Connect with Claude

This document explains everything from scratch — what happens at each step when Claude uses a tool, and how MCP fits into that picture.

---

## Start Here: Claude Cannot Do Anything By Itself

Claude is a text model. Left alone, all it can do is read text and write text. It cannot:
- Look up a database
- Send an emaI want you to reaserch on MCP and how does it works with agents as microservices. Find papersil
- Check an order status
- Call any external system

To give Claude the ability to *act*, you have to provide **tools**. Tools are the only way Claude can interact with the outside world.

---

## What Is a Tool (From Claude's Perspective)

A tool is a **description** that you send to Claude alongside the conversation. It tells Claude:
- What the tool is called
- What it does
- What inputs it needs

That's it. Claude never sees the actual code behind the tool. It only sees the description.

Here is what a tool description looks like in the API request you send to Claude:

```json
{
  "name": "get_order",
  "description": "Look up an order by its ID. Returns the order status, items, price, and delivery date.",
  "input_schema": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "The order ID, e.g. ORD-1234"
      }
    },
    "required": ["order_id"]
  }
}
```

Claude reads this description and understands: "I have a tool called `get_order`. If the customer asks about an order, I should call it and pass the order ID."

---

## The Full Flow, Step by Step

Let's trace exactly what happens when a customer sends: **"Where is my order #1234?"**

---

### Step 1 — Your Code Sends a Request to Claude

Your agent (your Python code) sends an HTTP request to Anthropic's API. That request contains:

1. The conversation so far (customer message)
2. The system prompt (your skills / instructions)
3. The list of tool descriptions

```
YOUR AGENT  ──── HTTP POST ────►  ANTHROPIC API (Claude)

Request body:
{
  "model": "claude-sonnet-4-6",
  "system": "You are a customer support agent...",
  "messages": [
    { "role": "user", "content": "Where is my order #1234?" }
  ],
  "tools": [
    { "name": "get_customer", "description": "...", "input_schema": {...} },
    { "name": "get_order",    "description": "...", "input_schema": {...} },
    { "name": "issue_refund", "description": "...", "input_schema": {...} }
  ]
}
```

Claude receives all of this and starts reasoning.

---

### Step 2 — Claude Decides to Use a Tool

Claude reads the customer message and the tool descriptions. It decides:
- "The customer wants to know about order #1234. I should call `get_order`."

Claude responds — but NOT with text. It responds with a **tool_use block**:

```
ANTHROPIC API (Claude)  ──── HTTP response ────►  YOUR AGENT

Response body:
{
  "stop_reason": "tool_use",
  "content": [
    {
      "type": "tool_use",
      "id": "call_abc123",
      "name": "get_order",
      "input": { "order_id": "1234" }
    }
  ]
}
```

`stop_reason: "tool_use"` means: Claude is pausing. It wants you to run a tool and bring back the result.

**Important:** Claude cannot run the tool itself. It just tells you what tool to run and with what inputs. YOU run it.

---

### Step 3 — Your Code Executes the Tool

Your agent reads the `tool_use` block, sees it wants `get_order` with `order_id: "1234"`, and executes that tool.

In this project, executing the tool means sending a request to the CRM MCP server:

```
YOUR AGENT  ──── HTTP ────►  CRM MCP SERVER (port 8002)
                              calls get_order("1234")
                              looks up orders.json
                              returns result

CRM MCP SERVER  ──── response ────►  YOUR AGENT

Result:
{
  "order_id": "1234",
  "status": "in transit",
  "items": ["Blue sneakers - size 38"],
  "price": 89.99,
  "estimated_delivery": "2026-03-12"
}
```

---

### Step 4 — Your Code Sends the Result Back to Claude

Now your agent takes that result and sends it back to Claude in a new API call. The conversation now includes:
1. The original user message
2. Claude's tool_use request
3. The tool result (from your code)

```
YOUR AGENT  ──── HTTP POST ────►  ANTHROPIC API (Claude)

Messages:
[
  { "role": "user",      "content": "Where is my order #1234?" },
  { "role": "assistant", "content": [{ "type": "tool_use", "name": "get_order", ... }] },
  { "role": "user",      "content": [{ "type": "tool_result", "tool_use_id": "call_abc123",
                                        "content": "{ order: 1234, status: in transit, ... }" }] }
]
```

---

### Step 5 — Claude Reads the Result and Responds

Claude now has the order data. It reasons: "The order is in transit, arriving March 12. I can answer the customer."

This time Claude responds with text:

```
ANTHROPIC API (Claude)  ──── HTTP response ────►  YOUR AGENT

Response body:
{
  "stop_reason": "end_turn",
  "content": [
    {
      "type": "text",
      "text": "Hi! Your order #1234 (Blue sneakers, size 38) is currently in transit
               and should arrive by March 12. Is there anything else I can help you with?"
    }
  ]
}
```

`stop_reason: "end_turn"` means Claude is done. Your agent streams this text to the frontend.

---

### The Loop in Code

This back-and-forth is called the **agentic loop**. In code it looks like this:

```python
messages = [{"role": "user", "content": customer_message}]

while True:
    # Send to Claude
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        system=skills,
        tools=all_mcp_tools,
        messages=messages
    )

    if response.stop_reason == "tool_use":
        # Claude wants to call a tool
        tool_call = response.content[0]           # e.g. get_order(order_id: "1234")
        result = execute_mcp_tool(tool_call)      # your code runs the tool

        # Add both Claude's request and the result to the conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": [{"type": "tool_result", ...result}]})
        # Loop again — Claude will read the result and decide what to do next

    elif response.stop_reason == "end_turn":
        # Claude is done — send the text response to the frontend
        final_text = response.content[0].text
        break
```

Claude might call 1 tool or 5 tools before producing a final answer. The loop runs until `stop_reason` is `end_turn`.

---

## Where Does MCP Come In?

Everything above describes how Claude and tools work. **MCP is about how your tool servers are built and connected.**

Without MCP, you would write the tool execution logic directly in your agent code:

```python
# Without MCP — tool logic lives inside the agent
def execute_tool(name, inputs):
    if name == "get_order":
        return lookup_order_in_database(inputs["order_id"])
    elif name == "issue_refund":
        return process_refund(inputs["order_id"])
    ...
```

This works but couples the tools to your agent. If you build a second agent, you copy and paste all that logic.

With MCP, the tool logic lives in **separate server processes** that speak the MCP protocol. Your agent connects to them over HTTP/SSE and asks: "what tools do you have?" and "please execute this tool."

```python
# With MCP — tool logic lives in separate servers
# Agent connects to servers at startup
crm_server    = connect_mcp("http://localhost:8002/mcp")
kb_server     = connect_mcp("http://localhost:8001/mcp")
action_server = connect_mcp("http://localhost:8003/mcp")

# Agent collects all tools from all servers
all_tools = crm_server.list_tools() + kb_server.list_tools() + action_server.list_tools()
# → [get_customer, get_order, get_ticket_history, search_faqs, search_docs,
#    issue_refund, escalate_ticket, send_email, create_ticket]

# These tool descriptions are sent to Claude in every API call (Step 1 above)

# When Claude returns a tool_use block (Step 3 above), the agent
# routes the call to the right MCP server
def execute_mcp_tool(tool_call):
    if tool_call.name in crm_server.tool_names:
        return crm_server.call_tool(tool_call.name, tool_call.input)
    elif tool_call.name in kb_server.tool_names:
        return kb_server.call_tool(tool_call.name, tool_call.input)
    elif tool_call.name in action_server.tool_names:
        return action_server.call_tool(tool_call.name, tool_call.input)
```

---

## The MCP Protocol Itself

When your agent connects to an MCP server over HTTP/SSE, two things happen:

### 1. Tool Discovery
The agent asks the server: "what tools do you have?"

```
AGENT  →  GET http://localhost:8002/mcp/tools
CRM SERVER  →  returns list of tool descriptions (same JSON schema format as above)
```

The agent collects these and sends them to Claude in every API call.

### 2. Tool Execution
When Claude asks for a tool (Step 3), the agent asks the server to run it:

```
AGENT  →  POST http://localhost:8002/mcp/call
           body: { "name": "get_order", "arguments": { "order_id": "1234" } }

CRM SERVER  →  runs the function, returns the result
```

That's MCP. It's a standardized way for an agent to discover and call tools that live in other processes.

---

## The Full Picture Together

```
CUSTOMER
   │ types message
   ▼
FRONTEND (React)
   │ sends via WebSocket
   ▼
AGENT BACKEND (port 8000)
   │
   ├─ 1. loads skills from skills/*.md into system prompt
   │
   ├─ 2. connects to MCP servers, collects all tool descriptions
   │       ├── Knowledge Base MCP (port 8001) → search_faqs, search_docs
   │       ├── CRM MCP (port 8002)            → get_customer, get_order, get_ticket_history
   │       └── Actions MCP (port 8003)        → issue_refund, escalate_ticket, send_email, create_ticket
   │
   ├─ 3. sends to Claude: { system, messages, tools }
   │
   ▼
CLAUDE (Anthropic API)
   │ reasons about the message
   │ returns tool_use block
   ▼
AGENT BACKEND
   │ routes to the right MCP server
   │ gets result back
   │ sends result back to Claude
   ▼
CLAUDE
   │ reads result, reasons again
   │ returns end_turn with text
   ▼
AGENT BACKEND
   │ streams text + tool call events
   ▼
FRONTEND
   │ renders tool call badges + agent response
   ▼
CUSTOMER sees the answer
```

---

## What Claude Knows vs What It Doesn't

| Claude knows | Claude does NOT know |
|---|---|
| Tool descriptions (name, what it does, inputs) | Your Python/server code |
| The result after you execute the tool | How the result was computed |
| Your system prompt (skills) | That MCP exists |
| The conversation history | Which server the tool came from |

Claude has no idea what MCP is. From its perspective, tools are just descriptions in the API request. The MCP protocol is entirely between your agent and the tool servers — Claude never sees it.

---

## Why Skills Are Different from Tools

**Tools** = things Claude can *call* to get data or trigger actions (dynamic, at runtime)

**Skills** = knowledge injected into the system prompt before the conversation starts (static)

Skills are just text. When your agent starts, it reads the markdown files and puts them in the system prompt:

```python
system_prompt = """
You are a customer support agent.

--- REFUND POLICY ---
Refunds are allowed within 30 days of purchase.
Full refund if item was never delivered.
Partial refund (50%) if item was opened.
No refund after 30 days unless item is defective.

--- ESCALATION RULES ---
Escalate immediately if the customer mentions: lawsuit, fraud, lawyer, regulatory body.
Escalate if customer is on the Enterprise plan (VIP).
...

--- TONE GUIDELINES ---
Always open with empathy.
Be concise. Never use jargon.
Always confirm what action was taken.
"""
```

Claude reads this and it shapes every decision it makes — when to escalate, when to refund, how to phrase things. No tool call needed. It's just part of how Claude thinks for the whole conversation.

---

## Summary

| Concept | What it is | Who uses it |
|---|---|---|
| **Tool description** | JSON schema telling Claude a tool exists | Sent by your agent to Claude |
| **tool_use block** | Claude's response asking you to run a tool | Returned by Claude to your agent |
| **tool_result** | The output of running the tool | Sent by your agent back to Claude |
| **Agentic loop** | The while loop that repeats until Claude is done | Your agent code |
| **MCP** | Standard protocol for tool servers | Between your agent and tool servers |
| **MCP server** | Standalone process that exposes tools over HTTP/SSE | Runs independently (port 8001/8002/8003) |
| **Skills** | Knowledge in the system prompt | Read by Claude before the conversation |
| **Anthropic API** | Where Claude lives | Called by your agent via HTTP |
