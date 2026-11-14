"""Layer 2: analyse each signal against the astronaut's OWN baseline.

For every signal we compute the personal baseline (mean and spread over the
baseline window), then measure how far today's value is from it in the
unhealthy direction. Absolute safety limits (for example blood oxygen below 92%)
are checked too, whatever the personal normal. Every flag carries a plain-language
reason, so the crew and the flight surgeon can see exactly why it was raised.
"""

from statistics import mean, pstdev

from .signals import SIGNALS, CABIN_SIGNALS, CAREER_DOSE_LIMIT, CO2_7DAY_REFERENCE

# With 13 signals checked every day, 2 standard deviations would raise a false flag
# on most days from natural noise alone, so the bar is set a little higher.
MILD_Z = 2.5    # 2.5 standard deviations away from personal normal
STRONG_Z = 3.5  # 3.5 standard deviations away


def compute_baseline(days, baseline_days):
    """Mean and spread of each signal over the baseline window."""
    baseline = {}
    for key, meta in SIGNALS.items():
        # Unavailable readings (sensor faults, skipped diary) are never learned from.
        values = [days[d][key] for d in baseline_days if d in days and days[d].get(key) is not None]
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
    while d in days and days[d].get(key) is not None and _bad_z(key, days[d][key], base) >= MILD_Z:
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
        if meta.get("confirm_first"):
            # An estimate (webcam heart or breathing rate) is a warning to confirm by hand, never an emergency alone.
            level = "strong"

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
            if meta.get("confirm_first"):
                text += " (a webcam estimate: confirm now by checking the pulse or counting breaths by hand)"
        result["reason"] = text + "."
    return result


def analyse_cabin(day, cabin):
    """Cabin readings are judged against fixed limits shared by the whole crew."""
    out = []
    for key, meta in CABIN_SIGNALS.items():
        value = cabin[day].get(key)
        if value is None:
            if meta.get("optional"):
                out.append({"signal": key, "name": meta["name"], "unit": meta["unit"], "value": None,
                            "level": None, "reason": None, "unavailable": True,
                            "note": f"{meta['name']}: sensor unavailable (no value is guessed)."})
                continue
            raise KeyError(f"Cabin value '{key}' missing on day {day}")
        level, side = None, "above"
        if value >= meta["act"]:
            level = "act"
        elif value >= meta["watch"]:
            level = "watch"
        elif "low_act" in meta and value <= meta["low_act"]:
            level, side = "act", "below"
        elif "low_watch" in meta and value <= meta["low_watch"]:
            level, side = "watch", "below"
        reason = None
        if level:
            limit = meta[level] if side == "above" else meta["low_" + level]
            reason = (f"{meta['name']} is {_fmt(key, value, CABIN_SIGNALS)} {meta['unit']}, "
                      f"{side} the {level} limit of {limit} {meta['unit']}.")
            if key in ("temperature", "humidity"):
                reason += " (NASA-STD-3001 [V2 6012] envelope: 18 °C/75% to 27 °C/25%.)"
        item = {"signal": key, "name": meta["name"], "unit": meta["unit"],
                "value": value, "level": level, "reason": reason}
        past = [cabin[d][key] for d in cabin if d <= day]
        if key == "radiation":
            # One day's dose says little about risk; the running mission total matters.
            total = sum(past)
            item.update(mission_total=round(total, 1), career_limit=CAREER_DOSE_LIMIT,
                        pct_of_career_limit=round(total / CAREER_DOSE_LIMIT * 100, 1),
                        note=(f"Mission total so far {total:.1f} mSv, {total / CAREER_DOSE_LIMIT * 100:.0f}% "
                              f"of NASA's 600 mSv career limit (simulated dosimeter)."))
        if key == "co2":
            week = [cabin[d][key] for d in cabin if day - 7 < d <= day]
            avg = sum(week) / len(week)
            item.update(avg_7d=round(avg, 2), note=(
                f"7-day average {avg:.1f} mmHg" + (f", above the {CO2_7DAY_REFERENCE} mmHg level that keeps "
                                                   "headache risk low." if avg > CO2_7DAY_REFERENCE else ".")))
        out.append(item)
    return out
