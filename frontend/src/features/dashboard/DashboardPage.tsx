import { useState, type FormEvent } from 'react'
import { ArrowUpRight } from 'lucide-react'
import { DashboardSidebar } from './components/DashboardSidebar'
import { DashboardHeader } from './components/DashboardHeader'
import type { NavItemId } from './navigation'
import { MOCK_RECENT_DOCUMENTS, type RecentDocument } from './mockData'
import { useBackendHealth } from '../../hooks/useBackendHealth'
import { useDashboardStats } from '../../hooks/useDashboardStats'
import { askQuestion } from '../../services/api'
import type { RagAnswer } from '../../types/api'
import DocumentsPage from '../documents/DocumentsPage'

const PAGE_TITLES: Record<NavItemId, string> = {
  dashboard: 'Financial Intelligence',
  documents: 'Documents',
  companies: 'Companies',
  settings: 'Settings',
}

const STATUS_STYLES: Record<RecentDocument['status'], string> = {
  Processed: 'bg-primary-container text-on-primary-container',
  Processing: 'bg-secondary-container text-on-secondary-container',
  Failed: 'bg-error-container text-on-error-container',
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: 'Documents' | 'Companies' | 'Financial Metrics'
  value: string
  hint: string
}) {
  return (
    <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6">
      <p className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
        {label}
      </p>
      <p className="mt-3 text-headline-lg tabular-nums text-on-surface">{value}</p>
      <p className="mt-1 text-label-sm text-on-surface-variant/80">{hint}</p>
    </div>
  )
}

function PlaceholderView({ title }: { title: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-12 text-center">
      <p className="text-headline-md text-on-surface">{title}</p>
      <p className="mt-2 text-body-md text-on-surface-variant/70">
        This area will be built in an upcoming milestone.
      </p>
    </div>
  )
}

function formatCount(n: number): string {
  return n.toLocaleString('en-US')
}

export default function DashboardPage() {
  const [active, setActive] = useState<NavItemId>('dashboard')
  const [question, setQuestion] = useState('')
  const [answerState, setAnswerState] = useState<RagAnswer & { question: string } | null>(null)
  const [asking, setAsking] = useState(false)
  const [askError, setAskError] = useState<string | null>(null)
  const backendStatus = useBackendHealth()
  const { status: statsStatus, stats } = useDashboardStats()

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

  const statCards = [
    { label: 'Documents' as const, key: 'documents' as const },
    { label: 'Companies' as const, key: 'companies' as const },
    { label: 'Financial Metrics' as const, key: 'financial_metrics' as const },
  ].map(({ label, key }) => {
    if (statsStatus === 'ready' && stats) {
      return { label, value: formatCount(stats[key]), hint: 'Live from database' }
    }
    if (statsStatus === 'error') {
      return { label, value: '—', hint: 'Stats unavailable (backend offline)' }
    }
    return { label, value: '…', hint: 'Loading stats…' }
  })

  return (
    <div className="flex h-screen w-full overflow-hidden bg-surface">
      <DashboardSidebar active={active} onSelect={setActive} />
      <div className="flex min-w-0 flex-1 flex-col">
        <DashboardHeader title="FinanceIQ" status={backendStatus} />
        <main className="flex-1 overflow-y-auto px-8 py-8">
          {active === 'documents' ? (
            <DocumentsPage />
          ) : active === 'dashboard' ? (
            <div className="mx-auto max-w-5xl space-y-10">
              <div>
                <h1 className="text-display-lg tracking-tight text-on-surface">
                  Financial Intelligence
                </h1>
                <p className="mt-3 max-w-2xl text-body-lg text-on-surface-variant">
                  Ask questions across filings and get grounded answers with
                  sources. Start with a question below or browse your document
                  library.
                </p>
              </div>

              <form onSubmit={handleAsk} className="flex flex-col gap-4">
                <label htmlFor="dashboard-question" className="sr-only">
                  Ask a financial question
                </label>
                <textarea
                  id="dashboard-question"
                  rows={3}
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="e.g. What was Apple's total net sales in fiscal year 2024?"
                  className="w-full resize-none rounded-2xl border border-outline-variant bg-surface-container-lowest px-6 py-4 text-body-lg text-on-surface placeholder:text-on-surface-variant/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                <button
                  type="submit"
                  disabled={asking || !question.trim()}
                  className="self-start rounded-xl bg-[#006d38] px-8 py-3 text-body-md font-semibold text-on-primary transition-colors hover:bg-[#005c2f] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {asking ? 'Thinking…' : 'Ask'}
                </button>
              </form>

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
                  className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6"
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
                            className="rounded-lg bg-secondary-container px-3 py-1.5 text-label-sm font-semibold text-on-secondary-container tabular-nums"
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

              <section aria-label="Key statistics">
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                  {statCards.map((stat) => (
                    <StatCard key={stat.label} {...stat} />
                  ))}
                </div>
              </section>

              <section aria-label="Recent documents">
                <h2 className="text-headline-md tracking-tight text-on-surface">
                  Recent Documents
                </h2>
                <div className="mt-4 overflow-hidden rounded-2xl border border-outline-variant bg-surface-container-lowest">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-outline-variant bg-surface-container-low">
                        <th className="px-6 py-3 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                          Document
                        </th>
                        <th className="px-6 py-3 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                          Company
                        </th>
                        <th className="px-6 py-3 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                          Type
                        </th>
                        <th className="px-6 py-3 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                          Uploaded
                        </th>
                        <th className="px-6 py-3 text-right text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {MOCK_RECENT_DOCUMENTS.map((doc) => (
                        <tr
                          key={doc.id}
                          className="border-b border-outline-variant/60 last:border-b-0 hover:bg-surface-container-low"
                        >
                          <td className="px-6 py-4">
                            <span className="flex items-center gap-2 text-body-md font-medium text-on-surface">
                              {doc.title}
                              <ArrowUpRight
                                size={14}
                                className="text-on-surface-variant/50"
                              />
                            </span>
                            <span className="text-label-sm text-on-surface-variant/70">
                              FY{doc.fiscalYear}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-body-md text-on-surface-variant">
                            {doc.company}
                          </td>
                          <td className="px-6 py-4">
                            <span className="rounded-lg bg-secondary-container px-2.5 py-1 text-label-sm font-semibold text-on-secondary-container">
                              {doc.documentType}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-data-tabular text-on-surface-variant">
                            {doc.uploadedAt}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <span
                              className={`inline-block rounded-full px-3 py-1 text-label-sm font-semibold ${STATUS_STYLES[doc.status]}`}
                            >
                              {doc.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          ) : (
            <PlaceholderView title={PAGE_TITLES[active]} />
          )}
        </main>
      </div>
    </div>
  )
}
