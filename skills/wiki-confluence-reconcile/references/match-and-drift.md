# Steps 3–4 — Match entities & detect drift

## Step 3 — Match Confluence entities to wiki pages

For each entity (feature, gap, decision) found in Confluence:

1. Normalize the name to a wiki slug (e.g., "Budget Management" → `budget-management`).
2. Find the wiki page: `wiki/clients/{company}/{type}/{slug}.md`.
3. Categorize the match:
   - **Exact** — wiki and Confluence both present, same entity.
   - **Partial** — Confluence has it, wiki page missing or named differently.
   - **Confluence Only** — Confluence mentions something not yet in wiki.
   - **Wiki Only** — wiki has it, not in Confluence (yet).

## Step 4 — Compare content and detect drift

### Decision-status comparison

| Confluence badge | Wiki `decision:` |
| ---------------- | ---------------- |
| 🟢 OOTB | `decision: ootb` |
| 🔵 Config | `decision: config` |
| 🟡 Custom | `decision: custom` |
| 🔴 Gap | `decision: gap` |
| ⚪ TBD | `decision: tbd` |
| 🟣 Third-Party | `decision: third-party` |

Drift = same entity, different values, no reconciliation note. Example: wiki `custom` vs Confluence `ootb` → flag.

### Status comparison

Compare the Confluence "Status" field (e.g. `In Progress`, `Approved`, `TBD`) with wiki content. Status may be implicit in the wiki body or explicit in frontmatter.

### Effort / estimation comparison

Map Confluence estimates (points / weeks) to wiki `effort:` (`S | M | L | XL`):

| Effort | Points |
| ------ | ------ |
| S (Small) | 1–3 |
| M (Medium) | 5–8 |
| L (Large) | 13–21 |
| XL | 34+ |

Flag if estimates differ significantly.

### Notes & rationale comparison

Extract `Notes` from Confluence; compare with wiki content (feature description, gaps, decisions). Flag when:
- Confluence has new info not in wiki.
- Wiki has rationale not in Confluence.
- Notes contradict the wiki.

### Risk & open-question comparison

Extract open questions and risks from Confluence; compare with `questions/` pages and questions linked from features. Flag e.g. Confluence `TBD` but wiki `Resolved`.
