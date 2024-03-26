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

# mount /dev/random and /dev/urandom (needed for some operations, such as git)
mkdir -p ./rootfs/dev
touch ./rootfs/dev/random
mount --rbind /dev/random ./rootfs/dev/random
mount --make-rslave ./rootfs/dev/random
touch ./rootfs/dev/urandom
mount --rbind /dev/urandom ./rootfs/dev/urandom
mount --make-rslave ./rootfs/dev/urandom

# # copy the necessary files
cp /app.sh ./rootfs/app.sh

if [ -d "/files" ]; then
    cp -rv /files/* ./rootfs/
fi

chroot ./rootfs/ /bin/sh /prepare.sh
rm ./rootfs/prepare.sh

if [ -f "/base.sh" ]; then
    cp /base.sh ./rootfs/base.sh
    chroot ./rootfs/ /bin/sh base.sh
    rm ./rootfs/base.sh
fi

# these are the mount points we need to create
mkdir -p ./rootfs/overlay/root \
    ./rootfs/overlay/work \
    ./rootfs/mnt \
    ./rootfs/rom

# now delete the nameserver config again
rm ./rootfs/etc/resolv.conf
ln -s /proc/net/pnp ./rootfs/etc/resolv.conf
# and unmount the devices
umount ./rootfs/dev/random
rm ./rootfs/dev/random
umount ./rootfs/dev/urandom
rm ./rootfs/dev/urandom

mksquashfs ./rootfs rootfs.img -noappend

mv rootfs.img /opt/code/"$1"
