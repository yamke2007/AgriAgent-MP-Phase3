from decimal import Decimal, InvalidOperation
from agriagent import normalization as n

def matches(pred, ref):
    if any(fn(pred.get(k,"")) != fn(ref.get(k,"")) for k,fn in
           (("crop",n.crop),("location",n.location),("period",n.period),("variable",n.text))):
        return False
    pu, ru = pred.get("unit"),ref.get("unit")
    pk, rk = n.UNITS.get(pu,(pu,None)),n.UNITS.get(ru,(ru,None))
    if pk[0] != rk[0] or pk[1] is None or rk[1] is None:
        return False
    kind = ref.get("value_kind","decimal")
    if kind in ("integer","code","text"):
        if kind == "text" or kind == "code":
            return pu == ru and n.text(pred.get("value","")) == n.text(ref.get("value",""))
        try:
            return n.number(pred["value"])*pk[1] == n.number(ref["value"])*rk[1]
        except (InvalidOperation,KeyError):
            return False
    try:
        p,r = n.number(pred["value"])*pk[1],n.number(ref["value"])*rk[1]
        return p.is_finite() and r.is_finite() and abs(p-r) <= abs(r)*Decimal("0.01")
    except (InvalidOperation,KeyError):
        return False

def counts(predicted, references):
    remaining = list(references)
    tp = 0
    for pred in predicted:
        index = next((i for i,r in enumerate(remaining) if matches(pred,r)),None)
        if index is not None:
            tp += 1
            remaining.pop(index)
    return tp,len(predicted)-tp,len(remaining)

def f1(tp,fp,fn):
    return 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0
