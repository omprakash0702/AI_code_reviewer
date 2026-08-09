import axios from 'axios'

// In dev: Vite proxy forwards / → localhost:8000
// In production: VITE_API_URL is injected by deploy.yml from the API_URL secret
const BASE = import.meta.env.VITE_API_URL ?? ''

const client = axios.create({
  baseURL: BASE,
  timeout: 30000,
})

// Starts a background analysis job — returns almost instantly with just an
// analysis_id. Cloning + review all happen server-side afterward; poll
// getAnalysisStatus() for progress and file_inventory (arrives once cloning
// finishes) until status is "complete".
export async function startAnalysis(repoUrl, branch = null) {
  const { data } = await client.post('/analyze-repo', {
    repo_url: repoUrl,
    branch: branch || undefined,
  })
  return data // { analysis_id }
}

export async function getAnalysisStatus(analysisId) {
  const { data } = await client.get(`/analysis/${analysisId}/status`, {
    // This URL gets polled repeatedly with an unchanged path — some browsers/
    // proxies will heuristically cache a GET like that and keep serving the
    // first (stale) response forever instead of hitting the server again.
    // Belt-and-suspenders: explicit no-cache headers + a cache-busting param.
    headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
    params: { _: Date.now() },
  })
  return data // { analysis_id, status, file_inventory, total_files_found, progress, error }
}

export async function getAnalysisResult(analysisId) {
  const { data } = await client.get(`/analysis/${analysisId}`)
  return data
}

export async function sendChatMessage(analysisId, message) {
  // Two AI calls under the hood (pick relevant files, then answer) — give it
  // more room than the default 30s.
  const { data } = await client.post(
    `/analysis/${analysisId}/chat`,
    { message },
    { timeout: 60000 }
  )
  return data.answer
}
