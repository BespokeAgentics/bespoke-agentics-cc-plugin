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
