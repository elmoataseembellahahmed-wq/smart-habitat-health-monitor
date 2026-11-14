"""FastAPI backend for the Astronaut Health Monitor.

Run from the project folder:
    uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000
"""

from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from engine import HealthMonitor, live, access
from engine.manual import QuickCheck, Upload, template_csv

app = FastAPI(
    title="Astronaut Health Monitor",
    description="On-board decision support: fuses vitals, sleep, camera, voice and cabin data "
                "into a NORMAL / WATCH / ACT state with reasons and a daily report.",
    version="0.1.0",
)

monitor = HealthMonitor()
monitor.status(monitor.days[-1])  # learn every week of the mission once, at startup
quick = QuickCheck(monitor)        # manual test: new days typed in by hand
uploaded = Upload()                # manual test: a whole mission from a CSV file
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def _day(day):
    if day is None:
        return monitor.days[-1]
    if day not in monitor.data["cabin"]:
        raise HTTPException(404, f"No data for day {day}. "
                                 f"Available: {monitor.days[0]}-{monitor.days[-1]}")
    return day


def _role(role):
    if not access.valid_role(role, [m["id"] for m in monitor.crew]):
        raise HTTPException(400, f"Unknown role: {role}")
    return role


ROLE_Q = Query("surgeon", description="surgeon, commander, or an astronaut id (A, B, C)")


def _member(aid):
    try:
        return monitor.member(aid)
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/api/mission")
def mission():
    """Mission length, baseline window, crew and the signal catalogue."""
    return monitor.mission()


@app.get("/api/status")
def status(day: int | None = Query(None, description="Mission day (default: latest)"), role: str = ROLE_Q):
    """State, flags, reasons and actions for the whole crew on one day, as `role` may see them."""
    access.log(_role(role), "all", f"status day {day}")
    return monitor.status(_day(day), role)


@app.get("/api/audit")
def audit(role: str = ROLE_Q):
    """Who looked at what (flight surgeon only)."""
    if _role(role) != "surgeon":
        raise HTTPException(403, "Flight surgeon only")
    return access.audit()


@app.get("/api/astronaut/{aid}")
def astronaut(aid: str, day: int | None = None, role: str = ROLE_Q):
    """Full assessment of one astronaut on one day (as `role` may see it)."""
    m = _member(aid)
    d = _day(day)
    access.log(_role(role), aid, f"astronaut day {d}")
    return access.view({**m, "day": d, **monitor.assess(aid, d), "trend": monitor.trend(aid, d)}, role)


@app.get("/api/report/{aid}", response_class=PlainTextResponse)
def report(aid: str, day: int | None = None,
           lang: str = Query("en", pattern="^(en|ar)$", description="en = English, ar = Arabic"),
           role: str = ROLE_Q):
    """The daily status report as plain text, in English or Arabic."""
    _member(aid)
    access.log(_role(role), aid, f"report day {day} ({lang})")
    return monitor.report(aid, _day(day), lang, role)


@app.get("/api/series/{aid}/{signal}")
def series(aid: str, signal: str, role: str = ROLE_Q):
    """Every value of one signal across the mission, with the personal baseline."""
    _member(aid)
    try:
        return access.series_view(monitor.series(aid, signal), aid, _role(role))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.post("/api/live")
def live_in(reading: dict = Body(...)):
    """Receives readings from camera/live_camera.py (about once a second)."""
    live.store(reading)
    return {"ok": True}


@app.get("/api/live")
def live_out():
    """Latest live camera reading with its state and reasons."""
    return live.latest()


@app.get("/api/manual/defaults")
def manual_defaults(aid: str = "A"):
    """A real normal day of this astronaut, to start the manual form from."""
    try:
        return quick.defaults(aid)
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.post("/api/manual/day")
def manual_day(body: dict = Body(...)):
    """Add the next day with readings typed in by hand, and judge it."""
    try:
        return quick.add(body.get("aid", "A"), body.get("values", {}), body.get("cabin", {}))
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.post("/api/manual/reading")
def manual_reading(body: dict = Body(...)):
    """Another reading (evening, unwell or re-measure) for a day added by hand."""
    try:
        return quick.add_reading(body.get("aid", "A"), int(body["day"]), body["signal"], body["value"],
                                 body.get("kind", "re-measure"), body.get("when"))
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/selfcheck/catalogue")
def selfcheck_catalogue(lang: str = "en"):
    from engine.selfcheck import catalogue
    return catalogue("ar" if lang == "ar" else "en")


@app.post("/api/selfcheck")
def selfcheck(body: dict = Body(...)):
    """Body self-check: the astronaut clicks where it hurts and gets guidance at once."""
    try:
        aid, day = body.get("aid", "A"), int(body.get("day", monitor.days[-1]))
        res = monitor.selfcheck(aid, day, body.get("symptoms", []), body.get("lang", "en"))
        access.log(aid, aid, f"self-check day {day}: {[c['id'] for c in res['cards']]} -> {res['state']}")
        return res
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/tasks/{aid}")
def tasks(aid: str, day: int = Query(None)):
    return monitor.task_board(aid, day or monitor.days[-1])


@app.post("/api/tasks/tick")
def tick(body: dict = Body(...)):
    try:
        aid, day = body.get("aid", "A"), int(body.get("day", monitor.days[-1]))
        access.log(aid, aid, f"task done day {day}: {body['task']}")
        return monitor.tick_task(aid, day, body["task"])
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/earth/{aid}", response_class=PlainTextResponse)
def earth_message(aid: str, day: int = Query(None), lang: str = "en"):
    """A short, prioritised message for the flight surgeon at the next contact window."""
    return monitor.earth_message(aid, day or monitor.days[-1], "ar" if lang == "ar" else "en")


@app.post("/api/manual/reset")
def manual_reset():
    quick.reset()
    return {"ok": True}


@app.get("/api/manual/template.csv")
def manual_template(full: int = 0):
    return Response(template_csv(full=bool(full)), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=mission_template.csv"})


@app.post("/api/manual/upload")
async def manual_upload(request: Request):
    """Upload a whole mission as CSV (see the template) and judge every day."""
    body = await request.body()
    if len(body) > 5_000_000:
        raise HTTPException(413, "File too large (5 MB max)")
    return uploaded.load(body.decode("utf-8-sig"))


@app.get("/api/manual/upload/report/{aid}", response_class=PlainTextResponse)
def manual_upload_report(aid: str, day: int, lang: str = Query("en", pattern="^(en|ar)$")):
    try:
        return uploaded.report(aid, day, lang)
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/manual")
def manual_page():
    return FileResponse(FRONTEND / "manual.html")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
