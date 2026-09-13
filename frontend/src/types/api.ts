export interface HealthResponse {
  status: string
}

export interface AuthUser {
  id: number
  email: string
  is_active: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export interface DashboardStats {
  documents: number
  companies: number
  financial_metrics: number
}

export interface CompanyOption {
  id: number
  ticker: string | null
  display_name: string | null
  legal_name: string
}

export interface Company {
  id: number
  legal_name: string
  display_name: string | null
  ticker: string | null
  exchange: string | null
  country: string | null
  industry: string | null
  sector: string | null
  created_at: string
  updated_at: string
}

export interface CompanyCreatePayload {
  legal_name: string
  display_name?: string | null
  ticker?: string | null
  exchange?: string | null
  country?: string | null
  industry?: string | null
  sector?: string | null
}

export interface CompanyUpdatePayload {
  display_name?: string | null
  country?: string | null
  industry?: string | null
  sector?: string | null
}

export interface UploadedDocument {
  id: number
  company_id: number | null
  document_type: string
  title: string
  processing_status: string
}

export interface DocumentListItem {
  id: number
  company_id: number | null
  company_name: string | null
  title: string
  document_type: string
  filing_date: string | null
  processing_status: string
  created_at: string
}

export interface DocumentStatus {
  document_id: number
  status: string
  page_count: number | null
  error: string | null
}

export interface DocumentPageItem {
  page_number: number
  cleaned_text: string | null
  extraction_method: string
}

export interface RagSource {
  document_id: number | null
  page_start: number | null
  page_end: number | null
  score: number
}

export interface RagAnswer {
  answer: string
  sources: RagSource[]
}
