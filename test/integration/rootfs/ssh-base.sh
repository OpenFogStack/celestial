#!/bin/sh

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

# the base script install all the necessary dependencies during root
# filesystem compilation

apk add openssh
# rc-update add sshd

mkdir -p /home/root/.ssh
chmod 700 /home/root/.ssh
cat id_ed25519.pub > /home/root/.ssh/authorized_keys
chmod 600 /home/root/.ssh/authorized_keys
# # echo "root:root" | chpasswd
ls -a /home/root/
passwd root -d root
