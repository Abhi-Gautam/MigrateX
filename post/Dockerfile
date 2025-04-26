# post/Dockerfile
FROM rust:latest as builder
LABEL stage="post"

WORKDIR /app
COPY post/Cargo.toml post/src/ ./ 
RUN cargo build --release

FROM ubuntu:25.04
COPY --from=builder /app/target/release/post_processor /usr/local/bin/
ENTRYPOINT ["post_processor"]
