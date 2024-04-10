#!/bin/sh
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

set -ex

sudo apt-get update

sudo apt-get install \
    --no-install-recommends \
    --no-install-suggests \
    -y g++ gcc make cmake build-essential

# and we need firecracker on the machine
# download the current release
curl -fsSL -o firecracker-v1.6.0-x86_64.tgz \
    https://github.com/firecracker-microvm/firecracker/releases/download/v1.6.0/firecracker-v1.6.0-x86_64.tgz
tar -xvf firecracker-v1.6.0-x86_64.tgz
# and add the firecracker and jailer binaries
sudo mv release-v1.6.0-x86_64/firecracker-v1.6.0-x86_64 /usr/local/bin/firecracker
sudo mv release-v1.6.0-x86_64/seccompiler-bin-v1.6.0-x86_64 /usr/local/bin/jailer

