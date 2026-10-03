#!/usr/bin/env bash
# Démarre le serveur web (gunicorn) + le worker QC en arrière-plan.
set -e
mkdir -p queue results work
python worker.py &
WORKER_PID=$!
echo "Worker démarré (PID $WORKER_PID)"
trap "kill $WORKER_PID" EXIT
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5057} --workers 2 --threads 4 --timeout 120
