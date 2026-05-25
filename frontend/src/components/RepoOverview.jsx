import React from 'react'
import { motion } from 'framer-motion'
import { Cpu, Code2, Layers, Package, Lightbulb } from 'lucide-react'

export default function RepoOverview({ intel }) {
  if (!intel) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="rounded-2xl p-6"
      style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
    >
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-5">
        <Cpu size={16} style={{ color: '#60a5fa' }} />
        Repository Intelligence
      </h3>

      <div className="space-y-5">
        <Row icon={Code2} label="Type">
          <span className="text-white font-medium">{intel.repo_type}</span>
        </Row>

        <Row icon={Layers} label="Architecture">
          <span className="text-sm leading-relaxed" style={{ color: '#d1d5db' }}>
            {intel.architecture_summary}
          </span>
        </Row>

        {intel.detected_frameworks?.length > 0 && (
          <Row icon={Package} label="Frameworks">
            <div className="flex flex-wrap gap-2">
              {intel.detected_frameworks.map(fw => (
                <span
                  key={fw}
                  className="text-xs font-medium px-2.5 py-1 rounded-full"
                  style={{
                    background: 'rgba(59,130,246,0.15)',
                    border: '1px solid rgba(59,130,246,0.35)',
                    color: '#93c5fd',
                  }}
                >
                  {fw}
                </span>
              ))}
            </div>
          </Row>
        )}

        {intel.important_modules?.length > 0 && (
          <div>
            <p className="text-xs uppercase tracking-wider mb-2.5" style={{ color: '#6b7280' }}>
              Key Modules
            </p>
            <ul className="space-y-1.5">
              {intel.important_modules.map(mod => (
                <li key={mod} className="flex items-center gap-2 text-sm" style={{ color: '#d1d5db' }}>
                  <span className="w-1 h-1 rounded-full shrink-0" style={{ backgroundColor: '#3b82f6' }} />
                  {mod}
                </li>
              ))}
            </ul>
          </div>
        )}

        {intel.ai_insights?.length > 0 && (
          <div
            className="rounded-xl p-4 mt-2"
            style={{ backgroundColor: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb size={13} style={{ color: '#a78bfa' }} />
              <p className="text-xs uppercase tracking-wider font-semibold" style={{ color: '#a78bfa' }}>
                AI Insights
              </p>
            </div>
            <ul className="space-y-2.5">
              {intel.ai_insights.map((insight, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + i * 0.07 }}
                  className="flex items-start gap-2.5 text-sm leading-relaxed"
                  style={{ color: '#c4b5fd' }}
                >
                  <span
                    className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ backgroundColor: '#7c3aed' }}
                  />
                  {insight}
                </motion.li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </motion.div>
  )
}

function Row({ icon: Icon, label, children }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1.5">
        <Icon size={11} style={{ color: '#6b7280' }} />
        <span className="text-xs uppercase tracking-wider" style={{ color: '#6b7280' }}>{label}</span>
      </div>
      {children}
    </div>
  )
}
