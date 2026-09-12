import { useState, type FormEvent } from 'react'
import { useAuth } from '../../auth/AuthContext'

type Mode = 'login' | 'register'

export function AuthScreen() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
    <div className="flex min-h-screen items-center justify-center bg-surface px-6">
      <div className="w-full max-w-md rounded-2xl border border-outline-variant bg-surface-container-lowest p-8 shadow-sm">
        <p className="text-label-sm font-semibold uppercase tracking-wider text-outline">
          FinanceIQ
        </p>
        <h1 className="mt-2 text-headline-lg tracking-tight text-on-surface">
          {isLogin ? 'Sign in' : 'Create an account'}
        </h1>
        <p className="mt-2 text-body-md text-on-surface-variant">
          {isLogin
            ? 'Use your email and password to open the dashboard.'
            : 'Register with an email and a password of at least 8 characters.'}
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label
              htmlFor="auth-email"
              className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant"
            >
              Email
            </label>
            <input
              id="auth-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-body-md text-on-surface placeholder:text-on-surface-variant/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label
              htmlFor="auth-password"
              className="text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant"
            >
              Password
            </label>
            <input
              id="auth-password"
              type="password"
              autoComplete={isLogin ? 'current-password' : 'new-password'}
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-body-md text-on-surface placeholder:text-on-surface-variant/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p role="alert" className="text-body-md text-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-[#006d38] px-8 py-3 text-body-md font-semibold text-on-primary transition-colors hover:bg-[#005c2f] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting
              ? isLogin
                ? 'Signing in…'
                : 'Creating account…'
              : isLogin
                ? 'Sign in'
                : 'Register'}
          </button>
        </form>

        <p className="mt-6 text-center text-body-md text-on-surface-variant">
          {isLogin ? 'Need an account?' : 'Already registered?'}{' '}
          <button
            type="button"
            className="font-semibold text-on-primary-container hover:underline"
            onClick={() => {
              setMode(isLogin ? 'register' : 'login')
              setError(null)
            }}
          >
            {isLogin ? 'Register' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  )
}
