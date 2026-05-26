# UI Integration — Extend, Don't Replace

Read this in Mode: scaffold whenever Phase 0.5 found existing AI UI. The default scaffold is for greenfield. This document is the extension playbook for projects that already render AI interactions and just need the four properties bolted on without disturbing the design.

## The contract

You preserve:
- The existing message renderer (shape, props, position in the tree).
- The existing styling primitive (Tailwind, shadcn, CSS Modules, styled-components, vanilla-extract, etc.).
- The existing state owner (local `useState`, custom `useChat`, Zustand, Jotai, server-state hooks).
- The existing layout (drawer vs panel vs modal vs inline).

You add or replace:
- The **stream consumer** (replace) — almost always wrong. Existing code either awaits the final response or fans out raw SDK events directly to renderers.
- The **tool-call surface** (add) — usually missing entirely.
- The **ETA + elapsed badge** (add) — almost always missing.
- The **activity log drawer** (add) — almost always missing.
- The **abort/pause/resume controls** (add or refit) — sometimes a Stop button exists but isn't wired to `AbortController`.
- The **OS notification dispatcher** (add) — non-visual; pure behavior.

## Detection patterns

### Existing AI UI surfaces

Run these greps in order; first hit wins per category.

| Category | Grep | What it tells you |
|----------|------|-------------------|
| Vercel `ai` consumer | `useChat\\(` / `useCompletion\\(` / `useAssistant\\(` | The project uses `ai` package; replace the stream consumer with an adapter that forwards events into the reducer. |
| Direct streaming consumer | `for await.*messages\\.stream` / `EventSource\\(` / `new ReadableStream` | Custom streaming. Replace with `useAgentSession` + transport. |
| Blocking consumer | `await.*messages\\.create` / `await.*query\\(` (no `for`) | Worst case — no streaming at all. Migration also requires changing the server route. |
| Message list | `messages\\.map` / `<MessageList` / `<Conversation` | The renderer surface. Preserve. Insert tool-call list as a sibling or child. |
| Loading indicator | `isLoading` / `isPending` / `isStreaming` / `<Spinner` / `<Skeleton` | Existing "thinking" indicator. Keep visible but augment with ETA + step counter; do not delete. |
| Input form | `<form` near a Send button next to the message list | The control plane attaches here (Abort/Pause buttons). |

### Styling primitive

| Hit | Implication |
|-----|-------------|
| `tailwind.config.{js,ts}` exists AND className strings contain utility classes | Generate Tailwind. Reuse any detected `cn()` / `clsx()` helper. |
| `@/components/ui/*.tsx` with shadcn-style exports (`Button`, `Card`, `Sheet`) | shadcn/ui. Generate components that import from the same `@/components/ui` namespace. |
| `*.module.css` near components | CSS Modules. Generate a `.module.css` per primitive; do not introduce Tailwind. |
| `styled.div\`` / `import.*from 'styled-components'` | styled-components. Generate with the same factory. |
| `import.*from '@vanilla-extract/css'` | vanilla-extract. Generate `.css.ts` siblings. |
| `import.*from '@stitches/react'` | Stitches. Match it. |
| None of the above, plain CSS files | Plain CSS. Generate a `.css` file and a `className` prop; do not introduce a CSS-in-JS dep. |

If the project mixes (e.g. Tailwind + CSS Modules), match the file you're editing — never the global majority. The user's eye is on the surrounding lines.

### State owner

| Hit | Adapter strategy |
|-----|------------------|
| Local `useState` in the parent of the message list | The reducer becomes a local `useReducer` in the same parent. Forward dispatched events. |
| Custom `useChat`/`useAgent` hook | Wrap the hook. New hook returns the original shape plus `toolCalls`, `eta`, `activityLog`. |
| Vercel `ai` `useChat` | Subscribe to the `messages` array, derive `AgentEvent[]` from `data` annotations and tool invocations, feed the reducer in parallel. Document the dual-source caveat. |
| Zustand store | Generate a `createAgentSlice` factory and merge into the existing store. |
| Jotai atoms | Generate `agentEventsAtom`, `sessionStateAtom = atom(get => replay(get(agentEventsAtom)))`. |
| Redux Toolkit slice | Generate a slice with the reducer; mount under existing root reducer. |
| Server state (TanStack Query, SWR) | Streaming doesn't fit query cache semantics — generate a hook that lives alongside, and document that the query result is the post-hoc record. |

### Extension seams

For each AI UI surface found, identify the **insertion point**. Don't ask the user; infer from the JSX shape, then show the proposed diff for approval.

