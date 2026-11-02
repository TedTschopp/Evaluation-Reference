"""Build browser data from validated shared assets. Run after replay generation."""
import json
import html
import re
import shutil
import sys
import markdown
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
target=ROOT/"web"/"public"/"data"
target.mkdir(parents=True,exist_ok=True)
for name in ["corpus.json","cases.json","replays.json"]:
    shutil.copy2(ROOT/"data"/name,target/name)
docs=ROOT/"web"/"public"/"docs"
docs.mkdir(parents=True,exist_ok=True)
for source in [ROOT/"README.md",ROOT/"data/sources/README.md",*sorted((ROOT/"docs").glob("*.md"))]:
    name=("reference" if source.parent==ROOT else "corpus-sources") if source.name=="README.md" else source.stem
    body=markdown.markdown(source.read_text(),extensions=["fenced_code","tables"])
    # The guide set is bundled alongside its original Markdown. Keep intra-guide links local.
    body=re.sub(r'href="(?:docs/)?([a-z-]+)\.md"',r'href="\1.html"',body)
    body=body.replace('href="docs/', 'href="').replace('href="integration/"','href="../integration/embed.html"').replace('href="examples/"','href="../examples/openai-compatible.json"').replace('href="data/sources/README.md"','href="corpus-sources.html"')
    title="Reference instructions" if name=="reference" else name.replace("-"," ").title()
    page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · Evaluation Lab</title><style>html{{color-scheme:light dark}}body{{font:1rem/1.65 system-ui,sans-serif;max-width:55rem;margin:2rem auto;padding:0 1.2rem}}a{{color:LinkText}}pre{{padding:1rem;background:#8882;overflow:auto}}code{{overflow-wrap:anywhere}}table{{border-collapse:collapse;display:block;overflow:auto}}th,td{{border:1px solid #888;padding:.5rem}}h1,h2,h3{{line-height:1.3}}</style></head><body><nav><a href="../">Return to the lab</a> · <a href="instructor-guide.html">Instructor guide</a> · <a href="reference.html">Startup instructions</a></nav>{body}</body></html>'''
    (docs/f"{name}.html").write_text(page)
    shutil.copy2(source,docs/f"{name}.md")
shutil.copytree(ROOT/"integration",ROOT/"web"/"public"/"integration",dirs_exist_ok=True)
shutil.copytree(ROOT/"examples",ROOT/"web"/"public"/"examples",dirs_exist_ok=True)
schema_dir=ROOT/"schemas"
schema_dir.mkdir(exist_ok=True)
from eval_lab.models import ModelEndpointDefinition,RunBundle,RunRequest
for name,model in [("model-endpoint",ModelEndpointDefinition),("run-bundle",RunBundle),("run-request",RunRequest)]:
    value=json.dumps(model.model_json_schema(),indent=2)+"\n"
    (schema_dir/f"{name}.schema.json").write_text(value)
    (target/f"{name}.schema.json").write_text(value)
print("Browser assets and versioned JSON schemas prepared.")

