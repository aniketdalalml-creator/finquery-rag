import { useState, type FormEvent } from 'react'
import {
  ArrowUpRight,
  Building2,
  FileText,
  Sparkles,
  Target,
} from 'lucide-react'
import { DashboardSidebar } from './components/DashboardSidebar'
import { DashboardHeader } from './components/DashboardHeader'
import type { NavItemId } from './navigation'
import { useBackendHealth } from '../../hooks/useBackendHealth'
import { useDashboardStats } from '../../hooks/useDashboardStats'
import { useDocuments } from '../../hooks/useDocuments'
import { askQuestion } from '../../services/api'
import type { DocumentListItem, RagAnswer } from '../../types/api'
import DocumentsPage from '../documents/DocumentsPage'
import CompaniesPage from '../companies/CompaniesPage'
import SettingsPage from '../settings/SettingsPage'
import { StatusBadge } from '../documents/components/StatusBadge'

const RECENT_DOCUMENTS_LIMIT = 5

const SUGGESTED_QUERIES = [
  "What was Apple's total net sales in the latest fiscal year?",
  'Summarize key risk factors from the most recent 10-K.',
  'What drove year-over-year revenue growth?',
]

function formatUploadedAt(value: string): string {
  return new Date(value).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function recentDocuments(documents: DocumentListItem[]): DocumentListItem[] {
  return [...documents]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
    .slice(0, RECENT_DOCUMENTS_LIMIT)
}

function formatCount(n: number): string {
  return n.toLocaleString('en-US')
}

function AskPanel({
  question,
  setQuestion,
  asking,
  onAsk,
  askError,
  answerState,
}: {
  question: string
  setQuestion: (value: string) => void
  asking: boolean
  onAsk: (event: FormEvent<HTMLFormElement>) => void
  askError: string | null
  answerState: (RagAnswer & { question: string }) | null
}) {
  return (
    <div className="space-y-4">
      <div className="relative overflow-hidden rounded-2xl bg-surface-container-lowest p-5 shadow-[var(--shadow-card)] lg:p-6">
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-container/10 text-primary">
                <Sparkles size={16} />
              </div>
              <h2 className="text-title-md font-semibold text-on-surface">
                Ask a Financial &amp; Disclosure Question
              </h2>
              <span className="rounded-full bg-surface-container px-2 py-0.5 text-caption font-semibold text-primary">
                Cross-Corpus Synthesis
              </span>
            </div>
          </div>

          <form
            onSubmit={onAsk}
            className="relative flex flex-col items-stretch gap-2 rounded-xl bg-surface-container-low p-1.5 sm:flex-row"
          >
            <label htmlFor="dashboard-question" className="sr-only">
              Ask a financial question
            </label>
            <input
              id="dashboard-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="e.g., What were Apple's Q4 Services gross margins and key headwinds?"
              className="w-full flex-1 rounded-lg bg-surface-container-lowest py-2.5 pl-4 pr-4 text-body-md text-on-surface placeholder:text-secondary transition-all focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
            <button
              type="submit"
              disabled={asking || !question.trim()}
              className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-primary px-5 py-2.5 text-label-md font-semibold text-on-primary shadow-sm transition-all hover:bg-primary-container disabled:cursor-not-allowed disabled:opacity-50"
            >
              {asking ? 'Querying…' : 'Query Documents'}
            </button>
          </form>

          <div className="flex flex-wrap items-center gap-2 pt-0.5">
            <span className="text-caption font-medium text-secondary">
              Suggested queries:
            </span>
            {SUGGESTED_QUERIES.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => setQuestion(suggestion)}
                className="inline-flex items-center rounded-full bg-surface-container-low px-3 py-1 text-label-sm text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
              >
                {suggestion.length > 42
                  ? `${suggestion.slice(0, 42)}…`
                  : suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>

      {askError && (
        <div
          role="alert"
          className="rounded-2xl border border-error/30 bg-error-container/60 px-6 py-4 text-body-md text-on-error-container"
        >
          {askError}
        </div>
      )}

      {answerState && (
        <section
          aria-label="Answer"
          className="rounded-2xl bg-surface-container-lowest p-6 shadow-[var(--shadow-card)]"
        >
          <h2 className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
            Question
          </h2>
          <p className="mt-2 whitespace-pre-wrap text-body-md font-medium text-on-surface">
            {answerState.question}
          </p>
          <h2 className="mt-6 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
            AI Answer
          </h2>
          <p className="mt-2 whitespace-pre-wrap text-body-lg leading-relaxed text-on-surface">
            {answerState.answer}
          </p>
          {answerState.sources.length > 0 && (
            <>
              <h3 className="mt-6 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                Sources
              </h3>
              <ul className="mt-3 flex flex-wrap gap-2">
                {answerState.sources.map((source, index) => (
                  <li
                    key={`${source.document_id}-${index}`}
                    className="rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-3 py-1.5 text-label-sm font-semibold tabular-nums text-[#1D4ED8]"
                  >
                    Doc #{source.document_id}
                    {source.page_start !== null &&
                      ` · pp. ${source.page_start}${
                        source.page_end !== source.page_start
                          ? `–${source.page_end}`
                          : ''
                      }`}
                    {' · '}
                    {(source.score * 100).toFixed(0)}%
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </div>
  )
}

export default function DashboardPage() {
  const [active, setActive] = useState<NavItemId>('dashboard')
  const [question, setQuestion] = useState('')
  const [answerState, setAnswerState] = useState<
    (RagAnswer & { question: string }) | null
  >(null)
  const [asking, setAsking] = useState(false)
  const [askError, setAskError] = useState<string | null>(null)
  const backendStatus = useBackendHealth()
  const { status: statsStatus, stats } = useDashboardStats()
  const { status: documentsStatus, documents } = useDocuments(0)
  const recent = recentDocuments(documents)

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || asking) return
    setAsking(true)
    setAskError(null)
    setAnswerState(null)
    try {
      setAnswerState({ ...(await askQuestion(trimmed)), question: trimmed })
    } catch (err) {
      setAskError(
        err instanceof Error ? err.message : 'Could not answer the question.',
      )
    } finally {
      setAsking(false)
    }
  }

  const docsValue =
    statsStatus === 'ready' && stats ? formatCount(stats.documents) : statsStatus === 'error' ? '—' : '…'
  const cosValue =
    statsStatus === 'ready' && stats ? formatCount(stats.companies) : statsStatus === 'error' ? '—' : '…'
  const metricsValue =
    statsStatus === 'ready' && stats
      ? formatCount(stats.financial_metrics)
      : statsStatus === 'error'
        ? '—'
        : '…'

  return (
    <div className="h-screen w-full overflow-hidden bg-background">
      <DashboardSidebar active={active} onSelect={setActive} />
      <div className="h-full pl-[104px] pr-6">
        <DashboardHeader
          active={active}
          status={backendStatus}
          onSelect={setActive}
        />
        <main className="h-full overflow-y-auto pb-8 pt-16">
          <div className="mx-auto flex w-full max-w-[1720px] flex-col gap-6 px-4 py-4 lg:px-8">
            {active === 'documents' ? (
              <DocumentsPage />
            ) : active === 'companies' ? (
              <CompaniesPage />
            ) : active === 'settings' ? (
              <SettingsPage />
            ) : active === 'chat' ? (
              <div className="mx-auto w-full max-w-4xl space-y-6">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                    <span className="text-label-sm uppercase tracking-wider text-secondary">
                      Synthesis Lab
                    </span>
                  </div>
                  <h1 className="mt-1 text-headline-lg font-bold tracking-tight text-on-surface">
                    Document Q&amp;A Assistant
                  </h1>
                  <p className="mt-2 max-w-2xl text-body-md text-on-surface-variant">
                    Grounded answers from your uploaded filings, with page-level
                    citations.
                  </p>
                </div>
                <AskPanel
                  question={question}
                  setQuestion={setQuestion}
                  asking={asking}
                  onAsk={handleAsk}
                  askError={askError}
                  answerState={answerState}
                />
              </div>
            ) : (
              <div className="flex flex-col gap-6">
                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                      <span className="text-label-sm uppercase tracking-wider text-secondary">
                        Institutional Synthesis Engine
                      </span>
                    </div>
                    <h1 className="text-headline-lg font-bold tracking-tight text-on-surface">
                      Institutional Research Canvas
                    </h1>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActive('documents')}
                    className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-1.5 text-label-md font-semibold text-on-primary shadow-md transition-all hover:bg-primary-container active:scale-95"
                  >
                    New Document
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
                  <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-surface-container-lowest p-5 shadow-[var(--shadow-card)] transition-shadow hover:shadow-md lg:p-6">
                    <div className="pointer-events-none absolute right-0 top-0 h-24 w-24 rounded-bl-full bg-primary/5 transition-transform group-hover:scale-110" />
                    <div className="mb-3 flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-container-low text-primary">
                          <FileText size={18} />
                        </div>
                        <span className="text-label-md font-medium text-secondary">
                          Documents
                        </span>
                      </div>
                    </div>
                    <div className="mb-3 flex items-baseline gap-2">
                      <span className="text-metric-numeral font-bold tracking-tight text-on-surface">
                        {docsValue}
                      </span>
                      <span className="text-caption text-secondary">
                        filings in library
                      </span>
                    </div>
                    <div className="rounded-xl bg-surface-container-low/50 px-2.5 py-1.5 text-caption text-secondary">
                      Live from your workspace
                    </div>
                  </div>

                  <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-surface-container-lowest p-5 shadow-[var(--shadow-card)] transition-shadow hover:shadow-md lg:p-6">
                    <div className="pointer-events-none absolute right-0 top-0 h-24 w-24 rounded-bl-full bg-tertiary/5 transition-transform group-hover:scale-110" />
                    <div className="mb-3 flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-container-low text-tertiary">
                          <Building2 size={18} />
                        </div>
                        <span className="text-label-md font-medium text-secondary">
                          Companies
                        </span>
                      </div>
                    </div>
                    <div className="mb-3 flex items-baseline gap-2">
                      <span className="text-metric-numeral font-bold tracking-tight text-on-surface">
                        {cosValue}
                      </span>
                      <span className="text-caption text-secondary">
                        in portfolio
                      </span>
                    </div>
                    <div className="rounded-xl bg-surface-container-low/50 px-2.5 py-1.5 text-caption text-secondary">
                      Per-user company directory
                    </div>
                  </div>

                  <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-surface-container-lowest p-5 shadow-[var(--shadow-card)] transition-shadow hover:shadow-md lg:p-6">
                    <div className="pointer-events-none absolute right-0 top-0 h-24 w-24 rounded-bl-full bg-primary/5 transition-transform group-hover:scale-110" />
                    <div className="mb-3 flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-container-low text-primary">
                          <Target size={18} />
                        </div>
                        <span className="text-label-md font-medium text-secondary">
                          Financial Metrics
                        </span>
                      </div>
                    </div>
                    <div className="mb-3 flex items-baseline gap-2">
                      <span className="text-metric-numeral font-bold tracking-tight text-on-surface">
                        {metricsValue}
                      </span>
                      <span className="text-caption text-secondary">
                        extracted figures
                      </span>
                    </div>
                    <div className="rounded-xl bg-surface-container-low/50 px-2.5 py-1.5 text-caption text-secondary">
                      From processed documents
                    </div>
                  </div>
                </div>

                <AskPanel
                  question={question}
                  setQuestion={setQuestion}
                  asking={asking}
                  onAsk={handleAsk}
                  askError={askError}
                  answerState={answerState}
                />

                <section
                  aria-label="Recent documents"
                  className="rounded-2xl bg-surface-container-lowest p-5 shadow-[var(--shadow-card)] lg:p-6"
                >
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-title-md font-bold text-on-surface">
                          Recent Filings &amp; Processing Pipeline
                        </h2>
                        <span className="h-2 w-2 rounded-full bg-tertiary" />
                      </div>
                      <span className="text-caption text-secondary">
                        Latest uploads in your workspace
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setActive('documents')}
                      className="text-label-sm font-semibold text-primary hover:underline"
                    >
                      View all
                    </button>
                  </div>

                  {documentsStatus === 'loading' ? (
                    <p className="p-8 text-center text-body-md text-on-surface-variant">
                      Loading documents…
                    </p>
                  ) : documentsStatus === 'error' ? (
                    <p
                      role="alert"
                      className="p-8 text-center text-body-md text-on-error-container"
                    >
                      Could not load documents. Check that the backend is running.
                    </p>
                  ) : recent.length === 0 ? (
                    <div className="p-8 text-center">
                      <p className="text-headline-sm text-on-surface">
                        No documents yet
                      </p>
                      <p className="mt-2 text-body-md text-on-surface-variant">
                        Upload a filing from Documents to see it here.
                      </p>
                      <button
                        type="button"
                        onClick={() => setActive('documents')}
                        className="mt-4 rounded-xl bg-primary px-6 py-2.5 text-body-md font-semibold text-on-primary hover:bg-primary-container"
                      >
                        Go to Documents
                      </button>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[620px] border-collapse text-left">
                        <thead>
                          <tr className="rounded-lg bg-surface-container-low/70 text-label-sm uppercase tracking-wider text-secondary">
                            <th className="rounded-l-lg px-3 py-2.5">Document</th>
                            <th className="px-3 py-2.5">Company</th>
                            <th className="px-3 py-2.5">Type</th>
                            <th className="px-3 py-2.5">Uploaded</th>
                            <th className="rounded-r-lg px-3 py-2.5 text-right">
                              Status
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {recent.map((doc) => (
                            <tr
                              key={doc.id}
                              className="cursor-pointer border-b border-outline-variant/40 last:border-0 hover:bg-surface-container-low/50"
                              onClick={() => setActive('documents')}
                            >
                              <td className="px-3 py-3">
                                <span className="flex items-center gap-2 text-body-md font-medium text-on-surface">
                                  {doc.title}
                                  <ArrowUpRight
                                    size={14}
                                    className="shrink-0 text-on-surface-variant/50"
                                  />
                                </span>
                              </td>
                              <td className="px-3 py-3 text-body-md text-on-surface-variant">
                                {doc.company_name ?? '—'}
                              </td>
                              <td className="px-3 py-3">
                                <span className="rounded-lg bg-secondary-container px-2.5 py-1 text-label-sm font-semibold text-on-secondary-container">
                                  {doc.document_type}
                                </span>
                              </td>
                              <td className="px-3 py-3 text-data-tabular text-on-surface-variant">
                                {formatUploadedAt(doc.created_at)}
                              </td>
                              <td className="px-3 py-3 text-right">
                                <StatusBadge status={doc.processing_status} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
