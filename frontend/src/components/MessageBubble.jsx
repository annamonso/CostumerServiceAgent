import React from 'react'
import ToolCallBadge from './ToolCallBadge'

/**
 * MessageBubble
 * Renders a single chat message with optional tool call badges.
 *
 * Props:
 *   role      {"user" | "assistant"}
 *   text      {string}
 *   toolCalls {Array<{name: string, input: object}>}
 */
export default function MessageBubble({ role, text, toolCalls = [] }) {
  const isUser = role === 'user'

  return (
    <div className={`flex items-end gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Avatar — left side for assistant */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-base select-none">
          🤖
        </div>
      )}

      <div className={`flex flex-col gap-1 max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Tool call badges — shown above the message text */}
        {toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {toolCalls.map((tc, i) => (
              <ToolCallBadge key={i} name={tc.name} input={tc.input} />
            ))}
          </div>
        )}

        {/* Message bubble */}
        {text && (
          <div
            className={
              isUser
                ? 'bg-blue-500 text-white px-4 py-2.5 rounded-2xl rounded-br-sm text-sm leading-relaxed'
                : 'bg-white border border-gray-200 text-gray-800 px-4 py-2.5 rounded-2xl rounded-bl-sm text-sm leading-relaxed shadow-sm'
            }
          >
            {text}
          </div>
        )}
      </div>

      {/* Avatar — right side for user */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-base select-none">
          👤
        </div>
      )}
    </div>
  )
}
