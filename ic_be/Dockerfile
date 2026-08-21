FROM python:3.10-alpine
ENV APPLICATION_SERVICE=/app

# Create the working directory
RUN mkdir -p $APPLICATION_SERVICE

# Set the working directory
WORKDIR $APPLICATION_SERVICE

# Install PostgreSQL client + make + bash
RUN apk add --no-cache postgresql-client make bash

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy and install dependencies using Poetry
COPY poetry.lock pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

# Copy the entire project after installing the core library
COPY . $APPLICATION_SERVICE

# Lệnh chạy ứng dụng
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
