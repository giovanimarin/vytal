import React, { useState, useEffect } from 'react'
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
import { useUserProfile, useUpdateProfile } from '../../src/hooks/useProfile'
import { useAuthStore } from '../../src/store/authStore'

const GOALS = [
  { label: 'Perder peso', value: 'lose_weight' },
  { label: 'Ganhar músculo', value: 'gain_muscle' },
  { label: 'Melhorar condicionamento', value: 'improve_endurance' },
  { label: 'Dormir melhor', value: 'better_sleep' },
  { label: 'Bem-estar geral', value: 'general_wellness' },
]

function formatDateToDisplay(iso: string | null | undefined): string {
  if (!iso) return ''
  const match = iso.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return ''
  const [, yyyy, mm, dd] = match
  return `${dd}/${mm}/${yyyy}`
}

function parseDateInput(raw: string): string | null {
  const match = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (!match) return null
  const [, dd, mm, yyyy] = match
  return `${yyyy}-${mm}-${dd}`
}

export default function ProfileScreen() {
  const router = useRouter()
  const userProfile = useAuthStore((s) => s.userProfile)
  const { data: remoteProfile, isLoading } = useUserProfile()
  const { mutate: updateProfile, isPending: isSaving } = useUpdateProfile()

  const profile = remoteProfile ?? userProfile

  const [name, setName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [weight, setWeight] = useState('')
  const [height, setHeight] = useState('')
  const [goal, setGoal] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const [nameFocused, setNameFocused] = useState(false)
  const [birthFocused, setBirthFocused] = useState(false)
  const [weightFocused, setWeightFocused] = useState(false)
  const [heightFocused, setHeightFocused] = useState(false)

  // Populate fields once profile is loaded
  useEffect(() => {
    if (profile) {
      setName(profile.name ?? '')
      setBirthDate(formatDateToDisplay(profile.birth_date))
      setWeight(profile.weight_kg != null ? String(profile.weight_kg) : '')
      setHeight(profile.height_cm != null ? String(profile.height_cm) : '')
      setGoal(profile.goal ?? null)
    }
  }, [profile?.user_id])

  function handleSave() {
    const fields: Record<string, any> = {}

    if (!name.trim()) {
      setErrorMsg('O nome não pode estar vazio.')
      return
    }
    fields.name = name.trim()

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

    setErrorMsg(null)
    setSuccessMsg(null)

    updateProfile(fields, {
      onSuccess: () => {
        setSuccessMsg('Perfil atualizado com sucesso!')
      },
      onError: (err: any) => {
        const msg =
          err?.response?.data?.detail || err?.message || 'Erro desconhecido'
        setErrorMsg(`Não foi possível salvar: ${msg}`)
      },
    })
  }

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator color="#3b82f6" size="large" />
      </View>
    )
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
        <View style={styles.topBar}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            activeOpacity={0.7}
          >
            <Text style={styles.backIcon}>←</Text>
            <Text style={styles.backText}>Voltar</Text>
          </TouchableOpacity>
          <Text style={styles.screenTitle}>Meu Perfil</Text>
        </View>

        {/* Read-only identity */}
        <View style={styles.identityCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarLetter}>
              {profile?.name?.charAt(0)?.toUpperCase() ?? '?'}
            </Text>
          </View>
          <View>
            <Text style={styles.identityName}>{profile?.name ?? '—'}</Text>
            <Text style={styles.identityEmail}>{profile?.email ?? '—'}</Text>
          </View>
        </View>

        {/* Editable fields */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>Informações pessoais</Text>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Nome</Text>
            <TextInput
              style={[styles.input, nameFocused && styles.inputFocused]}
              value={name}
              onChangeText={setName}
              onFocus={() => setNameFocused(true)}
              onBlur={() => setNameFocused(false)}
              autoCapitalize="words"
              returnKeyType="next"
              editable={!isSaving}
            />
          </View>

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
              editable={!isSaving}
              maxLength={10}
            />
          </View>

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
              editable={!isSaving}
            />
          </View>

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
              editable={!isSaving}
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

          {successMsg && (
            <View style={styles.successBox}>
              <Text style={styles.successText}>{successMsg}</Text>
            </View>
          )}

          <TouchableOpacity
            style={[styles.primaryButton, isSaving && styles.buttonDisabled]}
            onPress={handleSave}
            disabled={isSaving}
            activeOpacity={0.85}
          >
            {isSaving ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryButtonText}>Salvar alterações</Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0f172a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  container: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 56,
    paddingBottom: 48,
    gap: 20,
  },
  topBar: {
    gap: 16,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    alignSelf: 'flex-start',
  },
  backIcon: {
    fontSize: 18,
    color: '#94a3b8',
  },
  backText: {
    fontSize: 15,
    color: '#94a3b8',
    fontWeight: '500',
  },
  screenTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: -0.5,
  },
  identityCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#1d4ed8',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarLetter: {
    fontSize: 22,
    fontWeight: '700',
    color: '#fff',
  },
  identityName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  identityEmail: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 2,
  },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 20,
    padding: 24,
    gap: 16,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  fieldGroup: {
    gap: 6,
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
  successBox: {
    backgroundColor: '#052e16',
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: '#16a34a',
  },
  successText: {
    color: '#86efac',
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
})
