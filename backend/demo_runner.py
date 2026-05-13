import time
import json
import random
import requests
import sys
import os

BACKEND_URL = "http://localhost:8000"
DEMO_SPEED_SECONDS = 3
TOTAL_ROUNDS = 20

DEMO_SEQUENCE = [
    {"app": "Maps", "ram": 52, "battery": 85, "cpu": 30},
    {"app": "Spotify", "ram": 55, "battery": 83, "cpu": 25},
    {"app": "Chrome", "ram": 60, "battery": 80, "cpu": 40},
    {"app": "WhatsApp", "ram": 63, "battery": 78, "cpu": 35},
    {"app": "Instagram", "ram": 68, "battery": 75, "cpu": 45},
    {"app": "YouTube", "ram": 72, "battery": 71, "cpu": 55},
    {"app": "Chrome", "ram": 75, "battery": 68, "cpu": 50},
    {"app": "WhatsApp", "ram": 78, "battery": 65, "cpu": 42},
    {"app": "Gmail", "ram": 80, "battery": 62, "cpu": 38},
    {"app": "Chrome", "ram": 82, "battery": 58, "cpu": 60},
    {"app": "Maps", "ram": 79, "battery": 55, "cpu": 44},
    {"app": "Spotify", "ram": 74, "battery": 52, "cpu": 30},
    {"app": "Netflix", "ram": 85, "battery": 48, "cpu": 65},
    {"app": "YouTube", "ram": 88, "battery": 44, "cpu": 70},
    {"app": "Instagram", "ram": 83, "battery": 40, "cpu": 55},
    {"app": "Camera", "ram": 77, "battery": 37, "cpu": 48},
    {"app": "Photos", "ram": 73, "battery": 35, "cpu": 35},
    {"app": "WhatsApp", "ram": 69, "battery": 32, "cpu": 30},
    {"app": "Chrome", "ram": 65, "battery": 30, "cpu": 38},
    {"app": "Gmail", "ram": 60, "battery": 28, "cpu": 32},
]


def check_backend():
    try:
        response = requests.get(BACKEND_URL + "/metrics", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def print_header():
    print("=" * 60)
    print("  RAMWise — Context-Aware Adaptive Memory Management")
    print("  Live Demo Runner")
    print("=" * 60)
    print()


def print_step_divider(step_num, total, app_name):
    print(f"\n{'─' * 60}")
    print(f"  STEP {step_num}/{total} | App: {app_name}")
    print(f"{'─' * 60}")


def send_telemetry(step):
    try:
        payload = {
            "foreground_app": step["app"],
            "ram_usage": step["ram"],
            "cpu_usage": step["cpu"],
            "battery_level": step["battery"],
            "timestamp": int(time.time()),
        }
        response = requests.post(BACKEND_URL + "/telemetry", json=payload, timeout=5)
        if response.status_code in (200, 201):
            print(f"  [TELEMETRY] Sent → App: {step['app']} | RAM: {step['ram']}% | Battery: {step['battery']}% | CPU: {step['cpu']}%")
            return response.json()
        else:
            print(f"  [TELEMETRY] Failed to send (status {response.status_code})")
            return None
    except Exception:
        print("  [TELEMETRY] Error: could not reach backend")
        return None


def fetch_predictions(app_sequence_str):
    try:
        response = requests.get(BACKEND_URL + "/predict?app_sequence=" + app_sequence_str, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  [PREDICTIONS] Method: {data['method']}")
            for i, (app, score) in enumerate(zip(data["predicted_apps"], data["confidence_scores"])):
                bar_length = int(score * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)
                print(f"    {i+1}. {app:<15} [{bar}] {score:.0%}")
        else:
            print("  [PREDICTIONS] Could not fetch")
    except Exception:
        print("  [PREDICTIONS] Could not fetch")


def fetch_allocation(app, ram, battery):
    try:
        response = requests.get(BACKEND_URL + f"/allocate?app={app}&ram_usage={ram}&battery_level={battery}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tier_colors = {"HOT": "🔴", "WARM": "🟠", "COLD": "🔵"}
            tier_icon = tier_colors.get(data["cache_tier"], "⚪")
            print(f"  [RL DECISION] Action: {data['action'].upper()}")
            print(f"  [RL DECISION] Cache Tier: {tier_icon} {data['cache_tier']}")
            print(f"  [RL DECISION] Reason: {data['reason']}")
        else:
            print("  [RL DECISION] Could not fetch")
    except Exception:
        print("  [RL DECISION] Could not fetch")


def fetch_benchmark():
    try:
        response = requests.get(BACKEND_URL + "/benchmark", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\n  {'─'*40}")
            print(f"  BENCHMARK SNAPSHOT")
            print(f"  {'─'*40}")
            print(f"  Launch Latency  | LRU: {data['lru_latency']}s  → RAMWise: {data['ramwise_latency']}s  ({data['latency_improvement_percent']}% faster)")
            print(f"  Cache Hit Rate  | LRU: {data['lru_cache_hit_rate']}  → RAMWise: {data['ramwise_cache_hit_rate']}  ({data['cache_improvement_percent']}% better)")
            print(f"  Thrashing Rate  | LRU: {data['lru_thrashing']}  → RAMWise: {data['ramwise_thrashing']}  ({data['thrashing_improvement_percent']}% reduced)")
        else:
            print("  [BENCHMARK] Could not fetch")
    except Exception:
        print("  [BENCHMARK] Could not fetch")


if __name__ == "__main__":
    print_header()

    print("Checking backend connection...")
    if not check_backend():
        print("ERROR: Cannot connect to backend at localhost:8000")
        print("Start the server first: cd RAMWise/backend && uvicorn api.main:app --reload")
        sys.exit(1)

    print("Backend connected. Starting demo in 3 seconds...")
    time.sleep(3)

    print("Dashboard URL: http://localhost:3000")
    print(f"Running {TOTAL_ROUNDS} demo steps with {DEMO_SPEED_SECONDS}s interval")
    print("Open the dashboard now to see live updates!")
    time.sleep(2)

    for i, step in enumerate(DEMO_SEQUENCE):
        step_num = i + 1
        print_step_divider(step_num, TOTAL_ROUNDS, step["app"])

        send_telemetry(step)

        next_step = DEMO_SEQUENCE[(i + 1) % TOTAL_ROUNDS]
        next_next_step = DEMO_SEQUENCE[(i + 2) % TOTAL_ROUNDS]
        app_seq_str = f"{step['app']},{next_step['app']},{next_next_step['app']}"

        fetch_predictions(app_seq_str)
        fetch_allocation(step["app"], step["ram"], step["battery"])

        if step_num % 5 == 0:
            fetch_benchmark()

        print(f"\n  Waiting {DEMO_SPEED_SECONDS}s before next step...")
        time.sleep(DEMO_SPEED_SECONDS)

    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)
    fetch_benchmark()
    print("\n  RAMWise demo finished. Dashboard remains live.")
    print("  Press Ctrl+C to stop the backend server.")
