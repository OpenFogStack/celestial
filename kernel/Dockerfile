FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install -y \
    git \
    make \
    build-essential \
    linux-source \
    bc \
    kmod \
    cpio \
    flex \
    libncurses5-dev \
    libelf-dev \
    libssl-dev \
    bison -y && \
    rm -rf /var/lib/apt/lists/*

ARG KERNEL_VERSION="4.19.0"

RUN git clone https://github.com/torvalds/linux.git /linux.git --branch v${KERNEL_VERSION} --depth 1
WORKDIR /linux.git
