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

# For normal use, we recommend running Make commands with the celestial-make
# Docker container, as that has all the right depencies installed. Especially
# cumbersome are gRPC and protobuf, which make breaking changes without a
# proper versioning scheme. Simply replace `make` with `./celestial-make`.

ARCH=amd64
OS=linux

PROJECT_NAME := "celestial"
PKG := "github.com/OpenFogStack/$(PROJECT_NAME)"
GO_FILES := $(shell find . -name '*.go' | grep -v _test.go)

.PHONY: build proto ebpf containers celestial-make satgen-docker rootfsbuilder

build: celestial.bin

containers: celestial-make satgen-docker rootfsbuilder

proto: proto/celestial/celestial.pb.go proto/celestial/celestial_grpc.pb.go proto/celestial/celestial_pb2.py proto/celestial/celestial_pb2.pyi proto/celestial/celestial_pb2_grpc.py proto/celestial/celestial_pb2_grpc.pyi
proto/celestial/celestial.pb.go proto/celestial/celestial_grpc.pb.go proto/celestial/celestial_pb2.py proto/celestial/celestial_pb2.pyi proto/celestial/celestial_pb2_grpc.py proto/celestial/celestial_pb2_grpc.pyi: proto/celestial/celestial.proto proto/celestial/__init__.py ## build proto files
	@protoc -I proto/celestial/ celestial.proto --go_out=proto/celestial --go_opt=paths=source_relative --go-grpc_out=proto/celestial --go-grpc_opt=require_unimplemented_servers=false,paths=source_relative
	@python3 -m grpc_tools.protoc -I proto/celestial/ --python_out=proto/celestial --grpc_python_out=proto/celestial --mypy_out=proto/celestial celestial.proto --mypy_grpc_out=proto/celestial

ebpf: pkg/ebpfem/edt_x86_bpfel.go pkg/ebpfem/edt_x86_bpfel.o ## build ebpf files
pkg/ebpfem/edt_x86_bpfel.go pkg/ebpfem/edt_x86_bpfel.o: pkg/ebpfem/ebpfem.go pkg/ebpfem/ebpf/net.c pkg/ebpfem/ebpf/headers/helpers.h pkg/ebpfem/ebpf/headers/maps.h ## build ebpf files
    ## apt-get install -y clang gcc-multilib libbpf-dev llvm
	@go generate ./pkg/ebpfem

celestial.bin: go.mod go.sum celestial.go ${GO_FILES} ## build go binary
	GOOS=${OS} GOARCH=${ARCH} go build -o celestial.bin .

celestial-make: compile.Dockerfile ## build the compile container
	@docker build --platform ${OS}/${ARCH} -f $< -t $@ .

satgen-docker: satgen.Dockerfile satgen.py requirements.txt celestial/*.py ## build the satgen container
	@docker build -f $< -t $@ .

rootfsbuilder: builder/build-script.sh builder/Dockerfile builder/fcinit.c builder/inittab builder/interfaces builder/run-user-script builder/prepare.sh builder/ceinit ## build the rootfs builder container
	@docker build --platform=linux/amd64 -t $@:latest builder/
