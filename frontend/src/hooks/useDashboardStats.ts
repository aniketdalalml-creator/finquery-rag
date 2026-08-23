import { useEffect, useState } from 'react'
import { getDashboardStats } from '../services/api'
import type { DashboardStats } from '../types/api'

export type StatsStatus = 'loading' | 'ready' | 'error'

export function useDashboardStats(): {
  status: StatsStatus
  stats: DashboardStats | null
} {
  const [status, setStatus] = useState<StatsStatus>('loading')
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    let cancelled = false
    getDashboardStats()
      .then((data) => {
        if (!cancelled) {
          setStats(data)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { status, stats }
}
