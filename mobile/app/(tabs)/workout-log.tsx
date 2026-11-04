import React, { useState } from 'react'
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, ActivityIndicator, Alert, Modal, FlatList,
} from 'react-native'
import { useAuthStore } from '../../src/store/authStore'
import {
  useRegisterWorkout,
  useExerciseCatalog,
  useMuscleRecovery,
  useMuscleSuggestion,
} from '../../src/hooks/useWorkouts'
import { BodyMap } from '../../src/components/features/BodyMap'
import type { WorkoutModality, WorkoutIntensity, ExerciseCatalogItem } from '../../src/types/health'

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

const MODALITIES: { key: WorkoutModality; label: string; emoji: string }[] = [
  { key: 'crossfit', label: 'Crossfit', emoji: '🏋️' },
  { key: 'corrida',  label: 'Corrida',  emoji: '🏃' },
  { key: 'academia', label: 'Academia', emoji: '💪' },
  { key: 'tenis',    label: 'Tênis',    emoji: '🎾' },
  { key: 'pilates',  label: 'Pilates',  emoji: '🧘' },
  { key: 'surfe',    label: 'Surfe',    emoji: '🏄' },
  { key: 'yoga',     label: 'Yoga',     emoji: '🌿' },
  { key: 'ciclismo', label: 'Ciclismo', emoji: '🚴' },
]

const INTENSITIES: { key: WorkoutIntensity; label: string; color: string }[] = [
  { key: 'leve',     label: 'Leve',     color: '#4CAF50' },
  { key: 'moderado', label: 'Moderado', color: '#FFC107' },
  { key: 'intenso',  label: 'Intenso',  color: '#F44336' },
]

