import { useCallback, useEffect, useState } from 'react'
import { listDocuments } from '../services/api'
import type { DocumentListItem } from '../types/api'

export type ListStatus = 'loading' | 'ready' | 'error'

export function useDocuments(refreshKey: number): {
  status: ListStatus
  documents: DocumentListItem[]
  refresh: () => void
} {
  const [status, setStatus] = useState<ListStatus>('loading')
  const [documents, setDocuments] = useState<DocumentListItem[]>([])
  // Bumped by consumers to force a refetch without a page reload.
  const [reloadTick, setReloadTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    listDocuments()
      .then((items) => {
        if (!cancelled) {
          setDocuments(items)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [refreshKey, reloadTick])

  const refresh = useCallback(() => setReloadTick((t) => t + 1), [])
  return { status, documents, refresh }
}
