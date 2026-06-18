// Ambient module declarations so TS accepts asset imports under bundler resolution.
// Include this file in every tsconfig "program" that transitively imports an asset
// (both packages/ui and apps/storybook need their own copy, because each runs tsc
// over its own file set). Vite handles the real loading at build time.
declare module "*.svg" {
  const src: string;
  export default src;
}
declare module "*.png" {
  const src: string;
  export default src;
}
// Side-effect CSS imports (e.g. `import "@scope/ui/styles.css"` in preview.ts).
declare module "*.css";
declare module "*.svg?react" {
  import type * as React from "react";
  const ReactComponent: React.FC<React.SVGProps<SVGSVGElement>>;
  export default ReactComponent;
}
