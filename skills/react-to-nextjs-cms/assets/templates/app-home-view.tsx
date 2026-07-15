"use client";

import { useTina, tinaField } from "tinacms/dist/react";
import { Hero, Services, CtaBand } from "@/components/blocks";

// Client view: useTina makes the data live in edit mode (re-hydrates on every keystroke)
// and inert in production. It renders the page's block list, mapping each block template
// to its component and threading tinaField markers down so on-page elements are clickable.
export default function HomeView(props: {
  data: any;
  query: string;
  variables: object;
}) {
  const { data } = useTina(props);
  const blocks = data?.page?.blocks ?? [];

  return (
    <main>
      {blocks.map((block: any, i: number) => {
        switch (block.__typename) {
          case "PageBlocksHero":
            return <Hero key={i} block={block} />;
          case "PageBlocksServices":
            return <Services key={i} block={block} />;
          case "PageBlocksCta":
            return <CtaBand key={i} block={block} />;
          default:
            return null;
        }
      })}
    </main>
  );
}
