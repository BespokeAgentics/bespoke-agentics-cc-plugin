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
