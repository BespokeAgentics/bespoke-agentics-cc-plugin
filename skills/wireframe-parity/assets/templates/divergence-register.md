<!-- Divergence register — the at-a-glance action list. Inline this table into the
     parity report's "Divergence register" section, or keep as a sibling file.

     Color (status): 🟢 OOTB · 🔵 Config · 🟡 Custom Dev · 🔴 Gap · ⚪ TBD · 🟣 3rd Party
     Class: regression | intended-evolution | unspecified
     Priority: P0 (breaks a contract / dropped decision) · P1 · P2
     Group 🔴/regressions first. -->

| Color | ID | Divergence | Class | Intended | As-built | Evidence | Priority | Recommendation | Owner |
|-------|----|-----------|-------|----------|----------|----------|----------|----------------|-------|
| 🔴 | V1 | Breadcrumb no longer the single sticky element | regression | one sticky element (contract R1) | 4 stacked sticky bands, 12px seam when scrolled | spec §Contract · `FeatureHeader.tsx:41` · `bands()` gap 12px | P0 | Weld the bands into one sticky container | |
| 🟡 | V2 | Rail width 236 → 248px | intended-evolution | 236px (D5) | 248px | `FeatureSectionRail.tsx:24` · `rect()` w 248 | P2 | Keep; update D5 + spec | |
| 🟡 | V3 | Status pill shows raw enum | regression | `Internal Review` | `in_review` | `StatusPill.tsx:12` · `texts()` | P1 | Map enum → label | |
| ⚪ | V4 | Card shadow slightly softer | unspecified | — (never fixed) | `--elev-card` differs | `tokens.css:176` | — | Out of parity scope | |
