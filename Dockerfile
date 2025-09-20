FROM python:3.12-slim

LABEL authors="Oksana_Donchuk"

# Встановлюємо залежності системи
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Встановлюємо poetry
ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Копіюємо тільки файли залежностей
COPY pyproject.toml poetry.lock* ./

# Встановлюємо залежності
RUN poetry install --no-root --no-ansi

# Копіюємо решту проєкту
COPY . .

EXPOSE 8000


CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]