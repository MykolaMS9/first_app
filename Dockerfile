
FROM python:3.10

RUN pip install -U pip poetry==1.5.1

WORKDIR /app

COPY poetry.lock pyproject.toml README.md ./

ADD first_app ./first_app

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

EXPOSE 3000

WORKDIR /app/first_app

ENTRYPOINT ["python", "main.py"]

# /app/first_app/storage


