// Startet capture.yml in GitHub Actions per Cron Trigger.
// GitHub-Zeitpläne laufen in neuen Repos unzuverlässig, Cloudflare-Cron ist pünktlich.

const REPO = "StMarkus/stmarkus-neubau-livestream";
const WORKFLOW = "capture.yml";
const REF = "main";

async function dispatch(env) {
  const response = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "neubau-capture-trigger",
      },
      body: JSON.stringify({ ref: REF }),
    },
  );
  if (response.status !== 204) {
    throw new Error(`GitHub dispatch failed: ${response.status} ${await response.text()}`);
  }
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },

  // Manueller Test: GET auf die Worker-URL mit ?key=<TRIGGER_KEY> (optional, nur wenn gesetzt)
  async fetch(request, env) {
    const key = new URL(request.url).searchParams.get("key");
    if (!env.TRIGGER_KEY || key !== env.TRIGGER_KEY) {
      return new Response("Not found", { status: 404 });
    }
    await dispatch(env);
    return new Response("Capture workflow dispatched\n");
  },
};
