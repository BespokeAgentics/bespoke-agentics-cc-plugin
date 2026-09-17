-- .claude/db/views.sql — curated views for the project database (wiki flavour).
--
-- This file is yours. /db:sync drops and recreates every CREATE VIEW below (failures are reported,
-- never fatal), and the `-- doc:` line inside each statement becomes the view's description in
-- SCHEMA.md. Views are the SQL form of skills: when the same multi-table query gets written twice,
-- it belongs here so the next agent runs one line instead of re-deriving three joins.
-- `python3 .claude/db/db.py audit --top` lists repeated queries — the candidates.
--
-- Rules of thumb: build on `pages` + json_extract (so a view never depends on a generated view that
-- may not exist yet); alias pages.scope AS client; keep `body` out of wide views (query it by slug).

CREATE VIEW backlinks AS
  -- doc: who links TO a page: one row per (from → to) link with the line it appeared on
  SELECT t.id AS to_id, t.slug AS to_slug, t.type AS to_type,
         s.id AS from_id, s.slug AS from_slug, s.type AS from_type, s.scope AS client,
         l.kind, l.context
  FROM links l
  JOIN pages s ON s.id = l.from_id
  JOIN pages t ON t.id = l.to_id;

CREATE VIEW broken_links AS
  -- doc: [[links]] whose target page does not exist (lint input)
  SELECT s.slug AS from_slug, s.path AS from_path, s.scope AS client, l.to_slug, l.kind, l.context
  FROM links l
  JOIN pages s ON s.id = l.from_id
  WHERE l.to_id IS NULL;

CREATE VIEW orphan_pages AS
  -- doc: typed pages nothing links to (index, log and lint-report pages excluded)
  SELECT p.slug, p.type, p.scope AS client, p.path, p.updated
  FROM pages p
  WHERE p.type IS NOT NULL AND p.type NOT IN ('index', 'log', 'lint-report')
    AND NOT EXISTS (SELECT 1 FROM links l WHERE l.to_id = p.id);

CREATE VIEW page_summary AS
  -- doc: one row per page with type, status, link in/out counts, source count and freshness — no body
  SELECT p.id, p.slug, p.type, p.scope AS client, p.status, p.updated, p.word_count,
         (SELECT COUNT(*) FROM links l WHERE l.from_id = p.id) AS links_out,
         (SELECT COUNT(*) FROM links l WHERE l.to_id = p.id)   AS links_in,
         (SELECT COUNT(*) FROM sources s WHERE s.page_id = p.id) AS n_sources,
         p.path
  FROM pages p;

CREATE VIEW client_overview AS
  -- doc: per client, how many pages of each type (features, gaps, decisions, questions, meetings…)
  SELECT p.scope AS client, p.type, COUNT(*) AS n,
         SUM(CASE WHEN p.status IN ('open', 'pending', 'in-discovery') THEN 1 ELSE 0 END) AS n_open,
         MAX(p.updated) AS last_updated
  FROM pages p
  WHERE p.scope IS NOT NULL AND p.type IS NOT NULL
  GROUP BY p.scope, p.type;

CREATE VIEW open_gaps AS
  -- doc: gaps not resolved/accepted/mitigated, with severity, resolution approach and the related feature page (resolved through links, so any [[link]] spelling works)
  SELECT p.slug, p.title, p.scope AS client, COALESCE(p.status, 'open') AS status,
         json_extract(p.frontmatter, '$.severity') AS severity,
         json_extract(p.frontmatter, '$."resolution-approach"') AS resolution_approach,
         json_extract(p.frontmatter, '$."related-feature"') AS related_feature,
         f.slug AS feature_slug, f.title AS feature_title,
         p.updated, p.path
  FROM pages p
  LEFT JOIN links l ON l.from_id = p.id AND l.kind = 'frontmatter:related-feature'
  LEFT JOIN pages f ON f.id = l.to_id
  WHERE p.type = 'gap' AND COALESCE(p.status, 'open') NOT IN ('resolved', 'accepted', 'mitigated');

CREATE VIEW pending_decisions AS
  -- doc: decisions not yet decided (status pending/blocked/revisited) with their decision-status colour
  SELECT p.slug, p.title, p.scope AS client, p.status,
         json_extract(p.frontmatter, '$."decision-status"') AS decision_status,
         json_extract(p.frontmatter, '$."decided-by"') AS decided_by,
         p.updated, p.path
  FROM pages p
  WHERE p.type = 'decision' AND COALESCE(p.status, 'pending') <> 'decided';

CREATE VIEW open_questions AS
  -- doc: questions still open/blocked/deferred, with priority, category and owner
  SELECT p.slug, p.title, p.scope AS client, COALESCE(p.status, 'open') AS status,
         json_extract(p.frontmatter, '$.priority') AS priority,
         json_extract(p.frontmatter, '$.category') AS category,
         json_extract(p.frontmatter, '$.owner') AS owner,
         p.updated, p.path
  FROM pages p
  WHERE p.type = 'question' AND COALESCE(p.status, 'open') NOT IN ('answered', 'resolved', 'closed');

CREATE VIEW feature_assessment AS
  -- doc: features with their decision colour (ootb/config/custom/gap/tbd/third-party), effort, priority, category
  SELECT p.slug, p.title, p.scope AS client, p.status,
         json_extract(p.frontmatter, '$.decision') AS decision,
         json_extract(p.frontmatter, '$.effort') AS effort,
         json_extract(p.frontmatter, '$.priority') AS priority,
         json_extract(p.frontmatter, '$.category') AS category,
         (SELECT COUNT(*) FROM links l JOIN pages g ON g.id = l.from_id WHERE l.to_id = p.id AND g.type = 'gap') AS n_gaps_linking,
         p.updated, p.path
  FROM pages p
  WHERE p.type = 'feature';

CREATE VIEW meeting_mentions AS
  -- doc: what each meeting page links to — the pages a meeting discovered or discussed
  SELECT m.slug AS meeting, json_extract(m.frontmatter, '$."meeting-date"') AS meeting_date, m.scope AS client,
         t.slug AS mentioned, t.type AS mentioned_type, l.context
  FROM pages m
  JOIN links l ON l.from_id = m.id
  JOIN pages t ON t.id = l.to_id
  WHERE m.type = 'meeting';

CREATE VIEW recent_changes AS
  -- doc: the 50 most recently updated pages (by frontmatter `updated`)
  SELECT p.slug, p.type, p.scope AS client, p.status, p.updated, p.path
  FROM pages p
  WHERE p.updated IS NOT NULL
  ORDER BY p.updated DESC
  LIMIT 50;

CREATE VIEW tag_counts AS
  -- doc: how often each tag is used, and on which page types
  SELECT t.tag, COUNT(*) AS n, group_concat(DISTINCT p.type) AS types
  FROM tags t
  JOIN pages p ON p.id = t.page_id
  GROUP BY t.tag
  ORDER BY n DESC;
