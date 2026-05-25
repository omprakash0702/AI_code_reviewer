import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2 } from 'lucide-react'

export default function AnalysisTimeline({ data }) {
  const secCount  = data.issues?.security?.length     ?? 0
  const bugCount  = data.issues?.bugs?.length          ?? 0
  const perfCount = data.issues?.performance?.length   ?? 0
  const total     = Object.values(data.issues ?? {}).reduce((s, a) => s + a.length, 0)

  const steps = [
    { label: 'Repository cloned from GitHub',                              detail: data.repo_url?.replace('https://github.com/', '') },
    { label: `${data.total_files_found ?? '?'} files discovered in repo`, detail: `${data.files_analyzed} selected for analysis` },
    { label: 'Static analysis completed',                                  detail: 'lint + security scan (bandit/eslint)' },
    { label: 'AI review completed',                                        detail: `${data.files_analyzed} files reviewed by AI` },
    { label: 'Security scan finished',                                     detail: secCount > 0 ? `${secCount} issue${secCount > 1 ? 's' : ''} found` : 'No vulnerabilities detected' },
    { label: 'Bug analysis finished',                                      detail: bugCount > 0 ? `${bugCount} bug${bugCount > 1 ? 's' : ''} flagged` : 'No bugs detected' },
    { label: `Health score calculated: ${data.health_score}/100`,         detail: `${total} total issues across all categories` },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.35 }}
      className="rounded-2xl p-6"
      style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
    >
      <h3 className="text-sm font-semibold text-white mb-5">Analysis Timeline</h3>
      <div className="relative">
        {/* Vertical line */}
        <div
          className="absolute left-3 top-0 bottom-0 w-px"
          style={{ backgroundColor: '#374151' }}
        />

        <div className="space-y-4">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 + i * 0.06 }}
              className="flex items-start gap-4 pl-2"
            >
              <div className="relative z-10 shrink-0" style={{ marginTop: 1 }}>
                <CheckCircle2 size={16} style={{ color: '#22c55e' }} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-white">{step.label}</p>
                {step.detail && (
                  <p className="text-xs mt-0.5 truncate" style={{ color: '#6b7280' }}>{step.detail}</p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
