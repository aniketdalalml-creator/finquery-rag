import { AuthProvider, useAuth } from '../auth/AuthContext'
import { AuthScreen } from '../features/auth/AuthScreen'
import { DashboardPage } from '../features/dashboard'

function AppShell() {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <AuthScreen />
  }
  return <DashboardPage />
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}
