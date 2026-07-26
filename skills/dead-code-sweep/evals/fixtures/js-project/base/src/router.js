import { readFileSync } from 'node:fs';

const routes = JSON.parse(
  readFileSync(new URL('../config/routes.json', import.meta.url), 'utf8')
);

export async function dispatch(path, payload) {
  const route = routes[path];
  if (!route) return { status: 404 };
  const mod = await import(new URL(`./${route.module}`, import.meta.url));
  return mod[route.fn](payload);
}
