export type SourceDocument = {
  filename: string
  relevance_score: number
  snippet: string
}

export type QueryResponse = {
  question: string
  answer: string
  sources: SourceDocument[]
  context_chunks: number
  model: string
  processing_time_ms: number
}

export type HealthResponse = {
  status: string
  pipeline_ready: boolean
  total_chunks: number
  llm_model: string
  groq_configured: boolean
  jina_configured: boolean
  chat_mode?: string
}

export type MessageRole = 'user' | 'assistant'

export type MetricCard = {
  label: string
  value: string
  trend?: string
}

export type ChartPoint = {
  label: string
  value: number
}

export type RichAnalysis = {
  title: string
  summary: string
  metrics: MetricCard[]
  chart: {
    title: string
    unit: string
    points: ChartPoint[]
  }
  analysis: string
  sourceLabels?: string[]
}

export type ChatMessage = {
  id: string
  role: MessageRole
  content: string
  sources?: SourceDocument[]
  processingTimeMs?: number
  model?: string
  rich?: RichAnalysis
}

export type ChatSession = {
  id: string
  title: string
  messages: ChatMessage[]
  updatedAt: number
  isDemo?: boolean
}
