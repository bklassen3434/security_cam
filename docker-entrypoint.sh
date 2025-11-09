#!/usr/bin/env bash
set -e
# Warm model into memory (no network; loads from /app/models)
python -c "from app.engine_runtime import get_face_engine; get_face_engine(); print('[warmup] face engine ready')"
exec "$@"
