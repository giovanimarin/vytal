'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { todayISO } from '@/lib/utils'

const MODALITIES = ['crossfit', 'corrida', 'academia', 'tenis', 'pilates', 'surfe', 'yoga', 'ciclismo']
const INTENSITIES = [
  { key: 'leve',     label: 'Leve',     color: '#4CAF50' },
  { key: 'moderado', label: 'Moderado', color: '#FFC107' },
  { key: 'intenso',  label: 'Intenso',  color: '#F44336' },
]
const MODALITY_EMOJI: Record<string, string> = {
  crossfit:'🏋️', corrida:'🏃', academia:'💪', tenis:'🎾',
  pilates:'🧘', surfe:'🏄', yoga:'🌿', ciclismo:'🚴',
}

export default function WorkoutsPage() {
  const { userId } = useAuthStore()
  const qc = useQueryClient()
  const today = todayISO()

  const [tab, setTab] = useState<'register' | 'history'>('register')
  const [modality, setModality] = useState('academia')
  const [intensity, setIntensity] = useState('moderado')
  const [duration, setDuration] = useState('45')
  const [notes, setNotes] = useState('')
  const [freeText, setFreeText] = useState('')
  const [selectedExercises, setSelectedExercises] = useState<string[]>([])
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const { data: catalog } = useQuery({
    queryKey: ['exercise-catalog'],
    queryFn: async () => {
      const { data } = await api.get('/workouts/exercises/catalog')
      return data as { name: string; primary: string[]; secondary: string[] }[]
    },
    staleTime: Infinity,
  })

  const start = new Date(Date.now() - 29 * 86400000).toISOString().split('T')[0]
  const { data: history } = useQuery({
    queryKey: ['workouts', userId, start, today],
    queryFn: async () => {
      const { data } = await api.get(`/workouts/${userId}?start_date=${start}&end_date=${today}`)
      return data as any[]
    },
    enabled: !!userId && tab === 'history',
  })

  const register = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/workouts', {
        user_id: userId,
        modality,
        intensity,
        duration_min: parseInt(duration),
        date: today,
        notes: notes || undefined,
        exercises: selectedExercises.map(name => ({ name })),
        free_text: freeText || undefined,
      })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['muscle-recovery', userId] })
      qc.invalidateQueries({ queryKey: ['muscle-suggestion', userId] })
      qc.invalidateQueries({ queryKey: ['modality-readiness', userId] })
      qc.invalidateQueries({ queryKey: ['workouts', userId] })
      setSuccess('Treino registrado! Recuperação muscular atualizada.')
      setNotes(''); setFreeText(''); setSelectedExercises([])
      setTimeout(() => setSuccess(''), 4000)
    },
    onError: () => setError('Falha ao registrar treino.'),
  })

  const showExercises = modality === 'academia' || modality === 'crossfit'

  return (
    <AppShell>
      <div className="p-8 space-y-6">
        <div>
          <h1 className="text-3xl font-black text-text">Treinos</h1>
          <p className="text-muted text-sm mt-1">Registre seus treinos e veja o histórico</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2">
          {[{key:'register', label:'Registrar'}, {key:'history', label:'Histórico'}].map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key as any)}
              className={`px-5 py-2 rounded-xl text-sm font-semibold transition-colors ${
                tab === t.key ? 'bg-brand text-white' : 'bg-surface text-muted hover:text-text'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'register' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-surface rounded-2xl p-6 space-y-6">
              {/* Modalidade */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-muted uppercase tracking-wide">Modalidade</label>
                <div className="flex flex-wrap gap-2">
                  {MODALITIES.map(m => (
                    <button
                      key={m}
                      onClick={() => setModality(m)}
                      className={`px-3 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-1.5 ${
                        modality === m ? 'bg-brand text-white' : 'bg-bg text-muted hover:text-text'
                      }`}
                    >
                      <span>{MODALITY_EMOJI[m]}</span>
                      <span className="capitalize">{m}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Intensidade */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-muted uppercase tracking-wide">Intensidade</label>
                <div className="flex gap-3">
                  {INTENSITIES.map(i => (
                    <button
                      key={i.key}
                      onClick={() => setIntensity(i.key)}
                      className="flex-1 py-2 rounded-xl text-sm font-bold border-2 transition-all"
                      style={{
                        borderColor: intensity === i.key ? i.color : '#334155',
                        color: intensity === i.key ? i.color : '#64748b',
                        backgroundColor: intensity === i.key ? i.color + '15' : 'transparent',
                      }}
                    >
                      {i.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Duração */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-muted uppercase tracking-wide">Duração (min)</label>
                <input
                  type="number"
                  value={duration}
                  onChange={e => setDuration(e.target.value)}
                  className="w-full bg-bg border border-border rounded-xl px-4 py-3 text-text focus:outline-none focus:border-brand"
                  min={1}
                />
              </div>

              {/* Notas */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-muted uppercase tracking-wide">Notas (opcional)</label>
                <textarea
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  rows={3}
                  placeholder="Como foi o treino?"
                  className="w-full bg-bg border border-border rounded-xl px-4 py-3 text-text placeholder-muted focus:outline-none focus:border-brand resize-none"
                />
              </div>

              {success && <p className="text-green-400 text-sm">{success}</p>}
              {error && <p className="text-red-400 text-sm">{error}</p>}

              <button
                onClick={() => register.mutate()}
                disabled={register.isPending || !duration}
                className="w-full bg-brand hover:bg-blue-500 disabled:opacity-60 text-white font-bold py-3 rounded-xl transition-colors"
              >
                {register.isPending ? 'Registrando...' : 'Registrar Treino'}
              </button>
            </div>

            {/* Exercícios */}
            {showExercises && (
              <div className="bg-surface rounded-2xl p-6 space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-bold text-text">Exercícios (opcional)</h3>
                  <p className="text-xs text-muted">Selecione para mapear grupos musculares precisamente</p>
                </div>

                <textarea
                  value={freeText}
                  onChange={e => setFreeText(e.target.value)}
                  rows={2}
                  placeholder="Ou descreva em texto livre: fiz supino, agachamento..."
                  className="w-full bg-bg border border-border rounded-xl px-4 py-3 text-text placeholder-muted focus:outline-none focus:border-brand resize-none text-sm"
                />

                <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
                  {(catalog ?? []).map((ex) => {
                    const sel = selectedExercises.includes(ex.name)
                    return (
                      <div
                        key={ex.name}
                        onClick={() => setSelectedExercises(prev =>
                          sel ? prev.filter(n => n !== ex.name) : [...prev, ex.name]
                        )}
                        className={`flex items-center gap-3 px-3 py-2 rounded-xl cursor-pointer transition-colors ${
                          sel ? 'bg-brand/20 border border-brand/40' : 'hover:bg-bg'
                        }`}
                      >
                        <div className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 ${
                          sel ? 'border-brand bg-brand' : 'border-border'
                        }`}>
                          {sel && <span className="text-white text-xs">✓</span>}
                        </div>
                        <div>
                          <p className={`text-sm ${sel ? 'text-brand' : 'text-sub'}`}>{ex.name}</p>
                          <p className="text-xs text-muted">{ex.primary.join(', ')}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {selectedExercises.length > 0 && (
                  <p className="text-xs text-brand">{selectedExercises.length} exercício(s) selecionado(s)</p>
                )}
              </div>
            )}
          </div>
        )}

        {tab === 'history' && (
          <div className="space-y-3">
            {!history?.length && (
              <div className="bg-surface rounded-2xl p-6 text-center text-muted">Nenhum treino nos últimos 30 dias.</div>
            )}
            {(history ?? []).map((w: any) => (
              <div key={w.workout_id} className="bg-surface rounded-2xl p-5 space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{MODALITY_EMOJI[w.modality] ?? '🏅'}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-text capitalize">{w.modality}</h3>
                      <span
                        className="text-xs font-bold px-2 py-0.5 rounded-full"
                        style={{
                          backgroundColor: INTENSITIES.find(i => i.key === w.intensity)?.color + '22',
                          color: INTENSITIES.find(i => i.key === w.intensity)?.color,
                        }}
                      >
                        {w.intensity}
                      </span>
                    </div>
                    <p className="text-xs text-muted">{w.date} · {w.duration_min} min</p>
                  </div>
                </div>
                {w.notes && <p className="text-sm text-sub">{w.notes}</p>}
                {w.exercises?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {w.exercises.map((ex: any) => (
                      <span key={ex.exercise_id} className="bg-bg text-muted text-xs px-2 py-1 rounded-lg">
                        {ex.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
