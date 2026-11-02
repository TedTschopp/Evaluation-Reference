"""Build two independent archives, then a local catalogue for the distributing site."""
import hashlib
import json
import shutil
import zipfile
import markdown
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"dist"
COMMON=["README.md","LICENSE","pyproject.toml","uv.lock",".python-version",".streamlit","src","data","schemas","examples","docs","tests"]
SCRIPTS=["scripts/collect_corpus.py","scripts/build_assets.py","scripts/smoke_local_model.py","scripts/check_portability.py"]
EXCLUDE={"__pycache__",".pytest_cache",".DS_Store","node_modules",".venv",".cache","downloads",".wrangler",".hosting",".playwright-mcp","test-results"}

def add_tree(archive,path,kind):
    if not path.exists():raise FileNotFoundError(path)
    files=[path] if path.is_file() else sorted(path.rglob("*"))
    for item in files:
        relative=item.relative_to(ROOT)
        if not item.is_file() or EXCLUDE & set(relative.parts) or item.suffix in {".pyc",".tsbuildinfo"}:continue
        if kind=="react" and relative.as_posix()=="tests/test_python_app.py":continue
        if relative.as_posix()=="README.md":
            archive.write(item,"founding-eval-lab/REFERENCE.md")
        elif relative.as_posix()=="web/dist/distribution.json":
            # The downloadable app cannot contain or depend on its own ZIP.
            archive.write(ROOT/"web/public/distribution.json","founding-eval-lab/web/dist/distribution.json")
        else:
            archive.write(item,Path("founding-eval-lab")/relative)

def build():
    OUT.mkdir(exist_ok=True)
    for kind in ["python","react"]:
        target=OUT/f"founding-eval-lab-{kind}.zip"
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            edition=(ROOT/f"docs/start-{kind}.md").read_text().replace("(local-model.md)","(docs/local-model.md)")
            archive.writestr("founding-eval-lab/README.md",edition)
            body=markdown.markdown(edition,extensions=["fenced_code","tables"])
            page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Start here — {kind.title()} evaluation lab</title><style>html{{color-scheme:light dark}}body{{font:1rem/1.65 system-ui,sans-serif;max-width:55rem;margin:2rem auto;padding:0 1.2rem}}h1,h2,h3{{line-height:1.3}}a{{color:LinkText}}pre{{padding:1rem;background:#8882;overflow:auto}}code{{overflow-wrap:anywhere}}table{{border-collapse:collapse;display:block;overflow:auto}}th,td{{border:1px solid #888;padding:.5rem}}</style></head><body>{body}<hr><h2>Local model guide</h2>{markdown.markdown((ROOT/"docs/local-model.md").read_text(),extensions=["fenced_code","tables"])}</body></html>'''
            archive.writestr("founding-eval-lab/START-HERE.html",page)
            for name in COMMON+SCRIPTS:add_tree(archive,ROOT/name,kind)
            if kind=="python":add_tree(archive,ROOT/"python_app",kind)
            else:
                for name in ["web","Dockerfile",".dockerignore","docker-compose.yml","package.json","package-lock.json","integration"]:add_tree(archive,ROOT/name,kind)
        print(target.name,target.stat().st_size)
    paths=[OUT/f"founding-eval-lab-{kind}.zip" for kind in ["python","react"]]
    checksums="".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+p.name+"\n" for p in paths)
    (OUT/"SHA256SUMS.txt").write_text(checksums)
    destination=ROOT/"web/dist/downloads"
    destination.mkdir(parents=True,exist_ok=True)
    for path in [*paths,OUT/"SHA256SUMS.txt"]:shutil.copy2(path,destination/path.name)
    catalogue=json.loads((ROOT/"web/public/distribution.json").read_text())
    catalogue.update(downloads=[{"edition":kind,"href":f"./downloads/founding-eval-lab-{kind}.zip"} for kind in ["python","react"]],checksums="./downloads/SHA256SUMS.txt")
    (ROOT/"web/dist/distribution.json").write_text(json.dumps(catalogue,indent=2)+"\n")
    print("Independent archives built; relative download catalogue added only to the distributing build.")

if __name__=="__main__":build()
