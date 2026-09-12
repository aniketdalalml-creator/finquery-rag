import type { AuthUser } from '../types/api'

const STORAGE_KEY = 'financeiq_auth'

export type AuthSession = {
  token: string
  user: AuthUser
}

export function loadSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<AuthSession>
    if (typeof parsed.token !== 'string' || !parsed.user) return null
    if (typeof parsed.user.email !== 'string') return null
    return { token: parsed.token, user: parsed.user as AuthUser }
  } catch {
    return null
  }
}

export function saveSession(session: AuthSession): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export function clearSession(): void {
  localStorage.removeItem(STORAGE_KEY)
}

export function getStoredToken(): string | null {
  return loadSession()?.token ?? null
}
