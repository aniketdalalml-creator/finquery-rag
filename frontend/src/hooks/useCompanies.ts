import { useEffect, useState } from 'react'
import { listCompanyOptions } from '../services/api'
import type { CompanyOption } from '../types/api'

export function useCompanies(refreshKey = 0): {
  companies: CompanyOption[]
  loading: boolean
  error: string | null
} {
  const [companies, setCompanies] = useState<CompanyOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    listCompanyOptions()
      .then((items) => {
        if (!cancelled) {
          setCompanies(items)
          setError(null)
        }
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
  }, [refreshKey])

  return { companies, loading, error }
}
