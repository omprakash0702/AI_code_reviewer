import React, { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import Hero from './components/Hero'
import LoadingState from './components/LoadingState'
import Dashboard from './components/Dashboard'
import { analyzeRepo } from './lib/api'

export default function App() {
  const [phase, setPhase] = useState('hero')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  async function handleAnalyze(url) {
    setError(null)
    setPhase('loading')
    try {
      const result = await analyzeRepo(url)
      setData(result)
      setPhase('dashboard')
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Analysis failed. Check the URL and try again.'
      setError(msg)
      setPhase('hero')
    }
  }

  function handleReset() {
    setPhase('hero')
    setData(null)
    setError(null)
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
            <LoadingState />
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
