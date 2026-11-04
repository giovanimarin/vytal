import React from 'react'
import {
  View, Text, StyleSheet, ScrollView,
  ActivityIndicator, TouchableOpacity,
} from 'react-native'
import { useAuthStore } from '../../src/store/authStore'
import { useModalityReadiness } from '../../src/hooks/useWorkouts'
import type { ModalityReadiness } from '../../src/types/health'

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

const MODALITY_LABEL: Record<string, string> = {
  crossfit:  'Crossfit',
  corrida:   'Corrida',
  academia:  'Academia',
  tenis:     'Tênis',
  pilates:   'Pilates',
  surfe:     'Surfe',
  yoga:      'Yoga',
  ciclismo:  'Ciclismo',
}

const MODALITY_EMOJI: Record<string, string> = {
  crossfit:  '🏋️',
  corrida:   '🏃',
  academia:  '💪',
  tenis:     '🎾',
  pilates:   '🧘',
  surfe:     '🏄',
  yoga:      '🧘',
  ciclismo:  '🚴',
}

function statusColor(status: string): string {
  if (status === 'green')  return '#4CAF50'
  if (status === 'yellow') return '#FFC107'
  return '#F44336'
}

function statusLabel(status: string): string {
  if (status === 'green')  return 'Pronto'
  if (status === 'yellow') return 'Moderado'
  return 'Descansar'
}

function ModalityCard({ item }: { item: ModalityReadiness }) {
  const color = statusColor(item.status)
  const score = Math.round(item.score)

  return (
    <View style={[styles.card, { borderLeftColor: color, borderLeftWidth: 4 }]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardEmoji}>{MODALITY_EMOJI[item.modality] ?? '🏅'}</Text>
        <View style={styles.cardTitleBlock}>
          <Text style={styles.cardTitle}>{MODALITY_LABEL[item.modality] ?? item.modality}</Text>
          <View style={[styles.badge, { backgroundColor: color + '22' }]}>
            <Text style={[styles.badgeText, { color }]}>{statusLabel(item.status)}</Text>
          </View>
        </View>
        <Text style={[styles.cardScore, { color }]}>{score}</Text>
      </View>
      <Text style={styles.recommendation}>{item.recommendation}</Text>
      {item.low_confidence && (
        <Text style={styles.lowConf}>⚠ Confiança reduzida — HRV não disponível</Text>
      )}
    </View>
  )
}

export default function ModalitiesScreen() {
  const userId = useAuthStore((s) => s.userId)
  const today = todayISO()
  const { data, isLoading, error } = useModalityReadiness(userId, today)

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#3b82f6" size="large" />
      </View>
    )
  }

  if (error || !data) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Sem dados suficientes. Sincronize primeiro.</Text>
      </View>
    )
  }

  const sorted = [...data.modalities].sort((a, b) => b.score - a.score)

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Pronto para treinar?</Text>
        <Text style={styles.subtitle}>Score por modalidade — hoje</Text>
      </View>

      {sorted.map(item => (
        <ModalityCard key={item.modality} item={item} />
      ))}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: '#0f172a' },
  content:     { padding: 24, paddingBottom: 48, gap: 12 },
  center:      { flex: 1, backgroundColor: '#0f172a', alignItems: 'center', justifyContent: 'center' },
  header:      { gap: 4, marginBottom: 8 },
  title:       { fontSize: 28, fontWeight: '800', color: '#f8fafc' },
  subtitle:    { fontSize: 14, color: '#64748b' },
  errorText:   { color: '#64748b', textAlign: 'center' },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 16,
    gap: 10,
  },
  cardHeader:      { flexDirection: 'row', alignItems: 'center', gap: 12 },
  cardEmoji:       { fontSize: 28 },
  cardTitleBlock:  { flex: 1, gap: 4 },
  cardTitle:       { fontSize: 16, fontWeight: '700', color: '#f8fafc' },
  badge:           { alignSelf: 'flex-start', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  badgeText:       { fontSize: 11, fontWeight: '700' },
  cardScore:       { fontSize: 32, fontWeight: '800' },
  recommendation:  { color: '#94a3b8', fontSize: 14, lineHeight: 21 },
  lowConf:         { color: '#f59e0b', fontSize: 12 },
})
