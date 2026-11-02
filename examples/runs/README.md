# Captured hosted model runs

These two RunBundle files contain actual llama3.2:3b responses captured on 2026-11-02 through the deployed Cloudflare Python container. One used native Ollama; the other used OpenAI-compatible Chat Completions. Both used the pinned Microsoft Agent Framework and actual local evaluators.

Import either JSON file into either webapp to inspect the answer, observable actions, and evaluation results.

The model demonstrated function calling in its connection test, then failed the Senate-selection document task. This illustrates why endpoint connectivity and tool capability do not establish task reliability.

Each recording covers one case. The release suite is incomplete and its default decision is Hold. These recordings are not the authored baseline, candidate, or revised examples in the guided walkthrough.

The endpoint was a temporary authenticated inference-only HTTPS gateway to the local test model. It was closed after qualification. Its recorded URL is provenance, not a reusable service. Credentials were excluded from the exports. Measured latency reflects that test setup and should not be treated as a service guarantee.
