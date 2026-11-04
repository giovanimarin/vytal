import React, { useState } from 'react'
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native'
import { useRouter } from 'expo-router'
import { api } from '../src/services/api'
import { useAuthStore } from '../src/store/authStore'

const GOALS = [
  { label: 'Perder peso', value: 'lose_weight' },
  { label: 'Ganhar músculo', value: 'gain_muscle' },
  { label: 'Melhorar condicionamento', value: 'improve_endurance' },
  { label: 'Dormir melhor', value: 'better_sleep' },
  { label: 'Bem-estar geral', value: 'general_wellness' },
]

function parseDateInput(raw: string): string | null {
  // Accepts DD/MM/YYYY, returns YYYY-MM-DD or null
  const match = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (!match) return null
  const [, dd, mm, yyyy] = match
  return `${yyyy}-${mm}-${dd}`
}

export default function ProfileSetupScreen() {
  const [birthDate, setBirthDate] = useState('')
  const [weight, setWeight] = useState('')
  const [height, setHeight] = useState('')
  const [goal, setGoal] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const [birthFocused, setBirthFocused] = useState(false)
  const [weightFocused, setWeightFocused] = useState(false)
  const [heightFocused, setHeightFocused] = useState(false)

  const router = useRouter()
  const setProfile = useAuthStore((s) => s.setProfile)
  const currentProfile = useAuthStore((s) => s.userProfile)

  async function handleSubmit() {
    const fields: Record<string, any> = {}

    if (birthDate.trim()) {
      const parsed = parseDateInput(birthDate.trim())
      if (!parsed) {
        setErrorMsg('Data de nascimento inválida. Use o formato DD/MM/AAAA.')
        return
      }
      fields.birth_date = parsed
    }

    if (weight.trim()) {
      const w = parseFloat(weight.replace(',', '.'))
      if (isNaN(w) || w <= 0) {
        setErrorMsg('Peso inválido.')
        return
      }
      fields.weight_kg = w
    }

    if (height.trim()) {
      const h = parseFloat(height.replace(',', '.'))
      if (isNaN(h) || h <= 0) {
        setErrorMsg('Altura inválida.')
        return
      }
      fields.height_cm = h
    }

    if (goal) {
      fields.goal = goal
    }

    if (Object.keys(fields).length === 0) {
      router.replace('/(dashboard)')
      return
    }

    setLoading(true)
    setErrorMsg(null)
    try {
      const { data } = await api.patch('/users/me', fields)
      setProfile({
        user_id: data.user_id ?? currentProfile?.user_id ?? '',
        email: data.email ?? currentProfile?.email ?? '',
        name: data.name ?? currentProfile?.name ?? '',
        birth_date: data.birth_date ?? null,
        weight_kg: data.weight_kg ?? null,
        height_cm: data.height_cm ?? null,
        goal: data.goal ?? null,
      })
      router.replace('/(dashboard)')
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || 'Erro desconhecido'
      setErrorMsg(`Não foi possível salvar: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        style={styles.flex}
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Complete seu perfil</Text>
          <Text style={styles.subtitle}>
            Essas informações ajudam a personalizar seus relatórios. Você pode preencher depois.
          </Text>
        </View>

        {/* Card */}
        <View style={styles.card}>
          {/* Birth date */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Data de nascimento</Text>
            <TextInput
              style={[styles.input, birthFocused && styles.inputFocused]}
              placeholder="DD/MM/AAAA"
              placeholderTextColor="#475569"
              value={birthDate}
              onChangeText={setBirthDate}
              onFocus={() => setBirthFocused(true)}
              onBlur={() => setBirthFocused(false)}
              keyboardType="numbers-and-punctuation"
              returnKeyType="next"
              editable={!loading}
              maxLength={10}
            />
          </View>

          {/* Weight */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Peso (kg)</Text>
            <TextInput
              style={[styles.input, weightFocused && styles.inputFocused]}
              placeholder="Ex: 70"
              placeholderTextColor="#475569"
              value={weight}
              onChangeText={setWeight}
              onFocus={() => setWeightFocused(true)}
              onBlur={() => setWeightFocused(false)}
              keyboardType="decimal-pad"
              returnKeyType="next"
              editable={!loading}
            />
          </View>

          {/* Height */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Altura (cm)</Text>
            <TextInput
              style={[styles.input, heightFocused && styles.inputFocused]}
              placeholder="Ex: 175"
              placeholderTextColor="#475569"
              value={height}
              onChangeText={setHeight}
              onFocus={() => setHeightFocused(true)}
              onBlur={() => setHeightFocused(false)}
              keyboardType="decimal-pad"
              returnKeyType="done"
              editable={!loading}
            />
          </View>

          {/* Goal */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Objetivo principal</Text>
            <View style={styles.pillsContainer}>
              {GOALS.map((g) => (
                <TouchableOpacity
                  key={g.value}
                  style={[styles.pill, goal === g.value && styles.pillSelected]}
                  onPress={() => setGoal(goal === g.value ? null : g.value)}
                  activeOpacity={0.7}
                >
                  <Text
                    style={[styles.pillText, goal === g.value && styles.pillTextSelected]}
                  >
                    {g.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {errorMsg && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMsg}</Text>
            </View>
          )}

          <TouchableOpacity
            style={[styles.primaryButton, loading && styles.buttonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
            activeOpacity={0.85}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryButtonText}>Salvar e continuar</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Skip */}
        <TouchableOpacity
          style={styles.skipButton}
          onPress={() => router.replace('/(dashboard)')}
          activeOpacity={0.7}
        >
          <Text style={styles.skipText}>Pular por agora</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  container: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 72,
    paddingBottom: 48,
    gap: 24,
  },
  header: {
    gap: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 15,
    color: '#94a3b8',
    lineHeight: 22,
  },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 20,
    padding: 24,
    gap: 16,
  },
  fieldGroup: {
    gap: 8,
  },
  label: {
    fontSize: 13,
    color: '#94a3b8',
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#0f172a',
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: '#334155',
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: '#f8fafc',
  },
  inputFocused: {
    borderColor: '#3b82f6',
  },
  pillsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  pill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: '#334155',
    backgroundColor: '#0f172a',
  },
  pillSelected: {
    borderColor: '#3b82f6',
    backgroundColor: '#1d4ed8',
  },
  pillText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '500',
  },
  pillTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
  errorBox: {
    backgroundColor: '#450a0a',
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 13,
    lineHeight: 20,
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
    marginTop: 4,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  skipButton: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  skipText: {
    color: '#475569',
    fontSize: 14,
    textDecorationLine: 'underline',
  },
})
