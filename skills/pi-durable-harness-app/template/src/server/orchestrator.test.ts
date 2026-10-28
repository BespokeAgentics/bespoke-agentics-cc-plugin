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
