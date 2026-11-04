'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { todayISO, recoveryColor } from '@/lib/utils'

const MUSCLE_LABEL: Record<string, string> = {
  chest:           'Peitoral',
  front_shoulders: 'Ombros Ant.',
  rear_shoulders:  'Ombros Post.',
  biceps:          'Bíceps',
  triceps:         'Tríceps',
  upper_back:      'Costas Sup.',
  lower_back:      'Lombar',
  core:            'Core / Abdômen',
  glutes:          'Glúteos',
  quads:           'Quadríceps',
  hamstrings:      'Post. de Coxa',
  calves:          'Panturrilhas',
  hip_flexors:     'Flex. do Quadril',
}

// ─── SVG paths for each muscle group ────────────────────────────────────────
// ViewBox: 0 0 200 460. Coordinates for male front/back.
// Female variants scale hips wider (+12) and shoulders narrower (-6).

const FRONT_PATHS: Record<string, string> = {
  // Pectorals — two fan-shaped lobes
  chest: `
    M 76,108 C 76,98 84,90 100,88 C 116,90 124,98 124,108
    C 124,120 116,128 100,130 C 84,128 76,120 76,108 Z
  `,
  // Anterior deltoids — rounded shoulder caps
  front_shoulders: `
    M 62,88 C 54,82 50,90 52,100 C 54,110 62,114 68,108 C 72,102 70,92 62,88 Z
    M 138,88 C 146,82 150,90 148,100 C 146,110 138,114 132,108 C 128,102 130,92 138,88 Z
  `,
  // Biceps — two elongated shapes on front of upper arms
  biceps: `
    M 56,112 C 50,112 46,122 48,134 C 50,144 58,148 64,142 C 68,136 66,118 56,112 Z
    M 144,112 C 150,112 154,122 152,134 C 150,144 142,148 136,142 C 132,136 134,118 144,112 Z
  `,
  // Core — rectus abdominis (six-pack grid)
  core: `
    M 88,138 L 88,200 C 88,208 94,212 100,212 C 106,212 112,208 112,200 L 112,138
    C 112,132 106,128 100,128 C 94,128 88,132 88,138 Z
  `,
  // Hip flexors — lower abdomen / inguinal area
  hip_flexors: `
    M 86,210 C 80,210 74,218 76,226 C 78,232 86,234 92,230 C 96,226 96,216 86,210 Z
    M 114,210 C 120,210 126,218 124,226 C 122,232 114,234 108,230 C 104,226 104,216 114,210 Z
  `,
  // Quads — large thigh shapes (4 heads roughly)
  quads: `
    M 72,238 C 66,238 60,248 62,272 C 64,292 72,306 82,306 C 90,306 96,294 94,272
    C 92,252 84,238 72,238 Z
    M 128,238 C 134,238 140,248 138,272 C 136,292 128,306 118,306 C 110,306 104,294 106,272
    C 108,252 116,238 128,238 Z
  `,
}

