import React, { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { sendChatMessage } from '../lib/api'

export default function ChatPanel({ analysisId }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Ask me anything about this repo — I can read any file in it, not just the ones flagged as issues.",
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)

  async function handleSend(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || busy) return

    setMessages(prev => [...prev, { role: 'user', content: question }])
    setInput('')
    setBusy(true)
    setError(null)

    try {
      const answer = await sendChatMessage(analysisId, question)
      setMessages(prev => [...prev, { role: 'assistant', content: answer }])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to get a response.')
    } finally {
      setBusy(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-white">Ask AI</h2>
        <p className="text-sm mt-1" style={{ color: '#9ca3af' }}>
          Chat about this repo — it can fetch and read any source file on demand
        </p>
      </div>

      <div
        className="rounded-2xl overflow-hidden flex flex-col"
        style={{ backgroundColor: '#1f2937', border: '1px solid #374151', height: '520px' }}
      >
        {/* Message list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3"
              style={{ flexDirection: m.role === 'user' ? 'row-reverse' : 'row' }}
            >
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
                style={{
                  backgroundColor: m.role === 'user' ? 'rgba(96,165,250,0.15)' : 'rgba(167,139,250,0.15)',
                }}
              >
                {m.role === 'user'
                  ? <User size={13} style={{ color: '#60a5fa' }} />
                  : <Bot size={13} style={{ color: '#a78bfa' }} />}
              </div>
              <div
                className="rounded-xl px-4 py-2.5 text-sm leading-relaxed max-w-[80%]"
                style={{
                  backgroundColor: m.role === 'user' ? 'rgba(96,165,250,0.1)' : 'rgba(0,0,0,0.2)',
                  color: '#e2e8f0',
                }}
              >
                {m.content}
              </div>
            </motion.div>
          ))}

          {busy && (
            <div className="flex items-center gap-2 text-xs" style={{ color: '#6b7280' }}>
              <Loader2 size={13} className="animate-spin" />
              Reading the repo and thinking…
            </div>
          )}
          {error && (
            <p className="text-xs" style={{ color: '#f87171' }}>{error}</p>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input row */}
        <form
          onSubmit={handleSend}
          className="flex items-center gap-2 p-3"
          style={{ borderTop: '1px solid #374151' }}
        >
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="e.g. How is authentication handled in this repo?"
            disabled={busy}
            className="flex-1 px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 outline-none"
            style={{ backgroundColor: '#111827', border: '1px solid #374151' }}
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="p-2.5 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
            style={{ backgroundColor: '#3b82f6' }}
          >
            <Send size={15} color="#fff" />
          </button>
        </form>
      </div>
    </div>
  )
}
