"""Shared FP8 loader for the Qwen FP8 checkpoints.

Two separate transformers bugs have to be worked around.

1. `FineGrainedFP8HfQuantizer.update_tp_plan` raises AttributeError on these MoE
   configs even with no tensor parallelism. Swallow it.

2. Qwen3.8-27B-FP8 ships a `modules_to_not_convert` list containing
   `model.language_model.layers.N.mlp.gate` -- the MoE router, correctly protected
   in the checkpoint family this list was generated for. Transformers remaps
   `model.language_model.` -> `model.` for a text-only load and then matches skip
   entries by prefix, so `...mlp.gate` also swallows `...mlp.gate_proj`. The 27B is
   DENSE: there is no router, so the entry only ever hits gate_proj, which is then
   left as a plain nn.Linear holding an FP8 tensor with no dequant path. First
   matmul dies with

       RuntimeError: expected mat1 and mat2 to have the same dtype,
                     but got: c10::BFloat16 != c10::Float8_e4m3fn

   Dropping the bare `mlp.gate` entries fixes it (verified: gate_proj becomes
   FP8Linear, 17*23 -> 391, 29.9 GB, reasoning intact).
"""
import json, os
from pathlib import Path
import torch
from transformers.quantizers import quantizer_finegrained_fp8 as qfp8

_orig = qfp8.FineGrainedFP8HfQuantizer.update_tp_plan
def _safe_tp_plan(self, config):
    try:
        return _orig(self, config)
    except AttributeError:
        return config
qfp8.FineGrainedFP8HfQuantizer.update_tp_plan = _safe_tp_plan

from transformers import AutoModelForCausalLM, AutoConfig, FineGrainedFP8Config  # noqa: E402


def _config_path(model_id):
    try:
        from huggingface_hub import hf_hub_download
        return hf_hub_download(model_id, "config.json")
    except Exception:
        p = Path(model_id) / "config.json"
        return str(p) if p.exists() else None


def load(model_id, device="cuda:0", **kw):
    """from_pretrained with the gate_proj skip-list collision repaired."""
    qc = None
    cp = _config_path(model_id)
    if cp:
        raw = json.load(open(cp)).get("quantization_config") or {}
        skip = raw.get("modules_to_not_convert") or []
        keep = [x for x in skip if not x.endswith("mlp.gate")]
        if len(keep) != len(skip):
            print(f"[fp8_load] dropped {len(skip)-len(keep)} 'mlp.gate' skip entries "
                  f"that collide with mlp.gate_proj", flush=True)
            qc = FineGrainedFP8Config(
                activation_scheme=raw.get("activation_scheme", "dynamic"),
                modules_to_not_convert=keep)
    kw.setdefault("dtype", "auto")
    m = AutoModelForCausalLM.from_pretrained(model_id, device_map=device,
                                             quantization_config=qc, **kw) if qc \
        else AutoModelForCausalLM.from_pretrained(model_id, device_map=device, **kw)
    return m.eval()
