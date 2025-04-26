# translate/Dockerfile
FROM python:3.13-slim
LABEL stage="translate"

RUN pip install --no-cache-dir openai torch

WORKDIR /app
COPY translate/ .
ENTRYPOINT ["python", "orchestrate_llm.py"]
