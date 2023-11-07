PWD=$(shell pwd)

.PHONY: all container

all: container-%

container-%: Dockerfile
	@docker build --platform=linux/amd64 --build-arg KERNEL_VERSION=$* -t kernelbuilder:v$* .

config-%: container-%
	@docker run --platform=linux/amd64 -it --rm -v ${PWD}:/input kernelbuilder:v$* /input/config.sh /input $*

vmlinux-%.bin: container-% config-%
	@docker run --platform=linux/amd64 -it --rm -v ${PWD}:/input kernelbuilder:v$* /input/compile.sh /input $* $@
