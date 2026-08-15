import Database from 'better-sqlite3'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const schemaPath = fileURLToPath(new URL('./schema.sql', import.meta.url))

export const db = new Database(process.env.DATABASE_PATH ?? './data/teamboard.db')
db.pragma('journal_mode = WAL')
db.exec(readFileSync(schemaPath, 'utf8'))
