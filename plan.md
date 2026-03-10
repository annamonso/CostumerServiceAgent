# Customer Support Agent — Project Plan

## What We Are Building

A full-stack AI-powered customer support agent that:
- Accepts customer messages through a chat UI
- Uses Claude as the reasoning engine
- Dynamically calls **MCP tools** (search knowledge base, look up orders, issue refunds, escalate tickets)
- Applies **skills** (refund policy, escalation rules, tone guidelines) as injected context
- Streams responses back to the frontend in real time
- Shows the user which tools the agent called (transparency)

This is different from TripAdvisor's fixed LangGraph pipeline. Here, **Claude decides at runtime** which tools to call based on what the customer says. The path is never hardcoded.

---

## Project Structure

```
CustomerService/
├── plan.md                          ← this file
├── mcp-servers/                     # Three independent MCP microservices (HTTP/SSE)
│   ├── knowledge-base/
│   │   ├── server.py                # FastAPI + MCP over SSE, port 8001
│   │   ├── requirements.txt
│   │   └── data/
│   │       ├── faqs.json
│   │       └── docs.json
│   ├── crm/
│   │   ├── server.py                # FastAPI + MCP over SSE, port 8002
│   │   ├── requirements.txt
│   │   └── data/
│   │       ├── customers.json
│   │       └── orders.json
│   └── actions/
│       ├── server.py                # FastAPI + MCP over SSE, port 8003
│       └── requirements.txt
├── backend/
│   ├── main.py                      # FastAPI app with WebSocket + REST, port 8000
│   ├── agent.py                     # Claude agentic loop + MCP client connections (HTTP)
│   ├── skills/
│   │   ├── refund_policy.md         # When/how to refund
│   │   ├── escalation_rules.md      # When to escalate to a human
│   │   └── tone_guidelines.md       # How the agent should communicate
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── components/
            ├── ChatWindow.jsx        # Full chat container
            ├── MessageBubble.jsx     # Single message (user or agent)
            ├── ToolCallBadge.jsx     # Shows which MCP tool fired
            └── AgentStatusBar.jsx    # "Agent is thinking..." indicator
```

---

## Key Concepts Explained

### MCP (Model Context Protocol)

MCP is a **standardized protocol** for exposing tools to an LLM. Instead of hardcoding tool functions in your agent code, you run separate **MCP server processes** that expose tools. The agent connects to them and Claude can call any tool dynamically.

**Why this matters:**
- Tools live in their own processes — independently maintainable
- The same MCP server can be used by multiple agents
- Claude discovers tools at runtime, not at design time
- You can add/remove tools without touching agent code

**Transport:** We use **HTTP/SSE** — each MCP server runs as a standalone HTTP service on its own port. The agent connects to them over the network, not by spawning subprocesses. This means any agent (now or in the future) can connect to the same running servers without any changes.

```
Agent Backend (port 8000)
    │
    ├── HTTP/SSE → mcp-servers/knowledge-base/server.py  (port 8001)
    ├── HTTP/SSE → mcp-servers/crm/server.py             (port 8002)
    └── HTTP/SSE → mcp-servers/actions/server.py         (port 8003)
```

**Why HTTP/SSE instead of stdio:**

| | stdio | HTTP/SSE (our choice) |
|---|---|---|
| How it runs | Agent spawns the server as a subprocess | Server runs independently on its own port |
| Reusability | One agent = one instance | Any number of agents can connect |
| Lifecycle | Dies when the agent dies | Runs permanently, like a real service |
| Future agents | Must relaunch the server | Just connect to the URL |
| Real-world equivalent | Local script | Microservice / internal API |

This is how you would deploy MCP servers in a real company — as internal services that any agent in the organisation can consume.

### Skills

Skills are **not tools** — they are structured knowledge injected into Claude's system prompt before the conversation starts. Claude reads them and uses them to reason correctly without calling any API.

| Skill | Purpose |
|---|---|
| `refund_policy.md` | Rules for when refunds are allowed (e.g. within 30 days, unused orders only) |
| `escalation_rules.md` | Conditions that require a human agent (fraud suspicion, VIP customers, legal threats) |
| `tone_guidelines.md` | Communication style: empathetic, concise, never blame the customer |

### The Agentic Loop

This is the heart of the system. Unlike TripAdvisor where the graph decides what runs, here **Claude decides**:

```
1. Customer sends message
2. Backend sends to Claude:
   - System prompt = skills (injected context)
   - Available tools = all MCP tools from all 3 servers
   - Messages = conversation history
3. Claude responds with either:
   a. tool_use block → agent executes the tool via MCP, returns result to Claude → loop continues
   b. text block → final response, stream to frontend
4. Repeat until Claude produces a text response
```

A single customer message might cause Claude to:
- Call `get_customer` → verify who they are
- Call `get_order` → check order status
- Call `issue_refund` → process the refund
- Call `send_email` → send confirmation
- Then write the final response

Or for a simple FAQ question, Claude might only call `search_faqs` and respond immediately.

### WebSocket Streaming

We use WebSockets (not HTTP polling) so the frontend receives:
- Tool call events in real time (shown as badges)
- Claude's response tokens as they stream
- Status events ("agent is thinking", "tool executed")

