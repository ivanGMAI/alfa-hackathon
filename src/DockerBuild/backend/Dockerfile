FROM python:3.13.0-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /backend

RUN pip install --upgrade pip wheel "poetry==2.1.1"

RUN poetry config virtualenvs.create false

COPY backend/pyproject.toml backend/poetry.lock ./

RUN poetry install

COPY backend ./

# JWT keys are gitignored — generate them if they were not provided via the build context.
RUN if [ ! -f jwt-private.pem ] || [ ! -f jwt-public.pem ]; then \
        openssl genrsa -out jwt-private.pem 2048 && \
        openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem; \
    fi

RUN chmod +x main.py

CMD ["python3", "main.py"]
