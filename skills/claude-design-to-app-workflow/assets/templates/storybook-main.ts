import type { StorybookConfig } from "@storybook/react-vite";
import tailwindcss from "@tailwindcss/vite";

const config: StorybookConfig = {
  // Pick up stories from THIS app AND the sibling @<scope>/ui workspace package.
  stories: [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)",
    "../../../packages/ui/src/**/*.stories.@(js|jsx|mjs|ts|tsx)",
  ],
  addons: [
    "@storybook/addon-docs", // separate package in v10
    "@storybook/addon-a11y",
    "@storybook/addon-themes",
    // Do NOT add addon-essentials/controls/actions/viewport — built into Storybook 10 core.
  ],
  framework: { name: "@storybook/react-vite", options: {} },
  // Inject the Tailwind v4 Vite plugin into Storybook's own Vite pipeline.
  async viteFinal(viteConfig) {
    viteConfig.plugins = viteConfig.plugins ?? [];
    viteConfig.plugins.push(tailwindcss());
    return viteConfig;
  },
};

export default config;