| Existing shape | Insertion point |
|----------------|-----------------|
| `<Message role="assistant">{content}</Message>` | Wrap or extend `Message` with an `<aside>` slot or `actions` prop carrying `<ToolCallList />`. If the component takes children, insert as the last child. |
| `<MessageList items={messages} />` rendering its own bubbles | Inject a `renderToolCalls={(toolCalls) => ...}` prop, or render `<ToolCallList />` as a sibling element after the list. |
| `<ChatLayout>` with a `header` / `footer` / `sidebar` slot | Use the existing slot. `<EtaBadge />` in header; `<ActivityLogDrawer />` triggered from a button in header. |
| A custom drawer/sheet (shadcn `Sheet`, Headless UI `Dialog`) | Reuse it for the activity log; don't introduce a new modal system. |
| Streaming text rendered char-by-char from a `useState` string | Replace the state source with `session.state.textBuffer`; keep the rendering JSX exactly. |

## Adapter recipes by stack

### Vercel `ai` `useChat`

The project already streams via Vercel. You don't rip out `useChat`. You add a parallel feed into the reducer so tool calls, ETA, and the durable log appear without changing message rendering.

```ts
'use client';
import { useChat } from 'ai/react';
import { useEffect, useReducer, useMemo } from 'react';
import { agentReducer, initialSessionState } from '@/lib/agent/reducer';
import type { AgentEvent } from '@/lib/agent/events';

export function useChatWithAgentUX(opts: Parameters<typeof useChat>[0]) {
  const chat = useChat(opts);
  const [state, dispatch] = useReducer(agentReducer, initialSessionState);

  useEffect(() => {
    // Vercel ai exposes data annotations; map them to AgentEvents.
    // Tool invocations live on chat.messages[i].toolInvocations.
    const last = chat.messages.at(-1);
    if (!last) return;
    // ... derive events from last and dispatch them.
  }, [chat.messages, chat.isLoading]);

  return { ...chat, agent: state };
}
```

Document the dual-source caveat in the generated comment header: the LogSink owns the durable record; `useChat` keeps its in-memory view.

### shadcn/ui + Tailwind

Generate `ToolCallList`, `EtaBadge`, `ActivityLogDrawer`, `AbortButton` as files under `src/components/agent/` that import from `@/components/ui`:

```tsx
// src/components/agent/EtaBadge.tsx
import { Badge } from '@/components/ui/badge';
import { useETA } from '@/hooks/agent/useETA';
import type { SessionState } from '@/lib/agent/reducer';
import type { AgentEvent } from '@/lib/agent/events';

export function EtaBadge({ state, events }: { state: SessionState; events: AgentEvent[] }) {
  const eta = useETA(state, events);
  return (
    <div className="flex items-center gap-2">
      <Badge variant="secondary">{eta.elapsedLabel} elapsed</Badge>
      <Badge variant={eta.confidence === 'stable' ? 'default' : 'outline'}>
        ETA {eta.etaLabel}
      </Badge>
      {eta.isStalled && (
        <Badge variant="destructive">
          still running — last event {Math.round(eta.idleMs / 1000)}s ago
        </Badge>
      )}
    </div>
  );
}
```

### CSS Modules

Generate `EtaBadge.module.css` next to `EtaBadge.tsx`. Don't import Tailwind. Use the existing project's class naming convention if one is visible (BEM, atomic, etc.).

### Plain `useState` chat

The reducer lives in the same component as the existing state. Forward the chosen transport's events into both:

```tsx
const [messages, setMessages] = useState<Message[]>([]); // existing
const session = useAgentSession({ transport });          // new

useEffect(() => {
  // Mirror assistant text into the existing messages list.
  if (session.state.textBuffer) {
    setMessages((prev) => upsertAssistant(prev, session.state.textBuffer));
  }
}, [session.state.textBuffer]);
```

Document this as the "mirror pattern" — explicit, easy to reason about, no second source of truth for what the user reads.

## What to refuse

- Refuse to generate a new `<Chat>` component if one exists. Extend the existing one.
- Refuse to introduce a CSS-in-JS dependency the project doesn't already use.
- Refuse to migrate state from `useState` to Zustand/Jotai/Redux as part of this skill. That's a separate refactor and out of scope.
- Refuse to replace a working `useChat` consumer with a hand-rolled stream — wrap it instead.
- Refuse to silently change className strings on existing elements. If a class change is needed (e.g. to add `relative` so a child can absolutely-position), call it out in the diff plan.

## The smell test before finalizing

Before writing the extend-mode files, answer these to yourself. If any answer is "I'm not sure", stop and ask the user.

1. Will the existing message bubble render identically (no visual regression) for a session with no tool calls?
2. Does my extension match the same styling primitive as the file I'm editing on the line I'm editing?
3. If the user deletes my generated files and reverts my edits, is the project back to its prior working state? (No orphaned state owners, no dangling imports.)
4. Does the activity log drawer reuse an existing modal/drawer primitive, or did I introduce a new one?
5. Is there exactly one source of truth for what the user reads on screen? (Either `session.state.textBuffer` or the existing `messages[]` mirroring it — not both with conflicting content.)
