# chunking/Dockerfile
FROM python:3.13-slim
LABEL stage="chunking"

RUN pip install --no-cache-dir faiss-cpu transformers

WORKDIR /app
COPY chunking/ .
ENTRYPOINT ["python", "chunk_and_embed.py"]
