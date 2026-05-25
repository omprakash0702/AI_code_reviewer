import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Shield } from 'lucide-react'

// Real pipeline steps — shown sequentially based on elapsed time.
// These reflect what the backend actually does; timing is approximate.
const STEPS = [
  { label: 'Cloning repository via git…',           minMs: 0     },
  { label: 'Scanning and filtering source files…',  minMs: 5000  },
  { label: 'Running static analysis (lint/bandit)…',minMs: 9000  },
  { label: 'AI reviewing files — this takes a while…', minMs: 14000 },
  { label: 'Generating repository intelligence…',   minMs: 35000 },
  { label: 'Calculating health score…',             minMs: 45000 },
  { label: 'Building final report…',                minMs: 50000 },
]

export default function LoadingState() {
  const [elapsed, setElapsed] = useState(0)   // ms since mount
  const [stepIdx, setStepIdx] = useState(0)

  useEffect(() => {
    const t0 = Date.now()
    const id = setInterval(() => {
      const ms = Date.now() - t0
      setElapsed(ms)
      // advance to the last step whose minMs has been reached
      for (let i = STEPS.length - 1; i >= 0; i--) {
        if (ms >= STEPS[i].minMs) { setStepIdx(i); break }
      }
    }, 500)
    return () => clearInterval(id)
  }, [])

  // A gentle progress bar that grows logarithmically — honest about uncertainty
  const progress = Math.min(92, Math.log1p(elapsed / 1000) * 18)

  const elapsedSec = Math.floor(elapsed / 1000)

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
        </p>

        {/* Current step */}
        <motion.p
          key={stepIdx}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm mb-6"
          style={{ color: '#9ca3af' }}
        >
          {STEPS[stepIdx].label}
        </motion.p>

        {/* Progress bar — logarithmic, never reaches 100 until done */}
        <div
          className="rounded-full h-1.5 mb-3 overflow-hidden"
          style={{ backgroundColor: '#1f2937' }}
        >
          <motion.div
            className="h-full rounded-full"
            style={{
              width: `${progress}%`,
              background: 'linear-gradient(90deg,#3b82f6,#6366f1,#8b5cf6)',
            }}
            transition={{ duration: 0.5, ease: 'linear' }}
          />
        </div>

        {/* Step pipeline */}
        <div className="mt-8 text-left space-y-2">
          {STEPS.map((step, i) => {
            const done    = i < stepIdx
            const active  = i === stepIdx
            const pending = i > stepIdx
            return (
              <div
                key={i}
                className="flex items-center gap-3 text-xs"
                style={{ opacity: pending ? 0.35 : 1 }}
              >
                <div
                  className="w-4 h-4 rounded-full shrink-0 flex items-center justify-center text-xs font-bold"
                  style={{
                    backgroundColor: done
                      ? '#3b82f6'
                      : active
                      ? '#6366f1'
                      : '#374151',
                    color: '#fff',
                  }}
                >
                  {done ? '✓' : i + 1}
                </div>
                <span
                  style={{
                    color: done ? '#9ca3af' : active ? '#e2e8f0' : '#6b7280',
                  }}
                >
                  {step.label}
                </span>
                {active && (
                  <motion.span
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                    style={{ color: '#6366f1' }}
                  >
                    ●
                  </motion.span>
                )}
              </div>
            )
          })}
        </div>

        <p className="text-xs mt-8" style={{ color: '#4b5563' }}>
          Backend logs → <code style={{ color: '#6b7280' }}>logs/pr_guardian.log</code>
        </p>
      </div>
    </div>
  )
}
