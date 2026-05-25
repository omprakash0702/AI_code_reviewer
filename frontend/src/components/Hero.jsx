import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Github, Shield, Zap, Bug, Code2, AlertCircle } from 'lucide-react'

const PILLS = [
  { icon: Shield,  label: 'Security Analysis',  color: '#ef4444' },
  { icon: Zap,     label: 'Performance Checks', color: '#f97316' },
  { icon: Bug,     label: 'Bug Detection',       color: '#eab308' },
  { icon: Code2,   label: 'AI Code Review',      color: '#3b82f6' },
]

export default function Hero({ onAnalyze, error }) {
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!url.trim() || busy) return
    setBusy(true)
    await onAnalyze(url.trim())
    setBusy(false)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full opacity-[0.07]"
          style={{ background: 'radial-gradient(circle, #3b82f6 0%, transparent 70%)' }}
        />
        <div
          className="absolute bottom-0 right-0 w-[400px] h-[400px] rounded-full opacity-[0.05]"
          style={{ background: 'radial-gradient(circle, #8b5cf6 0%, transparent 70%)' }}
        />
      </div>

      <motion.div
        className="relative z-10 w-full max-w-3xl text-center"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.15 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium mb-8"
          style={{
            background: 'rgba(59,130,246,0.1)',
            border: '1px solid rgba(59,130,246,0.3)',
            color: '#93c5fd',
          }}
        >
          <Shield size={13} />
          AI-Powered Repository Analysis
        </motion.div>

        {/* Headline */}
        <h1 className="text-5xl sm:text-7xl font-extrabold mb-5 leading-tight tracking-tight">
          <span
            style={{
              background: 'linear-gradient(135deg,#60a5fa 0%,#818cf8 45%,#c084fc 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            PR Guardian
          </span>
          <br />
          <span className="text-white">AI</span>
        </h1>

        <p className="text-slate-400 text-lg sm:text-xl mb-12 max-w-xl mx-auto leading-relaxed">
          Paste any GitHub repo URL. Get a full AI review — security vulnerabilities,
          performance issues, bug reports, and auto-fix patches in one dashboard.
        </p>

        {/* Input row */}
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-2xl mx-auto">
          <div className="relative flex-1">
            <Github
              size={17}
              className="absolute left-4 top-1/2 -translate-y-1/2"
              style={{ color: '#6b7280' }}
            />
            <input
              type="text"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://github.com/username/repository"
              disabled={busy}
              className="w-full pl-12 pr-4 py-4 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all"
              style={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
              }}
              onFocus={e => (e.target.style.borderColor = '#3b82f6')}
              onBlur={e => (e.target.style.borderColor = '#374151')}
            />
          </div>
          <motion.button
            type="submit"
            disabled={busy || !url.trim()}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="px-8 py-4 rounded-xl font-semibold text-white text-sm whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            style={{
              background: 'linear-gradient(135deg,#3b82f6,#6366f1)',
              boxShadow: busy ? 'none' : '0 0 24px rgba(99,102,241,0.4)',
            }}
          >
            {busy ? 'Analyzing…' : 'Analyze Repo'}
          </motion.button>
        </form>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-center gap-2 mt-4 text-sm"
            style={{ color: '#f87171' }}
          >
            <AlertCircle size={14} />
            {error}
          </motion.div>
        )}

        {/* Feature pills */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex flex-wrap justify-center gap-3 mt-10"
        >
          {PILLS.map(({ icon: Icon, label, color }) => (
            <div
              key={label}
              className="flex items-center gap-2 px-4 py-2 rounded-full text-sm"
              style={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#d1d5db' }}
            >
              <Icon size={13} style={{ color }} />
              {label}
            </div>
          ))}
        </motion.div>
      </motion.div>

      {/* Bottom stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="relative z-10 flex gap-10 mt-16 text-center"
      >
        {[
          { value: '4', label: 'Issue Categories' },
          { value: '10+', label: 'Static Analyzers' },
          { value: 'GPT-4o', label: 'AI Engine' },
          { value: '< 60s', label: 'Avg. Analysis' },
        ].map(({ value, label }) => (
          <div key={label}>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-slate-500 text-xs mt-0.5">{label}</div>
          </div>
        ))}
      </motion.div>
    </div>
  )
}
