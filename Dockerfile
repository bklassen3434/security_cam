FROM python:3.11-slim

# system libs used by opencv and onnxruntime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install python deps
COPY requirements.docker.txt .
RUN pip install --no-cache-dir -r requirements.docker.txt

# copy code
COPY app ./app
COPY config.yaml ./config.yaml
COPY wsgi.py ./wsgi.py

# create dirs for data and models
RUN mkdir -p /app/data/events /app/data/enroll /app/models

# Tell InsightFace where the cached models live
ENV INSIGHTFACE_HOME=/app/models

# Make runtime defaults match the build-time prefetch
ENV INSIGHTFACE_MODEL=buffalo_l
ENV ONNX_PROVIDERS=CPUExecutionProvider
ENV INSIGHTFACE_DET_SIZE=320,320
ENV MIN_DET_SCORE=0.60

# Pre-fetch InsightFace models at build time
RUN python - <<'PY'
from insightface.app import FaceAnalysis
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(320,320))
print("Models ready")
PY

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# non-root user
RUN useradd -m runner
# Add runner user to it
RUN usermod -aG video runner
USER runner

# default is no command because compose will pass it
