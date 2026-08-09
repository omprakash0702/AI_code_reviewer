import React from 'react'
import { motion } from 'framer-motion'
import { AlertOctagon, Flame, ListOrdered, FileWarning } from 'lucide-react'
import { getSeverityStyle } from '../lib/utils'

function Card({ children, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="rounded-2xl p-6"
      style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
    >
      {children}
    </motion.div>
  )
}

function FileChips({ files }) {
  if (!files?.length) return null
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {files.map(f => (
        <span
          key={f}
          className="text-xs font-mono px-2 py-0.5 rounded-md"
          style={{ backgroundColor: 'rgba(0,0,0,0.25)', color: '#9ca3af' }}
        >
          {f}
        </span>
      ))}
    </div>
  )
}

export default function CriticalAnalysis({ data }) {
  const critical = data?.critical_analysis ?? {}
  const { top_risk, systemic_patterns = [], priority_recommendations = [] } = critical
  const hasAnything = top_risk || systemic_patterns.length > 0 || priority_recommendations.length > 0

  if (!hasAnything) {
    return (
      <div className="py-24 text-center">
        <div className="text-5xl mb-4">✅</div>
        <p className="text-xl font-semibold text-white">No systemic risks found</p>
        <p className="text-sm mt-2" style={{ color: '#6b7280' }}>
          No cross-file patterns or dominant risks were identified in this repository.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="mb-2">
        <h2 className="text-lg font-bold text-white">Critical Analysis</h2>
        <p className="text-sm mt-1" style={{ color: '#9ca3af' }}>
          Cross-file risk review — patterns and priorities that don't show up when reading one file at a time
        </p>
      </div>

      {/* Top risk */}
      {top_risk && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl p-6 relative overflow-hidden"
          style={{ backgroundColor: '#1f2937', border: '1px solid #dc2626' }}
        >
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.06]"
            style={{ background: 'radial-gradient(ellipse at top left, #ef4444, transparent 60%)' }}
          />
          <div className="relative flex items-start gap-4">
            <Flame size={32} style={{ color: '#f87171', flexShrink: 0 }} />
            <div className="flex-1 min-w-0">
              <p className="text-xs uppercase tracking-wider mb-1" style={{ color: '#9ca3af' }}>
                Top Risk
              </p>
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <p className="text-xl font-bold" style={{ color: '#f87171' }}>{top_risk.title}</p>
                <span
                  className="text-xs font-semibold uppercase px-2 py-0.5 rounded-full"
                  style={{ backgroundColor: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171' }}
                >
                  {top_risk.severity}
                </span>
              </div>
              <p className="text-sm leading-relaxed" style={{ color: '#d1d5db' }}>
                {top_risk.description}
              </p>
              <FileChips files={top_risk.affected_files} />
            </div>
          </div>
        </motion.div>
      )}

      {/* Systemic patterns */}
      {systemic_patterns.length > 0 && (
        <Card delay={0.1}>
          <div className="flex items-center gap-2 mb-4">
            <AlertOctagon size={16} style={{ color: '#fb923c' }} />
            <h3 className="text-sm font-semibold text-white">
              Systemic Patterns ({systemic_patterns.length})
            </h3>
          </div>
          <div className="space-y-3">
            {systemic_patterns.map((p, i) => {
              const sev = getSeverityStyle(p.severity)
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 + i * 0.05 }}
                  className="rounded-xl p-4"
                  style={{ backgroundColor: 'rgba(0,0,0,0.2)', border: `1px solid ${sev.border}` }}
                >
                  <div className="flex items-center gap-2 flex-wrap mb-1.5">
                    <FileWarning size={13} style={{ color: sev.color, flexShrink: 0 }} />
                    <p className="text-sm font-medium" style={{ color: sev.color }}>{p.pattern}</p>
                    <span
                      className="text-xs font-semibold uppercase px-2 py-0.5 rounded ml-auto"
                      style={{ backgroundColor: sev.bg, color: sev.color }}
                    >
                      {p.severity} · {p.affected_files?.length ?? 0} files
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed" style={{ color: '#d1d5db' }}>
                    {p.why_it_matters}
                  </p>
                  <FileChips files={p.affected_files} />
                </motion.div>
              )
            })}
          </div>
        </Card>
      )}

      {/* Priority recommendations */}
      {priority_recommendations.length > 0 && (
        <Card delay={0.2}>
          <div className="flex items-center gap-2 mb-4">
            <ListOrdered size={16} style={{ color: '#60a5fa' }} />
            <h3 className="text-sm font-semibold text-white">Fix This First</h3>
          </div>
          <div className="space-y-3">
            {[...priority_recommendations]
              .sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99))
              .map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.25 + i * 0.05 }}
                  className="flex items-start gap-3"
                >
                  <span
                    className="flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold shrink-0"
                    style={{ backgroundColor: 'rgba(96,165,250,0.15)', color: '#60a5fa' }}
                  >
                    {r.priority}
                  </span>
                  <div>
                    <p className="text-sm font-medium" style={{ color: '#f9fafb' }}>{r.action}</p>
                    <p className="text-xs mt-0.5" style={{ color: '#9ca3af' }}>{r.reason}</p>
                  </div>
                </motion.div>
              ))}
          </div>
        </Card>
      )}
    </div>
  )
}
