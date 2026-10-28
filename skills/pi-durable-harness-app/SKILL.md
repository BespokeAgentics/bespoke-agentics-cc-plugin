---
name: pi-durable-harness-app
description: Bootstrap a minimal pi-durable Harness app (Bun, Effect, FoldKit, optional Cloudflare Durable Objects), or audit a project's durability and its use of pi-durable tasks, tools, hooks and docs.
disable-model-invocation: true
---

# pi-durable Harness apps: bootstrap and audit

Two modes. Pick from the request:

- **Bootstrap**: "create / scaffold / start a harness app", "new pi-durable app", "add Cloudflare". Produces a working app where every unit of work is a pi-durable task, the UI is a FoldKit (Elm Architecture on Effect) projection of committed state, and the host runs on Bun or a Cloudflare Durable Object.
- **Audit**: "audit / review / check durability", "are we using pi-durable right". Produces a findings report against the checklist in this file.

Both modes start with **Step 0**.

## Ground truth

pi-durable is experimental and changes between releases. Prefer, in order:

1. The installed package's types: `node_modules/@earendil-works/pi-durable/dist/**/*.d.ts`.
2. The package README and spec: https://github.com/earendil-works/pi/tree/main/packages/durable (`README.md`, `docs/spec.md`, `test/examples/*.ts`).
3. The announcement post: https://earendil.com/posts/pi-durable/.

FoldKit is pre-1.0. Its generated `FOLDKIT.md` says the live code is canonical. When a FoldKit API in this file doesn't compile, run `npx create-foldkit-app@latest -n ref -r spa -e websocket-chat -p bun` in a temp dir and copy the shapes from `src/main.ts` there.

## Step 0: detect the installed version and its features

Run in the project root (after `bun install` for a new app):

```sh
D=node_modules/@earendil-works/pi-durable
grep '"version"' $D/package.json
for f in sleepUntil onWake restartLimit retryTask setTimer; do
  printf '%-13s ' $f; grep -rqs "\b$f\b" $D/dist --include=*.d.ts && echo yes || echo no
done
```

