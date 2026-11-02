FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable
COPY data ./data
COPY web/dist ./web/dist
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src" EVAL_LAB_DATA_DIR="/app/data" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
USER 10001:10001
CMD ["uvicorn","eval_lab.api:app","--host","0.0.0.0","--port","8000","--no-access-log"]

