import { createDatabase, createLocalDatabase } from "@tinacms/datalayer";
import { RedisLevel } from "upstash-redis-level";
import { GitHubProvider } from "tinacms-gitprovider-github";

// Upstash Redis datalayer. Talks HTTP, so it runs on Cloudflare Workers AND Vercel.
// Content source of truth is GitHub; this DB is an index/cache. Set TINA_PUBLIC_IS_LOCAL
// =true locally (in-memory DB, no creds needed); false/unset in production.
const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === "true";

const token = process.env.GITHUB_PERSONAL_ACCESS_TOKEN as string;
const owner = (process.env.GITHUB_OWNER || process.env.VERCEL_GIT_REPO_OWNER) as string;
const repo = (process.env.GITHUB_REPO || process.env.VERCEL_GIT_REPO_SLUG) as string;
const branch = (process.env.GITHUB_BRANCH ||
  process.env.VERCEL_GIT_COMMIT_REF ||
  "main") as string;

if (!branch) {
  throw new Error(
    "No branch found. Set GITHUB_BRANCH or process.env.VERCEL_GIT_COMMIT_REF."
  );
}

export default isLocal
  ? createLocalDatabase()
  : createDatabase({
      gitProvider: new GitHubProvider({ branch, owner, repo, token }),
      databaseAdapter: new RedisLevel<string, Record<string, unknown>>({
        redis: {
          url: (process.env.KV_REST_API_URL as string) || "http://localhost:8079",
          token: (process.env.KV_REST_API_TOKEN as string) || "example_token",
        },
        debug: process.env.DEBUG === "true" || false,
      }),
      namespace: branch,
    });
