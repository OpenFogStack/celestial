FROM debian:bookworm@sha256:7d3e8810c96a6a278c218eb8e7f01efaec9d65f50c54aae37421dc3cbeba6535

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    --no-install-suggests \
    ca-certificates \
    wget \
    make \
    unzip \
    python3 \
    git \
    python3-pip \
    python3-venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v24.4/protoc-24.4-linux-x86_64.zip && \
    unzip protoc-24.4-linux-x86_64.zip -d protoc-24.4 && \
    mv protoc-24.4 /usr/local/protoc && \
    rm protoc-24.4-linux-x86_64.zip && \
    chmod +x /usr/local/protoc/bin/* && \
    ln -s /usr/local/protoc/bin/protoc /usr/local/bin/protoc

RUN wget https://go.dev/dl/go1.21.3.linux-amd64.tar.gz && \
    rm -rf /usr/local/go && \
    tar -C /usr/local -xzf go1.21.3.linux-amd64.tar.gz && \
    echo 'export PATH="$PATH:/usr/local/go/bin"' >> /etc/profile && \
    echo 'export PATH="$PATH:/root/go/bin"' >> /etc/profile && \
    echo 'export GOPATH=/root/go' >> /etc/profile && \
    echo 'export GOBIN="/root/go/bin"' >> /etc/profile && \
    rm -rf go1.21.3.linux-amd64.tar.gz

ENV PATH $PATH:/usr/local/go/bin
ENV PATH $PATH:/root/go/bin
ENV GOPATH /root/go
ENV GOBIN /root/go/bin

RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.31.0 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt -U

WORKDIR /celestial

ENTRYPOINT [ "make" ]