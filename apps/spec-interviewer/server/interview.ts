import { randomUUID } from "node:crypto";
import { existsSync } from "node:fs";
import { promises as fs } from "node:fs";
import path from "node:path";
import type { ServerResponse } from "node:http";
import { query, type CanUseTool, type SDKMessage } from "@anthropic-ai/claude-agent-sdk";
import type { PermissionResult } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";
import type {
  AnswerValue,
  InterviewSnapshot,
  InterviewStatus,
  PendingQuestionRequest,
  PendingQuestionResolution,
  QuestionInput,
  TimelineEvent,
} from "./types.js";

const APP_ROOT = path.resolve(process.cwd());
const REPO_ROOT = path.resolve(APP_ROOT, "../..");
const COMMAND_PATH = path.join(REPO_ROOT, "commands/spec-elicitation.md");
const CLIENT_APP_ID = "bespoke-agentics-spec-interviewer/0.1.0";

const startSchema = z.object({
  idea: z.string().trim().min(8, "Describe the product or feature in at least a sentence."),
  specPath: z.string().trim().default("spec.md"),
  model: z.string().trim().default("opus"),
  maxTurns: z.number().int().min(4).max(120).default(80),
});

const answerSchema = z.object({
  requestId: z.string().min(1),
  answers: z.record(z.string(), z.union([z.string(), z.array(z.string())])),
});

type InterviewSession = InterviewSnapshot & {
  subscribers: Set<ServerResponse>;
  abortController: AbortController;
  pendingResolution?: PendingQuestionResolution;
};

const sessions = new Map<string, InterviewSession>();

export function getRepoRoot() {
  return REPO_ROOT;
}

export function getCommandPath() {
  return COMMAND_PATH;
}

export async function getCommandSummary() {
  const command = await fs.readFile(COMMAND_PATH, "utf8");
  const dimensions = [
    "Target & Scope",
    "Technical Architecture",
    "User Experience",
    "Business Logic",
    "Performance & Reliability",
    "Security & Compliance",
    "Future Considerations",
  ];

  return {
    path: path.relative(REPO_ROOT, COMMAND_PATH),
    title: "Spec Elicitation",
    dimensions,
    commandPreview: command.slice(0, 900),
  };
}

export function getAuthStatus() {
  if (process.env.ANTHROPIC_API_KEY) {
    return {
      mode: "api-key",
      label: "API key",
      detail: "Using ANTHROPIC_API_KEY from the local environment.",
    };
  }

  if (process.env.CLAUDE_CODE_USE_BEDROCK === "1") {
    return {
      mode: "bedrock",
      label: "Bedrock",
      detail: "Using the Claude Agent SDK Bedrock environment.",
    };
  }

  if (process.env.CLAUDE_CODE_USE_VERTEX === "1") {
    return {
      mode: "vertex",
      label: "Vertex",
      detail: "Using the Claude Agent SDK Vertex environment.",
    };
  }

  if (process.env.CLAUDE_CODE_USE_FOUNDRY === "1") {
    return {
      mode: "foundry",
      label: "Foundry",
      detail: "Using the Claude Agent SDK Foundry environment.",
    };
  }

  return {
    mode: "claude-code-oauth",
    label: "Claude Code OAuth",
    detail: "No API key is required when the local Claude Code login is available to the Agent SDK.",
  };
}

export async function startInterview(input: unknown) {
  const parsed = startSchema.parse(input);

  const specPath = resolveSpecPath(parsed.specPath);
  const session: InterviewSession = {
    id: randomUUID(),
    status: "starting",
    idea: parsed.idea,
    specPath,
    relativeSpecPath: path.relative(REPO_ROOT, specPath),
    model: parsed.model,
    startedAt: new Date().toISOString(),
    timeline: [],
    subscribers: new Set(),
    abortController: new AbortController(),
  };

  sessions.set(session.id, session);
  emit(session, {
    type: "status",
    status: "starting",
    message: "Preparing the spec interview.",
    at: new Date().toISOString(),
  });

  runInterview(session, parsed.maxTurns).catch((error: unknown) => {
    setStatus(session, "error", errorToMessage(error));
  });

  return publicSnapshot(session);
}

export function getInterview(id: string) {
  const session = sessions.get(id);
  return session ? publicSnapshot(session) : undefined;
}

export function subscribeToInterview(id: string, response: ServerResponse) {
  const session = sessions.get(id);
  if (!session) {
    return false;
  }

  response.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });
  response.write(`data: ${JSON.stringify({ type: "snapshot", snapshot: publicSnapshot(session) })}\n\n`);
  session.subscribers.add(response);

  const keepAlive = setInterval(() => {
    if (!response.destroyed) {
      response.write(": keepalive\n\n");
    }
  }, 15000);

  response.on("close", () => {
    clearInterval(keepAlive);
    session.subscribers.delete(response);
  });

  return true;
}

