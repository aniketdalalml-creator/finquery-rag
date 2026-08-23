type DashboardHeaderProps = {
  title: string
}

export function DashboardHeader({ title }: DashboardHeaderProps) {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-8">
      <span className="text-headline-md tracking-tight text-on-surface">
        {title}
      </span>
      <div
        className="flex items-center gap-2 rounded-full border border-outline-variant bg-surface-container-low px-4 py-1.5"
        aria-label="System status: all systems operational"
      >
        <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
          <span className="absolute inline-flex h-full w-full rounded-full bg-primary opacity-60" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#00a344]" />
        </span>
        <span className="text-label-sm font-semibold text-on-surface-variant">
          All systems operational
        </span>
      </div>
    </header>
  )
}
