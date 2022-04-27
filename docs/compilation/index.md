---
layout: home
title: Compilation
nav_order: 4
---

## Compilation

Use Docker to compile the project.

### Building the Compile Container

Run `make celestial-make` to build a container that has all the dependencies
needed to compile the project.

### Protocol Buffer

You can use the pre-compiled gRPC/protobuf files or compile your own:

```sh
# compile all protofiles for python and go
docker run --rm -v $(pwd):/celestial celestial-make proto/
```

### Python Client

The client does not require compilation as it is interpreted.

Nevertheless, it can be useful to check for type bugs with `mypy`:

```sh
mypy celestial.py
```

You can also package that client as a Docker container if you want.
This requires the `docker` command available on your system.

```sh
# make container
docker build -t celestial .
```

### Go Server

Compile the host server with:

```sh
docker run --rm -v $(pwd):/celestial celestial-make celestial.bin
```
