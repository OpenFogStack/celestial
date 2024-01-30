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

# for celestial coordinator: python + python-pip + python dependencies
sudo apt-get install \
    --no-install-recommends \
    --no-install-suggests \
    -y python3 python3-pip python3-dev g++ gcc make cmake build-essential

python3 -m pip install pip -U
python3 -m pip install -r requirements.txt -U

# for host
# we need the /celestial folder available on the hosts
sudo mkdir -p /celestial

# we also need wireguard and ipset as dependencies
sudo apt-get install \
    --no-install-recommends \
    --no-install-suggests \
    -y wireguard ipset

# and we need firecracker on the machine
# download the current release
curl -fsSL -o firecracker-v1.6.0-x86_64.tgz \
    https://github.com/firecracker-microvm/firecracker/releases/download/v1.6.0/firecracker-v1.6.0-x86_64.tgz
tar -xvf firecracker-v1.6.0-x86_64.tgz
# and add the firecracker and jailer binaries
sudo mv release-v1.6.0-x86_64/firecracker-v1.6.0-x86_64 /usr/local/bin/firecracker
sudo mv release-v1.6.0-x86_64/seccompiler-bin-v1.6.0-x86_64 /usr/local/bin/jailer

sudo mv vmlinux-5.12.bin /celestial/vmlinux.bin

# sometimes it can also be helpful to increase process and file handler
# limits on your host machines:
cat << END > ./limits.conf
* soft nofile 64000
* hard nofile 64000
root soft nofile 64000
root hard nofile 64000
* soft nproc 64000
* hard nproc 64000
root soft nproc 64000
root hard nproc 64000
END

sudo mv ./limits.conf /etc/security/limits.conf
