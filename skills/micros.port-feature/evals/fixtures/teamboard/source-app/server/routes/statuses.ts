import { Router } from 'express'
import { z } from 'zod'
import { db } from '../db.js'

export const statuses = Router()

const listStatuses = db.prepare(`
  SELECT s.id, s.body, s.emoji, s.expires_at, s.created_at,
         u.id AS user_id, u.display_name, u.avatar_color
  FROM statuses s
  JOIN users u ON u.id = s.user_id
  WHERE s.id IN (
    SELECT MAX(id) FROM statuses GROUP BY user_id
  )
  ORDER BY s.created_at DESC
`)

const insertStatus = db.prepare(
  'INSERT INTO statuses (user_id, body, emoji, expires_at) VALUES (?, ?, ?, ?)',
)

// Posting a status also writes the shared activity_log so the Activity page
// picks it up. Coupled on purpose — the PM wanted one feed for everything.
const logActivity = db.prepare(
  "INSERT INTO activity_log (user_id, kind, subject_id) VALUES (?, 'status.posted', ?)",
)

const NewStatus = z.object({
  body: z.string().min(1).max(140),
  emoji: z.string().emoji().optional(),
  expiresInHours: z.number().int().min(1).max(72).optional(),
})

statuses.get('/api/statuses', (_req, res) => {
  res.json({ statuses: listStatuses.all() })
})

statuses.post('/api/statuses', (req, res) => {
  const parsed = NewStatus.safeParse(req.body)
  if (!parsed.success) {
    res.status(422).json({ error: 'invalid_status', issues: parsed.error.issues })
    return
  }
  const { body, emoji, expiresInHours } = parsed.data
  const expiresAt = expiresInHours
    ? new Date(Date.now() + expiresInHours * 3_600_000).toISOString()
    : null
  const userId = req.session.userId as number
  const result = insertStatus.run(userId, body, emoji ?? null, expiresAt)
  logActivity.run(userId, result.lastInsertRowid)
  res.status(201).json({ id: result.lastInsertRowid })
})
