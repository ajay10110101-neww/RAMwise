# RAMWise — Start & Stop Instructions

## Start

```bash
cd RAMWise
./start.sh
```

This launches:
- Backend (FastAPI) on http://localhost:8000
- Frontend (React) on http://localhost:3000
- API docs at http://localhost:8000/docs

## Stop

Press `Ctrl+C` in the terminal running `start.sh`.

If that doesn't work:
```bash
lsof -ti :8000 | xargs kill -9
lsof -ti :3000 | xargs kill -9
```

## Run Demo (optional)

In a separate terminal while start.sh is running:
```bash
cd RAMWise/backend
source venv/bin/activate
python demo_runner.py
```

## Manual Start (two terminals)

Terminal 1 — Backend:
```bash
cd RAMWise/backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Terminal 2 — Frontend:
```bash
cd RAMWise/dashboard
npm start
```
