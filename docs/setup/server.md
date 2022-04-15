---
layout: default
title: Server
parent: Setup
nav_order: 2
---

## Server

You can run as many servers as you want, Celestial will inform you whether
resources are appropriately allocated for the microVMs you're planning to run.

We recommend that you run identical servers, that just makes it easier.
How about cloud VMs?

In order to run Celestial, make sure each server has the following:

- a Linux-based operating system with:
  - one main network interface (default name is `ens4`, but you can configure this)
  - WireGuard installed and available as `wg`
  - `iptables` and `ipset`
- virtualization capabilities
- the Firecracker binary on its `PATH` (available [here](https://github.com/firecracker-microvm/firecracker/releases))
- port 1969 available for the client (configurable)
- port 1970 available for other servers (configurable)

We recommend Ubuntu 18.04 on Google Cloud because that's what we test on.
Ideally, your machine should also not be in any `10.0.0.0/8` network, as that
could lead to conflicts with the Firecracker networks.

### A Word On Virtualization Capabilities

To use Firecracker on cloud VMs, those must support what is called _nested virtualization_.
Not all cloud VMs support this, e.g., on AWS EC2 you must use `metal` instances.

You can read more about this setup [here](https://github.com/firecracker-microvm/firecracker/blob/main/docs/dev-machine-setup.md).

#### Example: Creating an Ubuntu 18.04 Image in Google Cloud

This uses the `gcloud` shell:

```sh
# set configuration
# use Frankfurt as a region
$ FC_REGION=europe-west3
$ FC_ZONE=europe-west3-c

$ gcloud config set compute/region ${FC_REGION}
Updated property [compute/region].

$ gcloud config set compute/zone ${FC_ZONE}
Updated property [compute/zone].

# set a name for the image
$ FC_VDISK=disk-ubnt
$ FC_IMAGE=ubnt-nested-kvm

# create disk
$ gcloud compute disks create ${FC_VDISK} \
    --image-project ubuntu-os-cloud --image-family ubuntu-1804-lts
Created [https://www.googleapis.com/compute/v1/projects/[PROJECT-ID]/zones/europe-west3-c/disks/disk-ubnt].
NAME       ZONE            SIZE_GB  TYPE         STATUS
disk-ubnt  europe-west3-c  10       pd-standard  READY

# create image from disk with associated nested virtualization option
$ gcloud compute images create ${FC_IMAGE} --source-disk ${FC_VDISK} \
    --source-disk-zone ${FC_ZONE} \
    --licenses "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
Created [https://www.googleapis.com/compute/v1/projects/[PROJECT-ID]/global/images/ubnt-nested-kvm].
NAME              PROJECT           FAMILY  DEPRECATED  STATUS
ubnt-nested-kvm   [PROJECT-ID]                           READY
```

Once you have done that, start a VM with that image.
Enter it with `ssh` and enable access to `/dev/kvm`, then check that it's working:

```sh
$ sudo setfacl -m u:${USER}:rw /dev/kvm
$ [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo "OK" || echo "FAIL"
OK
```

### Compiling the Celestial Binary

We don't make compiled versions of the server software available at the moment.
To compile the celestial binary, use `go` >1.16:

```sh
GOOS=linux GOARCH=amd64 go build -o celestial.bin .
```

This should output a `celestial.bin` binary for you.

### Running the Server Software

Once you have the `celestial` binary available, you can run it with:

```sh
sudo ./celestial.bin
```

Root access is required to set up all the networking between machines.
Again, don't run this on your local computer if you don't know what you're doing.

You can configure some basic stuff using command line flags:

```text
Usage of ./celestial.bin:
  -dns-service-port int
        Port to bind DNS service server to (default 53)
  -eager
        Eager initialization -- start each machine at the beginning instead of
        lazily (default off)
  -info-server-port int
        Port to bind info server to (default 80)
  -network-interface string
        Name of your main network interface (default "ens4")
  -peering-port int
        Port to bind peering to (default 1970)
  -port int
        Port to bind to (default 1969)
```
