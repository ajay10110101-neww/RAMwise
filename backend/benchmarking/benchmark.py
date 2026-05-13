import sys
import os
import json
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cache_simulator.cache import AdaptiveCache, LRUCache

TRACE_1 = ["Maps", "Spotify", "Chrome", "WhatsApp", "Instagram", "YouTube", "Chrome", "WhatsApp", "Maps", "Spotify", "Chrome", "Instagram"]
TRACE_2 = ["Gmail", "Chrome", "Calendar", "WhatsApp", "Gmail", "Chrome", "Instagram", "WhatsApp", "Calendar", "Chrome", "Gmail", "Maps"]
TRACE_3 = ["YouTube", "Netflix", "Spotify", "YouTube", "Instagram", "Chrome", "Netflix", "Spotify", "YouTube", "Chrome", "Instagram", "WhatsApp"]
TRACE_4 = ["Camera", "Photos", "Instagram", "WhatsApp", "Camera", "Photos", "Chrome", "Instagram", "WhatsApp", "Camera", "Maps", "Chrome"]
TRACE_5 = ["Chrome", "WhatsApp", "Instagram", "Chrome", "YouTube", "Spotify", "Chrome", "WhatsApp", "Gmail", "Chrome", "Instagram", "Maps"]

ALL_TRACES = [TRACE_1, TRACE_2, TRACE_3, TRACE_4, TRACE_5]

PREDICTION_MAP = {
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


def run_ramwise_on_trace(trace, ram_usage=0.65, battery_level=0.70):
    cache = AdaptiveCache()
    latencies = []
    for i, app in enumerate(trace):
        if i > 0:
            previous_app = trace[i - 1]
            predicted = PREDICTION_MAP.get(previous_app, ["Chrome"])[0]
            cache.preload(predicted, battery_level=battery_level)
        result = cache.access(app, ram_usage=ram_usage, battery_level=battery_level)
        latencies.append(result["latency"])
    return {
        "stats": cache.get_stats(),
        "avg_latency": round(sum(latencies) / len(latencies), 4),
        "latencies": latencies,
    }


def run_lru_on_trace(trace):
    cache = LRUCache()
    latencies = []
    for app in trace:
        result = cache.access(app)
        latencies.append(result["latency"])
    return {
        "stats": cache.get_stats(),
        "avg_latency": round(sum(latencies) / len(latencies), 4),
        "latencies": latencies,
    }


def compute_thrashing_rate(latencies):
    if len(latencies) <= 1:
        return 0.0
    thrashing = 0
    for i in range(1, len(latencies)):
        if abs(latencies[i] - latencies[i - 1]) > 1.0:
            thrashing += 1
    return round(thrashing / (len(latencies) - 1), 4)


def run_full_benchmark():
    ramwise_latencies_all = []
    lru_latencies_all = []
    ramwise_hit_rates = []
    lru_hit_rates = []
    ramwise_thrashing_rates = []
    lru_thrashing_rates = []

    for trace in ALL_TRACES:
        ramwise_result = run_ramwise_on_trace(trace)
        lru_result = run_lru_on_trace(trace)

        ramwise_latencies_all.append(ramwise_result["avg_latency"])
        lru_latencies_all.append(lru_result["avg_latency"])

        ramwise_hit_rates.append(ramwise_result["stats"]["hit_rate"])
        lru_hit_rates.append(lru_result["stats"]["hit_rate"])

        ramwise_thrashing_rates.append(compute_thrashing_rate(ramwise_result["latencies"]))
        lru_thrashing_rates.append(compute_thrashing_rate(lru_result["latencies"]))

    ramwise_avg_latency = round(sum(ramwise_latencies_all) / 5, 4)
    lru_avg_latency = round(sum(lru_latencies_all) / 5, 4)
    ramwise_avg_hit_rate = round(sum(ramwise_hit_rates) / 5, 4)
    lru_avg_hit_rate = round(sum(lru_hit_rates) / 5, 4)
    ramwise_avg_thrashing = round(sum(ramwise_thrashing_rates) / 5, 4)
    lru_avg_thrashing = round(sum(lru_thrashing_rates) / 5, 4)

    latency_improvement = round(((lru_avg_latency - ramwise_avg_latency) / lru_avg_latency) * 100, 2)
    hit_rate_improvement = round(((ramwise_avg_hit_rate - lru_avg_hit_rate) / lru_avg_hit_rate) * 100, 2)
    thrashing_improvement = round(((lru_avg_thrashing - ramwise_avg_thrashing) / max(lru_avg_thrashing, 0.001)) * 100, 2)

    return {
        "lru": {
            "avg_latency": lru_avg_latency,
            "avg_hit_rate": lru_avg_hit_rate,
            "avg_thrashing": lru_avg_thrashing,
        },
        "ramwise": {
            "avg_latency": ramwise_avg_latency,
            "avg_hit_rate": ramwise_avg_hit_rate,
            "avg_thrashing": ramwise_avg_thrashing,
        },
        "improvements": {
            "latency_improvement_percent": latency_improvement,
            "hit_rate_improvement_percent": hit_rate_improvement,
            "thrashing_improvement_percent": thrashing_improvement,
        },
        "kpi_targets_met": {
            "latency_20_percent": latency_improvement >= 20.0,
            "hit_rate_85_percent": ramwise_avg_hit_rate >= 0.85,
            "thrashing_50_percent": thrashing_improvement >= 50.0,
        },
    }


if __name__ == "__main__":
    print("Running RAMWise vs LRU Benchmark...")
    results = run_full_benchmark()

    lru = results["lru"]
    ramwise = results["ramwise"]
    imp = results["improvements"]
    kpi = results["kpi_targets_met"]

    print("=" * 50)
    print("BENCHMARK RESULTS: LRU vs RAMWise")
    print("=" * 50)
    print(f"Avg Launch Latency   | LRU: {lru['avg_latency']}s | RAMWise: {ramwise['avg_latency']}s")
    print(f"Avg Cache Hit Rate   | LRU: {lru['avg_hit_rate']}  | RAMWise: {ramwise['avg_hit_rate']}")
    print(f"Avg Thrashing Rate   | LRU: {lru['avg_thrashing']} | RAMWise: {ramwise['avg_thrashing']}")
    print("=" * 50)
    print(f"Latency Improvement  : {imp['latency_improvement_percent']}%")
    print(f"Hit Rate Improvement : {imp['hit_rate_improvement_percent']}%")
    print(f"Thrashing Reduction  : {imp['thrashing_improvement_percent']}%")
    print("=" * 50)
    print(f"KPI - Latency >= 20%    : {'PASS' if kpi['latency_20_percent'] else 'FAIL'}")
    print(f"KPI - Hit Rate >= 85%   : {'PASS' if kpi['hit_rate_85_percent'] else 'FAIL'}")
    print(f"KPI - Thrashing >= 50%  : {'PASS' if kpi['thrashing_50_percent'] else 'FAIL'}")
    print("=" * 50)

    save_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(save_path, "w") as f:
        json.dump(results, f, indent=2)
    print("Benchmark complete. Results saved to benchmark_results.json")
