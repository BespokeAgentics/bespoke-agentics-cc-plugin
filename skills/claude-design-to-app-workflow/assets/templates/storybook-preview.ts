import type { Preview } from "@storybook/react-vite";
import { withThemeByDataAttribute } from "@storybook/addon-themes";

// Tailwind + the design tokens, imported once so every story gets utilities + @theme vars.
// This file lives in @<scope>/ui and imports the token layer; see ui-styles-index.css.
import "@<scope>/ui/styles.css";

const preview: Preview = {
  parameters: {
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/i } },
    a11y: { test: "todo" }, // 'error' to fail CI, 'todo' to warn, 'off' to skip
    layout: "fullscreen", // page-demo stories render full-viewport
  },
  decorators: [
    withThemeByDataAttribute({
      themes: { dark: "dark", light: "light" },
      defaultTheme: "dark", // <-- set to the SOURCE's default theme
      attributeName: "data-theme", // writes [data-theme] on <html>
    }),
  ],
};

export default preview;
