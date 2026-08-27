import { useEffect, useState } from 'react'
import { apiGet } from '../../lib/api'
import { timeAgo } from '../../lib/format'

type ActivityItem = {
  id: number
  kind: 'status.posted' | 'user.joined' | 'board.renamed'
  created_at: string
  display_name: string
  avatar_color: string
  status_body: string | null
  status_emoji: string | null
}

const LABELS: Record<ActivityItem['kind'], string> = {
  'status.posted': 'posted a status',
  'user.joined': 'joined the board',
  'board.renamed': 'renamed the board',
}

export function ActivityFeed() {
  const [items, setItems] = useState<ActivityItem[] | null>(null)

  useEffect(() => {
    void apiGet<{ activity: ActivityItem[] }>('/api/activity').then(
      ({ activity }) => setItems(activity),
      () => setItems([]),
    )
  }, [])

  if (items === null) return <p>Loading activity…</p>

  return (
    <ol className="activity-feed">
      {items.map((item) => (
        <li key={item.id}>
          <span className="activity-feed__dot" style={{ background: item.avatar_color }} />
          <strong>{item.display_name}</strong> {LABELS[item.kind]}
          {item.status_body && (
            <q>
              {item.status_emoji} {item.status_body}
            </q>
          )}
          <time dateTime={item.created_at}>{timeAgo(item.created_at)}</time>
        </li>
      ))}
    </ol>
  )
}
