import type { NextFunction, Request, Response } from 'express'
import session from 'express-session'

export const sessionMiddleware = session({
  secret: process.env.SESSION_SECRET ?? 'dev-only',
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, sameSite: 'lax' },
})

declare module 'express-session' {
  interface SessionData {
    userId?: number
  }
}

/** Every /api route except login sits behind this. */
export function requireUser(req: Request, res: Response, next: NextFunction) {
  if (!req.session.userId) {
    res.status(401).json({ error: 'unauthenticated' })
    return
  }
  next()
}
