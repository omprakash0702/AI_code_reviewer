import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Code2, ChevronDown, Wrench, Shield, Zap, Bug, MessageSquare, FileText } from 'lucide-react'
import { parseDiff, getSeverityStyle } from '../lib/utils'

const LINE_STYLES = {
  removed:     { bg: 'rgba(239,68,68,0.1)',    border: 'rgba(239,68,68,0.35)',  text: '#fca5a5', gutter: '-' },
  added:       { bg: 'rgba(34,197,94,0.1)',     border: 'rgba(34,197,94,0.35)', text: '#86efac', gutter: '+' },
  context:     { bg: 'transparent',             border: 'transparent',           text: '#94a3b8', gutter: '' },
  header:      { bg: 'rgba(59,130,246,0.08)',   border: 'transparent',           text: '#93c5fd', gutter: '' },
  placeholder: { bg: 'rgba(0,0,0,0.25)',        border: 'transparent',           text: 'transparent', gutter: '' },
}

const CATEGORY_ICON = {
  security:    Shield,
  performance: Zap,
  bugs:        Bug,
  code_quality: Code2,
}

const PATCH_CATEGORY_META = {
  code:          { label: 'Code',          color: '#60a5fa', bg: 'rgba(96,165,250,0.12)',  border: 'rgba(96,165,250,0.3)', icon: Code2,        sectionLabel: 'Code Fixes',          sectionNote: '— behavior/logic changes, ready to apply' },
  comment:       { label: 'Comment',       color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.3)', icon: MessageSquare, sectionLabel: 'Comment Fixes',        sectionNote: '— comment/docstring only' },
  documentation: { label: 'Documentation', color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)',  border: 'rgba(45,212,191,0.3)', icon: FileText,      sectionLabel: 'Documentation Fixes', sectionNote: '— README/markdown changes' },
}
const PATCH_CATEGORY_ORDER = ['code', 'documentation', 'comment']

function DiffLine({ type, lineNum, content }) {
  const s = LINE_STYLES[type] ?? LINE_STYLES.context
  return (
    <div
      className="flex items-stretch text-xs leading-5 font-mono"
      style={{ backgroundColor: s.bg, borderLeft: `2px solid ${s.border}` }}
    >
      <span className="w-10 shrink-0 text-right pr-2 select-none" style={{ color: '#4b5563', paddingTop: 2, paddingBottom: 2 }}>
        {lineNum ?? ''}
      </span>
      <span className="w-5 shrink-0 text-center select-none" style={{ color: s.text, paddingTop: 2 }}>
        {s.gutter}
      </span>
      <span className="flex-1 px-2 py-0.5 break-all whitespace-pre-wrap" style={{ color: s.text }}>
        {content}
      </span>
    </div>
  )
}

