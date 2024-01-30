---
layout: default
title: Nested Virtualization
nav_order: 9
---

## A Word On Virtualization Capabilities

To use Firecracker on cloud VMs, those must support what is called _nested virtualization_.
Not all cloud VMs support this, e.g., on AWS EC2 you must use `metal` instances.

You can read more about this setup [here](https://github.com/firecracker-microvm/firecracker/blob/main/docs/dev-machine-setup.md).

### Example: Creating an Ubuntu 22.04 Image in Google Cloud

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
    --image-project ubuntu-os-cloud --image-family ubuntu-2204-lts
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
