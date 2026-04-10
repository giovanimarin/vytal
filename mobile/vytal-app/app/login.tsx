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

export default function LoginScreen() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [emailFocused, setEmailFocused] = useState(false)
  const [passwordFocused, setPasswordFocused] = useState(false)

  const router = useRouter()
  const setTokens = useAuthStore((s) => s.setTokens)
  const setProfile = useAuthStore((s) => s.setProfile)

  async function handleLogin() {
    if (!email.trim() || !password) {
      setErrorMsg('Preencha e-mail e senha.')
      return
    }
    setLoading(true)
    setErrorMsg(null)
    try {
      const { data } = await api.post('/auth/login', { email: email.trim(), password })
      setTokens(data.access_token, data.refresh_token)
      if (data.user) {
        setProfile({
          user_id: data.user.user_id,
          email: data.user.email,
          name: data.user.name,
          birth_date: data.user.birth_date ?? null,
          weight_kg: data.user.weight_kg ?? null,
          height_cm: data.user.height_cm ?? null,
          goal: data.user.goal ?? null,
        })
      }
      router.replace('/(dashboard)')
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || 'Erro desconhecido'
      setErrorMsg(`Não foi possível entrar: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  function handleTestMode() {
    const setUserId = useAuthStore.getState().setUserId
    const setConnected = useAuthStore.getState().setConnected
    setUserId('user-mvp-1')
    setConnected(true)
    router.replace('/(dashboard)')
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
        {/* Hero */}
        <View style={styles.hero}>
          <Text style={styles.logo}>Vytal</Text>
          <Text style={styles.tagline}>Entenda sua saúde.</Text>
        </View>

        {/* Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Entrar</Text>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>E-mail</Text>
            <TextInput
              style={[styles.input, emailFocused && styles.inputFocused]}
              placeholder="seu@email.com"
              placeholderTextColor="#475569"
              value={email}
              onChangeText={setEmail}
              onFocus={() => setEmailFocused(true)}
              onBlur={() => setEmailFocused(false)}
              autoCapitalize="none"
              keyboardType="email-address"
              autoCorrect={false}
              returnKeyType="next"
              editable={!loading}
            />
          </View>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Senha</Text>
            <TextInput
              style={[styles.input, passwordFocused && styles.inputFocused]}
              placeholder="••••••••"
              placeholderTextColor="#475569"
              value={password}
              onChangeText={setPassword}
              onFocus={() => setPasswordFocused(true)}
              onBlur={() => setPasswordFocused(false)}
              secureTextEntry
              returnKeyType="done"
              onSubmitEditing={handleLogin}
              editable={!loading}
            />
          </View>

          {errorMsg && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMsg}</Text>
            </View>
          )}

          <TouchableOpacity
            style={[styles.primaryButton, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.85}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryButtonText}>Entrar</Text>
            )}
          </TouchableOpacity>

          <View style={styles.dividerRow}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>ou</Text>
            <View style={styles.dividerLine} />
          </View>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => router.push('/register')}
            activeOpacity={0.8}
          >
            <Text style={styles.secondaryButtonText}>Criar conta</Text>
          </TouchableOpacity>
        </View>

        {/* Test mode */}
        <TouchableOpacity style={styles.testModeButton} onPress={handleTestMode} activeOpacity={0.7}>
          <Text style={styles.testModeText}>Modo de teste</Text>
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
    paddingTop: 96,
    paddingBottom: 48,
    justifyContent: 'space-between',
  },
  hero: {
    gap: 8,
    marginBottom: 40,
  },
  logo: {
    fontSize: 52,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: -1.5,
  },
  tagline: {
    fontSize: 20,
    color: '#94a3b8',
    fontWeight: '400',
  },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 20,
    padding: 24,
    gap: 16,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#f8fafc',
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
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#334155',
  },
  dividerText: {
    color: '#475569',
    fontSize: 13,
  },
  secondaryButton: {
    borderWidth: 1.5,
    borderColor: '#334155',
    borderRadius: 12,
    paddingVertical: 13,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#94a3b8',
    fontSize: 15,
    fontWeight: '600',
  },
  testModeButton: {
    alignItems: 'center',
    paddingVertical: 8,
    marginTop: 24,
  },
  testModeText: {
    color: '#475569',
    fontSize: 13,
    textDecorationLine: 'underline',
  },
})
