export function handleWebhook(payload) {
  return { status: 200, event: payload.event ?? 'unknown' };
}
