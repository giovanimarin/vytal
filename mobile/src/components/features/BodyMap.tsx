import React, { useState } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  Dimensions,
} from 'react-native'
import Svg, { Path, G, Text as SvgText, Circle } from 'react-native-svg'
import type { MuscleGroup, MuscleRecovery } from '../../types/health'

const { width: SCREEN_WIDTH } = Dimensions.get('window')
const SVG_WIDTH = Math.min(SCREEN_WIDTH - 48, 320)
const SVG_HEIGHT = SVG_WIDTH * 1.6

// Cores por score de recuperação
function recoveryColor(score: number): string {
  if (score >= 70) return '#4CAF50'
  if (score >= 40) return '#FFC107'
  return '#F44336'
}

const MUSCLE_LABEL_PT: Record<MuscleGroup, string> = {
  chest:           'Peitoral',
  front_shoulders: 'Ombros Ant.',
  rear_shoulders:  'Ombros Post.',
  biceps:          'Bíceps',
  triceps:         'Tríceps',
  upper_back:      'Costas Sup.',
  lower_back:      'Lombar',
  core:            'Core',
  glutes:          'Glúteos',
  quads:           'Quadríceps',
  hamstrings:      'Post. Coxa',
  calves:          'Panturrilha',
  hip_flexors:     'Flex. Quadril',
}

// Pontos aproximados no SVG body para cada grupo muscular
// Formato: [cx, cy, rx, ry] elipse (frente | verso)
interface MuscleArea {
  front?: { cx: number; cy: number; rx: number; ry: number }
  back?: { cx: number; cy: number; rx: number; ry: number }
}

const SCALE = SVG_WIDTH / 200

const MUSCLE_AREAS: Record<MuscleGroup, MuscleArea> = {
  chest:           { front: { cx: 100, cy: 110, rx: 28, ry: 18 } },
  front_shoulders: { front: { cx: 100, cy: 95,  rx: 40, ry: 10 } },
  rear_shoulders:  { back:  { cx: 100, cy: 95,  rx: 40, ry: 10 } },
  biceps:          { front: { cx: 100, cy: 135, rx: 32, ry: 10 } },
  triceps:         { back:  { cx: 100, cy: 135, rx: 32, ry: 10 } },
  upper_back:      { back:  { cx: 100, cy: 110, rx: 30, ry: 20 } },
  lower_back:      { back:  { cx: 100, cy: 140, rx: 22, ry: 14 } },
  core:            { front: { cx: 100, cy: 155, rx: 22, ry: 22 } },
  glutes:          { back:  { cx: 100, cy: 175, rx: 28, ry: 16 } },
  quads:           { front: { cx: 100, cy: 200, rx: 28, ry: 24 } },
  hamstrings:      { back:  { cx: 100, cy: 200, rx: 28, ry: 24 } },
  calves:          { back:  { cx: 100, cy: 250, rx: 20, ry: 24 } },
  hip_flexors:     { front: { cx: 100, cy: 178, rx: 22, ry: 14 } },
}

interface BodyMapProps {
  muscles: MuscleRecovery[]
  onMusclePress?: (muscle: MuscleRecovery) => void
}

function BodyFigureFront({ muscles, onPress }: {
  muscles: MuscleRecovery[]
  onPress: (m: MuscleRecovery) => void
}) {
  const scoreMap = Object.fromEntries(muscles.map(m => [m.muscle_group, m]))
  const W = SVG_WIDTH
  const H = SVG_HEIGHT

  const scale = W / 200

  return (
    <Svg width={W} height={H} viewBox="0 0 200 320">
      {/* Silhueta frontal simplificada */}
      {/* Cabeça */}
      <Circle cx={100} cy={40} r={22} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Pescoço */}
      <Path d="M 90 60 L 110 60 L 108 75 L 92 75 Z" fill="#1e293b" />
      {/* Torso */}
      <Path d="M 68 75 L 132 75 L 140 190 L 60 190 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Braço esquerdo */}
      <Path d="M 68 78 L 52 80 L 44 150 L 58 150 L 62 90 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Braço direito */}
      <Path d="M 132 78 L 148 80 L 156 150 L 142 150 L 138 90 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Perna esquerda */}
      <Path d="M 75 190 L 95 190 L 90 290 L 70 290 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Perna direita */}
      <Path d="M 105 190 L 125 190 L 130 290 L 110 290 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />

      {/* Grupos musculares frontais */}
      {(Object.entries(MUSCLE_AREAS) as [MuscleGroup, MuscleArea][])
        .filter(([, area]) => area.front)
        .map(([muscle, area]) => {
          const record = scoreMap[muscle]
          const color = record ? recoveryColor(record.recovery_score) : '#334155'
          const { cx, cy, rx, ry } = area.front!
          return (
            <G key={muscle} onPress={() => record && onPress(record)}>
              <Path
                d={`M ${cx - rx} ${cy} A ${rx} ${ry} 0 0 1 ${cx + rx} ${cy} A ${rx} ${ry} 0 0 1 ${cx - rx} ${cy}`}
                fill={color}
                fillOpacity={0.6}
                stroke={color}
                strokeWidth={1.5}
              />
            </G>
          )
        })}
    </Svg>
  )
}

