"""Two data-integrity checks that keep the health rules honest.

1. Wristband swap check.
   Each wristband carries an astronaut's ID, and every astronaut has their own normal
   for heart rate, HRV, blood oxygen, temperature and sleep. If two astronauts swap
   bands, each band suddenly reads like the OTHER person's normal. When that happens
   the system does not raise a health alarm (the cause is the band, not an illness):
   it ignores that day's wristband readings and asks both astronauts to check their band.
   No face recognition is needed: the signals themselves give the swap away.

2. Slow-drift check (fixed anchor).
   The personal normal is re-learned every week, so a decline slow enough to look
   "normal" every single day could be absorbed into it little by little. To catch this,
   the normal learned in days 1-14 is kept as a fixed anchor. If the current normal has
   moved far from the anchor in the unhealthy direction, the flight surgeon is told,
   even though no single day crossed a limit.
"""

from .signals import SIGNALS, CORE_SIGNALS

# Signals that come from the wristband (the device that carries the astronaut's ID).
WRIST_SIGNALS = [k for k in CORE_SIGNALS if SIGNALS[k]["device"] == "wristband"]

# Swap: each band must fit the other person's normal clearly better than its owner's.
SWAP_RATIO = 0.5    # swapped fit must be at most half the "as labelled" distance
SWAP_MARGIN = 12.0  # and better by at least this much (sum of squared z, both bands)

# Drift: how far (in the anchor's standard deviations) the current normal may move.
DRIFT_Z = 1.5


def _distance(reading, base):
    """Sum of squared z-scores of the wristband signals against one person's normal."""
    return sum(((reading[k] - base[k]["mean"]) / base[k]["sd"]) ** 2 for k in WRIST_SIGNALS)


def band_swap(aid, day, crew_data, baseline_for, crew_ids):
    """Return {"with": other_id, ...} if aid's band looks swapped with another band, else None.

    baseline_for(aid, day) gives the personal normal in use on that day.
    """
    mine = crew_data[aid][day]
    if any(mine.get(k) is None for k in WRIST_SIGNALS):
        return None                     # a wristband reading is unavailable: can't compare
    base_me = baseline_for(aid, day)
    best = None
    for other in crew_ids:
        if other == aid or day not in crew_data[other]:
            continue
        theirs = crew_data[other][day]
        if any(theirs.get(k) is None for k in WRIST_SIGNALS):
            continue
        base_other = baseline_for(other, day)
        as_labelled = _distance(mine, base_me) + _distance(theirs, base_other)
        swapped = _distance(mine, base_other) + _distance(theirs, base_me)
        each_fits_other = (_distance(mine, base_other) < _distance(mine, base_me)
                           and _distance(theirs, base_me) < _distance(theirs, base_other))
        if (each_fits_other and swapped <= SWAP_RATIO * as_labelled
                and as_labelled - swapped >= SWAP_MARGIN):
            gain = as_labelled - swapped
            if best is None or gain > best["gain"]:
                best = {"with": other, "gain": round(gain, 1),
                        "as_labelled": round(as_labelled, 1), "swapped": round(swapped, 1)}
    return best


def _bad_shift(key, now, anchor):
    z = (now["mean"] - anchor["mean"]) / anchor["sd"]
    bad = SIGNALS[key]["bad"]
    if bad == "both":
        return abs(z)
    return z if bad == "high" else -z


def drift(anchor, current):
    """Signals whose current personal normal moved too far from the day 1-14 anchor."""
    out = []
    for key in CORE_SIGNALS:
        shift = _bad_shift(key, current[key], anchor[key])
        if shift >= DRIFT_Z:
            meta = SIGNALS[key]
            d = meta["decimals"]
            fmt = (lambda v: f"{v:.{d}f}") if d else (lambda v: f"{round(v)}")
            out.append({
                "signal": key, "name": meta["name"], "unit": meta["unit"],
                "anchor": round(anchor[key]["mean"], 2), "now": round(current[key]["mean"], 2),
                "shift": round(shift, 2),
                "reason": (f"{meta['name']}: this astronaut's normal has slowly moved from "
                           f"{fmt(anchor[key]['mean'])} to {fmt(current[key]['mean'])} {meta['unit']} "
                           f"since the start of the mission ({shift:.1f} standard deviations)."),
            })
    return sorted(out, key=lambda x: -x["shift"])
