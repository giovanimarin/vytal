import React, { useState } from 'react'
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, ActivityIndicator, Alert,
} from 'react-native'
import { useRouter } from 'expo-router'
import { ScoreRing } from '../../src/components/ui/ScoreRing'
import { ContributionBar } from '../../src/components/features/ContributionBar'
import { useReadiness, useSyncHealthData } from '../../src/hooks/useReadiness'
import { useAuthStore } from '../../src/store/authStore'

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

function sevenDaysAgoISO() {
  const d = new Date()
  d.setDate(d.getDate() - 7)
  return d.toISOString().split('T')[0]
}

export default function ReadinessScreen() {
  const userId = useAuthStore((s) => s.userId)
  const reset = useAuthStore((s) => s.reset)
  const today = todayISO()
  const router = useRouter()

  const { data, isLoading, error, refetch } = useReadiness(userId, today)
  const sync = useSyncHealthData()

  function handleDisconnect() {
    reset()
    router.replace('/connect')
  }

  async function handleSync() {
    if (!userId) return
    try {
      await sync.mutateAsync({
        userId,
        startDate: sevenDaysAgoISO(),
        endDate: today,
      })
      await refetch()
    } catch {
      Alert.alert('Erro', 'Falha ao sincronizar dados. Verifique sua conexão.')
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <Text style={styles.title}>Daily Readiness</Text>
          <TouchableOpacity onPress={handleDisconnect}>
            <Text style={styles.disconnectText}>Sair</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.date}>{formatDate(today)}</Text>
      </View>

      {isLoading && (
        <View style={styles.center}>
          <ActivityIndicator color="#3b82f6" size="large" />
        </View>
      )}

      {error && !isLoading && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Sem dados para hoje</Text>
          <Text style={styles.emptyText}>
            Sincronize seus dados do Google Fit para ver seu Daily Readiness Score.
          </Text>
          <TouchableOpacity
            style={[styles.syncButton, sync.isPending && styles.syncButtonDisabled]}
            onPress={handleSync}
            disabled={sync.isPending}
          >
            {sync.isPending
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.syncButtonText}>Sincronizar Agora</Text>
            }
          </TouchableOpacity>
        </View>
      )}

      {data && (
        <>
          <View style={styles.scoreSection}>
            <ScoreRing score={data.readiness_score} category={data.readiness_category} />
          </View>

          <View style={styles.insightCard}>
            <Text style={styles.insightText}>{data.insight_text}</Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Contribuições</Text>
            <View style={styles.contributions}>
              <ContributionBar label="Sono"              value={data.sleep_score_contribution}    weight="40%" />
              <ContributionBar label="Freq. Cardíaca"   value={data.hr_score_contribution}       weight="30%" />
              <ContributionBar label="Atividade"        value={data.activity_score_contribution} weight="20%" />
              <ContributionBar label="Estresse"         value={data.stress_score_contribution}   weight="10%" />
            </View>
          </View>

          <TouchableOpacity
            style={[styles.syncButton, sync.isPending && styles.syncButtonDisabled]}
            onPress={handleSync}
            disabled={sync.isPending}
          >
            {sync.isPending
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.syncButtonText}>Atualizar dados</Text>
            }
          </TouchableOpacity>
        </>
      )}
    </ScrollView>
  )
}

function formatDate(iso: string) {
  return new Date(iso + 'T12:00:00').toLocaleDateString('pt-BR', {
    weekday: 'long', day: 'numeric', month: 'long',
  })
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  content: { padding: 24, paddingBottom: 48, gap: 24 },
  header: { gap: 4 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '800', color: '#f8fafc' },
  disconnectText: { color: '#475569', fontSize: 14 },
  date: { fontSize: 14, color: '#64748b', textTransform: 'capitalize' },
  center: { alignItems: 'center', paddingVertical: 60 },
  scoreSection: { alignItems: 'center', paddingVertical: 16 },
  insightCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
  },
  insightText: { color: '#cbd5e1', fontSize: 15, lineHeight: 24 },
  section: { gap: 16 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#f8fafc' },
  contributions: { gap: 16 },
  syncButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
  },
  syncButtonDisabled: { opacity: 0.6 },
  syncButtonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  emptyState: { alignItems: 'center', gap: 16, paddingVertical: 40 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: '#f8fafc' },
  emptyText: { color: '#64748b', textAlign: 'center', lineHeight: 22, fontSize: 14 },
})
