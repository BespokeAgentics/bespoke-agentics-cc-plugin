import {
  ArrowCounterClockwise,
  Brain,
  CheckCircle,
  CircleNotch,
  FileText,
  Play,
  ShieldCheck,
  StopCircle,
  Warning,
} from "@phosphor-icons/react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  cancelSession,
  fetchCommandSummary,
  fetchHealth,
  startSession,
  submitAnswers,
} from "./api";
import type {
  AnswerValue,
  CommandSummary,
  HealthStatus,
  InterviewSnapshot,
  PendingQuestionRequest,
  QuestionInput,
  TimelineEvent,
} from "./types";

const initialIdea =
  "A spec-first interview tool that helps teams turn rough product ideas into implementation-ready markdown specs.";

export function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [command, setCommand] = useState<CommandSummary | null>(null);
  const [snapshot, setSnapshot] = useState<InterviewSnapshot | null>(null);
  const [idea, setIdea] = useState(initialIdea);
  const [specPath, setSpecPath] = useState("spec.md");
  const [model, setModel] = useState("opus");
  const [maxTurns, setMaxTurns] = useState(80);
  const [isStarting, setIsStarting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [appError, setAppError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchHealth(), fetchCommandSummary()])
      .then(([healthResult, commandResult]) => {
        if (cancelled) return;
        setHealth(healthResult);
        setCommand(commandResult);
      })
      .catch((error: unknown) => {
        if (!cancelled) setAppError(errorToMessage(error));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!snapshot?.id) return;
    const events = new EventSource(`/api/sessions/${snapshot.id}/events`);
    events.onmessage = (message) => {
      const data = JSON.parse(message.data) as {
        type: "snapshot" | "event";
        snapshot: InterviewSnapshot;
      };
      setSnapshot(data.snapshot);
    };
    events.onerror = () => {
      setAppError("The live interview stream disconnected.");
      events.close();
    };
    return () => events.close();
  }, [snapshot?.id]);

  const latestStatus = snapshot?.status ?? "idle";
  const isActive = ["starting", "running", "waiting"].includes(latestStatus);
  const timeline = snapshot?.timeline ?? [];

  async function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsStarting(true);
    setAppError(null);
    try {
      const started = await startSession({ idea, specPath, model, maxTurns });
      setSnapshot(started);
    } catch (error) {
      setAppError(errorToMessage(error));
    } finally {
      setIsStarting(false);
    }
  }

  async function handleCancel() {
    if (!snapshot) return;
    setIsCancelling(true);
    setAppError(null);
    try {
      const next = await cancelSession(snapshot.id);
      setSnapshot(next);
    } catch (error) {
      setAppError(errorToMessage(error));
    } finally {
      setIsCancelling(false);
    }
  }

  function handleReset() {
    setSnapshot(null);
    setAppError(null);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="setup-panel">
          <div className="brand-row">
            <div className="brand-mark" aria-hidden="true">
              <Brain size={24} weight="duotone" />
            </div>
            <div>
              <p className="eyebrow">Bespoke Agentics</p>
              <h1>Spec Interviewer</h1>
            </div>
          </div>

          <StatusStrip health={health} command={command} />

          <form className="start-form" onSubmit={handleStart}>
            <Field label="Starting idea" helper="A rough product, feature, or workflow brief.">
              <textarea
                value={idea}
                onChange={(event) => setIdea(event.target.value)}
                rows={7}
                disabled={isActive}
              />
            </Field>

            <Field label="Spec file" helper="Markdown path inside this plugin repo.">
              <input
                value={specPath}
                onChange={(event) => setSpecPath(event.target.value)}
                disabled={isActive}
              />
            </Field>

            <div className="form-grid">
              <Field label="Model" helper="Command default is Opus.">
                <select
                  value={model}
                  onChange={(event) => setModel(event.target.value)}
                  disabled={isActive}
                >
                  <option value="opus">Opus</option>
                  <option value="sonnet">Sonnet</option>
                  <option value="default">SDK default</option>
                </select>
              </Field>
              <Field label="Turns" helper="Upper interview limit.">
                <input
                  type="number"
                  min={4}
                  max={120}
                  value={maxTurns}
                  onChange={(event) => setMaxTurns(Number(event.target.value))}
                  disabled={isActive}
                />
              </Field>
            </div>

            {appError && (
              <div className="inline-error" role="alert">
                <Warning size={18} weight="bold" />
                <span>{appError}</span>
              </div>
            )}

            <div className="button-row">
              <button className="primary-button" type="submit" disabled={isStarting || isActive}>
                {isStarting ? <CircleNotch className="spin" size={18} /> : <Play size={18} weight="fill" />}
                <span>Start Interview</span>
              </button>

              {isActive && (
                <button
                  className="ghost-button"
                  type="button"
                  onClick={handleCancel}
                  disabled={isCancelling}
                >
                  {isCancelling ? <CircleNotch className="spin" size={18} /> : <StopCircle size={18} />}
                  <span>Cancel</span>
                </button>
              )}

              {!isActive && snapshot && (
                <button className="ghost-button" type="button" onClick={handleReset}>
                  <ArrowCounterClockwise size={18} />
                  <span>New Session</span>
                </button>
              )}
            </div>
          </form>
        </aside>

        <section className="interview-panel" aria-live="polite">
          <InterviewHeader snapshot={snapshot} command={command} />
          <QuestionSurface
            snapshot={snapshot}
            onSubmit={async (requestId, answers) => {
              if (!snapshot) return;
              setAppError(null);
              try {
                setSnapshot(await submitAnswers(snapshot.id, requestId, answers));
              } catch (error) {
                setAppError(errorToMessage(error));
              }
            }}
          />
          <Timeline events={timeline} />
        </section>
      </section>
    </main>
  );
}

