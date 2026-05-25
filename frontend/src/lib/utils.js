export function getScoreBg(score) {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#eab308'
  if (score >= 40) return '#f97316'
  return '#ef4444'
}

export function getScoreLabel(score) {
  if (score >= 80) return 'Excellent'
  if (score >= 60) return 'Good'
  if (score >= 40) return 'Fair'
  return 'Needs Work'
}

export function getSeverityStyle(severity) {
  const map = {
    critical: { color: '#f87171', bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.35)' },
    high:     { color: '#fb923c', bg: 'rgba(249,115,22,0.12)', border: 'rgba(249,115,22,0.35)' },
    medium:   { color: '#facc15', bg: 'rgba(234,179,8,0.12)',  border: 'rgba(234,179,8,0.35)'  },
    low:      { color: '#4ade80', bg: 'rgba(34,197,94,0.12)',  border: 'rgba(34,197,94,0.35)'  },
  }
  return map[severity] ?? map.low
}

export function getCategoryMeta(category) {
  const map = {
    security:     { label: 'Security',     emoji: '🔴', color: '#ef4444', bg: 'rgba(239,68,68,0.1)'  },
    performance:  { label: 'Performance',  emoji: '🟠', color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
    bugs:         { label: 'Bugs',         emoji: '🟡', color: '#eab308', bg: 'rgba(234,179,8,0.1)'  },
    code_quality: { label: 'Code Quality', emoji: '🟢', color: '#22c55e', bg: 'rgba(34,197,94,0.1)'  },
  }
  return map[category] ?? map.code_quality
}

export function parseDiff(patch) {
  if (!patch?.trim()) return null
  const lines = patch.split('\n')
  const left = []
  const right = []
  let leftNum = 1
  let rightNum = 1
  let inHunk = false

  for (const line of lines) {
    if (line.startsWith('---') || line.startsWith('+++')) continue
    if (line.startsWith('@@')) {
      const m1 = line.match(/@@ -(\d+)/)
      const m2 = line.match(/\+(\d+)/)
      if (m1) leftNum = parseInt(m1[1], 10)
      if (m2) rightNum = parseInt(m2[1], 10)
      left.push({ type: 'header', content: line, lineNum: null })
      right.push({ type: 'header', content: line, lineNum: null })
      inHunk = true
      continue
    }
    if (!inHunk) continue

    if (line.startsWith('-')) {
      left.push({ type: 'removed', content: line.slice(1), lineNum: leftNum++ })
      right.push({ type: 'placeholder', content: '', lineNum: null })
    } else if (line.startsWith('+')) {
      left.push({ type: 'placeholder', content: '', lineNum: null })
      right.push({ type: 'added', content: line.slice(1), lineNum: rightNum++ })
    } else {
      const content = line.startsWith(' ') ? line.slice(1) : line
      left.push({ type: 'context', content, lineNum: leftNum++ })
      right.push({ type: 'context', content, lineNum: rightNum++ })
    }
  }

  if (!left.length) return null
  return { left, right }
}

export function totalIssueCount(issues) {
  return Object.values(issues || {}).reduce((s, arr) => s + arr.length, 0)
}