What the answers mean (checked against 1.3.0, the npm `latest` when this skill was written, and the repo's `main`):

| Feature | 1.3.0 on npm | repo `main` | If missing |
|---|---|---|---|
| `runtime.sleepUntil` / `{status:"sleeping"}` | no | yes | No durable sleeps. Don't fake them with `setTimeout` inside a phase; model waits as child tasks, or upgrade. |
| `HarnessOptions.onWake`, `Wake` | no | yes | Evictable hosts keep a heartbeat alarm while tasks are live (the Cloudflare template does this). |
| `settings.restartLimit`, `harness.retryTask` | no | yes | No parking of crash-looping tasks; watch for them yourself. |
| `onReport(error, info)` | `onReport(error)` | two args | Use the signature your types declare. |

Everything else this skill uses (tasks with phases, `waiting` with `failFast`/`allSettled`, `runtime.outcomes`, `abort`, `abortTask`, `taskGraph`, `getTask`, `inspect`, `defineDoc`, `defineTool` with `replay`, `hook`, `configure`, `section`, `watchEvents`, `requestId` on `submit`, `openDurableObjectSqliteStorage`, the portable `SqliteStorage`) exists in 1.3.0.

---

# Mode 1: Bootstrap

## What you get

```text
browser (FoldKit)  --WebSocket /rpc, JSON records-->  HarnessHost  --commits-->  SQLite
  Model = last projection         act {requestId}          guard: actionsFor()      bun:sqlite (Bun)
  buttons = actionsFor(job)  <--  view {boot, version}  <-- taskGraph + records      DO SQLite (Cloudflare)
                                                            tasks: app.job --keyed effect--> outside world
```

- `src/shared/protocol.ts`: Effect Schemas for the wire, plus `actionsFor`, the state-to-UI contract that the client renders from and the host re-checks.
- `src/server/app.ts`: the durable domain: one task (`app.job`) with the effect sandwich, a keyed external effect, an `abort` that undoes it, and an `Intents` document that makes each user intent exactly-once.
- `src/server/host.ts`: platform-agnostic host: opens the Harness, applies intents, projects task graph + records into a view, and pushes it.
- `src/server/bun-sqlite.ts`: a `SqliteDatabase` facade over `bun:sqlite` for pi-durable's portable SQLite core (pi-durable ships Node and Cloudflare adapters, not a Bun one).
- `src/server/main.ts`: Bun entry. Effect scopes the Harness and the server, so SIGINT/SIGTERM close cleanly.
- `src/client/*`: FoldKit app: `ManagedResource` for the socket, a `Subscription` for records, `Command`s for sends and reconnect.
- `cloudflare/*`: a Worker routing `/rpc?session=<id>` to one SQLite-backed Durable Object per session.
- `src/server/orchestrator.ts` (optional): the master-orchestrator pattern (see "Add-on" below).
- Tests: `host.test.ts` (dedupe, guard, crash recovery), `orchestrator.test.ts` (faux model), `scripts/crash-test.ts` (kill -9 a live host).

This exact tree was built and checked with Bun 1.4.2, pi-durable 1.3.0, effect 4.0.0 and foldkit 0.168.0: typecheck, `bun test`, `vite build`, `crash-test`, `wrangler deploy --dry-run`, and `wrangler dev` against the Durable Object.

## Procedure

1. **Prerequisites.** Bun ≥ 1.2 (`bun --version`). Node is not needed to run the app. For Cloudflare: a Cloudflare account, and `bunx wrangler login` before deploying.
2. **Name and place.** Use the name the user gave (kebab-case) or `harness-app`. Create the directory; refuse to write into a non-empty one unless the user says so.
3. **Write every file below** exactly, replacing `harness-app` in `package.json` and `cloudflare/wrangler.jsonc` with the app name. Skip `cloudflare/` if the user doesn't want Cloudflare, and the orchestrator files if they don't want agents (remove those two files; nothing else imports them).
4. **Install:** `bun install`. Then run Step 0 and tell the user which features are missing for their version.
5. **Verify, in order, and stop at the first failure:**
   - `bun run typecheck` (and `bunx tsc --noEmit -p cloudflare` if included)
   - `bun test`
   - `bun run build`
   - `bun run crash-test`: must print `PASS: the job survived a hard kill`
   - Cloudflare: `bunx wrangler deploy --dry-run -c cloudflare/wrangler.jsonc --outdir .wrangler/dry`
6. **Run it:** `bun run dev` (Vite on :5173 proxies `/rpc` to the Bun host on :8787), or `bun run build && bun start` (the host serves `dist/` on :8787).
7. **Tell the user** what was created, the results of step 5, the Step 0 feature gaps, and the next step: replace `simulatedEffects()` with real keyed calls.

If `wrangler dev` reports a missing `workerd` binary, run `bun pm trust --all` (Bun blocks lifecycle scripts by default) and retry.

## Files

### package.json
```json
{
  "name": "harness-app",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "bun scripts/dev.ts",
    "dev:server": "bun --watch src/server/main.ts",
    "dev:client": "vite",
    "build": "vite build",
    "start": "bun src/server/main.ts",
    "typecheck": "tsc --noEmit",
    "test": "bun test",
    "cf:dev": "vite build && wrangler dev -c cloudflare/wrangler.jsonc",
    "cf:deploy": "vite build && wrangler deploy -c cloudflare/wrangler.jsonc",
    "crash-test": "bun scripts/crash-test.ts"
  },
  "dependencies": {
    "@earendil-works/chord": "1.3.0",
    "@earendil-works/pi-ai": "1.3.0",
    "@earendil-works/pi-durable": "1.3.0",
    "@effect/platform-browser": "4.0.0",
    "effect": "4.0.0",
    "foldkit": "0.168.0"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.20251001.0",
    "@foldkit/vite-plugin": "0.27.1",
    "@types/bun": "latest",
    "typescript": "^5.9.3",
    "vite": "^8.3.1",
    "wrangler": "^4.40.0"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "types": ["bun"],
    "strict": true,
    "skipLibCheck": true,
    "noEmit": true,
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "exactOptionalPropertyTypes": false
  },
  "include": ["src", "scripts", "vite.config.ts"]
}
```

### .gitignore
```text
node_modules/
dist/
data/
.wrangler/
```

### index.html
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Harness app</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/client/entry.ts"></script>
  </body>
</html>
```

### vite.config.ts
```ts
import { defineConfig } from 'vite'

import { foldkit } from '@foldkit/vite-plugin'

export default defineConfig({
  plugins: [foldkit()],
  optimizeDeps: { entries: ['src/client/entry.ts'] },
  // In dev, Vite serves the client and forwards the WebSocket to the Bun host.
  server: { proxy: { '/rpc': { target: 'ws://localhost:8787', ws: true } } },
})
```

### src/shared/protocol.ts
```ts
// The wire between the UI and the Harness host. Both sides import this file.
// Records follow pi's RPC shape: commands carry an `id`; the host answers with a `response`
// carrying the same `id`, and pushes `view` records whenever committed state changes.
import { Schema } from "effect";

// ---------------------------------------------------------------- commands (client -> host)

export const Act = Schema.TaggedStruct("act", {
	id: Schema.String,
	/** Idempotency key for the intent. A retry with the same requestId never acts twice. */
	requestId: Schema.String,
	command: Schema.Literals(["job.start", "job.cancel"]),
	jobId: Schema.optional(Schema.String),
	label: Schema.optional(Schema.String),
});
export type Act = typeof Act.Type;

export const ClientCommand = Schema.Union([Act, Schema.TaggedStruct("get_state", { id: Schema.String })]);
export type ClientCommand = typeof ClientCommand.Type;

// ---------------------------------------------------------------- records (host -> client)

export const JobStage = Schema.Literals(["queued", "working", "cancelling", "done", "failed", "cancelled"]);
export type JobStage = typeof JobStage.Type;

export const JobView = Schema.Struct({
	id: Schema.String,
	label: Schema.String,
	stage: JobStage,
	detail: Schema.String,
	recovered: Schema.Boolean,
});
export type JobView = typeof JobView.Type;

export const ViewRecord = Schema.TaggedStruct("view", {
	/** One id per host process. Versions restart with each process, so compare (boot, version). */
	boot: Schema.String,
	version: Schema.Number,
	host: Schema.Literals(["open", "restarting"]),
	jobs: Schema.Array(JobView),
});
export const ResponseRecord = Schema.TaggedStruct("response", {
	id: Schema.String,
	success: Schema.Boolean,
	error: Schema.optional(Schema.String),
	duplicate: Schema.optional(Schema.Boolean),
});
export const HostRecord = Schema.Union([ViewRecord, ResponseRecord]);
export type HostRecord = typeof HostRecord.Type;

// ---------------------------------------------------------------- the state-to-UI contract

export type Offered = { readonly command: Act["command"]; readonly label: string };

/** What a job offers in each stage. The client renders it; the host refuses anything else. */
export function actionsFor(job: JobView | undefined): ReadonlyArray<Offered> {
	if (job === undefined) return [{ command: "job.start", label: "Start a job" }];
	switch (job.stage) {
		case "queued":
		case "working":
			return [{ command: "job.cancel", label: "Cancel" }];
		default:
			return [];
	}
}
```

### src/server/app.ts
```ts
// Your durable domain: tasks, documents and the extension that installs them.
// Rules this file follows (from the pi-durable docs):
// - Every step is a task phase that ends in a commit; a phase reruns from its top after a crash.
// - External effects use an idempotency key derived from the task id, so a rerun never repeats them.
// - Each task undoes its own effect in `abort`.
import { defineDoc, defineExtension, defineTask } from "@earendil-works/pi-durable";

/** Whatever lives outside the commit: a payment provider, an email API, a queue. Keyed calls only. */
export interface Effects {
	perform(key: string, signal?: AbortSignal): Promise<{ receipt: string }>;
	undo(key: string): Promise<boolean>;
}

/** A stand-in that takes a few seconds and remembers keys, as a real provider's idempotency does. */
export function simulatedEffects(ms = 3000): Effects {
	const done = new Map<string, string>();
	return {
		async perform(key, signal) {
			const existing = done.get(key);
			if (existing) return { receipt: existing };
			await new Promise<void>((resolve, reject) => {
				const t = setTimeout(resolve, ms);
				signal?.addEventListener("abort", () => (clearTimeout(t), reject(signal.reason)), { once: true });
			});
			const receipt = `rcpt_${key}`;
			done.set(key, receipt);
			return { receipt };
		},
		async undo(key) {
			return done.delete(key);
		},
	};
}

export type JobInput = { label: string };
export type JobState = { phase: "run" };
export type JobResult = { receipt: string };

export const makeJobTask = (effects: Effects) =>
	defineTask<JobInput, JobState, JobResult>({
		name: "app.job",
		version: 1,
		initial: () => ({ phase: "run" }),
		phases: {
			// Effect sandwich: the task's intent was committed when it was created; perform the keyed
			// effect; commit the outcome. A crash in between reruns this phase with the same key.
			run: async (task, runtime, context) => {
				const { receipt } = await effects.perform(`job-${task.id}`, context.abortSignal);
				await runtime.commit(() => ({ status: "terminal", outcome: { status: "completed", result: { receipt } } }), context);
			},
		},
		abort: async (task, runtime, context) => {
			await effects.undo(`job-${task.id}`);
			await runtime.commit(() => ({ status: "terminal", outcome: { status: "aborted" } }), context);
		},
	});

/** Intents already applied, by requestId: the commit that creates the task also records the key. */
export const Intents = defineDoc<{ byRequest: Record<string, string> }>({
	kind: "app.intents",
	version: 1,
	scope: "session",
	initial: () => ({ byRequest: {} }),
	checkpointWhen: () => false,
});

export const makeAppExtension = (effects: Effects) => {
	const Job = makeJobTask(effects);
	return { Job, extension: defineExtension({ name: "app", tasks: [Job] }) };
};
```

### src/server/host.ts
```ts
// The Harness host: one owner of one storage. Platform-agnostic, so Bun and the Cloudflare
// Durable Object both run it. The UI never touches the Harness: intents come in through
// `handle()`, and a projection of committed state goes out through `broadcast`.
import { BACKGROUND_CONTEXT } from "@earendil-works/chord/context";
import { createModels } from "@earendil-works/pi-ai/models";
import { createRegistry, Harness } from "@earendil-works/pi-durable";
import { actionsFor, type ClientCommand, type HostRecord, type JobStage, type JobView } from "../shared/protocol.ts";
import { type Effects, Intents, makeAppExtension } from "./app.ts";

const context = BACKGROUND_CONTEXT;
type Storage = Parameters<typeof Harness.open>[0];

export type HostOptions = {
	readonly storage: Storage;
	readonly effects: Effects;
	readonly broadcast: (record: HostRecord) => void;
	/**
	 * Called with the number of live tasks whenever it changes. Evictable hosts (Cloudflare) keep an
	 * alarm armed while it is above zero. pi-durable releases after 1.3.0 add `onWake`, which replaces this.
	 */
	readonly onLive?: (live: number) => void;
};

export class HarnessHost {
	#harness!: Harness;
	#root!: Awaited<ReturnType<Harness["root"]>>;
	#Job!: ReturnType<typeof makeAppExtension>["Job"];
	#version = 0;
	#boot = crypto.randomUUID();
	#recovered = new Set<string>();
	#jobs: JobView[] = [];
	#scheduled = false;
	#live = 0;
	#graph!: Awaited<ReturnType<Harness["taskGraph"]>>;

	private constructor(private readonly options: HostOptions) {}

	static async open(options: HostOptions): Promise<HarnessHost> {
		const host = new HarnessHost(options);
		const { Job, extension } = makeAppExtension(options.effects);
		host.#Job = Job;
		const registry = createRegistry();
		registry.install(extension);
		host.#harness = await Harness.open(
			options.storage,
			{
				models: createModels(), // add providers here when you add conversations
				registry,
				onReport: (error: unknown) => console.warn("[pi-durable]", error),
			},
			context,
		);
		host.#root = await host.#harness.root(context);
		// Tasks still live at open were cut off by the last process: they run again from their checkpoint.
		for (const task of (await host.#harness.inspect(context)).tasks) host.#recovered.add(String(task.record.id));
		host.#graph = await host.#harness.taskGraph(context);
		host.#graph.subscribe(() => host.#schedule());
		host.#live = Object.keys(host.#graph.value.tasks).length;
		options.onLive?.(host.#live);
		host.#harness.resume();
		await host.#refresh();
		return host;
	}

	get live(): number {
		return this.#live;
	}

	/** Start the scheduler again, e.g. from an alarm after the process was evicted. */
	resume(): void {
		this.#harness.resume();
	}

	get harness(): Harness {
		return this.#harness;
	}

	view(): HostRecord {
		return { _tag: "view", boot: this.#boot, version: this.#version, host: "open", jobs: this.#jobs };
	}

	async handle(cmd: ClientCommand): Promise<HostRecord> {
		if (cmd._tag === "get_state") return { _tag: "response", id: cmd.id, success: true };
		const job = cmd.jobId === undefined ? undefined : this.#jobs.find((j) => j.id === cmd.jobId);
		// The host re-checks the same contract the UI rendered from.
		if (!actionsFor(job).some((a) => a.command === cmd.command)) return { _tag: "response", id: cmd.id, success: false, error: "No longer offered." };
		if (cmd.command === "job.start") {
			const Job = this.#Job;
			const label = cmd.label ?? `Job ${this.#jobs.length + 1}`;
			const duplicate = await this.#root.commit(async (tx) => {
				const intents = await tx.doc(Intents);
				if (intents.byRequest[cmd.requestId] !== undefined) return true;
				const id = await tx.createTask(Job, { label }, { ownership: { kind: "conversation" } });
				intents.byRequest[cmd.requestId] = String(id);
				return false;
			}, context);
			await this.#refresh();
			return { _tag: "response", id: cmd.id, success: true, duplicate };
		}
		await this.#harness.abortTask(Number(cmd.jobId) as never, context);
		return { _tag: "response", id: cmd.id, success: true };
	}

	async close(): Promise<void> {
		this.#graph.dispose();
		await this.#harness.close(context);
	}

	#schedule(): void {
		if (this.#scheduled) return;
		this.#scheduled = true;
		queueMicrotask(() => {
			this.#scheduled = false;
			void this.#refresh();
		});
	}

	/** Project committed records into the view model and push it. */
	async #refresh(): Promise<void> {
		const intents = await this.#harness.snapshot(Intents, context);
		const ids = Object.values(intents?.byRequest ?? {});
		const graph = this.#graph.value.tasks;
		const live = Object.keys(graph).length;
		if (live !== this.#live) {
			this.#live = live;
			this.options.onLive?.(live);
		}
		const jobs: JobView[] = [];
		for (const id of ids) {
			const record = await this.#harness.getTask(Number(id) as never, context);
			if (!record) continue;
			const node = graph[id];
			const input = record.input as { label: string };
			let stage: JobStage;
			let detail: string;
			if (node) {
				if (node.abortRequested) [stage, detail] = ["cancelling", "Undoing its effect"];
				else if (node.state.status === "running") [stage, detail] = ["working", "Performing its effect"];
				else [stage, detail] = ["queued", this.#recovered.has(id) ? "Picked up after a restart" : "Waiting for the scheduler"];
			} else if (record.state.status === "terminal") {
				const outcome = record.state.outcome as { status: string; result?: { receipt: string }; error?: { message: string } };
				this.#recovered.delete(id);
				if (outcome.status === "completed") [stage, detail] = ["done", `Receipt ${outcome.result?.receipt}`];
				else if (outcome.status === "aborted") [stage, detail] = ["cancelled", "Its effect was undone"];
				else [stage, detail] = ["failed", outcome.error?.message ?? outcome.status];
			} else [stage, detail] = ["queued", "Committed"];
			jobs.push({ id, label: input.label, stage, detail, recovered: this.#recovered.has(id) });
		}
		this.#jobs = jobs.reverse();
		this.#version++;
		this.options.broadcast(this.view());
	}
}
```

### src/server/bun-sqlite.ts
```ts
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
```

### src/server/main.ts
```ts
// Bun entry: one Harness over a SQLite file, a WebSocket for the UI, and the built client.
// Effect owns the lifecycle: the Harness and the server are scoped resources, closed in reverse
// order on SIGINT/SIGTERM, so a clean stop never counts against a task's restart limit.
import { Effect, Exit, Fiber, Schema } from "effect";
import { ClientCommand, type HostRecord } from "../shared/protocol.ts";
import { simulatedEffects } from "./app.ts";
import { openBunSqliteStorage } from "./bun-sqlite.ts";
import { HarnessHost } from "./host.ts";

const PORT = Number(process.env.PORT ?? 8787);
const DB = process.env.HARNESS_DB ?? "./data/session.sqlite";
const decodeCommand = Schema.decodeUnknownExit(Schema.fromJsonString(ClientCommand));

const program = Effect.gen(function* () {
	const sockets = new Set<Bun.ServerWebSocket<unknown>>();
	const broadcast = (record: HostRecord) => {
		const line = JSON.stringify(record);
		for (const ws of sockets) ws.send(line);
	};

	const host = yield* Effect.acquireRelease(
		Effect.promise(async () => HarnessHost.open({ storage: await openBunSqliteStorage(DB), effects: simulatedEffects(), broadcast })),
		(h) => Effect.promise(() => h.close()),
	);

	const server = yield* Effect.acquireRelease(
		Effect.sync(() =>
			Bun.serve({
				port: PORT,
				async fetch(req, srv) {
					const url = new URL(req.url);
					if (url.pathname === "/rpc") return srv.upgrade(req) ? undefined : new Response("Expected a WebSocket", { status: 426 });
					const file = Bun.file(`./dist${url.pathname === "/" ? "/index.html" : url.pathname}`);
					return (await file.exists()) ? new Response(file) : new Response(Bun.file("./dist/index.html"));
				},
				websocket: {
					open(ws) {
						sockets.add(ws);
						ws.send(JSON.stringify(host.view())); // late joiners start from the current view
					},
					close(ws) {
						sockets.delete(ws);
					},
					async message(ws, data) {
						const decoded = decodeCommand(String(data));
						if (Exit.isFailure(decoded)) {
							ws.send(JSON.stringify({ _tag: "response", id: "?", success: false, error: "Malformed command" }));
							return;
						}
						ws.send(JSON.stringify(await host.handle(decoded.value)));
					},
				},
			}),
		),
		(s) => Effect.sync(() => s.stop(true)),
	);

	yield* Effect.logInfo(`Harness app on http://localhost:${server.port} (storage ${DB})`);
	return yield* Effect.never;
});

const fiber = Effect.runFork(Effect.scoped(program));
for (const signal of ["SIGINT", "SIGTERM"] as const) process.on(signal, () => void Effect.runPromise(Fiber.interrupt(fiber)).then(() => process.exit(0)));
```

### src/client/main.ts
```ts
// FoldKit client: The Elm Architecture on Effect. The Model holds only what the host last sent
// (the projection) plus connection and in-flight command ids. Buttons come from the shared
// `actionsFor`, the same function the host uses to refuse stale intents.
import { Duration, Effect, Match, Option, Queue, Schema, Stream } from 'effect'
import { Command, ManagedResource, Runtime, Subscription, type Update } from 'foldkit'
import { type Document, type Html, type HtmlBuilder } from 'foldkit/html'
import { defineMessageUnion } from 'foldkit/message'
import { defineTaggedUnion } from 'foldkit/schema'
import { modifyFields } from 'foldkit/struct'

import { actionsFor, HostRecord, JobView } from '../shared/protocol.ts'

// ?session=<id> picks the session (one Durable Object each on Cloudflare; ignored by the Bun host).
const RPC_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/rpc${location.search}`
const decodeRecord = Schema.decodeUnknownOption(Schema.fromJsonString(HostRecord))

// MODEL

const RpcSocket = ManagedResource.tag<WebSocket>()('RpcSocket')
type RpcSocketService = ManagedResource.ServiceOf<typeof RpcSocket>

export const Connection = defineTaggedUnion({
  Connecting: {},
  Connected: {},
  Lost: { reason: Schema.String },
})

export const Model = Schema.Struct({
  connection: Connection,
  boot: Schema.String,
  version: Schema.Number,
  jobs: Schema.Array(JobView),
  inFlight: Schema.Array(Schema.Struct({ id: Schema.String, jobId: Schema.String })),
  notice: Schema.String,
  seq: Schema.Number,
})
export type Model = typeof Model.Type

// MESSAGE

export const Message = defineMessageUnion({
  ConnectedRpcSocket: {},
  ReleasedRpcSocket: {},
  FailedConnectRpcSocket: { error: Schema.String },
  ClosedRpcSocket: {},
  ReceivedRecord: { json: Schema.String },
  ClickedAction: { command: Schema.Literals(['job.start', 'job.cancel']), jobId: Schema.String },
  CompletedSendAct: { id: Schema.String },
  FailedSendAct: { id: Schema.String, error: Schema.String },
  CompletedWaitReconnect: {},
})
export type Message = typeof Message.Type

// UPDATE

type UpdateReturn = Update.Return<Model, Message, RpcSocketService>

export const update = (model: Model, message: Message) =>
  Message.match<UpdateReturn>(message, {
    ConnectedRpcSocket: () => ({ model: modifyFields(model, { connection: () => Connection.Connected() }) }),
    ReleasedRpcSocket: () => ({ model }),
    FailedConnectRpcSocket: ({ error }) => ({
      model: modifyFields(model, { connection: () => Connection.Lost({ reason: error }) }),
      commands: [WaitReconnect({})],
    }),
    ClosedRpcSocket: () => ({
      model: modifyFields(model, { connection: () => Connection.Lost({ reason: 'Host restarting' }), inFlight: () => [] }),
      commands: [WaitReconnect({})],
    }),
    CompletedWaitReconnect: () => ({ model: modifyFields(model, { connection: () => Connection.Connecting() }) }),
    ReceivedRecord: ({ json }) =>
      Option.match(decodeRecord(json), {
        onNone: () => ({ model }),
        onSome: record =>
          Match.value(record).pipe(
            Match.withReturnType<UpdateReturn>(),
            Match.tag('view', view =>
              view.boot === model.boot && view.version <= model.version
                ? { model }
                : { model: modifyFields(model, { boot: () => view.boot, version: () => view.version, jobs: () => view.jobs }) },
            ),
            Match.tag('response', response => ({
              model: modifyFields(model, {
                inFlight: inFlight => inFlight.filter(f => f.id !== response.id),
                notice: () =>
                  response.success ? (response.duplicate ? 'Already done: that request ran once.' : '') : (response.error ?? 'Refused'),
              }),
            })),
            Match.exhaustive,
          ),
      }),
    ClickedAction: ({ command, jobId }) => {
      const id = `act-${model.seq + 1}`
      return {
        model: modifyFields(model, {
          seq: seq => seq + 1,
          inFlight: inFlight => [...inFlight, { id, jobId }],
        }),
        commands: [SendAct({ id, command, jobId })],
      }
    },
    CompletedSendAct: () => ({ model }),
    FailedSendAct: ({ id, error }) => ({
      model: modifyFields(model, { inFlight: inFlight => inFlight.filter(f => f.id !== id), notice: () => error }),
    }),
  })

// INIT

export const init: Runtime.ApplicationInit<Model, Message> = () => ({
  model: { connection: Connection.Connecting(), boot: '', version: 0, jobs: [], inFlight: [], notice: '', seq: 0 },
})

// COMMAND

export const SendAct = Command.define('SendAct', {
  args: { id: Schema.String, command: Schema.Literals(['job.start', 'job.cancel']), jobId: Schema.String },
  messages: [Message.CompletedSendAct, Message.FailedSendAct],
  execute: ({ id, command, jobId }) =>
    RpcSocket.get.pipe(
      Effect.map(socket => {
        // The requestId is the intent's idempotency key: the host applies each one once.
        const requestId = `${id}-${crypto.randomUUID()}`
        socket.send(JSON.stringify({ _tag: 'act', id, requestId, command, ...(jobId ? { jobId } : {}) }))
        return Message.CompletedSendAct({ id })
      }),
      Effect.catchTag('ResourceNotAvailable', () => Effect.succeed(Message.FailedSendAct({ id, error: 'Not connected' }))),
    ),
})

export const WaitReconnect = Command.define('WaitReconnect', {
  args: {},
  messages: [Message.CompletedWaitReconnect],
  execute: () => Effect.sleep(Duration.seconds(1)).pipe(Effect.as(Message.CompletedWaitReconnect())),
})

// MANAGED RESOURCE

export const managedResources = ManagedResource.make<Model, Message>()(entry => ({
  rpcSocket: entry(Schema.Option(Schema.Null), {
    resource: RpcSocket,
    modelToMaybeRequirements: model =>
      Connection.match(model.connection, {
        Connecting: () => Option.some(null),
        Connected: () => Option.some(null),
        Lost: () => Option.none(),
      }),
    acquire: () =>
      Effect.callback<WebSocket, Error>(resume => {
        const ws = new WebSocket(RPC_URL)
        const onOpen = () => resume(Effect.succeed(ws))
        const onError = () => resume(Effect.fail(new Error('Could not reach the host')))
        ws.addEventListener('open', onOpen, { once: true })
        ws.addEventListener('error', onError, { once: true })
        return Effect.sync(() => {
          ws.removeEventListener('open', onOpen)
          ws.removeEventListener('error', onError)
        })
      }).pipe(Effect.timeout(Duration.seconds(5)), Effect.catchTag('TimeoutError', () => Effect.fail(new Error('Timed out')))),
    release: socket => Effect.sync(() => socket.close()),
    onAcquired: () => Message.ConnectedRpcSocket(),
    onReleased: () => Message.ReleasedRpcSocket(),
    onAcquireError: error => Message.FailedConnectRpcSocket({ error: error instanceof Error ? error.message : 'Unknown error' }),
  }),
}))

// SUBSCRIPTION

const records = (socket: WebSocket) =>
  Stream.callback<typeof Message.ReceivedRecord.Type | typeof Message.ClosedRpcSocket.Type>(queue =>
    Effect.acquireRelease(
      Effect.sync(() => {
        const onMessage = (event: MessageEvent) => Queue.offerUnsafe(queue, Message.ReceivedRecord({ json: String(event.data) }))
        const onClose = () => {
          Queue.offerUnsafe(queue, Message.ClosedRpcSocket())
          Queue.endUnsafe(queue)
        }
        socket.addEventListener('message', onMessage)
        socket.addEventListener('close', onClose)
        return { onMessage, onClose }
      }),
      ({ onMessage, onClose }) =>
        Effect.sync(() => {
          socket.removeEventListener('message', onMessage)
          socket.removeEventListener('close', onClose)
        }),
    ).pipe(Effect.flatMap(() => Effect.never)),
  )

export const subscriptions = Subscription.make<Model, Message, RpcSocketService>()(entry => ({
  hostRecords: entry(
    { isConnected: Schema.Boolean },
    {
      modelToDependencies: model => ({ isConnected: model.connection._tag === 'Connected' }),
      dependenciesToStream: ({ isConnected }) =>
        Stream.when(
          Stream.unwrap(
            RpcSocket.get.pipe(
              Effect.map(records),
              Effect.catchTag('ResourceNotAvailable', () => Effect.succeed(Stream.empty)),
            ),
          ),
          Effect.sync(() => isConnected),
        ),
    },
  ),
}))

// VIEW

const STAGE_TONE: Record<JobView['stage'], string> = {
  queued: 'neutral',
  working: 'info',
  cancelling: 'warning',
  done: 'success',
  failed: 'error',
  cancelled: 'neutral',
}

export const view = (model: Model, h: HtmlBuilder<Message>): Document => {
  const busy = (jobId: string) => model.inFlight.some(f => f.jobId === jobId)
  const offline = model.connection._tag !== 'Connected'
  const button = (label: string, command: 'job.start' | 'job.cancel', jobId: string, primary: boolean): Html =>
    h.button(
      [
        h.Type('button'),
        h.Class(primary ? 'btn btn-primary' : 'btn'),
        h.Disabled(offline || busy(jobId)),
        h.OnClick(Message.ClickedAction({ command, jobId })),
      ],
      [busy(jobId) ? `${label}…` : label],
    )
  return {
    title: 'Harness app',
    body: h.main(
      [h.Class('page')],
      [
        h.header(
          [h.Class('head')],
          [
            h.h1([], ['Jobs.']),
            h.span(
              [h.Class(`pill pill-${offline ? 'warning' : 'success'}`), h.AriaLive('polite')],
              [Connection.match(model.connection, { Connecting: () => 'Connecting', Connected: () => 'Live', Lost: ({ reason }) => reason })],
            ),
          ],
        ),
        h.p([h.Class('lede')], ['Each job is a pi-durable task. Kill the server mid-job and start it again: the job resumes.']),
        h.div([h.Class('bar')], actionsFor(undefined).map(a => button(a.label, a.command, '', true))),
        model.notice ? h.p([h.Class('notice'), h.Role('status')], [model.notice]) : h.span([], []),
        h.ul(
          [h.Class('jobs')],
          model.jobs.map(job =>
            h.li(
              [h.Class('job')],
              [
                h.div(
                  [h.Class('job-text')],
                  [h.strong([], [job.label]), h.span([h.Class('meta')], [`app.job #${job.id} · ${job.detail}`])],
                ),
                h.span([h.Class(`pill pill-${STAGE_TONE[job.stage]}`)], [job.recovered ? `${job.stage} · recovered` : job.stage]),
                h.div([h.Class('job-actions')], actionsFor(job).map(a => button(a.label, a.command, job.id, false))),
              ],
            ),
          ),
        ),
      ],
    ),
  }
}
```

### src/client/entry.ts
```ts
import { Runtime } from 'foldkit'

