# Privacy, security and data governance

## Camera data flow (what actually happens to a frame)

1. `cv2.VideoCapture` gives one frame as an array **in memory**.
2. The face detector and eye detector run on it. The only outputs are: number of faces, eyes open yes/no.
3. `BlinkTracker` keeps **only times and open/closed flags** for the last 60 s, plus daily totals (minutes in view, blinks, microsleeps).
4. The frame variable is overwritten by the next frame. Nothing is written to disk.
5. Once a second the camera sends **numbers only** (blink rate, eye closure %, fatigue score, confidence, the wristband ID) to the on-board server.

This is enforced and tested: `test_camera_never_stores_or_sends_images` checks that no camera code calls an image or video writer (`imwrite`, `VideoWriter`, `imencode`) or opens a binary file for writing, and that every value sent is a number, a yes/no or a short label. The only file the camera writes is the personal blink normal (two numbers) in `camera/baselines/`. The preview window can be switched off with `--no-window`.

## Identity: who is in front of the camera?

* No face recognition. Each camera reading carries the ID of the wristband assigned to that camera position.
* If **two or more faces** are in view, the camera pauses: no measurement is filed under anyone.
* Remaining risk: someone else alone at a camera assigned to another band. Mitigation designed (not built): a short-range proximity handshake between camera and band, and "identity uncertain" when the nearest band is not the assigned one.
* Wristband swaps are caught from the readings themselves (`engine/integrity.py`) and never raise a health alarm.

## Who can see what (enforced by the server)

| Data | Astronaut (own) | Crewmate | Commander | Flight surgeon |
|---|---|---|---|---|
| Status (Normal / Watch / Act) | yes | yes | yes | yes |
| Vital signs, reasons, actions, reports | yes | no | yes | yes |
| Mood and diary words (self-report) | yes | no | **no** (sees that a private signal is off, not its value) | yes |
| History charts | yes | no | yes, except self-report | yes |
| Audit log of who viewed what | no | no | no | yes |

Implemented in `engine/access.py` and used by every status, astronaut, report and chart request (`?role=surgeon|commander|A|B|C`). Test: `test_role_based_access`. **Limitation:** the prototype has no real login; the role is picked in the dashboard. A flight system needs individual log-ins (badge or PIN), so the role cannot be chosen freely.

## Self-report (mood and diary)

* Optional: the astronaut can skip any day; a skipped day is not a fault and not a mood flag.
* Treated as self-report, never as a diagnosis. Word counts are a rough proxy only.
* Private to the astronaut and the flight surgeon (see the table).
* Designed, not built: the astronaut can correct or delete their own entries; an emergency exception (the flight surgeon may share with the commander) is logged.
* Isolation and social connection: designed as an optional private weekly question ("How connected do you feel to the crew and to home?", 1-5), shown to the crew only as a crew-level average. Not built.

## Data inventory and retention (policy for flight use)

| Data | Stored where | Kept for | Who can delete |
|---|---|---|---|
| Daily health values and decisions | On-board computer, local files only | Whole mission, then handed to the medical team under mission rules | Flight surgeon (with log entry) |
| Daily reports | On-board computer | Whole mission | Flight surgeon |
| Diary text | **Not stored** in this design: only the daily mood score and word count are kept | - | Astronaut can delete their entry |
| Camera frames | **Never stored** | - | - |
| Personal camera normal | `camera/baselines/` (two numbers) | Until reset | Astronaut |
| Audit log | Server memory (prototype); a write-once file in the flight design | Whole mission | Nobody (append only) |

## Security (threat model, prototype vs flight design)

| Threat | Prototype | Flight design (not built) |
|---|---|---|
| Someone views another astronaut's data | Role rules on the server | Individual log-in, role from the account, not from the request |
| Fake sensor data injected | Server listens on 127.0.0.1 only (local machine) | Devices paired with keys; every reading signed |
| Data read from a stolen disk | Not protected | Encryption at rest |
| Bad software update changes alerts | Versions recorded on every decision | Signed updates, approval and rollback to the previous rule/model version |
| Data sent off board | Engine makes no network calls (`tools/benchmark.py` blocks all sockets) | Only approved downlink of reports to the flight surgeon |
