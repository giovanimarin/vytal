import React from 'react'
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native'
import { SleepDetails } from '../../src/components/features/SleepDetails'
import { HRZones } from '../../src/components/features/HRZones'
import { StepsCalories } from '../../src/components/features/StepsCalories'
import { AdvancedMetrics } from '../../src/components/features/AdvancedMetrics'
import { useHealthSummary } from '../../src/hooks/useHealthData'
import { useAdvancedMetrics } from '../../src/hooks/useReadiness'
import { useAuthStore } from '../../src/store/authStore'

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

function formatDate(iso: string) {
  return new Date(iso + 'T12:00:00').toLocaleDateString('pt-BR', {
    weekday: 'long', day: 'numeric', month: 'long',
  })
}

export default function DataScreen() {
  const userId = useAuthStore((s) => s.userId)
  const today = todayISO()

  const { data, isLoading } = useHealthSummary(userId, today)
  const { data: advancedMetrics, isLoading: advancedLoading } = useAdvancedMetrics(userId, today)

  const totalCalories = data?.activity?.length
    ? data.activity.reduce((sum, a) => sum + (a.calories_burned ?? 0), 0)
    : null

  const hasData = data && (
    data.sleep || data.steps || data.heart_rate || (data.activity?.length ?? 0) > 0
  )

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Seus Dados</Text>
      <Text style={styles.subtitle}>{formatDate(today)}</Text>

      {isLoading && (
        <View style={styles.center}>
          <ActivityIndicator color="#3b82f6" size="large" />
        </View>
      )}

      {!isLoading && !hasData && (
        <View style={styles.empty}>
          <Text style={styles.emptyTitle}>Nenhum dado disponível</Text>
          <Text style={styles.emptyText}>
            Sincronize seus dados na aba Hoje para visualizar suas métricas de saúde.
          </Text>
        </View>
      )}

      {!isLoading && hasData && (
        <>
          <SleepDetails sleep={data.sleep ?? null} />
          <HRZones heartRate={data.heart_rate ?? null} />
          <StepsCalories
            steps={data.steps?.total_steps ?? null}
            calories={totalCalories}
          />
          <AdvancedMetrics metrics={advancedMetrics ?? null} isLoading={advancedLoading} />
        </>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  content: { padding: 24, paddingBottom: 48, gap: 24 },
  title: { fontSize: 28, fontWeight: '800', color: '#f8fafc' },
  subtitle: { fontSize: 14, color: '#64748b', textTransform: 'capitalize', marginTop: -16 },
  center: { alignItems: 'center', paddingVertical: 60 },
  empty: { alignItems: 'center', gap: 12, paddingVertical: 60 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: '#f8fafc' },
  emptyText: { color: '#64748b', textAlign: 'center', lineHeight: 22, fontSize: 14 },
})
