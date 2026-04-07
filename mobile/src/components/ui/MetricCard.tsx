import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

interface Props {
  title: string
  value: string
  subtitle?: string
  accent?: string
}

export function MetricCard({ title, value, subtitle, accent = '#3b82f6' }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <Text style={[styles.value, { color: accent }]}>{value}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 16,
    flex: 1,
    minWidth: '45%',
    gap: 4,
  },
  title: {
    fontSize: 12,
    color: '#64748b',
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  value: {
    fontSize: 24,
    fontWeight: '700',
  },
  subtitle: {
    fontSize: 12,
    color: '#94a3b8',
  },
})
