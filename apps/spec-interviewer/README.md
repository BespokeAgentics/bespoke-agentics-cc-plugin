# Spec Interviewer

A local, form-driven UI for running the repository's `commands/spec-elicitation.md` workflow through the Claude Agent SDK.

## Run

```bash
cd apps/spec-interviewer
npm install
npm run dev
```

Open `http://127.0.0.1:4177`.

The Agent SDK can use your local Claude Code OAuth login automatically. `ANTHROPIC_API_KEY` is optional if you prefer key-based auth.

## What It Does

- Loads `../../commands/spec-elicitation.md` as the interview source of truth.
- Starts a Claude Agent SDK session from a product idea and target spec path.
- Converts SDK `AskUserQuestion` requests into form cards.
- Streams assistant progress, errors, and final spec status back into the UI.
- Writes completed specs inside this plugin repository.