function BodyFigureBack({ muscles, onPress }: {
  muscles: MuscleRecovery[]
  onPress: (m: MuscleRecovery) => void
}) {
  const scoreMap = Object.fromEntries(muscles.map(m => [m.muscle_group, m]))
  const W = SVG_WIDTH
  const H = SVG_HEIGHT

  return (
    <Svg width={W} height={H} viewBox="0 0 200 320">
      {/* Silhueta posterior */}
      <Circle cx={100} cy={40} r={22} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <Path d="M 90 60 L 110 60 L 108 75 L 92 75 Z" fill="#1e293b" />
      <Path d="M 68 75 L 132 75 L 140 190 L 60 190 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <Path d="M 68 78 L 52 80 L 44 150 L 58 150 L 62 90 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <Path d="M 132 78 L 148 80 L 156 150 L 142 150 L 138 90 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <Path d="M 75 190 L 95 190 L 90 290 L 70 290 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <Path d="M 105 190 L 125 190 L 130 290 L 110 290 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />

      {(Object.entries(MUSCLE_AREAS) as [MuscleGroup, MuscleArea][])
        .filter(([, area]) => area.back)
        .map(([muscle, area]) => {
          const record = scoreMap[muscle]
          const color = record ? recoveryColor(record.recovery_score) : '#334155'
          const { cx, cy, rx, ry } = area.back!
          return (
            <G key={muscle} onPress={() => record && onPress(record)}>
              <Path
                d={`M ${cx - rx} ${cy} A ${rx} ${ry} 0 0 1 ${cx + rx} ${cy} A ${rx} ${ry} 0 0 1 ${cx - rx} ${cy}`}
                fill={color}
                fillOpacity={0.6}
                stroke={color}
                strokeWidth={1.5}
              />
            </G>
          )
        })}
    </Svg>
  )
}

export function BodyMap({ muscles, onMusclePress }: BodyMapProps) {
  const [selected, setSelected] = useState<MuscleRecovery | null>(null)
  const [view, setView] = useState<'front' | 'back'>('front')

  function handlePress(m: MuscleRecovery) {
    setSelected(m)
    onMusclePress?.(m)
  }

  const color = selected ? recoveryColor(selected.recovery_score) : '#3b82f6'

  return (
    <View style={styles.container}>
      {/* Toggle frente/verso */}
      <View style={styles.toggle}>
        <TouchableOpacity
          style={[styles.toggleBtn, view === 'front' && styles.toggleActive]}
          onPress={() => setView('front')}
        >
          <Text style={[styles.toggleText, view === 'front' && styles.toggleTextActive]}>Frente</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.toggleBtn, view === 'back' && styles.toggleActive]}
          onPress={() => setView('back')}
        >
          <Text style={[styles.toggleText, view === 'back' && styles.toggleTextActive]}>Verso</Text>
        </TouchableOpacity>
      </View>

      {/* SVG */}
      <View style={styles.svgContainer}>
        {view === 'front'
          ? <BodyFigureFront muscles={muscles} onPress={handlePress} />
          : <BodyFigureBack  muscles={muscles} onPress={handlePress} />
        }
      </View>

      {/* Legenda */}
      <View style={styles.legend}>
        {[{ color: '#4CAF50', label: '≥ 70% recuperado' },
          { color: '#FFC107', label: '40–69%' },
          { color: '#F44336', label: '< 40%' }].map(item => (
          <View key={item.label} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: item.color }]} />
            <Text style={styles.legendLabel}>{item.label}</Text>
          </View>
        ))}
      </View>

      {/* Bottom sheet do músculo selecionado */}
      <Modal
        visible={!!selected}
        transparent
        animationType="slide"
        onRequestClose={() => setSelected(null)}
      >
        <TouchableOpacity style={styles.overlay} activeOpacity={1} onPress={() => setSelected(null)}>
          <View style={styles.sheet}>
            {selected && (
              <>
                <View style={[styles.sheetIndicator, { backgroundColor: color }]} />
                <Text style={styles.sheetTitle}>
                  {MUSCLE_LABEL_PT[selected.muscle_group as MuscleGroup]}
                </Text>
                <Text style={[styles.sheetScore, { color }]}>
                  {selected.recovery_score.toFixed(0)}% recuperado
                </Text>

                {selected.estimated_full_recovery_at && selected.recovery_score < 100 && (
                  <Text style={styles.sheetMeta}>
                    Recuperação completa: {new Date(selected.estimated_full_recovery_at).toLocaleString('pt-BR', {
                      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                    })}
                  </Text>
                )}

                {!selected.last_workout_id && (
                  <Text style={styles.sheetMeta}>Nenhum treino recente registrado.</Text>
                )}
              </>
            )}
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { gap: 16 },
  toggle: {
    flexDirection: 'row',
    backgroundColor: '#1e293b',
    borderRadius: 10,
    padding: 4,
    alignSelf: 'center',
    gap: 4,
  },
  toggleBtn: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 8 },
  toggleActive: { backgroundColor: '#3b82f6' },
  toggleText: { color: '#64748b', fontWeight: '600', fontSize: 13 },
  toggleTextActive: { color: '#fff' },
  svgContainer: { alignItems: 'center' },
  legend: { flexDirection: 'row', justifyContent: 'center', gap: 16 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendLabel: { color: '#64748b', fontSize: 11 },
  overlay: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' },
  sheet: {
    backgroundColor: '#1e293b',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 28,
    gap: 12,
    minHeight: 200,
  },
  sheetIndicator: { width: 40, height: 4, borderRadius: 2, alignSelf: 'center', marginBottom: 8 },
  sheetTitle: { fontSize: 22, fontWeight: '800', color: '#f8fafc', textAlign: 'center' },
  sheetScore: { fontSize: 36, fontWeight: '800', textAlign: 'center' },
  sheetMeta: { color: '#94a3b8', fontSize: 14, textAlign: 'center' },
})
