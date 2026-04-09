import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native'
import * as WebBrowser from 'expo-web-browser'
import * as Linking from 'expo-linking'
import { useRouter } from 'expo-router'
import { api } from '../src/services/api'
import { useAuthStore } from '../src/store/authStore'

const MVP_USER_ID = 'user-mvp-1'

WebBrowser.maybeCompleteAuthSession()

export default function LoginScreen() {
  const [loading, setLoading] = useState(false)
  const [oauthState, setOauthState] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const router = useRouter()
  const { setUserId, setConnected } = useAuthStore()

  useEffect(() => {
    const subscription = Linking.addEventListener('url', handleOAuthCallback)
    return () => subscription.remove()
  }, [oauthState])

  async function handleGooglePress() {
    setLoading(true)
    setErrorMsg(null)
    try {
      const { data } = await api.get('/connect/google_fit/auth-url', {
        params: { user_id: MVP_USER_ID },
      })
      setOauthState(data.state)
      const popup = (window as any).open?.(data.auth_url, '_blank', 'width=500,height=700')
      if (!popup) {
        ;(window as any).location.href = data.auth_url
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Erro desconhecido'
      setErrorMsg(`Não foi possível iniciar a conexão: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleOAuthCallback(event: { url: string }) {
    const { queryParams } = Linking.parse(event.url)
    const code = queryParams?.code as string | undefined

    if (!code || !oauthState) return

    setLoading(true)
    setErrorMsg(null)
    try {
      const redirectUri = Linking.createURL('oauth/callback')
      await api.post('/connect/google_fit/callback', {
        code,
        state: oauthState,
        redirect_uri: redirectUri,
      })
      setUserId(MVP_USER_ID)
      setConnected(true)
      router.replace('/(dashboard)')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Erro desconhecido'
      setErrorMsg(`Falha ao completar a conexão: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  function handleTestMode() {
    setUserId(MVP_USER_ID)
    setConnected(true)
    router.replace('/(dashboard)')
  }

  return (
    <View style={styles.container}>
      {/* Top: logo + tagline */}
      <View style={styles.hero}>
        <Text style={styles.logo}>Vytal</Text>
        <Text style={styles.tagline}>Entenda sua saúde.</Text>
      </View>

      {/* Middle: login card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Entrar</Text>

        <TouchableOpacity
          style={[styles.googleButton, loading && styles.buttonDisabled]}
          onPress={handleGooglePress}
          disabled={loading}
          activeOpacity={0.85}
        >
          {loading ? (
            <ActivityIndicator color="#1f2937" />
          ) : (
            <View style={styles.googleButtonInner}>
              <View style={styles.googleIconCircle}>
                <Text style={styles.googleIconText}>G</Text>
              </View>
              <Text style={styles.googleButtonText}>Continuar com Google Fit</Text>
            </View>
          )}
        </TouchableOpacity>

        {errorMsg && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{errorMsg}</Text>
          </View>
        )}

        <View style={styles.dividerRow}>
          <View style={styles.dividerLine} />
        </View>

        <Text style={styles.hint}>
          Ainda sem conta? O Vytal usa seus dados do Google Fit.
        </Text>
      </View>

      {/* Bottom: test mode */}
      <TouchableOpacity style={styles.testModeButton} onPress={handleTestMode} activeOpacity={0.7}>
        <Text style={styles.testModeText}>Modo de teste</Text>
      </TouchableOpacity>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
    paddingHorizontal: 24,
    paddingTop: 96,
    paddingBottom: 48,
    justifyContent: 'space-between',
  },
  hero: {
    gap: 8,
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
    gap: 20,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#f8fafc',
  },
  googleButton: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  googleButtonInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  googleIconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#4285F4',
    alignItems: 'center',
    justifyContent: 'center',
  },
  googleIconText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  googleButtonText: {
    color: '#1f2937',
    fontSize: 15,
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
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#334155',
  },
  hint: {
    color: '#64748b',
    fontSize: 13,
    lineHeight: 20,
    textAlign: 'center',
  },
  testModeButton: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  testModeText: {
    color: '#475569',
    fontSize: 13,
    textDecorationLine: 'underline',
  },
})
