import { useState } from 'react'
import { ApiError, apiPost } from '../../lib/api'
import { useToast } from '../../components/Toast'

const MAX_LEN = 140

export function StatusForm({ onPosted }: { onPosted: () => void }) {
  const [body, setBody] = useState('')
  const [emoji, setEmoji] = useState('')
  const [expiresInHours, setExpires] = useState<number | undefined>()
  const [submitting, setSubmitting] = useState(false)
  const [fieldError, setFieldError] = useState<string | null>(null)
  const { push } = useToast()

  const remaining = MAX_LEN - body.length
  const valid = body.trim().length > 0 && remaining >= 0

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!valid || submitting) return
    setSubmitting(true)
    setFieldError(null)
    try {
      await apiPost('/api/statuses', {
        body: body.trim(),
        emoji: emoji || undefined,
        expiresInHours,
      })
      setBody('')
      setEmoji('')
      push('Status posted')
      onPosted()
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setFieldError('That status didn’t validate — check length and emoji.')
      } else {
        push('Couldn’t post your status', 'error')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="status-form" onSubmit={submit}>
      <input
        value={emoji}
        onChange={(e) => setEmoji(e.target.value)}
        placeholder="😀"
        aria-label="Emoji"
        maxLength={4}
      />
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="What are you up to?"
        aria-label="Status"
        rows={2}
      />
      <span className={`status-form__count${remaining < 0 ? ' over' : ''}`}>{remaining}</span>
      <select
        value={expiresInHours ?? ''}
        onChange={(e) => setExpires(e.target.value ? Number(e.target.value) : undefined)}
        aria-label="Clears after"
      >
        <option value="">Doesn’t clear</option>
        <option value="4">4 hours</option>
        <option value="24">1 day</option>
        <option value="72">3 days</option>
      </select>
      <button disabled={!valid || submitting}>{submitting ? 'Posting…' : 'Post'}</button>
      {fieldError && <p role="alert">{fieldError}</p>}
    </form>
  )
}
