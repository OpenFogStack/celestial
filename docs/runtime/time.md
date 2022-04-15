---
layout: default
title: Time
parent: Runtime
nav_order: 2
---

## Time

Since the user provides kernel and root filesystem, all time and clock control is
in their hands.

If you're running experiments on Celestial you might be interested in an accurate
wall clock in your VMs, e.g. to measure network delays.
There are two ways to configure clock synchronization in your VMs: NTP and PTP.
You can read a bit more about that in [the Firecracker documentation](https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md#my-guest-wall-clock-is-drifting-how-can-i-fix-it).

### NTP

NTP is relatively simple to set up, the operating system on your root filesystem
is probably set up for it to some extent.
Choose a time-server to synchronize with and off you go.

### PTP

The downside of NTP is that all your machines synchronize with an external time-server.
If you run hundreds of machines, that's quite a bit of network traffic.

PTP synchronizes your machines with the host's time using cheap para-virtualized
KVM calls.
It's a lot more accurate as well (on one machine - if you run Celestial across
multiple serves, make sure to synchronize those too, and expect some inaccuracies!).

The downside here is that both hour host and guest must support it.

On a host side, we have seen that it works with `Amazon Linux 2` and
`Ubuntu 18.04 LTS`, but we weren't able to get it to work with Debian.
There is probably a way to find out if your host supports it, but maybe you just
need to try it out.

On a client side, you need to configure a time synchronization service and have
PTP support enabled in your kernel with these lines in your kernel config:

```config
CONFIG_PTP_1588_CLOCK=y
CONFIG_PTP_1588_CLOCK_KVM=y
```

Once you boot, you should see a `/dev/ptp0` device (if you don't your host probably
doesn't support it).

You then need to configure that device for your time keeping service, e.g. in `chrony`:

```sh
echo "refclock PHC /dev/ptp0 poll 3 dpoll -2 offset 0" > /etc/chrony/chrony.conf
```

You should then restart the `chrony` daemon:

```sh
service chronyd restart
```

To force time synchronization in the guest, use:

```sh
$ chronyc -a makestep
200 OK

$ chronyc tracking
Reference ID    : 50484330 (PHC0)
Stratum         : 1
Ref time (UTC)  : Mon May 10 11:58:30 2021
System time     : 0.000000122 seconds fast of NTP time
Last offset     : -0.000005912 seconds
RMS offset      : 0.000003069 seconds
Frequency       : 83.203 ppm slow
Residual freq   : -0.177 ppm
Skew            : 0.502 ppm
Root delay      : 0.000000001 seconds
Root dispersion : 0.000010668 seconds
Update interval : 7.9 seconds
Leap status     : Normal
```
