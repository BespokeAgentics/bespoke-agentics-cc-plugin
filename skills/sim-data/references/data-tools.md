# Data Tools & Shape-Mining Queries

Tool status verified July 2026 — the ecosystem has real corpses in it; check the table before
recommending anything.

## Alive / dead table

| Tool | Status (July 2026) | Verdict |
|------|--------------------|---------|
| **@snaplet/copycat** | 🟢 alive (supabase-community/copycat) | The deterministic primitive: same input → same output, forever. Use for identity fields. `npm i @snaplet/copycat` |
| **@faker-js/faker** | 🟢 alive (v10.x, Node 20+) | Breadth of realistic values; seedable (`faker.seed(n)`) but less rigorously stable across versions than copycat — pin the version. `npm i @faker-js/faker` |
| **Greenmask** | 🟢 alive (0.2.x shipping) | The maintained OSS Postgres anonymizer: pg_dump-compatible masking + synthesis + subsetting. Release binaries / Docker. |
| **PostgreSQL Anonymizer** (`anon`) | 🟢 alive | Declarative in-database masking (`SECURITY LABEL FOR anon ...`); right when masking should live with the schema. `pgxn install postgresql_anonymizer` |
| **@snaplet/seed** | 🟡 zombie (community-maintained, last real release 2024) | Works on stable schemas; don't build new pipelines on it. |
| **pganonymize** | 🟡 dormant (last release 2024) | Prefer Greenmask. |
| **Neosync** | 🔴 dead (archived Aug 2025) | Do not adopt; migrate away if found. |

## Pipeline A — anonymized subset (Postgres, Greenmask shape)

```yaml
# greenmask config (shape — consult current docs for exact syntax)
transformers:
  - table: users
    columns:
      email:      { transformer: RandomEmail }        # or Template with copycat-style stable hash
      full_name:  { transformer: RandomPerson }
      phone:      { transformer: RandomPhoneNumber }
      created_at: { transformer: NoiseDate, params: { ratio: "5d" } }  # preserve seasonality, break exactness
  - table: notes
    columns:
      body:       { transformer: RandomParagraph }    # free text is ALWAYS replaced, never "scrubbed"
```

Non-negotiables:

- **Free-text columns are replaced wholesale.** Masking names inside prose fails; generate new
  prose of the measured length distribution.
- **The review gate**: a named human reviews the rule set against the sensitivity map before
  the first masked dump crosses the prod boundary; re-review on schema change (new columns
  default to *blocked*, not *passed-through* — deny-by-default).
- **Subsetting**: select coherent graphs (a user and all their rows), sized per scenario;
  include the whale account deliberately.
- **Automated post-scan**: grep the masked output for real-space patterns (corporate email
  domain, phone formats, token prefixes like `sk-`, `ghp_`); zero hits or the pipeline fails.

## Pipeline B — synthetic from shapes (copycat + faker)

```ts
// seeds/lib/generators/user.ts
import { copycat } from "@snaplet/copycat";
import { faker } from "@faker-js/faker";

export function makeUser(i: number, seed: string) {
  const key = `${seed}:user:${i}`;
  faker.seed(hashToInt(key));
  return {
    id: copycat.uuid(key),
    email: copycat.email(key),                    // stable across runs & schema changes
    display_name: pickWeighted(key, [
      [0.90, () => faker.person.fullName()],
      [0.05, () => faker.person.fullName() + " " + faker.internet.emoji()],
      [0.03, () => faker.person.fullName({ locale: "ar" })],   // RTL reality
      [0.02, () => faker.string.alpha(2)],                     // the two-char name
    ]),
    bio: maybeNull(key, 0.34, () => faker.lorem.paragraph()),  // measured null rate
    created_at: sampleTemporal(key, PROFILE.users.created_at), // seasonality from the profile
  };
}
```

Distribution helpers to implement once (`seeds/lib/dist.ts`): `pickWeighted` (categorical
frequencies from the profile), `powerLaw` (cardinalities — orders per user, items per org),
`maybeNull(rate)`, `sampleTemporal` (histogram sampler). All keyed on the deterministic key,
never `Math.random()`.

Root-seed contract: `SEED=42 scripts/seed.sh <project> <scenario>` — the seed threads into
every key; print it on completion; changing generator code is allowed to change output, but
same code + same seed must be byte-identical (verify with the double-seed diff).

## Shape-mining queries (read-only aggregates — values never leave)

```sql
-- Cardinality skew: the p95 and the whale
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY n) AS p50,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY n) AS p95,
       max(n) AS whale
FROM (SELECT user_id, count(*) n FROM orders GROUP BY user_id) t;

-- Categorical frequencies
SELECT status, count(*)::float / sum(count(*)) OVER () AS freq
FROM orders GROUP BY status ORDER BY freq DESC;

-- Null rates, one row per column (generate per table from information_schema)
SELECT 'bio' col, avg((bio IS NULL)::int) null_rate FROM users
UNION ALL SELECT 'phone', avg((phone IS NULL)::int) FROM users;

-- Text length + charset reality
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY length(display_name)) p50_len,
       max(length(display_name)) max_len,
       avg((display_name ~ '[^\x00-\x7F]')::int) non_ascii_rate
FROM users;

-- Temporal shape (monthly histogram)
SELECT date_trunc('month', created_at) m, count(*) FROM users GROUP BY m ORDER BY m;

-- Referential quirks
SELECT count(*) FROM orders o LEFT JOIN users u ON u.id = o.user_id WHERE u.id IS NULL; -- orphans
SELECT avg((deleted_at IS NOT NULL)::int) FROM users;                                   -- soft-delete rate
```

Record each result in the profile as `measured` with the query; anything from memory or
interview is `asserted`.

## Scenario manifest template

```markdown
# Scenario: edge
Intent: every documented pathology in one seed — agents run this before claiming UI/query work done.
Volumes: 200 users, 5k orders (1 whale user: 3.8k orders — profile p-max).
Implements: cardinality skew, non-ascii names (5%), null bios (34%), 12 orphan orders,
  9% soft-deleted users, timestamps 1969-12-31 and 2038-01-19.
Ignores: load-scale volumes (see `load`), multi-tenant shapes (see `tenants`).
Seed time: 4.1s (measured 2026-07-13, SEED=42).
```

## Non-SQL notes

Mongo/Dynamo/ES: mining queries become aggregation pipelines / scans (same statistics);
generators unchanged (copycat/faker are store-agnostic); loading via the store's native bulk
path. Greenmask/anon don't apply — for anonymized-subset needs, write the transform as a
streaming script over a dump, same review gate and post-scan rules.
