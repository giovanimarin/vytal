import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

interface SleepData {
  duration_minutes: number
  deep_sleep_minutes: number
  rem_sleep_minutes: number
  light_sleep_minutes: number
  awake_minutes: number
}

interface Props {
  sleep: SleepData | null
}

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h > 0 && m > 0) return `${h}h ${m}min`
  if (h > 0) return `${h}h`
  return `${m}min`
}

interface PhaseConfig {
  key: keyof SleepData
  label: string
  color: string
}

const PHASES: PhaseConfig[] = [
  { key: 'deep_sleep_minutes', label: 'Profundo', color: '#1e40af' },
  { key: 'rem_sleep_minutes', label: 'REM', color: '#7c3aed' },
  { key: 'light_sleep_minutes', label: 'Leve', color: '#3b82f6' },
  { key: 'awake_minutes', label: 'Acordado', color: '#475569' },
]

export function SleepDetails({ sleep }: Props) {
  if (!sleep) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Sono</Text>
        <Text style={styles.empty}>Dados não disponíveis</Text>
      </View>
    )
  }

  const total = sleep.duration_minutes || 1

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Sono</Text>
        <Text style={styles.duration}>{formatDuration(sleep.duration_minutes)}</Text>
      </View>

      {/* Phase bar */}
      <View style={styles.phaseBarContainer}>
        {PHASES.map((phase) => {
          const minutes = sleep[phase.key] as number
          const pct = total > 0 ? (minutes / total) * 100 : 0
          if (pct <= 0) return null
          return (
            <View
              key={phase.key}
              style={[styles.phaseSegment, { flex: pct, backgroundColor: phase.color }]}
            />
          )
        })}
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        {PHASES.map((phase) => {
          const minutes = sleep[phase.key] as number
          if (!minutes) return null
          return (
            <View key={phase.key} style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: phase.color }]} />
              <Text style={styles.legendLabel}>{phase.label}</Text>
              <Text style={styles.legendValue}>{formatDuration(minutes)}</Text>
            </View>
          )
        })}
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  duration: {
    fontSize: 20,
    fontWeight: '800',
    color: '#818cf8',
  },
  phaseBarContainer: {
    flexDirection: 'row',
    height: 16,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#334155',
  },
  phaseSegment: {
    height: '100%',
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendLabel: {
    fontSize: 12,
    color: '#94a3b8',
  },
  legendValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#cbd5e1',
  },
  empty: {
    color: '#64748b',
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
})
