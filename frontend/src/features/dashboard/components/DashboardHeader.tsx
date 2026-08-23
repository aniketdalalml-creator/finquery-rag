import type { BackendStatus } from '../../../hooks/useBackendHealth'

const STATUS_UI: Record<
  BackendStatus,
  { dotClass: string; label: string }
> = {
  checking: {
    dotClass: 'bg-on-surface-variant/50',
    label: 'Checking backend…',
  },
  connected: {
    dotClass: 'bg-[#00a344]',
    label: 'All systems operational',
  },
  disconnected: {
    dotClass: 'bg-error',
    label: 'Backend offline',
  },
}

type DashboardHeaderProps = {
  title: string
  status: BackendStatus
}

export function DashboardHeader({ title, status }: DashboardHeaderProps) {
  const ui = STATUS_UI[status]
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-8">
      <span className="text-headline-md tracking-tight text-on-surface">
        {title}
      </span>
      <div
        role="status"
        aria-label={`System status: ${ui.label}`}
        className="flex items-center gap-2 rounded-full border border-outline-variant bg-surface-container-low px-4 py-1.5"
      >
        <span className={`h-2.5 w-2.5 rounded-full ${ui.dotClass}`} aria-hidden="true" />
        <span className="text-label-sm font-semibold text-on-surface-variant">
          {ui.label}
        </span>
      </div>
    </header>
  )
}
