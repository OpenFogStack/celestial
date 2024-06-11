---
layout: default
title: Known Limitations
nav_order: 7
---

## Known Limitations

These are the known limits of Celestial.
These limits are not part of the concept behind Celestial but rather purely
specific to the implementation.
Further development may lead to a change in these limits.

| Component             | Limit                   | Reason                                                                                                                                                                       |
| --------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Client                | 1                       | Satellite simulation requires fast I/O between components                                                                                                                    |
| Servers               | None                    | Hosts peer over the internet and machines are randomly distributed across them. In practice there is no benefit if you use more servers than total nodes in your simulation. |
| Shells                | 254                     | Limited by IP network space calculation.                                                                                                                                     |
| Satellites per Shell  | 16,384                  | Limited by IP network space calculation.                                                                                                                                     |
| vCPU, Memory, Storage | depends on your servers | --                                                                                                                                                                           |

Note also that latency between microVMs can only be set to a minimum of the physical
RTT of the VMs.

### Process and File Handler Limits

Depending on your Linux distribution, you may run into the process or file handler
limits when starting many microVMs.
This is not a limit of Celestial but rather a limit set in your operating system.
On Linux, you can change these security limits in the `/etc/security/limits.conf`
file:

```conf
* soft nofile 64000
* hard nofile 64000
root soft nofile 64000
root hard nofile 64000
* soft nproc 64000
* hard nproc 64000
root soft nproc 64000
root hard nproc 64000
```

This sets both file handler and process limits to 64,000, which should be enough
for most use cases.

### ARP Cache

To avoid garbage collection in the ARP cache, you may need to resize ARP cache
thresholds depending on the number of machines you plan to run.

```sh
sudo sysctl -w net.ipv4.neigh.default.gc_thresh1=2048
sudo sysctl -w net.ipv4.neigh.default.gc_thresh2=4096
sudo sysctl -w net.ipv4.neigh.default.gc_thresh3=8192
```

### Randomness

Each Linux machine has sources of randomness on `/dev/random` and `/dev/urandom`.
If your application depends on randomness (most do, actually: including simple things
such as TLS) you will notice that your applications need a long time to start if
you have many machines running concurrently.
The problem is that the randomness pool is easily depleted with many VMs starting
concurrently.
In some cases, you will receive a log statement such as `[random]: crng init done`
some few minutes after boot.

If you do not require cryptographically secure entropy, a good idea is to let your
VMs trust the hosts CPU for randomness.
This requires a Linux kernel of version >4.19 with the `CONFIG_RANDOM_TRUST_CPU`
option set.
You can read more about this issue [here](https://github.com/firecracker-microvm/firecracker/blob/main/docs/snapshotting/random-for-clones.md)
and [here](https://github.com/firecracker-microvm/firecracker/issues/663).

### Docker Networking

There may be an issue where having Docker installed on your host machine
prevents Firecracker networking to work.
Even uninstalling Docker did not help us with this.
If you have Docker installed on your host server, find a fresh host server to
run Celestial on.

### Memory

Celestial suspends microVMs for satellites that move outside the bounding box.
Suspending rather than stopping lets Celestial resume (unsuspend) those microVMs
seamlessly if a satellite moves back into the bounding box (usually after completing)
an orbit.
Firecracker suspends processes to memory, i.e., while the process no longer performs
any work, any memory pages claimed by the microVM will remain in memory.
For longer emulation runs, this can of course clutter your available memory with
useless information.
It is advisable to enable swapping on your host machines with a sufficiently
large swap space.
While swapping should normally not be used on servers, this is a different case:
For suspended microVMs, your host can simply move the unused memory pages to
your hard drive in case of memory pressure.
On your host, enable memory swapping like this:

```sh
# create an, e.g., 64GB swap file
sudo fallocate -l 64G /swapfile
# set permissions
sudo chmod 600 /swapfile
# make this file a swapping area
sudo mkswap /swapfile
# enable swapping
sudo swapon /swapfile
```

These settings do not persist across reboots.