export async function answerInterviewQuestion(id: string, input: unknown) {
  const session = sessions.get(id);
  if (!session) {
    throw new Error("Interview session not found.");
  }
  if (!session.pendingRequest || !session.pendingResolution) {
    throw new Error("This interview is not waiting for answers.");
  }

  const parsed = answerSchema.parse(input);
  if (parsed.requestId !== session.pendingRequest.id) {
    throw new Error("The answer belongs to an older question set.");
  }

  const answers = normalizeAnswers(session.pendingRequest.questions, parsed.answers);
  const request = session.pendingRequest;
  const resolvePending = session.pendingResolution;

  session.pendingRequest = undefined;
  session.pendingResolution = undefined;
  emit(session, {
    type: "answer",
    requestId: parsed.requestId,
    answers,
    at: new Date().toISOString(),
  });
  setStatus(session, "running", "Claude is folding your answers into the spec.");

  await resolvePending({
    behavior: "allow",
    updatedInput: {
      ...request.rawInput,
      questions: request.questions,
      answers,
    },
  });

  return publicSnapshot(session);
}

export function cancelInterview(id: string) {
  const session = sessions.get(id);
  if (!session) {
    throw new Error("Interview session not found.");
  }

  session.abortController.abort();
  if (session.pendingResolution) {
    session.pendingResolution({
      behavior: "deny",
      message: "The user cancelled the spec interview.",
    });
  }
  session.pendingRequest = undefined;
  session.pendingResolution = undefined;
  setStatus(session, "cancelled", "Interview cancelled.");
  return publicSnapshot(session);
}

