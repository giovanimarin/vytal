import React, { useEffect, useRef } from 'react'
import { View, Text, ActivityIndicator, StyleSheet, Animated } from 'react-native'

interface Props {
  status: 'idle' | 'syncing' | 'success' | 'error'
  onHide?: () => void
}

export function SyncStatusBanner({ status, onHide }: Props) {
  const heightAnim = useRef(new Animated.Value(0)).current
  const isVisible = status !== 'idle'

  useEffect(() => {
    Animated.timing(heightAnim, {
      toValue: isVisible ? 40 : 0,
      duration: 220,
      useNativeDriver: false,
    }).start()
  }, [isVisible])

  useEffect(() => {
    if (status === 'success') {
      const timer = setTimeout(() => {
        onHide?.()
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [status])

  const bgColor =
    status === 'syncing' ? '#1d4ed8' :
    status === 'success' ? '#15803d' :
    status === 'error'   ? '#b91c1c' :
    'transparent'

  const message =
    status === 'syncing' ? 'Sincronizando dados...' :
    status === 'success' ? 'Dados sincronizados!'  :
    status === 'error'   ? 'Erro ao sincronizar'   :
    ''

  return (
    <Animated.View style={[styles.banner, { height: heightAnim, backgroundColor: bgColor }]}>
      <View style={styles.inner}>
        {status === 'syncing' && (
          <ActivityIndicator color="#fff" size="small" style={styles.spinner} />
        )}
        <Text style={styles.text}>{message}</Text>
      </View>
    </Animated.View>
  )
}

const styles = StyleSheet.create({
  banner: {
    overflow: 'hidden',
    justifyContent: 'center',
  },
  inner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  spinner: {
    marginRight: 8,
  },
  text: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
})
