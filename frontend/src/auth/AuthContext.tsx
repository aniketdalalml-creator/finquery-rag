import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { AuthUser, LoginResponse } from '../types/api'
import {
  login as loginRequest,
  register as registerRequest,
  setUnauthorizedHandler,
} from '../services/api'
import {
  clearSession,
  loadSession,
  saveSession,
  type AuthSession,
} from './session'

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  logout: () => void
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function persistFromLogin(body: LoginResponse): AuthSession {
  const session: AuthSession = { token: body.access_token, user: body.user }
  saveSession(session)
  return session
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(() => loadSession())

  const logout = useCallback(() => {
    clearSession()
    setSession(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearSession()
      setSession(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const body = await loginRequest(email, password)
    setSession(persistFromLogin(body))
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await registerRequest(email, password)
    const body = await loginRequest(email, password)
    setSession(persistFromLogin(body))
  }, [])

  const value = useMemo(
    () => ({
      user: session?.user ?? null,
      token: session?.token ?? null,
      isAuthenticated: Boolean(session?.token),
      logout,
      login,
      register,
    }),
    [session, logout, login, register],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
