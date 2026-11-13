# Smart Habitat Health Monitor

NASA Space Apps Challenge 2026: *Create Health Monitoring Software for Astronauts on Space Missions*

A smart habitat that checks each astronaut's health **all day, without tests**. A wristband,
a few small body sensors and cabin cameras collect vital signs during normal work and sleep.
On-board software compares every reading to that astronaut's **own** normal, decides on one
status (**NORMAL / WATCH / ACT**), double-checks with an **AI anomaly model**, and shows the
astronaut what is happening, why, and what to do: on a **clickable body figure** and in a
daily report (English or Arabic). It runs fully offline, because a message from Mars can take
up to 20 minutes to reach Earth.

## Run it
You need Python 3.10 or newer.

**1. Start the server** (pick one)
```bash
python run_offline.py                 # nothing to install (good backup at the venue)
# or
pip install -r requirements.txt
uvicorn backend.main:app --reload     # FastAPI version, API docs at /docs
```
Open http://127.0.0.1:8000 and press **Play**. Keep this terminal open.

**2. Cabin camera (optional, in a second terminal)**
```bash
pip install opencv-python
python camera/live_camera.py --band B
```
`--band` is the wristband nearest the camera (A = Amira, B = Ben, C = Chen). The first time a
band is used, the camera learns that person's normal blinking over 60 seconds of face time and
saves it in `camera/baselines/`; later sessions start measuring at once (`--reset-baseline` to
learn again). The first run downloads OpenCV's face and eye detector files once (needs
internet). Other options: `--camera 1`, `--calibrate 30`, `--no-window`, `--server URL`.
Press `q` in the camera window to stop.

**3. Backup demo camera (no webcam needed)**
```bash
python camera/demo_camera.py --band B
```
Plays an "astronaut getting tired" sequence (alert, then tired, then microsleeps) into the
dashboard, using the same measuring code as the real camera. The dashboard labels it
"demo camera, simulated". Use it if the webcam or the lighting fails at the venue.

**Tests**
```bash
python tests/test_scenario.py         # or: python -m pytest tests
```

## Habitat devices (no tests needed)

| Device | Measures | How often |
|---|---|---|
| Wristband | Heart rate, HRV, blood oxygen, temperature, sleep; also the astronaut's ID | Continuous |
| Chest strap | Breathing rate | Continuous |
| Cuffless blood pressure sensor | Blood pressure | Several times a day (weekly cuff check) |
| Glucose patch | Blood sugar | Every few minutes (patch changed every 10-14 days) |
| Cabin cameras (work areas) | Blinks, eye closure, microsleeps | All day, when a face is in view |
| Voice and daily log (optional) | Mood, stress words | Daily |
| Cabin sensors | CO2, radiation | Continuous |

**Identification and privacy:** the wristband, not the face, tells each camera who is in front
of it (in a real habitat, by its short-range ultra-wideband radio position). No face
recognition, no video recorded or sent: only numbers leave the camera. Cameras are in work
areas only.

## How it works (4 layers)

| Layer | File | What it does |
|---|---|---|
| 1. Inputs | `engine/simulate.py`, `engine/signals.py`, `camera/` | 13 personal signals from 6 devices, plus cabin CO2 and radiation. The webcam is real; the rest are simulated |
| 2. Per-signal analysis | `engine/analysis.py` | Personal normal learned on days 1-14, then re-learned every 7 days from the last 30 days the astronaut was NORMAL. Flags a value 2.5+ SD (mild) or 3.5+ SD (strong) away in the unhealthy direction, counts days in a row, and checks absolute safety limits |
| 3a. Decision (rules) | `engine/fusion.py` | Readable rules turn flags into a score and risk patterns, then NORMAL / WATCH / ACT, and list which rules fired |
| 3b. AI double-check | `engine/anomaly.py` | Isolation Forest per astronaut, trained on their normal days, looking at all signals together |
| 4. Output | `engine/monitor.py`, `engine/reminders.py`, `engine/report.py`, `engine/arabic.py`, `frontend/` | Body-system status, routine reminders, dashboard, daily report in English or Arabic |

### Safety limits (checked whatever the personal normal)
| Signal | Limit |
|---|---|
| Blood oxygen | below 92% |
| Blood sugar | below 54 or above 250 mg/dL |
| Blood pressure | systolic above 180 or diastolic above 120 mmHg |
| Body temperature | above 38.0 °C |

### Decision rules
- Points: mild flag = 1, strong = 2, safety limit broken = 5, +1 if it lasts 3+ days.
- **ACT** if a safety limit is broken, or the score is 8+ **and** a signal has been off for 2+ days, or combined physical and mental stress lasts 3+ days, or cabin CO2 is above 4.0 mmHg.
- **WATCH** if the score is 3+, or a risk pattern is found: low oxygen (a strong drop), cabin air, possible fever, raised blood pressure, blood sugar out of range, combined stress, sleep debt, mental strain.
- A single bad day can reach WATCH but never ACT. This avoids false alarms.

