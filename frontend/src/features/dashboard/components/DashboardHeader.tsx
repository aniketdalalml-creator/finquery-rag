import type { BackendStatus } from '../../../hooks/useBackendHealth'
import { useAuth } from '../../../auth/AuthContext'
import { Logo } from '../../../shared/components/Logo'
import { PAGE_TITLES, type NavItemId } from '../navigation'

const STATUS_UI: Record<
  BackendStatus,
  { dotClass: string; label: string }
> = {
  checking: {
    dotClass: 'bg-on-surface-variant/50',
    label: 'Checking…',
  },
  connected: {
    dotClass: 'bg-tertiary',
    label: 'Systems operational',
  },
  disconnected: {
    dotClass: 'bg-error',
    label: 'Backend offline',
  },
}

type DashboardHeaderProps = {
  active: NavItemId
  status: BackendStatus
  onSelect: (id: NavItemId) => void
}

export function DashboardHeader({
  active,
  status,
  onSelect,
}: DashboardHeaderProps) {
  const ui = STATUS_UI[status]
  const { user, logout } = useAuth()
  const initials = (user?.email ?? 'U').slice(0, 1).toUpperCase()

  return (
    <header className="fixed left-[104px] right-6 top-0 z-40 flex h-16 items-center justify-between bg-surface/80 px-4 shadow-[0_1px_8px_rgba(0,0,0,0.04)] backdrop-blur-xl">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <Logo size={32} />
          <span className="text-headline-sm tracking-tight text-on-surface">
            FinanceIQ
          </span>
        </div>
        <div className="hidden h-4 w-px bg-outline-variant/60 lg:block" />
        <nav
          className="hidden items-center gap-1.5 rounded-xl bg-surface-container-low p-1 lg:flex"
          aria-label="Section"
        >
          {(
            [
              ['dashboard', 'Overview'],
              ['documents', 'Filings'],
              ['chat', 'Synthesis Lab'],
            ] as const
          ).map(([id, label]) => {
            const isActive = active === id
            return (
              <button
                key={id}
                type="button"
                onClick={() => onSelect(id)}
                className={`rounded-lg px-3 py-1 text-label-md transition-colors ${
                  isActive
                    ? 'bg-surface-container-high font-semibold text-primary'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {label}
              </button>
            )
          })}
        </nav>
        <span className="text-label-md text-on-surface-variant lg:hidden">
          {PAGE_TITLES[active]}
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div
          role="status"
          aria-label={`System status: ${ui.label}`}
          className="hidden items-center gap-2 rounded-xl bg-surface-container-lowest px-3 py-1.5 shadow-sm sm:flex"
        >
          <span className={`h-2 w-2 rounded-full ${ui.dotClass}`} aria-hidden />
          <span className="text-label-sm font-semibold text-on-surface-variant">
            {ui.label}
          </span>
        </div>
        {user && (
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-container text-label-md font-semibold text-on-primary shadow-sm">
              {initials}
            </div>
            <div className="hidden flex-col text-left xl:flex">
              <span className="max-w-[12rem] truncate text-label-md font-semibold leading-tight text-on-surface">
                {user.email}
              </span>
              <span className="text-caption leading-tight text-secondary">
                Workspace
              </span>
            </div>
            <button
              type="button"
              onClick={logout}
              className="hidden rounded-lg px-3 py-1.5 text-label-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container-low hover:text-error sm:inline-flex"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
