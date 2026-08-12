import { useCallback, useEffect, useState } from 'react'
import { fetchHealth } from '../api/client'
import type { HealthResponse } from '../types'

export type ApiStatus = 'checking' | 'online' | 'offline' | 'not-ready'

export function useApiHealth(intervalMs = 15000) {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [status, setStatus] = useState<ApiStatus>('checking')
  const [lastChecked, setLastChecked] = useState<number | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await fetchHealth()
      setHealth(data)
      setStatus(data.pipeline_ready ? 'online' : 'not-ready')
      setLastChecked(Date.now())
    } catch {
      setHealth(null)
      setStatus('offline')
      setLastChecked(Date.now())
    }
  }, [])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(() => void refresh(), intervalMs)
    return () => window.clearInterval(id)
  }, [refresh, intervalMs])

  return { health, status, lastChecked, refresh }
}
