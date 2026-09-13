import { useState, type FormEvent } from 'react'
import { AlertCircle, BarChart3, Building2, Eye, EyeOff, Lock, Mail, Shield } from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'
import { Logo } from '../../shared/components/Logo'

type Mode = 'login' | 'register'

export function AuthScreen() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const isLogin = mode === 'login'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (isLogin) {
        await login(email.trim(), password)
      } else {
        await register(email.trim(), password)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center overflow-y-auto bg-background px-4 py-8 text-on-surface antialiased">
      <div className="relative w-full max-w-6xl">
        <div className="pointer-events-none absolute -left-12 -top-16 -z-10 h-96 w-96 rounded-full bg-primary-container/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -right-12 -z-10 h-96 w-96 rounded-full bg-tertiary-fixed-dim/15 blur-3xl" />

        <div className="grid grid-cols-1 items-stretch gap-5 lg:grid-cols-12">
          <div className="relative flex flex-col justify-between overflow-hidden rounded-xl bg-inverse-surface p-8 text-inverse-on-surface shadow-xl lg:col-span-5">
            <div className="pointer-events-none absolute -bottom-12 -right-12 h-64 w-64 rounded-full bg-primary-container/20 blur-2xl" />
            <div className="relative z-10 flex flex-col gap-6">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary shadow-md">
                    <Logo size={28} />
                  </div>
                  <span className="text-headline-lg tracking-tight text-surface-container-lowest">
                    FinanceIQ
                  </span>
                </div>
                <div className="flex items-center gap-1.5 rounded-full bg-surface-container-highest/20 px-2.5 py-1 text-label-sm text-tertiary-fixed">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-tertiary-fixed" />
                  Filing Copilot
                </div>
              </div>

              <div className="mt-2 flex flex-col gap-1">
                <span className="text-label-sm uppercase tracking-wider text-tertiary-fixed">
                  Securities &amp; Exchange Filing Copilot
                </span>
                <h1 className="text-display-md font-bold text-surface-container-lowest">
                  Institutional Financial Intelligence
                </h1>
                <p className="mt-2 text-body-md leading-relaxed text-secondary-fixed-dim">
                  Ask natural-language questions across verified 10-K, 10-Q, and
                  earnings transcripts with page-level citations.
                </p>
              </div>

              <div className="mt-2 rounded-lg bg-inverse-surface/80 p-4 shadow-sm">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-caption text-secondary-fixed-dim">
                    Sample citation · Filing excerpt
                  </span>
                  <span className="rounded-full bg-tertiary-container/30 px-2 py-0.5 text-caption text-tertiary-fixed">
                    Verified
                  </span>
                </div>
                <p className="text-body-md italic text-surface-container-lowest">
                  &ldquo;Data Center revenue surged 112% YoY, primarily driven by
                  platform shipments…&rdquo;
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-primary/20 px-2 py-0.5 text-label-sm text-tertiary-fixed">
                    Doc: 10-Q
                  </span>
                  <span className="rounded-full bg-primary/20 px-2 py-0.5 text-label-sm text-tertiary-fixed">
                    Item 2 · P.34
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <div className="rounded-lg bg-surface-container-highest/10 p-3">
                  <div className="flex items-center gap-2 text-surface-container-lowest">
                    <BarChart3 size={16} />
                    <span className="text-metric-numeral">Cited</span>
                  </div>
                  <div className="text-caption text-secondary-fixed-dim">
                    Page-level sources
                  </div>
                </div>
                <div className="rounded-lg bg-surface-container-highest/10 p-3">
                  <div className="flex items-center gap-2 text-surface-container-lowest">
                    <Building2 size={16} />
                    <span className="text-metric-numeral">Private</span>
                  </div>
                  <div className="text-caption text-secondary-fixed-dim">
                    Per-user library
                  </div>
                </div>
              </div>
            </div>

            <div className="relative z-10 mt-8 flex items-start gap-2 pt-4 text-caption text-secondary-fixed-dim">
              <Shield size={18} className="mt-0.5 shrink-0 text-tertiary-fixed" />
              <p>
                Multi-tenant isolation. Your filings and queries stay scoped to
                your workspace.
              </p>
            </div>
          </div>

          <div className="flex flex-col justify-between rounded-xl bg-surface-container-lowest p-8 shadow-xl lg:col-span-7">
            <div>
              <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <h2 className="text-headline-lg text-on-surface">
                    {isLogin ? 'Sign in to Workspace' : 'Create Account'}
                  </h2>
                  <p className="mt-0.5 text-body-md text-secondary">
                    {isLogin
                      ? 'Enter credentials to access your research terminal.'
                      : 'Register with email and a password of at least 8 characters.'}
                  </p>
                </div>
                <div className="flex shrink-0 rounded-full bg-surface-container p-1 shadow-inner">
                  <button
                    type="button"
                    onClick={() => {
                      setMode('login')
                      setError(null)
                    }}
                    className={`rounded-full px-4 py-1.5 text-label-md transition-all ${
                      isLogin
                        ? 'bg-surface-container-lowest text-on-surface shadow-sm'
                        : 'text-secondary hover:text-on-surface'
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setMode('register')
                      setError(null)
                    }}
                    className={`rounded-full px-4 py-1.5 text-label-md transition-all ${
                      !isLogin
                        ? 'bg-surface-container-lowest text-on-surface shadow-sm'
                        : 'text-secondary hover:text-on-surface'
                    }`}
                  >
                    Create Account
                  </button>
                </div>
              </div>

              {error && (
                <div
                  role="alert"
                  className="mb-4 flex items-start gap-2 rounded-lg bg-error-container/40 p-4 text-on-error-container"
                >
                  <AlertCircle size={20} className="mt-0.5 shrink-0 text-error" />
                  <div>
                    <div className="text-title-md font-semibold text-error">
                      Authentication Notice
                    </div>
                    <div className="text-body-md">{error}</div>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label
                    htmlFor="auth-email"
                    className="flex items-center justify-between text-label-md text-on-surface"
                  >
                    <span>Corporate Email</span>
                  </label>
                  <div className="relative flex items-center">
                    <Mail
                      size={18}
                      className="pointer-events-none absolute left-3 text-secondary"
                    />
                    <input
                      id="auth-email"
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      className="w-full rounded-lg bg-surface-container-low py-2.5 pl-10 pr-3 text-body-md text-on-surface placeholder:text-secondary/60 transition-all focus:bg-surface-container-lowest focus:outline-none focus:shadow-[0_0_0_2px_#2563eb]"
                      placeholder="analyst@firm.com"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label
                    htmlFor="auth-password"
                    className="text-label-md text-on-surface"
                  >
                    Master Password
                  </label>
                  <div className="relative flex items-center">
                    <Lock
                      size={18}
                      className="pointer-events-none absolute left-3 text-secondary"
                    />
                    <input
                      id="auth-password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete={isLogin ? 'current-password' : 'new-password'}
                      required
                      minLength={8}
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      className="w-full rounded-lg bg-surface-container-low py-2.5 pl-10 pr-10 text-body-md text-on-surface placeholder:text-secondary/60 transition-all focus:bg-surface-container-lowest focus:outline-none focus:shadow-[0_0_0_2px_#2563eb]"
                      placeholder="••••••••••••••••"
                    />
                    <button
                      type="button"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute right-3 p-1 text-secondary transition-colors hover:text-on-surface"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="mt-2 w-full rounded-xl bg-primary px-8 py-3 text-body-md font-semibold text-on-primary shadow-md transition-all hover:bg-primary-container disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting
                    ? isLogin
                      ? 'Signing in…'
                      : 'Creating account…'
                    : isLogin
                      ? 'Sign in'
                      : 'Create account'}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
