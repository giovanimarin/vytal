import React, { useState } from 'react'
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native'
import { useRouter } from 'expo-router'
import { useDashboardStore } from '../../src/store/dashboardStore'
import type { WidgetId } from '../../src/store/dashboardStore'
import { DashboardWidget } from '../../src/components/dashboard/DashboardWidget'

import { ScoreRing } from '../../src/components/ui/ScoreRing'
import { ScoreHistory } from '../../src/components/features/ScoreHistory'
import { SleepDetails } from '../../src/components/features/SleepDetails'
import { StepsCalories } from '../../src/components/features/StepsCalories'
import { HRZones } from '../../src/components/features/HRZones'
import { AdvancedMetrics } from '../../src/components/features/AdvancedMetrics'
import { WellnessFeedback } from '../../src/components/features/WellnessFeedback'

import {
  useReadiness,
  useReadinessHistory,
  useAdvancedMetrics,
  useWellnessFeedback,
} from '../../src/hooks/useReadiness'
import { useHealthSummary } from '../../src/hooks/useHealthData'
import { useAuthStore } from '../../src/store/authStore'

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

function sevenDaysAgoISO() {
  const d = new Date()
  d.setDate(d.getDate() - 7)
  return d.toISOString().split('T')[0]
}

export default function DashboardScreen() {
  const router = useRouter()
  const userId = useAuthStore((s) => s.userId)
  const { activeWidgets, removeWidget } = useDashboardStore()
  const [editMode, setEditMode] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  const today = todayISO()
  const sevenDaysAgo = sevenDaysAgoISO()

  const { data: readiness, isLoading: readinessLoading } = useReadiness(userId, today)
  const { data: history } = useReadinessHistory(userId, sevenDaysAgo, today)
  const { data: healthSummary } = useHealthSummary(userId, today)
  const { data: advancedMetrics, isLoading: advancedLoading } = useAdvancedMetrics(userId, today)
  const { data: existingFeedback } = useWellnessFeedback(userId, today)

  const totalCalories = healthSummary?.activity?.length
    ? healthSummary.activity.reduce((sum: number, a: any) => sum + (a.calories_burned ?? 0), 0)
    : null

  const showFeedback = userId && !feedbackSubmitted && !existingFeedback

  if (activeWidgets.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>⊞</Text>
        <Text style={styles.emptyTitle}>Seu dashboard está vazio</Text>
        <Text style={styles.emptyText}>Toque em + para adicionar indicadores</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => router.push('/catalog')}
          activeOpacity={0.8}
        >
          <Text style={styles.addButtonText}>Adicionar indicadores</Text>
        </TouchableOpacity>
      </View>
    )
  }

  function renderWidget(widgetId: WidgetId) {
    switch (widgetId) {
      case 'readiness_score':
        if (readinessLoading) {
          return (
            <View style={styles.loadingCard}>
              <ActivityIndicator color="#3b82f6" />
            </View>
          )
        }
        if (!readiness) return null
        return (
          <View style={styles.widgetContainer}>
            <View style={styles.scoreSection}>
              <ScoreRing score={readiness.readiness_score} category={readiness.readiness_category} />
            </View>
            <View style={styles.insightCard}>
              <Text style={styles.insightText}>{readiness.insight_text}</Text>
            </View>
          </View>
        )

      case 'score_history':
        if (!history || history.length === 0) return null
        return <ScoreHistory history={history} />

      case 'sleep_details':
        return <SleepDetails sleep={healthSummary?.sleep ?? null} />

      case 'steps_calories':
        return (
          <StepsCalories
            steps={healthSummary?.steps?.total_steps ?? null}
            calories={totalCalories}
          />
        )

      case 'hr_zones':
        return <HRZones heartRate={healthSummary?.heart_rate ?? null} />

      case 'social_jetlag':
      case 'recovery_curve':
      case 'signal_quality':
        return (
          <AdvancedMetrics metrics={advancedMetrics ?? null} isLoading={advancedLoading} />
        )

      case 'wellness_feedback':
        if (!showFeedback || !userId) return null
        return (
          <WellnessFeedback
            userId={userId}
            date={today}
            onSubmitted={() => setFeedbackSubmitted(true)}
          />
        )

      default:
        return null
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Edit mode banner */}
      {editMode && (
        <View style={styles.editBanner}>
          <Text style={styles.editBannerText}>Modo de edição — toque no ✕ para remover</Text>
          <TouchableOpacity onPress={() => setEditMode(false)} style={styles.doneButton}>
            <Text style={styles.doneButtonText}>Concluído</Text>
          </TouchableOpacity>
        </View>
      )}

      {activeWidgets.map((widgetId) => {
        const content = renderWidget(widgetId)
        if (!content) return null
        return (
          <TouchableOpacity
            key={widgetId}
            activeOpacity={1}
            onLongPress={() => setEditMode(true)}
            delayLongPress={400}
          >
            <DashboardWidget
              widgetId={widgetId}
              editMode={editMode}
              onRemove={() => removeWidget(widgetId)}
            >
              {content}
            </DashboardWidget>
          </TouchableOpacity>
        )
      })}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    padding: 16,
    paddingBottom: 48,
    gap: 16,
  },
  emptyContainer: {
    flex: 1,
    backgroundColor: '#0f172a',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    gap: 16,
  },
  emptyIcon: {
    fontSize: 56,
    color: '#334155',
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#f8fafc',
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 15,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 22,
  },
  addButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 28,
    marginTop: 8,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  editBanner: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#334155',
  },
  editBannerText: {
    color: '#94a3b8',
    fontSize: 13,
    flex: 1,
  },
  doneButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 14,
    marginLeft: 12,
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  widgetContainer: {
    gap: 16,
  },
  scoreSection: {
    alignItems: 'center',
    paddingVertical: 16,
    backgroundColor: '#1e293b',
    borderRadius: 16,
  },
  insightCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
  },
  insightText: {
    color: '#cbd5e1',
    fontSize: 15,
    lineHeight: 24,
  },
  loadingCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 40,
    alignItems: 'center',
  },
})
