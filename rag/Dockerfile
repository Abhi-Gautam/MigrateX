# rag/Dockerfile
FROM python:3.13-slim
LABEL stage="rag"

RUN pip install --no-cache-dir faiss transformers langchain

WORKDIR /app
COPY rag/ .
ENTRYPOINT ["python", "retrieve_and_prompt.py"]
