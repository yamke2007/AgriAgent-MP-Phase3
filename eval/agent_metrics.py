"""Agent-level evaluators added for Phase 2.

- trajectory_match: AgentEvals trajectory match (M8). Our trajectories are
  converted to OpenAI-style tool-call messages, the format AgentEvals expects.
- grounded: deterministic groundedness (M10). A value is grounded when its
  exact string appears in the source evidence the tool returned for that
  locator (row text). No LLM judge is used, so no judge calibration is needed.
- workflow_eval: end-to-end workflow success (M11) over eval/workflow_cases.json,
  plus one live fault injection that must be recovered by a retry.
"""
import json

from agriagent.normalization import MISSING, NA, text


def to_messages(trajectory):
    msgs = [{"role": "user", "content": "extract observations"}]
    for i, c in enumerate(trajectory):
        msgs.append({"role": "assistant", "content": "", "tool_calls": [{
            "id": f"call_{i}", "type": "function",
            "function": {"name": c["tool"], "arguments": json.dumps(c.get("arguments") or {}, sort_keys=True)}}]})
        msgs.append({"role": "tool", "content": "ok", "tool_call_id": f"call_{i}"})
    msgs.append({"role": "assistant", "content": "done"})
    return msgs


_cache = {}


def trajectory_match(actual, reference, mode="strict", args_mode="exact"):
    """AgentEvals trajectory match; falls back to exact comparison if agentevals is not installed."""
    try:
        from agentevals.trajectory.match import create_trajectory_match_evaluator
    except ImportError:
        return actual == reference
    key = (mode, args_mode)
    if key not in _cache:
        _cache[key] = create_trajectory_match_evaluator(trajectory_match_mode=mode, tool_args_match_mode=args_mode)
    return bool(_cache[key](outputs=to_messages(actual), reference_outputs=to_messages(reference))["score"])


def grounded(record):
    value = text(record.get("value", ""))
    if not value or value in (MISSING, NA):
        return False
    evidence = text(record.get("evidence", ""))
    return value in evidence or value in evidence.replace(",", "")


def workflow_eval(root, process):
    cases = json.loads((root / "eval/workflow_cases.json").read_text(encoding="utf-8"))
    rows = []
    for c in cases:
        r = process(root / c["input"], persist=c.get("persist", False), inject_tool=c.get("inject_tool"))
        ok = r["status"] == c["expected_status"] and r.get("agents", []) == c["expected_plan"]
        if c.get("inject_tool"):
            ok = ok and r.get("retries", 0) >= 1
        rows.append(dict(input=c["input"], expected_status=c["expected_status"], status=r["status"],
                         plan=r.get("agents"), producers=r["agent"], handoffs=r.get("handoffs", []),
                         retries=r.get("retries", 0), fault=c.get("inject_tool"), correct=ok,
                         synthetic=c.get("synthetic", False), run_id=r["run_id"]))
    return rows
