import { Plus, Settings, X } from 'lucide-react'
import type { ChatSession } from '../types'
import { Logo } from '../../../shared/components/Logo'

type SidebarProps = {
  sessions: ChatSession[]
  activeId: string | null
  onNewChat: () => void
  onSelect: (id: string) => void
  open?: boolean
  onClose?: () => void
  settingsOpen?: boolean
  onToggleSettings?: () => void
}

export function Sidebar({
  sessions,
  activeId,
  onNewChat,
  onSelect,
  open = true,
  onClose,
  settingsOpen,
  onToggleSettings,
}: SidebarProps) {
  return (
    <>
      {open && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-on-surface/20 backdrop-blur-[2px] lg:hidden"
          aria-label="Close sidebar"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed left-0 top-0 z-50 flex h-full w-72 flex-col border-r border-outline-variant bg-surface-container-low transition-transform duration-300 ${
          open ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="flex items-center gap-3 p-6">
          <Logo size={32} />
          <span className="text-headline-md font-semibold tracking-tight text-on-surface">
            FinQuery
          </span>
        </div>

        <div className="mb-6 px-4">
          <button
            type="button"
            onClick={() => {
              onNewChat()
              onClose?.()
            }}
            className="flex w-full items-center gap-3 rounded-xl border border-outline-variant bg-surface-container-lowest px-4 py-3 text-label-sm font-semibold text-on-surface transition-all hover:bg-surface-container-high"
          >
            <Plus size={18} strokeWidth={2.25} />
            New Chat
          </button>
        </div>

        <div className="flex-1 space-y-1 overflow-y-auto px-4">
          <div className="px-4 py-2 text-label-sm font-semibold uppercase tracking-wider text-outline">
            Recent Chats
          </div>
          <nav className="space-y-1">
            {sessions.length === 0 && (
              <p className="px-4 py-2 text-body-md text-on-surface-variant/70">
                No chats yet
              </p>
            )}
            {sessions.map((s) => {
              const active = s.id === activeId
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    onSelect(s.id)
                    onClose?.()
                  }}
                  className={`flex w-full items-center truncate rounded-xl px-4 py-3 text-left transition-all ${
                    active
                      ? 'bg-primary-container font-semibold text-on-primary-container'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                  }`}
                >
                  {s.title}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="border-t border-outline-variant p-4">
          <button
            type="button"
            onClick={onToggleSettings}
            className={`flex w-full items-center rounded-xl px-4 py-3 text-body-md transition-all ${
              settingsOpen
                ? 'bg-surface-container-high text-on-surface'
                : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
            }`}
          >
            {settingsOpen ? <X size={18} className="mr-3" /> : <Settings size={18} className="mr-3" />}
            {settingsOpen ? 'Close settings' : 'Settings'}
          </button>
        </div>
      </aside>
    </>
  )
}
