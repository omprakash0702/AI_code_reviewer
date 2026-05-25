import React from 'react'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'

const SEV_DATA = (counts) => [
  { name: 'Critical', value: counts?.critical ?? 0, color: '#ef4444' },
  { name: 'High',     value: counts?.high     ?? 0, color: '#f97316' },
  { name: 'Medium',   value: counts?.medium   ?? 0, color: '#eab308' },
  { name: 'Low',      value: counts?.low      ?? 0, color: '#22c55e' },
]

const CAT_DATA = (issues) => [
  { name: 'Security',    value: issues?.security?.length     ?? 0, color: '#ef4444' },
  { name: 'Performance', value: issues?.performance?.length  ?? 0, color: '#f97316' },
  { name: 'Bugs',        value: issues?.bugs?.length         ?? 0, color: '#eab308' },
  { name: 'Quality',     value: issues?.code_quality?.length ?? 0, color: '#22c55e' },
].filter(d => d.value > 0)

function CustomTip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs border"
      style={{ backgroundColor: '#111827', borderColor: '#374151' }}
    >
      <span style={{ color: d.payload.color }}>{d.name}: </span>
      <span className="font-bold text-white">{d.value}</span>
    </div>
  )
}

export default function SeverityChart({ data }) {
  const sevData = SEV_DATA(data.severity_counts)
  const catData = CAT_DATA(data.issues)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="rounded-2xl p-6"
      style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
    >
      <h3 className="text-sm font-semibold text-white mb-6">Issue Distribution</h3>

      <div className="grid grid-cols-2 gap-6">
        {/* Bar – severity */}
        <div>
          <p className="text-xs uppercase tracking-wider mb-3" style={{ color: '#6b7280' }}>By Severity</p>
          <ResponsiveContainer width="100%" height={155}>
            <BarChart data={sevData} barSize={22}>
              <XAxis
                dataKey="name"
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis hide />
              <Tooltip content={<CustomTip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {sevData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Donut – categories */}
        <div>
          <p className="text-xs uppercase tracking-wider mb-3" style={{ color: '#6b7280' }}>By Category</p>
          {catData.length > 0 ? (
            <ResponsiveContainer width="100%" height={155}>
              <PieChart>
                <Pie
                  data={catData}
                  cx="50%" cy="50%"
                  innerRadius={42} outerRadius={68}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {catData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip content={<CustomTip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-sm" style={{ color: '#6b7280' }}>
              No issues found
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      {catData.length > 0 && (
        <div className="flex flex-wrap gap-4 mt-4 pt-4" style={{ borderTop: '1px solid #374151' }}>
          {catData.map(d => (
            <div key={d.name} className="flex items-center gap-1.5 text-xs" style={{ color: '#9ca3af' }}>
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
              {d.name}: <span className="font-semibold text-white">{d.value}</span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  )
}
