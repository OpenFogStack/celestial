---
layout: default
title: Compilation
nav_order: 4
---

## Compilation

Compiling the project requires generating protocol buffer files, generating some
Go code for eBPF, and compiling Go code into a static binary.

We recommend using Docker to compile the project.

### Using Docker

#### Building the Compile Container

Run `make celestial-make` to build a container that has all the dependencies
needed to compile the project.

#### Protocol Buffer

You can use the pre-compiled gRPC/protocol buffer files or compile your own:

```sh
# compile all protofiles for python and go
docker run --platform linux/amd64 --rm -v $(pwd):/celestial celestial-make proto
```

#### Go Server

Compile the host server with:

```sh
docker run --platfrom linux/amd64 --rm -v $(pwd):/celestial celestial-make celestial.bin
```

### Manually

To manually compile and generate code, install the dependencies found in [`compile.Dockerfile`](https://github.com/OpenFogStack/celestial/blob/compile.Dockerfile).
Then run `make` to compile.
