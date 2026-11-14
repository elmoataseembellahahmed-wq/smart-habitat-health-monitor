# Architecture

```mermaid
flowchart LR
  subgraph Devices["Habitat devices (simulated except the webcam)"]
    W[Typed measurements: pulse, SpO2, temperature, breathing, BP, blood sugar] --- C[Daily check-in: sleep, mood, symptoms]
    CAM[Cabin camera<br/>numbers only] --- V[Optional diary] --- CAB[Cabin CO2 + dosimeter]
  end
  Devices --> Q[1. Quality check<br/>missing / impossible / frozen]
  Q --> I[2. Integrity<br/>band swap, camera time, 2+ faces]
  I --> A[3. Personal-normal analysis<br/>SD + streaks + safety limits]
  A --> F[4. Rules: NORMAL / WATCH / ACT]
  A --> AI[AI double-check<br/>Isolation Forest]
  F --> D[5. Slow-drift anchor<br/>6. Coverage, 7. Crew-wide]
  AI --> D
  D --> R[Report EN / AR<br/>versions + coverage]
  R --> ACC{Access rules}
  ACC --> AST[Astronaut view]
  ACC --> CMD[Commander view]
  ACC --> SUR[Flight surgeon view<br/>+ audit log]
  L[(Learning: days 1-14,<br/>then weekly from NORMAL days)] -.-> A
  L -.-> AI
```

Everything in the diagram runs on one on-board computer with the Python standard library (`run_offline.py`), with no network. The FastAPI backend (`backend/main.py`) has the same API, for development.

| Layer | Code |
|---|---|
| Inputs | `engine/simulate.py` (simulator), `camera/` (real webcam) |
| Quality | `engine/quality.py` |
| Integrity | `engine/integrity.py`, `engine/monitor.py` |
| Analysis | `engine/analysis.py` |
| Rules | `engine/fusion.py` |
| AI | `engine/anomaly.py` |
| Reports | `engine/report.py`, `engine/arabic.py` |
| Access and audit | `engine/access.py` |
| Versions | `engine/version.py` |
| Servers | `run_offline.py`, `backend/main.py` |
| Dashboard | `frontend/` |

Operating concept:
* the **astronaut** opens their own view (What changed, How sure, Do next, When to escalate);
* the **commander** sees the crew's status without private self-report;
* the **flight surgeon** gets the full report at each contact window.

If a sensor fails, the status says so and the report asks for a sensor check. If the whole computer fails, the crew carries on with the normal mission medical procedures: the system is decision support, not a required control.
