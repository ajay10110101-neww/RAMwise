from pydantic import BaseModel, Field


class TelemetryInput(BaseModel):
    foreground_app: str
    ram_usage: int = Field(ge=0, le=100)
    cpu_usage: int = Field(ge=0, le=100)
    battery_level: int = Field(ge=0, le=100)
    timestamp: int


class TelemetryResponse(BaseModel):
    success: bool
    message: str
    id: int


class PredictionResponse(BaseModel):
    predicted_apps: list[str]
    confidence_scores: list[float]
    method: str


class AllocationResponse(BaseModel):
    action: str
    target_app: str
    cache_tier: str
    reason: str


class MetricsResponse(BaseModel):
    total_telemetry_records: int
    average_ram_usage: float
    average_battery_level: float
    average_cpu_usage: float
    cache_hit_rate: float
    last_updated: str


class BenchmarkResponse(BaseModel):
    lru_latency: float
    ramwise_latency: float
    lru_cache_hit_rate: float
    ramwise_cache_hit_rate: float
    lru_thrashing: float
    ramwise_thrashing: float
    latency_improvement_percent: float
    cache_improvement_percent: float
    thrashing_improvement_percent: float
