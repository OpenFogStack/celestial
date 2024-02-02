#!/bin/bash

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

# $1 = filename for your rootfs

set -ex

mkdir -p ./tmp

cp -r  minirootfs/* ./tmp/

# if you don't do this, apk can't access its repositories
cp /etc/resolv.conf ./tmp/etc/resolv.conf
# mount /dev/random and /dev/urandom (needed for some operations, such as git)
mkdir -p ./tmp/dev
touch ./tmp/dev/random
mount --rbind /dev/random ./tmp/dev/random
mount --make-rslave ./tmp/dev/random
touch ./tmp/dev/urandom
mount --rbind /dev/urandom ./tmp/dev/urandom
mount --make-rslave ./tmp/dev/urandom

# copy the necessary files
cp interfaces ./tmp/etc/network/interfaces
cp inittab ./tmp/etc/inittab
cp run-user-script ./tmp/sbin/run-user-script
cp fcinit ./tmp/sbin/fcinit
cp ceinit ./tmp/sbin/ceinit
cp /app.sh ./tmp/app.sh

if [ -d "/files" ]; then
    cp -rv /files/* ./tmp/
fi

cp prepare.sh ./tmp/prepare.sh
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

# now delete the nameserver config again
rm ./tmp/etc/resolv.conf
ln -s /proc/net/pnp ./tmp/etc/resolv.conf
# and unmount the devices
umount ./tmp/dev/random
rm ./tmp/dev/random
umount ./tmp/dev/urandom
rm ./tmp/dev/urandom

rm ./tmp/prepare.sh

mksquashfs ./tmp rootfs.img -noappend

mv rootfs.img /opt/code/"$1"
