# Start here — Python edition

This download is a complete local webapp. You do not need the author's accounts, an API key, Node.js, Docker, or the React download. Allow a few minutes for setup, then about 20 minutes for the lesson.

## 1. Extract and open the right folder

Extract the ZIP. Open the inner **founding-eval-lab** folder, which contains **pyproject.toml**, **python_app**, and **data**. Open a terminal in that folder. Keep it open while using the app.

On macOS, type `cd ` in Terminal, drag this folder into the window, and press Enter. On Windows, right-click inside this folder and choose **Open in Terminal**. On Linux, use your file manager's **Open in Terminal** command.

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

Close and reopen the terminal after installing uv, return to this folder, then run:

~~~sh
uv --version
uv python install 3.12
~~~

uv manages Python and the app's private environment. You do not need to activate a virtual environment or change your system Python. Initial setup downloads public packages and requires internet access; it does not require a login.

## 3. Start the app

Run these commands from the folder containing **pyproject.toml**:

~~~sh
uv sync --frozen --no-editable --extra python-app
uv run --no-editable --extra python-app streamlit run python_app/app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
~~~

Open [http://localhost:8501](http://localhost:8501), or the **Local URL** printed in the terminal. Seeing **Did it answer the question?** confirms startup. An optional Watchdog performance suggestion in the terminal does not require extra installation. Leave the terminal running. Stop it with **Ctrl+C**; run the second command again to restart.

## 4. Walk through the lesson

1. In the sidebar, keep **Replay** and **Candidate** selected. On a narrow screen, use the arrow at the top left to open the sidebar. The candidate incorrectly answers twelve for the 1791 ratification question. This failure is intentional.
2. Open **Observable action trace**, then use **Evidence desk → Retrieved evidence** to read its actual source passage. The weak checker passes an authentic quotation answering the wrong question.
3. Follow the **Next** buttons at the bottom, or use the six **Guided walkthrough** lessons in the sidebar. **Previous lesson** lets you go back. In **Test the grader**, inspect a valid paraphrase and a wrong-era answer.
4. In **Decide what can ship**, Candidate is **Hold**, even with 11/12 case passes. Change **Agent version** to **Revised** to see 12/12 meet the default policy. These are authored teaching examples, not live model measurements.
5. Use **Export RunBundle JSON** to save a result. Either edition can import it. **Return to bundled examples** clears an imported or live result.

Replay uses bundled text and scores and works without internet after installation. Opening a National Archives or documentation link is optional external reading.

## 5. Run a real model locally

Choose **Live** and open **Run a local model without an account**, or follow [the local model guide](local-model.md). Install Ollama, download `llama3.2:3b`, and use the local connection preset. No model is downloaded or started by the lab itself.

Test the connection and function calling before running **Selected case**. A failed answer is a valid evaluation result; a connection or model error needs setup attention. The **Hold** decision is expected for a one-case run because the release suite has twelve cases. An optional AI judge can use the same local Ollama server.

## Optional: recompute scores with Microsoft locally

Replay displays bundled scores. To execute the real Microsoft local evaluators on the authored examples yourself, stop the app with Ctrl+C and run:

~~~sh
uv run --no-editable --extra python-app eval-lab rebuild-replays
uv run --no-editable --extra python-app eval-lab validate
~~~

Expect Baseline 8/12 Hold, Candidate 11/12 Hold, Revised 12/12 Eligible, and calibration 8/8. This updates local replay data using the pinned evaluation engine without a model or key. Restart the app to see the refreshed scores.

## If something goes wrong

| Symptom | What to do |
|---|---|
| `uv` is not recognized | Install it, reopen the terminal, and check `uv --version`. |
| No `pyproject.toml`, or the app file is missing | Open the inner **founding-eval-lab** folder before running commands. |
| Browser cannot connect | Keep the server terminal open and use its printed URL. Do not double-click a Python file. |
| Port 8501 is busy | Add `--server.port 8502` to the start command; open http://localhost:8502. |
| App dependency is missing | Repeat both startup commands above, including `--extra python-app`. |
| Ollama cannot connect, or the model is missing | Open the Ollama app or run `ollama serve`, then `ollama pull llama3.2:3b`. Check the base URL and model name in the local model guide. |

The six lessons and all 31 source texts are in this ZIP. Tests and developer tools are optional: install them with `uv sync --frozen --no-editable --extra python-app --extra dev`, then run `uv run --no-editable --extra python-app --extra dev pytest`. See **REFERENCE.md** for shared architecture and **docs/instructor-guide.md** for teaching notes. React-specific build instructions apply to the React edition.
