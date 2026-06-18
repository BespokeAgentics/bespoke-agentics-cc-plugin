import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Storybook supplies its own Vite config via .storybook/main.ts (viteFinal), so this
// file is only needed if the storybook app also builds/serves something standalone.
// Kept minimal and consistent with the Storybook pipeline.
export default defineConfig({
  plugins: [react(), tailwindcss()],
});
