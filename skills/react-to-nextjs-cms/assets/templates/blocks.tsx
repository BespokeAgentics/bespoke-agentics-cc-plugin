import Image from "next/image";
import { tinaField } from "tinacms/dist/react";

// Block components render one section of a page. IMPORTANT: put `data-tina-field` on a
// REAL HTML element (never a React component) so Tina outlines it and click-to-edit
// focuses the right sidebar field. Replace the placeholder classes with your ported
// design-system components + token utilities (references/component-porting.md).

export function Hero({ block }: { block: any }) {
  return (
    <section data-accent={block.accent} data-layout={block.layout} className="relative">
      {block.eyebrow && (
        <p data-tina-field={tinaField(block, "eyebrow")} className="eyebrow">
          {block.eyebrow}
        </p>
      )}
      <h1 data-tina-field={tinaField(block, "headline")}>{block.headline}</h1>
      {block.sub && (
        <p data-tina-field={tinaField(block, "sub")}>{block.sub}</p>
      )}
      {block.cta?.text && (
        <a data-tina-field={tinaField(block.cta, "text")} href={block.cta.url}>
          {block.cta.text}
        </a>
      )}
      {block.image && (
        <Image
          data-tina-field={tinaField(block, "image")}
          src={block.image}
          alt={block.imageAlt ?? ""}
          width={1200}
          height={800}
          priority
        />
      )}
    </section>
  );
}

export function Services({ block }: { block: any }) {
  return (
    <section>
      {block.heading && (
        <h2 data-tina-field={tinaField(block, "heading")}>{block.heading}</h2>
      )}
      <div className="grid">
        {(block.items ?? []).map((item: any, i: number) => (
          <article key={i}>
            <h3 data-tina-field={tinaField(item, "title")}>{item.title}</h3>
            <p data-tina-field={tinaField(item, "body")}>{item.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function CtaBand({ block }: { block: any }) {
  return (
    <section>
      <a data-tina-field={tinaField(block, "text")} href={block.url}>
        {block.text}
      </a>
    </section>
  );
}
