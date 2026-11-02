# Cloudflare setup and deployment

Target: evals.tedt.org in Ted Tschopps Account. This project uses Workers static assets and a Python Cloudflare Container; Azure is not involved.

## Account setup

1. Enable the account's Workers Paid plan. Containers require it. Cloudflare lists a $5/month baseline plus applicable usage: https://developers.cloudflare.com/containers/platform/pricing/
2. Authenticate the project-local Wrangler CLI:

~~~sh
npx wrangler login
npx wrangler whoami
npx wrangler containers list
~~~

An empty container list confirms access. Current OAuth needs container/cloudchamber and Worker permissions. Refreshing an old Wrangler login adds the newer scopes. Do not paste access tokens into chat or commit them.

Docker must be running when building and pushing a local Dockerfile image.

## Build before publishing

~~~sh
uv sync --frozen --no-editable --extra python-app --extra dev
npm ci
npm --prefix web ci
uv run --no-editable pytest
uv run --no-editable eval-lab rebuild-replays
uv run --no-editable python scripts/build_assets.py
npm --prefix web run test
npm --prefix web run build
uv run --no-editable python scripts/package_downloads.py
~~~

## Deploy

~~~sh
npx wrangler deploy
npx wrangler containers list
~~~

wrangler.jsonc declares the custom domain, static assets, one basic container, its Durable Object binding, and at most one concurrent container instance. The Python service allows two concurrent operations and sleeps after two idle minutes while retaining active work.

Worker and container rollout are not atomic. A successful deploy command can precede container readiness. Verify both static replay and /api/health, then test a live connection and completed run. Never infer backend qualification from the frontend loading.

No model API key is installed as a shared Cloudflare secret. Visitors provide their own connections. Credentials remain request/session memory and are not exported or logged. Runtime access logs are disabled.

## Rollback and fallback

Keep the last verified Worker version and container image identifiers with the deployment record. Inspect both before rolling back. A replay-only fallback Worker configuration is supplied for separate emergency deployment; it does not silently claim live execution.

The static walkthrough does not depend on container availability. A failed or starting backend reports a live-service error while replay remains available.

## Local development

Use the Python API and Vite for ordinary development. The hosted container deliberately blocks local/private model endpoints. The downloaded local webapps support them without opening a visitor's model to the internet.