function StatusStrip({
  health,
  command,
}: {
  health: HealthStatus | null;
  command: CommandSummary | null;
}) {
  return (
    <div className="status-strip">
      <div className="status-item">
        <ShieldCheck size={18} />
        <span>{health?.auth.label ?? "Claude Code OAuth"}</span>
      </div>
      <div className="status-item">
        <FileText size={18} />
        <span>{command?.path ?? "Loading command"}</span>
      </div>
    </div>
  );
}

function Field({
  label,
  helper,
  children,
}: {
  label: string;
  helper: string;
  children: React.ReactNode;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      <span className="field-helper">{helper}</span>
    </label>
  );
}

function InterviewHeader({
  snapshot,
  command,
}: {
  snapshot: InterviewSnapshot | null;
  command: CommandSummary | null;
}) {
  const status = snapshot?.status ?? "idle";
  const dimensions = command?.dimensions ?? [];
  return (
    <header className="interview-header">
      <div>
        <p className="eyebrow">Interview Console</p>
        <h2>{statusTitle(status)}</h2>
      </div>
      <div className={`status-badge ${status}`}>
        <span className="pulse-dot" />
        <span>{status}</span>
      </div>
      <div className="dimension-rail">
        {dimensions.map((dimension) => (
          <span key={dimension}>{dimension}</span>
        ))}
      </div>
    </header>
  );
}

function QuestionSurface({
  snapshot,
  onSubmit,
}: {
  snapshot: InterviewSnapshot | null;
  onSubmit: (requestId: string, answers: Record<string, AnswerValue>) => Promise<void>;
}) {
  const request = snapshot?.pendingRequest;
  if (!request) {
    return <WaitingSurface snapshot={snapshot} />;
  }
  return <QuestionForm request={request} onSubmit={onSubmit} />;
}

