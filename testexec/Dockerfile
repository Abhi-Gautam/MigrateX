# testexec/Dockerfile
FROM ubuntu:25.04
LABEL stage="testexec"

RUN apt-get update && apt-get install -y cargo golang-go dotnet-sdk-6.0 python3-pytest && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /data  # tests & code mounted here
ENTRYPOINT ["./run_tests.sh"]
