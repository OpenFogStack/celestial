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

ARCH=amd64
OS=linux

PROJECT_NAME := "celestial"
PKG := "github.com/OpenFogStack/$(PROJECT_NAME)"
GO_FILES := $(shell find . -name '*.go' | grep -v _test.go)

.PHONY: build proto ebpf celestial-make rootfsbuilder

build: celestial.bin

proto: proto/celestial/celestial.pb.go proto/celestial/celestial_grpc.pb.go proto/celestial/celestial_pb2.py proto/celestial/celestial_pb2.pyi proto/celestial/celestial_pb2_grpc.py proto/celestial/celestial_pb2_grpc.pyi
proto/celestial/celestial.pb.go proto/celestial/celestial_grpc.pb.go proto/celestial/celestial_pb2.py proto/celestial/celestial_pb2.pyi proto/celestial/celestial_pb2_grpc.py proto/celestial/celestial_pb2_grpc.pyi: proto/celestial/celestial.proto proto/celestial/__init__.py ## build proto files
	@protoc -I proto/celestial/ celestial.proto --go_out=proto/celestial --go_opt=paths=source_relative --go-grpc_out=proto/celestial --go-grpc_opt=require_unimplemented_servers=false,paths=source_relative
	@python3 -m grpc_tools.protoc -I proto/celestial/ --python_out=proto/celestial --grpc_python_out=proto/celestial --mypy_out=proto/celestial celestial.proto --mypy_grpc_out=proto/celestial

ebpf: pkg/ebpfem/edt_bpfel_x86.go pkg/ebpfem/edt_bpfel_x86.o ## build ebpf files
pkg/ebpfem/edt_bpfel_x86.go pkg/ebpfem/edt_bpfel_x86.o: pkg/ebpfem/ebpfem.go pkg/ebpfem/ebpf/net.c pkg/ebpfem/ebpf/headers/helpers.h pkg/ebpfem/ebpf/headers/maps.h ## build ebpf files
    ## apt-get install -y clang gcc-multilib libbpf-dev llvm
	go generate ./pkg/ebpfem

celestial.bin: go.mod go.sum celestial.go ${GO_FILES} ## build go binary
	GOOS=${OS} GOARCH=${ARCH} go build -o celestial.bin .

celestial-make: compile.Dockerfile ## build the compile container
	docker build --platform ${OS}/${ARCH} -f $< -t $@ .

rootfsbuilder: ## build the rootfs builder container
	cd ./builder ; make rootfsbuilder ; cd ..
