import React from 'react'

/**
 * ToolCallBadge
 * Renders an inline badge showing which tool was called and with what arguments.
 * Example: "get_order(order_id: "ORD-1003")"
 *
 * Props:
 *   name  {string} — tool name
 *   input {object} — tool input key/value pairs
 */
export default function ToolCallBadge({ name, input }) {
  const args = Object.entries(input || {})
    .map(([k, v]) => `${k}: "${v}"`)
    .join(', ')

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-xs font-mono text-slate-600">
      <span>🔧</span>
      <span>
        {name}({args})
      </span>
    </span>
  )
}
