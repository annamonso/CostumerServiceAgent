import React, { useState, useEffect, useRef, useCallback } from 'react'
import MessageBubble from './MessageBubble'
import AgentStatusBar from './AgentStatusBar'

const WS_URL = 'ws://localhost:8000/ws'

let messageIdCounter = 0
function nextId() {
  return ++messageIdCounter
}

/**
 * ChatWindow
 * Main chat component. Manages WebSocket connection and all chat state.
 *
 * Message shape: { id, role, text, toolCalls }
 */
export default function ChatWindow() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)

  const wsRef = useRef(null)
  const bottomRef = useRef(null)
  // Track the id of the assistant message currently being streamed
  const streamingIdRef = useRef(null)
  // Accumulate pending tool calls for the current response
  const pendingToolCallsRef = useRef([])

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setError(null)
    }

    ws.onclose = () => {
      setConnected(false)
      // Attempt reconnect after 3 s
      setTimeout(connectWebSocket, 3000)
    }

    ws.onerror = () => {
      setError('Could not connect to the support agent. Retrying...')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'tool_call') {
        // Accumulate tool calls; they'll be attached to the assistant message
        pendingToolCallsRef.current = [
          ...pendingToolCallsRef.current,
          { name: data.name, input: data.input },
        ]
        // Create or update the streaming assistant message to show tool badges immediately
        setMessages((prev) => {
          const existingIdx = prev.findIndex((m) => m.id === streamingIdRef.current)
          if (existingIdx === -1) {
            const newId = nextId()
            streamingIdRef.current = newId
            return [
              ...prev,
              {
                id: newId,
                role: 'assistant',
                text: '',
                toolCalls: [...pendingToolCallsRef.current],
              },
            ]
          }
          // Update tool calls on existing streaming message
          const updated = [...prev]
          updated[existingIdx] = {
            ...updated[existingIdx],
            toolCalls: [...pendingToolCallsRef.current],
          }
          return updated
        })
      } else if (data.type === 'token') {
        setMessages((prev) => {
          const existingIdx = prev.findIndex((m) => m.id === streamingIdRef.current)
          if (existingIdx === -1) {
            // First token — create the assistant message
            const newId = nextId()
            streamingIdRef.current = newId
            return [
              ...prev,
              {
                id: newId,
                role: 'assistant',
                text: data.text,
                toolCalls: [...pendingToolCallsRef.current],
              },
            ]
          }
          // Append token to existing streaming message
          const updated = [...prev]
          updated[existingIdx] = {
            ...updated[existingIdx],
            text: updated[existingIdx].text + data.text,
          }
          return updated
        })
      } else if (data.type === 'done') {
        setIsThinking(false)
        streamingIdRef.current = null
        pendingToolCallsRef.current = []
      } else if (data.type === 'error') {
        setIsThinking(false)
        setError(data.message || 'An unexpected error occurred.')
        streamingIdRef.current = null
        pendingToolCallsRef.current = []
      }
      // 'history_updated' — no UI action needed
    }
  }, [])

  useEffect(() => {
    connectWebSocket()
    return () => {
      wsRef.current?.close()
    }
  }, [connectWebSocket])

  const sendMessage = () => {
    const text = input.trim()
    if (!text || !connected || isThinking) return

    setError(null)

    // Optimistically add user message
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: 'user', text, toolCalls: [] },
    ])
    setInput('')
    setIsThinking(true)

    wsRef.current.send(JSON.stringify({ text }))
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto bg-white shadow-xl">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-200 bg-white">
        <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-xl">
          🤖
        </div>
        <div>
          <h1 className="font-semibold text-gray-900 text-base leading-tight">
            Customer Support
          </h1>
          <p className="text-xs text-gray-500 leading-tight">
            {connected ? (
              <span className="text-green-500">Connected — ShopEasy AI Agent</span>
            ) : (
              <span className="text-red-400">Connecting...</span>
            )}
          </p>
        </div>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-5 flex flex-col gap-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 text-sm mt-10">
            <p className="text-3xl mb-2">👋</p>
            <p>Hi! I'm the ShopEasy support agent.</p>
            <p>How can I help you today?</p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role}
            text={msg.text}
            toolCalls={msg.toolCalls}
          />
        ))}

        {/* Agent thinking indicator */}
        <AgentStatusBar isThinking={isThinking} />

        {/* Error banner */}
        {error && (
          <div className="text-xs text-red-500 bg-red-50 border border-red-200 rounded px-3 py-2 text-center">
            {error}
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="flex items-end gap-2">
          <textarea
            className="flex-1 resize-none rounded-xl border border-gray-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 outline-none px-3 py-2.5 text-sm text-gray-800 placeholder-gray-400 max-h-36 min-h-[44px]"
            rows={1}
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!connected || isThinking}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || !connected || isThinking}
            className="flex-shrink-0 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-200 disabled:cursor-not-allowed text-white rounded-xl px-4 py-2.5 text-sm font-medium transition-colors"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-1.5 pl-1">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
