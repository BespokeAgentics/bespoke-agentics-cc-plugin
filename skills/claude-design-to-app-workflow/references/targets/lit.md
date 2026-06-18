# Target: Lit / Web Components

Use when `--framework lit` or `--framework web-components`. Components become framework-
agnostic custom elements. This is the most divergent port from the React source, so
favor faithful visual + API parity over clever abstractions.

## Stack

- Lit 3 + TypeScript + Vite. Icons: `lucide` (vanilla) rendering SVG, or inline SVG.
- **Styling decision matters for Web Components.** Tailwind utility classes do **not**
  pierce the shadow DOM by default. Two workable paths:
  1. **`css-vars` styling (recommended for WC):** keep the design's token-driven inline
     styles / a component `static styles` block that reads `var(--accent-default)` etc.
     The token sheet is injected at `:root`, and CSS custom properties **do** inherit
     into shadow DOM — so theming + `[data-theme]` switching work cleanly. This is the
     most robust option; prefer it unless the user insists on Tailwind.
  2. **Light DOM / no shadow:** render into light DOM (`createRenderRoot() { return this; }`)
     so global Tailwind applies. Loses style encapsulation; acceptable for a showcase.

If `--framework lit` is chosen without `--styling`, default to **css-vars** and say so.

## Component pattern (Lit + CSS custom properties)

```ts
import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('ds-button')
export class DsButton extends LitElement {
  @property() variant: 'primary' | 'secondary' | 'ghost' | 'accent' = 'primary';
  @property() size: 'sm' | 'md' | 'lg' = 'md';
  @property({ type: Boolean }) disabled = false;

  static styles = css`
    button {
      display: inline-flex; align-items: center; gap: 8px;
      border-radius: var(--radius-sm); font-family: var(--font-body);
      font-weight: var(--fw-medium); cursor: pointer; transition: all 120ms ease;
      border: 1px solid transparent;
    }
    :host([size='sm']) button { padding: 6px 12px; font-size: var(--fs-button-sm); }
    :host([size='md']) button { padding: 8px 16px; font-size: var(--fs-button); }
    :host([size='lg']) button { padding: 10px 20px; font-size: var(--fs-button-lg); }
    :host([variant='primary']) button { background: var(--accent-default); color: #fff; }
    :host([variant='primary']) button:hover { background: var(--accent-strong); }
    :host([variant='secondary']) button { background: var(--surface-default); color: var(--text-primary); border-color: var(--border-default); }
    button:disabled { opacity: .5; cursor: not-allowed; }
    button:focus-visible { outline: none; box-shadow: var(--shadow-focus); }
  `;
  render() { return html`<button ?disabled=${this.disabled}><slot></slot></button>`; }
}
```

## Mapping notes

- React props → `@property()` reflected attributes; use `:host([attr=value])` selectors
  for variant/size styling so encapsulated CSS still keys off them.
- `children` → `<slot>`. Multiple slots for icon-left/right if needed.
- `onClick` → dispatch a native `click`/custom event; consumers listen normally.
- This path leans on the runtime `tokens.css` (Phase 4) being injected globally so the
  inherited custom properties reach each element's shadow root. Skip the Tailwind layer.

## Storybook

`@storybook/web-components-vite`. Stories author the custom element via template
strings; the `[data-theme]` toggle still works (it's on `<html>`, and the vars inherit
down). Page demos compose the elements in a host story.
