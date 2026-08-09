import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Shield } from 'lucide-react'

function formatDuration(seconds) {
  if (seconds == null) return null
  if (seconds < 60) return `~${Math.max(1, Math.round(seconds))}s`
  const mins = Math.round(seconds / 60)
  return `~${mins} min`
}

export default function LoadingState({ analysisStatus, progress, fileInventory, etaSeconds }) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const t0 = Date.now()
    const id = setInterval(() => setElapsed(Date.now() - t0), 500)
    return () => clearInterval(id)
  }, [])

  const elapsedSec = Math.floor(elapsed / 1000)
  const hasProgress = progress && progress.total > 0
  const pct = hasProgress ? Math.min(100, Math.round((progress.done / progress.total) * 100)) : 0
  const etaLabel = formatDuration(etaSeconds)

  const stepLabel =
    analysisStatus === 'cloning' || !fileInventory
      ? 'Cloning repository and scanning files… (can take a while on a slow connection)'
      : !hasProgress || progress.done === 0
      ? 'Starting AI review…'
      : progress.done >= progress.total
      ? 'Finishing up — building final report…'
      : `Reviewing ${progress.current_file ?? '…'}`

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center w-full max-w-sm mx-auto">

        {/* Spinning shield */}
        <div className="relative w-24 h-24 mx-auto mb-8">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 rounded-full"
            style={{
              border: '3px solid transparent',
              borderTopColor: '#3b82f6',
              borderRightColor: '#6366f1',
            }}
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-3 rounded-full"
            style={{ border: '2px solid transparent', borderBottomColor: '#8b5cf6' }}
          />
          <div
            className="absolute inset-4 rounded-full flex items-center justify-center"
            style={{ backgroundColor: '#1f2937' }}
          >
            <Shield size={22} style={{ color: '#60a5fa' }} />
          </div>
        </div>

        <h2 className="text-2xl font-bold text-white mb-1">Analyzing Repository</h2>
        <p className="text-xs mb-6" style={{ color: '#6b7280' }}>
          elapsed: {elapsedSec}s
          {etaLabel && <> · estimated time remaining: <span style={{ color: '#93c5fd' }}>{etaLabel}</span></>}
        </p>

        {/* Current step — driven by real backend progress, not a guess */}
        <motion.p
          key={stepLabel}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm mb-6 font-mono truncate"
          style={{ color: '#9ca3af' }}
        >
          {stepLabel}
        </motion.p>

        {/* Progress bar — real done/total once the job starts, indeterminate before that */}
        <div
          className="rounded-full h-1.5 mb-3 overflow-hidden"
          style={{ backgroundColor: '#1f2937' }}
        >
          {hasProgress ? (
            <motion.div
              className="h-full rounded-full"
              style={{
                background: 'linear-gradient(90deg,#3b82f6,#6366f1,#8b5cf6)',
              }}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          ) : (
            <motion.div
              className="h-full rounded-full"
              style={{ width: '30%', background: 'linear-gradient(90deg,#3b82f6,#6366f1,#8b5cf6)' }}
              animate={{ x: ['-100%', '250%'] }}
              transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
            />
          )}
        </div>

        {hasProgress && (
          <p className="text-xs mb-6" style={{ color: '#6b7280' }}>
            {progress.done} / {progress.total} files reviewed ({pct}%)
          </p>
        )}

        {/* File inventory summary — shown as soon as scanning completes */}
        {fileInventory && (
          <div
            className="mt-6 rounded-xl p-4 text-left text-xs space-y-1"
            style={{ backgroundColor: '#111827', border: '1px solid #1f2937', color: '#9ca3af' }}
          >
            <p>
              <span className="text-white font-semibold">{fileInventory.total_files}</span> files found in repo
            </p>
            <p>
              <span className="text-white font-semibold">{fileInventory.supported}</span> eligible for AI review
              {fileInventory.total_files > fileInventory.supported && (
                <> · {fileInventory.total_files - fileInventory.supported} skipped (other file types)</>
              )}
            </p>
          </div>
        )}

        <p className="text-xs mt-8" style={{ color: '#4b5563' }}>
          Backend logs → <code style={{ color: '#6b7280' }}>logs/pr_guardian.log</code>
        </p>
      </div>
    </div>
  )
}
