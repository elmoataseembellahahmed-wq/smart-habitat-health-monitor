"""Version of every part that can change what the system says.

Each decision and report records these, together with the personal-normal version
(which days it was learned from), so any past alert can be reproduced exactly with
the same rules, thresholds and model. Change a number here whenever the matching
part changes.
"""

SOFTWARE = "1.4.0"
RULES = "rules-r4"            # engine/fusion.py, engine/integrity.py, engine/quality.py
THRESHOLDS = "thresholds-r3"  # engine/analysis.py (2.5 / 3.5 SD), engine/signals.py limits
MODEL = "iforest-r2"          # engine/anomaly.py: 200 trees, 500 samples, margin 0.09
STATUS = "prototype: thresholds and actions are not clinically validated or mission-approved"


def stamp():
    return {"software": SOFTWARE, "rules": RULES, "thresholds": THRESHOLDS, "model": MODEL,
            "status": STATUS}
