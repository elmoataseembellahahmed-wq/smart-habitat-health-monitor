"""Layer 2: analyse each signal against the astronaut's OWN baseline.

For every signal we compute the personal baseline (mean and spread over the
baseline window), then measure how far today's value is from it in the
unhealthy direction. Absolute safety limits (for example blood oxygen below 92%)
are checked too, whatever the personal normal. Every flag carries a plain-language
reason, so the crew and the flight surgeon can see exactly why it was raised.
"""

from statistics import mean, pstdev

from .signals import SIGNALS, CABIN_SIGNALS

# With 13 signals checked every day, 2 standard deviations would raise a false flag
# on most days from natural noise alone, so the bar is set a little higher.
MILD_Z = 2.5    # 2.5 standard deviations away from personal normal
STRONG_Z = 3.5  # 3.5 standard deviations away


def compute_baseline(days, baseline_days):
    """Mean and spread of each signal over the baseline window."""
    baseline = {}
    for key, meta in SIGNALS.items():
        values = [days[d][key] for d in baseline_days if d in days]
        spread = pstdev(values) if len(values) > 1 else 0.0
        # Floor on the spread so tiny natural variation doesn't cause false alarms.
        floor = meta.get("min_sd", max(abs(mean(values)) * 0.03, 0.5))
        baseline[key] = {"mean": mean(values), "sd": max(spread, floor)}
    return baseline


def _bad_z(key, value, base):
    """Distance from baseline in the unhealthy direction (positive = worse)."""
    z = (value - base["mean"]) / base["sd"]
    bad = SIGNALS[key]["bad"]
    if bad == "both":
        return abs(z)
    return z if bad == "high" else -z


def _fmt(key, value, table=SIGNALS):
    d = table[key]["decimals"]
    return f"{value:.{d}f}" if d else f"{round(value)}"


def hard_limit_broken(key, value):
    """Return ("below", limit) or ("above", limit) if a safety limit is broken, else None."""
    meta = SIGNALS[key]
    if "hard_low" in meta and value < meta["hard_low"]:
        return ("below", meta["hard_low"])
    if "hard_high" in meta and value > meta["hard_high"]:
        return ("above", meta["hard_high"])
    return None


def analyse_signal(key, day, days, baseline):
    """Return the analysis of one signal on one day."""
    meta = SIGNALS[key]
    value = days[day][key]
    base = baseline[key]
    bad_z = _bad_z(key, value, base)

    # How many days in a row (ending today) this signal has been at least mildly off.
    streak = 0
    d = day
    while d in days and _bad_z(key, days[d][key], base) >= MILD_Z:
        streak += 1
        d -= 1

    level = None
    if bad_z >= STRONG_Z:
        level = "strong"
    elif bad_z >= MILD_Z:
        level = "mild"
    broken = hard_limit_broken(key, value)
    if broken:
        level = "critical"

    result = {
        "signal": key,
        "name": meta["name"],
        "unit": meta["unit"],
        "device": meta["device"],
        "system": meta["system"],
        "domain": meta["domain"],
        "value": value,
        "baseline": round(base["mean"], 2),
        "z": round(bad_z, 2),
        "level": level,
        "streak_days": streak,
        "limit": broken,
        "reason": None,
    }
    if level:
        pct = abs(value - base["mean"]) / base["mean"] * 100 if base["mean"] else 0
        direction = "above" if value > base["mean"] else "below"
        text = (f"{meta['name']} is {_fmt(key, value)} {meta['unit']}, "
                f"{pct:.0f}% {direction} this astronaut's normal "
                f"({_fmt(key, base['mean'])} {meta['unit']})")
        if streak >= 2:
            text += f" for {streak} days in a row"
        if broken:
            text += f"; {broken[0]} the safety limit of {broken[1]:g} {meta['unit']}"
        result["reason"] = text + "."
    return result


def analyse_cabin(day, cabin):
    """Cabin readings are judged against fixed limits shared by the whole crew."""
    out = []
    for key, meta in CABIN_SIGNALS.items():
        value = cabin[day][key]
        level = "act" if value >= meta["act"] else "watch" if value >= meta["watch"] else None
        reason = None
        if level:
            limit = meta[level]
            reason = (f"{meta['name']} is {_fmt(key, value, CABIN_SIGNALS)} {meta['unit']}, "
                      f"above the {level} limit of {limit} {meta['unit']}.")
        out.append({"signal": key, "name": meta["name"], "unit": meta["unit"],
                    "value": value, "level": level, "reason": reason})
    return out
