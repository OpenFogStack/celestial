---
layout: default
title: DNS API
nav_order: 4
parent: Runtime
---

## DNS API

In addition to finding information about itself, a machine can also find the network
address of another machine by querying the provided DNS service.
This service is available at the machine's gateway on port 53 using `systemd-resolved`
on the host.
This is set as the default DNS server in Celestial.
It supports only `A` requests for the custom `.celestial` TLD.

Records are in the form `[ID].[SHELL].celestial` for satellites and `[NAME].gst.celestial`
for ground stations.
Note that all addresses are resolved if the machine is known, regardless of whether
that machine is active or can be accessed.

When using our builder, you can also use the hostname `info.celestial` as the address
of the info server, alas the gateway IP for a microVM.
