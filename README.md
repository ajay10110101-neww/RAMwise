# RAMWise — Context-Aware Adaptive Memory Management

RAMWise is an intelligent memory management system for Android that uses a Transformer model for app usage prediction and a PPO (Proximal Policy Optimization) reinforcement learning agent for adaptive cache allocation. It replaces traditional LRU caching with a three-tier HOT/WARM/COLD adaptive cache strategy.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Android Client  │────▶│   FastAPI Backend  │◀────│  React Dashboard │
│  (Kotlin)        │     │   (Python)         │     │  (TypeScript)    │
│                  │     │                    │     │                  │
│ • RAM monitoring │     │ • Transformer API  │     │ • Live charts    │
│ • Battery level  │     │ • PPO RL allocator │     │ • Cache tiers    │
│ • CPU usage      │     │ • SQLite storage   │     │ • Predictions    │
│ • App detection  │     │ • Benchmark engine │     │ • RL decisions   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Project Structure

```
RAMWise/
├── backend/
│   ├── api/
│   │   ├── main.py            # FastAPI app with 5 endpoints
│   │   ├── schemas.py         # Pydantic models
│   │   └── database.py        # SQLite setup
│   ├── transformer/
│   │   ├── model.py           # AppTransformer (PyTorch)
│   │   └── train.py           # Transformer training script
│   ├── rl_allocator/
│   │   ├── memory_env.py      # Custom Gymnasium environment
│   │   └── train_rl.py        # PPO training script
│   ├── cache_simulator/
│   │   └── cache.py           # AdaptiveCache + LRUCache
│   ├── benchmarking/
│   │   └── benchmark.py       # LRU vs RAMWise benchmark
│   ├── datasets/
│   │   ├── generate_dataset.py
│   │   └── preprocess.py
│   ├── demo_runner.py         # Live demo script
│   └── requirements.txt
├── dashboard/
│   └── src/
│       ├── api.ts             # API client (axios)
│       ├── App.tsx            # Dashboard UI (Recharts)
│       └── index.tsx          # Entry point
├── android-client/
│   └── app/src/main/
│       ├── AndroidManifest.xml
│       └── java/com/ramwise/telemetry/
│           ├── MainActivity.kt
│           └── TelemetryService.kt
├── models/                    # Trained weights (gitignored)
│   ├── transformer_weights/
│   └── rl_models/
├── start.sh                   # Start backend + frontend
└── .gitignore
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) Android Studio for the mobile client

### 1. Clone the repository

```bash
git clone https://github.com/your-username/RAMWise.git
cd RAMWise
```

### 2. Set up the Python backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate datasets and train models

```bash
# Generate synthetic dataset
cd datasets
python generate_dataset.py
python preprocess.py
cd ..

# Train Transformer model
cd transformer
python train.py
cd ..

# Train RL agent
cd rl_allocator
python train_rl.py
cd ..

# Run benchmark
cd benchmarking
python benchmark.py
cd ..
```

### 4. Set up the React dashboard

```bash
cd dashboard
npm install
```

### 5. Start everything

```bash
# From the project root — starts both backend and frontend
./start.sh
```

Or start manually in separate terminals:

```bash
# Terminal 1 — Backend
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd dashboard
npm start
```

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:3000

### 6. Run the live demo

```bash
cd backend
source venv/bin/activate
python demo_runner.py
```

The demo runs 20 steps simulating app switching, showing telemetry, Transformer predictions, PPO RL decisions, and benchmark comparisons in the terminal while updating the dashboard in real time.

### 7. Stop everything

```bash
lsof -ti :8000 | xargs kill -9
lsof -ti :3000 | xargs kill -9
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/telemetry` | Record device telemetry (RAM, CPU, battery, foreground app) |
| `GET` | `/predict?app_sequence=Chrome,WhatsApp` | Predict next apps using Transformer model |
| `GET` | `/allocate?app=Chrome&ram_usage=70&battery_level=60` | Get cache allocation decision from PPO agent |
| `GET` | `/metrics` | Aggregated telemetry metrics from SQLite |
| `GET` | `/benchmark` | LRU vs RAMWise benchmark comparison |

## Models

### Transformer (App Prediction)

- **Architecture:** 2-layer Transformer Encoder, 4 attention heads, 64-dim embeddings
- **Input:** Last 2 app token IDs + context features (RAM, battery, CPU, cache state)
- **Output:** Top-3 predicted next apps with confidence scores
- **Training:** 2000 synthetic records, 30 epochs, CrossEntropyLoss
- **File:** `models/transformer_weights/transformer_model.pt`

### PPO RL Agent (Memory Allocation)

- **Algorithm:** Proximal Policy Optimization (Stable-Baselines3)
- **Observation:** 10-dim vector (RAM, battery, CPU, cache tiers, predicted app, hit rate, thrashing, step)
- **Action:** 5 discrete actions (preload, evict, move_to_hot, move_to_warm, move_to_cold)
- **Training:** 50000 timesteps, custom Gymnasium environment
- **File:** `models/rl_models/ppo_ramwise.zip`

## Benchmark Results

The benchmark compares RAMWise (adaptive 3-tier cache with prediction) against a standard LRU cache across 5 realistic app usage traces.

Results are generated by running:
```bash
cd backend/benchmarking
python benchmark.py
```

## Android Client

The Android client runs as a foreground service that collects:
- Foreground app name (via UsageStatsManager)
- RAM usage (via ActivityManager)
- Battery level (via BatteryManager)
- CPU usage (estimated)

It posts telemetry to the backend every 3 seconds. Build with Android Studio from `android-client/`.

For the Android emulator, the backend URL defaults to `http://10.0.2.2:8000` (emulator loopback to host). For a real device, update `BACKEND_URL` in `TelemetryService.kt` to your machine's IP address.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | FastAPI, Uvicorn |
| Database | SQLite |
| Prediction Model | PyTorch Transformer |
| RL Agent | Stable-Baselines3 (PPO) |
| Environment | Gymnasium |
| Dashboard | React, TypeScript, Recharts, Axios |
| Android Client | Kotlin, Coroutines |

## License

MIT
