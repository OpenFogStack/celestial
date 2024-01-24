#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


FROM debian:bookworm@sha256:b16cef8cbcb20935c0f052e37fc3d38dc92bfec0bcfb894c328547f81e932d67

ARG OS=linux
ARG ARCH=x86_64
ARG GO_ARCH=amd64
ARG LIBPROTOC_VERSION=25.1
ARG GO_VERSION=1.21.6
ARG PROTOC_GEN_GO_VERSION=1.31.0
ARG PROTOC_GEN_GO_GRPC_VERSION=1.3

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    --no-install-suggests \
    ca-certificates \
    wget \
    make \
    clang \
    gcc-multilib \
    libbpf-dev \
    llvm \
    build-essential \
    unzip \
    python3 \
    git \
    python3-pip \
    python3-venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v${LIBPROTOC_VERSION}/protoc-${LIBPROTOC_VERSION}-${OS}-${ARCH}.zip && \
    unzip protoc-${LIBPROTOC_VERSION}-${OS}-${ARCH}.zip -d protoc-${LIBPROTOC_VERSION} && \
    mv protoc-${LIBPROTOC_VERSION} /usr/local/protoc && \
    rm protoc-${LIBPROTOC_VERSION}-${OS}-${ARCH}.zip && \
    chmod +x /usr/local/protoc/bin/* && \
    ln -s /usr/local/protoc/bin/protoc /usr/local/bin/protoc

RUN wget https://go.dev/dl/go${GO_VERSION}.${OS}-${GO_ARCH}.tar.gz && \
    rm -rf /usr/local/go && \
    tar -C /usr/local -xzf go${GO_VERSION}.${OS}-${GO_ARCH}.tar.gz && \
    echo 'export PATH="$PATH:/usr/local/go/bin"' >> /etc/profile && \
    echo 'export PATH="$PATH:/root/go/bin"' >> /etc/profile && \
    echo 'export GOPATH=/root/go' >> /etc/profile && \
    echo 'export GOBIN="/root/go/bin"' >> /etc/profile && \
    rm -rf go${GO_VERSION}.${OS}-${GO_ARCH}.tar.gz

ENV PATH $PATH:/usr/local/go/bin
ENV PATH $PATH:/root/go/bin
ENV GOPATH /root/go
ENV GOBIN /root/go/bin

RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v${PROTOC_GEN_GO_VERSION} && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v${PROTOC_GEN_GO_GRPC_VERSION}

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt -U

WORKDIR /celestial

ENTRYPOINT [ "make" ]