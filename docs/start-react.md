# Start here — React edition

This download includes the built website, React source, and a Python service for live evaluation. You do not need the author's accounts, Node.js, Docker, an API key, or the Python download to use it. Allow a few minutes for setup, then about 20 minutes for the lesson.

## 1. Extract and open the right folder

Extract the ZIP. Open the inner **founding-eval-lab** folder, which contains **pyproject.toml**, **web**, and **data**. Open a terminal there. Keep it open while using the app.

On macOS, type `cd ` in Terminal, drag this folder into the window, and press Enter. On Windows, right-click inside the folder and choose **Open in Terminal**. On Linux, use your file manager's **Open in Terminal** command. Opening **web/dist/index.html** directly will not load the app; use a server as shown below.

## 2. Install uv and Python

If `uv --version` already works, skip the uv installation. Otherwise use the [official uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/), or:

macOS / Linux:

~~~sh
curl -LsSf https://astral.sh/uv/install.sh | sh
~~~

Windows PowerShell:

~~~powershell
winget install --id=astral-sh.uv -e
~~~

Reopen the terminal after installing uv, return to this folder, then run:

~~~sh
uv --version
uv python install 3.12
~~~

uv manages Python and a private environment for this app. There is no virtual-environment activation step. Initial setup downloads public packages and requires internet access; it does not require a login.

## 3. Start the complete local app

From the folder containing **pyproject.toml**:

~~~sh
uv sync --frozen --no-editable
uv run --no-editable eval-lab serve
~~~

Open [http://localhost:8000](http://localhost:8000). Seeing **Did it answer the question?** confirms startup. This one server provides replay and the live evaluation API. No React build is needed. Leave the terminal running. Stop it with **Ctrl+C**; run the second command to restart.

## 4. Walk through the lesson

1. Keep **Replay the lesson** and **Candidate** selected. It incorrectly answers twelve for the 1791 ratification question. This failure is intentional.
2. Open **Observable action trace**, then click its passage identifier to highlight the source in the evidence desk. Authentic text can still answer the wrong question.
3. Follow **Next** through all six lessons. In **Test the grader**, inspect a correct paraphrase and a wrong-era answer.
4. In **Decide what can ship**, Candidate is **Hold** with 11/12 passes because a critical case fails. Select **Revised** to see 12/12 meet the default policy. These are authored teaching examples, not live model measurements.
5. **Export run** saves a RunBundle JSON file; **Import run** displays a saved result from either edition. **Return to bundled examples** clears the imported or live result.

Replay uses bundled data, guides, and fonts and works without internet after installation. Microsoft and National Archives links are optional external reading.

## 5. Run a real model locally

Choose **Run it live**, then **Use local Ollama**. Follow [the local model guide](local-model.md): install Ollama, download `llama3.2:3b`, and test the connection and tools before running **Selected case**. No API key is needed. The lab does not start or download a model for you.

A failed answer is a useful evaluation result; a connection or model error needs setup attention. A one-case run remains **Hold** because it does not complete the twelve-case release suite. The optional AI judge can also use the local Ollama server.

## Optional: lighter replay-only server

To inspect replay without installing the evaluation engine, use:

~~~sh
uv run --no-project --python 3.12 python -m http.server 8080 --bind 127.0.0.1 --directory web/dist
~~~

Open [http://localhost:8080](http://localhost:8080). This server has no live API. To use **Run it live**, stop it and start the complete app from step 3, then move to port 8000. If you already have Python, `python3 -m http.server 8080 --bind 127.0.0.1 --directory web/dist` is another replay-only option.

## Optional: recompute scores with Microsoft locally

The default replay reads bundled scores. To execute the real Microsoft local evaluators on those authored responses, stop the server with Ctrl+C, then run:

~~~sh
uv run --no-editable eval-lab rebuild-replays
uv run --no-editable eval-lab validate
~~~

Expect Baseline 8/12 Hold, Candidate 11/12 Hold, Revised 12/12 Eligible, and calibration 8/8. This refreshes both the local replay data and the existing built website without Node.js, a model, or a key. Restart the server and reload the browser afterward.

## If something goes wrong

| Symptom | What to do |
|---|---|
| `uv` is not recognized | Install it, reopen the terminal, then check `uv --version`. |
| No `pyproject.toml` or `web/dist` | Open the inner **founding-eval-lab** folder. |
| Blank page or a fetch error after opening an HTML file | Use the server in step 3 and open its HTTP URL. |
| Port 8000 is busy | Use `uv run --no-editable eval-lab serve --port 8001` and open http://localhost:8001. |
| Live service is unavailable | Use the complete app on port 8000; a static replay server does not run Python evaluations. |
| Ollama connection or model fails | Open Ollama or run `ollama serve`, then `ollama pull llama3.2:3b`; check the local model guide. |

Node.js 24 is needed only to edit and rebuild the React source. Docker is an optional alternative, described in **docs/deployment.md**. See **REFERENCE.md** for developer commands and **docs/instructor-guide.md** for teaching notes. Streamlit-specific instructions apply to the Python edition.
