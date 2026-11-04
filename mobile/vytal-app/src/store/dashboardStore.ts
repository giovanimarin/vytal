import create from 'zustand'

export type WidgetId =
  | 'readiness_score'
  | 'score_history'
  | 'sleep_details'
  | 'steps_calories'
  | 'hr_zones'
  | 'social_jetlag'
  | 'recovery_curve'
  | 'signal_quality'
  | 'wellness_feedback'

interface DashboardState {
  activeWidgets: WidgetId[]
  addWidget: (id: WidgetId) => void
  removeWidget: (id: WidgetId) => void
  reorderWidgets: (newOrder: WidgetId[]) => void
  hasWidget: (id: WidgetId) => boolean
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  activeWidgets: [],
  addWidget: (id) =>
    set((s) => ({
      activeWidgets: s.activeWidgets.includes(id)
        ? s.activeWidgets
        : [...s.activeWidgets, id],
    })),
  removeWidget: (id) =>
    set((s) => ({
      activeWidgets: s.activeWidgets.filter((w) => w !== id),
    })),
  reorderWidgets: (newOrder) => set({ activeWidgets: newOrder }),
  hasWidget: (id) => get().activeWidgets.includes(id),
}))
