import { useState } from 'react'
import { ToastProvider } from './components/Toast'
import { ActivityFeed } from './features/activity/ActivityFeed'
import { StatusBoard } from './features/status-board/StatusBoard'

type Page = 'board' | 'activity'

export default function App() {
  const [page, setPage] = useState<Page>('board')
  return (
    <ToastProvider>
      <header className="app-shell__header">
        <h1>TeamBoard</h1>
        <nav>
          <button aria-current={page === 'board'} onClick={() => setPage('board')}>
            Board
          </button>
          <button aria-current={page === 'activity'} onClick={() => setPage('activity')}>
            Activity
          </button>
        </nav>
      </header>
      <main>{page === 'board' ? <StatusBoard /> : <ActivityFeed />}</main>
    </ToastProvider>
  )
}
