import type { HealthResponse, QueryResponse } from '../types'

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || '/api'

async function parseError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg
  } catch {
    /* ignore */
  }
  if (res.status === 400) return 'No documents ingested. Run POST /ingest on the API first.'
  if (res.status >= 500) return 'API error. Check the backend terminal and API keys.'
  return `Request failed (${res.status})`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, init)
  } catch {
    throw new Error(
      'Cannot reach the API. Start it with: uvicorn api.main:app --reload --port 8000',
    )
  }
  if (!res.ok) throw new Error(await parseError(res))
  return res.json() as Promise<T>
}

export async function queryFinQuery(question: string): Promise<QueryResponse> {
  return request<QueryResponse>('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export async function ingestDocuments(): Promise<{
  status: string
  chunks_added: number
  sources: string[]
  message: string
}> {
  return request('/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
}
