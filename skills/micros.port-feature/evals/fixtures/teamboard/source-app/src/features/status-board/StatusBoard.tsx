import { StatusCard } from './StatusCard'
import { StatusForm } from './StatusForm'
import { useStatuses } from './useStatuses'

export function StatusBoard() {
  const { state, reload } = useStatuses()

  return (
    <section className="status-board">
      <h2>Team status</h2>
      <StatusForm onPosted={() => void reload()} />

      {state.kind === 'loading' && <p className="status-board__loading">Loading the board…</p>}

      {state.kind === 'error' && (
        <div className="status-board__error" role="alert">
          <p>Couldn’t load the board: {state.message}</p>
          <button onClick={() => void reload()}>Try again</button>
        </div>
      )}

      {state.kind === 'loaded' && state.statuses.length === 0 && (
        <p className="status-board__empty">Nobody has posted yet. Be the first!</p>
      )}

      {state.kind === 'loaded' && state.statuses.length > 0 && (
        <div className="status-board__grid" data-refreshing={state.refreshing || undefined}>
          {state.statuses.map((s) => (
            <StatusCard key={s.id} status={s} />
          ))}
        </div>
      )}
    </section>
  )
}
