# RAMWise -- Context-Aware Adaptive Memory Management

RAMWise is an intelligent memory management system for Android that replaces
traditional LRU caching with a two-stage ML pipeline: a Transformer model
predicts which app the user will open next, and a Proximal Policy Optimization
(PPO) reinforcement learning agent decides how to place that app across a
three-tier cache (HOT / WARM / COLD).  A React dashboard visualises every
decision in real time, and a benchmark engine quantifies the improvement over
standard LRU across realistic app-usage traces.

---

## Table of Contents

1. [Working Principle](#working-principle)
2. [Architecture](#architecture)
3. [Component Details](#component-details)
4. [API Endpoints](#api-endpoints)
5. [Benchmark Results](#benchmark-results)
6. [Project Structure](#project-structure)
7. [Setup and Running](#setup-and-running)
8. [Tech Stack](#tech-stack)

---

## Working Principle

### Problem Statement

Android devices manage memory with a flat LRU (Least Recently Used) cache.
When RAM pressure rises, the OS evicts the least-recently-used app regardless
of whether the user is likely to return to it.  This causes two problems:

1. **Launch latency** -- evicted apps must cold-start from storage (1-3 seconds).
2. **Thrashing** -- under pressure, the OS evicts and re-loads the same apps
   repeatedly, wasting CPU and battery.

RAMWise addresses both by predicting future app usage and proactively managing
a tiered cache.

### Two-Stage ML Pipeline

```
                         Stage 1: Prediction
 User's recent app   ──────────────────────────────>  Predicted next app
 sequence (last 7)        Transformer Model
                                |
                                v
                         Stage 2: Allocation
 Device state         ──────────────────────────────>  Cache action
 (RAM, battery,       PPO Reinforcement Learning       (preload / evict /
  predicted app,       Agent                            move_to_hot /
  cache hit rate,                                       move_to_warm /
  thrashing)                                            move_to_cold)
```

**Stage 1 -- Transformer (Next-App Prediction)**

The Transformer encoder takes the last 7 app token IDs as input, combined with
a 2-dimensional context vector (hour of day normalised to [0,1] and a cache
state indicator).  It outputs a probability distribution over all 201 known
apps.  The top-3 predictions are returned to the dashboard; the top-1
prediction is forwarded to Stage 2.

**Stage 2 -- PPO Agent (Cache Allocation)**

The PPO agent observes a 10-dimensional state vector that mirrors the training
environment's observation space:

| Index | Feature | Description |
|-------|---------|-------------|
| 0 | ram_usage | Current RAM usage normalised to [0, 1] |
| 1 | battery_level | Current battery level normalised to [0, 1] |
| 2 | cpu_usage | Estimated CPU usage |
| 3 | hot_ratio | Fraction of HOT cache slots occupied |
| 4 | warm_ratio | Fraction of WARM cache slots occupied |
| 5 | cold_ratio | Fraction of apps in COLD storage |
| 6 | predicted_app | Transformer's predicted app ID / 150 |
| 7 | hit_rate | Running cache hit rate |
| 8 | thrashing | Normalised thrashing counter |
| 9 | hour | Current hour of day / 23 |

The agent selects one of 5 discrete actions:

| Action | Meaning | When to use |
|--------|---------|-------------|
| 0 | preload_app | RAM low, battery healthy -- pre-cache predicted app into HOT |
| 1 | evict_app | RAM high -- remove an app from HOT to free memory |
| 2 | move_to_hot | Promote a WARM app to HOT for faster access |
| 3 | move_to_warm | Promote a COLD app to WARM as a buffer |
| 4 | move_to_cold | Demote a HOT app to COLD to save memory or battery |

The action, target app (from the Transformer), and cache tier are returned to
the dashboard and displayed with a human-readable reason.

### Three-Tier Adaptive Cache

Unlike a flat LRU cache, RAMWise organises cached apps into three tiers:

| Tier | Capacity | Hit Latency | Description |
|------|----------|-------------|-------------|
| HOT | 4 slots | 0.1s | Fully resident in RAM, fastest access |
| WARM | 6 slots | 0.4s | Partially retained, promoted to HOT on access |
| COLD | unbounded | 1.8s | Evicted from active memory, cold-start on access |

When an app is accessed:
- If it is in HOT: immediate hit (0.1s).
- If it is in WARM: hit with promotion to HOT (0.4s), demoting the least-used
  HOT app to WARM.
- If it is in COLD or unknown: cold miss (1.8s), inserted into HOT with
  cascading demotion.

The Transformer's predictions allow the cache to **preload** likely-next apps
into the WARM tier before the user opens them, converting future cold misses
into warm hits.

### Reward Structure (RL Training)

The PPO agent is trained in a custom Gymnasium environment (`MemoryEnv`) with
state-dependent rewards that encode the correct cache management policy:

| Condition | Reward |
|-----------|--------|
| App found in HOT cache | +1.0 |
| App found in WARM cache | +0.3 |
| Cache miss (cold) | -0.5 |
| Preload when RAM < 0.6 and battery > 0.4 | +0.6 |
| Preload when RAM > 0.8 | -0.5 |
| Evict from HOT when RAM > 0.7 | +0.4 |
| Evict when RAM < 0.5 | -0.5 |
| Promote to HOT when RAM < 0.65 | +0.3 |
| Demote to COLD when RAM > 0.65 | +0.5 |
| Demote to COLD when RAM < 0.5 | -0.5 |
| Battery < 0.2 global penalty | -0.2 |
| RAM > 0.85 global penalty | -0.2 |
| Per-thrashing penalty | -0.005 * count |

This reward structure ensures the agent learns:
- Preload when the system is under light load (proactive caching).
- Evict or demote when RAM pressure is high (reactive memory freeing).
- Never preload under high RAM or low battery (avoid worsening pressure).

---

## Architecture

```
 +---------------------+       HTTP        +-----------------------------+
 |  Android Client     | ----------------> |   FastAPI Backend           |
 |  (Kotlin)           |   POST /telemetry |   (backend/api/main.py)     |
 |                     |                   |                             |
 | - Foreground app    |                   |  +-----------------------+  |
 | - RAM usage         |                   |  | SQLite (ramwise.db)   |  |
 | - CPU usage         |                   |  | - telemetry table     |  |
 | - Battery level     |                   |  | - predictions table   |  |
 | - Timestamp         |                   |  +-----------------------+  |
 +---------------------+                   |                             |
                                           |  +-----------------------+  |
 +---------------------+       HTTP        |  | AppTransformer        |  |
 |  React Dashboard    | <---------------> |  | (3-layer, 8-head,     |  |
 |  (TypeScript)       |   /predict        |  |  256-dim, 201 vocab)  |  |
 |                     |   /allocate       |  +-----------------------+  |
 | - Live RAM/CPU      |   /metrics        |                             |
 | - Cache tier viz    |   /benchmark      |  +-----------------------+  |
 | - Prediction feed   |                   |  | PPO RL Agent          |  |
 | - RL decision panel |                   |  | (10-dim obs,          |  |
 | - Battery slider    |                   |  |  5 discrete actions)  |  |
 | - Benchmark chart   |                   |  +-----------------------+  |
 +---------------------+                   +-----------------------------+
                                                        |
                                                        v
                                           +-----------------------------+
                                           |  Cache Simulator            |
                                           |  (cache_simulator/cache.py) |
                                           |                             |
                                           |  AdaptiveCache              |
                                           |  +--------+--------+------+ |
                                           |  |  HOT   |  WARM  | COLD | |
                                           |  | 4 slots| 6 slots| inf  | |
                                           |  | 0.1s   | 0.4s   | 1.8s | |
                                           |  +--------+--------+------+ |
                                           |                             |
                                           |  LRUCache (baseline)        |
                                           |  Flat, capacity=3           |
                                           +-----------------------------+
                                                        |
                                                        v
                                           +-----------------------------+
                                           |  Benchmark Engine           |
                                           |  (benchmarking/             |
                                           |   benchmark.py)             |
                                           |                             |
                                           |  5 traces x 25 accesses     |
                                           |  Metrics: latency, hit rate,|
                                           |  thrashing, mem efficiency  |
                                           +-----------------------------+
```

### Data Flow

1. The Android client collects device telemetry (RAM, CPU, battery, foreground
   app) every 3 seconds and POSTs it to `/telemetry`.
2. The dashboard posts simulated telemetry and fetches predictions and
   allocation decisions in parallel every 3 seconds.
3. On `/predict`, the backend tokenises the app sequence, runs the Transformer,
   and returns the top-3 predicted apps with confidence scores.
4. On `/allocate`, the backend runs a two-step pipeline:
   - The Transformer predicts the next app (top-1).
   - A 10-dimensional observation vector is built from device state and the
     predicted app.
   - The PPO agent selects a cache action based on the observation.
   - The response includes the action, target app, cache tier, and a
     human-readable reason.
5. The benchmark engine replays 5 realistic app-usage traces through the
   AdaptiveCache (with Transformer preloading) and a flat LRUCache, then
   compares latency, hit rate, thrashing, and memory efficiency.

---

## Component Details

### Transformer Model (`backend/transformer/model.py`)

- **Architecture:** 3-layer Transformer Encoder, 8 attention heads, 256-dim
  embeddings, context dimension 2.
- **Input:** Last 7 app token IDs (integer sequence) + 2-dim context vector
  (hour normalised, cache state).
- **Output:** Logits over 201 app classes.  Top-k predictions extracted via
  softmax + topk.
- **Training data:** UbiqLog dataset, per-user models for 10 users, global
  model trained on combined data.
- **Training metrics:** Average top-1 accuracy 76.1%, average top-3 accuracy
  87.2%, best user top-1 accuracy 84.4%.

### PPO RL Agent (`backend/rl_allocator/`)

- **Algorithm:** Proximal Policy Optimization (Stable-Baselines3).
- **Observation space:** 10-dimensional continuous [0, 1] box.
- **Action space:** 5 discrete actions (preload, evict, move_to_hot,
  move_to_warm, move_to_cold).
- **Training:** 200,000 timesteps on custom Gymnasium environment with
  state-dependent rewards.
- **Dataset:** `ramwise_combined_dataset.json` (UbiqLog app usage records).
- **Environment:** `MemoryEnv` with 150 simulated apps, cache size 10,
  200-step episodes.

### Cache Simulator (`backend/cache_simulator/cache.py`)

**AdaptiveCache (RAMWise):**
- HOT tier: 4 slots, 0.1s hit latency.
- WARM tier: 6 slots, 0.4s hit latency (promoted to HOT on access).
- COLD tier: unbounded, 1.8s miss latency.
- Supports preloading (insert into WARM if battery > 40%).
- Cascading demotion: HOT overflow goes to WARM, WARM overflow goes to COLD.

**LRUCache (Baseline):**
- Flat cache, capacity 3.
- 0.2s hit latency, 1.8s miss latency.
- Standard LRU eviction policy.

### Benchmark Engine (`backend/benchmarking/benchmark.py`)

Five realistic app-usage traces, each with 25 accesses:

| Trace | Pattern | Unique Apps |
|-------|---------|-------------|
| TRACE_1 | Productivity | client, cms, home, music |
| TRACE_2 | Social | whatsapp, contacts, dialer, client |
| TRACE_3 | Media | youtube, music, firefox, client |
| TRACE_4 | Navigation | maps, weather, calendar, client |
| TRACE_5 | Camera | camera, gallery, home, client |

For each trace, RAMWise uses the Transformer to predict the next app and
preloads the top-3 predictions into the WARM tier before each access.  The
LRU baseline uses no prediction.

Metrics computed:
- **Average launch latency** (seconds)
- **Cache hit rate** (fraction of accesses that hit HOT or WARM)
- **Thrashing rate** (fraction of consecutive high-latency pairs)
- **Memory efficiency** (hit rate gain relative to LRU baseline)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/telemetry` | Record device telemetry (foreground app, RAM, CPU, battery, timestamp, user_id) |
| `GET` | `/predict?app_sequence=chrome,whatsapp&user_id=default` | Predict next 3 apps using Transformer |
| `GET` | `/allocate?app_sequence=chrome,whatsapp&ram_usage=70&battery_level=60&user_id=default` | Two-step pipeline: Transformer prediction + PPO cache allocation |
| `GET` | `/metrics` | Aggregated telemetry metrics from SQLite |
| `GET` | `/benchmark` | LRU vs RAMWise benchmark comparison (from saved results) |

All endpoints return JSON.  The `/allocate` endpoint is the core pipeline: it
queries SQLite for recent telemetry, runs the Transformer, builds the RL
observation, and returns the PPO's decision.

---

## Benchmark Results

```
==================================================
BENCHMARK RESULTS: LRU vs RAMWise
==================================================
Avg Launch Latency   | LRU: 0.9168s | RAMWise: 0.316s
Avg Cache Hit Rate   | LRU: 0.552  | RAMWise: 0.88
Avg Thrashing Rate   | LRU: 0.1167 | RAMWise: 0.0417
==================================================
Latency Improvement  : 65.53%
Hit Rate             : 88% (>= 85% KPI)
Thrashing Reduction  : 64.27%
Memory Efficiency    : 59.42%
==================================================
KPI - Latency >= 20%    : PASS
KPI - Hit Rate >= 85%   : PASS
KPI - Thrashing >= 50%  : PASS
KPI - Memory >= 30%     : PASS
==================================================
```

**Why RAMWise wins:**

- The Transformer preloads predicted apps into the WARM tier, converting
  future cold misses (1.8s) into warm hits (0.4s).
- The PPO agent adapts cache placement based on RAM pressure and battery,
  avoiding preloads under high load and evicting only when necessary.
- The three-tier cache keeps frequently-used apps in HOT (0.1s), recently-used
  apps in WARM (0.4s), and rarely-used apps in COLD (1.8s), whereas LRU treats
  all cached apps equally and evicts the least-recently-used regardless of
  future usage.

---

## Project Structure

```
RAMWise/
+-- backend/
|   +-- api/
|   |   +-- main.py              FastAPI app -- 5 endpoints, model loading,
|   |   |                        Transformer+RL pipeline
|   |   +-- schemas.py           Pydantic request/response models
|   |   +-- database.py          SQLite setup (telemetry, predictions tables)
|   +-- transformer/
|   |   +-- model.py             AppTransformer class + get_topk_predictions
|   +-- rl_allocator/
|   |   +-- memory_env.py        Custom Gymnasium environment (MemoryEnv)
|   |   +-- train_rl.py          PPO training script (Stable-Baselines3)
|   +-- cache_simulator/
|   |   +-- cache.py             AdaptiveCache + LRUCache
|   +-- benchmarking/
|   |   +-- benchmark.py         LRU vs RAMWise benchmark engine
|   +-- demo_runner.py           Live demo script (20 steps, 3s interval)
|   +-- requirements.txt
+-- datasets/
|   +-- ubiqlog/
|       +-- tokenizer.json       App name to ID mapping (201 apps)
|       +-- per_user/            Per-user .pth model files (10 users)
|       +-- benchmark_report.json  Transformer training report
+-- models/
|   +-- transformer_weights/
|   |   +-- global_model.pth     Global Transformer model
|   +-- rl_models/
|       +-- ppo_ramwise.zip      Trained PPO RL model
|       +-- best_model.zip       Best checkpoint during training
|       +-- rl_training_log.json Training summary
|       +-- evaluations.npz      Evaluation data
+-- dashboard/
|   +-- src/
|       +-- api.ts               TypeScript API client + type definitions
|       +-- App.tsx               Main dashboard (live charts, cache viz,
|       |                        predictions, RL decisions, benchmark)
|       +-- PredictionFeed.tsx    Chaining prediction feed component
|       +-- index.tsx             React entry point
+-- android-client/
|   +-- app/src/main/
|       +-- AndroidManifest.xml
|       +-- java/com/ramwise/telemetry/
|           +-- MainActivity.kt
|           +-- TelemetryService.kt
+-- start.sh                     Start backend + frontend
+-- startandstopInstruction.md   Operations guide
+-- .gitignore
+-- README.md
```

---

## Setup and Running

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) Android Studio for the mobile client

### 1. Clone and set up Python environment

```bash
git clone https://github.com/Ajay-1011-git/RAMWise.git
cd RAMWise/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Add model assets

Place these files in the project (not in git due to size):

| File | Location | Source |
|------|----------|--------|
| Global Transformer | `models/transformer_weights/global_model.pth` | Trained on UbiqLog |
| PPO RL model | `models/rl_models/ppo_ramwise.zip` | Trained with train_rl.py |
| Tokenizer | `datasets/ubiqlog/tokenizer.json` | UbiqLog vocabulary |
| Per-user models | `datasets/ubiqlog/per_user/*.pth` | Optional, per-user fine-tuning |

### 3. Start everything

```bash
./start.sh
```

This launches:
- **Backend:** http://localhost:8000 (FastAPI + Uvicorn)
- **Frontend:** http://localhost:3000 (React + TypeScript)
- **API Docs:** http://localhost:8000/docs (Swagger UI)

### 4. Run the live demo (optional)

In a separate terminal:

```bash
cd RAMWise/backend
source venv/bin/activate
python demo_runner.py
```

The demo runs 20 steps at 3-second intervals, posting telemetry, fetching
predictions, and displaying RL decisions in the terminal.

### 5. Run the benchmark (optional)

```bash
cd RAMWise/backend/benchmarking
python benchmark.py
```

Requires the backend to be running (calls `/predict` for Transformer
predictions during trace replay).

### 6. Stop

Press `Ctrl+C` in the terminal running `start.sh`, or:

```bash
lsof -ti :8000 | xargs kill -9
lsof -ti :3000 | xargs kill -9
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | FastAPI, Uvicorn, Pydantic |
| Database | SQLite |
| Prediction Model | PyTorch Transformer Encoder |
| RL Agent | Stable-Baselines3 (PPO), Gymnasium |
| Dashboard | React, TypeScript, Recharts, Axios |
| Android Client | Kotlin, Coroutines |
| Cache Simulation | Custom Python (AdaptiveCache, LRUCache) |
| Benchmark | Custom Python trace-driven evaluation |
