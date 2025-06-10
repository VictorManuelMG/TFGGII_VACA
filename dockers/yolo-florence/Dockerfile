FROM python:3.12-slim

WORKDIR /app
RUN apt-get update
RUN apt-get install -y libgl1
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-root

COPY . .





CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

