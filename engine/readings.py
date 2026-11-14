"""Several readings a day, and re-measuring before an emergency.

A typed measurement is one moment of the day. To make the result more valid:

* The MORNING reading (same conditions every day: rested, before eating) is the one
  compared with the personal normal, so like is compared with like.
* The astronaut can add more readings the same day: in the evening, or any time he
  feels unwell. Any of them that breaks a safety limit counts at once (immediate path).
* A value past a safety limit is checked once more before it is trusted: the astronaut
  is asked to RE-MEASURE after 5 minutes.
    - Re-measure also past the limit: CONFIRMED, it stays critical (ACT).
    - Re-measure back within the limit: NOT CONFIRMED, probably a measuring error (cold
      hand on the oximeter, talking during the cuff reading). No emergency; it is noted.
    - Not re-measured yet: it stays critical (safety first), with "re-measure now".

Extra readings are stored per day as
  crew[aid][day]["extra"] = [{"signal": ..., "value": ..., "when": "HH:MM", "kind": ...}]
with kind "evening", "unwell" or "re-measure".
"""

from .analysis import hard_limit_broken, _fmt
from .quality import VALID
from .signals import SIGNALS

KINDS = ("evening", "unwell", "re-measure")
KIND_TEXT = {"evening": "Evening reading", "unwell": "Reading taken while feeling unwell",
             "re-measure": "Re-measured value"}


def extras(days, day, key):
    out = []
    for x in days[day].get("extra") or []:
        if x.get("signal") != key or x.get("value") is None:
            continue
        lo, hi = VALID[key]
        if lo <= float(x["value"]) <= hi:        # an impossible extra value is a typo: ignored
            out.append(x)
    return out


def apply(entry, key, day, days):
    """Update one signal's analysis with the extra readings of that day."""
    meta = SIGNALS[key]
    more = extras(days, day, key)
    if not more:
        if entry.get("level") == "critical":
            entry["remeasure_needed"] = True
            entry["reason"] += " Re-measure in 5 minutes to confirm."
        return entry
    entry["extra_readings"] = [{"value": x["value"], "when": x.get("when"), "kind": x.get("kind")} for x in more]
    # 1. Evening or 'unwell' readings past a safety limit count at once.
    for x in more:
        if x.get("kind") == "re-measure":
            continue
        broken = hard_limit_broken(key, float(x["value"]))
        if broken and entry.get("level") != "critical" and not meta.get("confirm_first"):
            entry.update(level="critical", limit=broken, alert_value=x["value"],
                         reason=(f"{KIND_TEXT.get(x.get('kind'), 'Extra reading')} at {x.get('when', '?')}: "
                                 f"{meta['name'].lower()} {_fmt(key, float(x['value']))} {meta['unit']}, "
                                 f"{broken[0]} the safety limit of {broken[1]:g} {meta['unit']}."))
    # 2. A critical value is confirmed or not by the re-measure.
    if entry.get("level") == "critical":
        checks = [x for x in more if x.get("kind") == "re-measure"]
        if not checks:
            entry["remeasure_needed"] = True
            entry["reason"] += " Re-measure in 5 minutes to confirm."
        elif hard_limit_broken(key, float(checks[-1]["value"])):
            entry["confirmed"] = True
            entry["reason"] += (f" Confirmed on re-measure ({_fmt(key, float(checks[-1]['value']))} "
                                f"{meta['unit']}).")
        else:
            v = float(checks[-1]["value"])
            entry.update(level="mild", limit=None, unconfirmed=True,
                         reason=(f"{meta['name']} read {_fmt(key, float(entry.get('alert_value', entry['value'])))} "
                                 f"{meta['unit']}, past the safety limit, but the re-measure was "
                                 f"{_fmt(key, v)} {meta['unit']}: not confirmed, probably a measuring error. "
                                 "No emergency; keep an eye on it."))
    return entry
