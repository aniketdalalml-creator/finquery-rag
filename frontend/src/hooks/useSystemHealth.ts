import { useCallback, useEffect, useState } from 'react'
import { getHealth } from '../services/api'
import type { HealthResponse } from '../types/api'

export type SystemHealthState = {
  status: 'loading' | 'ready' | 'error'
  health: HealthResponse | null
  refresh: () => void
}

export function useSystemHealth(): SystemHealthState {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    getHealth()
      .then((data) => {
        if (!cancelled) {
          setHealth(data)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHealth(null)
          setStatus('error')
        }
      })
    return () => {
      cancelled = true
    }
  }, [tick])

  const refresh = useCallback(() => setTick((t) => t + 1), [])
  return { status, health, refresh }
}
