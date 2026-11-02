# Portable deployment

Both editions run on your own computer. Neither requires a hosting account. All replay data, fonts, document snapshots, and teaching guides are bundled.

For first-time setup, use [Python startup](start-python.md) or [React startup](start-react.md). The account-free live path is documented in [the local model guide](local-model.md). The sections below cover deployment choices after local startup works.

## Static replay

Serve the React edition's `web/dist` directory with any static HTTP server:

~~~sh
uv run --no-project --python 3.12 python -m http.server 8080 --bind 127.0.0.1 --directory web/dist
~~~

Open http://localhost:8080. Paths are relative, so the site also works in a subdirectory. The browser needs no model service for replay. The default download catalogue has no remote archive links. Source and historical citations are optional external reading.

## Python webapp

~~~sh
uv sync --frozen --no-editable --extra python-app
uv run --no-editable --extra python-app streamlit run python_app/app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
~~~

Open the URL printed by Streamlit. The instructor guide is available in its sidebar. Configure model endpoints in this app for live runs.

## React with live execution

~~~sh
uv sync --frozen --no-editable
uv run --no-editable eval-lab serve
~~~

This serves the built UI and API together at http://localhost:8000. Alternatively use `docker compose up --build`. The service binds port 8000. Supply model URLs and visitor credentials through the interface, rather than baking them into the image.

For a public deployment, terminate HTTPS at your reverse proxy. Route `/api/` to the Python service and other paths to `web/dist`. Keep streaming enabled and avoid buffering NDJSON responses. Keep the service inaccessible directly if trusting a proxy-supplied client address.

Set these environment variables for public live execution:

| Variable | Meaning |
|---|---|
| `EVAL_LAB_HOSTED=1` | Reject private/reserved inference destinations and require public HTTPS on port 443. |
| `EVAL_LAB_ALLOWED_ORIGINS` | Optional comma-separated exact browser origins permitted for POST requests. Same-origin requests are permitted automatically. This is an origin check, not a cross-origin CORS deployment; proxy API requests under the UI origin. |
| `EVAL_LAB_CLIENT_IP_HEADER` | Optional client-address header set and overwritten by your trusted proxy. Leave unset for a direct service. Never trust arbitrary visitors' forwarded headers. |
| `EVAL_LAB_DATA_DIR` | Optional absolute path to the bundled data directory. |

The service retains its two-operation limit, ten hosted live requests per minute per client, 64 KiB request limit, and cancellation cleanup. Size your process and proxy limits for your deployment. Replay remains available when the service is stopped.

## Downloads and embeds

Run the documented build and packaging commands to create independent ZIPs. Packaging writes a deployment-only `web/dist/distribution.json` catalogue with `./downloads/…` links. Each archive instead contains the default catalogue and local reference materials. It never links back to the distributing server.

Copy [the embedding example](../integration/embed.html) and set its relative lab URL for your layout. When serving from another origin, configure the parent's `frame-src` and the lab's `frame-ancestors` policies. Set `parent_origin` to the exact parent origin to enable height messages. The parent listener must verify both child origin and window identity.

Before publishing, check static replay, API health, a completed streamed run, cancellation, downloads, and embedding from the actual deployed origins. A successful build does not qualify live inference.
