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
