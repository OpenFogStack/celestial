#!/bin/bash

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

# $1 = filename for your rootfs

mkdir -p ./tmp

cp -r  minirootfs/* ./tmp/

# if you don't do this, apk can't access its repositories
cp /etc/resolv.conf ./tmp/etc/resolv.conf
cp interfaces ./tmp/etc/network/interfaces
cp inittab ./tmp/etc/inittab
cp start-script ./tmp/start.sh
cp /app.sh ./tmp/app.sh

if [ -d "/files" ]; then
    cp -rv /files/* ./tmp/
fi

cat > ./tmp/prepare.sh <<EOF
passwd root -d root
apk add -u openrc ca-certificates
rc-update add devfs boot
rc-update add procfs boot
rc-update add sysfs boot
exit
EOF

chroot ./tmp/ /bin/sh /prepare.sh

if [ -f "/base.sh" ]; then
    cp /base.sh ./tmp/base.sh
    chroot ./tmp/ /bin/sh base.sh
    rm ./tmp/base.sh
fi

# these are the mount points we need to create
mkdir -p ./tmp/overlay/root \
    ./tmp/overlay/work \
    ./tmp/mnt \
    ./tmp/rom

# now switch back to a public name server
echo nameserver 1.1.1.1 > ./tmp/etc/resolv.conf

rm ./tmp/prepare.sh

mksquashfs ./tmp rootfs.img -noappend

mv rootfs.img /opt/code/"$1"