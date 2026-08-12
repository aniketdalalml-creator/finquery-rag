import { Logo } from '../../../shared/components/Logo'

export function EmptyState() {
  return (
    <div className="flex min-h-full w-full flex-col items-center justify-center px-6 py-16 text-center">
      <div className="flex w-full max-w-2xl flex-col items-center gap-8">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-surface-container shadow-sm">
          <Logo size={40} />
        </div>
        <div className="space-y-3">
          <h1 className="text-4xl font-bold tracking-tight text-on-surface md:text-5xl">
            FinQuery
          </h1>
          <h2 className="text-xl font-medium text-on-surface-variant md:text-2xl">
            Your AI financial research assistant
          </h2>
          <p className="text-base text-outline md:text-lg">
            Ask questions about companies, financials and markets.
          </p>
        </div>
      </div>
    </div>
  )
}
