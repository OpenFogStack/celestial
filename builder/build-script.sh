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

if [ -d "/files" ]; then
    cp -rv /files/* ./tmp/
fi

# if you don't do this, apk can't access its repositories
ls ./tmp/etc/
cat ./tmp/etc/resolv.conf
echo nameserver 2001:4860:4860::8888 > ./tmp/etc/resolv.conf
ping -c 4 dl-cdn.alpinelinux.org

cat > ./tmp/prepare.sh <<EOF
cat /etc/resolv.conf
ip a s
ping -c 4 151.101.114.133
ping -c 4 8.8.8.8
ping -c 4 dl-cdn.alpinelinux.org
ping -c 4 google.com
wget https://dl-cdn.alpinelinux.org/alpine/v3.14/main/x86_64/APKINDEX.tar.gz
apk -vv update
passwd root -d root
# apk add -uvv openrc ca-certificates
exit
EOF

chroot ./tmp/ /bin/sh /prepare.sh

cp interfaces ./tmp/etc/network/interfaces
cp inittab ./tmp/etc/inittab
cp start-script ./tmp/start.sh
cp /app.sh ./tmp/app.sh
# these are the mount points we need to create
mkdir -p ./tmp/overlay/root \
    ./tmp/overlay/work \
    ./tmp/mnt \
    ./tmp/rom

if [ -f "/base.sh" ]; then
    cp /base.sh ./tmp/base.sh
    chroot ./tmp/ /bin/sh base.sh
    rm ./tmp/base.sh
fi

rm ./tmp/prepare.sh

mksquashfs ./tmp rootfs.img -noappend

mv rootfs.img /opt/code/"$1"