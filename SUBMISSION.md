# Submission texts (NASA Space Apps 2026)

Replace [Team name] and [City, Country]. Check the length limits on the submission page and shorten if needed.

## High-level project summary

Smart Habitat Health Monitor checks an astronaut's health all day without asking them to stop and take tests. On a mission to Mars, a message to Earth can take up to 20 minutes, so the crew must spot health problems themselves. A wristband, a chest strap, a cuffless blood pressure sensor, a glucose patch and cabin cameras collect 11 personal signals during normal work and sleep, plus cabin CO2 and radiation. On-board software compares every reading to that astronaut's own normal, decides on one status (Normal, Watch or Act) with readable rules, and double-checks it with an Isolation Forest anomaly model. The astronaut sees a clickable body figure colored by status, plain-language reasons and what to do, and gets a daily report for the flight surgeon. Cameras identify the wristband, not the face, and never record video. It runs fully offline. The webcam fatigue input is real; the other sensors are simulated because in-flight astronaut data is not public.

## Detailed description

**What it does.** The habitat measures physical and psychological health together, with no scheduled tests. It has four steps: (1) measure: wristband (heart rate, heart rate variability, blood oxygen, temperature, sleep), chest strap (breathing), cuffless blood pressure sensor, glucose patch, cabin cameras (blink rate, eye closure, microsleeps) and cabin sensors (CO2, radiation); (2) compare each signal to the astronaut's personal baseline and to absolute safety limits; (3) decide Normal, Watch or Act with readable rules, double-checked by an Isolation Forest per astronaut; (4) show a clickable body figure, reasons, actions, a short routine and a daily report in English or Arabic.

**Why it matters.** On the way to Mars, real-time telemedicine is impossible, and scheduled tests take crew time. Continuous monitoring during normal activities also removes the effect of knowing you are being tested. Our design choices follow from this: it runs offline, every alert shows its reason, safety limits trigger action at once, and a single bad day never triggers an emergency, which avoids false alarms over months.

**Privacy.** Each wristband tells the nearest camera who is in front of it, so no face recognition is needed. Video is analyzed on the spot and never recorded or sent. Cameras are in work areas only.

**Results on our simulated Mars transit (days 1-125).** The system learns each astronaut's normal in the first 14 days and keeps re-learning it every week from their healthy days. Over 104 healthy days it gives only one single-day Watch and never Act. Ben's slow stress build-up (less sleep, lower HRV, higher blood pressure, breathing and blood sugar) is caught: Watch on day 120 and Act on day 121, with the AI model flagging him from day 120 and more strongly as he declines. Chen's single bad night gives Watch, then Normal, with no false emergency. When the CO2 scrubber degrades, the whole crew is flagged and the report warns that fatigue may come from the air. In the story days (100-125) the AI model and the rules agree on 71 of 78 crew-days, and the AI never flags the healthy astronaut.

**Tools.** Python, FastAPI (plus a standard-library backup server), OpenCV for the cabin camera, a plain-JavaScript dashboard that works offline, and an Isolation Forest written in plain Python.

**Limits.** Almost test-free: blood pressure sensors need a weekly cuff check and glucose patches are changed every 10-14 days. Most data is simulated. Thresholds are starting values, not clinically validated. It is decision support; the flight surgeon makes medical decisions.

## Video script (about 2 minutes)

| Time | On screen | Voice-over |
|---|---|---|
| 0:00-0:15 | Title slide | On the way to Mars, a message to Earth can take up to 20 minutes. A crew can't wait for a doctor, and tests take time. We built a habitat that checks health with no tests. |
| 0:15-0:35 | Devices slide | A wristband, a chest strap, a blood pressure sensor, a glucose patch and cabin cameras measure health during normal work and sleep. |
| 0:35-0:50 | Privacy slide | The wristband tells each camera who is in front of it. No face recognition, no video stored. |
| 0:50-1:10 | Live camera, then the dashboard camera panel | This is real: the camera measures my blinking and eye closure. When I get drowsy, the status changes and it says why. |
| 1:10-1:35 | Dashboard, press Play from day 114 | In our simulated Mars transit, Ben's stress builds slowly. The system moves him to Watch, then Act, days early. Chen has one bad night: Watch, then Normal. |
| 1:35-1:50 | Click the heart on the body figure | Click any body part to see the readings, what space does to it, and what to do. |
| 1:50-2:00 | Thank-you slide | No tests, offline, explainable and private. Smart Habitat Health Monitor, by team [Team name]. |

## Demo checklist (before judging)

1. Start the server: `python run_offline.py` (or ▶ on `run_offline.py` in VS Code).
2. Open http://127.0.0.1:8000.
3. Start the camera in a second terminal: `python camera/live_camera.py --band B`. Look at the screen for about a minute the first time.
4. If the webcam or lighting fails: `python camera/demo_camera.py --band B`.
5. Press Play from day 114. Click Ben, then the heart on the body figure. Switch the report to Arabic.
