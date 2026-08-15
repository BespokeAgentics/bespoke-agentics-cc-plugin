import express from 'express'
import { requireUser, sessionMiddleware } from './auth.js'
import { activity } from './routes/activity.js'
import { statuses } from './routes/statuses.js'

const app = express()
app.use(express.json())
app.use(sessionMiddleware)

// Demo login: any email gets a session. Real SSO replaced this in prod.
app.post('/api/login', (req, res) => {
  req.session.userId = 1
  res.json({ ok: true })
})

app.use('/api', requireUser)
app.use(statuses)
app.use(activity)

const port = Number(process.env.PORT ?? 4000)
app.listen(port, () => console.log(`teamboard api on :${port}`))
