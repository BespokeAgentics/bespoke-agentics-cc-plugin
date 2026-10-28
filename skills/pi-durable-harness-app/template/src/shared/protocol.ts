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
