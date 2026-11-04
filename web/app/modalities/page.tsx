'use client'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { todayISO, statusColor, statusLabel } from '@/lib/utils'

const MODALITY_META: Record<string, { label: string; emoji: string; desc: string }> = {
  crossfit:  { label: 'Crossfit',  emoji: '🏋️', desc: 'Full body, alta intensidade' },
  corrida:   { label: 'Corrida',   emoji: '🏃', desc: 'Cardio, membros inferiores' },
  academia:  { label: 'Academia',  emoji: '💪', desc: 'Musculação, força' },
  tenis:     { label: 'Tênis',     emoji: '🎾', desc: 'Agilidade, membros sup. e inf.' },
  pilates:   { label: 'Pilates',   emoji: '🧘', desc: 'Core, flexibilidade, lombar' },
  surfe:     { label: 'Surfe',     emoji: '🏄', desc: 'Ombros, core, equilíbrio' },
  yoga:      { label: 'Yoga',      emoji: '🌿', desc: 'Mobilidade, respiração' },
  ciclismo:  { label: 'Ciclismo',  emoji: '🚴', desc: 'Cardio, quadríceps, resistência' },
}

export default function ModalitiesPage() {
  const { userId, preferredModalities } = useAuthStore()
  const today = todayISO()

  const { data, isLoading } = useQuery({
    queryKey: ['modality-readiness', userId, today],
    queryFn: async () => {
      const { data } = await api.get(`/readiness/modalities/${userId}?date=${today}`)
      return data
    },
    enabled: !!userId,
  })

  const sorted = data?.modalities
    ? [...data.modalities].sort((a: any, b: any) => b.score - a.score)
    : []

  return (
    <AppShell>
      <div className="p-8 space-y-6">
        <div>
          <h1 className="text-3xl font-black text-text">Pronto para treinar?</h1>
          <p className="text-muted text-sm mt-1">Score de prontidão por modalidade — hoje</p>
        </div>

        {(!preferredModalities || preferredModalities.length === 0) && (
          <div className="bg-surface border border-yellow-500/40 rounded-2xl p-4 flex items-center justify-between">
            <p className="text-sm text-sub">Você ainda não selecionou suas modalidades. Exibindo todas.</p>
            <Link href="/settings" className="text-brand text-sm font-semibold hover:underline shrink-0 ml-4">
              Configurar →
            </Link>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="w-10 h-10 border-4 border-brand border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {sorted.map((item: any) => {
            const meta = MODALITY_META[item.modality] ?? { label: item.modality, emoji: '🏅', desc: '' }
            const color = statusColor(item.status)
            const score = Math.round(item.score)

            return (
              <div
                key={item.modality}
                className="bg-surface rounded-2xl p-5 space-y-4"
                style={{ borderLeft: `4px solid ${color}` }}
              >
                {/* Header */}
                <div className="flex items-start gap-3">
                  <span className="text-3xl">{meta.emoji}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-text">{meta.label}</h3>
                      <span
                        className="text-xs font-bold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: color + '22', color }}
                      >
                        {statusLabel(item.status)}
                      </span>
                    </div>
                    <p className="text-xs text-muted mt-0.5">{meta.desc}</p>
                  </div>
                  <span className="text-3xl font-black" style={{ color }}>{score}</span>
                </div>

                {/* Score bar */}
                <div className="h-1.5 bg-border rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: color }} />
                </div>

                {/* Recomendação */}
                <p className="text-sub text-sm leading-relaxed">{item.recommendation}</p>

                {item.low_confidence && (
                  <p className="text-yellow-400 text-xs">⚠ HRV indisponível — confiança reduzida</p>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </AppShell>
  )
}
