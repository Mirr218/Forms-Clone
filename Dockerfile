FROM python:3.13-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry && poetry config virtualenvs.in-project true && poetry install --no-cache --without dev

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app /app

COPY . .

CMD ["/app/.venv/bin/python", "/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
