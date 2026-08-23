import { UploadPdfCard } from './components/UploadPdfCard'

export default function DocumentsPage() {
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
      <UploadPdfCard />
    </div>
  )
}
