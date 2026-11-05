export interface UserProfile {
  user_id: string
  email: string
  name: string
  birth_date: string | null
  weight_kg: number | null
  height_cm: number | null
  goal: string | null
}

export interface AuthSession {
  accessToken: string
  refreshToken: string
  userProfile: UserProfile
}

function requiredString(value: unknown): string {
  if (typeof value !== 'string' || !value.trim()) throw new Error('Resposta de autenticação inválida.')
  return value
}

export function profileFromResponse(value: unknown): UserProfile {
  if (!value || typeof value !== 'object') throw new Error('Perfil inválido.')
  const data = value as Record<string, unknown>
  return {
    user_id: requiredString(data.user_id),
    email: requiredString(data.email),
    name: typeof data.name === 'string' ? data.name : '',
    birth_date: typeof data.birth_date === 'string' ? data.birth_date : null,
    weight_kg: typeof data.weight_kg === 'number' ? data.weight_kg : null,
    height_cm: typeof data.height_cm === 'number' ? data.height_cm : null,
    goal: typeof data.goal === 'string' ? data.goal : null,
  }
}

// The public v1 contract is flat, for both login and registration.
export function sessionFromResponse(value: unknown): AuthSession {
  if (!value || typeof value !== 'object') throw new Error('Resposta de autenticação inválida.')
  const data = value as Record<string, unknown>
  return {
    accessToken: requiredString(data.access_token),
    refreshToken: requiredString(data.refresh_token),
    userProfile: profileFromResponse(data),
  }
}
