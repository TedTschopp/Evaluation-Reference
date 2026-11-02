"""Reject deployment coupling in reference source, compiled assets, and archives."""
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
# Construct destination patterns without embedding prohibited destinations in this guard.
DOMAINS=["tedt"+".org","cloud"+"flare.com","trycloud"+"flare.com","workers"+".dev","pages"+".dev","cloud"+"flare.net"]
PATTERN=re.compile("|".join(re.escape(domain) for domain in DOMAINS),re.I)
ACCOUNT=re.compile(r'"(?:account_id|zone_id)"\s*:\s*"[a-f0-9]{32}"',re.I)
EXCLUDE={".git",".hosting",".wrangler","node_modules",".venv",".cache","artifacts","test-results",".playwright-mcp","__pycache__",".pytest_cache","downloads"}
FAILURES=[]
COUNTS={"source":0,"build":0,"python_archive":0,"react_archive":0}

def check(name,content):
    value=content.decode("utf-8",errors="ignore")
    match=PATTERN.search(value) or ACCOUNT.search(value)
    if match:FAILURES.append(f"{name}: prohibited destination or account field {match.group(0)}")

def source_paths():
    # Git sees new reference files and tracked deletions. Archive extraction needs no Git.
    if (ROOT/".git").exists():
        result=subprocess.run(["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT,check=True,capture_output=True)
        return [ROOT/name for name in result.stdout.decode().split("\0") if name]
    return list(ROOT.rglob("*"))

def main():
    for path in source_paths():
        relative=path.relative_to(ROOT)
        if not path.is_file() or EXCLUDE & set(relative.parts) or relative.parts[0] in {"dist","build"}:continue
        check(str(relative),path.read_bytes());COUNTS["source"]+=1
    site=ROOT/"web/dist"
    if site.exists():
        for path in site.rglob("*"):
            if path.is_file() and "downloads" not in path.relative_to(site).parts:
                check("build/"+str(path.relative_to(site)),path.read_bytes());COUNTS["build"]+=1
    for kind in ["python","react"]:
        path=ROOT/f"dist/founding-eval-lab-{kind}.zip"
        if not path.exists():continue
        with zipfile.ZipFile(path) as archive:
            names=archive.namelist()
            if len(names)!=len(set(names)):FAILURES.append(f"{kind}: duplicate ZIP members")
            for name in names:
                parts=Path(name).parts
                if EXCLUDE & set(parts) or any(p.startswith('.env') for p in parts):FAILURES.append(f"{kind}: operator/cache/credential file {name}")
                check(kind+"/"+name,archive.read(name));COUNTS[kind+"_archive"]+=1
            for required in ["README.md","REFERENCE.md","data/corpus.json","data/cases.json","data/replays.json","docs/instructor-guide.md","src/eval_lab/engine.py"]:
                if "founding-eval-lab/"+required not in names:FAILURES.append(f"{kind}: missing {required}")
            if kind=="react":
                catalogue=json.loads(archive.read("founding-eval-lab/web/dist/distribution.json"))
                if catalogue["downloads"] or catalogue.get("checksums"):FAILURES.append("React ZIP contains links to unbundled archives")
            if kind=="python" and "founding-eval-lab/python_app/app.py" not in names:FAILURES.append("Python ZIP missing its app")
    print(json.dumps({"checked":COUNTS,"failures":FAILURES},indent=2))
    if FAILURES:raise SystemExit(1)

if __name__=="__main__":main()
