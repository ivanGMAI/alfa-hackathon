FROM python:3.13.0-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# uv: more network-resilient than poetry on flaky connections (parallel + retries).
ENV UV_HTTP_TIMEOUT=120
ENV UV_LINK_MODE=copy

WORKDIR /backend

RUN pip install --no-cache-dir --upgrade pip uv

# Install runtime + dev dependencies (PEP 621 + dependency-groups) into the
# system environment. Dev tools are needed for `make test` / `make lint`.
COPY backend/pyproject.toml ./
RUN uv pip install --system -r pyproject.toml --group dev

COPY backend ./

# JWT keys are gitignored — generate them if they were not provided via the build context.
RUN if [ ! -f jwt-private.pem ] || [ ! -f jwt-public.pem ]; then \
        openssl genrsa -out jwt-private.pem 2048 && \
        openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem; \
    fi

RUN chmod +x main.py

CMD ["python3", "main.py"]
