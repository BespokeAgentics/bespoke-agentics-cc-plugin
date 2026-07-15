import { createDatabase, createLocalDatabase } from "@tinacms/datalayer";
import { MongodbLevel } from "mongodb-level";
import { GitHubProvider } from "tinacms-gitprovider-github";

// MongoDB Atlas datalayer. Uses the MongoDB Node driver (raw TCP) — fine on Vercel/Node,
// FRAGILE on Cloudflare Workers (no SRV DNS, connection churn). Prefer database.upstash.ts
// on Cloudflare. Content source of truth is GitHub; this DB is an index/cache.
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
      databaseAdapter: new MongodbLevel<string, Record<string, any>>({
        collectionName: `tinacms-${branch}`, // per-branch isolation
        dbName: "tinacms",
        mongoUri: process.env.MONGODB_URI as string,
      }),
    });
