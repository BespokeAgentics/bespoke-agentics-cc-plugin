const SMTP_PORT = 2525;

export function sendMailDigest(alerts) {
  return {
    port: SMTP_PORT,
    body: alerts.map((a) => a.message).join('\n')
  };
}
