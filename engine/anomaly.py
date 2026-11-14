"""AI layer: an Isolation Forest anomaly detector, one per astronaut.

Why Isolation Forest: it learns what "normal" looks like from unlabeled data, so it
does not need examples of sick astronauts (which don't exist publicly). It builds
many random trees that split the data; unusual days get isolated in fewer splits,
so a short average path = an unusual day.

Each astronaut gets their own forest, trained only on their baseline days, using all
8 signals together. That lets it catch unusual COMBINATIONS that no single rule
looks for. It runs beside the rules, not instead of them: the rules explain, the
model double-checks.

Written in plain Python (no scikit-learn needed) so it runs on board with no extra
installs. The algorithm follows Liu, Ting and Zhou (2008).
"""

import math
import random

N_TREES = 200
SEED = 7


def _c(n):
    """Average path length of an unsuccessful search in a binary search tree of n points."""
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    return 2.0 * (math.log(n - 1) + 0.5772156649) - 2.0 * (n - 1) / n


def _build(points, depth, max_depth, rng):
    if depth >= max_depth or len(points) <= 1:
        return {"size": len(points)}
    dims = len(points[0])
    for _ in range(dims):  # pick a feature that actually varies
        f = rng.randrange(dims)
        lo = min(p[f] for p in points)
        hi = max(p[f] for p in points)
        if hi > lo:
            break
    else:
        return {"size": len(points)}
    split = rng.uniform(lo, hi)
    left = [p for p in points if p[f] < split]
    right = [p for p in points if p[f] >= split]
    return {"f": f, "split": split,
            "left": _build(left, depth + 1, max_depth, rng),
            "right": _build(right, depth + 1, max_depth, rng)}


def _path(node, x, depth=0):
    while "f" in node:
        node = node["left"] if x[node["f"]] < node["split"] else node["right"]
        depth += 1
    return depth + _c(node["size"])


class IsolationForest:
    def __init__(self, n_trees=N_TREES, sample_size=256, seed=SEED):
        self.n_trees = n_trees
        self.sample_size = sample_size
        self.seed = seed
        self.trees = []
        self.n = 0

    def fit(self, data):
        rng = random.Random(self.seed)
        self.n = min(self.sample_size, len(data))
        max_depth = math.ceil(math.log2(max(self.n, 2)))
        self.trees = [_build(rng.sample(data, self.n), 0, max_depth, rng) for _ in range(self.n_trees)]
        return self

    def score(self, x):
        """Anomaly score in (0, 1): about 0.5 or lower = normal, closer to 1 = more unusual."""
        mean_path = sum(_path(t, x) for t in self.trees) / len(self.trees)
        return 2.0 ** (-mean_path / _c(self.n))


class AnomalyModel:
    """Per-astronaut forest on standardized signals, with a threshold learned from the baseline."""

    MARGIN = 0.09     # a day must score this much above the most unusual baseline day
                      # (normal day-to-day variation after the baseline stays below this)
    N_AUGMENT = 500   # plausible normal days generated from the real baseline days
    JITTER = 0.5      # noise added, in baseline standard deviations

    def __init__(self, days, baseline_days, baseline_stats, signal_keys):
        self.keys = list(signal_keys)
        self.stats = baseline_stats
        real = [self._vector(days[d]) for d in baseline_days
                if d in days and all(days[d].get(k) is not None for k in self.keys)]
        # 14 real days are too few for a forest to tell "a bit unusual" from "very
        # unusual". So we resample the real baseline days with small noise. This keeps
        # how the signals move together on real days, and gives the trees enough data.
        rng = random.Random(SEED)
        train = [[v + rng.gauss(0, self.JITTER) for v in rng.choice(real)]
                 for _ in range(self.N_AUGMENT)]
        self.forest = IsolationForest().fit(train)
        self.threshold = max(self.forest.score(v) for v in real) + self.MARGIN
        self.strong = self.threshold + 0.08

    def _vector(self, reading):
        return [(reading[k] - self.stats[k]["mean"]) / self.stats[k]["sd"] for k in self.keys]

    def assess(self, reading):
        s = self.forest.score(self._vector(reading))
        level = "strong" if s >= self.strong else "unusual" if s >= self.threshold else "normal"
        return {"score": round(s, 3), "threshold": round(self.threshold, 3), "level": level}
