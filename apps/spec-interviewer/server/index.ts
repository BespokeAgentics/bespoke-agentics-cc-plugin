import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createServer as createViteServer } from "vite";
import {
  answerInterviewQuestion,
  cancelInterview,
  getCommandPath,
  getCommandSummary,
  getInterview,
  getRepoRoot,
  getAuthStatus,
  startInterview,
  subscribeToInterview,
} from "./interview.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(__dirname, "..");
const isProduction = process.env.NODE_ENV === "production";
const port = Number(process.env.PORT || 4177);
const host = process.env.HOST || "127.0.0.1";

const vite = isProduction
  ? undefined
  : await createViteServer({
      root: appRoot,
      server: { middlewareMode: true },
      appType: "spa",
    });

const server = createServer(async (request, response) => {
  try {
    if (!request.url) {
      sendJson(response, 400, { error: "Missing URL." });
      return;
    }

    const url = new URL(request.url, `http://${request.headers.host || `${host}:${port}`}`);
    if (url.pathname.startsWith("/api/")) {
      await handleApi(request, response, url);
      return;
    }

    if (vite) {
      vite.middlewares(request, response, (error?: unknown) => {
        if (error) {
          sendError(response, error);
        }
      });
      return;
    }

    await serveStatic(response, url.pathname);
  } catch (error) {
    sendError(response, error);
  }
});

server.listen(port, host, () => {
  console.log(`Spec Interviewer listening at http://${host}:${port}`);
});

async function handleApi(request: IncomingMessage, response: ServerResponse, url: URL) {
  if (request.method === "GET" && url.pathname === "/api/health") {
    sendJson(response, 200, {
      ok: true,
      auth: getAuthStatus(),
      repoRoot: getRepoRoot(),
      commandPath: path.relative(getRepoRoot(), getCommandPath()),
    });
    return;
  }

  if (request.method === "GET" && url.pathname === "/api/command") {
    sendJson(response, 200, await getCommandSummary());
    return;
  }

  if (request.method === "POST" && url.pathname === "/api/sessions") {
    const body = await readJson(request);
    sendJson(response, 201, await startInterview(body));
    return;
  }

  const sessionMatch = url.pathname.match(/^\/api\/sessions\/([^/]+)(?:\/([^/]+))?$/);
  if (sessionMatch) {
    const [, sessionId, action] = sessionMatch;

    if (request.method === "GET" && !action) {
      const snapshot = getInterview(sessionId);
      if (!snapshot) {
        sendJson(response, 404, { error: "Interview session not found." });
        return;
      }
      sendJson(response, 200, snapshot);
      return;
    }

    if (request.method === "GET" && action === "events") {
      if (!subscribeToInterview(sessionId, response)) {
        sendJson(response, 404, { error: "Interview session not found." });
      }
      return;
    }

    if (request.method === "POST" && action === "answers") {
      const body = await readJson(request);
      sendJson(response, 200, await answerInterviewQuestion(sessionId, body));
      return;
    }

    if (request.method === "POST" && action === "cancel") {
      sendJson(response, 200, cancelInterview(sessionId));
      return;
    }
  }

  sendJson(response, 404, { error: "Route not found." });
}

async function readJson(request: IncomingMessage) {
  const chunks: Buffer[] = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  if (chunks.length === 0) {
    return {};
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function sendJson(response: ServerResponse, status: number, payload: unknown) {
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
  });
  response.end(JSON.stringify(payload));
}

function sendError(response: ServerResponse, error: unknown) {
  const message = error instanceof Error ? error.message : "Unknown server error.";
  sendJson(response, 500, { error: message });
}

async function serveStatic(response: ServerResponse, pathname: string) {
  const distRoot = path.join(appRoot, "dist");
  const requested = path.normalize(pathname).replace(/^(\.\.[/\\])+/, "");
  let filePath = path.join(distRoot, requested === "/" ? "index.html" : requested);
  try {
    const stat = await fs.stat(filePath);
    if (stat.isDirectory()) {
      filePath = path.join(filePath, "index.html");
    }
    response.writeHead(200, {
      "Content-Type": contentType(filePath),
    });
    response.end(await fs.readFile(filePath));
  } catch {
    response.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
    });
    response.end(await fs.readFile(path.join(distRoot, "index.html")));
  }
}

function contentType(filePath: string) {
  if (filePath.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (filePath.endsWith(".css")) return "text/css; charset=utf-8";
  if (filePath.endsWith(".svg")) return "image/svg+xml";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  return "text/html; charset=utf-8";
}
