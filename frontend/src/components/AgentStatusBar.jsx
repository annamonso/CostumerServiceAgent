import React from 'react'

/**
 * AgentStatusBar
 * Shows a pulsing "Agent is thinking..." indicator when isThinking is true.
 * Renders nothing when isThinking is false.
 *
 * Props:
 *   isThinking {boolean}
 */
export default function AgentStatusBar({ isThinking }) {
  if (!isThinking) return null

  return (
    <div className="flex items-center gap-2 px-4 py-2 text-sm text-gray-500">
      {/* Animated pulse dot */}
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500" />
      </span>
      <span className="italic">Agent is thinking...</span>
    </div>
  )
}
