import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Github } from 'lucide-react'
import StatsGrid from './StatsGrid'
import RepoOverview from './RepoOverview'
import SeverityChart from './SeverityChart'
import IssuesPanel from './IssuesPanel'
import PatchViewer from './PatchViewer'
import AISummary from './AISummary'
import AnalysisTimeline from './AnalysisTimeline'

export default function Dashboard({ data, onReset }) {
  const [tab, setTab] = useState('overview')

  const tabs = [
    { id: 'overview',     label: 'Overview' },
    { id: 'security',     label: `Security (${data.issues?.security?.length ?? 0})` },
    { id: 'performance',  label: `Performance (${data.issues?.performance?.length ?? 0})` },
    { id: 'bugs',         label: `Bugs (${data.issues?.bugs?.length ?? 0})` },
    { id: 'code_quality', label: `Code Quality (${data.issues?.code_quality?.length ?? 0})` },
    { id: 'patches',      label: `Patches (${(data.file_results ?? []).filter(f => f.patch?.trim() || f.issues?.some(i => i.suggested_fix?.trim())).length})` },
    { id: 'summary',      label: 'AI Summary' },
  ]

  return (
    <div className="min-h-screen">
      {/* Sticky header */}
      <header
        className="sticky top-0 z-50"
        style={{ backgroundColor: 'rgba(10,15,30,0.95)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #1f2937' }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0">
            <button
              onClick={onReset}
              className="flex items-center gap-1.5 text-sm transition-colors shrink-0"
              style={{ color: '#9ca3af' }}
              onMouseEnter={e => (e.currentTarget.style.color = '#f9fafb')}
              onMouseLeave={e => (e.currentTarget.style.color = '#9ca3af')}
            >
              <ArrowLeft size={14} />
              New Analysis
            </button>
            <div className="w-px h-4 shrink-0" style={{ backgroundColor: '#374151' }} />
            <div className="flex items-center gap-2 min-w-0">
              <Github size={13} style={{ color: '#6b7280', flexShrink: 0 }} />
              <span
                className="text-sm truncate"
                style={{ color: '#d1d5db', maxWidth: '320px' }}
                title={data.repo_url}
              >
                {data.repo_url.replace('https://github.com/', '')}
              </span>
            </div>
          </div>
          <span className="text-xs shrink-0" style={{ color: '#6b7280' }}>
            {data.files_analyzed} files · Health&nbsp;
            <span
              className="font-semibold"
              style={{ color: data.health_score >= 80 ? '#4ade80' : data.health_score >= 60 ? '#facc15' : '#f87171' }}
            >
              {data.health_score}/100
            </span>
          </span>
        </div>

        {/* Tab bar */}
        <div
          className="max-w-7xl mx-auto px-4 sm:px-6 flex gap-0 overflow-x-auto"
          style={{ borderTop: '1px solid #1f2937' }}
        >
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className="px-4 py-2.5 text-xs font-medium whitespace-nowrap border-b-2 transition-colors"
              style={{
                borderColor: tab === t.id ? '#3b82f6' : 'transparent',
                color: tab === t.id ? '#60a5fa' : '#9ca3af',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      {/* Page content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          {tab === 'overview' && (
            <div className="space-y-6">
              <StatsGrid data={data} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <SeverityChart data={data} />
                <RepoOverview intel={data.repository_intelligence} />
              </div>
              <AnalysisTimeline data={data} />
            </div>
          )}
          {tab === 'security' && (
            <IssuesPanel issues={data.issues?.security ?? []} category="security" />
          )}
          {tab === 'performance' && (
            <IssuesPanel issues={data.issues?.performance ?? []} category="performance" />
          )}
          {tab === 'bugs' && (
            <IssuesPanel issues={data.issues?.bugs ?? []} category="bugs" />
          )}
          {tab === 'code_quality' && (
            <IssuesPanel issues={data.issues?.code_quality ?? []} category="code_quality" />
          )}
          {tab === 'patches' && (
            <PatchViewer fileResults={data.file_results ?? []} />
          )}
          {tab === 'summary' && (
            <AISummary data={data} />
          )}
        </motion.div>
      </main>
    </div>
  )
}
