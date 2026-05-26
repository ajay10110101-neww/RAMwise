FOR STARTING
./start.sh

FOR STOPPING
lsof -ti :8000 | xargs kill -9; lsof -ti :3000 | xargs kill -9