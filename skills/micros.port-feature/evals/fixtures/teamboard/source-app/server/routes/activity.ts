import { Router } from 'express'
import { db } from '../db.js'

export const activity = Router()

// Reads three tables: activity_log is its own, but it joins users for names
// and statuses for the posted body when kind = 'status.posted'.
const recentActivity = db.prepare(`
  SELECT a.id, a.kind, a.created_at,
         u.display_name, u.avatar_color,
         s.body AS status_body, s.emoji AS status_emoji
  FROM activity_log a
  JOIN users u ON u.id = a.user_id
  LEFT JOIN statuses s ON s.id = a.subject_id AND a.kind = 'status.posted'
  ORDER BY a.created_at DESC
  LIMIT 50
`)

activity.get('/api/activity', (_req, res) => {
  res.json({ activity: recentActivity.all() })
})
