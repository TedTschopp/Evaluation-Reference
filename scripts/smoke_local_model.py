"""Real-model smoke tests. Uses an already-running Ollama server; no secrets."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from eval_lab.engine import execute_run
from eval_lab.models import EndpointConnection,ModelEndpointDefinition,RunRequest

async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",default="http://127.0.0.1:11435")
    parser.add_argument("--model",default="llama3.2:3b")
    args=parser.parse_args()
    output=ROOT/"artifacts"
    output.mkdir(exist_ok=True)
    for protocol in ["ollama","openai_chat_completions"]:
        definition=ModelEndpointDefinition(name="Local smoke: "+protocol,protocol=protocol,
            base_url=args.url+("/v1" if protocol=="openai_chat_completions" else ""),
            model=args.model,generation={"timeout_seconds":120,"max_output_tokens":1200,"json_schema":True})
        request=RunRequest(case_ids=["senate-1789"],agent=EndpointConnection(definition=definition))
        result=await execute_run(request,hosted=False)
        (output/f"live-{protocol}.json").write_text(result.model_dump_json(indent=2)+"\n")
        for case in result.results:
            print(json.dumps({"protocol":protocol,"case":case.case_id,"status":case.status,
                "latency_ms":case.latency_ms,"error":case.error,"framework":bool(case.framework)}),flush=True)
        assert result.results and all(r.framework for r in result.results),"No model answer reached Microsoft evaluation."
asyncio.run(main())