---

## The Three MCP Servers

### 1. Knowledge Base Server

**File:** `mcp-servers/knowledge-base/server.py`

**Tools exposed:**

| Tool | Input | Output |
|---|---|---|
| `search_faqs` | `query: str` | List of matching FAQ entries (question + answer) |
| `search_docs` | `topic: str` | Relevant documentation sections |

**Data:** JSON files with mock FAQs about a fictional e-commerce company (shipping policies, return windows, product info, account management).

**How it works:** Simple keyword/substring search over the JSON data. No vector DB needed for this prototype — keep it simple.

---

### 2. CRM Server

**File:** `mcp-servers/crm/server.py`

**Tools exposed:**

| Tool | Input | Output |
|---|---|---|
| `get_customer` | `email: str` | Customer name, plan, account status, customer ID |
| `get_order` | `order_id: str` | Items, price, status, delivery date, eligible for refund |
| `get_ticket_history` | `customer_id: str` | Past support tickets and resolutions |

**Data:** JSON files with mock customers and orders. About 10 customers and 20 orders to make it realistic.

**Why it's separate from actions:** Read operations (CRM) vs write operations (actions) are intentionally split. This mirrors real company architecture where data access and mutations go through different systems.

---

### 3. Actions Server

**File:** `mcp-servers/actions/server.py`

**Tools exposed:**

| Tool | Input | Output |
|---|---|---|
| `issue_refund` | `order_id: str, reason: str` | Confirmation ID, refund amount, timeline |
| `escalate_ticket` | `customer_id: str, reason: str, priority: str` | Ticket ID, assigned agent |
| `send_email` | `to: str, subject: str, body: str` | Delivery confirmation |
| `create_ticket` | `customer_id: str, issue: str, category: str` | Ticket ID |

**Important:** These are mock implementations — they don't call real payment processors. They simulate the action and return realistic confirmation data. This is intentional for learning purposes.

---

## Backend

### `main.py` — FastAPI Entry Point

Two endpoints:

1. **`POST /chat`** — single-turn (for testing)
2. **`WS /ws`** — WebSocket for real-time streaming chat

The WebSocket endpoint:
- Accepts customer messages
- Passes to `agent.py`
- Streams back tool call events + response tokens

### `agent.py` — The Claude Agentic Loop

This is the most important file. It:

1. Loads all skills from `skills/` directory into the system prompt
2. Connects to all 3 MCP servers via HTTP/SSE (by URL, not subprocess)
3. Collects all available tools from all servers
4. Runs the agentic loop:
   - Sends messages to Claude with tools
   - Handles `tool_use` responses by routing to the right MCP server
   - Collects `tool_result` and feeds back to Claude
   - Yields events (tool calls, tokens) for the WebSocket to stream
5. Returns the final response

**Key pattern — the loop:**
```python
while True:
    response = claude.messages.create(...)
    if response.stop_reason == "tool_use":
        # execute tools, add results to messages, loop again
    elif response.stop_reason == "end_turn":
        # stream final text, break
```

---

## Frontend

### Chat UI

A minimal but functional chat interface with one special feature: **tool call transparency**.

**Components:**

- **`ChatWindow.jsx`** — manages message list and WebSocket connection
- **`MessageBubble.jsx`** — renders user or agent message
- **`ToolCallBadge.jsx`** — inline badge showing `🔧 get_order(order_id: 1234)` as tools fire
- **`AgentStatusBar.jsx`** — pulsing "Agent is thinking..." while Claude reasons

**Message flow on the frontend:**

```
WebSocket message received
    ├── type: "tool_call"   → render ToolCallBadge
    ├── type: "token"       → append to current agent message (streaming)
    └── type: "done"        → finalize message
```

**UI layout:**
```
┌────────────────────────────────────────┐
│  🤖 Customer Support                   │
│  ──────────────────────────────────── │
│                                        │
│  [User]: My order #1234 never arrived  │
│                                        │
│  🔧 get_customer(anna@email.com)       │
│  🔧 get_order(order_id: 1234)          │
│  🔧 issue_refund(1234, "not arrived")  │
│  🔧 send_email(anna@email.com, ...)    │
│                                        │
│  [Agent]: Hi Anna! I'm sorry to hear   │
│  that. I've issued a full refund of    │
│  $49.99 for order #1234. You'll see    │
│  it in 3–5 business days...            │
│                                        │
│  ──────────────────────────────────── │
│  [Type your message...]         [Send] │
└────────────────────────────────────────┘
```

---

## Development Strategy — Step by Step

### Phase 1 — Mock Data + MCP Microservices

**Goal:** Get all 3 MCP servers running as standalone HTTP services, testable in isolation.

Steps:
1. Write `customers.json` and `orders.json` (mock data)
2. Write `faqs.json` and `docs.json` (mock knowledge base)
3. Build `crm/server.py` — MCP over HTTP/SSE on port 8002, expose `get_customer`, `get_order`, `get_ticket_history`
4. Build `knowledge-base/server.py` — MCP over HTTP/SSE on port 8001, expose `search_faqs`, `search_docs`
5. Build `actions/server.py` — MCP over HTTP/SSE on port 8003, expose `issue_refund`, `escalate_ticket`, `send_email`, `create_ticket`
6. Test each server independently by hitting its SSE endpoint directly

