#!/bin/sh

# install dependencies
apk -X "http://dl-5.alpinelinux.org/alpine/latest-stable/main" -U --allow-untrusted --root / --initdb add \
    openrc \
    ca-certificates \
    alpine-base \
    util-linux \
    iptables \
    iproute2 \
    grep

# link rc services
ln -sf /etc/init.d/devfs        /etc/runlevels/boot/devfs
ln -sf /etc/init.d/procfs       /etc/runlevels/boot/procfs
ln -sf /etc/init.d/sysfs        /etc/runlevels/boot/sysfs

# link and configure ttyS0 with agetty
ln -sf agetty                   /etc/init.d/agetty.ttyS0
echo "ttyS0" >>                 /etc/securetty
ln -sf /etc/init.d/agetty.ttyS0 /etc/runlevels/default/agetty.ttyS0

ln -sf networking               /etc/init.d/net.eth0
ln -sf /etc/init.d/networking   /etc/runlevels/default/networking
ln -sf /etc/init.d/net.eth0     /etc/runlevels/default/net.eth0

ln -sf /etc/init.d/local        /etc/runlevels/boot/local

# enable fcnet-setup
chown root /etc/init.d/fcnet
chmod 755 /etc/init.d/fcnet
ln -sf /etc/init.d/fcnet        /etc/runlevels/default/fcnet
chmod 755 /etc/init.d/fcnet
mv /fcnet-setup /bin/fcnet-setup

# install custom init
mv /sbin/init /sbin/openrc-init
mv /overlay-init /sbin/overlay-init
mv /init /sbin/init

# disable modules
echo rc_want="!modules" >> /etc/rc.conf

passwd root -d root
exit
