import { timeAgo } from '../../lib/format'
import type { Status } from './types'

export function StatusCard({ status }: { status: Status }) {
  const expired = status.expires_at !== null && Date.parse(status.expires_at) < Date.now()
  return (
    <article className={`status-card${expired ? ' status-card--expired' : ''}`}>
      <span className="status-card__avatar" style={{ background: status.avatar_color }}>
        {status.display_name[0]}
      </span>
      <div>
        <header>
          <strong>{status.display_name}</strong>
          <time dateTime={status.created_at}>{timeAgo(status.created_at)}</time>
        </header>
        <p>
          {status.emoji && <span className="status-card__emoji">{status.emoji}</span>}
          {status.body}
        </p>
        {expired && <small>expired</small>}
      </div>
    </article>
  )
}
