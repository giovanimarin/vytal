'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'

export default function LoginPage() {
  const router = useRouter()
  const { setAuth, setProfile } = useAuthStore()
  const [email, setEmail] = useState('demo@vytal.app')
  const [password, setPassword] = useState('demo1234')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [seeding, setSeeding] = useState(false)

  async function handleSeed() {
    setSeeding(true)
    setError('')
    try {
      const { data } = await api.post('/dev/seed')
      setEmail(data.email)
      setPassword(data.password)
      setAuth(data.user_id, data.email, 'Demo User', data.access_token)
      // load profile fields after auth token is set
      try {
        const { data: me } = await api.get('/users/me', { headers: { Authorization: `Bearer ${data.access_token}` } })
        setProfile({ gender: me.gender, preferredModalities: me.preferred_modalities ?? [] })
      } catch {}
      router.replace('/dashboard')
    } catch {
      setError('Falha ao criar dados demo. O backend está rodando?')
    } finally {
      setSeeding(false)
    }
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/auth/login', { email, password })
      setAuth(data.user_id, data.email, data.name || 'Usuário', data.access_token)
      try {
        const { data: me } = await api.get('/users/me', { headers: { Authorization: `Bearer ${data.access_token}` } })
        setProfile({ gender: me.gender, preferredModalities: me.preferred_modalities ?? [] })
      } catch {}
      router.replace('/dashboard')
    } catch {
      setError('Email ou senha inválidos.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="text-center space-y-1">
          <h1 className="text-4xl font-black text-text">Vytal</h1>
          <p className="text-muted text-sm">Health Analytics</p>
        </div>

        {/* Demo card */}
        <div className="bg-surface border border-brand/40 rounded-2xl p-5 space-y-3">
          <p className="text-sm font-semibold text-brand">Modo Demo</p>
          <p className="text-xs text-sub leading-relaxed">
            Clique abaixo para criar dados mockados de 14 dias e entrar automaticamente. Ideal para explorar todas as funcionalidades.
          </p>
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="w-full bg-brand hover:bg-blue-500 disabled:opacity-60 text-white font-bold py-3 rounded-xl transition-colors text-sm"
          >
            {seeding ? 'Gerando dados...' : '🚀 Entrar com dados demo'}
          </button>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs text-muted">ou entre com sua conta</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-surface border border-border rounded-xl px-4 py-3 text-text placeholder-muted focus:outline-none focus:border-brand text-sm"
            required
          />
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-surface border border-border rounded-xl px-4 py-3 text-text placeholder-muted focus:outline-none focus:border-brand text-sm"
            required
          />
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-surface hover:bg-border border border-border disabled:opacity-60 text-text font-bold py-3 rounded-xl transition-colors text-sm"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
