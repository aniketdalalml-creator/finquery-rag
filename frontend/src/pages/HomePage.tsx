import { StatusRow } from '../components/StatusRow'
import { useBackendHealth } from '../hooks/useBackendHealth'

const BACKEND_STATUS_LABELS = {
  checking: 'Checking...',
  connected: 'Connected',
  disconnected: 'Disconnected',
} as const

export default function HomePage() {
  const backendStatus = useBackendHealth()

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-2">
      <h1 className="text-4xl font-bold">Finance AI</h1>
      <h2 className="text-xl text-neutral-600">Platform</h2>
      <div className="mt-6 flex flex-col gap-1">
        <StatusRow label="Frontend" value="Running" />
        <StatusRow label="Backend" value={BACKEND_STATUS_LABELS[backendStatus]} />
      </div>
    </main>
  )
}
