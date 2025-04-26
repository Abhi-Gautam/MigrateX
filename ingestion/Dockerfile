# ingestion/Dockerfile
FROM ubuntu:25.04
LABEL stage="ingestion"

# Install VCS, Python, Java, .NET SDKs, Clang
RUN apt-get update && \
    apt-get install -y git subversion python3 python3-pip openjdk-11-jdk clang libclang-dev dotnet-sdk-6.0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ingestion/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ingestion/ .
ENTRYPOINT ["python3", "repo_cloner.py"]
