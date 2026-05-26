export type InterviewStatus =
  | "idle"
  | "starting"
  | "running"
  | "waiting"
  | "complete"
  | "error"
  | "cancelled";

export type QuestionOption = {
  label: string;
  description: string;
  preview?: string;
};

export type QuestionInput = {
  question: string;
  header: string;
  options: QuestionOption[];
  multiSelect: boolean;
};

export type AnswerValue = string | string[];

export type PendingQuestionRequest = {
  id: string;
  questions: QuestionInput[];
  rawInput: Record<string, unknown>;
  createdAt: string;
};

export type TimelineEvent =
  | {
      type: "status";
      status: InterviewStatus;
      message: string;
      at: string;
    }
  | {
      type: "assistant";
      text: string;
      at: string;
    }
  | {
      type: "question";
      request: PendingQuestionRequest;
      at: string;
    }
  | {
      type: "answer";
      requestId: string;
      answers: Record<string, AnswerValue>;
      at: string;
    }
  | {
      type: "result";
      text: string;
      specPath: string;
      at: string;
    }
  | {
      type: "error";
      message: string;
      at: string;
    };

export type InterviewSnapshot = {
  id: string;
  status: InterviewStatus;
  idea: string;
  specPath: string;
  relativeSpecPath: string;
  model: string;
  startedAt: string;
  completedAt?: string;
  pendingRequest?: PendingQuestionRequest;
  timeline: TimelineEvent[];
};

export type CommandSummary = {
  path: string;
  title: string;
  dimensions: string[];
  commandPreview: string;
};

export type HealthStatus = {
  ok: boolean;
  auth: {
    mode: string;
    label: string;
    detail: string;
  };
  repoRoot: string;
  commandPath: string;
};
