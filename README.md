# ShopEasy Customer Service Agent

An AI-powered customer service agent for a fictional e-commerce store (ShopEasy), built with Claude and the Model Context Protocol (MCP). The agent handles refund requests, order lookups, ticket escalations, and general support queries in real time via a chat interface.

## Architecture

```
frontend (React + Vite)
    │
    │  WebSocket (streaming)
    ▼
backend (FastAPI)
    │  Claude claude-opus-4-5 + MCP tools
    ├──▶ MCP Server: knowledge-base  (port 8001)
    ├──▶ MCP Server: crm             (port 8002)
    └──▶ MCP Server: actions         (port 8003)
```

The backend runs an agentic loop: Claude decides which MCP tools to call, executes them, and streams the response token-by-token to the frontend over WebSocket.

## MCP Servers

| Server | Port | Tools |
|---|---|---|
| `knowledge-base` | 8001 | `search_faqs`, `search_docs` |
| `crm` | 8002 | `get_customer`, `get_order`, `get_orders_by_customer`, `get_ticket_history` |
| `actions` | 8003 | `issue_refund`, `escalate_ticket`, `send_email`, `create_ticket` |

## Agent Skills

The agent's behavior is defined by three skill files loaded as its system prompt:

- **Refund Policy** — rules for full, partial, and no-refund scenarios
- **Escalation Rules** — when and how to escalate (legal threats, fraud, VIP customers, repeated issues)
- **Tone Guidelines** — communication style, empathy, and clarity standards

## Project Structure

```
CustomerService/
├── backend/
│   ├── main.py              # FastAPI app — REST + WebSocket endpoints
│   ├── agent.py             # Agentic loop (Claude + MCP tool execution)
│   ├── requirements.txt
│   ├── .env.example
│   └── skills/
│       ├── refund_policy.md
│       ├── escalation_rules.md
│       └── tone_guidelines.md
├── frontend/
│   ├── src/                 # React components
│   ├── index.html
│   └── package.json
└── mcp-servers/
    ├── crm/
    │   ├── server.py
    │   └── data/            # customers.json, orders.json
    ├── knowledge-base/
    │   ├── server.py
    │   └── data/            # faqs.json, docs.json
    └── actions/
        └── server.py
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

uvicorn main:app --reload --port 8000
```

### 2. MCP Servers

Open three terminal tabs and run each server:

```bash
# Terminal 1
cd mcp-servers/knowledge-base
python server.py

# Terminal 2
cd mcp-servers/crm
python server.py

# Terminal 3
cd mcp-servers/actions
python server.py
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Single-turn chat (for testing) |
| `WS` | `/ws` | Streaming WebSocket chat |

### WebSocket Events

**Send:**
```json
{ "text": "I need a refund for order ORD-1001" }
```

**Receive:**
```json
{ "type": "tool_call",   "name": "get_order", "input": { "order_id": "ORD-1001" } }
{ "type": "tool_result", "name": "get_order", "result": "..." }
{ "type": "token",       "text": "Hi " }
{ "type": "done" }
```

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
