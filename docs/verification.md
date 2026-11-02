# Verification record

Recorded 2026-11-02. This is a reference implementation and a bounded teaching suite.

## Local checks

- 31 text records and 320 stable passages checked against five bundled National Archives HTML snapshots, including amendment numbering, complete supplied transcription parity, provenance hashes, relationships, and Bill of Rights duplicate prevention.
- Python verification covers corpus and fixtures, actual Microsoft LocalEvaluator and evaluate_agent behavior, evidence restrictions, temporal scope, paraphrases, clarification, error handling, imported decisions, credential redaction, and the six Streamlit lessons.
- TypeScript contract checks verify parity with the three bundled Python decisions, partial suites, critical failures, tampered imports, and streamed event parsing.
- Chrome checks exercise the lesson navigator, source browser, graders, release controls, downloads, keyboard navigation, result export/import, iframe layout, mobile sizing, reduced motion, and replay during backend failure. Automated axe checks cover the initial mobile light and dark views; these checks are not a complete accessibility certification.
- The independently installed Python webapp was also checked in Chrome at 390-pixel width, with reduced motion and both native light and dark themes. The rendered initial lesson passed axe checks without horizontal overflow. Version 1.0.1 corrects caption opacity and wraps source identifiers to preserve contrast and keyboard access.

Run the checks from the full source checkout:

~~~sh
uv run --no-editable pytest
npm --prefix web run test
npm --prefix web run build
node web/node_modules/typescript/bin/tsc --project worker/tsconfig.json
# Start Vite on localhost:5174, then run in the web directory:
npm exec -- playwright test --config playwright.config.ts
~~~

## Real model checks

Both the native Ollama adapter and OpenAI-compatible Chat Completions adapter completed real local llama3.2:3b executions through Microsoft Agent Framework. The model demonstrated function calling in the connection probe, then failed the Senate-selection document task. Its incorrect source/answer behavior was recorded as a failure by the actual evaluators. A working endpoint is not evidence of a reliable agent.

An independent AI judge was also invoked against a source-supported response. Full judge acceptance still requires the eight-case calibration performed for each configured judged run.

No paid provider credential was used or installed. Live diagnostic traces and model weights are excluded from the downloads.

## Reproduction and deployment

The two downloads contain the same corpus, authored replay results, schemas, and engine. Their ZIP checksums accompany the hosted files. Each edition has its own startup README.

Hosted deployment requires a successful static-page check, a container-backed health response, and a completed streamed model run. Worker deployment success alone is insufficient. Deployment and clean-download results are recorded separately under docs/delivery.md when available.

## Practical limits

The local graders use finite patterns and approved passage references for twelve declared tasks. Eight calibration responses do not establish broad semantic grading accuracy. The authored version comparison is an instructional example, not a benchmark of real model versions.

The upstream evaluation APIs in Core 1.24.0 carry an experimental warning. Keep the dependency lock and rerun compatibility checks when upgrading.

Imports validate consistency and recompute release decisions; they do not authenticate an imported run's claimed origin. Nothing here certifies production reliability or stakeholder acceptance.