import { Message, Model, init, managedResources, subscriptions, update, view } from './main.ts'
import './styles.css'

Runtime.run(
  Runtime.makeApplication({
    Model,
    init,
    update,
    view,
    subscriptions,
    managedResources,
    container: document.getElementById('root'),
    devTools: { Message },
  }),
)
```

### src/client/styles.css
```css
:root { --bg: #f8fafc; --fg: #0f172a; --muted: #515f74; --line: #e2e8f0; --card: #fff; --accent: #1d4ed8; --ok: #16a34a; --warn: #d97706; --err: #dc2626; color-scheme: light; }
@media (prefers-color-scheme: dark) { :root { --bg: #050509; --fg: #d0daf0; --muted: #8194bc; --line: #1a2038; --card: #0a0e1a; --accent: #60a5fa; --ok: #4ade80; --warn: #fbbf24; --err: #f87171; color-scheme: dark; } }
body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.6 system-ui, sans-serif; }
.page { max-width: 760px; margin: 0 auto; padding: 48px max(16px, 4vw); display: flex; flex-direction: column; gap: 16px; }
.head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
h1 { margin: 0; font-size: 40px; letter-spacing: -.03em; }
.lede, .meta { color: var(--muted); margin: 0; }
.meta { font: 12px/1.6 ui-monospace, monospace; }
.btn { font: inherit; font-size: 14px; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--line); background: var(--card); color: var(--fg); cursor: pointer; }
.btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.jobs { list-style: none; margin: 0; padding: 0; border: 1px solid var(--line); border-radius: 14px; background: var(--card); }
.job { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: center; padding: 14px 18px; }
.job + .job { border-top: 1px solid var(--line); }
.job-text { display: flex; flex-direction: column; min-width: 0; }
.pill { font: 11px/1.6 ui-monospace, monospace; padding: 2px 8px; border-radius: 99px; border: 1px solid var(--line); color: var(--muted); }
.pill-success { color: var(--ok); } .pill-info { color: var(--accent); } .pill-warning { color: var(--warn); } .pill-error { color: var(--err); }
.notice { margin: 0; padding: 10px 14px; border: 1px solid var(--line); border-radius: 10px; }
```

### src/server/host.test.ts
```ts
import { expect, test } from "bun:test";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { HostRecord } from "../shared/protocol.ts";
import { simulatedEffects } from "./app.ts";
import { openBunSqliteStorage } from "./bun-sqlite.ts";
import { HarnessHost } from "./host.ts";

const until = async (check: () => boolean, ms = 5000) => {
	const end = Date.now() + ms;
	while (!check()) {
		if (Date.now() > end) throw new Error("timed out");
		await Bun.sleep(20);
	}
};
const lastView = (records: HostRecord[]) => [...records].reverse().find((r) => r._tag === "view") as Extract<HostRecord, { _tag: "view" }>;

test("an intent runs once per requestId, and stale actions are refused", async () => {
	const records: HostRecord[] = [];
	const db = join(mkdtempSync(join(tmpdir(), "harness-")), "s.sqlite");
	const host = await HarnessHost.open({ storage: await openBunSqliteStorage(db), effects: simulatedEffects(50), broadcast: (r) => records.push(r) });
	const a = await host.handle({ _tag: "act", id: "1", requestId: "r", command: "job.start" });
	const b = await host.handle({ _tag: "act", id: "2", requestId: "r", command: "job.start" });
	expect(a).toMatchObject({ success: true, duplicate: false });
	expect(b).toMatchObject({ success: true, duplicate: true });
	await until(() => lastView(records)?.jobs[0]?.stage === "done");
	expect(lastView(records).jobs).toHaveLength(1);
	const stale = await host.handle({ _tag: "act", id: "3", requestId: "r2", command: "job.cancel", jobId: lastView(records).jobs[0]!.id });
	expect(stale).toMatchObject({ success: false });
	await host.close();
});

test("a job cut off by a crash finishes after reopening the same storage", async () => {
	const db = join(mkdtempSync(join(tmpdir(), "harness-")), "s.sqlite");
	const first: HostRecord[] = [];
	const host1 = await HarnessHost.open({ storage: await openBunSqliteStorage(db), effects: simulatedEffects(10_000), broadcast: (r) => first.push(r) });
	await host1.handle({ _tag: "act", id: "1", requestId: "r", command: "job.start" });
	await until(() => lastView(first)?.jobs[0]?.stage === "working");
	await host1.close(); // close leaves the running phase pending, as a crash does
	const second: HostRecord[] = [];
	const host2 = await HarnessHost.open({ storage: await openBunSqliteStorage(db), effects: simulatedEffects(50), broadcast: (r) => second.push(r) });
	expect(lastView(second).jobs[0]?.recovered).toBe(true);
	await until(() => lastView(second)?.jobs[0]?.stage === "done");
	await host2.close();
});
```

### scripts/dev.ts
```ts
export {}
// Runs the Bun host (with --watch) and the Vite client together.
const procs = [
  Bun.spawn(['bun', '--watch', 'src/server/main.ts'], { stdout: 'inherit', stderr: 'inherit' }),
  Bun.spawn(['bunx', 'vite'], { stdout: 'inherit', stderr: 'inherit' }),
]
const stopAll = () => {
  for (const p of procs) p.kill('SIGINT')
  process.exit(0)
}
process.on("SIGINT", stopAll)
process.on("SIGTERM", stopAll)
await Promise.race(procs.map(p => p.exited))
stopAll()
```

### scripts/crash-test.ts
```ts
// Proves recovery: start a job, kill -9 the host mid-job, start it again, expect the job done.
export {}
const PORT = 8899
const DB = `./data/crash-test-${Date.now()}.sqlite`
const env = { ...process.env, PORT: String(PORT), HARNESS_DB: DB }
const start = () => Bun.spawn(['bun', 'src/server/main.ts'], { env, stdout: 'ignore', stderr: 'inherit' })
const connect = async () => {
  for (let i = 0; i < 50; i++) {
    try {
      const ws = new WebSocket(`ws://localhost:${PORT}/rpc`)
      await new Promise((ok, fail) => ((ws.onopen = ok), (ws.onerror = fail)))
      return ws
    } catch {
      await Bun.sleep(100)
    }
  }
  throw new Error('host did not start')
}
const nextView = (ws: WebSocket, pred: (v: any) => boolean, ms = 10_000) =>
  new Promise<any>((ok, fail) => {
    const t = setTimeout(() => fail(new Error('timed out waiting for view')), ms)
    ws.addEventListener('message', e => {
      const r = JSON.parse(String(e.data))
      if (r._tag === 'view' && pred(r)) (clearTimeout(t), ok(r))
    })
  })

let host = start()
let ws = await connect()
const working = nextView(ws, v => v.jobs[0]?.stage === 'working')
ws.send(JSON.stringify({ _tag: 'act', id: '1', requestId: `crash-${Date.now()}`, command: 'job.start', label: 'Crash test' }))
const before = await working
console.log(`job #${before.jobs[0].id} is working; killing the host with SIGKILL`)
host.kill(9)
await host.exited
host = start()
ws = await connect()
const after = await nextView(ws, v => v.jobs[0]?.stage === 'done')
console.log(`after restart: job #${after.jobs[0].id} ${after.jobs[0].stage} (${after.jobs[0].detail})`)
host.kill('SIGINT')
await host.exited
console.log('PASS: the job survived a hard kill')
process.exit(0)
```

### cloudflare/wrangler.jsonc
```jsonc
{
  "$schema": "../node_modules/wrangler/config-schema.json",
  "name": "harness-app",
  "main": "src/worker.ts",
  "compatibility_date": "2025-09-01",
  "compatibility_flags": ["nodejs_compat"],
  // The built FoldKit client. /rpc goes to the Worker first; everything else is a static asset.
  "assets": {
    "directory": "../dist",
    "binding": "ASSETS",
    "not_found_handling": "single-page-application",
    "run_worker_first": ["/rpc"]
  },
  // One SQLite-backed Durable Object per session: the object is the single owner pi-durable requires.
  "durable_objects": { "bindings": [{ "name": "SESSION", "class_name": "Session" }] },
  "migrations": [{ "tag": "v1", "new_sqlite_classes": ["Session"] }]
}
```

### cloudflare/tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2023"],
    "types": ["@cloudflare/workers-types"],
    "strict": true,
    "skipLibCheck": true,
    "noEmit": true,
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true
  },
  "include": ["src", "../src/shared", "../src/server/app.ts", "../src/server/host.ts"]
}
```

### cloudflare/src/worker.ts
```ts
// Cloudflare deployment: a Worker routes /rpc?session=<id> to that session's Durable Object.
// The object opens the same HarnessHost over its own SQLite storage, so commits are its storage
// transactions, and one object per session gives pi-durable the single owner it requires.
import { DurableObject } from "cloudflare:workers";
import { openDurableObjectSqliteStorage } from "@earendil-works/pi-durable/storage/sqlite/cloudflare";
import { Exit, Schema } from "effect";
import { simulatedEffects } from "../../src/server/app.ts";
import { HarnessHost } from "../../src/server/host.ts";
import { ClientCommand, type HostRecord } from "../../src/shared/protocol.ts";

export interface Env {
	SESSION: DurableObjectNamespace<Session>;
	ASSETS: Fetcher;
}

const decodeCommand = Schema.decodeUnknownExit(Schema.fromJsonString(ClientCommand));
const HEARTBEAT_MS = 30_000;

export class Session extends DurableObject<Env> {
	#host!: HarnessHost;

	constructor(ctx: DurableObjectState, env: Env) {
		super(ctx, env);
		void ctx.blockConcurrencyWhile(async () => {
			// Arm a fallback first: if open or recovery throws, the alarm starts the object again.
			const fallback = Date.now() + 60_000;
			const current = await ctx.storage.getAlarm();
			if (current === null || current > fallback) await ctx.storage.setAlarm(fallback);
			const storage = await openDurableObjectSqliteStorage(ctx.storage);
			this.#host = await HarnessHost.open({
				storage,
				effects: simulatedEffects(), // replace with your keyed external calls
				broadcast: (record) => this.#broadcast(record),
				onLive: (live) => void this.#arm(live).catch(() => ctx.abort("Alarm write failed")),
			});
			await this.#arm(this.#host.live);
		});
	}

	override async fetch(request: Request): Promise<Response> {
		if (request.headers.get("Upgrade") !== "websocket") return new Response("Expected a WebSocket", { status: 426 });
		const pair = new WebSocketPair();
		const [client, server] = Object.values(pair) as [WebSocket, WebSocket];
		this.ctx.acceptWebSocket(server); // hibernatable: the object can sleep with sockets open
		server.send(JSON.stringify(this.#host.view()));
		return new Response(null, { status: 101, webSocket: client });
	}

	override async webSocketMessage(ws: WebSocket, message: string | ArrayBuffer): Promise<void> {
		const decoded = decodeCommand(typeof message === "string" ? message : new TextDecoder().decode(message));
		if (Exit.isFailure(decoded)) {
			ws.send(JSON.stringify({ _tag: "response", id: "?", success: false, error: "Malformed command" }));
			return;
		}
		// Arm before any call that can start work: an early alarm is harmless, a missing one strands it.
		await this.#arm(Math.max(1, this.#host.live));
		ws.send(JSON.stringify(await this.#host.handle(decoded.value)));
	}

	override async webSocketClose(ws: WebSocket, code: number, reason: string): Promise<void> {
		ws.close(code, reason);
	}

	/** Wakes an evicted object: continue work a lost instance left, then keep the heartbeat while work is live. */
	override async alarm(): Promise<void> {
		this.#host.resume();
		await this.#arm(this.#host.live);
	}

	#broadcast(record: HostRecord): void {
		const line = JSON.stringify(record);
		for (const ws of this.ctx.getWebSockets()) ws.send(line);
	}

	async #arm(live: number): Promise<void> {
		if (live > 0) await this.ctx.storage.setAlarm(Date.now() + HEARTBEAT_MS);
		else await this.ctx.storage.deleteAlarm();
	}
}

export default {
	async fetch(request, env): Promise<Response> {
		const url = new URL(request.url);
		if (url.pathname === "/rpc") {
			const session = url.searchParams.get("session") ?? "default";
			return env.SESSION.get(env.SESSION.idFromName(session)).fetch(request);
		}
		return env.ASSETS.fetch(request);
	},
} satisfies ExportedHandler<Env>;
```

## Cloudflare notes

- **One owner.** pi-durable has no cross-process locking; one process owns a storage. A Durable Object per session id is that owner. Route every client of a session to the same id (`idFromName(session)`).
- **Waking up.** An evicted object only runs again on a request or an alarm. With 1.3.0 the template keeps an alarm 30 s out while any task is live, and `alarm()` calls `resume()`. On a release with `onWake`, switch to the README pattern: pass `onWake` to `Harness.open`, arm `min(heartbeat, wake.at)` in it, and arm before every call that can start work (submit, abortTask, compact, abort):

  ```ts
  async #arm(wake: Wake) {
    const heartbeat = wake.active ? Date.now() + 60_000 : undefined;
    const at = heartbeat === undefined || wake.at === undefined ? (heartbeat ?? wake.at) : Math.min(heartbeat, wake.at);
    if (at === undefined) await this.ctx.storage.deleteAlarm(); else await this.ctx.storage.setAlarm(at);
  }
  ```
- **Fallback alarm first.** The constructor arms a fallback alarm before opening, so an object whose open throws is started again.
- **Sharing the object's SQLite** with your own tables: open both through one `DurableObjectSqliteDatabase` and pass `{ prefix: "pi_" }` (README, Storage).
- **Not verified locally:** eviction and alarm wake-up. After the first deploy, start a job, then force a new deployment or wait for eviction, and confirm the job finishes.

## Add-on: master orchestrator (agent-driven UI)

For apps where a session's orchestrator receives UI Actions and subagents decide what the interface shows. Pattern (all on pi-durable primitives):

- The root conversation is the orchestrator. Every UI Action is `root.submit({ type: "input", content: JSON.stringify(action), requestId })`. Busy conversations queue it (`whenBusy` defaults to follow-up).
- Its only tool, `delegate`, creates a child conversation owned by the tool call (`ownership: { kind: "task", taskId: api.taskId }`), selects one specialist extension, and submits the brief with `requestId: \`delegate:${api.taskId}\``. `replay: "safe"` plus `scanConversations({ ownerTaskId })` makes a rerun find the same child.
- Specialists answer only through `render`, whose TypeBox schema is the UI contract. It patches a session document (`Surface`) and returns `control: { terminate: true }`, so one Action costs two model calls.
- The host watches `Surface` (`harness.watchDoc`) and pushes it to the client like any other projection; buttons in it carry the next Action's command.

### src/server/orchestrator.ts
```ts
// Optional add-on: a master orchestrator that turns UI Actions into interface changes.
// The root conversation is the orchestrator; each Action is a submission to it (with a requestId).
// It delegates to a specialist subagent (a child conversation owned by the tool call), whose only
// way to answer is the `render` tool: a TypeBox schema that patches the Surface document.
import { Type } from "@earendil-works/pi-ai";
import { configure, defineDoc, defineExtension, defineTool, type Extension, section } from "@earendil-works/pi-durable";

export const Surface = defineDoc<{
	version: number;
	by: string | null;
	headline: string;
	body: string;
	actions: { label: string; command: string }[];
	lastCall: string | null;
}>({
	kind: "app.surface",
	version: 1,
	scope: "session",
	initial: () => ({ version: 0, by: null, headline: "", body: "", actions: [], lastCall: null }),
	checkpointWhen: () => false,
});

const Action = Type.Object(
	{ label: Type.String({ minLength: 1, maxLength: 40 }), command: Type.String({ pattern: "^[a-z]+\\.[a-z_]+$", maxLength: 40 }) },
	{ additionalProperties: false },
);

const render = defineTool({
	name: "render",
	description: "Change the interface. Omit a field to keep it. Each action is a button: its command is what the orchestrator receives on click.",
	parameters: Type.Object(
		{ headline: Type.Optional(Type.String({ maxLength: 70 })), body: Type.Optional(Type.String({ maxLength: 600 })), actions: Type.Optional(Type.Array(Action, { maxItems: 4 })) },
		{ additionalProperties: false },
	),
	replay: "safe", // idempotent: a rerun finds its own lastCall and skips
	execute: async (args, api, context) => {
		const version = await api.commit(async (tx) => {
			const s = await tx.doc(Surface);
			if (s.lastCall === String(api.taskId)) return s.version;
			if (args.headline !== undefined) s.headline = args.headline;
			if (args.body !== undefined) s.body = args.body;
			if (args.actions !== undefined) s.actions = args.actions;
			s.version += 1;
			s.by = String(api.conversationId);
			s.lastCall = String(api.taskId);
			return s.version;
		}, context);
		return { output: [{ type: "text", text: `Interface v${version}` }], control: { terminate: true } };
	},
});
export const SurfaceTools = defineExtension({ name: "surface", tools: [render] });

export function makeOrchestrator(specialists: Record<string, string>, model: { provider: string; modelId: string }) {
	const agents: Record<string, Extension> = Object.fromEntries(
		Object.entries(specialists).map(([name, role]) => [
			name,
			defineExtension({ name: `agent.${name}`, sections: [section("agent", () => name), section("role", () => `${role}\nAnswer only by calling render once.`)] }),
		]),
	);
	const delegate = defineTool({
		name: "delegate",
		description: "Hand the action to one specialist with a self-contained brief.",
		parameters: Type.Object({ agent: Type.Union(Object.keys(specialists).map((k) => Type.Literal(k))), brief: Type.String({ maxLength: 1500 }) }, { additionalProperties: false }),
		replay: "safe", // a rerun finds the same child conversation and the same submission
		execute: async (args, api, context) => {
			const child = await api.commit(async (tx) => {
				const existing = (await tx.scanConversations({ ownerTaskId: api.taskId }, 1)).items[0];
				if (existing !== undefined) return existing.id;
				const created = await tx.createConversation({ ownership: { kind: "task", taskId: api.taskId } });
				await configure(tx, created.id, { model, extensions: [agents[args.agent]!, SurfaceTools] });
				return created.id;
			}, context);
			await api.details({ conversationId: child, agent: args.agent }, context);
			const handle = (await api.conversation(child, context))!;
			const settled = await (await handle.submit({ type: "input", content: args.brief, requestId: `delegate:${api.taskId}` }, context)).wait(context);
			return { output: [{ type: "text", text: `${args.agent}: ${settled.status}` }], control: { terminate: true } };
		},
	});
	const Orchestrator = defineExtension({
		name: "orchestrator",
		tools: [delegate],
		sections: [
			section("agent", () => "orchestrator"),
			section("role", () => "Every user turn is a UI Action as JSON {command, args}. Call delegate once with the right specialist. Never answer yourself."),
		],
	});
	return { Orchestrator, extensions: [Orchestrator, SurfaceTools, ...Object.values(agents)] };
}
```

### src/server/orchestrator.test.ts
```ts
import { expect, test } from "bun:test";
import { BACKGROUND_CONTEXT as context } from "@earendil-works/chord/context";
import { createModels } from "@earendil-works/pi-ai/models";
import { fauxAssistantMessage, fauxProvider, fauxToolCall } from "@earendil-works/pi-ai/providers/faux";
import { createRegistry, Harness, MemoryStorage } from "@earendil-works/pi-durable";
import { makeOrchestrator, Surface } from "./orchestrator.ts";

test("an Action becomes a delegate call, then a render that patches the Surface", async () => {
	const faux = fauxProvider();
	const models = createModels();
	models.setProvider(faux.provider);
	const model = { provider: "faux", modelId: "faux-1" };
	faux.setResponses([
		fauxAssistantMessage([fauxToolCall("delegate", { agent: "returns", brief: "return.start for FO-1042" })], { stopReason: "toolUse" }),
		fauxAssistantMessage([fauxToolCall("render", { headline: "What would you like to return?", actions: [{ label: "Back", command: "order.overview" }] })], { stopReason: "toolUse" }),
	]);
	const { Orchestrator, extensions } = makeOrchestrator({ returns: "You own returns." }, model);
	const registry = createRegistry();
	for (const e of extensions) registry.install(e);
	const harness = await Harness.open(new MemoryStorage(), { models, registry, settings: { extensions: [] } }, context);
	const root = await harness.root(context, { agent: { model, extensions: [Orchestrator] } });
	const action = JSON.stringify({ command: "return.start", args: {} });
	const first = await root.submit({ type: "input", content: action, requestId: "a-1" }, context);
	const again = await root.submit({ type: "input", content: action, requestId: "a-1" }, context);
	expect(again.id).toBe(first.id); // exactly once
	expect((await first.wait(context)).status).toBe("done");
	const surface = await harness.snapshot(Surface, context);
	expect(surface?.headline).toBe("What would you like to return?");
	expect(surface?.actions[0]?.command).toBe("order.overview");
	expect(faux.state.callCount).toBe(2); // terminate: no extra model request after render or delegate
	await harness.close(context);
});
```

Wiring it into the host: install `extensions` in the registry, open with `settings: { extensions: [] }`, create the root with `{ agent: { model, extensions: [Orchestrator] } }`, and set a real provider: `models.setProvider(anthropicProvider())` from `@earendil-works/pi-ai/providers/anthropic` (reads `ANTHROPIC_API_KEY`). List model ids with `models.getModels().filter(m => m.provider === "anthropic")` and use one the user picks. Don't hard-code an id from memory.

Two traps seen while building this:
- A host-side `root.commit(...)` while the root conversation is mid-run waits for the run. Don't put per-action bookkeeping in a root commit on the hot path; track it in the host or in the tool's own commit.
- A process restart loses in-memory `submission.wait()` promises. Resubmit pending Actions with the same `requestId` after reopening; Pi returns the original submission to wait on.

---

# Mode 2: Audit

## Procedure

1. Run **Step 0**. Record the version and missing features; findings must not recommend APIs the installed version lacks without saying "after upgrading".
2. **Inventory** (read-only):

   ```sh
   rg -n "Harness\.open|openNodeSqliteStorage|openDurableObjectSqliteStorage|SqliteStorage\.open|MemoryStorage|openNodeJsonlStorage" -g '!node_modules'
   rg -n "defineTask|defineTool|defineDoc|defineExtension|hook\(|wrapTool|section\(" -g '!node_modules'
   rg -n "\.submit\(|createTask\(|abortTask\(|retryTask\(|sleepUntil|runtime\.commit|api\.commit|replay:|background:|abandonOnRestart|memo\(" -g '!node_modules'
   rg -n "harness\.closed|\.close\(|SIGTERM|SIGINT|onReport|onWake|setAlarm|resume\(\)" -g '!node_modules'
   ```
3. **Read every hit in context.** A search hit is a lead, not a finding: a multi-line `submit({...})` may carry `requestId` on a later line, and an in-memory store may be a deliberate test double. Read each `defineTask` phase by phase, each tool's `execute`, and each host entry point.
4. **Check every rule below.** For each violation record: rule ID, severity, `file:line`, evidence (the code), why it breaks durability, and the fix.
5. **Optional dynamic check**, if the project has a runnable host: adapt `scripts/crash-test.ts` from the bootstrap. Start a unit of work, `kill -9` the host mid-phase, restart on the same storage, and assert the outcome is correct and no external effect ran twice.
6. **Write the report** in the format at the end. Don't change code during an audit unless the user asks.

Severity:
- **Critical**: work or money can be lost or done twice (missing idempotency key, MemoryStorage in production, two owners of one storage).
- **High**: work can stall or be stranded (no resume after open, no alarm on an evictable host, waits that never settle).
- **Medium**: recovery or visibility is degraded (no `harness.closed` handling, UI that can't re-baseline after a restart, no `onReport`).
- **Low**: hygiene (missing `version` bumps on unchanged tasks, naming, unused `background`).

## Checklist

### H: host, storage, lifecycle

- **H1 One owner per storage.** Exactly one process opens a given SQLite file / JSONL dir / Durable Object storage at a time. Flag several replicas, workers or cron jobs opening the same path. (README, Storage: "One process owns a storage at a time; there is no cross-process locking.")
- **H2 Real storage in production.** `MemoryStorage` persists nothing; JSONL keeps all history in memory too ("use SQLite for long-running agents"). Critical if a production path uses MemoryStorage.
- **H3 Resume after open.** After `Harness.open` the host calls `harness.resume()`, or submits or waits, which also start the scheduler. Otherwise work a dead process left stays pending.
- **H4 Clean close.** Shutdown signals call `harness.close(context)`. A close is not counted toward the restart limit; a crash is. Task code must honor `context.abortSignal`, because closing waits for running task code to return.
- **H5 Reopen on failure.** A storage error ends the Harness (README, Errors rule 1). Expect `harness.closed.then(end => end.reason === "failed" && reopen())` or equivalent supervision.
- **H6 One clock.** Every process opening one storage uses the same `now` (sleep deadlines are stored on it).
- **H7 Errors are reported.** `onReport` is wired to logs or telemetry, with the signature the installed types declare.
- **H8 Evictable hosts wake.** On Cloudflare (or any host that can be evicted): `blockConcurrencyWhile` around open, a fallback alarm armed before open, `alarm()` calls `resume()`, and an alarm is armed before any call that can start work. Use `onWake` when available, otherwise a heartbeat while tasks are live. A missing alarm strands work (High).
- **H9 Parked tasks are visible.** If the version has `restartLimit`, something shows tasks blocked with `restart_limit` and offers `retryTask`.

### T: tasks (`defineTask`)

- **T1 Every phase ends in a commit.** Each phase returns after `runtime.commit` of a next checkpoint, `waiting`, `sleeping` or `terminal`, or after `sleepUntil`. A phase that returns without committing is a bug.
- **T2 No waiting inside a phase.** No `setTimeout`, polling loops or long awaits for *time* inside a phase: a phase reruns from its top after a restart. Use `sleepUntil` / `{status:"sleeping"}` (if available), or end the phase and continue in the next with what it needs in the checkpoint. Awaiting the external call itself is fine (that is the effect).
- **T3 Effect sandwich with a key.** Every external effect in a phase or abort handler (payment, email, HTTP POST, queue publish, LLM call with side effects) passes an idempotency key derived from `task.id` (e.g. `payment-${task.id}`), and the provider honors it. Without one, a crash after the effect and before the commit repeats it (Critical).
- **T4 Abort undoes.** A task with external effects has an `abort` handler that compensates with the same key and commits `{status:"terminal", outcome:{status:"aborted"}}`. Abort handlers can't return `waiting` or create owned children.
- **T5 Stable values across reruns.** Values a rerun must reproduce (`Date.now()`, random ids, a chosen option) live in the checkpoint or in `runtime.memo(name, candidate)` (first writer wins), not recomputed in the phase.
- **T6 Children and waits.** Child tasks are created inside a commit with `ownership: { kind: "task", taskId: task.id }`; the parent commits `waiting` with `on` and `policy`, and reads results with `runtime.outcomes()` in its next phase. `failFast` aborts the other tasks in `on`, so use it only on tasks the parent owns; use `allSettled` for dependencies on tasks it doesn't own.
- **T7 Ownership is deliberate.** Work that must survive the parent's abort uses `{ background: true }`. Tasks awaited only in memory by a creator that won't resume them use `abandonOnRestart: true`.
- **T8 Versions.** A change to a task's phases or state shape bumps `version` and migrates. Expect `task_too_old` / `migration_failed` blocks otherwise.
- **T9 Phases honor cancellation.** Long phase code passes `context.abortSignal` to its I/O.

### C: tools (`defineTool`) and subagents

- **C1 `replay: "safe"` only when idempotent.** A replay-safe tool's `execute` must produce the same effect when rerun: keyed external calls, reuse of an existing child (`scanConversations({ ownerTaskId: api.taskId })`), first-writer checks in its commits. Otherwise leave replay off; the model then gets an `interrupted` result.
- **C2 Keys in tools.** External effects in `execute` are keyed by `api.taskId`. Nested `api.executeTool()` calls follow their own replay policy; a replay-safe tool with external effects still needs its own idempotency.
- **C3 Subagents are owned.** A subagent's conversation is created in `api.commit` with `ownership: { kind: "task", taskId: api.taskId }`, and its input is submitted with a `requestId` derived from `api.taskId`.
- **C4 Ending runs on purpose.** Tools whose result should end the run return `control: { terminate: true }` (saves a model request). Tools that should hand off use `control: { handoff }`.
- **C5 Exposure.** `callers` and `modelTools` limit which tools the model sees. Large tool sets use `deferred` + tool search.

### K: hooks

- **K1 Hooks adjust built-in tasks only.** `beforeTool` / `afterTool` on `ToolTask`; `beforeRequest` / `afterResponse` / `onYield` / `afterTools` on `GenerationTask`; `beforeCompact` on `CompactionTask`.
- **K2 Decisions persist.** A hook that asks for or computes a decision (an approval, a classification) stores it with `api.memo(...)`, so a restart doesn't ask again (post: "A memo stores decisions so hooks don't re-ask after a restart").
- **K3 No control flow by throwing.** A throwing hook is reported and skipped (a throwing `beforeTool` blocks the call). Return `{ block: "reason" }` instead of throwing.
- **K4 Scoped.** A hook meant for some conversations lives in an extension selected only there (`configure({ extensions: { add: [Guard] } })`).

### S: submissions and intents

- **S1 `requestId` on every outside-triggered submit.** User actions, webhooks and retries call `submit({ ..., requestId })` with a key stable across retries. A retry then returns the same submission (Critical when missing on paths that cost money or send messages).
- **S2 Custom intents are exactly-once too.** Host actions that aren't submissions (create a task, abort, write a document) record their key in a document *in the same commit* as the change.
- **S3 Busy behavior is chosen.** `whenBusy: "steer" | "followUp" | "reject"` matches the product's intent.
- **S4 Reacquire after restart.** Hosts that wait on submissions reacquire them after reopening (`harness.submission(id)` or resubmit with the same `requestId`).
- **S5 Server re-checks offered actions.** The host refuses an intent the current state no longer offers (the same `actionsFor` the UI renders from).

### D: documents and state

- **D1 Durable state is in documents.** State that must survive a restart lives in `defineDoc` documents changed in commits, not module-level `Map`s or variables. Flag in-memory registries of ids, approvals or progress.
- **D2 Atomic with the work.** A document change that belongs with a task creation or transcript entry is in the same commit.
- **D3 Document definitions are complete.** `checkpointWhen` is set; `history` and `fork` are chosen for conversation-scoped docs.

### U: observation and UI

- **U1 Views come from commits.** UIs read through `viewState` / `watch` / `taskGraph` / `watchDoc` / `watchEvents`, not by polling storage.
- **U2 Late join and restart re-baseline.** Watches start from the current view with no replay. Clients must accept a fresh baseline after a reconnect. Version counters that restart with the process need a boot id (`(boot, version)`); a bare counter makes clients ignore the new process's views. Notifications derived from diffs must reset their baseline on reconnect, or they replay or vanish.
- **U3 Projection leaks.** `taskGraph()` / `watchDoc()` handles are created once and disposed on close, not per refresh.

## Report format

```markdown
# pi-durable audit: <project> (<date>)

pi-durable <version> · features missing: <list or "none"> · scope: <paths read>

## Summary
<two or three sentences: overall durability, the most serious risk, what is solid>

| Severity | Count |
|---|---|
| Critical | n |
| High | n |
| Medium | n |
| Low | n |

## Findings
### <ID> <title> (<Severity>)
- Where: `path/to/file.ts:123`
- Evidence: <short code excerpt>
- Why it matters: <what happens on a crash, retry, eviction or restart>
- Fix: <concrete change, with the API from the installed version>

## Checks passed
<rule IDs that were verified, one line each>

## Not checked
<rules that didn't apply or couldn't be verified, and why; whether the dynamic crash check ran>
```

---

# Primitive reference (what each is for)

- **Harness**: one storage plus the scheduler. All changes go through one line of atomic commits; nothing is shown before its commit is stored.
- **Commit**: `conversation.commit(tx => ...)` / `runtime.commit` / `api.commit`. Entries, documents and task creation together, all or nothing.
- **Task**: a durable state machine; each phase checkpoints. Owned by a conversation or a task. Built-ins: `pi.generation`, `pi.tool`, compaction.
- **Waiting**: `{status:"waiting", checkpoint, on, policy}`. No code runs until the tasks in `on` settle.
- **Sleeping** (newer releases): `runtime.sleepUntil(until, checkpoint)`. Stored deadline, no invocation held.
- **Abort**: `harness.abortTask(id)`; cascades bottom-up, children's abort handlers first.
- **Tool**: `defineTool` with a TypeBox schema; each call is a task; `replay` decides rerun after a crash.
- **Hook**: `hook(ToolTask | GenerationTask | CompactionTask, {...})` inside an extension; `memo` for decisions.
- **Document**: `defineDoc` typed JSON, session / conversation / task scope, committed with everything else.
- **Submission**: `submit({type:"input"|"write", requestId})`, exactly-once per `requestId`; `wait()` for the outcome.
- **Observation**: `viewState` / `watch` (conversation), `taskGraph` / `watchTaskGraph`, `watchDoc`, `watchEvents`.
- **Storage**: `MemoryStorage` (tests), Node SQLite, JSONL, Cloudflare DO SQLite, and the portable `SqliteStorage` over any `SqliteDatabase` facade (the bootstrap's `bun-sqlite.ts`).
