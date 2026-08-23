import { NAV_ITEMS, type NavItemId } from '../navigation'

type DashboardSidebarProps = {
  active: NavItemId
  onSelect: (id: NavItemId) => void
}

export function DashboardSidebar({ active, onSelect }: DashboardSidebarProps) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-outline-variant bg-surface-container-low">
      <div className="px-6 py-5">
        <span className="text-label-sm font-semibold uppercase tracking-wider text-outline">
          Workspace
        </span>
      </div>
      <nav className="space-y-1 px-3" aria-label="Main navigation">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const isActive = id === active
          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelect(id)}
              aria-current={isActive ? 'page' : undefined}
              className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-body-md transition-colors ${
                isActive
                  ? 'bg-primary-container font-semibold text-on-primary-container'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`}
            >
              <Icon size={18} strokeWidth={2.25} />
              {label}
            </button>
          )
        })}
      </nav>
      <div className="mt-auto px-6 py-5">
        <p className="text-label-sm text-on-surface-variant/70">FinanceIQ v0.1</p>
      </div>
    </aside>
  )
}