async function runInterview(session: InterviewSession, maxTurns: number) {
  const commandMarkdown = await fs.readFile(COMMAND_PATH, "utf8");
  const existingSpec = await readOptional(session.specPath);
  const prompt = buildInterviewPrompt({
    commandMarkdown,
    existingSpec,
    idea: session.idea,
    relativeSpecPath: session.relativeSpecPath,
  });

  setStatus(session, "running", "Claude is reading the command and opening the interview.");

  const canUseTool: CanUseTool = async (toolName, input, context) => {
    if (session.abortController.signal.aborted || context.signal.aborted) {
      return {
        behavior: "deny",
        message: "The interview has been cancelled.",
      };
    }

    if (toolName === "AskUserQuestion") {
      return waitForQuestionAnswers(session, input, context.signal);
    }

    return {
      behavior: "allow",
      updatedInput: input,
    };
  };

  for await (const message of query({
    prompt,
    options: {
      cwd: REPO_ROOT,
      model: session.model === "default" ? undefined : session.model,
      maxTurns,
      tools: ["Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "AskUserQuestion"],
      allowedTools: ["Read", "Write", "Edit", "MultiEdit", "Glob", "Grep"],
      canUseTool,
      permissionMode: "acceptEdits",
      toolConfig: {
        askUserQuestion: {
          previewFormat: "html",
        },
      },
      env: {
        ...process.env,
        CLAUDE_AGENT_SDK_CLIENT_APP: CLIENT_APP_ID,
      },
    },
  })) {
    handleSdkMessage(session, message);
  }

  if (!["complete", "error", "cancelled"].includes(session.status)) {
    setStatus(session, "complete", "Interview finished.");
  }
}

function waitForQuestionAnswers(
  session: InterviewSession,
  rawInput: Record<string, unknown>,
  signal: AbortSignal,
): Promise<PermissionResult> {
  const parsed = parseQuestionInput(rawInput);
  const pendingRequest: PendingQuestionRequest = {
    id: randomUUID(),
    questions: parsed.questions,
    rawInput,
    createdAt: new Date().toISOString(),
  };

  session.pendingRequest = pendingRequest;
  setStatus(session, "waiting", "Claude needs interview answers.");
  emit(session, {
    type: "question",
    request: pendingRequest,
    at: new Date().toISOString(),
  });

  return new Promise((resolve) => {
    const abort = () => {
      if (session.pendingRequest?.id === pendingRequest.id) {
        session.pendingRequest = undefined;
        session.pendingResolution = undefined;
      }
      resolve({
        behavior: "deny",
        message: "The question was cancelled before the user answered.",
      });
    };

    signal.addEventListener("abort", abort, { once: true });
    session.abortController.signal.addEventListener("abort", abort, { once: true });
    session.pendingResolution = async (result) => {
      signal.removeEventListener("abort", abort);
      session.abortController.signal.removeEventListener("abort", abort);
      resolve(result);
    };
  });
}

function handleSdkMessage(session: InterviewSession, message: SDKMessage) {
  if (message.type === "assistant") {
    const text = extractAssistantText(message.message.content);
    if (text) {
      emit(session, {
        type: "assistant",
        text,
        at: new Date().toISOString(),
      });
    }
    return;
  }

  if (message.type === "result") {
    if (message.subtype === "success") {
      session.completedAt = new Date().toISOString();
      emit(session, {
        type: "result",
        text: message.result,
        specPath: session.relativeSpecPath,
        at: session.completedAt,
      });
      setStatus(session, "complete", "Spec interview complete.");
    } else {
      setStatus(session, "error", message.errors.join("\n") || message.stop_reason || "Claude stopped with an error.");
    }
    return;
  }

  if (message.type === "system" && message.subtype === "api_retry") {
    emit(session, {
      type: "status",
      status: session.status,
      message: `Claude API retry ${message.attempt} of ${message.max_retries}.`,
      at: new Date().toISOString(),
    });
  }
}

function buildInterviewPrompt(input: {
  commandMarkdown: string;
  existingSpec: string;
  idea: string;
  relativeSpecPath: string;
}) {
  return `You are hosting a web-based, form-driven spec interview.

Use this repository command file as the source of truth:

<command path="commands/spec-elicitation.md">
${input.commandMarkdown}
</command>

Starting idea:
${input.idea}

Target spec path:
${input.relativeSpecPath}

Existing spec content, if any:
<existing_spec>
${input.existingSpec || "[No existing spec file found.]"}
</existing_spec>

Operating rules for this SDK UI:
- Follow the command file exactly, including the interview dimensions and final spec format.
- Ask the user questions only through the AskUserQuestion tool.
- Ask 1-4 focused questions per batch.
- Each question must have 2-4 concrete options and no built-in Other option. The UI provides free-text Other support.
- Keep interviewing until every command dimension has been explored and the user confirms completeness.
- Read the existing spec if it exists, create a minimal placeholder if needed, and write the completed spec to the target path.
- After writing the spec, summarize what was captured and ask via AskUserQuestion whether any sections need revision.`;
}

function parseQuestionInput(input: Record<string, unknown>) {
  const parsed = z
    .object({
      questions: z.array(
        z.object({
          question: z.string(),
          header: z.string(),
          options: z
            .array(
              z.object({
                label: z.string(),
                description: z.string(),
                preview: z.string().optional(),
              }),
            )
            .min(2)
            .max(4),
          multiSelect: z.boolean().default(false),
        }),
      )
        .min(1)
        .max(4),
    })
    .parse(input);

  return parsed;
}

function normalizeAnswers(questions: QuestionInput[], answers: Record<string, AnswerValue>) {
  const normalized: Record<string, AnswerValue> = {};
  for (const question of questions) {
    const answer = answers[question.question];
    if (answer === undefined) {
      throw new Error(`Missing answer for: ${question.question}`);
    }
    if (Array.isArray(answer)) {
      const values = answer.map((item) => item.trim()).filter(Boolean);
      if (values.length === 0) {
        throw new Error(`Missing answer for: ${question.question}`);
      }
      normalized[question.question] = values;
    } else {
      const value = answer.trim();
      if (!value) {
        throw new Error(`Missing answer for: ${question.question}`);
      }
      normalized[question.question] = value;
    }
  }
  return normalized;
}

function resolveSpecPath(inputPath: string) {
  const requested = inputPath.trim() || "spec.md";
  if (requested.includes("\0")) {
    throw new Error("Spec path contains invalid characters.");
  }
  if (!requested.endsWith(".md")) {
    throw new Error("Spec path must be a Markdown file.");
  }

  const resolved = path.resolve(REPO_ROOT, requested);
  const relative = path.relative(REPO_ROOT, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Spec path must stay inside this plugin repository.");
  }
  return resolved;
}

async function readOptional(filePath: string) {
  if (!existsSync(filePath)) {
    return "";
  }
  return fs.readFile(filePath, "utf8");
}

function publicSnapshot(session: InterviewSession): InterviewSnapshot {
  return {
    id: session.id,
    status: session.status,
    idea: session.idea,
    specPath: session.specPath,
    relativeSpecPath: session.relativeSpecPath,
    model: session.model,
    startedAt: session.startedAt,
    completedAt: session.completedAt,
    pendingRequest: session.pendingRequest,
    timeline: session.timeline,
  };
}

function setStatus(session: InterviewSession, status: InterviewStatus, message: string) {
  session.status = status;
  emit(session, {
    type: "status",
    status,
    message,
    at: new Date().toISOString(),
  });
}

function emit(session: InterviewSession, event: TimelineEvent) {
  session.timeline.push(event);
  const payload = `data: ${JSON.stringify({ type: "event", event, snapshot: publicSnapshot(session) })}\n\n`;
  for (const subscriber of session.subscribers) {
    if (!subscriber.destroyed) {
      subscriber.write(payload);
    }
  }
}

function extractAssistantText(content: unknown) {
  if (!Array.isArray(content)) {
    return "";
  }
  return content
    .flatMap((block) => {
      if (
        block &&
        typeof block === "object" &&
        "type" in block &&
        block.type === "text" &&
        "text" in block &&
        typeof block.text === "string"
      ) {
        return [block.text.trim()];
      }
      return [];
    })
    .filter(Boolean)
    .join("\n\n");
}

function errorToMessage(error: unknown) {
  if (error instanceof z.ZodError) {
    return error.issues.map((issue) => issue.message).join("\n");
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unknown error occurred.";
}
