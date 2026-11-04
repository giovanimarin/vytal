import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import type { ReadinessCategory } from '../../types/health'

const CATEGORY_COLORS: Record<ReadinessCategory, string> = {
  intense:  '#22c55e', // green
  moderate: '#3b82f6', // blue
  light:    '#f59e0b', // amber
  rest:     '#ef4444', // red
}

const CATEGORY_LABELS: Record<ReadinessCategory, string> = {
  intense:  'Treino Intenso',
  moderate: 'Treino Moderado',
  light:    'Atividade Leve',
  rest:     'Descanse',
}

interface Props {
  score: number
  category: ReadinessCategory
}

export function ScoreRing({ score, category }: Props) {
  const color = CATEGORY_COLORS[category]
  const label = CATEGORY_LABELS[category]

  return (
    <View style={styles.container}>
      <View style={[styles.ring, { borderColor: color }]}>
        <Text style={[styles.score, { color }]}>{Math.round(score)}</Text>
        <Text style={styles.outOf}>/100</Text>
      </View>
      <Text style={[styles.label, { color }]}>{label}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    gap: 12,
  },
  ring: {
    width: 180,
    height: 180,
    borderRadius: 90,
    borderWidth: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  score: {
    fontSize: 56,
    fontWeight: '800',
    lineHeight: 60,
  },
  outOf: {
    fontSize: 16,
    color: '#94a3b8',
    fontWeight: '500',
  },
  label: {
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
})
