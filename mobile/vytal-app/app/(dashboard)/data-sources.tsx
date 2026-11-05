import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Linking,
} from 'react-native'
import { useRouter } from 'expo-router'
import { api } from '../../src/services/api'
import { getHealthAuthUrl, authErrorMessage } from '../../src/services/auth'
import { useAuthStore } from '../../src/store/authStore'

interface DataSource {
  id: string
  name: string
  description: string
  icon: string
  available: boolean
}

const DATA_SOURCES: DataSource[] = [
  {
    id: 'google_fit',
    name: 'Google Fit',
    description: 'Acesso a sono, frequência cardíaca, atividade e passos',
    icon: '🏃',
    available: true,
  },
  {
    id: 'apple_health',
    name: 'Apple Health',
    description: 'Em breve',
    icon: '🍎',
    available: false,
  },
  {
    id: 'fitbit',
    name: 'Fitbit',
    description: 'Em breve',
    icon: '⌚',
    available: false,
  },
  {
    id: 'samsung_health',
    name: 'Samsung Health',
    description: 'Em breve',
    icon: '📱',
    available: false,
  },
]

export default function DataSourcesScreen() {
  const router = useRouter()
  const userId = useAuthStore((s) => s.userId)

  const [connectedSources, setConnectedSources] = useState<Set<string>>(new Set())
  const [loadingSource, setLoadingSource] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Check Google Fit connection status on mount
  useEffect(() => {
    checkConnectionStatus()
  }, [])

  async function checkConnectionStatus() {
    try {
      const { data } = await api.get('/connect/google_fit/status', {
        params: { user_id: userId },
      })
      if (data?.connected) {
        setConnectedSources((prev) => new Set(prev).add('google_fit'))
      }
    } catch {
      // Endpoint may not exist yet — ignore silently
    }
  }

  async function handleConnect(source: DataSource) {
    if (!source.available || loadingSource) return
    setErrorMsg(null)

    if (source.id === 'google_fit') {
      await connectGoogleFit()
    }
  }

  async function handleDisconnect(sourceId: string) {
    if (loadingSource) return
    setLoadingSource(sourceId)
    setErrorMsg(null)
    try {
      await api.delete(`/connect/${sourceId}`, {
        params: { user_id: userId },
      })
      setConnectedSources((prev) => {
        const next = new Set(prev)
        next.delete(sourceId)
        return next
      })
    } catch (err: unknown) {
      const msg = authErrorMessage(err)
      setErrorMsg(`Não foi possível desconectar: ${msg}`)
    } finally {
      setLoadingSource(null)
    }
  }

  async function connectGoogleFit() {
    setLoadingSource('google_fit')
    setErrorMsg(null)
    try {
      const data = await getHealthAuthUrl('google_fit')
      // Open OAuth URL in system browser
      await Linking.openURL(data.auth_url)
    } catch (err: unknown) {
      const msg = authErrorMessage(err)
      setErrorMsg(`Não foi possível iniciar a conexão: ${msg}`)
    } finally {
      setLoadingSource(null)
    }
  }

  const connected = DATA_SOURCES.filter((s) => connectedSources.has(s.id))
  const available = DATA_SOURCES.filter((s) => !connectedSources.has(s.id))

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
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
        <Text style={styles.screenTitle}>Fontes de Dados</Text>
        <Text style={styles.screenSubtitle}>
          Conecte seus dispositivos e apps de saúde para enriquecer seus relatórios.
        </Text>
      </View>

      {errorMsg && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{errorMsg}</Text>
        </View>
      )}

      {/* Connected sources */}
      {connected.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Conectadas</Text>
          <View style={styles.sourceList}>
            {connected.map((source) => (
              <SourceCard
                key={source.id}
                source={source}
                isConnected
                isLoading={loadingSource === source.id}
                onDisconnect={() => handleDisconnect(source.id)}
              />
            ))}
          </View>
        </View>
      )}

      {/* Available sources */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>Disponíveis</Text>
        <View style={styles.sourceList}>
          {available.map((source) => (
            <SourceCard
              key={source.id}
              source={source}
              isConnected={false}
              isLoading={loadingSource === source.id}
              onConnect={() => handleConnect(source)}
            />
          ))}
        </View>
      </View>
    </ScrollView>
  )
}

interface SourceCardProps {
  source: DataSource
  isConnected: boolean
  isLoading: boolean
  onConnect?: () => void
  onDisconnect?: () => void
}

function SourceCard({ source, isConnected, isLoading, onConnect, onDisconnect }: SourceCardProps) {
  return (
    <View style={cardStyles.container}>
      <View style={cardStyles.iconWrap}>
        <Text style={cardStyles.icon}>{source.icon}</Text>
      </View>
      <View style={cardStyles.info}>
        <Text style={cardStyles.name}>{source.name}</Text>
        <Text style={cardStyles.description}>{source.description}</Text>
      </View>
      <View style={cardStyles.actionWrap}>
        {isConnected ? (
          <View style={cardStyles.connectedBadge}>
            <Text style={cardStyles.connectedCheck}>✓</Text>
          </View>
        ) : null}
        {isConnected ? (
          <TouchableOpacity
            style={cardStyles.disconnectButton}
            onPress={onDisconnect}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <ActivityIndicator color="#ef4444" size="small" />
            ) : (
              <Text style={cardStyles.disconnectText}>Desconectar</Text>
            )}
          </TouchableOpacity>
        ) : source.available ? (
          <TouchableOpacity
            style={cardStyles.connectButton}
            onPress={onConnect}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={cardStyles.connectText}>Conectar</Text>
            )}
          </TouchableOpacity>
        ) : (
          <View style={cardStyles.soonBadge}>
            <Text style={cardStyles.soonText}>Em breve</Text>
          </View>
        )}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    paddingHorizontal: 24,
    paddingTop: 56,
    paddingBottom: 48,
    gap: 24,
  },
  topBar: {
    gap: 8,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    alignSelf: 'flex-start',
    marginBottom: 8,
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
  screenSubtitle: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
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
  section: {
    gap: 12,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  sourceList: {
    gap: 10,
  },
})

const cardStyles = StyleSheet.create({
  container: {
    backgroundColor: '#1e293b',
    borderRadius: 14,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#0f172a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: 22,
  },
  info: {
    flex: 1,
    gap: 3,
  },
  name: {
    fontSize: 15,
    fontWeight: '600',
    color: '#f8fafc',
  },
  description: {
    fontSize: 12,
    color: '#64748b',
    lineHeight: 17,
  },
  actionWrap: {
    alignItems: 'flex-end',
    gap: 4,
  },
  connectedBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#16a34a',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  connectedCheck: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  connectButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    minWidth: 80,
    alignItems: 'center',
  },
  connectText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  disconnectButton: {
    borderWidth: 1,
    borderColor: '#ef4444',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    minWidth: 100,
    alignItems: 'center',
  },
  disconnectText: {
    color: '#ef4444',
    fontSize: 13,
    fontWeight: '600',
  },
  soonBadge: {
    backgroundColor: '#1e3a5f',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  soonText: {
    color: '#60a5fa',
    fontSize: 12,
    fontWeight: '500',
  },
})
