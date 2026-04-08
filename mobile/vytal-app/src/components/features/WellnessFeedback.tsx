import React, { useState } from 'react'
import {
  View, Text, StyleSheet, TouchableOpacity, ActivityIndicator,
} from 'react-native'
import { useSubmitWellnessFeedback } from '../../hooks/useReadiness'

interface Props {
  userId: string
  date: string
  onSubmitted: () => void
}

const EMOJIS = ['😴', '😑', '😊', '💪', '🔥']

export function WellnessFeedback({ userId, date, onSubmitted }: Props) {
  const [feelingScore, setFeelingScore] = useState<number | null>(null)
  const [trainedToday, setTrainedToday] = useState<boolean | null>(null)
  const [workoutWorthIt, setWorkoutWorthIt] = useState<boolean | null>(null)

  const mutation = useSubmitWellnessFeedback()

  async function handleSubmit() {
    if (feelingScore == null) return
    try {
      await mutation.mutateAsync({
        user_id: userId,
        date,
        feeling_score: feelingScore,
        trained_today: trainedToday,
        workout_worth_it: trainedToday ? workoutWorthIt : null,
      })
      onSubmitted()
    } catch {
      // silently fail — user can retry
    }
  }

  const canSubmit = feelingScore != null

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Como foi seu dia?</Text>

      {/* Energy level */}
      <View style={styles.question}>
        <Text style={styles.questionLabel}>Nível de energia</Text>
        <View style={styles.emojiRow}>
          {EMOJIS.map((emoji, index) => {
            const score = index + 1
            const selected = feelingScore === score
            return (
              <TouchableOpacity
                key={score}
                style={[styles.emojiButton, selected && styles.emojiButtonSelected]}
                onPress={() => setFeelingScore(score)}
                activeOpacity={0.7}
              >
                <Text style={styles.emoji}>{emoji}</Text>
              </TouchableOpacity>
            )
          })}
        </View>
      </View>

      {/* Trained today */}
      <View style={styles.question}>
        <Text style={styles.questionLabel}>Treinou hoje?</Text>
        <View style={styles.toggleRow}>
          <TouchableOpacity
            style={[styles.toggleButton, trainedToday === true && styles.toggleButtonActive]}
            onPress={() => setTrainedToday(true)}
            activeOpacity={0.7}
          >
            <Text style={[styles.toggleText, trainedToday === true && styles.toggleTextActive]}>
              Sim
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleButton, trainedToday === false && styles.toggleButtonActive]}
            onPress={() => {
              setTrainedToday(false)
              setWorkoutWorthIt(null)
            }}
            activeOpacity={0.7}
          >
            <Text style={[styles.toggleText, trainedToday === false && styles.toggleTextActive]}>
              Não
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Workout worth it */}
      {trainedToday === true && (
        <View style={styles.question}>
          <Text style={styles.questionLabel}>Valeu a pena?</Text>
          <View style={styles.toggleRow}>
            <TouchableOpacity
              style={[styles.toggleButton, workoutWorthIt === true && styles.toggleButtonActive]}
              onPress={() => setWorkoutWorthIt(true)}
              activeOpacity={0.7}
            >
              <Text style={[styles.toggleText, workoutWorthIt === true && styles.toggleTextActive]}>
                Sim
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleButton, workoutWorthIt === false && styles.toggleButtonActive]}
              onPress={() => setWorkoutWorthIt(false)}
              activeOpacity={0.7}
            >
              <Text style={[styles.toggleText, workoutWorthIt === false && styles.toggleTextActive]}>
                Não
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Submit */}
      <TouchableOpacity
        style={[styles.submitButton, (!canSubmit || mutation.isPending) && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={!canSubmit || mutation.isPending}
        activeOpacity={0.8}
      >
        {mutation.isPending
          ? <ActivityIndicator color="#fff" size="small" />
          : <Text style={styles.submitText}>Enviar</Text>
        }
      </TouchableOpacity>

      {mutation.isError && (
        <Text style={styles.errorText}>Erro ao enviar. Tente novamente.</Text>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
    gap: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  question: {
    gap: 10,
  },
  questionLabel: {
    fontSize: 13,
    color: '#94a3b8',
  },
  emojiRow: {
    flexDirection: 'row',
    gap: 8,
  },
  emojiButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#0f172a',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  emojiButtonSelected: {
    borderColor: '#3b82f6',
    backgroundColor: '#1e3a5f',
  },
  emoji: {
    fontSize: 22,
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 10,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 10,
    backgroundColor: '#0f172a',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  toggleButtonActive: {
    borderColor: '#3b82f6',
    backgroundColor: '#1e3a5f',
  },
  toggleText: {
    fontSize: 14,
    color: '#64748b',
    fontWeight: '600',
  },
  toggleTextActive: {
    color: '#3b82f6',
  },
  submitButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  errorText: {
    color: '#ef4444',
    fontSize: 13,
    textAlign: 'center',
  },
})
