'use client'
import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'

const MODALITIES = [
  { key: 'academia',  label: 'Academia',  emoji: '💪' },
  { key: 'corrida',   label: 'Corrida',   emoji: '🏃' },
  { key: 'crossfit',  label: 'Crossfit',  emoji: '🏋️' },
  { key: 'ciclismo',  label: 'Ciclismo',  emoji: '🚴' },
  { key: 'tenis',     label: 'Tênis',     emoji: '🎾' },
  { key: 'pilates',   label: 'Pilates',   emoji: '🧘' },
  { key: 'surfe',     label: 'Surfe',     emoji: '🏄' },
  { key: 'yoga',      label: 'Yoga',      emoji: '🌿' },
]

export default function SettingsPage() {
  const { setProfile, userId } = useAuthStore()
  const qc = useQueryClient()

  const { data: profile } = useQuery({
    queryKey: ['profile-me', userId],
    enabled: !!userId,
    queryFn: async () => {
      const { data } = await api.get('/users/me')
      return data
    },
  })

  const [gender, setGender] = useState<string>('')
  const [modalities, setModalities] = useState<string[]>([])
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (profile) {
      setGender(profile.gender ?? '')
      setModalities(profile.preferred_modalities ?? [])
    }
  }, [profile])

  const save = useMutation({
    mutationFn: async () => {
      const { data } = await api.patch('/users/me', {
        gender: gender || null,
        preferred_modalities: modalities,
      })
      return data
    },
    onSuccess: (data) => {
      setProfile({ gender: data.gender, preferredModalities: data.preferred_modalities ?? [] })
      qc.invalidateQueries({ queryKey: ['profile-me'] })
      qc.invalidateQueries({ queryKey: ['modality-readiness'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  function toggleModality(key: string) {
    setModalities((prev) =>
      prev.includes(key) ? prev.filter((m) => m !== key) : [...prev, key]
    )
  }

  return (
    <AppShell>
      <div className="p-8 space-y-8 max-w-2xl">
        <div>
          <h1 className="text-3xl font-black text-text">Perfil</h1>
          <p className="text-muted text-sm mt-1">Configure suas preferências pessoais</p>
        </div>

        {/* Gênero */}
        <div className="bg-surface rounded-2xl p-6 space-y-4">
          <h2 className="font-bold text-text">Sexo biológico</h2>
          <p className="text-xs text-muted">Usado para exibir a silhueta correta no Body Map</p>
          <div className="flex gap-3">
            {[
              { key: 'male',   label: 'Masculino', emoji: '♂' },
              { key: 'female', label: 'Feminino',  emoji: '♀' },
            ].map((g) => (
              <button
                key={g.key}
                onClick={() => setGender(g.key)}
                className="flex-1 py-4 rounded-xl border-2 text-sm font-bold transition-all flex flex-col items-center gap-1"
                style={{
                  borderColor: gender === g.key ? '#3b82f6' : '#334155',
                  backgroundColor: gender === g.key ? '#3b82f615' : 'transparent',
                  color: gender === g.key ? '#3b82f6' : '#64748b',
                }}
              >
                <span className="text-2xl">{g.emoji}</span>
                {g.label}
              </button>
            ))}
          </div>
        </div>

        {/* Modalidades */}
        <div className="bg-surface rounded-2xl p-6 space-y-4">
          <div>
            <h2 className="font-bold text-text">Modalidades que você pratica</h2>
            <p className="text-xs text-muted mt-1">
              Somente as selecionadas aparecerão na página de Modalidades
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {MODALITIES.map((m) => {
              const sel = modalities.includes(m.key)
              return (
                <button
                  key={m.key}
                  onClick={() => toggleModality(m.key)}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl border-2 text-sm font-medium transition-all text-left"
                  style={{
                    borderColor: sel ? '#3b82f6' : '#334155',
                    backgroundColor: sel ? '#3b82f615' : 'transparent',
                    color: sel ? '#3b82f6' : '#94a3b8',
                  }}
                >
                  <span className="text-xl">{m.emoji}</span>
                  <span>{m.label}</span>
                  {sel && <span className="ml-auto text-xs">✓</span>}
                </button>
              )
            })}
          </div>
          {modalities.length === 0 && (
            <p className="text-xs text-yellow-400">
              Nenhuma selecionada — todas as modalidades serão exibidas.
            </p>
          )}
        </div>

        {saved && (
          <p className="text-green-400 text-sm font-medium">Perfil atualizado com sucesso!</p>
        )}

        <button
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="bg-brand hover:bg-blue-500 disabled:opacity-60 text-white font-bold py-3 px-8 rounded-xl transition-colors"
        >
          {save.isPending ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </AppShell>
  )
}
