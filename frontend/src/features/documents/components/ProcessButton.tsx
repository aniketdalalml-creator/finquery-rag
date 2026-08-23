import { useEffect, useRef, useState } from 'react'
import { Loader2, Play } from 'lucide-react'
import { getDocumentStatus, processDocument } from '../../../services/api'

const TERMINAL_STATUSES = new Set([
  'processed',
  'completed',
  'partially_processed',
  'failed',
])
const POLL_INTERVAL_MS = 1500

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

type ProcessButtonProps = {
  documentId: number
  onFinished: () => void
  onError: (message: string) => void
}

export function ProcessButton({
  documentId,
  onFinished,
  onError,
}: ProcessButtonProps) {
  const [running, setRunning] = useState(false)
  // Survives parent re-renders caused by list refreshes mid-poll.
  const finishedRef = useRef(onFinished)
  const errorRef = useRef(onError)
  useEffect(() => {
    finishedRef.current = onFinished
    errorRef.current = onError
  }, [onFinished, onError])

  async function handleClick() {
    setRunning(true)
    try {
      await processDocument(documentId)
      // Poll until the pipeline reports a terminal status.
      for (;;) {
        const status = await getDocumentStatus(documentId)
        if (TERMINAL_STATUSES.has(status.status)) break
        if (status.status === 'uploaded') {
          throw new Error('Processing was interrupted — please try again.')
        }
        await sleep(POLL_INTERVAL_MS)
      }
      finishedRef.current()
    } catch (err) {
      errorRef.current(
        err instanceof Error ? err.message : 'Processing failed unexpectedly.',
      )
    } finally {
      setRunning(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={running}
      title={running ? 'Processing…' : 'Run the ingestion pipeline'}
      className="inline-flex items-center gap-1.5 rounded-lg border border-outline-variant bg-surface-container-low px-3 py-1.5 text-label-sm font-semibold text-on-surface transition-colors hover:bg-surface-container-high disabled:cursor-not-allowed disabled:opacity-50"
    >
      {running ? (
        <Loader2 size={14} className="animate-spin" />
      ) : (
        <Play size={14} />
      )}
      {running ? 'Processing…' : 'Process'}
    </button>
  )
}
