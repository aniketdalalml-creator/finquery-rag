import { useEffect, useState } from 'react'
import { listCompanies } from '../services/api'
import type { CompanyOption } from '../types/api'

export function useCompanies(): {
  companies: CompanyOption[]
  loading: boolean
  error: string | null
} {
  const [companies, setCompanies] = useState<CompanyOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    listCompanies()
      .then((items) => {
        if (!cancelled) setCompanies(items)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { companies, loading, error }
}
