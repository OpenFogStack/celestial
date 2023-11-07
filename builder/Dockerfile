#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
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

FROM debian:sid

ARG ALPINE_VERSION_MAJOR="3"
ARG ALPINE_VERSION_MINOR="18"
ARG ALPINE_VERSION_PATCH="0"
ARG ALPINE_ARCH="x86_64"

ARG ALPINE_VERSION="${ALPINE_VERSION_MAJOR}.${ALPINE_VERSION_MINOR}.${ALPINE_VERSION_PATCH}"

RUN apt update && \
    apt install -y \
    wget \
    squashfs-tools \
    gcc && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir minirootfs
RUN wget http://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VERSION_MAJOR}.${ALPINE_VERSION_MINOR}/releases/${ALPINE_ARCH}/alpine-minirootfs-${ALPINE_VERSION}-${ALPINE_ARCH}.tar.gz && \
    cd minirootfs && \
    tar xzf ../alpine-minirootfs-${ALPINE_VERSION}-${ALPINE_ARCH}.tar.gz && \
    cd .. && \
    rm alpine-minirootfs-${ALPINE_VERSION}-${ALPINE_ARCH}.tar.gz

COPY fcinit.c fcinit.c
RUN gcc -static -O3 -o ./fcinit fcinit.c && \
    rm fcinit.c

COPY inittab inittab
COPY interfaces interfaces
COPY run-user-script run-user-script
COPY prepare.sh prepare.sh
COPY ceinit ceinit

COPY build-script.sh /build-script.sh

ENTRYPOINT ["/bin/sh", "/build-script.sh"]
