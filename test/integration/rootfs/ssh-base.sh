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

# the base script install all the necessary dependencies during root
# filesystem compilation
# configure ssh

apk -U --allow-untrusted --root / add openssh

ln -sf sshd                     /etc/init.d/sshd.eth0
ln -sf /etc/init.d/sshd.eth0    /etc/runlevels/default/sshd.eth0

mkdir -m 0600 -p /root/.ssh/
ssh-keygen -f /root/.ssh/id_rsa -N ""
ssh-keygen -A
cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys

cat >> /etc/conf.d/sshd << EOF
sshd_disable_keygen="yes"
rc_need="net.eth0"
EOF

sed -E -i /etc/ssh/sshd_config \
	-e "/^[# ]*PermitRootLogin .+$/d" \
	-e "/^[# ]*PermitEmptyPasswords .+$/d" \
	-e "/^[# ]*PubkeyAuthentication .+$/d"

	echo "
PermitRootLogin yes
PermitEmptyPasswords yes
PubkeyAuthentication yes
" | tee -a /etc/ssh/sshd_config >/dev/null

cat id_ed25519.pub >> /root/.ssh/authorized_keys

# add iperf3
apk -U --allow-untrusted --root / add iperf3