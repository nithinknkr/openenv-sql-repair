# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker

FROM python:3.11-slim

# HuggingFace Spaces requires a non-root user with uid=1000
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install dependencies (single source of truth: pyproject.toml)
# Copy all project files first (needed for pip install . to find pyproject.toml)
COPY --chown=user . /app

# Install from pyproject.toml — single source of truth, picks up ALL dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Verify SQLite is available (built into Python stdlib)
RUN python -c "import sqlite3; print('SQLite OK:', sqlite3.sqlite_version)"

# HuggingFace Spaces default port
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
