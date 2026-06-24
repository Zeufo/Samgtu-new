FROM python:3.14-slim

WORKDIR /app 

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --frozen

RUN apt-get update && apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

COPY src/ ./src/

CMD ["uv", "run", "src/main.py"]
