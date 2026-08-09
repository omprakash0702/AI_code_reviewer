import React from 'react'
import { motion } from 'framer-motion'
import { Files, CheckCircle2, XCircle } from 'lucide-react'

// Fixed-order categorical palette, assigned by rank (most common extension
// first) — never cycled per-render, so the same extension keeps its color
// across re-renders. Anything past the top N folds into a single "Other" bar.
const PALETTE = ['#60a5fa', '#a78bfa', '#34d399', '#fbbf24', '#f472b6', '#38bdf8', '#fb923c']
const OTHER_COLOR = '#6b7280'
const TOP_N = 7

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

export default function FileInventory({ inventory, delay = 0 }) {
  if (!inventory || !inventory.total_files) return null

  const entries = Object.entries(inventory.by_extension ?? {})
  const top = entries.slice(0, TOP_N)
  const restCount = entries.slice(TOP_N).reduce((sum, [, count]) => sum + count, 0)
  const bars = [
    ...top.map(([ext, count], i) => ({ label: ext, count, color: PALETTE[i % PALETTE.length] })),
    ...(restCount > 0 ? [{ label: 'Other', count: restCount, color: OTHER_COLOR }] : []),
  ]
  const maxCount = Math.max(...bars.map(b => b.count), 1)

  const skipped =
    (inventory.skipped_unsupported_type ?? 0) +
    (inventory.skipped_oversized ?? 0) +
    (inventory.skipped_unreadable ?? 0)

  const skipReasons = [
    inventory.skipped_unsupported_type > 0 && `${inventory.skipped_unsupported_type} unsupported file type`,
    inventory.skipped_oversized > 0 && `${inventory.skipped_oversized} too large`,
    inventory.skipped_unreadable > 0 && `${inventory.skipped_unreadable} unreadable`,
  ].filter(Boolean).join(', ')

  return (
    <Card delay={delay}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-white">Repository File Inventory</h3>
        <span className="text-xs" style={{ color: '#6b7280' }}>{inventory.total_files} files total</span>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="rounded-xl p-3 text-center" style={{ backgroundColor: '#111827' }}>
          <Files size={14} className="mx-auto mb-1" style={{ color: '#60a5fa' }} />
          <p className="text-lg font-bold text-white">{inventory.total_files}</p>
          <p className="text-xs" style={{ color: '#6b7280' }}>Total Files</p>
        </div>
        <div className="rounded-xl p-3 text-center" style={{ backgroundColor: '#111827' }}>
          <CheckCircle2 size={14} className="mx-auto mb-1" style={{ color: '#4ade80' }} />
          <p className="text-lg font-bold" style={{ color: '#4ade80' }}>{inventory.supported}</p>
          <p className="text-xs" style={{ color: '#6b7280' }}>AI-Reviewed</p>
        </div>
        <div className="rounded-xl p-3 text-center" style={{ backgroundColor: '#111827' }}>
          <XCircle size={14} className="mx-auto mb-1" style={{ color: '#9ca3af' }} />
          <p className="text-lg font-bold" style={{ color: '#9ca3af' }}>{skipped}</p>
          <p className="text-xs" style={{ color: '#6b7280' }}>Skipped</p>
        </div>
      </div>

      {/* By-extension bars — each bar is its own direct label, so no separate legend needed */}
      <p className="text-xs uppercase tracking-wider mb-3" style={{ color: '#6b7280' }}>By File Type</p>
      <div className="space-y-2.5">
        {bars.map(({ label, count, color }) => (
          <div key={label} className="flex items-center gap-3">
            <span
              className="text-xs font-mono w-16 shrink-0 truncate"
              style={{ color: '#9ca3af' }}
              title={label}
            >
              {label}
            </span>
            <div className="flex-1 rounded-full h-2" style={{ backgroundColor: '#374151' }}>
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: color }}
                initial={{ width: 0 }}
                animate={{ width: `${(count / maxCount) * 100}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
            <span className="text-xs font-semibold w-8 text-right shrink-0" style={{ color }}>{count}</span>
          </div>
        ))}
      </div>

      {skipReasons && (
        <p className="text-xs mt-4 pt-4" style={{ color: '#6b7280', borderTop: '1px solid #374151' }}>
          Skipped: {skipReasons}
        </p>
      )}
    </Card>
  )
}
