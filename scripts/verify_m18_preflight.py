"""Verify the frozen Colab package and exercise a tiny CPU-only LoRA round trip."""
import argparse
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.model import load_local
from eval.heldout import load_cases, verify_training
from eval.train_release_adapter import adapter_settings, token_budget, training_settings


def verify_package(package, required):
    with ZipFile(package / "agriagent-colab-inputs.zip") as bundle:
        members = bundle.namelist()
        if len(members) != len(set(members)) or set(members) != required or bundle.testzip():
            raise ValueError("M18 archive is corrupt, includes unexpected files or is incomplete")
        for name in members:
            data = bundle.read(name)
            if data != (ROOT / name).read_bytes():
                raise ValueError(f"Packaged file differs from current source: {name}")
            if name.endswith(".py"):
                compile(data, name, "exec")
    notebook = json.loads((package / "AgriAgent_M18.ipynb").read_text(encoding="utf-8"))
    if notebook["metadata"]["accelerator"] != "GPU":
        raise ValueError("Notebook is missing its GPU runtime setting")
    for cell in notebook["cells"]:
        code = "".join(cell["source"])
        if cell["cell_type"] == "code" and not code.startswith("%pip "):
            compile(code, "notebook", "exec")
    return len(members)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ["HF_DATASETS_CACHE"] = str(args.output / "cache")
    os.environ["HF_HUB_OFFLINE"] = "1"
    cases = load_cases()
    examples = verify_training(ROOT, cases)
    required = {
        "agriagent/__init__.py", "agriagent/model.py", "data/train/examples.jsonl",
        "eval/__init__.py", "eval/heldout.py", "eval/m18_cases.json",
        "eval/requirements-colab.txt", "eval/train_release_adapter.py",
        *(case["input"] for case in cases), *(example["source"] for example in examples),
    }
    members = verify_package(args.package, required)

    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoTokenizer, Qwen2Config, Qwen2ForCausalLM, set_seed
    from trl import SFTConfig, SFTTrainer

    torch.set_num_threads(2)
    set_seed(7)
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
    budget = token_budget(tokenizer, examples, cases)
    settings = training_settings(args.output)
    settings.update(use_cpu=True, fp16=False, max_steps=1, gradient_accumulation_steps=1,
                    gradient_checkpointing=False, max_length=128, disable_tqdm=True)
    configuration = Qwen2Config(vocab_size=len(tokenizer), hidden_size=32, intermediate_size=64,
                                num_attention_heads=4, num_key_value_heads=2, num_hidden_layers=1,
                                max_position_embeddings=128, bos_token_id=tokenizer.bos_token_id,
                                eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id)
    base = Qwen2ForCausalLM(configuration)
    base_dir = args.output.resolve() / "smoke-base"
    base.save_pretrained(base_dir)
    tokenizer.save_pretrained(base_dir)
    dataset = Dataset.from_list([{"messages": [
        {"role": "user", "content": "Return an empty list."}, {"role": "assistant", "content": "[]"},
    ]}])
    trainer = SFTTrainer(model=base, args=SFTConfig(**settings), train_dataset=dataset,
                         processing_class=tokenizer, peft_config=LoraConfig(**adapter_settings()))
    trainer.train()
    adapter = args.output / "smoke-adapter"
    trainer.save_model(str(adapter))
    restored, loaded_tokenizer = load_local(str(base_dir), str(adapter.resolve()))
    has_weights = any("lora_B" in key and torch.count_nonzero(tensor).item() > 0
                      for key, tensor in restored.state_dict().items())
    ids = loaded_tokenizer("Return an empty list.", return_tensors="pt")
    with torch.inference_mode():
        outcome = restored.generate(**ids, do_sample=False, max_new_tokens=2)
    generated = outcome.shape[-1] - ids.input_ids.shape[-1]
    if trainer.state.global_step != 1 or not has_weights or generated < 1:
        raise ValueError("CPU adapter train/save/reload/inference smoke test failed")
    report = {
        "scope": "Synthetic, randomly initialized CPU compatibility check; no M18 predictions or scores",
        "archive_members": members, "frozen_cases": len(cases),
        "training_examples_verified_against_source_cells": len(examples),
        "training_cells": sum(len(e["target"]) for e in examples),
        "versions": {name: importlib.metadata.version(name) for name in
                     ("torch", "transformers", "trl", "peft", "accelerate", "bitsandbytes", "datasets")},
        "token_budget": budget, "steps": trainer.state.global_step,
        "adapter_parameters_updated": has_weights, "smoke_generated_tokens": generated,
        "cuda_available": torch.cuda.is_available(),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
