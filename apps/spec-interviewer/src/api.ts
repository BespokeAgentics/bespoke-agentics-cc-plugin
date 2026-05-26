import type {
  AnswerValue,
  CommandSummary,
  HealthStatus,
  InterviewSnapshot,
} from "./types";

export async function fetchHealth() {
  return requestJson<HealthStatus>("/api/health");
}

export async function fetchCommandSummary() {
  return requestJson<CommandSummary>("/api/command");
}

export async function startSession(input: {
  idea: string;
  specPath: string;
  model: string;
  maxTurns: number;
}) {
  return requestJson<InterviewSnapshot>("/api/sessions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function submitAnswers(
  sessionId: string,
  requestId: string,
  answers: Record<string, AnswerValue>,
) {
  return requestJson<InterviewSnapshot>(`/api/sessions/${sessionId}/answers`, {
    method: "POST",
    body: JSON.stringify({ requestId, answers }),
  });
}

export async function cancelSession(sessionId: string) {
  return requestJson<InterviewSnapshot>(`/api/sessions/${sessionId}/cancel`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Request failed.");
  }
  return data as T;
}
