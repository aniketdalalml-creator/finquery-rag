import { useEffect, useState, type FormEvent } from 'react'
import {
  createCompany,
  listCompanies,
  updateCompany,
} from '../../services/api'
import type { Company } from '../../types/api'

const EMPTY_FORM = {
  legal_name: '',
  display_name: '',
  ticker: '',
  exchange: '',
  country: '',
  industry: '',
  sector: '',
}

type EditDraft = {
  display_name: string
  country: string
  industry: string
  sector: string
}

function dash(value: string | null | undefined): string {
  return value?.trim() ? value : '—'
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [search, setSearch] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [listError, setListError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null)
  const [savingId, setSavingId] = useState<number | null>(null)

  async function loadCompanies(query?: string) {
    setStatus('loading')
    setListError(null)
    try {
      const items = await listCompanies(query)
      setCompanies(items)
      setStatus('ready')
    } catch (err) {
      setStatus('error')
      setListError(err instanceof Error ? err.message : 'Could not load companies.')
    }
  }

  useEffect(() => {
    void loadCompanies()
  }, [])

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await loadCompanies(search)
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await createCompany({
        legal_name: form.legal_name.trim(),
        display_name: form.display_name.trim() || null,
        ticker: form.ticker.trim() || null,
        exchange: form.exchange.trim() || null,
        country: form.country.trim().toUpperCase() || null,
        industry: form.industry.trim() || null,
        sector: form.sector.trim() || null,
      })
      setForm(EMPTY_FORM)
      await loadCompanies(search)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not create company.')
    } finally {
      setSubmitting(false)
    }
  }

  function startEdit(company: Company) {
    setEditingId(company.id)
    setEditDraft({
      display_name: company.display_name ?? '',
      country: company.country ?? '',
      industry: company.industry ?? '',
      sector: company.sector ?? '',
    })
    setFormError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setEditDraft(null)
  }

  async function saveEdit(companyId: number) {
    if (!editDraft) return
    setSavingId(companyId)
    setFormError(null)
    try {
      await updateCompany(companyId, {
        display_name: editDraft.display_name.trim() || null,
        country: editDraft.country.trim().toUpperCase() || null,
        industry: editDraft.industry.trim() || null,
        sector: editDraft.sector.trim() || null,
      })
      cancelEdit()
      await loadCompanies(search)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not update company.')
    } finally {
      setSavingId(null)
    }
  }

  const inputClass =
    'mt-2 w-full rounded-xl border border-outline-variant bg-surface px-4 py-2.5 text-body-md text-on-surface placeholder:text-on-surface-variant/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30'

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <h1 className="text-display-lg tracking-tight text-on-surface">Companies</h1>
        <p className="mt-3 max-w-2xl text-body-lg text-on-surface-variant">
          Manage company master data used when uploading and organizing filings.
        </p>
      </div>

      {(formError || listError) && (
        <div
          role="alert"
          className="rounded-xl border border-error/30 bg-error-container/60 px-5 py-4 text-body-md text-on-error-container"
        >
          {formError ?? listError}
        </div>
      )}

      <form
        onSubmit={handleCreate}
        className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6"
      >
        <h2 className="text-headline-md tracking-tight text-on-surface">Add company</h2>
        <p className="mt-1 text-body-md text-on-surface-variant/80">
          Legal name is required. Ticker and country are optional.
        </p>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label htmlFor="company-legal-name" className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              Legal name
            </label>
            <input
              id="company-legal-name"
              required
              value={form.legal_name}
              onChange={(e) => setForm((f) => ({ ...f, legal_name: e.target.value }))}
              className={inputClass}
              placeholder="Apple Inc."
            />
          </div>
          <div>
            <label htmlFor="company-display-name" className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              Display name
            </label>
            <input
              id="company-display-name"
              value={form.display_name}
              onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
              className={inputClass}
              placeholder="Apple"
            />
          </div>
          <div>
            <label htmlFor="company-ticker" className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              Ticker
            </label>
            <input
              id="company-ticker"
              value={form.ticker}
              onChange={(e) => setForm((f) => ({ ...f, ticker: e.target.value }))}
              className={inputClass}
              placeholder="AAPL"
              pattern="[A-Za-z0-9.\-]{1,32}"
              title="Letters, numbers, dots, or hyphens"
            />
          </div>
          <div>
            <label htmlFor="company-exchange" className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              Exchange
            </label>
            <input
              id="company-exchange"
              value={form.exchange}
              onChange={(e) => setForm((f) => ({ ...f, exchange: e.target.value }))}
              className={inputClass}
              placeholder="NASDAQ"
            />
          </div>
          <div>
            <label htmlFor="company-country" className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              Country (ISO-2)
            </label>
            <input
              id="company-country"
              value={form.country}
              onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
              className={inputClass}
              placeholder="US"
              maxLength={2}
            />
          </div>
          <div>
            <label htmlFor="company-industry" className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              Industry
            </label>
            <input
              id="company-industry"
              value={form.industry}
              onChange={(e) => setForm((f) => ({ ...f, industry: e.target.value }))}
              className={inputClass}
              placeholder="Consumer Electronics"
            />
          </div>
          <div>
            <label htmlFor="company-sector" className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
              Sector
            </label>
            <input
              id="company-sector"
              value={form.sector}
              onChange={(e) => setForm((f) => ({ ...f, sector: e.target.value }))}
              className={inputClass}
              placeholder="Technology"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting || !form.legal_name.trim()}
          className="mt-6 rounded-xl bg-[#006d38] px-8 py-3 text-body-md font-semibold text-on-primary transition-colors hover:bg-[#005c2f] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? 'Saving…' : 'Create company'}
        </button>
      </form>

      <section aria-label="Company library">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <h2 className="text-headline-md tracking-tight text-on-surface">Company library</h2>
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name or ticker"
              className="w-full min-w-[14rem] rounded-xl border border-outline-variant bg-surface-container-lowest px-4 py-2.5 text-body-md text-on-surface placeholder:text-on-surface-variant/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30 sm:w-64"
            />
            <button
              type="submit"
              className="rounded-xl border border-outline-variant px-4 py-2.5 text-label-sm font-semibold text-on-surface-variant hover:bg-surface-container-low"
            >
              Search
            </button>
          </form>
        </div>

        <div className="mt-4">
          {status === 'loading' ? (
            <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-10 text-center text-body-md text-on-surface-variant">
              Loading companies…
            </div>
          ) : status === 'error' ? (
            <div
              role="alert"
              className="rounded-2xl border border-error/30 bg-error-container/60 p-10 text-center text-body-md text-on-error-container"
            >
              Could not load companies. Check that the backend is running.
            </div>
          ) : companies.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-10 text-center">
              <p className="text-headline-md text-on-surface">No companies yet</p>
              <p className="mt-2 text-body-md text-on-surface-variant/70">
                Create your first company above to use it when uploading PDFs.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-outline-variant bg-surface-container-lowest">
              <table className="w-full min-w-[48rem] text-left">
                <thead>
                  <tr className="border-b border-outline-variant bg-surface-container-low">
                    {['Company', 'Ticker', 'Exchange', 'Country', 'Industry', 'Sector', ''].map(
                      (heading) => (
                        <th
                          key={heading || 'actions'}
                          className="px-5 py-3 text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant"
                        >
                          {heading}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => {
                    const editing = editingId === company.id && editDraft
                    return (
                      <tr
                        key={company.id}
                        className="border-b border-outline-variant/60 last:border-b-0"
                      >
                        <td className="px-5 py-4">
                          <p className="text-body-md font-medium text-on-surface">
                            {editing ? (
                              <input
                                value={editDraft.display_name}
                                onChange={(e) =>
                                  setEditDraft({ ...editDraft, display_name: e.target.value })
                                }
                                className="w-full rounded-lg border border-outline-variant bg-surface px-3 py-1.5 text-body-md"
                                placeholder="Display name"
                              />
                            ) : (
                              company.display_name || company.legal_name
                            )}
                          </p>
                          {!editing && (
                            <p className="mt-0.5 text-label-sm text-on-surface-variant/70">
                              {company.legal_name}
                            </p>
                          )}
                        </td>
                        <td className="px-5 py-4 text-data-tabular text-on-surface-variant">
                          {dash(company.ticker)}
                        </td>
                        <td className="px-5 py-4 text-body-md text-on-surface-variant">
                          {dash(company.exchange)}
                        </td>
                        <td className="px-5 py-4 text-body-md text-on-surface-variant">
                          {editing ? (
                            <input
                              value={editDraft.country}
                              onChange={(e) =>
                                setEditDraft({ ...editDraft, country: e.target.value })
                              }
                              className="w-16 rounded-lg border border-outline-variant bg-surface px-2 py-1.5 text-body-md"
                              maxLength={2}
                              placeholder="US"
                            />
                          ) : (
                            dash(company.country)
                          )}
                        </td>
                        <td className="px-5 py-4 text-body-md text-on-surface-variant">
                          {editing ? (
                            <input
                              value={editDraft.industry}
                              onChange={(e) =>
                                setEditDraft({ ...editDraft, industry: e.target.value })
                              }
                              className="w-full rounded-lg border border-outline-variant bg-surface px-2 py-1.5 text-body-md"
                            />
                          ) : (
                            dash(company.industry)
                          )}
                        </td>
                        <td className="px-5 py-4 text-body-md text-on-surface-variant">
                          {editing ? (
                            <input
                              value={editDraft.sector}
                              onChange={(e) =>
                                setEditDraft({ ...editDraft, sector: e.target.value })
                              }
                              className="w-full rounded-lg border border-outline-variant bg-surface px-2 py-1.5 text-body-md"
                            />
                          ) : (
                            dash(company.sector)
                          )}
                        </td>
                        <td className="px-5 py-4 text-right">
                          {editing ? (
                            <div className="flex justify-end gap-2">
                              <button
                                type="button"
                                disabled={savingId === company.id}
                                onClick={() => void saveEdit(company.id)}
                                className="rounded-lg bg-[#006d38] px-3 py-1.5 text-label-sm font-semibold text-on-primary disabled:opacity-50"
                              >
                                {savingId === company.id ? 'Saving…' : 'Save'}
                              </button>
                              <button
                                type="button"
                                onClick={cancelEdit}
                                className="rounded-lg border border-outline-variant px-3 py-1.5 text-label-sm font-semibold text-on-surface-variant"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() => startEdit(company)}
                              className="rounded-lg border border-outline-variant px-3 py-1.5 text-label-sm font-semibold text-on-surface-variant hover:bg-surface-container-low"
                            >
                              Edit
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
