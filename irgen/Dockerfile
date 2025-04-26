# irgen/Dockerfile
FROM ubuntu:25.04
LABEL stage="irgen"

RUN apt-get update && \
    apt-get install -y python3 python3-pip clang libclang-dev default-jdk && \
    pip3 install --no-cache-dir mlir-python-bindings && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY irgen/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY irgen/ .
ENTRYPOINT ["python3", "generate_ir.py"]
