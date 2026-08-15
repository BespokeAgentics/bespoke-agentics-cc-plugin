export type Status = {
  id: number
  user_id: number
  display_name: string
  avatar_color: string
  body: string
  emoji: string | null
  expires_at: string | null
  created_at: string
}

export type NewStatus = {
  body: string
  emoji?: string
  expiresInHours?: number
}
