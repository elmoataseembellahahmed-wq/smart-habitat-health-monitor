"""Data ingestion layer for real devices (for example the ESP32 wristband).

Every sample a device sends carries its device ID and its own timestamp. Before any
reading can be used, this layer:

  * accepts only PAIRED devices (device ID -> astronaut ID), so data is filed by the
    device, never by a face or a name typed in;
  * rejects a timestamp too far in the future (bad device clock);
  * drops DUPLICATES (same device and timestamp: a resend after a lost link);
  * accepts LATE samples (sent from the device's buffer after a link loss) and files
    them on the day they were measured;
  * drops physically impossible values (same plausible ranges as engine/quality.py);
  * writes every accepted sample to an append-only local file, so nothing is lost on
    a restart and no network is needed.

It then turns one astronaut-day of samples into a daily reading (the median, robust
to spikes) with a data-quality summary: samples received, the longest gap (packet
loss), and noise. That daily reading feeds the same HealthMonitor as everything else.
"""

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from .quality import VALID

MAX_FUTURE_S = 300        # a timestamp more than 5 min ahead = bad device clock
GAP_WARN_MIN = 60         # a gap longer than this in one day = possible packet loss
NOISE_WARN = 0.15         # coefficient of variation above this = noisy signal


def _ts(value):
    """Epoch seconds from an epoch number or an ISO-8601 string."""
    if isinstance(value, (int, float)):
        return float(value)
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


class Ingest:
    def __init__(self, pairing, log_path=None, mission_start=None, now=time.time):
        """pairing: {device_id: astronaut_id}. mission_start: epoch seconds of day 1."""
        self.pairing = dict(pairing)
        self.now = now
        # Default: day 1 starts at midnight UTC today, so mission days follow calendar days.
        self.mission_start = mission_start if mission_start is not None else (now() // 86400) * 86400
        self.samples = {}          # (device_id, ts) -> sample
        self.log_path = Path(log_path) if log_path else None
        self.rejected = []
        if self.log_path and self.log_path.exists():
            for line in self.log_path.read_text(encoding="utf-8").splitlines():
                try:
                    s = json.loads(line)
                    self.samples[(s["device_id"], s["ts"])] = s
                except (ValueError, KeyError):
                    continue

    def mission_day(self, ts):
        return int((ts - self.mission_start) // 86400) + 1

    def accept(self, msg):
        """Take one message from a device. Returns {"status": accepted|duplicate|rejected, ...}."""
        dev = str(msg.get("device_id", ""))
        if dev not in self.pairing:
            return self._reject(msg, "unknown device: pair it with an astronaut first")
        try:
            ts = _ts(msg["timestamp"])
        except (KeyError, ValueError, TypeError):
            return self._reject(msg, "missing or unreadable timestamp")
        if ts > self.now() + MAX_FUTURE_S:
            return self._reject(msg, "timestamp is in the future: check the device clock")
        if (dev, ts) in self.samples:
            return {"status": "duplicate", "device_id": dev, "ts": ts}
        readings, dropped = {}, []
        for key, value in (msg.get("readings") or {}).items():
            if key not in VALID:
                dropped.append(f"{key}: unknown signal")
                continue
            try:
                v = float(value)
            except (TypeError, ValueError):
                dropped.append(f"{key}: not a number")
                continue
            lo, hi = VALID[key]
            if not lo <= v <= hi:
                dropped.append(f"{key}: {v:g} outside {lo:g}-{hi:g} (sensor error)")
                continue
            readings[key] = v
        if not readings:
            return self._reject(msg, "no usable readings (" + "; ".join(dropped) + ")")
        latest = max((t for (d, t) in self.samples if d == dev), default=None)
        sample = {"device_id": dev, "astronaut": self.pairing[dev], "ts": ts,
                  "day": self.mission_day(ts), "readings": readings, "received": self.now(),
                  "late": latest is not None and ts < latest}
        self.samples[(dev, ts)] = sample
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sample) + "\n")
        return {"status": "accepted", "device_id": dev, "astronaut": sample["astronaut"],
                "day": sample["day"], "late": sample["late"], "dropped": dropped}

    def _reject(self, msg, reason):
        self.rejected.append({"device_id": msg.get("device_id"), "reason": reason, "at": self.now()})
        del self.rejected[:-200]
        return {"status": "rejected", "reason": reason}

    def daily(self, aid, day):
        """One astronaut-day: median per signal + data quality per signal."""
        rows = sorted((s for s in self.samples.values() if s["astronaut"] == aid and s["day"] == day),
                      key=lambda s: s["ts"])
        reading, quality = {}, {}
        keys = sorted({k for s in rows for k in s["readings"]})
        for key in keys:
            pts = [(s["ts"], s["readings"][key]) for s in rows if key in s["readings"]]
            vals = [v for _, v in pts]
            gaps = [(b[0] - a[0]) / 60 for a, b in zip(pts, pts[1:])]
            mean = statistics.fmean(vals)
            cv = statistics.pstdev(vals) / abs(mean) if len(vals) > 1 and mean else 0.0
            reading[key] = round(statistics.median(vals), 2)
            notes = []
            if gaps and max(gaps) > GAP_WARN_MIN:
                notes.append(f"longest gap {max(gaps):.0f} min (possible packet loss)")
            if cv > NOISE_WARN:
                notes.append(f"noisy signal (variation {cv:.0%})")
            quality[key] = {"samples": len(vals), "longest_gap_min": round(max(gaps), 1) if gaps else None,
                            "noise_cv": round(cv, 3), "ok": not notes, "notes": notes}
        return {"astronaut": aid, "day": day, "reading": reading, "quality": quality, "samples": len(rows),
                "late_samples": sum(1 for s in rows if s["late"])}

    def devices(self):
        """Status of every paired device: last seen, samples, today's quality."""
        out = []
        for dev, aid in self.pairing.items():
            mine = [s for s in self.samples.values() if s["device_id"] == dev]
            last = max((s["ts"] for s in mine), default=None)
            today = self.mission_day(self.now())
            out.append({"device_id": dev, "astronaut": aid, "samples": len(mine),
                        "last_seen": last, "minutes_since_last": None if last is None else round((self.now() - last) / 60, 1),
                        "today": self.daily(aid, today) if mine else None})
        return {"devices": out, "rejected_recent": self.rejected[-10:]}
