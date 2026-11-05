import React, { useState } from 'react'
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet, ScrollView } from 'react-native'
import * as SecureStore from 'expo-secure-store'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { getSessionVersion, useAuthStore } from '../store/authStore'
import { connectHealthConnect, healthConnectReader } from './native'
import { Checkpoint, synchronize } from './sync'
import { Category, ImportedRecord, RECORD_TYPES } from './types'

const LABELS: Record<string, string> = { ExerciseSession: 'Exercício', Steps: 'Passos', Distance: 'Distância',
  ActiveCaloriesBurned: 'Calorias ativas', TotalCaloriesBurned: 'Calorias totais', HeartRate: 'Frequência cardíaca',
  RestingHeartRate: 'FC em repouso', SleepSession: 'Sono', Weight: 'Peso', Speed: 'Velocidade', ElevationGained: 'Elevação ganha' }
export function HealthConnectPanel({ account }: { account: string }) {
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('Não conectado. Requer development build Android, não Expo Go.')
  const [category, setCategory] = useState<Category | ''>('')
  const [records, setRecords] = useState<ImportedRecord[]>([])
  const query = useQueryClient()
  async function sync(connect: boolean) {
    if (busy) return
    setBusy(true)
    const version = getSessionVersion()
    const stillOwner = () => useAuthStore.getState().userId === account && getSessionVersion() === version
    const key = 'hc_checkpoint_' + account
    const bound = { _sessionVersion: version, _accountId: account }
    const warnings: string[] = []
    try {
      if (connect) await connectHealthConnect()
      let installation = await SecureStore.getItemAsync('hc_installation')
      if (!installation) {
        installation = Date.now().toString(36) + '-' + Math.random().toString(36).slice(2)
        await SecureStore.setItemAsync('hc_installation', installation)
      }
      const report = await synchronize({ reader: healthConnectReader, stillOwner,
        async load() { const raw = await SecureStore.getItemAsync(key); return raw ? JSON.parse(raw) as Checkpoint : null },
        async save(value) { if (!stillOwner()) throw new Error('Session changed'); if (value) await SecureStore.setItemAsync(key, JSON.stringify(value)); else await SecureStore.deleteItemAsync(key) },
        async upload(items, deleted) {
          // Bound request identity prevents an account switch between the check and interceptor.
          const result = await api.post('/health-connect/records', { installation_id: installation, records: items, deleted }, { headers: {}, ...bound })
          warnings.push(...(result.data.projection_warnings || []))
        },
      })
      if (!stillOwner()) return
      const { data } = await api.get('/health-connect/records', { headers: {}, ...bound, params: category ? { category } : undefined })
      if (!stillOwner()) return
      setRecords(data.records)
      setStatus(report.state === 'denied' ? 'Permissão negada: conceda leitura na Conexão Saúde.'
        : report.state === 'expired' ? 'Histórico incremental expirou. Sincronize novamente para reler a janela disponível.'
        : report.state === 'partial' || warnings.length ? `Importação parcial. Categorias sem acesso/dados válidos: ${[...report.failed, ...warnings].join(', ') || 'verifique permissões'}. Toque novamente para tentar.`
        : data.displayed === 0 ? 'Sem dados disponíveis. Confirme se Garmin Connect gravou registros na Conexão Saúde.'
        : `Sincronização concluída. ${data.displayed} registros importados de Health Connect exibidos (até 200 recentes).`)
      await query.invalidateQueries()
    } catch {
      if (stillOwner()) setStatus('Falha na importação. Verifique development build, disponibilidade/permissões do Health Connect e conexão Wi-Fi com o backend local. Tente novamente; o cursor não avança sem confirmação.')
    } finally { setBusy(false) }
  }
  async function rescan() {
    if (busy) return
    try { await SecureStore.deleteItemAsync('hc_checkpoint_' + account) }
    catch { setStatus('Não foi possível reiniciar a sincronização local.'); return }
    await sync(false)
  }
  async function filter(next: Category | '') {
    setCategory(next)
    const version = getSessionVersion()
    try {
      const { data } = await api.get('/health-connect/records', { headers: {}, _sessionVersion: version, _accountId: account, params: next ? { category: next } : undefined } as Parameters<typeof api.get>[1])
      if (useAuthStore.getState().userId === account && getSessionVersion() === version) setRecords(data.records)
    } catch { setStatus('Não foi possível consultar os registros locais.') }
  }
  return <View style={styles.card}>
    <Text style={styles.title}>Conexão Saúde (Health Connect)</Text>
    <Text style={styles.text}>Leitura local opcional. Dados disponíveis de Garmin e outros apps, sem credenciais Garmin. O Vytal guarda os registros no backend SQLite da sua conta via Wi-Fi; não envia ao Google Cloud. Revogue leitura nas configurações da Conexão Saúde. Dados simulados não são importados por este conector. A leitura inicial cobre 30 dias; registros mais antigos retidos não são revalidados numa releitura.</Text>
    <Text accessibilityLiveRegion="polite" style={styles.text}>{status}</Text>
    {busy ? <ActivityIndicator /> : <View>
      <TouchableOpacity accessibilityRole="button" onPress={() => sync(true)} style={styles.button}><Text style={styles.text}>Conectar / conceder leitura</Text></TouchableOpacity>
      <TouchableOpacity accessibilityRole="button" onPress={rescan} style={styles.button}><Text style={styles.text}>Reler janela inicial (30 dias)</Text></TouchableOpacity>
      <TouchableOpacity accessibilityRole="button" onPress={() => sync(false)} style={styles.button}><Text style={styles.text}>Sincronizar novamente</Text></TouchableOpacity>
    </View>}
    <ScrollView horizontal><TouchableOpacity onPress={() => filter('')} style={styles.button}><Text style={styles.text}>Todos</Text></TouchableOpacity>
      {RECORD_TYPES.map(type => <TouchableOpacity key={type} onPress={() => filter(type)} style={styles.button}><Text style={styles.text}>{LABELS[type]}</Text></TouchableOpacity>)}
    </ScrollView>
    {records.map((record, index) => <View key={record.origin + record.id + index} style={styles.row}>
      <Text style={styles.title}>{LABELS[record.category] || record.category} · importado / Health Connect</Text>
      <Text style={styles.text}>{new Date(record.start).toLocaleString()} — {new Date(record.end).toLocaleString()}</Text>
      <Text selectable style={styles.text}>Origem: {record.origin === 'com.garmin.android.apps.connectmobile' ? 'Garmin Connect · ' : ''}{record.origin} · ID: {record.id}</Text>
      <Text style={styles.text}>Espelhamentos retidos: {record.aliases?.map(a => a.origin).join(', ') || record.origin}</Text>
      <Text selectable style={styles.text}>{JSON.stringify(Array.isArray(record.values.samples) ? { ...record.values, samples: record.values.samples.slice(0, 3), sampleCount: record.values.samples.length } : record.values)}</Text>
    </View>)}
  </View>
}
const styles = StyleSheet.create({ card: { backgroundColor: '#1e293b', padding: 16, borderRadius: 12, gap: 10 },
  title: { color: '#f8fafc', fontWeight: '700' }, text: { color: '#cbd5e1', fontSize: 13 },
  button: { backgroundColor: '#1d4ed8', padding: 12, borderRadius: 8, marginVertical: 4 }, row: { borderTopWidth: 1, borderColor: '#475569', paddingVertical: 12, gap: 4 } })
