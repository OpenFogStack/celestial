---
layout: default
title: Guest Kernel
nav_order: 8
---


## Building a Kernel

Compiling your own Linux is not actually that hard.
You will want to do this if the `hello-world` kernel provided by Firecracker lacks
options you need or if you want to use a newer kernel version.
This documentation is adapted from the [Firecracker developer guide](https://github.com/firecracker-microvm/firecracker/blob/main/docs/rootfs-and-kernel-setup.md).
We recommend using the `v5.12` kernel configuration we provide in the [`./kernel`](https://github.com/OpenFogStack/celestial/blob/kernel/config-5.12)
directory.

You need three things:

1. Kernel sources
2. A tool chain
3. A configuration file

You can get the kernel sources by cloning the Linux repository:

```sh
# warning! this is about 3.5GB in size so sit back and wait
git clone https://github.com/torvalds/linux.git linux.git
cd linux.git

# then checkout the version you want, e.g. v4.19
git checkout v4.19
```

You also need a few things for your tool chain.
The details depend on your distribution, here are the packages needed on Ubuntu 18.04:

```sh
sudo apt-get install build-essential linux-source bc kmod cpio flex \
    libncurses5-dev libelf-dev libssl-dev bison -y
```

Finally, your config file is used to configure your kernel.
We recommend our [`./kernel/config-5.12`](https://github.com/OpenFogStack/celestial/blob/kernel/config-5.12)
for the `v5.12` configuration.
You should name your config file `.config` and place it in the `linux.git` folder.

You can modify this configuration with the `menuconfig` tool:

```sh
make menuconfig
```

Save your configuration and build your kernel with:

```sh
make vmlinux
```

Pro-tip: use `make vmlinux -j [NO_THREADS]` to multi-thread your compilation.

This takes a few minutes.
There you go, now you have your `vmlinux` file that you can use as a kernel.

If you want to use Docker within your microVM, you need to build a kernel that has
support for everything Docker requires.
Check out [this repository](https://github.com/njapke/docker-in-firecracker) for
information on how to do that.