const BACK_PATHS: Record<string, string> = {
  // Posterior deltoids
  rear_shoulders: `
    M 62,88 C 54,82 50,90 52,100 C 54,110 62,114 68,108 C 72,102 70,92 62,88 Z
    M 138,88 C 146,82 150,90 148,100 C 146,110 138,114 132,108 C 128,102 130,92 138,88 Z
  `,
  // Triceps — back of upper arms
  triceps: `
    M 56,112 C 50,112 46,122 48,134 C 50,144 58,148 64,142 C 68,136 66,118 56,112 Z
    M 144,112 C 150,112 154,122 152,134 C 150,144 142,148 136,142 C 132,136 134,118 144,112 Z
  `,
  // Trapezius + rhomboids (upper back)
  upper_back: `
    M 68,88 C 68,88 72,96 78,104 C 86,112 94,116 100,116 C 106,116 114,112 122,104
    C 128,96 132,88 132,88 C 124,84 112,82 100,82 C 88,82 76,84 68,88 Z
  `,
  // Erector spinae (lower back)
  lower_back: `
    M 84,136 C 80,136 76,144 78,158 C 80,168 86,172 92,168 C 96,164 96,148 84,136 Z
    M 116,136 C 120,136 124,144 122,158 C 120,168 114,172 108,168 C 104,164 104,148 116,136 Z
  `,
  // Glutes — two large rounded shapes
  glutes: `
    M 72,190 C 62,190 56,202 58,220 C 60,234 72,242 84,238 C 94,234 98,218 94,204
    C 90,194 82,190 72,190 Z
    M 128,190 C 138,190 144,202 142,220 C 140,234 128,242 116,238 C 106,234 102,218 106,204
    C 110,194 118,190 128,190 Z
  `,
  // Hamstrings — back of thighs
  hamstrings: `
    M 72,244 C 64,244 58,256 60,278 C 62,298 72,310 82,308 C 92,306 96,290 94,270
    C 92,252 82,244 72,244 Z
    M 128,244 C 136,244 142,256 140,278 C 138,298 128,310 118,308 C 108,306 104,290 106,270
    C 108,252 118,244 128,244 Z
  `,
  // Calves — gastrocnemius
  calves: `
    M 76,318 C 68,318 64,330 66,350 C 68,366 76,374 84,370 C 92,366 94,350 90,334
    C 88,322 84,318 76,318 Z
    M 124,318 C 132,318 136,330 134,350 C 132,366 124,374 116,370 C 108,366 106,350 110,334
    C 112,322 116,318 124,318 Z
  `,
}

// ─── Body silhouette paths ───────────────────────────────────────────────────

function maleSilhouette(view: 'front' | 'back') {
  return (
    <>
      {/* Head */}
      <ellipse cx={100} cy={44} rx={22} ry={26} fill="#1e293b" stroke="#334155" strokeWidth={1.5} />
      {/* Neck */}
      <rect x={91} y={68} width={18} height={14} rx={4} fill="#1e293b" />
      {/* Torso */}
      <path d="M 66,80 L 134,80 L 140,200 L 60,200 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.5} />
      {/* Left arm */}
      <path d="M 66,82 L 50,88 L 44,160 L 58,158 L 66,100 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Right arm */}
      <path d="M 134,82 L 150,88 L 156,160 L 142,158 L 134,100 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Forearms */}
      <path d="M 44,160 L 38,220 L 52,222 L 58,160 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <path d="M 156,160 L 162,220 L 148,222 L 142,160 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Hands */}
      <ellipse cx={45} cy={228} rx={9} ry={12} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <ellipse cx={155} cy={228} rx={9} ry={12} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Hips */}
      <path d="M 60,198 L 140,198 L 148,236 L 52,236 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Left leg */}
      <path d="M 60,234 L 52,234 L 54,390 L 86,390 L 88,234 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Right leg */}
      <path d="M 112,234 L 148,234 L 146,390 L 114,390 L 112,234 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Feet */}
      <ellipse cx={70} cy={396} rx={16} ry={8} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <ellipse cx={130} cy={396} rx={16} ry={8} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {view === 'front' && (
        <>
          {/* Collarbone lines */}
          <line x1={68} y1={82} x2={100} y2={86} stroke="#334155" strokeWidth={1} />
          <line x1={132} y1={82} x2={100} y2={86} stroke="#334155" strokeWidth={1} />
          {/* Navel */}
          <circle cx={100} cy={172} r={2.5} fill="#334155" />
        </>
      )}
    </>
  )
}

