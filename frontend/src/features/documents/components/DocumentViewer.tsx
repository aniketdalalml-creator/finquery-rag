import { ArrowLeft, FileText } from 'lucide-react'
import { StatusBadge } from './StatusBadge'
import { useDocumentPages } from '../hooks/useDocumentPages'
import type { DocumentListItem } from '../../../types/api'

type DocumentViewerProps = {
  document: DocumentListItem
  onClose: () => void
}

export function DocumentViewer({ document, onClose }: DocumentViewerProps) {
  const { status, pages } = useDocumentPages(document.id)

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={onClose}
        className="inline-flex items-center gap-1.5 text-label-lg font-semibold text-on-surface-variant transition-colors hover:text-on-surface"
      >
        <ArrowLeft size={16} />
        Back to documents
      </button>

      <header className="rounded-2xl border border-outline-variant bg-surface-container-lowest px-6 py-5">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <FileText size={22} className="shrink-0 text-primary" />
          <h2 className="text-headline-md tracking-tight text-on-surface">
            {document.title}
          </h2>
          <StatusBadge status={document.processing_status} />
        </div>
        <p className="mt-2 text-body-md text-on-surface-variant">
          {pages.length > 0
            ? `${pages.length} page${pages.length === 1 ? '' : 's'} extracted`
            : document.company_name
              ? `${document.company_name} · ${document.document_type}`
              : document.document_type}
        </p>
      </header>

      {status === 'loading' && (
        <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-10 text-center text-body-md text-on-surface-variant">
          Loading pages…
        </div>
      )}

      {status === 'error' && (
        <div
          role="alert"
          className="rounded-2xl border border-error/30 bg-error-container/60 p-10 text-center text-body-md text-on-error-container"
        >
          Could not load the extracted pages. Check that the backend is running
          and try again.
        </div>
      )}

      {status === 'ready' && pages.length === 0 && (
        <div className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-10 text-center">
          <p className="text-headline-md text-on-surface">No pages extracted</p>
          <p className="mt-2 text-body-md text-on-surface-variant/70">
            This document has no stored page content yet. Try reprocessing it.
          </p>
        </div>
      )}

      {status === 'ready' && pages.length > 0 && (
        <ol className="space-y-4">
          {pages.map((page) => (
            <li
              key={page.page_number}
              className="overflow-hidden rounded-2xl border border-outline-variant bg-surface-container-lowest"
            >
              <div className="flex items-center justify-between border-b border-outline-variant/60 bg-surface-container-low px-6 py-3">
                <span className="text-label-lg font-semibold uppercase tracking-wider text-on-surface-variant">
                  Page {page.page_number}
                </span>
                <span className="rounded-lg bg-secondary-container px-2.5 py-1 text-label-sm font-semibold text-on-secondary-container">
                  {page.extraction_method}
                </span>
              </div>
              <div className="px-6 py-5">
                {page.cleaned_text ? (
                  <p className="whitespace-pre-wrap text-body-md leading-relaxed text-on-surface">
                    {page.cleaned_text}
                  </p>
                ) : (
                  <p className="text-body-md italic text-on-surface-variant/70">
                    No readable text on this page (e.g. scanned image).
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
