"""FastAPI backend for the Astronaut Health Monitor.

Run from the project folder:
    uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000
"""

from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from engine import HealthMonitor, live

app = FastAPI(
    title="Astronaut Health Monitor",
    description="On-board decision support: fuses vitals, sleep, camera, voice and cabin data "
                "into a NORMAL / WATCH / ACT state with reasons and a daily report.",
    version="0.1.0",
)

monitor = HealthMonitor()
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def _day(day):
    if day is None:
        return monitor.days[-1]
    if day not in monitor.data["cabin"]:
        raise HTTPException(404, f"No data for day {day}. "
                                 f"Available: {monitor.days[0]}-{monitor.days[-1]}")
    return day


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
def status(day: int | None = Query(None, description="Mission day (default: latest)")):
    """State, flags, reasons and actions for the whole crew on one day."""
    return monitor.status(_day(day))


@app.get("/api/astronaut/{aid}")
def astronaut(aid: str, day: int | None = None):
    """Full assessment of one astronaut on one day."""
    m = _member(aid)
    d = _day(day)
    return {**m, "day": d, **monitor.assess(aid, d), "trend": monitor.trend(aid, d)}


@app.get("/api/report/{aid}", response_class=PlainTextResponse)
def report(aid: str, day: int | None = None,
           lang: str = Query("en", pattern="^(en|ar)$", description="en = English, ar = Arabic")):
    """The daily status report as plain text, in English or Arabic."""
    _member(aid)
    return monitor.report(aid, _day(day), lang)


@app.get("/api/series/{aid}/{signal}")
def series(aid: str, signal: str):
    """Every value of one signal across the mission, with the personal baseline."""
    _member(aid)
    try:
        return monitor.series(aid, signal)
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
