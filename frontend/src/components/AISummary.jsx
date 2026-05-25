import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Shield, Zap, Bug, Code2, CheckCheck } from 'lucide-react'
import { getScoreBg, getScoreLabel, totalIssueCount } from '../lib/utils'

const CATEGORY_META = [
  { key: 'security',     label: 'Security',     icon: Shield, color: '#ef4444' },
  { key: 'performance',  label: 'Performance',  icon: Zap,    color: '#f97316' },
  { key: 'bugs',         label: 'Bugs',         icon: Bug,    color: '#eab308' },
  { key: 'code_quality', label: 'Code Quality', icon: Code2,  color: '#22c55e' },
]

function computeConfidence(severity_counts, issues, health_score) {
  let conf = 97
  conf -= Math.min(45, (severity_counts?.critical ?? 0) * 15)
  conf -= Math.min(20, (severity_counts?.high     ?? 0) * 5)
  conf -= Math.min(10, (severity_counts?.medium   ?? 0) * 1)
  const secCount = issues?.security?.length ?? 0
  if (secCount > 0) conf -= Math.min(15, secCount * 5)
  if (health_score < 60) conf -= 5
  return Math.max(52, Math.min(99, Math.round(conf)))
}

function buildReasons(data, isApprove) {
  const { severity_counts, issues, health_score } = data
  const reasons = []

  const critical = severity_counts?.critical ?? 0
  const high     = severity_counts?.high     ?? 0
  const secCount = issues?.security?.length  ?? 0
  const bugCount = issues?.bugs?.length      ?? 0

  if (critical === 0) {
    reasons.push('No critical issues detected')
  } else {
    reasons.push(`${critical} critical issue${critical > 1 ? 's' : ''} require immediate attention`)
  }

  if (secCount === 0) {
    reasons.push('No security vulnerabilities found')
  } else {
    reasons.push(`${secCount} security risk${secCount > 1 ? 's' : ''} identified`)
  }

  if (health_score >= 80) {
    reasons.push(`Strong overall code health (${health_score}/100)`)
  } else if (health_score >= 60) {
    reasons.push(`Acceptable code health with room to improve (${health_score}/100)`)
  } else {
    reasons.push(`Code health needs attention (${health_score}/100)`)
  }

  if (high === 0 && bugCount === 0) {
    reasons.push('No high-severity bugs or regressions')
  } else if (bugCount > 0) {
    reasons.push(`${bugCount} bug${bugCount > 1 ? 's' : ''} flagged for review`)
  } else {
    reasons.push(`${high} high-severity issue${high > 1 ? 's' : ''} flagged`)
  }

  return reasons.slice(0, 4)
}

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

