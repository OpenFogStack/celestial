---
layout: default
title: Application
parent: Runtime
nav_order: 3
---

## Your Application

In order to deploy your application to your microVMs, Celestial lets you specify
kernels and filesystems for different machines.
That means that you will need to provide your own kernel and filesystem.

These will need to be available on each server, so they can be loaded into Firecracker.
By default, `celestial` looks in the `/celestial` folder on the server for those
files.

You can use the example files provided by the Firecracker team for testing.
Refer to their [Getting Started Guide](https://github.com/firecracker-microvm/firecracker/blob/main/docs/getting-started.md)
to find and download them.

To deploy custom kernels and applications, refer to one of the many guides on building
these for Firecracker.
Keep in mind that you should not set custom networking in your machine so that Celestial
can take care of that.

### Building a Kernel

Compiling your own Linux is not actually that hard.
You will want to do this if the `hello-world` kernel provided by Firecracker lacks
options you need or if you want to use a newer kernel version.
This documentation is adapted from the [Firecracker developer guide](https://github.com/firecracker-microvm/firecracker/blob/main/docs/rootfs-and-kernel-setup.md).

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
The Firecracker team has a [recommended starting config](https://github.com/firecracker-microvm/firecracker/blob/main/resources/microvm-kernel-x86_64.config)
available that you can use.
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

### Building a Filesystem

You also need a filesystem that has your application and any dependencies.
You can either create this directly on your machine or using a Docker container.
Celestial uses union filesystems.
Instead of creating thousands of copies of the same disk image, we have one that
has all the data but is read-only, and we then create a writable overlay for each
machine, which helps with storage.

#### Directly on Your Machine

This documentation is adapted from the [UNIK documentation](https://github.com/solo-io/unik/blob/master/docs/compilers/firecracker/make_artifacts.md)
with additional help by [Nils](https://github.com/njapke/overlayfs-in-firecracker).

The easiest way to get started with this is to use a base filesystem that is already
finished.
To that end, we'll be extracting files from alpine Linux.
Pull an alpine Linux image and extract that

```sh
# get our base filesystem
wget http://dl-cdn.alpinelinux.org/alpine/v3.8/releases/x86_64/alpine-minirootfs-3.8.1-x86_64.tar.gz

# extract
mkdir -p minirootfs
tar xzf ../alpine-minirootfs-3.8.1-x86_64.tar.gz -C minirootfs

# create a new empty file system and copy
mkdir tmp
cp -r minirootfs/* tmp/
```

While this would probably work, we can do a bit of additional work.
First, we set a name server (Cloudflare's `1.1.1.1` service in this case) so that
we can install packages:

```sh
echo nameserver 1.1.1.1 | sudo tee ./tmp/etc/resolv.conf
```

Now we need three files: network interface descriptors, an `inittab` that will configure
our init system (OpenRC), and a start script.

`interfaces`:

```text
auto eth0
iface eth0 inet manual
```

`inittab`:

```text
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::wait:/sbin/openrc default

# Set up a couple of getty's
# tty1::respawn:/sbin/getty 38400 tty1
# tty2::respawn:/sbin/getty 38400 tty2
# tty3::respawn:/sbin/getty 38400 tty3
# tty4::respawn:/sbin/getty 38400 tty4
# tty5::respawn:/sbin/getty 38400 tty5
# tty6::respawn:/sbin/getty 38400 tty6

# Put a getty on the serial port
ttyS0::respawn:/bin/ash /start.sh
# ttyS0::respawn:/sbin/getty -L ttyS0 115200 vt100

# Stuff to do for the 3-finger salute
::ctrlaltdel:/sbin/reboot

# Stuff to do before rebooting
::shutdown:/sbin/openrc shutdown
```

`start-script`:

```sh
# in addition to the base file system, here we mount our overlay
/bin/mount -t ext4 "/dev/$overlay_root" /overlay
mkdir -p /overlay/root /overlay/work

/bin/mount \
    -o noatime,lowerdir=/,upperdir=/overlay/root,workdir=/overlay/work \
    -t overlay "overlayfs:/overlay/root" /mnt
pivot_root /mnt /mnt/rom

# do some minimal init
rc-service sysfs start
rc-service networking start

# run program. the firecracker compiler would place this here.
/usr/local/bin/program

# shutdown firecracker
reboot
```

We need to copy these files into our custom filesystem as well:

```sh
cat interfaces | sudo tee ./tmp/etc/network/interfaces
cat inittab | sudo tee ./tmp/etc/inittab
cat start-script | sudo tee ./tmp/start.sh

# these are the mount points we need to create
sudo mkdir -p ./tmp/overlay/root \
    ./tmp/overlay/work \
    ./tmp/mnt \
    ./tmp/rom
```

You can see from the `start-script` that it runs a program called `/usr/local/bin/program`.
Here, you can put whatever application you want to run.
But be aware that you also need to copy those binaries to your filesystem at this
point.

Now, we'll move inside the filesystem to make a few changes, namely setting a root
password and installing our init system (OpenRC) and CA certificates.
We'll be using `chroot` for this purpose:

```sh
# move into the filesystem with chroot
sudo chroot tmp/ /bin/sh
# set a password for the root user
passwd root -d root
# update apk repositories and package lists
apk update
# install openrc and ca-certificates
apk add -u openrc ca-certificates
# leave chroot
exit
```

Now all we need to do is build a `squashfs` filesystem from our files:

```sh
sudo mksquashfs ./tmp rootfs.img -noappend
```

Then you can use `rootfs.img` as a root filesystem for your machines.

#### Using Docker

Alternatively, you can also create a filesystem using Docker.
Check the `builder` directory for that.

##### Build the Docker Container

Before you can get to building your root filesystem, you need to build the container
from within this directory:

```sh
docker build -t rootfsbuilder .
```

##### Prepare your app.sh

Your `app.sh` will be run with `/bin/sh` once the microVM starts.
As soon as the script ends, your microVM will shut down automatically.
To run a simple binary (placed in filesystem root as `/main`), this is what your
`app.sh` could look like:

```sh
#!/bin/sh

# this optionally sets the gateway as your nameserver to be able to resolve internal
# .celestial IP addresses
IP=$(/sbin/ip route | awk '/default/ { print $3 }')
echo nameserver $IP > /etc/resolv.conf

/main
```

##### Building your root filesystem

To build your root filesystem, use the container we have just created:

```sh
docker run --rm --privileged -v [PATH_TO_APP.SH]:/client.sh \
    -v [OPTIONAL_PATH_TO_ADDITIONAL_FILES]:/files \
    -v [OPTIONAL_PATH_TO_PREPARATION_SCRIPT]:/base.sh \
    -v $(pwd):/opt/code rootfsbuilder [OUTPUT]
```

You must run the container as `--privileged` to allow it to mount the new filesystem.

The important part is how the files are mapped into the container.
Your `app.sh` must be mounted as a volume in `/app.sh`.

Any files in the directory mounted as `/files` will be copied to the root of your
root filesystem.

A script mounted as `base.sh` will be executed in your root filesystem. You can
use that to install additional dependencies that you don't want to add at runtime.

`/opt/code` is the internal folder where your final root filesystem will be placed.
In this case, it will appear in the current working directory on your host.
