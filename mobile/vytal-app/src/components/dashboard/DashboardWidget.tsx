import React from 'react'
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native'
import type { WidgetId } from '../../store/dashboardStore'

interface Props {
  widgetId: WidgetId
  editMode: boolean
  onRemove: () => void
  children: React.ReactNode
}

export function DashboardWidget({ editMode, onRemove, children }: Props) {
  return (
    <View style={styles.wrapper}>
      {children}
      {editMode && (
        <TouchableOpacity style={styles.removeButton} onPress={onRemove} activeOpacity={0.8}>
          <Text style={styles.removeIcon}>✕</Text>
        </TouchableOpacity>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'relative',
  },
  removeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#ef4444',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.4,
    shadowRadius: 4,
    elevation: 4,
  },
  removeIcon: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
})
