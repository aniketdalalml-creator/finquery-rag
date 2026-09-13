import { LogOut } from 'lucide-react'
import { Logo } from '../../../shared/components/Logo'
import { useAuth } from '../../../auth/AuthContext'
import { NAV_ITEMS, type NavItemId } from '../navigation'

type DashboardSidebarProps = {
  active: NavItemId
  onSelect: (id: NavItemId) => void
}

export function DashboardSidebar({ active, onSelect }: DashboardSidebarProps) {
  const { logout } = useAuth()

  return (
    <aside className="fixed bottom-4 left-4 top-4 z-50 flex w-[72px] flex-col items-center justify-between rounded-2xl bg-inverse-surface py-5 shadow-[var(--shadow-dock)]">
      <div className="flex w-full flex-col items-center gap-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl shadow-sm">
          <Logo size={40} />
        </div>
        <nav
          className="flex w-full flex-col items-center gap-3 px-3"
          aria-label="Main navigation"
        >
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
            const isActive = id === active
            return (
              <button
                key={id}
                type="button"
                title={label}
                onClick={() => onSelect(id)}
                aria-current={isActive ? 'page' : undefined}
                className={`flex h-11 w-11 items-center justify-center rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-primary-container text-on-primary shadow-md'
                    : 'text-secondary-fixed-dim hover:bg-surface-container-high/20 hover:text-surface'
                }`}
              >
                <Icon size={22} strokeWidth={2} />
              </button>
            )
          })}
        </nav>
      </div>
      <div className="flex w-full flex-col items-center px-3">
        <button
          type="button"
          title="Log out"
          onClick={logout}
          className="flex h-11 w-11 items-center justify-center rounded-xl text-secondary-fixed-dim transition-all duration-200 hover:bg-surface-container-high/20 hover:text-surface"
        >
          <LogOut size={22} strokeWidth={2} />
        </button>
      </div>
    </aside>
  )
}
