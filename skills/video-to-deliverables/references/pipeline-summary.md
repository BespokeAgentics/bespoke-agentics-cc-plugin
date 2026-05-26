# Pipeline summary block

After all phases complete, print:

```
===============================================
  Video-to-Deliverables Complete
  Project: {project-name} | Label: {label}
  Profile: {PROFILE}
===============================================

Phase 0 — Preprocessing
  ✓ {FRAMES_DIR}/manifest.json                    ({N} unique frames)
  ✓ {FRAMES_DIR}/transcript.txt                   ({N} words)

Phase 1 — Frame Analysis
  ✓ {DOCS_DIR}/frame-analysis-chunk-*.md           ({N} chunks)
  ✓ {DOCS_DIR}/screen-catalog.md
  ✓ {DOCS_DIR}/component-library.md
  ✓ {DOCS_DIR}/system-architecture-map.md

Phase 2 — {PROFILE} Deliverables
  {list all profile-specific deliverables with status}

Total files generated: {N}
Primary deliverable: {primary deliverable path}
```

Status indicators:
- `✓` generated successfully
- `⊘` skipped (already existed)
- `✗` failed (with brief reason)

## skill-factory addendum

If `PROFILE == skill-factory`, the Phase 2 block should also list the generated plugin artifacts explicitly:

```
Phase 2 — skill-factory Deliverables
  ✓ {DOCS_DIR}/candidate-skills.md
  ✓ {DOCS_DIR}/extracted-artifacts.md
  ✓ {DOCS_DIR}/external-references.md
  ✓ {DOCS_DIR}/interview-answers.json
  ✓ {DOCS_DIR}/skill-factory-validation.md
  ✓ {PLUGIN_DIR}/plugin.json                  ← primary deliverable
  ✓ {PLUGIN_DIR}/README.md
  ✓ {PLUGIN_DIR}/skills/{name}/SKILL.md       (×N)
  ✓ {PLUGIN_DIR}/skills/{name}/scripts/       (×N when artifacts were promoted)
  ✓ {PLUGIN_DIR}/commands/{plugin}:*.md       (×N)
  ✓ {PLUGIN_DIR}/agents/*.md                  (when include_subagents)
```
