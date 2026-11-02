"""Build two independent archives, then a local catalogue for the distributing site."""
import hashlib
import json
import shutil
import zipfile
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
            command="uv sync --frozen --no-editable --extra python-app --extra dev\nuv run --no-editable streamlit run python_app/app.py --browser.gatherUsageStats false" if kind=="python" else "python3 -m http.server 8080 --directory web/dist"
            edition=f"# Founding Documents AI Evaluation Lab — {kind.title()} edition\n\nThis archive runs independently. Open a terminal in this folder.\n\n## Start the walkthrough\n\n~~~sh\n{command}\n~~~\n\n"
            if kind=="react":
                edition+="Open http://localhost:8080 for replay. For live runs, install uv and Python 3.12, run uv sync --frozen --no-editable, then uv run --no-editable eval-lab serve. Open http://localhost:8000. Docker users can run docker compose up --build instead.\n\n"
            else:
                edition+="Open the local URL printed by Streamlit. React and Node are not needed. Use the sidebar for lessons, the local instructor guide, replay, or live model configuration.\n\n"
            edition+="Replay needs no model, credentials, or hosting account. All fonts, document text, cases, and teaching data are local. Live endpoints are configured in the interface. API keys remain in memory and are excluded from exports.\n\nSee docs/instructor-guide.md for the 20-minute lesson, docs/deployment.md for hosting, and REFERENCE.md for source build and test instructions. This download contains no links to the original distributing site's assets.\n"
            archive.writestr("founding-eval-lab/README.md",edition)
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