function FilePatch({ filename, patch, category, index }) {
  const [open, setOpen] = useState(index === 0)
  const parsed   = parseDiff(patch)
  const removals  = parsed?.left.filter(l => l.type === 'removed').length  ?? 0
  const additions = parsed?.right.filter(l => l.type === 'added').length   ?? 0
  const catMeta   = PATCH_CATEGORY_META[category]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="rounded-xl overflow-hidden"
      style={{ border: '1px solid #374151' }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 transition-colors"
        style={{ backgroundColor: '#1f2937' }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#263141')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#1f2937')}
      >
        <div className="flex items-center gap-3 min-w-0">
          <Code2 size={14} style={{ color: '#60a5fa', flexShrink: 0 }} />
          <span className="font-mono text-sm text-white truncate">{filename}</span>
          {catMeta && (
            <span className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
              style={{ color: catMeta.color, backgroundColor: catMeta.bg, border: `1px solid ${catMeta.border}` }}>
              {catMeta.label}
            </span>
          )}
          {parsed && (
            <div className="flex gap-2 shrink-0">
              {removals   > 0 && <span className="text-xs font-medium" style={{ color: '#f87171' }}>−{removals}</span>}
              {additions  > 0 && <span className="text-xs font-medium" style={{ color: '#4ade80' }}>+{additions}</span>}
            </div>
          )}
        </div>
        <ChevronDown
          size={14}
          style={{ color: '#6b7280', transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
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
            {parsed ? (
              <div className="grid grid-cols-2" style={{ borderTop: '1px solid #374151' }}>
                <div style={{ borderRight: '1px solid #374151' }}>
                  <div className="px-3 py-1.5 text-xs uppercase tracking-wider"
                    style={{ backgroundColor: '#111827', borderBottom: '1px solid #374151', color: '#6b7280' }}>
                    Current Code
                  </div>
                  <div className="overflow-x-auto" style={{ backgroundColor: '#0d1117', maxHeight: '400px', overflowY: 'auto' }}>
                    {parsed.left.map((line, i) => <DiffLine key={i} {...line} />)}
                  </div>
                </div>
                <div>
                  <div className="px-3 py-1.5 text-xs uppercase tracking-wider"
                    style={{ backgroundColor: '#111827', borderBottom: '1px solid #374151', color: '#6b7280' }}>
                    Suggested Code
                  </div>
                  <div className="overflow-x-auto" style={{ backgroundColor: '#0d1117', maxHeight: '400px', overflowY: 'auto' }}>
                    {parsed.right.map((line, i) => <DiffLine key={i} {...line} />)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="px-4 py-6 text-sm text-center" style={{ backgroundColor: '#111827', color: '#6b7280' }}>
                No diff available for this file.
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function FixCard({ filename, issues, index }) {
  const [open, setOpen] = useState(index === 0)
  const fixable = issues.filter(i => i.suggested_fix?.trim())
  if (!fixable.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="rounded-xl overflow-hidden"
      style={{ border: '1px solid #374151' }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 transition-colors"
        style={{ backgroundColor: '#1f2937' }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#263141')}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#1f2937')}
      >
        <div className="flex items-center gap-3 min-w-0">
          <Wrench size={14} style={{ color: '#a78bfa', flexShrink: 0 }} />
          <span className="font-mono text-sm text-white truncate">{filename}</span>
          <span className="text-xs shrink-0 px-2 py-0.5 rounded-full"
            style={{ backgroundColor: 'rgba(167,139,250,0.12)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.25)' }}>
            {fixable.length} fix{fixable.length > 1 ? 'es' : ''}
          </span>
        </div>
        <ChevronDown
          size={14}
          style={{ color: '#6b7280', transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ borderTop: '1px solid #374151', backgroundColor: '#111827' }}
          >
            <div className="p-4 space-y-4">
              {fixable.map((issue, i) => {
                const sev = getSeverityStyle(issue.severity)
                const CatIcon = CATEGORY_ICON[issue.category] ?? Code2
                return (
                  <div key={i} className="rounded-xl overflow-hidden" style={{ border: `1px solid ${sev.border}` }}>
                    {/* Issue header */}
                    <div className="px-4 py-2.5 flex items-center gap-2.5"
                      style={{ backgroundColor: sev.bg }}>
                      <CatIcon size={13} style={{ color: sev.color, flexShrink: 0 }} />
                      <span className="text-sm font-medium" style={{ color: sev.color }}>{issue.title}</span>
                      {issue.line != null && (
                        <span className="text-xs font-mono" style={{ color: sev.color, opacity: 0.7 }}>
                          :{issue.line}
                        </span>
                      )}
                      <span className="ml-auto text-xs font-semibold uppercase px-2 py-0.5 rounded"
                        style={{ backgroundColor: 'rgba(0,0,0,0.25)', color: sev.color }}>
                        {issue.severity}
                      </span>
                    </div>

                    {/* Why it matters */}
                    {issue.description && (
                      <div className="px-4 py-2 text-xs leading-relaxed" style={{ color: '#9ca3af', backgroundColor: 'rgba(0,0,0,0.15)' }}>
                        {issue.description}
                      </div>
                    )}

                    {/* Side-by-side: current code vs fixed code */}
                    <div className="grid grid-cols-1 sm:grid-cols-2" style={{ borderTop: `1px solid ${sev.border}` }}>
                      <div style={{ borderRight: '1px solid #374151' }}>
                        <div className="px-3 py-1.5 text-xs uppercase tracking-wider flex items-center gap-1.5"
                          style={{ backgroundColor: 'rgba(239,68,68,0.05)', borderBottom: '1px solid #374151', color: '#9ca3af' }}>
                          <span style={{ color: '#f87171' }}>✕</span> Current Code
                        </div>
                        {issue.code_snippet?.trim() ? (
                          <pre className="p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap break-all overflow-x-auto"
                            style={{ color: '#fca5a5', backgroundColor: 'rgba(239,68,68,0.04)', minHeight: '60px' }}>
                            {issue.code_snippet}
                          </pre>
                        ) : (
                          <div className="p-3 text-sm leading-relaxed" style={{ color: '#fca5a5', minHeight: '60px' }}>
                            {issue.description}
                          </div>
                        )}
                      </div>
                      <div>
                        <div className="px-3 py-1.5 text-xs uppercase tracking-wider flex items-center gap-1.5"
                          style={{ backgroundColor: 'rgba(34,197,94,0.05)', borderBottom: '1px solid #374151', color: '#9ca3af' }}>
                          <span style={{ color: '#4ade80' }}>✓</span> Fixed Code
                        </div>
                        <pre className="p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap break-all overflow-x-auto"
                          style={{ color: '#86efac', backgroundColor: 'rgba(34,197,94,0.04)', minHeight: '60px' }}>
                          {issue.suggested_fix}
                        </pre>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function PatchViewer({ fileResults }) {
  const withPatches     = fileResults.filter(f => f.patch?.trim())
  const withSuggestions = fileResults.filter(
    f => !f.patch?.trim() && f.issues?.some(i => i.suggested_fix?.trim())
  )

  const hasAnything = withPatches.length > 0 || withSuggestions.length > 0

  if (!hasAnything) {
    return (
      <div className="py-24 text-center">
        <div className="text-5xl mb-4">📄</div>
        <p className="text-xl font-semibold text-white">No fixes generated</p>
        <p className="text-sm mt-2" style={{ color: '#6b7280' }}>
          The AI didn't generate patches or fix suggestions for this repository.
        </p>
      </div>
    )
  }

  const byCategory = {}
  for (const f of withPatches) {
    const cat = f.patch_category ?? 'code'
    ;(byCategory[cat] ??= []).push(f)
  }
  const activeCategories = PATCH_CATEGORY_ORDER.filter(cat => byCategory[cat]?.length)

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-bold text-white">Patch Viewer</h2>
        <p className="text-sm mt-1" style={{ color: '#9ca3af' }}>
          AI-generated code fixes — unified diffs and suggested improvements
        </p>
      </div>

      {/* Category comparison strip */}
      {activeCategories.length > 0 && (
        <div className="flex flex-wrap gap-3 mb-8">
          {activeCategories.map(cat => {
            const meta = PATCH_CATEGORY_META[cat]
            const Icon = meta.icon
            return (
              <div
                key={cat}
                className="flex items-center gap-2 px-3 py-2 rounded-xl"
                style={{ backgroundColor: meta.bg, border: `1px solid ${meta.border}` }}
              >
                <Icon size={14} style={{ color: meta.color }} />
                <span className="text-sm font-semibold" style={{ color: meta.color }}>
                  {byCategory[cat].length}
                </span>
                <span className="text-xs" style={{ color: '#9ca3af' }}>{meta.label}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* Unified diff patches, grouped by category */}
      {activeCategories.map(cat => {
        const meta = PATCH_CATEGORY_META[cat]
        const Icon = meta.icon
        return (
          <div key={cat} className="mb-8">
            <div className="flex items-center gap-2 mb-3">
              <Icon size={14} style={{ color: meta.color }} />
              <h3 className="text-sm font-semibold" style={{ color: meta.color }}>
                {meta.sectionLabel} ({byCategory[cat].length})
              </h3>
              <span className="text-xs" style={{ color: '#6b7280' }}>{meta.sectionNote}</span>
            </div>
            <div className="space-y-4">
              {byCategory[cat].map((f, i) => (
                <FilePatch key={f.filename} filename={f.filename} patch={f.patch} category={f.patch_category} index={i} />
              ))}
            </div>
          </div>
        )
      })}

      {/* Textual fix suggestions */}
      {withSuggestions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Wrench size={14} style={{ color: '#a78bfa' }} />
            <h3 className="text-sm font-semibold" style={{ color: '#a78bfa' }}>
              Fix Suggestions ({withSuggestions.length} files)
            </h3>
            <span className="text-xs" style={{ color: '#6b7280' }}>— problem + actionable fix</span>
          </div>
          <div className="space-y-4">
            {withSuggestions.map((f, i) => (
              <FixCard key={f.filename} filename={f.filename} issues={f.issues ?? []} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
