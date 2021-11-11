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

FROM debian:buster

RUN apt update
RUN apt install -y wget
RUN apt install -y squashfs-tools

RUN mkdir minirootfs
RUN wget http://dl-cdn.alpinelinux.org/alpine/v3.14/releases/x86_64/alpine-minirootfs-3.14.2-x86_64.tar.gz
RUN cd minirootfs && \
    tar xzf ../alpine-minirootfs-3.14.2-x86_64.tar.gz

COPY inittab inittab
COPY interfaces interfaces
COPY start-script start-script

COPY build-script.sh /build-script.sh

ENTRYPOINT ["/bin/sh", "/build-script.sh"]