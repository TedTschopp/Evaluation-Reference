# First-time user review — 1.2.0

Reviewed on November 2, 2026. Both published 1.1.0 ZIPs were downloaded over public, unauthenticated HTTPS and extracted independently. The revised editions were installed into new folders, including folder names with spaces, using a fresh public-package cache. No deployment login, author credentials, shared inference key, or other edition was used to start either app.

## Findings and fixes

| Finding in the original walkthrough | Fix |
|---|---|
| Startup assumed uv and Python were already available. | Edition-specific installation steps, folder guidance, expected screen and URL, stop/restart instructions, port alternatives, and troubleshooting. Each ZIP includes a browser-readable START-HERE.html. |
| React's default static server could not run live evaluations; testing a connection showed an HTML/JSON parsing error. | Recommend the bundled Python service for the complete app. Keep static replay as an explicit optional path. Detect API availability and show local startup instructions before enabling live actions. |
| Python retained the remote URL and bearer authentication when switching to native Ollama. | Start with a complete local Ollama connection and update URL/authentication when the protocol changes. React also has a complete local preset, including an optional local judge preset. |
| A partially typed Python URL could display a validation traceback. | Show a short corrective message and disable connection/run controls until valid. |
| The small local model could fail the declared answer format before task grading. | Enable supported structured output in the local Ollama preset and explain format errors separately from failed task criteria. |
| The local React app described public-host endpoint restrictions. | Describe local or hosted connectivity according to the actual API health response. |
| Python re-imported an uploaded file immediately after returning to examples. Imported cases could also be hard to locate. | Reset the uploader together with result state; imports select their recorded lesson and case. Add a visible return-to-examples control in React. |
| Recomputing replay scores gave no CLI summary and left the prebuilt React copy stale. | Print the decisions and calibration count, refresh existing browser data, and document the restart/reload step. No Node build is needed to regrade the downloaded examples. |
| Python navigation on a phone depended on a collapsed sidebar. | Add Next/Previous lesson controls in the main page and explain the sidebar arrow in startup instructions. |

## What was exercised

The browser walkthrough covers all six lessons, source passages, calibration, version comparison, the critical release gate, JSON exports/imports, and returning to replay. Additional checks cover missing API recovery, incomplete endpoint/judge configuration, invalid Python input, protocol changes, local guides/fonts, embedding, mobile sizing, keyboard navigation, and light/dark accessibility checks.

Actual `llama3.2:3b` runs completed through both downloaded interfaces against a local Ollama server with cloud operation disabled and no API key. Native Ollama and the local OpenAI-compatible adapter both produced captured answers that reached the real Microsoft evaluation engine. Their Senate-selection answers failed task criteria; these are successful executions of an evaluation that found agent failures. The optional local judge completed all eight calibration judgments but matched only 3/8; its required assessments remained Not assessed. No false agent or judge pass was substituted for those failures.

A complete twelve-case local suite also finished, with all twelve answers reaching Microsoft grading. That small model passed 0/12 under these instructions and received Hold with one critical failure and no unresolved assessments. These observed model results are separate from the authored replay's 8/12, 11/12, and 12/12 version examples.

Real RunBundles were exported, imported into the other edition, and exported again to check preservation of results, decisions, and version metadata. Replay and local guides use bundled assets. Public source documentation, historical source citations, and initial package/model downloads are external; no live teaching step depends on the original hosting account.

Local GUI qualification was performed on macOS. The project CI additionally exercises Python and frontend checks on Linux. Windows installation commands are drawn from the official uv instructions; this review did not execute a Windows desktop session. Model results vary by hardware and generation; this is a teaching suite, not a general reliability certification.