Each server is started with `python server.py` and keeps running. The agent connects to it by URL — it does not launch or own the server process.

**Deliverable:** 3 running MCP microservices on ports 8001, 8002, 8003, each testable independently.

---

### Phase 2 — Skills

**Goal:** Write the 3 skill files that shape Claude's behavior.

Steps:
1. Write `refund_policy.md` — e.g., refunds allowed within 30 days, full refund if item not delivered, partial refund if opened
2. Write `escalation_rules.md` — e.g., escalate if customer mentions "lawyer", "fraud", or is a VIP (plan: enterprise)
3. Write `tone_guidelines.md` — empathetic opening, clear action summary, no jargon, always confirm what was done

**Deliverable:** 3 skill files that can be read and injected into the system prompt.

---

### Phase 3 — Agent Backend

**Goal:** Claude can receive a message, call MCP tools, and return a response.

Steps:
1. Set up FastAPI app with a simple `POST /chat` endpoint
2. Write the MCP client connection logic (connect by URL to ports 8001, 8002, 8003)
3. Write the agentic loop in `agent.py`
4. Load skills into system prompt
5. Test end-to-end with curl: send a message, see tool calls, get response
6. Add WebSocket endpoint for streaming

**Deliverable:** Working agent accessible via curl or WebSocket.

---

### Phase 4 — Frontend

**Goal:** Chat UI connected to the agent via WebSocket.

Steps:
1. Scaffold React + Vite + TailwindCSS project
2. Build `ChatWindow` with WebSocket connection
3. Build `MessageBubble` for user and agent messages
4. Build `ToolCallBadge` — rendered inline as tools fire
5. Build `AgentStatusBar` — shows when Claude is reasoning
6. Wire everything together and test full flow

**Deliverable:** Working chat UI, tool calls visible in real time.

---

### Phase 5 — Polish & Test Scenarios

**Goal:** Make it feel real with good test cases.

Test scenarios to verify the agent behaves correctly:

| Customer message | Expected tool calls | Expected behavior |
|---|---|---|
| "What's your return policy?" | `search_faqs` | Answers from knowledge base, no write actions |
| "Where is my order #1234?" | `get_customer`, `get_order` | Gives order status |
| "My order never arrived, I want a refund" | `get_customer`, `get_order`, `issue_refund`, `send_email` | Full refund flow |
| "This is fraud, I'm calling my lawyer" | `get_customer`, `escalate_ticket` | Escalates, doesn't try to resolve itself |
| "I can't log into my account" | `search_docs`, `get_customer` | Guides through account recovery |

---

## Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| MCP servers | Python `mcp` SDK | Standard protocol, easy to build servers |
| Agent backend | FastAPI + Anthropic SDK | Same stack as TripAdvisor, you know it |
| Skills | Markdown files | Simple, readable, easy to edit |
| Frontend | React + Vite + TailwindCSS | Same stack as TripAdvisor |
| Transport | WebSocket | Real-time streaming of tokens + tool calls |
| Data | JSON files | No database needed for prototype |
| MCP transport | HTTP/SSE | Servers run independently, reusable by any agent |

---

## API Keys Needed

| Key | Used for | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude (the reasoning engine) | Yes |

No other external APIs needed — all tools are mock implementations backed by JSON files. This keeps the focus on the MCP + agent architecture, not on API integrations.

---

## Ports Reference

| Service | Port | Started by |
|---|---|---|
| Agent backend | 8000 | `uvicorn main:app --reload` in `backend/` |
| Knowledge Base MCP | 8001 | `python server.py` in `mcp-servers/knowledge-base/` |
| CRM MCP | 8002 | `python server.py` in `mcp-servers/crm/` |
| Actions MCP | 8003 | `python server.py` in `mcp-servers/actions/` |
| Frontend | 5173 | `npm run dev` in `frontend/` |

Each MCP server must be started before the agent backend. They run permanently and independently — if you build a second agent tomorrow, it connects to the same running servers on the same ports.

---

## What You Will Learn

By the end of this project you will understand:

1. **How to build an MCP server as a microservice** — running on HTTP/SSE, independently of any agent
2. **How the Claude agentic loop works** — `tool_use` → execute → `tool_result` → loop
3. **How skills differ from tools** — static injected context vs dynamic callable functions
4. **How dynamic tool selection works** — Claude picks tools based on the message, not a fixed graph
5. **How to stream agentic responses** — WebSocket events for tool calls + tokens
6. **Why MCP over HTTP beats stdio** — tools are reusable services, not agent-owned subprocesses

---

## What We Build Next

Once this plan is clear, we build in order:

- [ ] Phase 1: Mock data + 3 MCP servers
- [ ] Phase 2: Skills (3 markdown files)
- [ ] Phase 3: Agent backend (FastAPI + Claude loop)
- [ ] Phase 4: Frontend (React chat UI)
- [ ] Phase 5: Test scenarios + polish
