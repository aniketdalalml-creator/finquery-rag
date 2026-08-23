import { useEffect, useState } from 'react'
import { getDocumentPages } from '../../../services/api'
import type { DocumentPageItem } from '../../../types/api'

export type PagesStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useDocumentPages(documentId: number | null): {
  status: PagesStatus
  pages: DocumentPageItem[]
} {
  const [status, setStatus] = useState<PagesStatus>('idle')
  const [pages, setPages] = useState<DocumentPageItem[]>([])

  useEffect(() => {
    if (documentId === null) {
      setStatus('idle')
      setPages([])
      return
    }
    let cancelled = false
    setStatus('loading')
    getDocumentPages(documentId)
      .then((items) => {
        if (!cancelled) {
          setPages(items)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [documentId])

  return { status, pages }
}
