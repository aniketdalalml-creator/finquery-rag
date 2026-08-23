import type {
  CompanyOption,
  DashboardStats,
  HealthResponse,
  UploadedDocument,
} from '../types/api'

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ||
  '/api'

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const data = (await res.clone().json()) as { detail?: unknown }
    if (typeof data.detail === 'string') return data.detail
  } catch {
    /* not JSON */
  }
  return `Request failed with status ${res.status}`
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`)
  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`)
  }
  return res.json() as Promise<HealthResponse>
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE_URL}/stats/dashboard`)
  if (!res.ok) {
    throw new Error(`Dashboard stats failed with status ${res.status}`)
  }
  return res.json() as Promise<DashboardStats>
}

export async function listCompanies(): Promise<CompanyOption[]> {
  const res = await fetch(`${API_BASE_URL}/v1/companies?limit=100`)
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  const body = (await res.json()) as { items: CompanyOption[] }
  return body.items ?? []
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
  const res = await fetch(`${API_BASE_URL}/v1/documents/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    throw new Error(await parseErrorDetail(res))
  }
  return res.json() as Promise<UploadedDocument>
}
