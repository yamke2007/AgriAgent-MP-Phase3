# LoRA training data (M18)

`raw/` holds 72 training inputs built by `scripts/build_agmarknet_training.py` from real Agmarknet daily price records (Madhya Pradesh markets; soybean, wheat, maize; years 2008-2010). The evaluation cases use 2011-2017 only, so no file, date or row is shared.
`examples.jsonl` has one example per input: the same prompt as `eval/infer_adapter.py` and a target copied from the source cells by the script (no model). Spot-check at least 5 examples against `raw/` before training.

The hash audit (`eval/contamination.py`) excludes this README and checks all other files recursively against every evaluation input and parent source: 0 overlaps.

No model or adapter has been trained yet. Run `eval/train_lora_colab.py` on Colab (see `eval/README.md`, section "M18 on Colab").

To add other training sources, put them in `raw/` and run `python scripts/build_training_set.py` (pipeline-drafted targets with `checked: false` that must be reviewed). Never use evaluation cases or their parent files.
