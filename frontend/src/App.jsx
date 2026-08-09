import React, { useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import Hero from './components/Hero'
import LoadingState from './components/LoadingState'
import Dashboard from './components/Dashboard'
import { startAnalysis, getAnalysisStatus, getAnalysisResult } from './lib/api'

const POLL_INTERVAL_MS = 2000
const MAX_POLL_MS = 15 * 60 * 1000 // safety net — never spin silently forever

export default function App() {
  const [phase, setPhase] = useState('hero')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [analysisStatus, setAnalysisStatus] = useState(null) // "cloning" | "running" | "complete" | "failed"
  const [progress, setProgress] = useState(null)
  const [fileInventory, setFileInventory] = useState(null)
  const [etaSeconds, setEtaSeconds] = useState(null)
  const cancelledRef = useRef(false)

  async function handleAnalyze(url) {
    cancelledRef.current = false
    setError(null)
    setAnalysisStatus('cloning')
    setProgress(null)
    setFileInventory(null)
    setEtaSeconds(null)
    setPhase('loading')
    try {
      // Returns near-instantly — cloning happens in the background job, not
      // here, so this can never trip a client-side request timeout no
      // matter how slow GitHub/network is at this moment.
      const start = await startAnalysis(url)
      if (cancelledRef.current) return

      let status
      let lastInventory = null
      const pollStart = Date.now()
      while (true) {
        if (Date.now() - pollStart > MAX_POLL_MS) {
          throw new Error(
            'This is taking far longer than expected. The analysis may still be running on the ' +
            'server — check the backend logs, or try again.'
          )
        }
        status = await getAnalysisStatus(start.analysis_id)
        if (cancelledRef.current) return
        setAnalysisStatus(status.status)
        setProgress(status.progress)
        setEtaSeconds(status.estimated_seconds_remaining)
        if (status.file_inventory) {
          lastInventory = status.file_inventory
          setFileInventory(status.file_inventory)
        }
        if (status.status === 'complete') break
        if (status.status === 'failed') {
          throw new Error(status.error || 'Analysis failed')
        }
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS))
      }

      const result = await getAnalysisResult(start.analysis_id)
      if (cancelledRef.current) return
      setData({ ...result, analysis_id: start.analysis_id, file_inventory: lastInventory })
      setPhase('dashboard')
    } catch (err) {
      if (cancelledRef.current) return
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Analysis failed. Check the URL and try again.'
      setError(msg)
      setPhase('hero')
    }
  }

  function handleReset() {
    cancelledRef.current = true
    setPhase('hero')
    setData(null)
    setError(null)
    setAnalysisStatus(null)
    setProgress(null)
    setFileInventory(null)
    setEtaSeconds(null)
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0a0f1e' }}>
      <AnimatePresence mode="wait">
        {phase === 'hero' && (
          <motion.div
            key="hero"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.35 }}
          >
            <Hero onAnalyze={handleAnalyze} error={error} />
          </motion.div>
        )}

        {phase === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <LoadingState
              analysisStatus={analysisStatus}
              progress={progress}
              fileInventory={fileInventory}
              etaSeconds={etaSeconds}
            />
          </motion.div>
        )}

        {phase === 'dashboard' && data && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          >
            <Dashboard data={data} onReset={handleReset} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
