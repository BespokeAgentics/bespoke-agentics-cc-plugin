import type { Metadata } from "next";
import "./globals.css";

// Root layout. Prefer next/font for the prototype's Google Fonts (self-hosted, no layout
// shift) — swap the families for the ones analyze_prototype.py listed under `fonts`.
export const metadata: Metadata = {
  title: "<name>",
  description: "Built from a prototype with react-to-nextjs-cms.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
