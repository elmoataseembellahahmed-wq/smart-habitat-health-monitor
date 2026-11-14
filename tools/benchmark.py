"""Performance, resource and offline check.

Measures startup time, time to process one mission day for the whole crew, memory, and
the size of the data, and proves the engine runs with no network: before importing
it, every way to open a network connection is blocked, so any attempt would crash.

Run:  python tools/benchmark.py
"""

import json
import platform
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _no_network(*args, **kwargs):
    raise RuntimeError("Network access attempted, but the system must run fully offline.")


def main():
    socket.socket.connect = _no_network          # block every outgoing connection
    socket.create_connection = _no_network
    socket.getaddrinfo = _no_network

    t0 = time.perf_counter()
    from engine import HealthMonitor
    import engine
    m = HealthMonitor()
    t_init = time.perf_counter() - t0

    t1 = time.perf_counter()
    m.status(m.days[-1])                         # learns every week of the mission once
    t_learn = time.perf_counter() - t1

    per_day = []
    for d in m.days:
        m._ai_cache.clear()                      # force the AI check to run again
        t = time.perf_counter()
        m.status(d)
        per_day.append(time.perf_counter() - t)
    try:
        import resource                          # Linux / macOS
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_mb = rss / 1e6 if sys.platform == "darwin" else rss / 1024
    except ImportError:                          # Windows
        peak_mb = None

    t2 = time.perf_counter()
    for aid in "ABC":
        m.report(aid, m.days[-1]), m.report(aid, m.days[-1], "ar")
    t_report = (time.perf_counter() - t2) / 6

    third_party = sorted({name.split(".")[0] for name in sys.modules
                          if name.split(".")[0] in ("numpy", "sklearn", "pandas", "cv2", "fastapi", "requests")})
    res = {
        "machine": f"{platform.processor() or platform.machine()}, Python {platform.python_version()}",
        "startup_seconds": round(t_init, 2),
        "learn_whole_mission_seconds": round(t_learn, 2),
        "per_mission_day_whole_crew_ms": {"median": round(sorted(per_day)[len(per_day) // 2] * 1000, 1),
                                          "max": round(max(per_day) * 1000, 1)},
        "report_ms": round(t_report * 1000, 1),
        "peak_memory_mb": None if peak_mb is None else round(peak_mb, 1),
        "data_file_kb": round((ROOT / "data" / "simulated_mission_data.csv").stat().st_size / 1024, 1),
        "network_used": False,
        "third_party_packages_needed_by_engine": third_party or "none (Python standard library only)",
        "engine_files": len(list(Path(engine.__file__).parent.glob("*.py"))),
    }
    out = ROOT / "docs" / "benchmark_results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
