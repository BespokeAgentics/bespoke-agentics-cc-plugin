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