export default function WorkoutLogScreen() {
  const userId = useAuthStore((s) => s.userId)
  const today = todayISO()

  const [tab, setTab] = useState<'register' | 'bodymap'>('register')
  const [modality, setModality] = useState<WorkoutModality>('academia')
  const [intensity, setIntensity] = useState<WorkoutIntensity>('moderado')
  const [duration, setDuration] = useState('45')
  const [notes, setNotes] = useState('')
  const [freeText, setFreeText] = useState('')
  const [selectedExercises, setSelectedExercises] = useState<ExerciseCatalogItem[]>([])
  const [catalogVisible, setCatalogVisible] = useState(false)

  const register = useRegisterWorkout()
  const { data: catalog } = useExerciseCatalog()
  const { data: recoveryData } = useMuscleRecovery(userId, today)
  const { data: suggestion } = useMuscleSuggestion(userId, today)

  const showExercisePicker = modality === 'academia' || modality === 'crossfit'

  async function handleSubmit() {
    if (!userId) return
    const dur = parseInt(duration, 10)
    if (!dur || dur <= 0) {
      Alert.alert('Erro', 'Informe a duração em minutos.')
      return
    }

    try {
      await register.mutateAsync({
        user_id: userId,
        modality,
        intensity,
        duration_min: dur,
        date: today,
        notes: notes || undefined,
        exercises: selectedExercises.map(e => ({ name: e.name })),
        free_text: freeText || undefined,
      })
      Alert.alert('Treino registrado!', 'Sua recuperação muscular foi atualizada.')
      setNotes('')
      setFreeText('')
      setSelectedExercises([])
      setTab('bodymap')
    } catch {
      Alert.alert('Erro', 'Não foi possível registrar o treino.')
    }
  }

  function toggleExercise(ex: ExerciseCatalogItem) {
    setSelectedExercises(prev =>
      prev.find(e => e.name === ex.name)
        ? prev.filter(e => e.name !== ex.name)
        : [...prev, ex]
    )
  }

  return (
    <View style={styles.root}>
      {/* Tab bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, tab === 'register' && styles.tabActive]}
          onPress={() => setTab('register')}
        >
          <Text style={[styles.tabText, tab === 'register' && styles.tabTextActive]}>
            Registrar Treino
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, tab === 'bodymap' && styles.tabActive]}
          onPress={() => setTab('bodymap')}
        >
          <Text style={[styles.tabText, tab === 'bodymap' && styles.tabTextActive]}>
            Body Map
          </Text>
        </TouchableOpacity>
      </View>

      {tab === 'register' ? (
        <ScrollView style={styles.container} contentContainerStyle={styles.content}>
          <Text style={styles.sectionTitle}>Modalidade</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pills}>
            {MODALITIES.map(m => (
              <TouchableOpacity
                key={m.key}
                style={[styles.pill, modality === m.key && styles.pillActive]}
                onPress={() => setModality(m.key)}
              >
                <Text style={styles.pillEmoji}>{m.emoji}</Text>
                <Text style={[styles.pillText, modality === m.key && styles.pillTextActive]}>
                  {m.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <Text style={styles.sectionTitle}>Intensidade</Text>
          <View style={styles.intensityRow}>
            {INTENSITIES.map(i => (
              <TouchableOpacity
                key={i.key}
                style={[styles.intensityBtn,
                  intensity === i.key && { backgroundColor: i.color + '22', borderColor: i.color }]}
                onPress={() => setIntensity(i.key)}
              >
                <Text style={[styles.intensityText, intensity === i.key && { color: i.color }]}>
                  {i.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.sectionTitle}>Duração (min)</Text>
          <TextInput
            style={styles.input}
            keyboardType="numeric"
            value={duration}
            onChangeText={setDuration}
            placeholderTextColor="#475569"
            placeholder="45"
          />

          {showExercisePicker && (
            <>
              <Text style={styles.sectionTitle}>Exercícios</Text>
              <TouchableOpacity style={styles.catalogBtn} onPress={() => setCatalogVisible(true)}>
                <Text style={styles.catalogBtnText}>
                  {selectedExercises.length > 0
                    ? `${selectedExercises.length} exercício(s) selecionado(s)`
                    : 'Selecionar exercícios'}
                </Text>
              </TouchableOpacity>
              <Text style={styles.orText}>ou descreva em texto livre:</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={freeText}
                onChangeText={setFreeText}
                placeholder="Ex: Fiz supino, agachamento e remada..."
                placeholderTextColor="#475569"
                multiline
                numberOfLines={3}
              />
            </>
          )}

          <Text style={styles.sectionTitle}>Notas (opcional)</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={notes}
            onChangeText={setNotes}
            placeholder="Como foi o treino?"
            placeholderTextColor="#475569"
            multiline
            numberOfLines={3}
          />

          <TouchableOpacity
            style={[styles.submitBtn, register.isPending && styles.submitDisabled]}
            onPress={handleSubmit}
            disabled={register.isPending}
          >
            {register.isPending
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.submitText}>Registrar Treino</Text>
            }
          </TouchableOpacity>
        </ScrollView>
      ) : (
        <ScrollView style={styles.container} contentContainerStyle={styles.content}>
          {suggestion?.suggestion && (
            <View style={styles.suggestionCard}>
              <Text style={styles.suggestionTitle}>Sugestão do dia</Text>
              <Text style={styles.suggestionText}>{suggestion.message}</Text>
            </View>
          )}

          {recoveryData?.muscles ? (
            <BodyMap muscles={recoveryData.muscles} />
          ) : (
            <View style={styles.center}>
              <ActivityIndicator color="#3b82f6" />
            </View>
          )}
        </ScrollView>
      )}

      {/* Modal catálogo de exercícios */}
      <Modal visible={catalogVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Exercícios</Text>
              <TouchableOpacity onPress={() => setCatalogVisible(false)}>
                <Text style={styles.modalClose}>Fechar</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={catalog ?? []}
              keyExtractor={item => item.name}
              renderItem={({ item }) => {
                const selected = selectedExercises.some(e => e.name === item.name)
                return (
                  <TouchableOpacity
                    style={[styles.exerciseItem, selected && styles.exerciseItemSelected]}
                    onPress={() => toggleExercise(item)}
                  >
                    <Text style={[styles.exerciseName, selected && styles.exerciseNameSelected]}>
                      {item.name}
                    </Text>
                    <Text style={styles.exerciseMuscles}>
                      {item.primary.join(', ')}
                    </Text>
                  </TouchableOpacity>
                )
              }}
            />
          </View>
        </View>
      </Modal>
    </View>
  )
}

const styles = StyleSheet.create({
  root:           { flex: 1, backgroundColor: '#0f172a' },
  tabBar:         { flexDirection: 'row', backgroundColor: '#1e293b', padding: 4, gap: 4 },
  tab:            { flex: 1, paddingVertical: 10, alignItems: 'center', borderRadius: 8 },
  tabActive:      { backgroundColor: '#3b82f6' },
  tabText:        { color: '#64748b', fontWeight: '600' },
  tabTextActive:  { color: '#fff' },
  container:      { flex: 1 },
  content:        { padding: 24, paddingBottom: 48, gap: 12 },
  center:         { alignItems: 'center', paddingVertical: 40 },
  sectionTitle:   { fontSize: 13, fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5 },
  pills:          { flexDirection: 'row' },
  pill: {
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginRight: 8,
    gap: 4,
  },
  pillActive:     { backgroundColor: '#3b82f6' },
  pillEmoji:      { fontSize: 20 },
  pillText:       { color: '#64748b', fontSize: 12, fontWeight: '600' },
  pillTextActive: { color: '#fff' },
  intensityRow:   { flexDirection: 'row', gap: 10 },
  intensityBtn: {
    flex: 1, paddingVertical: 12, alignItems: 'center',
    borderRadius: 12, borderWidth: 1.5, borderColor: '#334155',
  },
  intensityText:  { color: '#94a3b8', fontWeight: '700' },
  input: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 14,
    color: '#f8fafc',
    fontSize: 15,
  },
  textArea:       { minHeight: 80, textAlignVertical: 'top' },
  catalogBtn: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  catalogBtnText: { color: '#3b82f6', fontWeight: '600' },
  orText:         { color: '#475569', textAlign: 'center', fontSize: 13 },
  submitBtn: {
    backgroundColor: '#3b82f6',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  submitDisabled: { opacity: 0.6 },
  submitText:     { color: '#fff', fontWeight: '700', fontSize: 15 },
  suggestionCard: {
    backgroundColor: '#0f3460',
    borderRadius: 16,
    padding: 16,
    gap: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6',
  },
  suggestionTitle: { color: '#93c5fd', fontWeight: '700', fontSize: 13, textTransform: 'uppercase' },
  suggestionText:  { color: '#e2e8f0', fontSize: 14, lineHeight: 21 },
  modalOverlay:    { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalContent:    { backgroundColor: '#1e293b', borderTopLeftRadius: 24, borderTopRightRadius: 24, maxHeight: '75%' },
  modalHeader:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, borderBottomWidth: 1, borderBottomColor: '#334155' },
  modalTitle:      { color: '#f8fafc', fontSize: 18, fontWeight: '700' },
  modalClose:      { color: '#3b82f6', fontWeight: '600' },
  exerciseItem:    { padding: 16, borderBottomWidth: 1, borderBottomColor: '#0f172a' },
  exerciseItemSelected: { backgroundColor: '#1d4ed822' },
  exerciseName:    { color: '#f8fafc', fontWeight: '600' },
  exerciseNameSelected: { color: '#60a5fa' },
  exerciseMuscles: { color: '#64748b', fontSize: 12, marginTop: 3 },
})
