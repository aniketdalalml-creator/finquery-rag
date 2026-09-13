import {
  Building2,
  FileText,
  LayoutDashboard,
  MessageSquare,
  Settings,
} from 'lucide-react'

export type NavItemId =
  | 'dashboard'
  | 'documents'
  | 'companies'
  | 'chat'
  | 'settings'

export type NavItem = {
  id: NavItemId
  label: string
  icon: typeof LayoutDashboard
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'companies', label: 'Companies', icon: Building2 },
  { id: 'chat', label: 'Chat / Ask', icon: MessageSquare },
  { id: 'settings', label: 'Settings', icon: Settings },
]

export const PAGE_TITLES: Record<NavItemId, string> = {
  dashboard: 'Overview',
  documents: 'Filings & Transcripts',
  companies: 'Companies',
  chat: 'Synthesis Lab',
  settings: 'Settings',
}
