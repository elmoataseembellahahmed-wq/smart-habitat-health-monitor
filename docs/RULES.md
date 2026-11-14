# Rule catalogue and decision flow

Version `rules-r4`. Every rule below is in the code, and every rule that fires is listed in the report with its reason.

## Decision flow (one astronaut, one day)

```
readings
  -> 1. quality check      missing / impossible / frozen -> "unavailable" + sensor check (no health meaning)
  -> 2. integrity checks   profile mix-up -> typed values set aside + "check your profile" (no health alarm)
                           camera < 30 min -> fatigue and blink "not measured" (said plainly)
  -> 3. per-signal check   distance from the personal normal (SD), days in a row, absolute safety limits
  -> 4. fusion             points -> score; risk patterns; NORMAL / WATCH / ACT
  -> 5. slow drift         current normal far from the day 1-14 anchor -> at least WATCH + flight-surgeon review
  -> 6. AI double-check    Isolation Forest: agrees / AI only / rules only (never changes the state)
  -> 7. coverage           "status based on N of 13 signals", confidence full / limited / low
  -> 8. crew-wide          shared change + cabin fault = environmental; shared change without a cabin cause = individual
  -> report                observation (what and why) kept apart from suggested actions (what to do)
```

## Hard safety rules (kept apart from the score)

| Rule | Effect |
|---|---|
| A signal beyond its absolute safety limit (SpO2 < 92, BP > 180/120, glucose < 54 or > 250) | ACT at once, whatever the score |
| Wrist skin temperature above 38 °C | Strong flag + "possible fever" pattern (WATCH): confirm with a core thermometer first, because it is an estimate |
| Cabin CO2 at or above 4.0 mmHg | ACT for every crew member |

## Score rules

| Rule | Effect |
|---|---|
| Mild flag 1 point, strong 2, safety limit 5; +1 if the flag has lasted 3+ days | Adds to the score |
| Score 8+ **and** a signal off 2+ days | ACT |
| Score 8+ on one day only | WATCH ("ACT if it continues tomorrow") |
| Score 3+ | WATCH |
| Combined physical and mental stress (heart + sleep + mind signals) for 3+ days | ACT |

## Risk patterns (each gives at least WATCH)

| Pattern | Condition |
|---|---|
| Low oxygen | SpO2 strong or below the limit |
| Cabin air | CO2 above its WATCH limit |
| Possible fever | wrist temperature strong or above the limit |
| Raised blood pressure | flagged 2+ days, or above the limit |
| Blood sugar out of range | flagged 2+ days, or beyond a limit |
| Combined stress | heart + sleep + mind signals off together |
| Sleep debt | sleep flagged 2+ days |
| Mental strain | mood and stress words both off, or one of them 2+ days |

## Missing, invalid and conflicting data

| Situation | Behaviour |
|---|---|
| Reading missing, impossible or frozen | Not scored, not learned, AI gets a neutral value; "sensor check" with a device action; coverage drops |
| A safety-limit signal is unavailable | Coverage says "Normal cannot rule out a problem in it" |
| Diary skipped | Not a fault, not a mood flag; noted in the report |
| Profile mix-up | All typed measurements set aside for the day, both astronauts asked to check and re-enter |
| Camera saw the face < 30 min | Fatigue and blink rate "not measured" (said in the report); typed values still count |
| Two faces in front of a camera | Camera pauses until one face remains |
| Rules and AI disagree | Both shown; the state follows the rules, the note says which one flagged |

## Escalation and de-escalation

* The state is recomputed each day from that day's readings and the streaks behind them. **There is no hidden memory**: a signal that returns to normal stops counting at once, so WATCH clears to NORMAL the next normal day (see Chen, day 122).
* ACT always adds "send this report to the flight surgeon at the next contact window".
* Planned, not implemented: the astronaut acknowledges an alert; a repeated alert is grouped instead of shown again; recovery requires 2 normal days before an ACT clears.

## Action policy

The system **observes and suggests**; it does not diagnose or treat. Every action has a type, shown in the dashboard and reports:

| Type | Meaning | Example |
|---|---|---|
| confirm first | Re-measure with a reference device before believing a reading | finger-prick glucose, cuff blood pressure, oral thermometer |
| equipment | Fix or check hardware | service the CO2 scrubber, check the webcam |
| self-care | Low-risk routine steps the crew already do | protect tonight's sleep, take a break |
| escalate | Tell a person with authority | flight surgeon, flight psychologist, commander |

The action texts are a **prototype list**. For flight use each one must be replaced by, or linked to, a mission-approved procedure and reviewed by a flight surgeon. No action gives a drug, a dose or a treatment.