export default function AISummary({ data }) {
  const { pr_summary, health_score, repository_intelligence, severity_counts, issues } = data
  const isApprove = pr_summary?.recommendation === 'approve'
  const total      = totalIssueCount(issues)
  const confidence = computeConfidence(severity_counts, issues, health_score)
  const reasons    = buildReasons(data, isApprove)

  return (
    <div className="space-y-6 max-w-4xl mx-auto">

      {/* Recommendation banner */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl p-6 relative overflow-hidden"
        style={{
          backgroundColor: '#1f2937',
          border: `1px solid ${isApprove ? '#16a34a' : '#dc2626'}`,
        }}
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.06]"
          style={{
            background: `radial-gradient(ellipse at top left, ${isApprove ? '#22c55e' : '#ef4444'}, transparent 60%)`,
          }}
        />

        <div className="relative flex items-start gap-4">
          {isApprove
            ? <CheckCircle size={36} style={{ color: '#4ade80', flexShrink: 0 }} />
            : <XCircle    size={36} style={{ color: '#f87171', flexShrink: 0 }} />
          }
          <div className="flex-1 min-w-0">
            <p className="text-xs uppercase tracking-wider mb-1" style={{ color: '#9ca3af' }}>
              AI Recommendation
            </p>
            <div className="flex items-center gap-4 mb-2 flex-wrap">
              <p
                className="text-2xl font-bold"
                style={{ color: isApprove ? '#4ade80' : '#f87171' }}
              >
                {isApprove ? '✓ Approve' : '⚠ Request Changes'}
              </p>
              {/* Confidence badge */}
              <div
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
                style={{
                  backgroundColor: isApprove ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
                  border: `1px solid ${isApprove ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
                  color: isApprove ? '#4ade80' : '#f87171',
                }}
              >
                Confidence: {confidence}%
              </div>
            </div>

            {pr_summary?.recommendation_reason && (
              <p className="text-sm mb-4" style={{ color: '#d1d5db' }}>
                {pr_summary.recommendation_reason}
              </p>
            )}

            {/* Reason bullets */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
              {reasons.map((reason, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.07 }}
                  className="flex items-center gap-2 text-sm"
                >
                  <CheckCheck
                    size={14}
                    style={{ color: isApprove ? '#4ade80' : '#f87171', flexShrink: 0 }}
                  />
                  <span style={{ color: '#d1d5db' }}>{reason}</span>
                </motion.div>
              ))}
            </div>

            <div
              className="rounded-xl p-4"
              style={{ backgroundColor: 'rgba(0,0,0,0.2)' }}
            >
              <p className="text-xs uppercase tracking-wider mb-2" style={{ color: '#6b7280' }}>
                Main Findings
              </p>
              <p className="text-sm leading-relaxed" style={{ color: '#e2e8f0' }}>
                {pr_summary?.main_findings}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Health Score',    value: health_score,                  color: getScoreBg(health_score), sub: getScoreLabel(health_score) },
          { label: 'Files Analyzed',  value: pr_summary?.files_analyzed,    color: '#60a5fa' },
          { label: 'Critical Issues', value: pr_summary?.critical_risks,    color: (pr_summary?.critical_risks ?? 0) > 0 ? '#f87171' : '#4ade80' },
          { label: 'Total Issues',    value: total,                          color: '#f9fafb' },
        ].map(({ label, value, color, sub }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.06 }}
            className="rounded-xl p-4 text-center"
            style={{ backgroundColor: '#111827', border: '1px solid #374151' }}
          >
            <p className="text-3xl font-bold" style={{ color }}>{value ?? 0}</p>
            <p className="text-xs mt-1" style={{ color: '#6b7280' }}>{label}</p>
            {sub && <p className="text-xs mt-0.5 font-medium" style={{ color }}>{sub}</p>}
          </motion.div>
        ))}
      </div>

      {/* Category breakdown */}
      <Card delay={0.25}>
        <h3 className="text-sm font-semibold text-white mb-4">Issue Breakdown</h3>
        <div className="grid grid-cols-2 gap-3">
          {CATEGORY_META.map(({ key, label, icon: Icon, color }) => {
            const count = issues?.[key]?.length ?? 0
            return (
              <div
                key={key}
                className="flex items-center gap-3 p-3 rounded-xl"
                style={{ backgroundColor: 'rgba(0,0,0,0.2)' }}
              >
                <div
                  className="p-2 rounded-lg shrink-0"
                  style={{ backgroundColor: `${color}18` }}
                >
                  <Icon size={15} style={{ color }} />
                </div>
                <div>
                  <p className="text-base font-bold" style={{ color }}>{count}</p>
                  <p className="text-xs" style={{ color: '#9ca3af' }}>{label}</p>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Severity breakdown */}
      <Card delay={0.32}>
        <h3 className="text-sm font-semibold text-white mb-4">Severity Breakdown</h3>
        <div className="space-y-3">
          {[
            { label: 'Critical', count: severity_counts?.critical ?? 0, color: '#ef4444', max: 20 },
            { label: 'High',     count: severity_counts?.high     ?? 0, color: '#f97316', max: 20 },
            { label: 'Medium',   count: severity_counts?.medium   ?? 0, color: '#eab308', max: 20 },
            { label: 'Low',      count: severity_counts?.low      ?? 0, color: '#22c55e', max: 20 },
          ].map(({ label, count, color, max }) => (
            <div key={label} className="flex items-center gap-3">
              <span className="text-xs w-14 shrink-0" style={{ color: '#9ca3af' }}>{label}</span>
              <div className="flex-1 rounded-full h-1.5" style={{ backgroundColor: '#374151' }}>
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (count / max) * 100)}%` }}
                  transition={{ duration: 1, ease: 'easeOut', delay: 0.4 }}
                />
              </div>
              <span className="text-xs font-semibold w-5 text-right shrink-0" style={{ color }}>{count}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Repo summary */}
      {repository_intelligence && (
        <Card delay={0.4}>
          <h3 className="text-sm font-semibold text-white mb-4">Repository Summary</h3>
          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            <div>
              <p className="text-xs uppercase tracking-wider mb-1" style={{ color: '#6b7280' }}>Type</p>
              <p className="text-white">{repository_intelligence.repo_type}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider mb-1" style={{ color: '#6b7280' }}>Primary Language</p>
              <p className="text-white">{repository_intelligence.primary_language}</p>
            </div>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider mb-1" style={{ color: '#6b7280' }}>Architecture</p>
            <p className="text-sm leading-relaxed" style={{ color: '#d1d5db' }}>
              {repository_intelligence.architecture_summary}
            </p>
          </div>
        </Card>
      )}

    </div>
  )
}
