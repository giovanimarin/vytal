import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function todayISO() {
  return new Date().toISOString().split('T')[0]
}

export function formatDate(iso: string) {
  return new Date(iso + 'T12:00:00').toLocaleDateString('pt-BR', {
    weekday: 'long', day: 'numeric', month: 'long',
  })
}

export function statusColor(status: string) {
  if (status === 'green')  return '#4CAF50'
  if (status === 'yellow') return '#FFC107'
  return '#F44336'
}

export function statusLabel(status: string) {
  if (status === 'green')  return 'Pronto'
  if (status === 'yellow') return 'Moderado'
  return 'Descansar'
}

export function recoveryColor(score: number) {
  if (score >= 70) return '#4CAF50'
  if (score >= 40) return '#FFC107'
  return '#F44336'
}
