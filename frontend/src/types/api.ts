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
