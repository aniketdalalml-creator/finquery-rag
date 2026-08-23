import { useState } from 'react'
import { UploadPdfCard } from './components/UploadPdfCard'
import { DocumentsTable } from './components/DocumentsTable'
import { useDocuments } from '../../hooks/useDocuments'

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0)
  const { status, documents } = useDocuments(refreshKey)

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
      <UploadPdfCard onSuccess={() => setRefreshKey((key) => key + 1)} />
      <section aria-label="Document library">
        <h2 className="text-headline-md tracking-tight text-on-surface">
          Document Library
        </h2>
        <div className="mt-4">
          <DocumentsTable status={status} documents={documents} />
        </div>
      </section>
    </div>
  )
}
