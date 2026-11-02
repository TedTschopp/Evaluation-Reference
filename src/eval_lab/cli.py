"""Notebook-free CLI companion for the downloadable reference."""
import argparse
import asyncio
import json
from pathlib import Path
from .corpus import Corpus,DATA_DIR
from .engine import execute_run
from .models import EndpointConnection,ModelEndpointDefinition,RunRequest

def main():
    parser=argparse.ArgumentParser(description="Founding Documents AI Evaluation Lab")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("validate",help="Check corpus and show bundled evaluation decisions")
    sub.add_parser("rebuild-replays",help="Recompute authored examples with Microsoft LocalEvaluator")
    serve=sub.add_parser("serve",help="Serve the React build and live API locally")
    serve.add_argument("--port",type=int,default=8000)
    run=sub.add_parser("run",help="Run a case using a secret-free endpoint definition")
    run.add_argument("--connection",required=True,type=Path)
    run.add_argument("--case",action="append",required=True,dest="case_ids")
    run.add_argument("--output",type=Path,default=Path("run.json"))
    args=parser.parse_args()
    if args.command=="validate":
        c=Corpus()
        assert len(c.documents)==31 and len(c.passages)==len(set(c.passages))
        print(f"{len(c.documents)} documents; {len(c.passages)} passages; {c.sha256}")
        for p in json.loads((DATA_DIR/"replays.json").read_text())["profiles"]:
            d=p["bundle"]["decision"]
            print(f"{p['title']}: {d['passed']}/{d['total']}, {d['verdict']}")
    elif args.command=="rebuild-replays":
        from .replay import generate_replays
        value=asyncio.run(generate_replays())
        # Refresh existing browser data too; a downloaded static build needs no Node rebuild.
        encoded=json.dumps(value,ensure_ascii=False,indent=2)+"\n"
        for directory in [Path.cwd()/"web/public/data",Path.cwd()/"web/dist/data"]:
            if (directory/"corpus.json").is_file():
                (directory/"replays.json").write_text(encoded,encoding="utf-8")
        for profile in value["profiles"]:
            decision=profile["bundle"]["decision"]
            print(f"{profile['title']}: {decision['passed']}/{decision['total']}, {decision['verdict']}")
        print(f"Calibration: {sum(row['matches_reference'] for row in value['calibration'])}/{len(value['calibration'])}")
        print("Local replay scores updated. Restart the app and reload the browser to inspect them.")
    elif args.command=="serve":
        if not (Path.cwd()/"web/dist/index.html").is_file():
            parser.error("The built React site is missing. Run this command from the extracted React edition's founding-eval-lab folder. The Python edition starts with the Streamlit command in its README; source checkouts need a React build first.")
        import uvicorn
        uvicorn.run("eval_lab.api:app",host="127.0.0.1",port=args.port)
    elif args.command=="run":
        definition=ModelEndpointDefinition.model_validate_json(args.connection.read_text())
        request=RunRequest(case_ids=args.case_ids,agent=EndpointConnection(definition=definition))
        bundle=asyncio.run(execute_run(request))
        args.output.write_text(bundle.model_dump_json(indent=2)+"\n")
        print(f"{bundle.decision.verdict}: {bundle.decision.passed}/{bundle.decision.total}; {args.output}")

if __name__=="__main__":
    main()

