-- .claude/db/views.sql — curated views for the project database (generic flavour, no wiki).
--
-- This file is yours. /db:sync drops and recreates every CREATE VIEW below (failures are reported,
-- never fatal), and the `-- doc:` line inside each statement becomes the view's description in
-- SCHEMA.md. Views are the SQL form of skills: when the same multi-table query gets written twice,
-- it belongs here so the next agent runs one line instead of re-deriving three joins.
-- `python3 .claude/db/db.py audit --top` lists repeated queries — the candidates.
--
-- Rules of thumb: build on `pages` + json_extract and on the tabular tables listed in SCHEMA.md;
-- keep `body` out of wide views (query it by slug).

CREATE VIEW backlinks AS
  -- doc: who links TO a page: one row per (from → to) link with the line it appeared on
  SELECT t.id AS to_id, t.slug AS to_slug, t.type AS to_type,
         s.id AS from_id, s.slug AS from_slug, s.type AS from_type,
         l.kind, l.context
  FROM links l
  JOIN pages s ON s.id = l.from_id
  JOIN pages t ON t.id = l.to_id;

CREATE VIEW broken_links AS
  -- doc: [[links]] whose target page does not exist
  SELECT s.slug AS from_slug, s.path AS from_path, l.to_slug, l.kind, l.context
  FROM links l
  JOIN pages s ON s.id = l.from_id
  WHERE l.to_id IS NULL;

CREATE VIEW orphan_pages AS
  -- doc: pages nothing links to
  SELECT p.slug, p.type, p.collection, p.path, p.updated
  FROM pages p
  WHERE NOT EXISTS (SELECT 1 FROM links l WHERE l.to_id = p.id);

CREATE VIEW page_summary AS
  -- doc: one row per page with collection, type, status, link in/out counts and freshness — no body
  SELECT p.id, p.slug, p.collection, p.type, p.status, p.updated, p.word_count,
         (SELECT COUNT(*) FROM links l WHERE l.from_id = p.id) AS links_out,
         (SELECT COUNT(*) FROM links l WHERE l.to_id = p.id)   AS links_in,
         p.path
  FROM pages p;

CREATE VIEW collection_overview AS
  -- doc: per collection and type, page counts and last update
  SELECT p.collection, p.type, COUNT(*) AS n, MAX(p.updated) AS last_updated, SUM(p.word_count) AS words
  FROM pages p
  GROUP BY p.collection, p.type;

CREATE VIEW recent_changes AS
  -- doc: the 50 most recently updated pages (by frontmatter `updated`, else file mtime)
  SELECT p.slug, p.collection, p.type, p.status,
         COALESCE(p.updated, datetime(p.mtime, 'unixepoch')) AS updated, p.path
  FROM pages p
  ORDER BY updated DESC
  LIMIT 50;

CREATE VIEW tag_counts AS
  -- doc: how often each tag is used, and on which page types
  SELECT t.tag, COUNT(*) AS n, group_concat(DISTINCT p.type) AS types
  FROM tags t
  JOIN pages p ON p.id = t.page_id
  GROUP BY t.tag
  ORDER BY n DESC;
