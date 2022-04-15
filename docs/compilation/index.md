---
layout: home
title: Compilation
nav_order: 3
---

## Compilation

Use the Makefiles to compile the project.

### Protocol Buffer

You can use the pre-compiled gRPC/protobuf files or compile your own.

To compile the `proto` files (needed for communication between server and client),
you will need the following tools:

- `go`, version 1.16 or later
- `python3`, preferably Python 3.8 or later
- `protoc`, version 3.15.8 or later (on macOS, install with `brew install protobuf`)
- `mypy-protobuf` (`pip3 install mypy-protobuf`) to compile type hints for
  generated Python files
- `grpcio-tools`, version 1.37.1 or later (`pip3 install grpcio-tools`) to
  generate gRPC Python files
- `protoc-gen-go` (install with `go install google.golang.org/protobuf/cmd/protoc-gen-go@latest`)
  to generate gRPC Go files

Once you have these tools installed, execute:

```sh
# compile all protofiles for python and go
make proto
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
make container
```

### Go Server

To compile the server, you need `go` version 1.16 or later.

```sh
make binary
```
