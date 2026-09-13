import type {
  AuthUser,
  Company,
  CompanyCreatePayload,
  CompanyOption,
  CompanyUpdatePayload,
  DashboardStats,
  DocumentListItem,
  DocumentPageItem,
  LoginResponse,
  RagAnswer,
  DocumentStatus,
  HealthResponse,
  UploadedDocument,
} from '../types/api'
import { clearSession, getStoredToken } from '../auth/session'

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ||
  '/api'

let onUnauthorized: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const data = (await res.clone().json()) as { detail?: unknown }
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      const first = data.detail[0] as { msg?: string } | undefined
      if (first?.msg) return first.msg
    }
  } catch {
    /* not JSON */
  }
  return `Request failed with status ${res.status}`
}

async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  const token = getStoredToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  const isAuthPath = path.startsWith('/v1/auth/')
  if (res.status === 401 && !isAuthPath) {
    clearSession()
    onUnauthorized?.()
  }
  return res
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`)
  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`)
  }
  return res.json() as Promise<HealthResponse>
}

export async function register(email: string, password: string): Promise<AuthUser> {
  const res = await apiFetch('/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<AuthUser>
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await apiFetch('/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<LoginResponse>
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await apiFetch('/v1/stats/dashboard')
  if (!res.ok) {
    throw new Error(`Dashboard stats failed with status ${res.status}`)
  }
  return res.json() as Promise<DashboardStats>
}

export async function listCompanies(query?: string): Promise<Company[]> {
  const params = new URLSearchParams({ limit: '100' })
  if (query?.trim()) params.set('q', query.trim())
  const res = await apiFetch(`/v1/companies?${params}`)
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  const body = (await res.json()) as { items: Company[] }
  return body.items ?? []
}

/** Lightweight shape used by upload dropdowns. */
export async function listCompanyOptions(): Promise<CompanyOption[]> {
  const items = await listCompanies()
  return items.map(({ id, ticker, display_name, legal_name }) => ({
    id,
    ticker,
    display_name,
    legal_name,
  }))
}

export async function createCompany(
  payload: CompanyCreatePayload,
): Promise<Company> {
  const res = await apiFetch('/v1/companies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<Company>
}

export async function updateCompany(
  companyId: number,
  payload: CompanyUpdatePayload,
): Promise<Company> {
  const res = await apiFetch(`/v1/companies/${companyId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<Company>
}

export async function listDocuments(): Promise<DocumentListItem[]> {
  const res = await apiFetch('/v1/documents')
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<DocumentListItem[]>
}

export async function processDocument(documentId: number): Promise<void> {
  const res = await apiFetch(`/v1/documents/${documentId}/process`, {
    method: 'POST',
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
}

export async function getDocumentStatus(
  documentId: number,
): Promise<DocumentStatus> {
  const res = await apiFetch(`/v1/documents/${documentId}/status`)
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<DocumentStatus>
}

export async function getDocumentPages(
  documentId: number,
): Promise<DocumentPageItem[]> {
  const res = await apiFetch(`/v1/documents/${documentId}/pages`)
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<DocumentPageItem[]>
}

export async function askQuestion(question: string): Promise<RagAnswer> {
  const res = await apiFetch('/v1/rag/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<RagAnswer>
}

export async function uploadDocument(
  file: File,
  options: { companyId: number | null; documentType?: string },
): Promise<UploadedDocument> {
  const form = new FormData()
  form.append('file', file)
  if (options.companyId !== null) {
    form.append('company_id', String(options.companyId))
  }
  form.append('document_type', options.documentType ?? 'Other')
  const res = await apiFetch('/v1/documents/upload', {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<UploadedDocument>
}
