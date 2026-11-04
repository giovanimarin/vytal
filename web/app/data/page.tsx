'use client'
import { useQuery } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { todayISO } from '@/lib/utils'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const CHART_STYLE = {
  contentStyle: { backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 },
  labelStyle: { color: '#94a3b8', fontSize: 11 },
}

export default function DataPage() {
  const { userId } = useAuthStore()
  const today = todayISO()
  const start = new Date(Date.now() - 13 * 86400000).toISOString().split('T')[0]

  const { data: history } = useQuery({
    queryKey: ['readiness-history-data', userId],
    queryFn: async () => {
      const { data } = await api.get(`/readiness/${userId}/history?start_date=${start}&end_date=${today}`)
      return (data as any[]).reverse()
    },
    enabled: !!userId,
  })

  const { data: todayReadiness } = useQuery({
    queryKey: ['readiness', userId, today],
    queryFn: async () => {
      const { data } = await api.get(`/readiness/${userId}?date=${today}`)
      return data
    },
    enabled: !!userId,
  })

  function MetricCard({ title, value, unit, icon, color = '#3b82f6' }: any) {
    return (
      <div className="bg-surface rounded-2xl p-5 space-y-2">
        <div className="flex items-center gap-2 text-muted">
          <span>{icon}</span>
          <span className="text-xs uppercase tracking-wide font-bold">{title}</span>
        </div>
        <div className="flex items-end gap-1">
          <span className="text-3xl font-black" style={{ color }}>{value ?? '—'}</span>
          {unit && <span className="text-muted text-sm mb-1">{unit}</span>}
        </div>
      </div>
    )
  }

  const latest = history?.[history.length - 1]

  // Preparar dados para os gráficos
  const sleepData = history?.map((h: any) => ({
    date: h.date?.slice(5),
    score: Math.round(h.readiness_score),
  })) ?? []

  return (
    <AppShell>
      <div className="p-8 space-y-8">
        <div>
          <h1 className="text-3xl font-black text-text">Dados de Saúde</h1>
          <p className="text-muted text-sm mt-1">Visão geral dos últimos 14 dias</p>
        </div>

        {/* Cards de métricas do dia */}
        {todayReadiness && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Readiness"
              value={Math.round(todayReadiness.readiness_score)}
              unit="/100"
              icon="📊"
              color={todayReadiness.readiness_score >= 70 ? '#4CAF50' : todayReadiness.readiness_score >= 40 ? '#FFC107' : '#F44336'}
            />
            <MetricCard
              title="Sono"
              value={Math.round(todayReadiness.sleep_score_contribution)}
              unit="/100"
              icon="😴"
              color="#818cf8"
            />
            <MetricCard
              title="Freq. Cardíaca"
              value={Math.round(todayReadiness.hr_score_contribution)}
              unit="/100"
              icon="❤️"
              color="#f43f5e"
            />
            <MetricCard
              title="Estresse"
              value={todayReadiness.stress_score_contribution !== null ? Math.round(todayReadiness.stress_score_contribution) : null}
              unit="/100"
              icon="🧠"
              color="#f59e0b"
            />
          </div>
        )}

        {/* Readiness Score — histórico */}
        {sleepData.length > 0 && (
          <div className="bg-surface rounded-2xl p-6 space-y-4">
            <h2 className="font-bold text-text">Readiness Score — 14 dias</h2>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={sleepData}>
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#334155" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 11 }} width={30} />
                <Tooltip {...CHART_STYLE} itemStyle={{ color: '#3b82f6' }} />
                <Area type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} fill="url(#grad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Contribuições detalhadas do dia */}
        {todayReadiness && (
          <div className="bg-surface rounded-2xl p-6 space-y-4">
            <h2 className="font-bold text-text">Contribuições de hoje — detalhado</h2>
            <div className="space-y-4">
              {[
                { label: 'Sono', value: todayReadiness.sleep_score_contribution, weight: '40%', color: '#818cf8' },
                { label: 'Frequência Cardíaca', value: todayReadiness.hr_score_contribution, weight: '30%', color: '#f43f5e' },
                { label: 'Atividade', value: todayReadiness.activity_score_contribution, weight: '20%', color: '#4CAF50' },
                { label: 'Estresse', value: todayReadiness.stress_score_contribution, weight: '10%', color: '#f59e0b' },
              ].filter(c => c.value !== null).map(c => (
                <div key={c.label} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-sub">{c.label}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-muted text-xs">{c.weight}</span>
                      <span className="font-bold" style={{ color: c.color }}>{Math.round(c.value)}</span>
                    </div>
                  </div>
                  <div className="h-2 bg-bg rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${c.value}%`, backgroundColor: c.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Insight */}
        {todayReadiness?.insight_text && (
          <div className="bg-surface rounded-2xl p-6">
            <p className="text-xs text-muted uppercase tracking-wide mb-3 font-bold">Insight do dia</p>
            <p className="text-sub leading-relaxed">{todayReadiness.insight_text}</p>
          </div>
        )}
      </div>
    </AppShell>
  )
}
