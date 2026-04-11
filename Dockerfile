# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker

FROM public.ecr.aws/docker/library/python:3.11-slim

# HuggingFace Spaces requires a non-root user with uid=1000
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy all project files first (needed for pip install . to find pyproject.toml)
COPY --chown=user . /app

# Install PyTorch CPU first (smaller image, no CUDA overhead on HF Spaces)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir .

# Verify both SQLite and PyTorch are available
RUN python -c "import sqlite3; print('SQLite OK:', sqlite3.sqlite_version)"
RUN python -c "import torch; print('PyTorch OK:', torch.__version__)"

# HuggingFace Spaces default port
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
