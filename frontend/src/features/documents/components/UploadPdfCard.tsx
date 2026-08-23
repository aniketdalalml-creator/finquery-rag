import { useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { CheckCircle2, FileUp, Loader2, TriangleAlert } from 'lucide-react'
import { uploadDocument } from '../../../services/api'
import type { UploadedDocument } from '../../../types/api'
import { useCompanies } from '../../../hooks/useCompanies'

type UploadState =
  | { kind: 'idle' }
  | { kind: 'uploading' }
  | { kind: 'success'; document: UploadedDocument; filename: string }
  | { kind: 'error'; message: string }

function isPdf(file: File): boolean {
  return (
    file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
  )
}

type UploadPdfCardProps = {
  onSuccess?: (document: UploadedDocument) => void
}

export function UploadPdfCard({ onSuccess }: UploadPdfCardProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selected, setSelected] = useState<File | null>(null)
  const [companyId, setCompanyId] = useState<string>('')
  const [state, setState] = useState<UploadState>({ kind: 'idle' })
  const { companies, loading: companiesLoading } = useCompanies()

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    setState({ kind: 'idle' })
    if (file && !isPdf(file)) {
      setSelected(null)
      setState({
        kind: 'error',
        message: `"${file.name}" is not a PDF. Please choose a .pdf file.`,
      })
      return
    }
    setSelected(file)
  }

  function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) return
    setState({ kind: 'uploading' })
    uploadDocument(selected, {
      companyId: companyId ? Number(companyId) : null,
      documentType: '10-K',
    })
      .then((document) => {
        setState({ kind: 'success', document, filename: selected.name })
        setSelected(null)
        if (inputRef.current) inputRef.current.value = ''
        onSuccess?.(document)
      })
      .catch((err: Error) => {
        setState({ kind: 'error', message: err.message })
      })
  }

  const busy = state.kind === 'uploading'

  return (
    <form
      onSubmit={handleUpload}
      className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6"
    >
      <h3 className="text-headline-md tracking-tight text-on-surface">
        Upload PDF
      </h3>
      <p className="mt-1 text-body-md text-on-surface-variant/80">
        Add a filing to the library. Processing runs separately.
      </p>

      <div className="mt-5 flex flex-wrap items-center gap-4">
        <input
          ref={inputRef}
          id="pdf-upload-input"
          type="file"
          accept="application/pdf,.pdf"
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          type="button"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
          className="flex items-center gap-2 rounded-xl border border-outline-variant bg-surface-container-low px-5 py-3 text-body-md font-semibold text-on-surface transition-colors hover:bg-surface-container-high disabled:opacity-50"
        >
          <FileUp size={18} strokeWidth={2.25} />
          Choose PDF
        </button>
        <span className="text-body-md text-on-surface-variant">
          {selected ? selected.name : 'No file selected'}
        </span>

        <label htmlFor="upload-company" className="sr-only">
          Company
        </label>
        <select
          id="upload-company"
          value={companyId}
          onChange={(event) => setCompanyId(event.target.value)}
          disabled={busy || companiesLoading}
          className="ml-auto rounded-xl border border-outline-variant bg-surface-container-low px-4 py-3 text-body-md text-on-surface focus:border-primary focus:outline-none"
        >
          <option value="">
            {companiesLoading ? 'Loading companies…' : 'No company (optional)'}
          </option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.display_name ?? company.legal_name}
              {company.ticker ? ` (${company.ticker})` : ''}
            </option>
          ))}
        </select>

        <button
          type="submit"
          disabled={!selected || busy}
          className="flex items-center gap-2 rounded-xl bg-[#006d38] px-6 py-3 text-body-md font-semibold text-on-primary transition-colors hover:bg-[#005c2f] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy && <Loader2 size={16} className="animate-spin" />}
          {busy ? 'Uploading…' : 'Upload'}
        </button>
      </div>

      {state.kind === 'success' && (
        <div
          role="status"
          className="mt-5 flex items-start gap-3 rounded-xl border border-outline-variant bg-primary-container/40 px-5 py-4 text-body-md text-on-surface"
        >
          <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-[#00a344]" />
          <span>
            Uploaded successfully — Document ID{' '}
            <strong className="tabular-nums">{state.document.id}</strong>, file{' '}
            <strong>{state.filename}</strong>, status{' '}
            <strong>{state.document.processing_status}</strong>.
          </span>
        </div>
      )}

      {state.kind === 'error' && (
        <div
          role="alert"
          className="mt-5 flex items-start gap-3 rounded-xl border border-error/30 bg-error-container/60 px-5 py-4 text-body-md text-on-error-container"
        >
          <TriangleAlert size={20} className="mt-0.5 shrink-0" />
          <span>{state.message}</span>
        </div>
      )}
    </form>
  )
}
