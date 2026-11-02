# Architecture and extension points

## Runtime

React replay is a static site with bundled data, fonts, and guides. A local Python/FastAPI service serves the same build and three /api operations for optional live runs. Any static host can serve replay; a reverse proxy can route /api to the Python service.

The Python service permits two concurrent operations and has bounded request bodies and run durations. Model inference occurs at the configured endpoint. There is no database or durable conversation store. Deployment-specific routing, accounts, and lifecycle settings belong to the operator, outside this reference.

Streamlit is an independent Python webapp using the same engine and data. Per-session jobs support cancellation with a two-job process limit.

## Microsoft evaluation

Authored conversations become EvalItem objects scored by the actual LocalEvaluator. Live responses use evaluate_agent with its responses parameter, avoiding a second model invocation. Custom checks use the evaluator decorator and CheckResult.

Core 1.24.0 is pinned. Its evaluation APIs are marked experimental upstream despite the stable package release. Upgrades require explicit compatibility checks and replay comparison.

Local criteria are finite case-specific checks, not general entailment. Approved passage references address wrong-clause errors. An optional AI judge applies a written rubric and must pass source-checked calibration.

## Contracts and imports

Generated Pydantic JSON schemas live in schemas/:

- ModelEndpointDefinition: protocol, URL, model, authentication reference, generation settings, capabilities.
- RunRequest: selected cases, profile, repetitions, independent connections, and policy.
- RunBundle: provenance, versions, case identities, messages, tool events, answers, grades, calibration, and decision.

Keys are separate secret inputs excluded from serialized connection models. Hosted mode never resolves a visitor's environment-variable reference against server secrets.

Runs stream newline-delimited JSON. Only a terminal complete event establishes a completed bundle. Interrupted runs are incomplete.

Imports validate identities, repetitions, critical flags, canonical criterion applicability and status consistency. They recompute decisions but do not authenticate claimed provenance.

## Retrieval

The small corpus uses inspectable lexical ranking, without embeddings or cloud search. Both tools enforce approved document IDs. Search returns stable passage IDs, primary text, and separately labeled archival notes. Retrieval rejects unavailable or unauthorized IDs.

The agent receives neither reference answers nor grader patterns. Exported public messages omit reasoning-content records and raw provider objects.

## Add an endpoint adapter

Built-in protocols are openai_chat_completions and ollama. Both construct native SDK clients explicitly and disable ambient credential/proxy fallback.

Implement a trusted Python async context manager accepting an EndpointConnection and hosted boolean, yielding a framework-compatible chat client. Register it with register_adapter in providers.py. Add its dependency, UI preset, and provider contract tests.

Preserve model identifiers, function calls/results, cleanup, timeouts, cancellation, and endpoint restrictions. Connection files cannot contain executable adapters.

Hosted mode permits public HTTPS port 443. DNS is checked and connections use checked IPs while preserving TLS hostname validation. Private/reserved destinations, embedded credentials, and redirects are rejected. Local mode permits local/private endpoints.

## Release policy

The denominator is all twelve cases, or 36 case attempts when repeated three times. A known critical failure cannot disappear because a judge also errored. Errors and missing assessments remain separately counted.

A changed policy is a distinct decision configuration. Teaching eligibility is not a general reliability certificate.

