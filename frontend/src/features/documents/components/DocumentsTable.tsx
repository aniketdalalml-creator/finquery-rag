import { StatusBadge } from './StatusBadge'
import type { DocumentListItem } from '../../../types/api'
import type { ListStatus } from '../../../hooks/useDocuments'

function formatDate(value: string | null): string {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

type DocumentsTableProps = {
  status: ListStatus
  documents: DocumentListItem[]
}

export function DocumentsTable({ status, documents }: DocumentsTableProps) {
  if (status === 'loading') {
    return (
      <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-10 text-center text-body-md text-on-surface-variant">
        Loading documents…
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div
        role="alert"
        className="rounded-2xl border border-error/30 bg-error-container/60 p-10 text-center text-body-md text-on-error-container"
      >
        Could not load documents. Check that the backend is running and try
        again.
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-10 text-center">
        <p className="text-headline-md text-on-surface">No documents yet</p>
        <p className="mt-2 text-body-md text-on-surface-variant/70">
          Upload your first PDF above to get started.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-outline-variant bg-surface-container-lowest">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-outline-variant bg-surface-container-low">
            {['Document', 'Company', 'Type', 'Filing date', 'Uploaded', 'Status'].map(
              (heading, index) => (
                <th
                  key={heading}
                  className={`px-6 py-3 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant ${
                    index === 5 ? 'text-right' : ''
                  }`}
                >
                  {heading}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr
              key={doc.id}
              className="border-b border-outline-variant/60 last:border-b-0 hover:bg-surface-container-low"
            >
              <td className="px-6 py-4">
                <span className="text-body-md font-medium text-on-surface">
                  {doc.title}
                </span>
                <span className="ml-2 text-label-sm tabular-nums text-on-surface-variant/60">
                  #{doc.id}
                </span>
              </td>
              <td className="px-6 py-4 text-body-md text-on-surface-variant">
                {doc.company_name ?? '—'}
              </td>
              <td className="px-6 py-4">
                <span className="rounded-lg bg-secondary-container px-2.5 py-1 text-label-sm font-semibold text-on-secondary-container">
                  {doc.document_type}
                </span>
              </td>
              <td className="px-6 py-4 text-data-tabular text-on-surface-variant">
                {formatDate(doc.filing_date)}
              </td>
              <td className="px-6 py-4 text-data-tabular text-on-surface-variant">
                {formatDate(doc.created_at)}
              </td>
              <td className="px-6 py-4 text-right">
                <StatusBadge status={doc.processing_status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
