# Did it answer the question?

A visual reference for evaluating an AI agent's **work**, using 31 U.S. founding and constitutional texts. The six-lesson walkthrough takes about 20 minutes.

**[Open the hosted lab](https://evals.tedt.org)** · [Read the article](https://tedt.org/Your-AI-Passed-the-Test/) · [Instructor guide](docs/instructor-guide.md)

Two independently runnable webapps share the corpus, cases, Microsoft evaluation engine, and JSON contracts. Replay needs no model, API key, or Azure account. Optional live execution supports configurable OpenAI-compatible and native Ollama endpoints.

## The lesson

A weak checker accepts a number because it appears in an authentic source. The agent can still have answered the wrong question, used the wrong period, ignored an evidence boundary, or asked an unnecessary question.

| Version | Cases passed | Default decision |
|---|---:|---|
| Baseline | 8/12 | Hold |
| Candidate | 11/12 | Hold: critical ratification error |
| Revised | 12/12 | Eligible under the teaching policy |

Replay responses and action traces are **authored teaching fixtures**, not purported model recordings. Their scores are computed by the real pinned Microsoft Agent Framework. Captured live model responses are labeled separately. Fixtures have no invented latency, token usage, or model cost.

Local checks are finite heuristics for the declared cases. They inspect declared concepts, retrieved citations, permitted documents, approved task-relevant passages, dates, and response behavior. They are not universal semantic graders. An optional independent AI judge applies a broader rubric and must first match eight source-checked calibration judgments.

## Python webapp

Install Python 3.12 and [uv](https://docs.astral.sh/uv/), then run from this directory:

~~~sh
uv sync --frozen --no-editable --extra python-app --extra dev
uv run --no-editable streamlit run python_app/app.py --browser.gatherUsageStats false
~~~

Open Streamlit's printed local URL. Both replay and live controls are in the browser. React is not needed.

## React webapp

The React download includes an already-built site. Serve it locally:

~~~sh
python3 -m http.server 8080 --directory web/dist
~~~

Open [localhost:8080](http://localhost:8080). Replay works without installing the Python engine.

To also enable live runs, serve the built app and API together:

~~~sh
uv sync --frozen --no-editable
uv run --no-editable eval-lab serve
~~~

Open [localhost:8000](http://localhost:8000). A Docker alternative is:

~~~sh
docker compose up --build
~~~

Inside Docker, reach an Ollama server on your host with http://host.docker.internal:11434.

For frontend development:

~~~sh
npm ci
npm --prefix web ci
uv run --no-editable python scripts/build_assets.py
npm run dev
~~~

Run the API in a second terminal with uv run --no-editable eval-lab serve. Vite proxies /api to port 8000. Use port 5173 or 5174 for the development UI.

## Live model setup

Choose **Run it live**, select the API format, enter a base URL and model identifier, and test the connection. A harmless function round trip verifies demonstrated tool use. Passing the probe does not guarantee correct tool use on the document tasks.

- OpenAI-compatible: a service base URL, commonly ending in /v1.
- Native Ollama: the server root, commonly http://localhost:11434, without /v1.
- Bearer credentials stay in memory and are excluded from exports.
- The structured-JSON option uses an endpoint's schema support. Models can behave differently when tools and constrained output are combined. Unsupported or malformed responses are errors, not passes.
- Hosted live execution reaches public HTTPS endpoints on port 443. Use the local webapp for private endpoints and models on your computer.

Agent and judge endpoints are independent. No shared inference key is supplied. Model generation and optional judging use your connections; local checks need no model calls.

See [endpoint definitions](examples/) and [adapter instructions](docs/architecture.md).

## Inspect and reproduce

~~~sh
uv run --no-editable eval-lab validate
uv run --no-editable eval-lab rebuild-replays
uv run --no-editable python scripts/build_assets.py
~~~

CLI live example, with the key read from the configured environment variable only in local mode:

~~~sh
uv run --no-editable eval-lab run --connection examples/openai-compatible.json --case senate-1789 --output run.json
~~~

Both apps import and export RunBundle 1.0. Imports validate canonical case identities, repetitions, critical flags, criterion applicability, and status consistency, then recompute the decision. An import does not authenticate a claimed model run.

One-case live runs remain incomplete twelve-case release suites. Three repetitions expand the suite to 36 results. Missing required results, a critical failure, or an insufficient pass rate hold the default decision.

## Validate and package

~~~sh
uv sync --frozen --no-editable --extra python-app --extra dev
uv run --no-editable pytest
npm ci
npm --prefix web ci
uv run --no-editable python scripts/build_assets.py
npm --prefix web run test
npm --prefix web run build
uv run --no-editable python scripts/package_downloads.py
~~~

The packaging script writes two self-contained ZIPs and checksums, then places them beside the hosted build. It excludes virtual environments, model weights, credentials, caches, and live diagnostic artifacts.

See [verification](docs/verification.md), [Cloudflare deployment](docs/cloudflare-setup.md), and [blog integration](integration/).

## Corpus and licensing

The corpus contains the Declaration, Articles of Confederation, original Constitution, 1789 proposal, and Amendments 1–27. Bill of Rights is a collection of Amendments 1–10, without duplicate text.

Five National Archives HTML snapshots, complete supplied transcripts, archival notes, source URLs, dates, stable passage IDs, amendment relationships, and SHA-256 checksums are bundled. [Source inventory and caveats](data/sources/README.md)

The supplied NARA Articles transcript ends at its closing attestation and does not transcribe delegate signatures. That omission is documented rather than filled from an unrelated edition.

Code: MIT. Historical material retains its source provenance. Inter and Manrope fonts carry accompanying SIL Open Font Licenses.

