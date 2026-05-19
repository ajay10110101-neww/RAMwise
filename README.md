# RAMWise — Context-Aware Adaptive Memory Management

RAMWise is an intelligent memory management system for Android that uses a Transformer model for app usage prediction and a PPO reinforcement learning agent for adaptive cache allocation.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Android Client  │────▶│   FastAPI Backend  │◀────│  React Dashboard │
│  (Kotlin)        │     │   (Python)         │     │  (TypeScript)    │
│                  │     │                    │     │                  │
│ • RAM monitoring │     │ • Transformer API  │     │ • Live charts    │
│ • Battery level  │     │ • PPO RL allocator │     │ • Prediction feed│
│ • CPU usage      │     │ • SQLite storage   │     │ • Cache tiers    │
│ • App detection  │     │ • Benchmark engine │     │ • RL decisions   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Project Structure

```
RAMWise/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app — 5 endpoints
│   │   ├── schemas.py           # Pydantic models
│   │   └── database.py          # SQLite setup
│   ├── transformer/
│   │   └── model.py             # AppTransformer (PyTorch)
│   ├── rl_allocator/
│   │   ├── memory_env.py        # Custom Gymnasium environment
│   │   └── train_rl.py          # PPO training script
│   ├── cache_simulator/
│   │   └── cache.py             # AdaptiveCache + LRUCache
│   ├── benchmarking/
│   │   └── benchmark.py         # LRU vs RAMWise benchmark
│   ├── demo_runner.py           # Live demo script
│   └── requirements.txt
├── datasets/
│   └── ubiqlog/
│       ├── per_user/            # Per-user .pth model files
│       └── tokenizer.json       # App name tokenizer (201 apps)
├── models/
│   ├── transformer_weights/
│   │   └── global_model.pth     # Global Transformer model
│   └── rl_models/
│       └── ppo_ramwise.zip      # PPO RL model
├── dashboard/
│   └── src/
│       ├── api.ts               # API client
│       ├── App.tsx              # Dashboard UI
│       ├── PredictionFeed.tsx   # Live prediction feed
│       └── index.tsx            # Entry point
├── android-client/
│   └── app/src/main/
│       ├── AndroidManifest.xml
│       └── java/com/ramwise/telemetry/
│           ├── MainActivity.kt
│           └── TelemetryService.kt
├── start.sh
└── .gitignore
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) Android Studio

### 1. Clone and set up

```bash
git clone https://github.com/your-username/RAMWise.git
cd RAMWise
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Add model assets

Place these files manually (not in git due to size):
- `models/transformer_weights/global_model.pth` — global Transformer
- `models/rl_models/ppo_ramwise.zip` — PPO RL agent
- `datasets/ubiqlog/tokenizer.json` — app tokenizer
- `datasets/ubiqlog/per_user/*.pth` — per-user models (optional)

### 3. Start everything

```bash
./start.sh
```

- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:3000

### 4. Run the live demo

```bash
cd backend
source venv/bin/activate
python demo_runner.py
```

### 5. Stop

```bash
lsof -ti :8000 | xargs kill -9
lsof -ti :3000 | xargs kill -9
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/telemetry` | Record device telemetry (RAM, CPU, battery, app) |
| `GET` | `/predict?app_sequence=chrome,whatsapp` | Predict next apps via Transformer |
| `GET` | `/allocate?app=chrome&ram_usage=70&battery_level=60` | PPO RL cache allocation |
| `GET` | `/metrics` | Aggregated telemetry metrics |
| `GET` | `/benchmark` | LRU vs RAMWise comparison |

## Models

### Transformer (App Prediction)

- **Architecture:** 2-layer Transformer Encoder, 4 heads, 128-dim embeddings
- **Input:** Last 5 app token IDs + 2-dim context (hour, cache state)
- **Output:** Top-3 predicted next apps with confidence scores
- **Vocab:** 201 apps from UbiqLog dataset
- **Location:** `models/transformer_weights/global_model.pth`

### PPO RL Agent (Memory Allocation)

- **Algorithm:** Proximal Policy Optimization
- **Observation:** 10-dim vector (RAM, battery, CPU, cache tiers, etc.)
- **Action:** 5 discrete actions (preload, evict, move_to_hot/warm/cold)
- **Location:** `models/rl_models/ppo_ramwise.zip`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | FastAPI, Uvicorn |
| Database | SQLite |
| Prediction | PyTorch Transformer |
| RL Agent | Stable-Baselines3 (PPO) |
| Dashboard | React, TypeScript, Recharts |
| Android | Kotlin, Coroutines |

## License

MIT
