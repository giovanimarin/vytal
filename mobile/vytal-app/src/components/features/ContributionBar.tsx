import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

interface Props {
  label: string
  value: number | null
  weight: string
}

export function ContributionBar({ label, value, weight }: Props) {
  if (value === null) {
    return (
      <View style={styles.row}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.unavailable}>indisponível</Text>
      </View>
    )
  }

  const color = value >= 75 ? '#22c55e' : value >= 50 ? '#3b82f6' : value >= 30 ? '#f59e0b' : '#ef4444'

  return (
    <View style={styles.row}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.weight}>{weight}</Text>
      </View>
      <View style={styles.barBg}>
        <View style={[styles.barFill, { width: `${value}%`, backgroundColor: color }]} />
      </View>
      <Text style={[styles.valueText, { color }]}>{Math.round(value)}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  row: {
    gap: 6,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  label: {
    color: '#cbd5e1',
    fontSize: 14,
    fontWeight: '500',
  },
  weight: {
    color: '#475569',
    fontSize: 12,
  },
  barBg: {
    height: 8,
    backgroundColor: '#1e293b',
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
  },
  valueText: {
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'right',
  },
  unavailable: {
    color: '#475569',
    fontSize: 12,
    fontStyle: 'italic',
  },
})
