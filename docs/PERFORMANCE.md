# Performance, resources and offline operation

Measured with `python tools/benchmark.py` (results in `docs/benchmark_results.json`) on a cloud x86-64 machine, Python 3.13:

| Measure | Result |
|---|---|
| Startup (load engine, read data, quality scan) | 0.4 s |
| Learn the whole 125-day mission once (16 weekly updates × 3 forests) | 7.2 s |
| One mission day, whole crew, AI re-run | median 107 ms, worst 275 ms |
| One daily report | 12 ms |
| Peak memory | about 290 MB (mostly the Isolation Forest trees, kept for every weekly version) |
| Data file for the whole mission | 45 KB |
| Third-party packages needed by the engine | none (Python standard library only) |
| Network used | none |

## Offline proof

`tools/benchmark.py` disables every way to open a network connection (`socket.connect`, `create_connection`, `getaddrinfo`) **before** importing the engine, then runs the full mission and the reports. Any network attempt would crash the run; none happens. `run_offline.py` serves the dashboard with only the standard library, on 127.0.0.1, so it needs no internet and no installs. The dashboard uses no external scripts, fonts or images.

## Restart

The engine is deterministic: after a restart it rebuilds the same decisions from the stored daily data (`data/`), so recent alerts and reports are available again within the startup and learning time above. **Not built:** live readings received since the last save are kept only in memory; a flight version writes each reading to an append-only local file before processing it.

## Limits

* Memory could be cut a lot by keeping only the current and previous weekly models (for rollback) instead of all of them.
* No long-duration soak test (weeks of continuous running) has been done.
* Not measured on a flight-like computer (low-power ARM board), which is the next step.
