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
