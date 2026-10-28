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
