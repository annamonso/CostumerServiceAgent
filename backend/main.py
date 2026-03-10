import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from agent import run_agent  # noqa: E402 — must come after load_dotenv


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="ShopEasy Customer Service API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok"}


@app.post("/chat")
async def chat(body: dict):
    """Single-turn (non-streaming) chat endpoint — useful for testing."""
    messages = body.get("messages", [])
    if not messages:
        return {"error": "No messages provided"}

    result_text = ""
    tool_calls = []

    async for event in run_agent(messages):
        if event["type"] == "token":
            result_text += event["text"]
        elif event["type"] == "tool_call":
            tool_calls.append({"name": event["name"], "input": event["input"]})
        elif event["type"] == "error":
            return {"error": event["message"]}

    return {"response": result_text.strip(), "tool_calls": tool_calls}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Streaming WebSocket endpoint.

    Incoming message format:  {"text": "user message here"}

    Outgoing event types:
        {"type": "tool_call",   "name": str, "input": dict}
        {"type": "tool_result", "name": str, "result": str}
        {"type": "token",       "text": str}
        {"type": "done"}
        {"type": "error",       "message": str}
        {"type": "history_updated"}
    """
    await websocket.accept()
    conversation_history: list[dict] = []

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            user_text = message.get("text", "").strip()
            if not user_text:
                continue

            # Add user message to history
            conversation_history.append({"role": "user", "content": user_text})

            # Stream agent events to the client, collecting the full response text
            full_response = ""

            async for event in run_agent(list(conversation_history)):
                await websocket.send_text(json.dumps(event))

                if event["type"] == "token":
                    full_response += event["text"]
                elif event["type"] == "error":
                    # Remove the user message we just added so history stays consistent
                    conversation_history.pop()
                    break

            # Persist the assistant's complete response in history
            if full_response:
                conversation_history.append(
                    {"role": "assistant", "content": full_response.strip()}
                )
                await websocket.send_text(json.dumps({"type": "history_updated"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "message": str(e)})
            )
        except Exception:
            pass
