import { useAuth } from '../../auth/AuthContext'
import { useSystemHealth } from '../../hooks/useSystemHealth'

function Row({
  label,
  value,
  ok,
}: {
  label: string
  value: string
  ok?: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-outline-variant/50 py-3 last:border-0">
      <span className="text-body-md text-on-surface-variant">{label}</span>
      <span
        className={`text-right text-body-md font-medium ${
          ok === false
            ? 'text-error'
            :           ok === true
              ? 'text-success'
              : 'text-on-surface'
        }`}
      >
        {value}
      </span>
    </div>
  )
}

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const { status, health, refresh } = useSystemHealth()

  const connectionLabel =
    status === 'loading'
      ? 'Checking…'
      : status === 'error'
        ? 'Offline'
        : health?.status === 'ok'
          ? 'Online'
          : 'Degraded'

  const connectionOk =
    status === 'ready' && health?.status === 'ok' ? true : status === 'error' ? false : undefined

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
          <span className="text-label-sm uppercase tracking-wider text-secondary">
            Workspace
          </span>
        </div>
        <h1 className="mt-1 text-headline-lg font-bold tracking-tight text-on-surface">
          Settings
        </h1>
        <p className="mt-2 max-w-2xl text-body-md text-on-surface-variant">
          Account, backend health, and session controls for FinanceIQ.
        </p>
      </div>

      <section
        aria-label="Account"
        className="rounded-2xl bg-surface-container-lowest p-6 shadow-[var(--shadow-card)]"
      >
        <h2 className="text-headline-md tracking-tight text-on-surface">Account</h2>
        <p className="mt-1 text-body-md text-on-surface-variant/80">
          Signed-in user for this browser session.
        </p>
        <div className="mt-4">
          <Row label="Email" value={user?.email ?? '—'} />
          <Row
            label="Status"
            value={user?.is_active ? 'Active' : 'Inactive'}
            ok={user?.is_active}
          />
          <Row label="User ID" value={user ? String(user.id) : '—'} />
        </div>
        <button
          type="button"
          onClick={logout}
          className="mt-6 rounded-xl border border-outline-variant px-6 py-2.5 text-body-md font-semibold text-on-surface-variant hover:bg-surface-container-low"
        >
          Log out
        </button>
      </section>

      <section
        aria-label="System status"
        className="rounded-2xl bg-surface-container-lowest p-6 shadow-[var(--shadow-card)]"
      >
        <h2 className="text-headline-md tracking-tight text-on-surface">System</h2>
        <p className="mt-1 text-body-md text-on-surface-variant/80">
          Live status from the API health endpoint. API keys are never shown.
        </p>
        <div className="mt-4">
          <Row label="Connection" value={connectionLabel} ok={connectionOk} />
          <Row label="Chat mode" value={health?.chat_mode ?? '—'} />
          <Row label="LLM model" value={health?.llm_model ?? '—'} />
          <Row
            label="Pipeline ready"
            value={
              status === 'loading'
                ? '…'
                : health?.pipeline_ready
                  ? 'Yes'
                  : 'No'
            }
            ok={health?.pipeline_ready}
          />
          <Row
            label="Groq"
            value={
              health == null
                ? '—'
                : health.groq_configured
                  ? 'Configured'
                  : 'Missing'
            }
            ok={health?.groq_configured}
          />
          <Row
            label="Jina embeddings"
            value={
              health == null
                ? '—'
                : health.jina_configured
                  ? 'Configured'
                  : 'Missing'
            }
            ok={health?.jina_configured}
          />
          <Row
            label="Chunks indexed"
            value={health == null ? '—' : String(health.total_chunks ?? 0)}
          />
        </div>
        <button
          type="button"
          onClick={refresh}
          className="mt-6 rounded-xl bg-primary px-6 py-2.5 text-body-md font-semibold text-on-primary hover:bg-primary-container"
        >
          Refresh status
        </button>
      </section>

      <section
        aria-label="About"
        className="rounded-2xl bg-surface-container-lowest p-6 shadow-[var(--shadow-card)]"
      >
        <h2 className="text-headline-md tracking-tight text-on-surface">About</h2>
        <div className="mt-4">
          <Row label="Product" value="FinanceIQ / FinQuery" />
          <Row label="Version" value="0.1" />
          <Row label="Stack" value="FastAPI · React · MySQL · Vector DB" />
        </div>
        <p className="mt-4 text-body-md text-on-surface-variant/80">
          Document processing runs from the Documents page (upload → process).
          Companies are managed under Companies.
        </p>
      </section>
    </div>
  )
}
