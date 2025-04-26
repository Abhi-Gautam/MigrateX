# testgen/Dockerfile
FROM python:3.13-slim
LABEL stage="testgen"

RUN pip install --no-cache-dir transformers

WORKDIR /app
COPY testgen/ .
ENTRYPOINT ["python", "generate_tests.py"]