### AI anomaly model (Isolation Forest)
- One forest of 200 trees per astronaut, written in plain Python (no scikit-learn needed).
- Trained on 500 plausible normal days made by resampling that astronaut's real normal days (the first 14 days, then up to 30 recent NORMAL days, re-trained every week) with small noise.
- A day is *unusual* when its score is 0.09 above the most unusual baseline day, and *strong* 0.08 above that.
- In the story days (100-125) it agrees with the rules on 71 of 78 crew-days, flags Ben from day 120 (more strongly as he declines), and never flags Amira. Over the 104 healthy days before, it raises only 3 single-day "unusual" notes and never an alarm.

### Cabin camera, all-day mode
- OpenCV finds the face, then looks for open eyes in its upper half. The eye detector doesn't find closed eyes, so "face but no eyes" means eyes closed.
- `camera/blink_tracker.py` measures **blink rate**, **PERCLOS** (share of time the eyes are closed) and **long closures** (0.5 s or more, possible microsleep) over the last minute, for instant alerts.
- It also keeps a **daily summary**: minutes in view, eye closure today, microsleeps today and the most tired hour.
- When nobody faces the camera, it simply measures nothing. Calibration counts only face time.
- Smoothing: a closure only counts once it lasts 2 frames, so a single missed detection is not a fake blink.
- `engine/live.py` compares readings with the saved personal normal: WATCH if blinking or eye closure rises, ACT for 2+ long closures in a minute.

## The demo story (mission days 1-125)
- **Days 1-14**: the system learns each astronaut's personal normal. After that it keeps learning: every 7 days it updates the normal from the last 30 days the astronaut was NORMAL, so slow changes in space are followed, but bad days are never learned as "normal".
- **Days 15-118**: everyone is healthy. Over these 104 days the system gives one single-day WATCH (Amira, day 48) and no ACT.
- **Amira**: healthy throughout. The system stays quiet.
- **Ben**: slow stress build-up from day 119: sleep drops, HRV falls, blood pressure, breathing and blood sugar rise, mood falls. WATCH on day 120, ACT from day 121. The AI model flags him from day 120, and its alert grows stronger as he declines.
- **Chen**: one bad night on day 121 gives WATCH, then NORMAL again. No false emergency.
- **Cabin**: the CO2 scrubber degrades on days 123-125. Everyone breathes a little faster, and the whole crew goes to WATCH and then ACT. The report warns that fatigue may be caused by CO2, not only by stress.

## Dashboard
- **Play** runs the mission day by day (quiet weeks fast, the story days from day 115 slowly); click a crew card for details. Drag the day slider to jump to any day 1-125.
- **Body figure**: each body system (brain and mind, heart, lungs, metabolism, immune system, bones and muscles) is colored by status. Click one to see what it does, how space affects it, the spaceflight hazards behind it, today's readings and what to do. Bones and muscles show "no daily sensor" with exercise guidance.
- **Cabin camera panel**: live readings filed under the wristband ID, plus today's fatigue summary.
- **Habitat sensors**: every device, what it measures and whether it is live or simulated.
- **Routine**: the few things the habitat still needs from the crew: a weekly blood pressure cuff check, a glucose patch change every 14 days, and the daily exercise session, plus the streak of days in Normal.
- Daily report: **English / عربي**, **Copy**, and **Save as PDF**.

## API
| Endpoint | Returns |
|---|---|
| `GET /api/mission` | Mission days, crew, signals, devices, body systems |
| `GET /api/status?day=N` | Whole crew: state, flags with reasons, patterns, rules, AI result, body systems, actions, trend |
| `GET /api/astronaut/{id}?day=N` | One astronaut in full |
| `GET /api/report/{id}?day=N&lang=en\|ar` | Daily report (plain text) |
| `GET /api/series/{id}/{signal}` | All values of one signal plus the personal baseline |
| `POST /api/live` | Cabin camera reading with its wristband ID (sent by `camera/live_camera.py`) |
| `GET /api/live` | Latest reading per wristband with its state and reasons |

## Honest limits (say these in the pitch)
- **Not fully test-free:** cuffless blood pressure needs a regular cuff check, and the glucose patch is changed every 10-14 days.
- **Most data is simulated.** Day-by-day in-flight astronaut data is not public. The webcam input is real.
- Wrist temperature is an estimate of body temperature.
- Thresholds are starting values, not clinically validated.
- The camera needs a visible face and steady light. Spacecraft lighting is controlled, which helps.
- This is decision support. The flight surgeon makes medical decisions.

## License
MIT. See [LICENSE](LICENSE).
