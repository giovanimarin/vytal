/**
 * Entry point — redireciona para Connect se não autenticado,
 * ou para o Dashboard se já conectado.
 */
import { Redirect } from 'expo-router'
import { useAuthStore } from '../src/store/authStore'

export default function Index() {
  const isConnected = useAuthStore((s) => s.isConnected)
  return <Redirect href={isConnected ? '/(tabs)' : '/connect'} />
}
