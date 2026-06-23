FROM python:3.14-slim

WORKDIR /app 

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --frozen

COPY src/ ./src/

CMD ["uv", "run", "src/main.py"]
