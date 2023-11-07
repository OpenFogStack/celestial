#!/bin/sh

# install dependencies
apk -X "http://dl-5.alpinelinux.org/alpine/latest-stable/main" -U --allow-untrusted --root / --initdb add \
    openrc \
    ca-certificates \
    alpine-base \
    util-linux \
    iptables \
    iproute2 \
    strace \
    attr \
    grep

# link rc services
ln -sf /etc/init.d/devfs        /etc/runlevels/boot/devfs
ln -sf /etc/init.d/procfs       /etc/runlevels/boot/procfs
ln -sf /etc/init.d/sysfs        /etc/runlevels/boot/sysfs

ln -sf networking               /etc/init.d/net.eth0
ln -sf /etc/init.d/networking   /etc/runlevels/default/networking
ln -sf /etc/init.d/net.eth0     /etc/runlevels/default/net.eth0

# disable modules
echo rc_want="!modules">> /etc/rc.conf

passwd root -d root
exit
