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
