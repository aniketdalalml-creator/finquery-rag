import { Menu } from 'lucide-react'
import { Logo } from './Logo'

type HeaderProps = {
  onMenuClick?: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="absolute left-0 right-0 top-0 z-30 flex h-16 shrink-0 items-center justify-between bg-surface/80 px-4 backdrop-blur-xl lg:left-0 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="rounded-lg p-2 text-on-surface-variant hover:bg-surface-container lg:hidden"
          onClick={onMenuClick}
          aria-label="Open menu"
        >
          <Menu size={22} />
        </button>
        <Logo size={24} className="opacity-50" />
      </div>
      <div className="flex items-center gap-4">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full border border-outline-variant bg-surface-container text-label-sm font-semibold text-on-surface-variant"
          aria-hidden
        >
          U
        </div>
      </div>
    </header>
  )
}
