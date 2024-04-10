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

TAP_NAME="ce-tap0"
GUEST_IFACE="eth0"
GUEST_IP="10.1.0.2"
GUEST_NETMASK="255.255.255.252"
GUEST_NETMASK_CIDR="30"
GUEST_MAC="AA:FC:00:00:00:01"
HOST_IP="10.1.0.1"

INTERFACE_NAME=$(ip -o -4 route show to default | awk '{print $5}')

sudo ip tuntap add "$TAP_NAME" mode tap

sudo ip addr add $HOST_IP/$GUEST_NETMASK_CIDR dev "$TAP_NAME"
sudo ip link set "$TAP_NAME" up

sudo sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv4.conf.all.forwarding=1
sudo sysctl -w net.ipv4.conf.$TAP_NAME.proxy_arp=1

sudo iptables -t nat -A POSTROUTING -o "$INTERFACE_NAME" -j MASQUERADE
sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i "$TAP_NAME" -o "$INTERFACE_NAME" -j ACCEPT

# ensure tsc time source
sudo sh -c "echo 'tsc' > /sys/devices/system/clocksource/clocksource0/current_clocksource"

# allow DNS
mkdir -p /etc/systemd/resolved.conf.d
cat <<EOF > /etc/systemd/resolved.conf.d/celestial-microvm.conf
[Resolve]
DNSStubListenerExtra=$HOST_IP
EOF

FC_SOCKET_PATH="/tmp/firecracker.socket"
KERNEL_PATH=$(pwd)/vmlinux.bin
ROOTFS_PATH=$(pwd)/ssh.img
OVERLAY_PATH=$(pwd)/overlay.ext4

# create the overlay
dd if=/dev/zero of="$OVERLAY_PATH" conv=sparse bs=1M count=10000
mkfs.ext4 "$OVERLAY_PATH"

firecracker --api-sock "$FC_SOCKET_PATH" &
FC_PID=$!

curl --unix-socket "$FC_SOCKET_PATH" -i \
    -X PUT 'http://localhost/boot-source'   \
    -H 'Accept: application/json'           \
    -H 'Content-Type: application/json'     \
    -d "{
        \"kernel_image_path\": \"${KERNEL_PATH}\",
        \"boot_args\": \"init=/sbin/ceinit ro console=ttyS0 noapic acpi=off reboot=k panic=1 random.trust_cpu=on pci=off tsc=reliable quiet ipv6.disable=1 overlay_root=vdb loglevel=3 i8042.noaux i8042.nomux i8042.nopnp i8042.dumbkbd ip=$GUEST_IP::$HOST_IP:$GUEST_NETMASK::$GUEST_IFACE:off:$HOST_IP::\"
    }"
# ip=172.16.0.2::172.16.0.1:255.255.255.0::eth0:off:172.16.0.1::

curl --unix-socket /tmp/firecracker.socket -i \
  -X PUT 'http://localhost/drives/rootfs' \
  -H 'Accept: application/json'           \
  -H 'Content-Type: application/json'     \
  -d "{
        \"drive_id\": \"rootfs\",
        \"path_on_host\": \"${ROOTFS_PATH}\",
        \"is_root_device\": true,
        \"is_read_only\": true
   }"

curl --unix-socket /tmp/firecracker.socket -i \
  -X PUT 'http://localhost/drives/overlay' \
  -H 'Accept: application/json'           \
  -H 'Content-Type: application/json'     \
  -d "{
        \"drive_id\": \"overlay\",
        \"path_on_host\": \"${OVERLAY_PATH}\",
        \"is_root_device\": false,
        \"is_read_only\": false
   }"

curl --unix-socket /tmp/firecracker.socket -i \
  -X PUT 'http://localhost/network-interfaces/eth0' \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d "{
      \"iface_id\": \"${GUEST_IFACE}\",
      \"guest_mac\": \"${GUEST_MAC}\",
      \"host_dev_name\": \"${TAP_NAME}\"
    }"

curl --unix-socket /tmp/firecracker.socket -i  \
  -X PUT 'http://localhost/machine-config' \
  -H 'Accept: application/json'            \
  -H 'Content-Type: application/json'      \
  -d '{
      "vcpu_count": 2,
      "mem_size_mib": 1024
  }'


curl --unix-socket /tmp/firecracker.socket -i \
  -X PUT 'http://localhost/actions'       \
  -H  'Accept: application/json'          \
  -H  'Content-Type: application/json'    \
  -d '{
      "action_type": "InstanceStart"
   }'

echo "You can now ssh into the machine with 'ssh -o StrictHostKeyChecking=no -i id_ed25519 root@${GUEST_IP}'"
echo "To stop the machine, run 'reboot -f' inside the machine."

wait $FC_PID
rm -f /etc/systemd/resolved.conf.d/celestial-microvm.conf
