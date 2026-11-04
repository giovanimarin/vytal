import React from 'react'
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native'
import type { AdvancedMetricsResponse } from '../../types/health'

interface Props {
  metrics: AdvancedMetricsResponse | null
  isLoading: boolean
}


export function AdvancedMetrics({ metrics, isLoading }: Props) {
  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Métricas Avançadas</Text>
        <View style={styles.center}>
          <ActivityIndicator color="#3b82f6" />
        </View>
      </View>
    )
  }

  if (!metrics) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Métricas Avançadas</Text>
        <Text style={styles.empty}>Dados não disponíveis</Text>
      </View>
    )
  }

  const { social_jetlag, recovery_curve, signal_quality } = metrics

  const FLAG_COLORS: Record<string, string> = {
    reliable: '#10b981',
    caution: '#f59e0b',
    incomplete: '#ef4444',
  }
  const FLAG_LABELS: Record<string, string> = {
    reliable: 'Boa',
    caution: 'Regular',
    incomplete: 'Baixa',
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Métricas Avançadas</Text>

      <View style={styles.cardsRow}>
        {/* Social Jetlag */}
        <View style={styles.card}>
          <Text style={styles.cardIcon}>🕐</Text>
          <Text style={styles.cardValue}>
            {social_jetlag?.available && social_jetlag.score != null
              ? `${(social_jetlag.score as number).toFixed(1)}h`
              : '—'}
          </Text>
          <Text style={styles.cardLabel}>Jetlag Social</Text>
          {social_jetlag?.interpretation ? (
            <Text style={styles.cardInterp}>{social_jetlag.interpretation}</Text>
          ) : null}
        </View>

        {/* Recovery Curve */}
        <View style={styles.card}>
          <Text style={styles.cardIcon}>📈</Text>
          <Text style={styles.cardValue}>
            {recovery_curve?.available && recovery_curve.avg_recovery_days != null
              ? `${recovery_curve.avg_recovery_days}d`
              : '—'}
          </Text>
          <Text style={styles.cardLabel}>Recuperação</Text>
          {recovery_curve?.interpretation ? (
            <Text style={styles.cardInterp}>{recovery_curve.interpretation}</Text>
          ) : null}
        </View>

        {/* Signal Quality */}
        <View style={styles.card}>
          <Text style={styles.cardIcon}>📡</Text>
          {signal_quality != null ? (
            <>
              <View
                style={[
                  styles.qualityBadge,
                  { backgroundColor: (FLAG_COLORS[signal_quality.flag] ?? '#64748b') + '22' },
                ]}
              >
                <Text
                  style={[
                    styles.qualityBadgeText,
                    { color: FLAG_COLORS[signal_quality.flag] ?? '#64748b' },
                  ]}
                >
                  {FLAG_LABELS[signal_quality.flag] ?? signal_quality.flag}
                </Text>
              </View>
              <Text style={styles.cardValue}>{Math.round(signal_quality.score)}%</Text>
              <Text style={styles.cardLabel}>Qualidade</Text>
              {signal_quality.interpretation ? (
                <Text style={styles.cardInterp}>{signal_quality.interpretation}</Text>
              ) : null}
            </>
          ) : (
            <>
              <Text style={styles.cardValue}>—</Text>
              <Text style={styles.cardLabel}>Qualidade</Text>
            </>
          )}
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
    gap: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  center: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  empty: {
    color: '#64748b',
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
  cardsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  card: {
    flex: 1,
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    gap: 4,
  },
  cardIcon: {
    fontSize: 20,
    marginBottom: 2,
  },
  cardValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#f8fafc',
  },
  cardLabel: {
    fontSize: 11,
    color: '#64748b',
    textAlign: 'center',
  },
  cardInterp: {
    fontSize: 10,
    color: '#475569',
    textAlign: 'center',
    marginTop: 2,
  },
  qualityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginBottom: 2,
  },
  qualityBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
})
