import { Building2, FileText, LayoutDashboard, Settings } from 'lucide-react'

export type NavItemId = 'dashboard' | 'documents' | 'companies' | 'settings'

export type NavItem = {
  id: NavItemId
  label: string
  icon: typeof LayoutDashboard
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'companies', label: 'Companies', icon: Building2 },
  { id: 'settings', label: 'Settings', icon: Settings },
]
