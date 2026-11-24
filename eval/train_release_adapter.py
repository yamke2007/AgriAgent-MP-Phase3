"""Run genuine base inference, QLoRA training, and adapter inference on a CUDA host."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.model import MAX_GENERATION, predict, prompt_for
from eval.heldout import load_cases, sha, verify_training

BASE = "Qwen/Qwen2.5-1.5B-Instruct"
BASE_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
PACKAGES = ("torch", "transformers", "trl", "peft", "accelerate", "bitsandbytes", "datasets")
MAX_SEQUENCE = 4096


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def training_settings(output):
    return dict(output_dir=str(output / "trainer"), num_train_epochs=3, per_device_train_batch_size=1,
                gradient_accumulation_steps=8, learning_rate=2e-4, logging_steps=1,
                save_strategy="no", report_to="none", fp16=True, seed=7, max_length=MAX_SEQUENCE)


def adapter_settings():
    return dict(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])


def conversation(example):
    return [{"role": "user", "content": example["prompt"]},
            {"role": "assistant", "content": json.dumps(example["target"], ensure_ascii=False)}]


def token_budget(tokenizer, examples, cases):
    chats = [conversation(example) for example in examples]
    sequences = [len(tokenizer.apply_chat_template(chat)) for chat in chats]
    targets = [len(tokenizer(chat[1]["content"], add_special_tokens=False).input_ids) for chat in chats]
    inputs = []
    for case in cases:
        path = ROOT / case["input"]
        message = [{"role": "user", "content": prompt_for(path.read_text(encoding="utf-8-sig"), path.name)}]
        inputs.append(len(tokenizer.apply_chat_template(message, add_generation_prompt=True)))
    if max(sequences) > MAX_SEQUENCE or max(inputs) > 3072 or max(targets) + 32 > MAX_GENERATION:
        raise ValueError("Frozen training, evaluation or output budget exceeded")
    return {"longest_training_sequence": max(sequences), "longest_evaluation_input": max(inputs),
            "longest_training_target": max(targets)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/m18")
    parser.add_argument("--revision", default=BASE_REVISION, help="Full immutable Hugging Face model revision SHA")
    args = parser.parse_args()
    if len(args.revision) != 40 or any(char not in "0123456789abcdef" for char in args.revision):
        parser.error("Expected a full model commit SHA")
    cases = load_cases(ROOT, references=False)
    examples = verify_training(ROOT, cases)
    if not examples or not all(example["checked"] for example in examples):
        raise ValueError("Training examples must have source-derived checked targets")

    import torch
    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable. Run this workflow in a Colab GPU runtime.")

    from datasets import Dataset
    from peft import LoraConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
    from trl import SFTConfig, SFTTrainer

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error("Choose an empty output directory")
    set_seed(7)
    opts = dict(revision=args.revision, trust_remote_code=False)
    tokenizer = AutoTokenizer.from_pretrained(BASE, **opts)
    budget = token_budget(tokenizer, examples, cases)
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                     bnb_4bit_compute_dtype=torch.float16)
    adapter_config = LoraConfig(**adapter_settings())
    training_config = SFTConfig(**training_settings(output))
    write_json(output / "configuration.json", {
        "base": BASE, "revision": args.revision, "gpu": torch.cuda.get_device_name(0),
        "packages": {package: importlib.metadata.version(package) for package in PACKAGES},
        "case_lock_sha256": sha(ROOT / "eval/m18_cases.json"),
        "training_sha256": sha(ROOT / "data/train/examples.jsonl"),
        "training_examples": len(examples), "evaluation_cases": [case["case_id"] for case in cases],
        "quantization": {"bits": 4, "quant_type": "nf4", "compute": "float16"},
        "lora": adapter_settings(),
        "training": training_config.to_dict(), "decode": {"do_sample": False, "max_new_tokens": MAX_GENERATION},
        "token_budget": budget,
    })

    def base_model():
        return AutoModelForCausalLM.from_pretrained(BASE, quantization_config=quantization,
                                                   device_map={"": 0}, **opts)

    def export(condition, model):
        predictions, trace = {}, {}
        model.eval()
        for case in cases:
            key = case["case_id"]
            try:
                predictions[key], trace[key] = predict(model, tokenizer, ROOT / case["input"], MAX_GENERATION)
            except (ValueError, TypeError) as exc:
                predictions[key] = []
                trace[key] = {"decode_error": str(exc)}
        write_json(output / (condition + ".json"), predictions)
        write_json(output / (condition + "_trace.json"), trace)

    base = base_model()
    export("base", base)
    # The same quantized checkpoint proceeds to training only after the baseline is saved.
    dataset = Dataset.from_list([{"messages": conversation(example)} for example in examples])
    trainer = SFTTrainer(model=base, args=training_config, train_dataset=dataset,
                         processing_class=tokenizer, peft_config=adapter_config)
    trainer.train()
    trainer.save_model(str(output / "adapter"))
    write_json(output / "training_log.json", trainer.state.log_history)
    del trainer, base
    gc.collect()
    torch.cuda.empty_cache()
    adapted = PeftModel.from_pretrained(base_model(), output / "adapter", is_trainable=False)
    export("adapter", adapted)
    write_json(output / "hashes.json", {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.rglob("*")) if path.is_file()
    })


if __name__ == "__main__":
    main()
