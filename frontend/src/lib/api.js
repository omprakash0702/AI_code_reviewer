import axios from 'axios'

// In dev: Vite proxy forwards / → localhost:8000
// In production: VITE_API_URL is injected by deploy.yml from the API_URL secret
const BASE = import.meta.env.VITE_API_URL ?? ''

const client = axios.create({
  baseURL: BASE,
  timeout: 360000, // 6 minutes — repo analysis is slow
})

export async function analyzeRepo(repoUrl, branch = null) {
  const { data } = await client.post('/analyze-repo', {
    repo_url: repoUrl,
    branch: branch || undefined,
  })
  return data
}
