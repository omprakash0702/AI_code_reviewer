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

// Aligns a block of removed lines against a block of added lines via LCS, so
// lines that are identical on both sides render as unchanged context instead
// of a full remove+add pair. O(n*m) — fine for the small hunks AI patches produce.
function alignChangeBlock(removed, added) {
  const n = removed.length
  const m = added.length
  const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = removed[i] === added[j]
        ? dp[i + 1][j + 1] + 1
        : Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }

  const rows = []
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (removed[i] === added[j]) {
      rows.push({ kind: 'context', text: removed[i] })
      i++; j++
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      rows.push({ kind: 'removed', text: removed[i] })
      i++
    } else {
      rows.push({ kind: 'added', text: added[j] })
      j++
    }
  }
  while (i < n) { rows.push({ kind: 'removed', text: removed[i] }); i++ }
  while (j < m) { rows.push({ kind: 'added', text: added[j] }); j++ }
  return rows
}

export function parseDiff(patch) {
  if (!patch?.trim()) return null
  const lines = patch.split('\n')
  const left = []
  const right = []
  let leftNum = 1
  let rightNum = 1
  let inHunk = false

  const flushChangeBlock = (removed, added) => {
    for (const row of alignChangeBlock(removed, added)) {
      if (row.kind === 'context') {
        left.push({ type: 'context', content: row.text, lineNum: leftNum++ })
        right.push({ type: 'context', content: row.text, lineNum: rightNum++ })
      } else if (row.kind === 'removed') {
        left.push({ type: 'removed', content: row.text, lineNum: leftNum++ })
        right.push({ type: 'placeholder', content: '', lineNum: null })
      } else {
        left.push({ type: 'placeholder', content: '', lineNum: null })
        right.push({ type: 'added', content: row.text, lineNum: rightNum++ })
      }
    }
    removed.length = 0
    added.length = 0
  }

  let pendingRemoved = []
  let pendingAdded = []

  for (const line of lines) {
    if (line.startsWith('---') || line.startsWith('+++')) continue
    if (line.startsWith('@@')) {
      flushChangeBlock(pendingRemoved, pendingAdded)
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
      pendingRemoved.push(line.slice(1))
    } else if (line.startsWith('+')) {
      pendingAdded.push(line.slice(1))
    } else {
      flushChangeBlock(pendingRemoved, pendingAdded)
      const content = line.startsWith(' ') ? line.slice(1) : line
      left.push({ type: 'context', content, lineNum: leftNum++ })
      right.push({ type: 'context', content, lineNum: rightNum++ })
    }
  }
  flushChangeBlock(pendingRemoved, pendingAdded)

  if (!left.length) return null
  return { left, right }
}

export function totalIssueCount(issues) {
  return Object.values(issues || {}).reduce((s, arr) => s + arr.length, 0)
}
