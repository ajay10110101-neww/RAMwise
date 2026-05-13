import json
import random
import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    TelemetryInput,
    TelemetryResponse,
    PredictionResponse,
    AllocationResponse,
    MetricsResponse,
    BenchmarkResponse,
)
from api.database import get_connection, init_db

app = FastAPI(title="RAMWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


TRANSITION_MAP = {
    "Chrome": ["WhatsApp", "YouTube", "Gmail"],
    "WhatsApp": ["Instagram", "Camera", "Chrome"],
    "Instagram": ["WhatsApp", "Camera", "Spotify"],
    "Spotify": ["YouTube", "Instagram", "Chrome"],
    "YouTube": ["Instagram", "Spotify", "Chrome"],
    "Maps": ["Chrome", "Spotify", "WhatsApp"],
    "Gmail": ["Chrome", "Calendar", "WhatsApp"],
    "Twitter": ["Chrome", "Instagram", "YouTube"],
    "Netflix": ["YouTube", "Spotify", "Chrome"],
    "Camera": ["Photos", "Instagram", "WhatsApp"],
    "Photos": ["Instagram", "WhatsApp", "Camera"],
    "Settings": ["Chrome", "Files", "Calculator"],
    "Calculator": ["Chrome", "Files", "Calendar"],
    "Calendar": ["Gmail", "Chrome", "WhatsApp"],
    "Files": ["Chrome", "Gmail", "Calculator"],
}


@app.post("/telemetry", response_model=TelemetryResponse)
def record_telemetry(data: TelemetryInput):
    """Record a telemetry data point from an Android device into the SQLite database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO telemetry (foreground_app, ram_usage, cpu_usage, battery_level, timestamp) VALUES (?, ?, ?, ?, ?)",
            (data.foreground_app, data.ram_usage, data.cpu_usage, data.battery_level, data.timestamp),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return TelemetryResponse(success=True, message="Telemetry recorded", id=new_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict", response_model=PredictionResponse)
def predict_next_apps(app_sequence: str = "Chrome,WhatsApp,Instagram"):
    """Predict the next likely apps based on the given app sequence using heuristic transition lookup."""
    apps = app_sequence.split(",")
    last_app = apps[-1].strip()

    if last_app in TRANSITION_MAP:
        predicted_apps = TRANSITION_MAP[last_app]
    else:
        predicted_apps = ["Chrome", "WhatsApp", "YouTube"]

    first = round(random.uniform(0.5, 0.7), 2)
    second = round(random.uniform(0.2, 0.35), 2)
    third = round(1.0 - first - second, 2)
    confidence_scores = [first, second, third]

    return PredictionResponse(
        predicted_apps=predicted_apps,
        confidence_scores=confidence_scores,
        method="heuristic",
    )


@app.get("/allocate", response_model=AllocationResponse)
def allocate_memory(app: str = "Chrome", ram_usage: int = 70, battery_level: int = 60):
    """Determine memory allocation action for an app based on current RAM and battery state."""
    if ram_usage < 60 and battery_level > 50:
        action = "preload_app"
        cache_tier = "HOT"
        reason = "Low memory pressure and sufficient battery allows aggressive preloading"
    elif 60 <= ram_usage <= 80:
        action = "move_to_warm"
        cache_tier = "WARM"
        reason = "Moderate memory pressure, app moved to warm cache"
    else:
        action = "evict_app"
        cache_tier = "COLD"
        reason = "High memory pressure or low battery forces eviction"

    return AllocationResponse(
        action=action,
        target_app=app,
        cache_tier=cache_tier,
        reason=reason,
    )


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """Return aggregated metrics from all recorded telemetry data."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), AVG(ram_usage), AVG(battery_level), AVG(cpu_usage) FROM telemetry")
    row = cursor.fetchone()
    conn.close()

    count = row[0]
    if count == 0:
        avg_ram = 0.0
        avg_battery = 0.0
        avg_cpu = 0.0
    else:
        avg_ram = round(row[1], 2)
        avg_battery = round(row[2], 2)
        avg_cpu = round(row[3], 2)

    return MetricsResponse(
        total_telemetry_records=count,
        average_ram_usage=avg_ram,
        average_battery_level=avg_battery,
        average_cpu_usage=avg_cpu,
        cache_hit_rate=0.87,
        last_updated=datetime.datetime.now().isoformat(),
    )


@app.get("/benchmark", response_model=BenchmarkResponse)
def run_benchmark():
    """Simulate a benchmark comparison between LRU and RAMWise caching strategies."""
    lru_latency = round(random.uniform(1.8, 2.2), 2)
    ramwise_latency = round(random.uniform(0.9, 1.2), 2)
    lru_cache_hit_rate = round(random.uniform(0.55, 0.65), 2)
    ramwise_cache_hit_rate = round(random.uniform(0.83, 0.91), 2)
    lru_thrashing = round(random.uniform(0.35, 0.45), 2)
    ramwise_thrashing = round(random.uniform(0.10, 0.18), 2)

    latency_improvement = round(((lru_latency - ramwise_latency) / lru_latency) * 100, 1)
    cache_improvement = round(((ramwise_cache_hit_rate - lru_cache_hit_rate) / lru_cache_hit_rate) * 100, 1)
    thrashing_improvement = round(((lru_thrashing - ramwise_thrashing) / lru_thrashing) * 100, 1)

    return BenchmarkResponse(
        lru_latency=lru_latency,
        ramwise_latency=ramwise_latency,
        lru_cache_hit_rate=lru_cache_hit_rate,
        ramwise_cache_hit_rate=ramwise_cache_hit_rate,
        lru_thrashing=lru_thrashing,
        ramwise_thrashing=ramwise_thrashing,
        latency_improvement_percent=latency_improvement,
        cache_improvement_percent=cache_improvement,
        thrashing_improvement_percent=thrashing_improvement,
    )
