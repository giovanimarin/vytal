import React, { useState, useEffect } from 'react'
import {
  View, Text, StyleSheet, TouchableOpacity,
  ActivityIndicator,
} from 'react-native'
import * as WebBrowser from 'expo-web-browser'
import * as Linking from 'expo-linking'
import { useRouter } from 'expo-router'
import { api } from '../src/services/api'
import { getHealthAuthUrl, authErrorMessage } from '../src/services/auth'


WebBrowser.maybeCompleteAuthSession()

export default function ConnectScreen() {
  const [loading, setLoading] = useState(false)
  const [state, setState] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const router = useRouter()

  // Escuta o deep link de retorno do OAuth
  useEffect(() => {
    const subscription = Linking.addEventListener('url', handleOAuthCallback)
    return () => subscription.remove()
  }, [state])

  async function handleConnectPress() {
    setLoading(true)
    setErrorMsg(null)
    try {
      const data = await getHealthAuthUrl('google_fit')
      setState(data.state)
      await WebBrowser.openBrowserAsync(data.auth_url)
    } catch (err: unknown) {
      const msg = authErrorMessage(err)
      setErrorMsg(`Não foi possível iniciar a conexão: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleOAuthCallback(event: { url: string }) {
    const { queryParams } = Linking.parse(event.url)
    const code = queryParams?.code as string | undefined

    if (!code || !state) return

    setLoading(true)
    setErrorMsg(null)
    try {
      const redirectUri = Linking.createURL('oauth/callback')
      await api.post(`/connect/google_fit/callback`, {
        code,
        state,
        redirect_uri: redirectUri,
      })
      router.replace('/(dashboard)')
    } catch (err: unknown) {
      const msg = authErrorMessage(err)
      setErrorMsg(`Falha ao completar a conexão: ${msg}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.logo}>Vytal</Text>
        <Text style={styles.tagline}>
          Entenda sua saúde.{'\n'}Com o relógio que você já tem.
        </Text>

        <View style={styles.featuresContainer}>
          {['Daily Readiness Score', 'Análise do sono', 'Frequência cardíaca', 'Carga de atividade'].map((f) => (
            <View key={f} style={styles.featureRow}>
              <Text style={styles.featureDot}>●</Text>
              <Text style={styles.featureText}>{f}</Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleConnectPress}
          disabled={loading}
        >
          {loading
            ? <ActivityIndicator color="#0f172a" />
            : <Text style={styles.buttonText}>Conectar com Google Fit</Text>
          }
        </TouchableOpacity>

        {errorMsg && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{errorMsg}</Text>
          </View>
        )}



        <Text style={styles.disclaimer}>
          Seus dados ficam no seu dispositivo e nunca são compartilhados.
        </Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
    paddingHorizontal: 24,
    paddingTop: 80,
    paddingBottom: 40,
    justifyContent: 'space-between',
  },
  content: {
    gap: 32,
  },
  logo: {
    fontSize: 48,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: -1,
  },
  tagline: {
    fontSize: 22,
    color: '#94a3b8',
    lineHeight: 32,
    fontWeight: '400',
  },
  featuresContainer: {
    gap: 12,
    paddingTop: 8,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  featureDot: {
    color: '#3b82f6',
    fontSize: 8,
  },
  featureText: {
    color: '#cbd5e1',
    fontSize: 16,
  },
  footer: {
    gap: 16,
  },
  button: {
    backgroundColor: '#3b82f6',
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  devButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  devButtonText: {
    color: '#475569',
    fontSize: 14,
    textDecorationLine: 'underline',
  },
  errorBox: {
    backgroundColor: '#450a0a',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 13,
    lineHeight: 20,
  },
  disclaimer: {
    color: '#475569',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
})
