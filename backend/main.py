"""FastAPI backend for the Astronaut Health Monitor.

Run from the project folder:
    uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000
"""

from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from engine import HealthMonitor, live, access

app = FastAPI(
    title="Astronaut Health Monitor",
    description="On-board decision support: fuses vitals, sleep, camera, voice and cabin data "
                "into a NORMAL / WATCH / ACT state with reasons and a daily report.",
    version="0.1.0",
)

monitor = HealthMonitor()
monitor.status(monitor.days[-1])  # learn every week of the mission once, at startup
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


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
