import type { HealthResponse } from '../types'
import type { ApiStatus } from '../hooks/useApiHealth'

type SettingsPanelProps = {
  health: HealthResponse | null
  status: ApiStatus
  onRefresh: () => void
  onIngest: () => Promise<void>
  ingesting?: boolean
  ingestMessage?: string | null
}

function Row({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-outline-variant/40 py-3 last:border-0">
      <span className="text-body-md text-on-surface-variant">{label}</span>
      <span
        className={`text-right text-body-md font-medium ${
          ok === false ? 'text-error' : ok === true ? 'text-on-primary-container' : 'text-on-surface'
        }`}
      >
        {value}
      </span>
    </div>
  )
}

export function SettingsPanel({
  health,
  status,
  onRefresh,
  onIngest,
  ingesting,
  ingestMessage,
}: SettingsPanelProps) {
  return (
    <div className="mx-auto w-full max-w-xl px-6 py-12">
      <h1 className="text-headline-lg font-semibold text-on-surface">Settings</h1>
      <p className="mt-2 text-body-md text-on-surface-variant">
        Backend connection and index status for FinQuery RAG.
      </p>

      <div className="mt-8 rounded-2xl border border-outline-variant/40 bg-surface-container-lowest p-6 shadow-sm">
        <h2 className="mb-2 text-headline-md font-semibold text-on-surface">API</h2>
        <Row
          label="Connection"
          value={
            status === 'online'
              ? 'Online'
              : status === 'not-ready'
                ? 'Connected (empty index)'
                : status === 'checking'
                  ? 'Checking…'
                  : 'Offline'
          }
          ok={status === 'online'}
        />
        <Row label="Chat mode" value={health?.chat_mode ?? '—'} />
        <Row label="Endpoint" value="/api → localhost:8000" />
        <Row label="Model" value={health?.llm_model ?? '—'} />
        <Row
          label="Groq key"
          value={health?.groq_configured ? 'Configured' : 'Missing / invalid'}
          ok={health?.groq_configured}
        />
        <Row
          label="Jina key"
          value={health?.jina_configured ? 'Configured' : 'Missing'}
          ok={health?.jina_configured}
        />
        <Row label="Chunks indexed" value={String(health?.total_chunks ?? 0)} />

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-lg border border-outline-variant px-4 py-2 text-label-sm font-semibold text-on-surface transition-colors hover:bg-surface-container"
          >
            Refresh status
          </button>
          <button
            type="button"
            onClick={() => void onIngest()}
            disabled={ingesting || status === 'offline'}
            className="rounded-lg bg-primary-container px-4 py-2 text-label-sm font-semibold text-on-primary-container transition-colors hover:bg-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {ingesting ? 'Ingesting…' : 'Re-ingest documents'}
          </button>
        </div>
        {ingestMessage && (
          <p className="mt-4 text-label-sm text-on-surface-variant">{ingestMessage}</p>
        )}
      </div>
    </div>
  )
}
