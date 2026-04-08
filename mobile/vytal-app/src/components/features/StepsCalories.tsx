import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

interface Props {
  steps: number | null
  calories: number | null
}

const STEPS_GOAL = 10000

export function StepsCalories({ steps, calories }: Props) {
  const hasAny = steps != null || calories != null

  if (!hasAny) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Atividade</Text>
        <Text style={styles.empty}>Dados não disponíveis</Text>
      </View>
    )
  }

  const progress = steps != null ? Math.min(steps / STEPS_GOAL, 1) : 0
  const progressPct = Math.round(progress * 100)

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Atividade</Text>

      <View style={styles.row}>
        {/* Steps */}
        <View style={styles.card}>
          <Text style={styles.metricLabel}>Passos</Text>
          <Text style={styles.stepsValue}>
            {steps != null ? steps.toLocaleString('pt-BR') : '—'}
          </Text>
          <Text style={styles.goalLabel}>meta: {STEPS_GOAL.toLocaleString('pt-BR')}</Text>

          {steps != null && (
            <>
              <View style={styles.progressTrack}>
                <View
                  style={[
                    styles.progressFill,
                    { width: `${progressPct}%` as unknown as number },
                  ]}
                />
              </View>
              <Text style={styles.progressPct}>{progressPct}%</Text>
            </>
          )}
        </View>

        {/* Calories */}
        <View style={styles.card}>
          <Text style={styles.metricLabel}>Calorias</Text>
          <Text style={styles.caloriesValue}>
            {calories != null ? Math.round(calories).toLocaleString('pt-BR') : '—'}
          </Text>
          <Text style={styles.goalLabel}>kcal queimadas</Text>
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
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  card: {
    flex: 1,
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 14,
    gap: 4,
  },
  metricLabel: {
    fontSize: 12,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  stepsValue: {
    fontSize: 26,
    fontWeight: '800',
    color: '#10b981',
  },
  caloriesValue: {
    fontSize: 26,
    fontWeight: '800',
    color: '#f59e0b',
  },
  goalLabel: {
    fontSize: 11,
    color: '#475569',
  },
  progressTrack: {
    height: 6,
    backgroundColor: '#1e293b',
    borderRadius: 3,
    marginTop: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#10b981',
    borderRadius: 3,
  },
  progressPct: {
    fontSize: 11,
    color: '#10b981',
    fontWeight: '600',
  },
  empty: {
    color: '#64748b',
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
})
