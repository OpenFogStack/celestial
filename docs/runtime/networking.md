---
layout: default
title: Networking
parent: Runtime
nav_order: 1
---

## Networking

In Celestial, all machines are equipped with a virtual network adapter that is
available within the microVM as `eth0`.
Each machine is placed in a dedicated subnet.
Machines that can communicate with each other (these are machines where a network
path exists between their corresponding satellites or ground stations) can find
each other using the DNS service described below.

All networks are subnets of the `10.0.0.0/8` network.
Networks are calculated as follows:

1. Byte is always `10` (0x0A)
2. Byte is the shell identifier, or `255` (`0xFF`) for ground stations
3. Byte is the satellite's identifier in the shell, shifted right by 6 bits (e.g.
   `12` or `0x0C` for satellite `831`)
4. Byte is the satellite's identifier in the shell, shifted left by 2 bits (e.g.
   `252` or `0xFC` for satellite `831`)

Within this network, the network + 1 is the gateway IP and network + 2 is the microVMs
IP.
The network has a `/30` network mask, hence only those two are available.

`tc` is used to manipulate network performance between machines.
WireGuard is used to link machines on different hosts.
