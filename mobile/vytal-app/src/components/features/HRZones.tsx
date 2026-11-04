import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

interface HeartRateData {
  resting_bpm: number
  average_bpm: number
  max_bpm: number
  min_bpm: number
}

interface Props {
  heartRate: HeartRateData | null
}

interface Zone {
  label: string
  color: string
  rangeLabel: string
  isActive: boolean
}

function buildZones(hr: HeartRateData): Zone[] {
  const { resting_bpm, max_bpm, average_bpm } = hr
  const leve65 = Math.round(max_bpm * 0.65)
  const mod80 = Math.round(max_bpm * 0.8)

  return [
    {
      label: 'Repouso',
      color: '#64748b',
      rangeLabel: `≤ ${resting_bpm} bpm`,
      isActive: average_bpm <= resting_bpm,
    },
    {
      label: 'Leve',
      color: '#10b981',
      rangeLabel: `${resting_bpm + 1}–${leve65} bpm`,
      isActive: average_bpm > resting_bpm && average_bpm <= leve65,
    },
    {
      label: 'Moderado',
      color: '#f59e0b',
      rangeLabel: `${leve65 + 1}–${mod80} bpm`,
      isActive: average_bpm > leve65 && average_bpm <= mod80,
    },
    {
      label: 'Intenso',
      color: '#ef4444',
      rangeLabel: `> ${mod80} bpm`,
      isActive: average_bpm > mod80,
    },
  ]
}

export function HRZones({ heartRate }: Props) {
  if (!heartRate) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Frequência Cardíaca</Text>
        <Text style={styles.empty}>Dados não disponíveis</Text>
      </View>
    )
  }

  const zones = buildZones(heartRate)

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Frequência Cardíaca</Text>
        <Text style={styles.avgBpm}>{Math.round(heartRate.average_bpm)} bpm méd.</Text>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}>
          <Text style={styles.statValue}>{Math.round(heartRate.resting_bpm)}</Text>
          <Text style={styles.statLabel}>Repouso</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.stat}>
          <Text style={styles.statValue}>{Math.round(heartRate.min_bpm)}</Text>
          <Text style={styles.statLabel}>Mínima</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.stat}>
          <Text style={styles.statValue}>{Math.round(heartRate.max_bpm)}</Text>
          <Text style={styles.statLabel}>Máxima</Text>
        </View>
      </View>

      <View style={styles.zones}>
        {zones.map((zone) => (
          <View key={zone.label} style={[styles.zoneRow, zone.isActive && styles.zoneRowActive]}>
            <View style={[styles.zoneIndicator, { backgroundColor: zone.color }]} />
            <Text style={[styles.zoneLabel, zone.isActive && styles.zoneLabelActive]}>
              {zone.label}
            </Text>
            <Text style={styles.zoneRange}>{zone.rangeLabel}</Text>
            {zone.isActive && (
              <View style={[styles.activeBadge, { backgroundColor: zone.color + '33' }]}>
                <Text style={[styles.activeBadgeText, { color: zone.color }]}>Hoje</Text>
              </View>
            )}
          </View>
        ))}
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
  avgBpm: {
    fontSize: 13,
    color: '#94a3b8',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 16,
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  stat: {
    alignItems: 'center',
    gap: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#f8fafc',
  },
  statLabel: {
    fontSize: 11,
    color: '#64748b',
  },
  statDivider: {
    width: 1,
    height: 32,
    backgroundColor: '#1e293b',
  },
  zones: {
    gap: 8,
  },
  zoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: '#0f172a',
  },
  zoneRowActive: {
    borderWidth: 1,
    borderColor: '#334155',
  },
  zoneIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  zoneLabel: {
    fontSize: 13,
    color: '#94a3b8',
    flex: 1,
  },
  zoneLabelActive: {
    color: '#f8fafc',
    fontWeight: '600',
  },
  zoneRange: {
    fontSize: 12,
    color: '#64748b',
  },
  activeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginLeft: 6,
  },
  activeBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  empty: {
    color: '#64748b',
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
})
