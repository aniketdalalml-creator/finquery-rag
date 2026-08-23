import { useState } from 'react'
import { UploadPdfCard } from './components/UploadPdfCard'
import { DocumentsTable } from './components/DocumentsTable'
import { DocumentViewer } from './components/DocumentViewer'
import { useDocuments } from '../../hooks/useDocuments'
import type { DocumentListItem } from '../../types/api'

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [processError, setProcessError] = useState<string | null>(null)
  const [selectedDocument, setSelectedDocument] =
    useState<DocumentListItem | null>(null)
  const { status, documents } = useDocuments(refreshKey)

  if (selectedDocument !== null) {
    return (
      <div className="mx-auto max-w-4xl">
        <DocumentViewer
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)}
        />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <h1 className="text-display-lg tracking-tight text-on-surface">
          Documents
        </h1>
        <p className="mt-3 max-w-2xl text-body-lg text-on-surface-variant">
          Upload filings and manage your document library.
        </p>
      </div>
      {processError && (
        <div
          role="alert"
          className="flex items-start justify-between gap-4 rounded-xl border border-error/30 bg-error-container/60 px-5 py-4 text-body-md text-on-error-container"
        >
          <span>Processing error: {processError}</span>
          <button
            type="button"
            onClick={() => setProcessError(null)}
            className="text-label-sm font-semibold underline underline-offset-2"
          >
            Dismiss
          </button>
        </div>
      )}
      <UploadPdfCard onSuccess={() => setRefreshKey((key) => key + 1)} />
      <section aria-label="Document library">
        <h2 className="text-headline-md tracking-tight text-on-surface">
          Document Library
        </h2>
        <div className="mt-4">
          <DocumentsTable
            status={status}
            documents={documents}
            onProcessed={() => setRefreshKey((key) => key + 1)}
            onProcessError={(message) => {
              setProcessError(message)
              setRefreshKey((key) => key + 1)
            }}
            onSelectDocument={setSelectedDocument}
          />
        </div>
      </section>
    </div>
  )
}
