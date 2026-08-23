export interface HealthResponse {
  status: string
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
