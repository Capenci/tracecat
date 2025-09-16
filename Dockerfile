# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.8.6-python3.12-bookworm-slim

ENV HOST=0.0.0.0
ENV PORT=8000

# Enable bytecode compilation and optimize uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install required apt packages
COPY scripts/install-packages.sh .
RUN chmod +x install-packages.sh && \
    ./install-packages.sh && \
    rm install-packages.sh

# Auto update script
COPY scripts/auto-update.sh ./auto-update.sh
RUN chmod +x auto-update.sh && \
    ./auto-update.sh && \
    rm auto-update.sh

# Create non-root user
RUN groupadd -g 1001 apiuser && \
    useradd -m -u 1001 -g apiuser apiuser

# Pre-create dirs (owned by apiuser from start, so no later chown needed)
RUN install -d -o apiuser -g apiuser \
    /home/apiuser/.cache/uv \
    /home/apiuser/.cache/deno \
    /home/apiuser/.cache/s3 \
    /home/apiuser/.cache/tmp \
    /home/apiuser/.local/bin \
    /home/apiuser/.local/lib/node_modules \
    /app/.scripts

# Pre-copy cached node/deno if available
RUN cp -r /opt/deno-cache/* /home/apiuser/.cache/deno/ 2>/dev/null || true && \
    cp -r /opt/node_modules/* /home/apiuser/.local/lib/node_modules/ 2>/dev/null || true && \
    rm -rf /opt/deno-cache /opt/node_modules

# Environment setup
ENV PYTHONUSERBASE="/home/apiuser/.local"
ENV UV_CACHE_DIR="/home/apiuser/.cache/uv"
ENV PYTHONPATH=/home/apiuser/.local:$PYTHONPATH
ENV PATH=/home/apiuser/.local/bin:$PATH
ENV DENO_DIR="/home/apiuser/.cache/deno"
ENV NODE_MODULES_DIR="/home/apiuser/.local/lib/node_modules"
ENV TMPDIR="/home/apiuser/.cache/tmp"
ENV TEMP="/home/apiuser/.cache/tmp"
ENV TMP="/home/apiuser/.cache/tmp"

WORKDIR /app

# Install dependencies only (cache optimized)
COPY pyproject.toml uv.lock ./  
COPY packages ./packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev --no-editable

# Copy project files (already owned by apiuser)
COPY --chown=apiuser:apiuser ./tracecat /app/tracecat
COPY --chown=apiuser:apiuser ./packages/tracecat-registry /app/packages/tracecat-registry
COPY --chown=apiuser:apiuser ./packages/tracecat-ee /app/packages/tracecat-ee
COPY --chown=apiuser:apiuser ./pyproject.toml /app/pyproject.toml
COPY --chown=apiuser:apiuser ./uv.lock /app/uv.lock
COPY --chown=apiuser:apiuser ./.python-version /app/.python-version
COPY --chown=apiuser:apiuser ./README.md /app/README.md
COPY --chown=apiuser:apiuser ./LICENSE /app/LICENSE
COPY --chown=apiuser:apiuser ./alembic.ini /app/alembic.ini
COPY --chown=apiuser:apiuser ./alembic /app/alembic

# Scripts (use COPY --chmod to avoid chmod step)
COPY --chown=apiuser:apiuser --chmod=755 scripts/entrypoint.sh /app/entrypoint.sh
COPY --chmod=755 scripts/check_tmp.py /usr/local/bin/check_tmp.py

# Install the project with EE features
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Symlink uv for apiuser (no need to chown, dir is already owned by apiuser)
RUN ln -s $(which uv) /home/apiuser/.local/bin/uv || true

# Switch to non-root
USER apiuser

# Verify access (sanity check)
RUN python3 -c "import os; print('UV cache writable:', os.access(os.environ['UV_CACHE_DIR'], os.W_OK))"

EXPOSE $PORT

ENTRYPOINT ["/app/entrypoint.sh"]
ENV PATH="/app/.venv/bin:$PATH"
CMD ["sh", "-c", "python3 -m uvicorn tracecat.api.app:app --host $HOST --port $PORT"]