function WaitingSurface({ snapshot }: { snapshot: InterviewSnapshot | null }) {
  const status = snapshot?.status ?? "idle";
  if (status === "complete") {
    return (
      <div className="state-surface complete">
        <CheckCircle size={34} weight="fill" />
        <div>
          <h3>Spec captured</h3>
          <p>{snapshot?.relativeSpecPath}</p>
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="state-surface error">
        <Warning size={34} weight="fill" />
        <div>
          <h3>Interview stopped</h3>
          <p>Review the timeline for the failure details.</p>
        </div>
      </div>
    );
  }

  if (status === "running" || status === "starting") {
    return (
      <div className="state-surface running">
        <CircleNotch className="spin" size={34} />
        <div>
          <h3>Claude is working</h3>
          <p>The next structured question set will appear here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="state-surface empty">
      <FileText size={34} />
      <div>
        <h3>No interview running</h3>
        <p>The form on the left starts a new spec session.</p>
      </div>
    </div>
  );
}

function QuestionForm({
  request,
  onSubmit,
}: {
  request: PendingQuestionRequest;
  onSubmit: (requestId: string, answers: Record<string, AnswerValue>) => Promise<void>;
}) {
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [otherValues, setOtherValues] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const canSubmit = useMemo(
    () =>
      request.questions.every((question) => {
        const answer = answers[question.question];
        if (Array.isArray(answer)) return answer.length > 0;
        return typeof answer === "string" && answer.trim().length > 0;
      }),
    [answers, request.questions],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      await onSubmit(request.id, answers);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="question-stack" onSubmit={handleSubmit}>
      <div className="question-meta">
        <span>{request.questions.length} decision{request.questions.length === 1 ? "" : "s"}</span>
        <span>{new Date(request.createdAt).toLocaleTimeString()}</span>
      </div>

      {request.questions.map((question) => (
        <QuestionCard
          key={question.question}
          question={question}
          answer={answers[question.question]}
          otherValue={otherValues[question.question] ?? ""}
          onAnswer={(value) => setAnswers((current) => ({ ...current, [question.question]: value }))}
          onOtherChange={(value) => {
            setOtherValues((current) => ({ ...current, [question.question]: value }));
            setAnswers((current) => ({ ...current, [question.question]: value }));
          }}
        />
      ))}

      <div className="question-actions">
        <button className="primary-button" type="submit" disabled={!canSubmit || submitting}>
          {submitting ? <CircleNotch className="spin" size={18} /> : <CheckCircle size={18} weight="fill" />}
          <span>Send Answers</span>
        </button>
      </div>
    </form>
  );
}

function QuestionCard({
  question,
  answer,
  otherValue,
  onAnswer,
  onOtherChange,
}: {
  question: QuestionInput;
  answer: AnswerValue | undefined;
  otherValue: string;
  onAnswer: (value: AnswerValue) => void;
  onOtherChange: (value: string) => void;
}) {
  const selectedValues = Array.isArray(answer) ? answer : answer ? [answer] : [];

  function toggleOption(label: string) {
    if (!question.multiSelect) {
      onAnswer(label);
      return;
    }
    const selected = new Set(selectedValues);
    if (selected.has(label)) selected.delete(label);
    else selected.add(label);
    onAnswer([...selected]);
  }

  return (
    <article className="question-card">
      <div className="question-heading">
        <span>{question.header}</span>
        <h3>{question.question}</h3>
      </div>

      <div className="option-grid">
        {question.options.map((option) => {
          const selected = selectedValues.includes(option.label);
          return (
            <button
              key={option.label}
              className={`option-card ${selected ? "selected" : ""}`}
              type="button"
              onClick={() => toggleOption(option.label)}
            >
              <span className="option-title">{option.label}</span>
              <span className="option-copy">{option.description}</span>
              {option.preview && <PreviewFrame html={option.preview} />}
            </button>
          );
        })}
      </div>

      <label className="other-field">
        <span>Other</span>
        <input
          value={otherValue}
          onChange={(event) => onOtherChange(event.target.value)}
          placeholder="Type a custom answer"
        />
      </label>
    </article>
  );
}

function PreviewFrame({ html }: { html: string }) {
  return (
    <iframe
      title="Option preview"
      sandbox=""
      srcDoc={html}
      className="preview-frame"
    />
  );
}

function Timeline({ events }: { events: TimelineEvent[] }) {
  const visible = events.slice(-12).reverse();
  return (
    <section className="timeline">
      <div className="timeline-heading">
        <h3>Session Timeline</h3>
        <span>{events.length} events</span>
      </div>
      {visible.length === 0 ? (
        <div className="timeline-empty">No session events yet.</div>
      ) : (
        <ol>
          {visible.map((event, index) => (
            <TimelineItem event={event} key={`${event.at}-${event.type}-${index}`} />
          ))}
        </ol>
      )}
    </section>
  );
}

function TimelineItem({ event }: { event: TimelineEvent }) {
  return (
    <li className={`timeline-item ${event.type}`}>
      <time>{new Date(event.at).toLocaleTimeString()}</time>
      <div>
        <strong>{timelineTitle(event)}</strong>
        <p>{timelineBody(event)}</p>
      </div>
    </li>
  );
}

function timelineTitle(event: TimelineEvent) {
  if (event.type === "status") return event.status;
  if (event.type === "assistant") return "assistant";
  if (event.type === "question") return "question";
  if (event.type === "answer") return "answer";
  if (event.type === "result") return "result";
  return "error";
}

function timelineBody(event: TimelineEvent) {
  if (event.type === "status") return event.message;
  if (event.type === "assistant") return clamp(event.text);
  if (event.type === "question") return `${event.request.questions.length} question set ready.`;
  if (event.type === "answer") return `${Object.keys(event.answers).length} answers sent.`;
  if (event.type === "result") return `Spec written to ${event.specPath}.`;
  return event.message;
}

function statusTitle(status: string) {
  if (status === "waiting") return "Your turn to decide";
  if (status === "running" || status === "starting") return "Interview in motion";
  if (status === "complete") return "Specification ready";
  if (status === "error") return "Needs attention";
  if (status === "cancelled") return "Session cancelled";
  return "Ready to shape the spec";
}

function clamp(value: string) {
  return value.length > 220 ? `${value.slice(0, 217)}...` : value;
}

function errorToMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error.";
}
