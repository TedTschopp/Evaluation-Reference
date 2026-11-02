"""Build browser data from validated shared assets. Run after replay generation."""
import json
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
target=ROOT/"web"/"public"/"data"
target.mkdir(parents=True,exist_ok=True)
for name in ["corpus.json","cases.json","replays.json"]:
    shutil.copy2(ROOT/"data"/name,target/name)
schema_dir=ROOT/"schemas"
schema_dir.mkdir(exist_ok=True)
from eval_lab.models import ModelEndpointDefinition,RunBundle,RunRequest
for name,model in [("model-endpoint",ModelEndpointDefinition),("run-bundle",RunBundle),("run-request",RunRequest)]:
    value=json.dumps(model.model_json_schema(),indent=2)+"\n"
    (schema_dir/f"{name}.schema.json").write_text(value)
    (target/f"{name}.schema.json").write_text(value)
print("Browser assets and versioned JSON schemas prepared.")

