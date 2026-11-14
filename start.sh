#!/bin/sh
set -e

exec granian \
  --interface asgi \
  src.actions.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-paths /event-management \
  --reload-ignore-dirs .venv  \
  --workers 1 \
  --workers-kill-timeout 1 \
  --access-log \
  --log-level info
