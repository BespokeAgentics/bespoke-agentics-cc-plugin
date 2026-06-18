# TypeScript gotchas (porting prototype code under strict mode)

The same handful of `tsc --noEmit` errors recur when porting loosely-typed claude.ai
prototype code into a strict TS library. Here's each pattern and its canonical fix so
you don't rediscover them per component. (`scaffold_workspace.py` already ships the
`*.svg`/`*.css` shim and a pragmatic base tsconfig, which pre-empts the first two.)

## 1. Asset imports — `Cannot find module './x.svg'` (TS2307)
Each tsc *program* that imports an asset needs the ambient shim. The scaffold writes
`svg-shim.d.ts` into **both** `packages/ui` and `apps/storybook` and includes it in each
`tsconfig.json`. If you add a new tsconfig program, include a copy. Covers `*.svg`,
`*.png`, `*.svg?react`, and side-effect `*.css` imports.

## 2. Indexed lookups — `Object is possibly 'undefined'` (only if noUncheckedIndexedAccess)
Source code does `variants[variant]`, `tones[tone]`, `sizes[size]` constantly. The
shipped base tsconfig sets `noUncheckedIndexedAccess: false` precisely so these don't
each need a guard — there's no real safety win for a closed lookup map keyed by a union.
Keep it off. (If you must keep it on, narrow with `styles.colors[color] ?? styles.colors.primary`.)

## 3. Render-only stories — `satisfies Meta` portability (TS2742) / missing `args`
A story that only defines `render` can trip *"The inferred type of X cannot be named
without a reference to …"* under `satisfies`/`StoryObj`. Two reliable fixes:
- Type the default export explicitly instead of `satisfies`:
  ```ts
  const meta: Meta<typeof Button> = { title: "...", component: Button };
  export default meta;
  type Story = StoryObj<typeof Button>;
  export const AllVariants: Story = { render: () => <.../> };
  ```
- For render-only stories that TS wants `args` on, give `args: {}`.

## 4. Reducer / accumulator typing — `'acc' implicitly has type 'any'`
Ported `data.jsx` often has `arr.reduce((acc, x) => {...}, {})`. Annotate the seed:
`reduce((acc: Record<string, Item[]>, x) => {...}, {} as Record<string, Item[]>)`.

## 5. Non-uniform `as const` arrays / tuples
`['primary','secondary'].map(v => <Button variant={v}/>)` — `v` is `string`, not the
union. Cast the array: `(['primary','secondary'] as const).map(...)` or annotate the
param `(v: ButtonProps['variant'])`.

## 6. Co-located stories need the Storybook types
Because `*.stories.tsx` live in `packages/ui`, that package must devDepend on
`@storybook/react-vite` (its `Meta`/`StoryObj` types). The shipped `ui-package.json`
template already includes it — don't remove it, or the ui package can't typecheck its
own stories.

## 7. `verbatimModuleSyntax` — type-only imports must say `type`
`import { Meta, StoryObj } from "@storybook/react-vite"` → `import type { Meta, StoryObj
} from "@storybook/react-vite"`. **Under Storybook v10 the package is
`@storybook/react-vite`, not `@storybook/react`** — import `Meta`/`StoryObj` from there.
Same `import type` rule for any imported interface/type; it's on in the base tsconfig to
keep output clean.

## Workflow
Run `bunx tsc --noEmit` per package after porting a batch, not at the very end — the
errors cluster by pattern, so fixing the first occurrence of each (above) usually clears
the rest. The empty skeleton from `scaffold_workspace.py` is already clean, so any error
you see is from code you just added.
