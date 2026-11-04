import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import type { ReadinessCategory } from '../../types/health'

interface HistoryItem {
  date: string
  readiness_score: number
  readiness_category: ReadinessCategory
}

interface Props {
  history: HistoryItem[]
}

const CATEGORY_COLORS: Record<string, string> = {
  intense: '#3b82f6',
  moderate: '#10b981',
  light: '#f59e0b',
  rest: '#ef4444',
}

const DAY_LABELS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

const MAX_BAR_HEIGHT = 80

function getDayLabel(isoDate: string): string {
  const d = new Date(isoDate + 'T12:00:00')
  return DAY_LABELS[d.getDay()]
}

export function ScoreHistory({ history }: Props) {
  if (!history || history.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Histórico 7 Dias</Text>
        <Text style={styles.empty}>Dados não disponíveis</Text>
      </View>
    )
  }

  const maxScore = Math.max(...history.map((h) => h.readiness_score), 1)

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Histórico 7 Dias</Text>
      <View style={styles.chart}>
        {history.map((item, index) => {
          const barHeight = Math.max(
            4,
            Math.round((item.readiness_score / 100) * MAX_BAR_HEIGHT)
          )
          const color = CATEGORY_COLORS[item.readiness_category] ?? '#64748b'
          return (
            <View key={index} style={styles.barWrapper}>
              <Text style={styles.scoreLabel}>{Math.round(item.readiness_score)}</Text>
              <View style={styles.barContainer}>
                <View
                  style={[
                    styles.bar,
                    { height: barHeight, backgroundColor: color },
                  ]}
                />
              </View>
              <Text style={styles.dayLabel}>{getDayLabel(item.date)}</Text>
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
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  chart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    gap: 4,
  },
  barWrapper: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
  },
  scoreLabel: {
    fontSize: 10,
    color: '#94a3b8',
    fontWeight: '600',
  },
  barContainer: {
    height: MAX_BAR_HEIGHT,
    justifyContent: 'flex-end',
    alignItems: 'center',
    width: '100%',
  },
  bar: {
    width: '70%',
    borderRadius: 4,
    minHeight: 4,
  },
  dayLabel: {
    fontSize: 10,
    color: '#64748b',
    textAlign: 'center',
  },
  empty: {
    color: '#64748b',
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
})
