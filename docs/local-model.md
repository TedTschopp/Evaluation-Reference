# Run a local model without an account

Both editions can run the document agent and optional AI judge on your own computer. Choose local Ollama models throughout this guide. You need no API key, sign-in, hosting account, or access to the author's services.

## Install and start Ollama

Install [Ollama](https://ollama.com/download) for your operating system. Open the app. If you use its command-line installation, run this in a separate terminal and leave it running:

~~~sh
ollama serve
~~~

If the app is already running and the port is in use, use that running server. You do not need a second server. Download the test model in another terminal:

~~~sh
ollama pull llama3.2:3b
ollama list
~~~

Confirm `llama3.2:3b` appears in the list. This local model download is about 2 GB, separate from the lab ZIP. It needs sufficient disk space and memory; generation speed depends on your computer. Model and package downloads require internet initially. Once installed, local inference and replay need no network service beyond your computer.

## Connect from the lab

Keep the lab running locally. In React choose **Run it live → Use local Ollama**. In Python choose **Live**; its default is local Ollama. Check these settings:

| Setting | Value |
|---|---|
| API format | Native Ollama |
| Base URL | `http://localhost:11434` |
| Model identifier | `llama3.2:3b` |
| Authentication | No key |
| Timeout | 120 seconds for this first local run |
| Structured JSON schema | On for this Ollama example |

Use the root URL for Native Ollama; do not append `/v1`. If your Ollama server uses a different port, update the URL in the app. The bundled `examples/ollama.json` is a secret-free example, not a hosted service.

The local preset requests structured JSON so the model returns the declared answer format before the evaluators grade it. Other endpoints may lack schema support; their generation settings can disable it. A format error is visibly distinct from an answer failing a task criterion.

Click **Test connection and tools** in React, or **Test connection and function calling** in Python. Proceed after function calling is verified. A model that only responds with text has not demonstrated the tool calls needed by the document agent. If the probe fails, inspect its message; leave release criteria unchanged.

Choose **Selected case**, keep **1 attempt**, and run the evaluation. Start with a single case; a twelve-case suite or repeated attempts takes longer. The result shows actual retrieved passages, answer, and grades. A small model may fail these checks even after passing its connection probe. That is expected teaching material, not evidence that the setup is broken. An error or timeout means no complete assessment was obtained.

The release panel stays **Hold** for a single-case run because the default policy requires the full twelve-case suite. To measure a complete suite, select **All twelve cases**. Long local suites can hit the service's five-minute run limit; reduce repetitions, use a faster model, or inspect individual cases. Do not interpret a timeout as a pass.

## Try the other adapter or a local judge

The same Ollama server can test the **OpenAI-compatible** adapter: set base URL `http://localhost:11434/v1`, model `llama3.2:3b`, and authentication **No key**, then test the connection again. This uses your local model, not an external OpenAI account.

For an optional judge, enable **Add an AI judge**, choose Native Ollama, and use the same local URL and model, or a second local model you have installed. The judge runs eight calibration examples first, so this takes more time. Calibration mismatches leave required AI judgments **Not assessed**. A failed judge is distinct from an agent's failed answer. Judge setup is optional; deterministic evaluations work without it.

## Common connection problems

| Message or symptom | Check |
|---|---|
| Cannot connect | Open Ollama or run `ollama serve`. Keep both the lab and Ollama running. |
| Model not found | Run `ollama list` and copy the exact name. Pull the model if it is missing. |
| Authentication rejected | A local default Ollama server uses **No key**. Cloud models and other providers have separate requirements. |
| Tool support not demonstrated | Retry the probe once or use another installed model with tool support. The lab cannot enable that capability for a model. |
| Timeout on the first call | Allow the model to load. Use the 120-second timeout; try one case with one attempt. |
| Answer JSON contract error | For this local Ollama example, enable **Generation settings → Use structured JSON schema output**, then rerun. The failed attempt remains a format error. |
| Working on port 8080 but live mode unavailable | Start the React Python service with `uv run --no-editable eval-lab serve`, then open its printed address. |

When the lab runs inside Docker, `localhost` means the container. With Docker Desktop use `http://host.docker.internal:11434` for Ollama on your computer. Direct local startup is the simplest path for this exercise. Linux Docker users may also need an explicit host gateway and an Ollama listen address reachable from that container; follow your Docker and Ollama networking configuration.

Export a RunBundle from either app and import it into the other to inspect the same recorded behavior without rerunning the model. Stop the lab's terminal with **Ctrl+C** when finished; stop the separate Ollama terminal too if you started one.

Sources: [Ollama local setup](https://docs.ollama.com/quickstart), [CLI commands](https://docs.ollama.com/cli), [model size and tool capability](https://ollama.com/library/llama3.2).
