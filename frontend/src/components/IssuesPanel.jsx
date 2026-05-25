import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, FileCode } from 'lucide-react'
import { getSeverityStyle, getCategoryMeta } from '../lib/utils'

function IssueCard({ issue, index }) {
  const [open, setOpen] = useState(false)
  const sev = getSeverityStyle(issue.severity)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="rounded-xl overflow-hidden"
      style={{ border: `1px solid #374151` }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left p-4 flex items-start gap-3 transition-colors"
        style={{ backgroundColor: '#111827' }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#161d2b')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#111827')}
      >
        {/* Severity badge */}
        <span
          className="shrink-0 mt-0.5 text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wider border"
          style={{ color: sev.color, backgroundColor: sev.bg, borderColor: sev.border }}
        >
          {issue.severity}
        </span>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white mb-0.5">{issue.title}</p>
          <div className="flex items-center gap-2 flex-wrap">
            {issue.filename && (
              <span className="flex items-center gap-1 text-xs" style={{ color: '#6b7280' }}>
                <FileCode size={10} />
                {issue.filename}{issue.line ? `:${issue.line}` : ''}
              </span>
            )}
            {!open && (
              <span className="text-xs truncate max-w-sm" style={{ color: '#9ca3af' }}>
                {issue.description}
              </span>
            )}
          </div>
        </div>

        <ChevronDown
          size={15}
          className="shrink-0 mt-1 transition-transform"
          style={{ color: '#6b7280', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ borderTop: '1px solid #374151', overflow: 'hidden' }}
          >
            <div className="p-4 space-y-4" style={{ backgroundColor: '#0d1117' }}>
              <Section title="Why it matters" text={issue.description} />
              {issue.impact && <Section title="Impact" text={issue.impact} />}
              {issue.suggested_fix && (
                <div>
                  <p className="text-xs uppercase tracking-wider mb-2" style={{ color: '#6b7280' }}>Suggested Fix</p>
                  <pre
                    className="text-sm rounded-lg p-3 font-mono whitespace-pre-wrap break-all"
                    style={{ backgroundColor: 'rgba(34,197,94,0.07)', color: '#86efac', border: '1px solid rgba(34,197,94,0.2)' }}
                  >
                    {issue.suggested_fix}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function Section({ title, text }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider mb-1" style={{ color: '#6b7280' }}>{title}</p>
      <p className="text-sm leading-relaxed" style={{ color: '#d1d5db' }}>{text}</p>
    </div>
  )
}

export default function IssuesPanel({ issues, category }) {
  const meta = getCategoryMeta(category)

  if (!issues.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="py-24 text-center"
      >
        <div className="text-5xl mb-4">✅</div>
        <p className="text-xl font-semibold text-white">No {meta.label} issues found!</p>
        <p className="text-sm mt-2" style={{ color: '#6b7280' }}>This category looks clean.</p>
      </motion.div>
    )
  }

  // Group by severity
  const groups = { critical: [], high: [], medium: [], low: [] }
  for (const issue of issues) {
    const s = issue.severity ?? 'low'
    ;(groups[s] ?? groups.low).push(issue)
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-white">
          {meta.emoji} {meta.label} Issues
        </h2>
        <span
          className="text-xs font-semibold px-3 py-1 rounded-full"
          style={{ color: meta.color, backgroundColor: meta.bg }}
        >
          {issues.length} issue{issues.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="space-y-8">
        {['critical', 'high', 'medium', 'low'].map(sev => {
          const group = groups[sev]
          if (!group.length) return null
          const s = getSeverityStyle(sev)
          return (
            <div key={sev}>
              <h3
                className="text-xs font-bold uppercase tracking-widest mb-3"
                style={{ color: s.color }}
              >
                {sev} · {group.length}
              </h3>
              <div className="space-y-2">
                {group.map((issue, i) => (
                  <IssueCard key={i} issue={issue} index={i} />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
