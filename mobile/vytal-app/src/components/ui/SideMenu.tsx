import React, { useEffect, useRef } from 'react'
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Animated,
  TouchableWithoutFeedback,
} from 'react-native'
import { useRouter, type Href } from 'expo-router'
import { logout } from '../../services/auth'
import { useAuthStore } from '../../store/authStore'

const MENU_WIDTH = 280

interface Props {
  visible: boolean
  onClose: () => void
}

export function SideMenu({ visible, onClose }: Props) {
  const router = useRouter()
  const userName = useAuthStore((s) => s.userProfile?.name)
  const userEmail = useAuthStore((s) => s.userProfile?.email)
  const slideAnim = useRef(new Animated.Value(-MENU_WIDTH)).current

  useEffect(() => {
    Animated.timing(slideAnim, {
      toValue: visible ? 0 : -MENU_WIDTH,
      duration: 260,
      useNativeDriver: true,
    }).start()
  }, [visible])

  function navigate(path: string) {
    onClose()
    // Small delay so close animation plays before navigation
    setTimeout(() => router.push(path as Href), 200)
  }

  function handleSignOut() {
    onClose()
    logout()
    setTimeout(() => {
      router.replace('/login')
    }, 200)
  }

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}>
      <View style={styles.overlay}>
        {/* Tappable dark overlay to close */}
        <TouchableWithoutFeedback onPress={onClose}>
          <View style={styles.backdrop} />
        </TouchableWithoutFeedback>

        <Animated.View style={[styles.menu, { transform: [{ translateX: slideAnim }] }]}>
          {/* Header */}
          <View style={styles.menuHeader}>
            <View style={styles.headerInfo}>
              <Text style={styles.menuTitle}>Vytal</Text>
              {userName ? (
                <Text style={styles.menuUserName}>{userName}</Text>
              ) : null}
              {userEmail ? (
                <Text style={styles.menuUserEmail}>{userEmail}</Text>
              ) : null}
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeIcon}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Menu items */}
          <View style={styles.menuItems}>
            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => navigate('/(dashboard)/profile')}
            >
              <Text style={styles.menuItemIcon}>👤</Text>
              <Text style={styles.menuItemText}>Meu Perfil</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => navigate('/(dashboard)/data-sources')}
            >
              <Text style={styles.menuItemIcon}>🔗</Text>
              <Text style={styles.menuItemText}>Fontes de Dados</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.menuItem} onPress={() => navigate('/catalog')}>
              <Text style={styles.menuItemIcon}>📊</Text>
              <Text style={styles.menuItemText}>Meus Indicadores</Text>
            </TouchableOpacity>

            <View style={styles.divider} />

            <TouchableOpacity style={styles.menuItem} onPress={handleSignOut}>
              <Text style={styles.menuItemIcon}>🚪</Text>
              <Text style={[styles.menuItemText, styles.signOutText]}>Sair</Text>
            </TouchableOpacity>
          </View>

          {/* Footer */}
          <View style={styles.menuFooter}>
            <Text style={styles.versionText}>Versão MVP</Text>
          </View>
        </Animated.View>
      </View>
    </Modal>
  )
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    flexDirection: 'row',
  },
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  menu: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: MENU_WIDTH,
    backgroundColor: '#1e293b',
    paddingTop: 56,
    paddingBottom: 32,
    shadowColor: '#000',
    shadowOffset: { width: 4, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 16,
  },
  menuHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingBottom: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  headerInfo: {
    flex: 1,
    gap: 2,
  },
  menuTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: -0.5,
  },
  menuUserName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#cbd5e1',
    marginTop: 4,
  },
  menuUserEmail: {
    fontSize: 12,
    color: '#64748b',
  },
  closeButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeIcon: {
    color: '#64748b',
    fontSize: 16,
  },
  menuItems: {
    paddingTop: 16,
    flex: 1,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
    gap: 14,
  },
  menuItemIcon: {
    fontSize: 20,
  },
  menuItemText: {
    fontSize: 16,
    color: '#f8fafc',
    fontWeight: '500',
  },
  signOutText: {
    color: '#ef4444',
  },
  divider: {
    height: 1,
    backgroundColor: '#334155',
    marginHorizontal: 24,
    marginVertical: 8,
  },
  menuFooter: {
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  versionText: {
    color: '#475569',
    fontSize: 12,
  },
})
