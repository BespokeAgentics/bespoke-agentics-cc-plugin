# Vault layout & Obsidian config

## Step 3 — Root directory structure

Create the skeleton based on interview answers:

```
{WIKI_DIR}/
├─ .obsidian/              # Obsidian app configuration
├_ _schema/                # Schema definition and templates
│  └─ templates/           # 7 page-type templates
├─ {top-level-1}/          # e.g. clients/ or projects/ or domains/
├─ {top-level-2}/          # e.g. platforms/ (only if platforms were selected)
├─ {org-name}/             # e.g. verndale/ or acme/ (only if not skipped)
│  └─ processes/
```

Adapt the top-level folders to the interview answers:

| Q3 answer | Top-level folder |
| --------- | ---------------- |
| By client / customer | `clients/` |
| By project / product | `projects/` |
| By team / department | `teams/` |
| By domain / topic | `domains/` |

Always include:
- `platforms/` — only if Q4 platforms were selected.
- `{org-slug}/processes/` — only if Q5 org name was provided.

Use individual `mkdir -p` calls. Do NOT use brace expansion (unreliable across shells).

## Step 4 — Obsidian configuration

### 4a. `.obsidian/app.json`

```json
{
  "showFrontmatter": true,
  "livePreview": true,
  "defaultViewMode": "source",
  "strictLineBreaks": false,
  "showLineNumber": true,
  "readableLineLength": true
}
```

### 4b. `.obsidian/appearance.json`

```json
{
  "baseFontSize": 16,
  "theme": "obsidian"
}
```

### 4c. `.obsidian/core-plugins.json`

```json
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "outgoing-link",
  "tag-pane",
  "page-preview",
  "templates",
  "note-composer",
  "command-palette",
  "editor-status",
  "markdown-importer",
  "outline",
  "word-count"
]
```

### 4d. `.obsidian/graph.json`

Generate color groups based on the actual folder structure created. Map each top-level folder to a distinct color.

```json
{
  "collapse-filter": false,
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [
    { "query": "path:{top-level-1}", "color": { "a": 1, "rgb": 3447003 } },
    { "query": "path:{top-level-2}", "color": { "a": 1, "rgb": 65280 } },
    { "query": "path:{org-slug}",    "color": { "a": 1, "rgb": 16750848 } },
    { "query": "tag:#gap",           "color": { "a": 1, "rgb": 16711680 } },
    { "query": "tag:#decision",      "color": { "a": 1, "rgb": 10040268 } },
    { "query": "tag:#question",      "color": { "a": 1, "rgb": 16776960 } }
  ],
  "collapse-display": false,
  "showArrow": true,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.5,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250
}
```

### 4e. `.obsidian/workspace.json`

```json
{
  "main":   { "id": "main",  "type": "split", "children": [] },
  "left":   { "id": "left",  "type": "split", "children": [], "direction": "horizontal", "width": 300 },
  "right":  { "id": "right", "type": "split", "children": [], "direction": "horizontal", "width": 300 },
  "active": "main"
}
```
