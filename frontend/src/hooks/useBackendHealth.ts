import { useEffect, useState } from 'react'
import { getHealth } from '../services/api'

export type BackendStatus = 'checking' | 'connected' | 'disconnected'

export function useBackendHealth(): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>('checking')

  useEffect(() => {
    let cancelled = false
    getHealth()
      .then((health) => {
        if (!cancelled) {
          setStatus(health.status === 'ok' ? 'connected' : 'disconnected')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus('disconnected')
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  return status
}