function femaleSilhouette(view: 'front' | 'back') {
  return (
    <>
      {/* Head — slightly smaller */}
      <ellipse cx={100} cy={44} rx={20} ry={24} fill="#1e293b" stroke="#334155" strokeWidth={1.5} />
      {/* Neck */}
      <rect x={92} y={66} width={16} height={14} rx={4} fill="#1e293b" />
      {/* Torso — narrower shoulders, wider hips */}
      <path d="M 70,78 L 130,78 L 138,170 L 62,170 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.5} />
      {/* Chest curves (female) */}
      {view === 'front' && (
        <>
          <path d="M 76,108 Q 88,128 100,130 Q 112,128 124,108" fill="none" stroke="#334155" strokeWidth={1} />
          <ellipse cx={86} cy={118} rx={11} ry={9} fill="#243347" stroke="#334155" strokeWidth={0.8} />
          <ellipse cx={114} cy={118} rx={11} ry={9} fill="#243347" stroke="#334155" strokeWidth={0.8} />
          <circle cx={86} cy={118} r={3} fill="#334155" />
          <circle cx={114} cy={118} r={3} fill="#334155" />
        </>
      )}
      {/* Waist narrowing */}
      <path d="M 62,170 L 56,190 L 144,190 L 138,170 Z" fill="#1e293b" />
      {/* Hips wider for female */}
      <path d="M 56,188 L 144,188 L 154,234 L 46,234 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Left arm — slimmer */}
      <path d="M 70,80 L 54,86 L 48,156 L 62,154 L 70,98 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Right arm */}
      <path d="M 130,80 L 146,86 L 152,156 L 138,154 L 130,98 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Forearms */}
      <path d="M 48,156 L 42,214 L 56,216 L 62,154 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <path d="M 152,156 L 158,214 L 144,216 L 138,154 Z" fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Hands */}
      <ellipse cx={47} cy={222} rx={9} ry={11} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <ellipse cx={153} cy={222} rx={9} ry={11} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {/* Left leg */}
      <path d="M 60,232 L 46,232 L 50,388 L 84,388 L 86,232 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Right leg */}
      <path d="M 114,232 L 154,232 L 150,388 L 116,388 L 114,232 Z" fill="#1e293b" stroke="#334155" strokeWidth={1.2} />
      {/* Feet */}
      <ellipse cx={67} cy={394} rx={15} ry={7} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      <ellipse cx={133} cy={394} rx={15} ry={7} fill="#1e293b" stroke="#334155" strokeWidth={1} />
      {view === 'front' && (
        <>
          <line x1={70} y1={80} x2={100} y2={84} stroke="#334155" strokeWidth={1} />
          <line x1={130} y1={80} x2={100} y2={84} stroke="#334155" strokeWidth={1} />
          <circle cx={100} cy={166} r={2} fill="#334155" />
        </>
      )}
    </>
  )
}

function BodySVG({
  muscles,
  view,
  gender,
  selected,
  onSelect,
}: {
  muscles: Record<string, number>
  view: 'front' | 'back'
  gender: string
  selected: string | null
  onSelect: (m: string) => void
}) {
  const paths = view === 'front' ? FRONT_PATHS : BACK_PATHS

  return (
    <svg viewBox="0 0 200 460" className="w-full max-w-[200px]">
      {/* Body silhouette */}
      {gender === 'female' ? femaleSilhouette(view) : maleSilhouette(view)}

      {/* Muscle overlays */}
      {Object.entries(paths).map(([muscle, d]) => {
        const score = muscles[muscle] ?? 100
        const color = recoveryColor(score)
        const isSelected = selected === muscle
        return (
          <path
            key={muscle}
            d={d}
            fill={color}
            fillOpacity={isSelected ? 0.9 : 0.65}
            stroke={color}
            strokeWidth={isSelected ? 2 : 1}
            strokeOpacity={isSelected ? 1 : 0.8}
            style={{ cursor: 'pointer', filter: isSelected ? `drop-shadow(0 0 4px ${color})` : 'none' }}
            onClick={() => onSelect(muscle)}
          />
        )
      })}
    </svg>
  )
}

