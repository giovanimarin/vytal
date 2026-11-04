'use client'
import { useQuery } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { todayISO, formatDate, statusColor, statusLabel } from '@/lib/utils'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function ScoreRing({ score, category }: { score: number; category: string }) {
  const color = statusColor(
    score >= 70 ? 'green' : score >= 40 ? 'yellow' : 'red'
  )
  const r = 70
  const circ = 2 * Math.PI * r
  const dash = (score / 100) * circ

  return (
    <div className="flex flex-col items-center gap-4">
      <svg width={180} height={180} viewBox="0 0 180 180">
        <circle cx={90} cy={90} r={r} fill="none" stroke="#334155" strokeWidth={14} />
        <circle
          cx={90} cy={90} r={r} fill="none"
          stroke={color} strokeWidth={14}
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="round"
          transform="rotate(-90 90 90)"
        />
        <text x={90} y={88} textAnchor="middle" fill={color} fontSize={42} fontWeight={800}>{Math.round(score)}</text>
        <text x={90} y={112} textAnchor="middle" fill="#94a3b8" fontSize={13}>{statusLabel(score >= 70 ? 'green' : score >= 40 ? 'yellow' : 'red')}</text>
      </svg>
    </div>
  )
}

function ContribBar({ label, value, weight }: { label: string; value: number | null; weight: string }) {
  if (value === null) return null
  const color = statusColor(value >= 70 ? 'green' : value >= 40 ? 'yellow' : 'red')
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-sub">
        <span>{label}</span>
        <span className="text-muted">{weight}</span>
      </div>
      <div className="h-2 bg-border rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${value}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { userId } = useAuthStore()
  const today = todayISO()

  const { data, isLoading, error } = useQuery({
    queryKey: ['readiness', userId, today],
    queryFn: async () => {
      const { data } = await api.get(`/readiness/${userId}?date=${today}`)
      return data
    },
    enabled: !!userId,
  })

  const { data: history } = useQuery({
    queryKey: ['readiness-history', userId],
    queryFn: async () => {
      const end = today
      const start = new Date(Date.now() - 13 * 86400000).toISOString().split('T')[0]
      const { data } = await api.get(`/readiness/${userId}/history?start_date=${start}&end_date=${end}`)
      return data as { date: string; readiness_score: number; readiness_category: string }[]
    },
    enabled: !!userId,
  })

  const { data: advanced } = useQuery({
    queryKey: ['advanced', userId, today],
    queryFn: async () => {
      const { data } = await api.get(`/readiness/${userId}/advanced?date=${today}`)
      return data
    },
    enabled: !!userId,
  })

  const chartData = history
    ? [...history].reverse().map(h => ({
        date: h.date.slice(5),
        score: Math.round(h.readiness_score),
      }))
    : []

  return (
    <AppShell>
      <div className="p-8 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-black text-text">Daily Readiness</h1>
          <p className="text-muted text-sm capitalize mt-1">{formatDate(today)}</p>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="w-10 h-10 border-4 border-brand border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {error && !isLoading && (
          <div className="bg-surface rounded-2xl p-6 text-center space-y-2">
            <p className="text-sub">Sem dados para hoje.</p>
            <p className="text-xs text-muted">Volte para o login e clique em "Entrar com dados demo".</p>
          </div>
        )}

        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Score */}
            <div className="bg-surface rounded-2xl p-6 flex flex-col items-center gap-4">
              <ScoreRing score={data.readiness_score} category={data.readiness_category} />
              <p className="text-sub text-sm text-center leading-relaxed">{data.insight_text}</p>
            </div>

            {/* Contribuições */}
            <div className="bg-surface rounded-2xl p-6 space-y-5">
              <h2 className="font-bold text-text">Contribuições</h2>
              <ContribBar label="Sono"           value={data.sleep_score_contribution}    weight="40%" />
              <ContribBar label="Freq. Cardíaca" value={data.hr_score_contribution}       weight="30%" />
              <ContribBar label="Atividade"      value={data.activity_score_contribution} weight="20%" />
              <ContribBar label="Estresse"       value={data.stress_score_contribution}   weight="10%" />
            </div>

            {/* Advanced metrics */}
            {advanced && (
              <div className="bg-surface rounded-2xl p-6 space-y-4">
                <h2 className="font-bold text-text">Métricas Avançadas</h2>

                <div className="space-y-1">
                  <p className="text-xs text-muted uppercase tracking-wide">Social Jetlag</p>
                  <p className="text-sm text-sub">{advanced.social_jetlag?.interpretation ?? 'Dados insuficientes'}</p>
                </div>

                <div className="space-y-1">
                  <p className="text-xs text-muted uppercase tracking-wide">Curva de Recuperação</p>
                  <p className="text-sm text-sub">{advanced.recovery_curve?.interpretation ?? 'Dados insuficientes'}</p>
                </div>

                <div className="space-y-1">
                  <p className="text-xs text-muted uppercase tracking-wide">Qualidade do Sinal</p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold" style={{
                      color: advanced.signal_quality?.flag === 'reliable' ? '#4CAF50'
                        : advanced.signal_quality?.flag === 'caution' ? '#FFC107' : '#F44336'
                    }}>
                      {advanced.signal_quality?.score ?? 0}
                    </span>
                    <span className="text-xs text-muted">{advanced.signal_quality?.interpretation}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Histórico 14 dias */}
        {chartData.length > 0 && (
          <div className="bg-surface rounded-2xl p-6 space-y-4">
            <h2 className="font-bold text-text">Histórico — 14 dias</h2>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData}>
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 11 }} width={30} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8', fontSize: 11 }}
                  itemStyle={{ color: '#3b82f6' }}
                />
                <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </AppShell>
  )
}
