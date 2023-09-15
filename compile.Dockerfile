FROM debian:bullseye@sha256:bdf44f19d09b558203306836a612cc8e42a1106b2f731fbeb000e2696c04f9c8

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    --no-install-suggests \
    ca-certificates \
    wget \
    make \
    unzip \
    python3 \
    git \
    python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.15.8/protoc-3.15.8-linux-x86_64.zip && \
    unzip protoc-3.15.8-linux-x86_64.zip -d protoc-3.15.8 && \
    mv protoc-3.15.8 /usr/local/protoc && \
    rm protoc-3.15.8-linux-x86_64.zip && \
    chmod +x /usr/local/protoc/bin/* && \
    ln -s /usr/local/protoc/bin/protoc /usr/local/bin/protoc

RUN wget https://go.dev/dl/go1.21.1.linux-amd64.tar.gz && \
    rm -rf /usr/local/go && \
    tar -C /usr/local -xzf go1.21.1.linux-amd64.tar.gz && \
    echo 'export PATH="$PATH:/usr/local/go/bin"' >> /etc/profile && \
    echo 'export PATH="$PATH:/root/go/bin"' >> /etc/profile && \
    echo 'export GOPATH=/root/go' >> /etc/profile && \
    echo 'export GOBIN="/root/go/bin"' >> /etc/profile && \
    rm -rf go1.21.1.linux-amd64.tar.gz

ENV PATH $PATH:/usr/local/go/bin
ENV PATH $PATH:/root/go/bin
ENV GOPATH /root/go
ENV GOBIN /root/go/bin

RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.26.0 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.1

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt -U

WORKDIR /celestial

ENTRYPOINT [ "make" ]