export default function BodyMapPage() {
  const { userId, gender } = useAuthStore()
  const today = todayISO()
  const [view, setView] = useState<'front' | 'back'>('front')
  const [selected, setSelected] = useState<string | null>(null)

  const { data: recoveryData } = useQuery({
    queryKey: ['muscle-recovery', userId, today],
    queryFn: async () => {
      const { data } = await api.get(`/muscles/${userId}/recovery?date=${today}`)
      return data
    },
    enabled: !!userId,
  })

  const { data: suggestion } = useQuery({
    queryKey: ['muscle-suggestion', userId, today],
    queryFn: async () => {
      const { data } = await api.get(`/muscles/${userId}/suggestion?date=${today}`)
      return data
    },
    enabled: !!userId,
  })

  const muscles = recoveryData?.muscles ?? []
  const muscleMap: Record<string, number> = Object.fromEntries(
    muscles.map((m: any) => [m.muscle_group, m.recovery_score])
  )
  const selectedRecord = muscles.find((m: any) => m.muscle_group === selected)
  const sorted = [...muscles].sort((a: any, b: any) => a.recovery_score - b.recovery_score)
  const effectiveGender = gender || 'male'

  return (
    <AppShell>
      <div className="p-8 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-black text-text">Body Map</h1>
            <p className="text-muted text-sm mt-1">Recuperação muscular — clique no músculo para detalhes</p>
          </div>
          {!gender && (
            <Link href="/settings" className="text-xs text-yellow-400 hover:underline">
              ⚠ Configure seu sexo biológico →
            </Link>
          )}
        </div>

        {suggestion?.suggestion && (
          <div className="bg-surface border-l-4 border-brand rounded-2xl p-5">
            <p className="text-xs text-brand font-bold uppercase tracking-wide mb-1">Sugestão do dia</p>
            <p className="text-sub text-sm">{suggestion.message}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* SVG */}
          <div className="bg-surface rounded-2xl p-6 space-y-4">
            <div className="flex gap-2">
              {(['front', 'back'] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`px-5 py-2 rounded-xl text-sm font-semibold transition-colors ${
                    view === v ? 'bg-brand text-white' : 'bg-bg text-muted hover:text-text'
                  }`}
                >
                  {v === 'front' ? 'Frente' : 'Verso'}
                </button>
              ))}
              <span className="ml-auto text-xs text-muted self-center">
                {effectiveGender === 'female' ? '♀ Feminino' : '♂ Masculino'}
              </span>
            </div>

            <div className="flex justify-center">
              <BodySVG
                muscles={muscleMap}
                view={view}
                gender={effectiveGender}
                selected={selected}
                onSelect={setSelected}
              />
            </div>

            {/* Legenda */}
            <div className="flex justify-center gap-6">
              {[['#4CAF50', '≥ 70%'], ['#FFC107', '40–69%'], ['#F44336', '< 40%']].map(([color, label]) => (
                <div key={label} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-xs text-muted">{label}</span>
                </div>
              ))}
            </div>

            {selectedRecord && (
              <div className="bg-bg rounded-xl p-4 space-y-2 border border-border">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-text">{MUSCLE_LABEL[selected!] ?? selected}</h3>
                  <span
                    className="text-2xl font-black"
                    style={{ color: recoveryColor(selectedRecord.recovery_score) }}
                  >
                    {Math.round(selectedRecord.recovery_score)}%
                  </span>
                </div>
                {selectedRecord.estimated_full_recovery_at && selectedRecord.recovery_score < 100 && (
                  <p className="text-xs text-muted">
                    Recuperação completa: {new Date(selectedRecord.estimated_full_recovery_at).toLocaleString('pt-BR', {
                      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                    })}
                  </p>
                )}
                {!selectedRecord.last_workout_id && (
                  <p className="text-xs text-muted">Nenhum treino recente registrado.</p>
                )}
              </div>
            )}
          </div>

          {/* Tabela */}
          <div className="bg-surface rounded-2xl p-6 space-y-3">
            <h2 className="font-bold text-text">Todos os grupos musculares</h2>
            <div className="space-y-2">
              {sorted.map((m: any) => {
                const color = recoveryColor(m.recovery_score)
                const score = Math.round(m.recovery_score)
                return (
                  <div
                    key={m.muscle_group}
                    className="flex items-center gap-3 cursor-pointer hover:bg-bg rounded-xl px-3 py-2 transition-colors"
                    onClick={() => {
                      setSelected(m.muscle_group)
                      const viewFor = Object.keys(FRONT_PATHS).includes(m.muscle_group) ? 'front' : 'back'
                      setView(viewFor)
                    }}
                  >
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
                    <span className="flex-1 text-sm text-sub">{MUSCLE_LABEL[m.muscle_group] ?? m.muscle_group}</span>
                    <div className="w-24 h-1.5 bg-border rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: color }} />
                    </div>
                    <span className="text-sm font-bold w-10 text-right" style={{ color }}>{score}%</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
