import React from 'react'
import { motion } from 'framer-motion'
import { FileCode, AlertTriangle, Shield } from 'lucide-react'
import { getScoreBg, getScoreLabel, totalIssueCount } from '../lib/utils'

function Card({ children, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="rounded-2xl p-5 sm:p-6"
      style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
    >
      {children}
    </motion.div>
  )
}

function HealthCircle({ score }) {
  const color = getScoreBg(score)
  const r = 38
  const circ = 2 * Math.PI * r
  const dashOffset = circ - (score / 100) * circ

  return (
    <Card delay={0}>
      <p className="text-xs font-medium uppercase tracking-wider mb-3" style={{ color: '#6b7280' }}>
        Health Score
      </p>
      <div className="flex items-center gap-4">
        <div className="relative shrink-0">
          <svg width="88" height="88" viewBox="0 0 88 88">
            <circle cx="44" cy="44" r={r} fill="none" stroke="#374151" strokeWidth="7" />
            <motion.circle
              cx="44" cy="44" r={r}
              fill="none"
              stroke={color}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={circ}
              initial={{ strokeDashoffset: circ }}
              animate={{ strokeDashoffset: dashOffset }}
              transition={{ duration: 1.4, ease: 'easeOut', delay: 0.3 }}
              transform="rotate(-90 44 44)"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-bold" style={{ color }}>{score}</span>
          </div>
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{score}<span className="text-base font-normal text-slate-500">/100</span></p>
          <p className="text-xs mt-0.5" style={{ color }}>{getScoreLabel(score)}</p>
        </div>
      </div>
    </Card>
  )
}

function StatCard({ icon: Icon, title, value, subtitle, accent, delay }) {
  return (
    <Card delay={delay}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider mb-2" style={{ color: '#6b7280' }}>{title}</p>
          <p className="text-4xl font-bold" style={{ color: accent ?? '#f9fafb' }}>{value}</p>
          {subtitle && <p className="text-xs mt-1.5" style={{ color: '#6b7280' }}>{subtitle}</p>}
        </div>
        <div className="p-2 rounded-lg" style={{ backgroundColor: '#374151' }}>
          <Icon size={18} style={{ color: accent ?? '#9ca3af' }} />
        </div>
      </div>
    </Card>
  )
}

export default function StatsGrid({ data }) {
  const total = totalIssueCount(data.issues)
  const critical = data.severity_counts?.critical ?? 0
  const security = data.issues?.security?.length ?? 0

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <HealthCircle score={data.health_score} />
      <StatCard
        icon={FileCode}
        title="Files Analyzed"
        value={data.files_analyzed}
        subtitle={`${data.total_files_found} found in repo`}
        accent="#60a5fa"
        delay={0.08}
      />
      <StatCard
        icon={AlertTriangle}
        title="Critical Issues"
        value={critical}
        subtitle={`${total} issues total`}
        accent={critical > 0 ? '#f87171' : '#4ade80'}
        delay={0.16}
      />
      <StatCard
        icon={Shield}
        title="Security Issues"
        value={security}
        subtitle="Potential vulnerabilities"
        accent={security > 0 ? '#fb923c' : '#4ade80'}
        delay={0.24}
      />
    </div>
  )
}
