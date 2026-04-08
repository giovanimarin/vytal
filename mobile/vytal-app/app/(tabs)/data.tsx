import React from 'react'
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native'
import { MetricCard } from '../../src/components/ui/MetricCard'
import { useHealthSummary } from '../../src/hooks/useHealthData'
import { useAuthStore } from '../../src/store/authStore'

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

export default function DataScreen() {
  const userId = useAuthStore((s) => s.userId)
  const today = todayISO()
  const { data, isLoading } = useHealthSummary(userId, today)

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Meus Dados</Text>
      <Text style={styles.subtitle}>Hoje</Text>

      {isLoading && (
        <View style={styles.center}>
          <ActivityIndicator color="#3b82f6" size="large" />
        </View>
      )}

      {data && (
        <>
          {/* Sono */}
          {data.sleep && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Sono</Text>
              <View style={styles.cards}>
                <MetricCard
                  title="Duração"
                  value={formatMinutes(data.sleep.duration_minutes)}
                  accent="#818cf8"
                />
                <MetricCard
                  title="Sono Profundo"
                  value={formatMinutes(data.sleep.deep_sleep_minutes)}
                  accent="#6366f1"
                />
                <MetricCard
                  title="REM"
                  value={formatMinutes(data.sleep.rem_sleep_minutes)}
                  accent="#8b5cf6"
                />
                {data.sleep.sleep_score != null && (
                  <MetricCard
                    title="Score"
                    value={`${Math.round(data.sleep.sleep_score)}`}
                    subtitle="de 100"
                    accent="#a78bfa"
                  />
                )}
              </View>
            </View>
          )}

          {/* Passos */}
          {data.steps && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Passos</Text>
              <View style={styles.cards}>
                <MetricCard
                  title="Total"
                  value={data.steps.total_steps.toLocaleString('pt-BR')}
                  subtitle="passos hoje"
                  accent="#34d399"
                />
              </View>
            </View>
          )}

          {/* Frequência Cardíaca */}
          {data.heart_rate && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Frequência Cardíaca</Text>
              <View style={styles.cards}>
                <MetricCard
                  title="Repouso"
                  value={`${Math.round(data.heart_rate.resting_bpm)} bpm`}
                  accent="#f87171"
                />
                <MetricCard
                  title="Média"
                  value={`${Math.round(data.heart_rate.average_bpm)} bpm`}
                  accent="#fca5a5"
                />
                <MetricCard
                  title="Máx"
                  value={`${Math.round(data.heart_rate.max_bpm)} bpm`}
                  accent="#ef4444"
                />
              </View>
            </View>
          )}

          {/* Atividades */}
          {data.activity?.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Atividades</Text>
              {data.activity.map((a, i) => (
                <View key={i} style={styles.activityRow}>
                  <Text style={styles.activityType}>{formatActivityType(a.activity_type)}</Text>
                  <Text style={styles.activityDetail}>
                    {a.duration_minutes} min · {formatIntensity(a.intensity)} · {Math.round(a.calories_burned)} kcal
                  </Text>
                </View>
              ))}
            </View>
          )}

          {(!data.sleep && !data.steps && !data.heart_rate && !data.activity?.length) && (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>Nenhum dado para hoje. Sincronize na aba Hoje.</Text>
            </View>
          )}
        </>
      )}
    </ScrollView>
  )
}

function formatMinutes(min: number) {
  const h = Math.floor(min / 60)
  const m = min % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatActivityType(type: string) {
  const map: Record<string, string> = {
    running: 'Corrida', walking: 'Caminhada', biking: 'Ciclismo',
    hiking: 'Trilha', strength_training: 'Musculação',
    yoga: 'Yoga', swimming: 'Natação',
  }
  return map[type] ?? type
}

function formatIntensity(i: string) {
  const map: Record<string, string> = { low: 'leve', moderate: 'moderada', high: 'intensa' }
  return map[i] ?? i
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  content: { padding: 24, paddingBottom: 48, gap: 24 },
  title: { fontSize: 28, fontWeight: '800', color: '#f8fafc' },
  subtitle: { fontSize: 14, color: '#64748b' },
  center: { alignItems: 'center', paddingVertical: 60 },
  section: { gap: 12 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#f8fafc' },
  cards: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  activityRow: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 14,
    gap: 4,
  },
  activityType: { color: '#f8fafc', fontSize: 15, fontWeight: '600' },
  activityDetail: { color: '#94a3b8', fontSize: 13 },
  empty: { alignItems: 'center', paddingVertical: 40 },
  emptyText: { color: '#475569', textAlign: 'center', fontSize: 14 },
})
