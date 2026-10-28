// SqliteDatabase facade over bun:sqlite, for pi-durable's portable SQLite core.
// Contract (pi-durable storage/sqlite/database.d.ts): async ops, one transaction at a time,
// unrelated operations queue behind a running transaction, rollback before rejecting.
import { Database, type Statement } from "bun:sqlite";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import type { SqliteDatabase, SqliteExecutor, SqliteValue } from "@earendil-works/pi-durable/storage/sqlite";
import { SqliteStorage } from "@earendil-works/pi-durable/storage/sqlite";

class Executor implements SqliteExecutor {
	constructor(
		protected readonly db: Database,
		protected readonly statements: Map<string, Statement>,
		protected readonly guard: () => void = () => {},
	) {}
	protected statement(sql: string): Statement {
		let s = this.statements.get(sql);
		if (s === undefined) {
			s = this.db.prepare(sql);
			this.statements.set(sql, s);
		}
		return s;
	}
	protected op<T>(fn: () => T): Promise<T> {
		this.guard();
		return Promise.resolve(fn());
	}
	exec(sql: string): Promise<void> {
		return this.op(() => void this.db.exec(sql));
	}
	run(sql: string, ...params: SqliteValue[]): Promise<void> {
		return this.op(() => void this.statement(sql).run(...(params as never[])));
	}
	get<T extends object>(sql: string, ...params: SqliteValue[]): Promise<T | undefined> {
		return this.op(() => (this.statement(sql).get(...(params as never[])) as T | null) ?? undefined);
	}
	all<T extends object>(sql: string, ...params: SqliteValue[]): Promise<T[]> {
		return this.op(() => this.statement(sql).all(...(params as never[])) as T[]);
	}
}

export class BunSqliteDatabase extends Executor implements SqliteDatabase {
	#tail: Promise<unknown> = Promise.resolve();
	#closed = false;

	constructor(path: string) {
		if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });
		const db = new Database(path, { create: true, strict: true });
		super(db, new Map());
		db.exec("PRAGMA journal_mode = WAL");
		db.exec("PRAGMA synchronous = NORMAL");
		db.exec("PRAGMA busy_timeout = 5000");
	}

	/** Every operation waits for the one before it, so nothing interleaves with a transaction. */
	#serial<T>(fn: () => Promise<T>): Promise<T> {
		const next = this.#tail.then(fn, fn);
		this.#tail = next.catch(() => {});
		return next;
	}

	protected override op<T>(fn: () => T): Promise<T> {
		return this.#serial(async () => fn());
	}

	transaction<T>(callback: (transaction: SqliteExecutor) => Promise<T>): Promise<T> {
		return this.#serial(async () => {
			this.db.exec("BEGIN IMMEDIATE");
			const scope = { active: true };
			const handle = new Executor(this.db, this.statements, () => {
				if (!scope.active) throw new Error("SQLite transaction handle is no longer active");
			});
			try {
				const result = await callback(handle);
				scope.active = false;
				this.db.exec("COMMIT");
				return result;
			} catch (error) {
				scope.active = false;
				try {
					this.db.exec("ROLLBACK");
				} catch (rollbackError) {
					throw new AggregateError([error, rollbackError], "SQLite transaction failed and rollback failed");
				}
				throw error;
			}
		});
	}

	close(): Promise<void> {
		return this.#serial(async () => {
			if (this.#closed) return;
			this.#closed = true;
			for (const s of this.statements.values()) s.finalize();
			this.statements.clear();
			try {
				this.db.exec("PRAGMA wal_checkpoint(TRUNCATE)");
			} finally {
				this.db.close();
			}
		});
	}
}

export const openBunSqliteStorage = (path: string, options?: { prefix?: string }) => SqliteStorage.open(new BunSqliteDatabase(path), options);
