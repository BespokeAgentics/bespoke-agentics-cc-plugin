import { useCallback, useEffect, useRef, useState } from 'react'
import { apiGet } from '../../lib/api'
import type { Status } from './types'

const POLL_MS = 5000

type State =
  | { kind: 'loading' }
  | { kind: 'loaded'; statuses: Status[]; refreshing: boolean }
  | { kind: 'error'; message: string }

/**
 * Polls /api/statuses every 5s. On a refresh failure we keep showing the last
 * good list (stale beats blank); only the initial load surfaces the error UI.
 */
export function useStatuses() {
  const [state, setState] = useState<State>({ kind: 'loading' })
  const timer = useRef<ReturnType<typeof setInterval>>()

  const load = useCallback(async (initial: boolean) => {
    if (!initial) {
      setState((s) => (s.kind === 'loaded' ? { ...s, refreshing: true } : s))
    }
    try {
      const { statuses } = await apiGet<{ statuses: Status[] }>('/api/statuses')
      setState({ kind: 'loaded', statuses, refreshing: false })
    } catch (err) {
      setState((s) =>
        s.kind === 'loaded'
          ? { ...s, refreshing: false } // stale beats blank
          : { kind: 'error', message: err instanceof Error ? err.message : 'failed' },
      )
    }
  }, [])

  useEffect(() => {
    void load(true)
    timer.current = setInterval(() => void load(false), POLL_MS)
    return () => clearInterval(timer.current)
  }, [load])

  return { state, reload: () => load(false) }
}
