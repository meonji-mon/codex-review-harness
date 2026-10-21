"""Read OpenCodex model metadata and prepare explicit selections, without inference."""
import json
import subprocess

EFFORTS = ("low", "medium", "high", "xhigh", "max")


def review_eligible(model):
    name = model.lower()
    # Grok is instruction-writing only; automatic routes cannot establish that
    # every possible underlying reviewer is allowed. Never select Terra.
    return not any(part in name for part in ("grok", "terra", "combo", "laya"))


def read_catalog():
    result = subprocess.run(["ocx", "claude", "config", "status", "--json"],
                            capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError("OpenCodex model metadata unavailable; no substitution")
    data = json.loads(result.stdout)
    if not isinstance(data.get("available"), list) or not isinstance(data.get("aliases"), list):
        raise RuntimeError("unsupported OpenCodex catalog response")
    rows = []
    seen = set()
    for row in data["aliases"]:
        model = row.get("id")
        if not isinstance(model, str) or not model or "terra" in model.lower() or model in seen:
            continue
        seen.add(model)
        rows.append({"id": model, "label": row.get("display_name") or model,
                     "review_eligible": review_eligible(model), "instruction_only": "grok" in model.lower()})
    return {"available": [model for model in data["available"] if isinstance(model, str) and "terra" not in model.lower()],
            "models": rows, "effort_options": list(EFFORTS),
            "runtime_model_effort_verified": False}


def select_reviewer(definition, model=None, effort=None, catalog=None):
    # Role permissions are fixed independently of model and effort selection.
    role = dict(definition["code-reviewer"])
    selected_model = model or role["model"]
    selected_effort = effort or role["effort"]
    if catalog is None:
        catalog = read_catalog()
    known = set(catalog["available"]) | {entry["id"] for entry in catalog["models"]}
    if selected_model not in known:
        raise ValueError("model is not in the current configured catalog; no fallback")
    if not review_eligible(selected_model):
        raise ValueError("model/automatic route is not eligible for code review under the current harness")
    if selected_effort not in EFFORTS:
        raise ValueError("effort is not supported by this Claude Code CLI adapter")
    role.update(model=selected_model, effort=selected_effort)
    return {"code-reviewer": role}


def picker_settings(catalog):
    rows = []
    for entry in catalog["models"]:
        label = entry["label"]
        if entry["instruction_only"]:
            label += " — instruction writing only"
        elif not entry["review_eligible"]:
            label += " — explicit task selection required"
        rows.append({"model": entry["id"], "label": label})
    # No behavesAs/capability fabrication, default model, or permission changes.
    return {"modelPicker": {"options": rows, "replaceBuiltInOptions": False}}
