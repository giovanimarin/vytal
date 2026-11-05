'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { logout } from '@/lib/auth'
import { useAuthStore } from '@/lib/store'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/dashboard',   label: 'Dashboard',    icon: '📊' },
  { href: '/modalities',  label: 'Modalidades',  icon: '🏅' },
  { href: '/body-map',    label: 'Body Map',     icon: '🦴' },
  { href: '/workouts',    label: 'Treinos',      icon: '💪' },
  { href: '/data',        label: 'Dados',        icon: '📈' },
  { href: '/settings',    label: 'Perfil',       icon: '⚙️' },
]

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { userId, email, name } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    const unsubscribe = useAuthStore.persist.onFinishHydration(() => setHydrated(true))
    if (useAuthStore.persist.hasHydrated()) setHydrated(true)
    return unsubscribe
  }, [])

  useEffect(() => {
    if (hydrated && !userId) router.replace('/login')
  }, [hydrated, userId, router])

  if (!hydrated || !userId) return null

  return (
    <div className="flex h-screen bg-bg overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-6 border-b border-border">
          <span className="text-2xl font-black text-text tracking-tight">Vytal</span>
          <p className="text-xs text-muted mt-1">Health Analytics</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors',
                pathname === item.href
                  ? 'bg-brand text-white'
                  : 'text-muted hover:bg-border hover:text-text'
              )}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-bg">
            <div className="w-8 h-8 rounded-full bg-brand flex items-center justify-center text-white text-sm font-bold">
              {(name || email || 'U')[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text truncate">{name || 'Usuário'}</p>
              <p className="text-xs text-muted truncate">{email}</p>
            </div>
            <button
              onClick={() => { logout(); router.replace('/login') }}
              className="text-muted hover:text-text text-xs"
              title="Sair"
            >
              ↩
            </button>
          </div>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
