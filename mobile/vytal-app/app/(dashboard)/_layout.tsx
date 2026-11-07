import React, { useState } from 'react'
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native'
import { Stack, useRouter } from 'expo-router'
import { SideMenu } from '../../src/components/ui/SideMenu'
import { SyncStatusBanner } from '../../src/components/ui/SyncStatusBanner'
import { useSyncHealthData } from '../../src/hooks/useReadiness'
import { useAuthStore } from '../../src/store/authStore'

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

function sevenDaysAgoISO() {
  const d = new Date()
  d.setDate(d.getDate() - 7)
  return d.toISOString().split('T')[0]
}

export default function DashboardLayout() {
  const router = useRouter()
  const userId = useAuthStore((s) => s.userId)
  const sync = useSyncHealthData()
  const [menuOpen, setMenuOpen] = useState(false)
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle')

  async function handleSync() {
    if (!userId) return
    setSyncStatus('syncing')
    try {
      await sync.mutateAsync({
        userId,
        startDate: sevenDaysAgoISO(),
        endDate: todayISO(),
      })
      setSyncStatus('success')
    } catch {
      setSyncStatus('error')
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Custom top bar */}
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.iconButton}
          testID="dashboard-menu"
          onPress={() => setMenuOpen(true)}
          activeOpacity={0.7}
        >
          <Text style={styles.iconText}>≡</Text>
        </TouchableOpacity>

        <Text style={styles.topBarTitle}>Vytal</Text>

        <View style={styles.topBarRight}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={handleSync}
            disabled={sync.isPending}
            activeOpacity={0.7}
          >
            <Text style={[styles.iconText, sync.isPending && styles.iconDisabled]}>↻</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => router.push('/catalog')}
            activeOpacity={0.7}
          >
            <Text style={styles.iconText}>+</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Sync status banner */}
      <SyncStatusBanner
        status={syncStatus}
        onHide={() => setSyncStatus('idle')}
      />

      {/* Screen content */}
      <View style={styles.content}>
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#0f172a' } }} />
      </View>

      {/* Side menu overlay */}
      <SideMenu visible={menuOpen} onClose={() => setMenuOpen(false)} />
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  topBar: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
    backgroundColor: '#0f172a',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  topBarTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: -0.5,
  },
  topBarRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    fontSize: 22,
    color: '#f8fafc',
    fontWeight: '400',
  },
  iconDisabled: {
    color: '#475569',
  },
  content: {
    flex: 1,
  },
})
