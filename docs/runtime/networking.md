---
layout: default
title: Networking
nav_order: 1
parent: Runtime
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
1. Byte is the shell identifier, `0` for ground stations and starting at `1` for
    satellite shells
1. Byte is the satellite's identifier in the shell, shifted right by 6 bits (e.g.
   `12` or `0x0C` for satellite `831`)
1. Byte is the satellite's identifier in the shell, shifted left by 2 bits (e.g.
   `252` or `0xFC` for satellite `831`)

Within this network, the network + 1 is the gateway IP and network + 2 is the microVMs
IP.
The network has a `/30` network mask, hence only those two are available.

eBPF programs and `tc` are used to modify network latency between microVMs.
WireGuard is used to link machines on different hosts.
