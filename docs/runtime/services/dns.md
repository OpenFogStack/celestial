---
layout: default
title: DNS API
parent: Services
grand_parent: Runtime
nav_order: 2
---

## DNS API

In addition to finding information about itself, a machine can also find the network
address of another machine by querying the provided DNS service.
This service is available at the machine's gateway on port 53.
It supports only `A` requests for the custom `.celestial` TLD.

Records are in the form `[ID].[SHELL].celestial` for satellites and `[NAME].gst.celestial`
for ground stations.
Note that all addresses are resolved if the machine is known, regardless of whether
that machine is active or can be accessed.
