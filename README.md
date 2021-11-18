# Celestial 🛰

Celestial is an emulator for the LEO edge.
It supports satellite servers as well as ground stations.
Each node is booted as a microVM.
Celestial scales across as many hosts as you want.

At any given time, only a subset of given satellite servers are booted,
dependent on your configured bounding box.

Celestial...

- ...creates Firecracker microVMs with your custom kernel and filesystem
- ...modifies network connections for a realistic network condition
- ...let's you define a bounding box on earth so you only need to emulate
  satellites that you're actually interested in
- ...creates/suspends microVMs as they move in to/out of your bounding box
- ...has APIs for your satellites to retrieve some meta-information

Check out [`celestial-videoconferencing-evaluation`](https://github.com/OpenFogStack/celestial-videoconferencing-evaluation)
for an example application on Celestial!
Further examples can be found in [the `examples` directory](./examples).

A word of caution: you can technically run the server-side software on any
computer you want, but it requires root access to fiddle with your network settings.
Therefore, we _highly_ encourage you to only run it on dedicated servers.
It's doing its best to clean up everything but it has to make changes to a lot
of networking settings so we can't guarantee that it doesn't destroy any of your
other stuff.

Please note that the article is still pending publication, but [a preprint is
not yet available on arXiv](https://www.youtube.com/watch?v=W2jZMtG2UAw).

A full list of our [publications](https://www.mcc.tu-berlin.de/menue/forschung/publikationen/parameter/en/)
and [prototypes](https://www.mcc.tu-berlin.de/menue/forschung/prototypes/parameter/en/)
is available on our group website.

## License

The code in this repository is licensed under the terms of the [GPLv3](./LICENSE)
license.

## Contributing

Feel free to contribute to this project in any way you see fit.
Please note that all contributions must adhere to the terms of the GPLv3 license.

If you want to contribute code, please open a pull request on this GitHub repository.
Please make sure that your code passes the quality checks.
You can use [`act`](https://github.com/nektos/act) to run GitHub actions locally.

## Compilation

Use the makefiles to compile the project.

### Protocol Buffer

You can use the pre-compiled gRPC/protobuf files or compile your own.

To compile the `proto` files (needed for communication between server and client),
you will need the following tools:

- `go`, version 1.16 or later
- `python3`, preferably Python 3.8 or later
- `protoc`, version 3.15.8 or later (on macOS, install with `brew install protobuf`)
- `mypy-protobuf` (`pip3 install mypy-protobuf`) to compile type hints for
  generated Python files
- `grpcio-tools`, version 1.37.1 or later (`pip3 install grpcio-tools`) to
  generate gRPC Python files
- `protoc-gen-go` (install with `go install google.golang.org/protobuf/cmd/protoc-gen-go@latest`)
  to generate gRPC Go files

Once you have these tools installed, execute:

```sh
# compile all protofiles for python and go
make proto
```

### Python Client

The client does not require compilation as it is interpreted.

Nevertheless, it can be useful to check for type bugs with `mypy`:

```sh
mypy celestial.py
```

You can also package that client as a Docker container if you want.
This requires the `docker` command available on your system.

```sh
make container
```

### Go Server

To compile the server, you need `go` version 1.16 or later.

```sh
make binary
```

## Setup

You will need:

- a celestial client -- this runs the satellite movement simulation and controls
  everything
- one to n celestial servers -- these host your microVMs

For obvious reasons, clients and servers need to have network connections
available between them.

### Client

You have two options to run the client software: either with Python3 or with
Docker.
Docker is obviously a bit easier but running it directly lets you activate the
cool animation as well.

In order to use the database feature (more about that in the [Services](#services)
section), you must open a TCP port of your choice on your client and it must be
reachable from your servers.

#### Python3

To run the client with Python3, make sure you have `python3` and `pip`/`pip3` installed.
We recommend setting up a virtual environment (`venv`) for Celestial:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies with:

```sh
python3 -m pip install -r requirements.txt
```

Additionally, install the `VTK` and `seaborn` packages to enable the animation
(requires a somewhat up-to-date computer):

```sh
python3 -m pip install vtk
python3 -m pip install vtk
```

Then run the client with:

```sh
python3 celestial.py [YOUR-CONFIG-FILE]
```

#### Docker

To run the client from within Docker, have `docker` installed and run:

```sh
# build the container
# this builds python-igraph from source, don't worry if it takes a while
docker build -t celestial .
# run the container with your config file mapped as a volume
docker run --rm -it -v $(pwd)/[YOUR-CONFIG-FILE]:/config.toml celestial /config.toml
```

This maps your config file as a volume within the container.
If you set `animation = true` within that config file, you will probably run
into errors, so don't do it.

If you want to enable the database, e.g., on port `8000`, instruct Docker to
forward that port:

```sh
docker run --rm -it -p8000:8000 \
    -v $(pwd)/[YOUR-CONFIG-FILE]:/config.toml \
    celestial /config.toml
```

### Server

You can run as many servers as you want, Celestial will inform you whether
resources are appropriately allocated for the microVMs you're planning to run.

We recommend that you run identical servers, that just makes it easier.
How about cloud VMs?

In order to run Celestial, make sure each server has the following:

- a Linux-based operating system with:
  - one main network interface (default name is `ens4` but you can configure this)
  - WireGuard installed and available as `wg`
  - `iptables` and `ipset`
- virtualization capabilities
- the Firecracker binary on its `PATH` (available [here](https://github.com/firecracker-microvm/firecracker/releases))
- port 1969 available for the client (configureable)
- port 1970 available for other servers (configureable)

We recommend Ubuntu 18.04 on Google Cloud because that's what we test on.
Ideally, your machine should also not be in any `10.0.0.0/8` network, as that
could lead to conflicts with the Firecracker networks.

#### A Word On Virtualization Capabilities

To use Firecracker on cloud VMs, those must support what is called _nested virtualization_.
Not all cloud VMs support this, e.g., on AWS EC2 you must use `metal` instances.

You can read more about this setup [here](https://github.com/firecracker-microvm/firecracker/blob/main/docs/dev-machine-setup.md).

##### Example: Creating a Ubuntu 18.04 Image in Google Cloud

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

#### Compiling the Celestial Binary

We don't make compiled versions of the server software available at the moment.
To compile the celestial binary, use `go` >1.16:

```sh
GOOS=linux GOARCH=amd64 go build -o celestial.bin .
```

This should output a `celestial.bin` binary for you.

#### Running the Server Software

Once you have the `celestial` binary available, you can run it with:

```sh
sudo ./celestial.bin
```

Root access is required to set up all of the networking between machines.
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

### Your Application

In order to deploy your application to your microVMs, Celestial lets you specify
kernels and filesystems for different machines.
That means that you will need to provide your own kernel and filesystem.

These will need to be available on each server so they can be loaded into Firecracker.
By default, `celestial` looks in the `/celestial` folder on the server for those
files.

You can use the example files provided by the Firecracker team for testing.
Refer to their [Getting Started Guide](https://github.com/firecracker-microvm/firecracker/blob/main/docs/getting-started.md)
to find and download them.

To deploy custom kernels and applications, refer to one of the many guides on building
these for Firecracker.
Keep in mind that you should not set custom networking in your machine so that Celestial
can take care of that.

#### Building a Kernel

Compiling your own Linux is not actually that hard.
You will want to do this if the `hello-world` kernel provided by Firecracker lacks
options you need or if you want to use a newer kernel version.
This documentation is adapted from the [Firecracker developer guide](https://github.com/firecracker-microvm/firecracker/blob/main/docs/rootfs-and-kernel-setup.md).

You need three things:

1. Kernel sources
2. A toolchain
3. A configuration file

You can get the kernel sources by cloning the Linux repository:

```sh
# warning! this is about 3.1GB in size so sit back and wait
git clone https://github.com/torvalds/linux.git linux.git
cd linux.git

# then checkout the version you want, e.g. v4.20
git checkout v4.19
```

You also need a few things for your toolchain.
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

Pro tip: use `make vmlinux -j [NO_THREADS]` to multi-thread your compilation.

This takes a few minutes.
There you go, now you have your `vmlinux` file that you can use as a kernel.

If you want to use Docker within your microVM, you need to build a kernel that has
support for everything Docker requires.
Check out [this repository](https://github.com/njapke/docker-in-firecracker) for
information on how to do that.

#### Building a Filesystem

You also need a filesystem that has your application and any dependencies.
You can either create this directly on your machine or using a Docker container.
Celestial uses union filesystems.
Instead of creating thousands of copies of the same disk image, we have one that
has all the data but is read-only, and we then create a writable overlay for each
machine, which helps with storage.

##### Directly on Your Machine

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

##### Using Docker

Alternatively, you can also create a filesystem using Docker.
Check the `builder` directory for that.

###### Build the Docker Container

Before you can get to building your rootFS, you need to build the container from
within this directory:

```sh
docker build -t rootfsbuilder .
```

###### Prepare your app.sh

Your `app.sh` will be run with `/bin/sh` once the microVM starts.
As soon as the script ends, your microVM will shutdown automatically.
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

###### Building your rootFS

To build your rootFS, use the container we have just created:

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
rootFS.

A script mounted as `base.sh` will be executed in your root filesystem. You can
use that to install additional dependencies that you don't want to add at runtime.

`/opt/code` is the internal folder where your final rootFS will be placed.
In this case, it will appear in the current working directory on your host.

### The Configuration File

All user configuration (with the exception of server-side command line flags) is
in the configuration file.
That configuration file follows the TOML specification.

This is an example configuration file for a constellation with one shell of 1584
satellites and one ground station:

```toml
# Orbital model to use, can be "SGP4" or "Kepler". Kepler is a bit easier to
# work with, but SGP4 is more accurate. If you use SGP4, Celestial will inform
# you whether the more efficient C++ implementation is available on your
# computer.
model = "SGP4"

# The bounding box of the area you would like to simulate. Satellite servers
# outside of this bounding box are suspended to save on resources. Provide
# coordinates in a Lat-Long (bottom left) Lat-Long (top right) format. You may
# want to checkout http://bboxfinder.com/ to find your bounding box.
bbox = [34.657635,-13.881488,58.794799,26.196637]

# Set the minimum update interval in seconds. For example, a value of 1 means
# that satellite positions are updated every second. Lower intervals lead to
# more resource consumption, higher intervals are less accurate.
# Celestial will inform you if your chosen interval cannot be achieved on your
# machine.
interval = 1

# If a desktop environment is available, you can choose to see an animated
# version of your constellation in a GUI. This depends on the VTK package, so
# make sure to have this installed.
animation = true

# Your servers will need to be available from your local client. Provide a list
# of endpoints including port.
hosts = ["35.198.102.193:1969"]
# Your servers also need to be able to communicate among each other. Provide a
# list of endpoints for this as well, including port. Please provide this even
# if you only want to run a single server. Note that IP addresses may be
# different when you run your hosts within the same private network.
peeringhosts = ["192.168.0.40:1970"]

# The networkparams section lets you specify parameters for networking between
# your machines. These can also be overridden for different shells or ground
# stations.
[networkparams]
# The ISL propagation factor determines the speed of ISLs. This propagation
# factor is in ms/m, with lasers in a vacuum this should be about 1/c.
islpropagation = 3.336e-6

# Bandwidth sets the available bandwidth for each ISL in Mbit/s. Current
# estimates set this at 10Gbit/s.
bandwidth = 10_000

# ISLs don't work at all altitudes given atmospheric refractions of lasers.
# Set the minimum altitude for ISLs here. For example, set it to 100km so that
# only links with their lowest point above 100km are considered stable.
mincommsaltitude = 100_000

# Whether a satellite is available from a ground stations depends on the
# minimum elevation in degrees (0 <= minelevation <= 90). If there is no
# satellite within this distance from a ground station, that ground station is
# cut off from the satellite network.
minelevation = 40

# Just as ISLs have their propagation delay, so do the down links from
# satellites to ground stations. We estimate this to be on the order of 1/c as well.
# This is also in ms/m.
gstpropagation = 3.336e-6

# There are different options for connecting a ground station. The main
# question is whether a ground station can connect to all available satellites
# simultaneously ("all" option), only their nearest satellite at any time
# ("shortest" option), or one nearest satellite for each shell ("one" option).
groundstationconnectiontype = "all"

# If you use SGP4 as your orbital model, you may want to set additional
# parameters that are passed to the SGP4 solvers. Note that we calculate most
# parameters from the orbital parameters. Check the Python-SGP4 documentation
# for further details: https://pypi.org/project/sgp4/. You can find reference
# data in the TLE database: http://www.celestrak.com/NORAD/elements/
[sgp4params]
# You can set a custom starting time for the simulation, which will be used to
# calculate the 'epoch' parameter. This date should be in RFC 3339 format
# (https://tools.ietf.org/html/rfc3339).
starttime = 2021-01-01T12:00:00+00:00

# SGP4 uses the "WGS72" gravity model by default but you can also set
# "WGS72OLD" or "WGS84" models.
model = "WGS72"
# Your opsmode is "i" by default but you can also set "a" for the old AFSPC
# mode.
mode = "i"
# Drag coefficient of your satellites should be 0 if you are unsure, but you
# can use data from the TLE database. For reference, at the time of writing
# this, STARLINK-2046 and ONEWEB-145 have drag coefficients of -0.7438e-3 and
# -0.71194, respectively. Although this is nonsensical since they shouldn't be
# negative.
bstar = -0.7438e-3
# The ballistic coefficient can be modified for compatibility reasons but you
# can safely ignore it, since it is also ignored by Python-SGP4. For reference,
# STARLINK-2046 and ONEWEB-145 have ballistic coefficients of -0.68197e-3 and
# -0.1102422e-1 at the time of writing this.
ndot = -0.68197e-3
# The argument of perigee describes the orbits angle to the equatorial plane.
# Since you will likely want to use circular orbits, this makes no difference.
argpo = 0.0

# The compute params section lets you configure Firecracker machine
# configuration options for your servers. The values you set here are
# considered the defaults but can be overridden for individual shells or
# ground stations.
[computeparams]
# Set the number of vCPUs that you want to allocate to each active server.
vcpu_count = 1
# Set the memory allocation for each server in MiB.
mem_size_mib = 128
# Set the maximum disk size for your machine. An empty sparse file will be
# created with a MAXIMUM size of disk_size_mib, and that file expands as your
# machine writes into it. Depending on the storage available on your hosts, you
# may run into problems.
disk_size_mib = 20_000
# You can enable Hyperthreading for your microVMs. The default for this setting
# is "off".
ht_enabled = false
# In addition to the default kernel boot parameters, you can also specify your
# own. These will be passed to the machine at boot time. Be sure not to have
# duplicate parameters with the defaults (these cannot be changed without
# recompiling Celestial):
#
#   console=ttyS0
#   noapic
#   reboot=k
#   panic=1
#   pci=off
#   tsc=reliable
#   quiet
#   ipv6.disable=1
#   nomodules
#   overlay_root=vdb
#
# Additionally, Firecracker passes these parameters:
#
#   ip (IP configuration)
#   root (root device configuration)
#   virtio_mmio.device
#
# You can also pass the empty string if you do not require this parameter.
bootparams = "8250.nr_uarts=0"
# Specify the compiled kernel to use for your microVMs. The filename you
# specify here must be available in the "/celestial" folder on your servers.
kernel = "test.bin"
# Specify the root filesystem image to use for your microVMs. The filename you
# specify here must be available in the "/celestial" folder on your servers.
rootfs = "rootfs.img"
# You can specify which host a machine or group of machines should be deployed
# to by setting the hostaffinity parameter. This parameter should be a list of
# integers in the range [0, len(hosts)] - this skips the normal even
# distribution of machines across available hosts. This can be beneficial if
# you require a particular API or better clock synchonization.
# If you don't need this, you can skip it.
# hostaffinity = [0, 2]

# You can define an arbitrary number of shells with the [[shell]] keyword. For
# sake of brevitiy, we only define a single shell here. Note that you can leave
# out some settings that override previously defined defaults.
[[shell]]
# One basic parameter for a shell is the amount of planes it has. Each plane is
# one orbital plane.
planes = 72
# Then, define how many satellites you would like for each plane of the shell.
# Satellites are evenly spaced around each orbit.
sats = 22
# Define the altitude of the shell in kilometers. This is used to compute the
# semi-major axis as altitude + earth_radius.
altitude = 550
# Angle of the satellite orbit plane measured from the Earth's equatorial
# plane, in degrees.
inclination = 53.0
# The angle of arc (in degrees) that the ascending nodes of all the orbital
# planes is evenly spaced along. For example, seting this to 180 results in a
# Pi constellation like Iridium. For a standard 2Pi constellation like
# Starlink, set this to 360.0.
arcofascendingnodes = 360.0
# The eccentricity of the orbit defines its "oval-ness". The value is between
# 0.0 (perfectly circular orbit) and 1.0 (completely parabolic). For LEO
# constellations, this should be 0.0. For reference, STARLINK-2046 and
# ONEWEB-145 have this as 0.0001205 and 0.0012512, respectively, at the time of
# writing.
eccentricity = 0.0

# If you use the SGP4 model you can set custom parameters for specific shells.
# Starttime, model, and mode cannot be overridden as they are shared for all
# shells.
[shell.sgp4params]
bstar = 0.0
ndot = 0.0

# You can also override computeparams for specific shells. For example, you
# might desire to allocate more memory to the servers in a specific shell.
[shell.computeparams]
mem_size_mib = 256

# Finally, you can also set networkparams for specific shells. For example,
# you may want to set higher bandwidths for a specific shell.
[shell.networkparams]
bandwidth = 10_000

# In addition to satellites, ground stations are another important part of your
# constellation. Each ground station is a server on earth that communicates
# with the satellite constellation over radio links. You can specify up to
# 16,384 ground station with the [[groundstation]] tag, or no ground stations
# at all.
# Ground stations servers are always active, regardless of whether they lie in
# the bounding box or not.
[[groundstation]]
# You can set a name for the ground station. This will be available to the
# microVM over the included HTTP information service.
name = "Berlin"
# Set a latitude and longitude for the ground station. This location is used to
# calculate nearby satellites and establish links to the satellite
# constellation.
lat = 52.51492067
long = 13.32666938

# By default, ground stations inherit the computeparams parameters defined
# before, but those can of course be overridden. Generally, you may want to
# allocate more resources at ground stations.
[groundstation.computeparams]
vcpu_count = 4
mem_size_mib = 8192
disk_size_mib = 5_000
ht_enabled = true
hostaffinity = [1]

# Additionally, you can also set networkparams specifically for a ground
# station if you want to override the standard values set above.
[groundstation.networkparams]
gstpropagation = 3.336e-6
bandwidth = 1_000
```

### Known Limitations

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

#### Process and File Handler Limits

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

#### ARP Cache

To avoid garbage collection in the ARP cache, you may need to resize ARP cache
thresholds depending on the number of machines you plan to run.

```sh
sudo sysctl -w net.ipv4.neigh.default.gc_thresh1=2048
sudo sysctl -w net.ipv4.neigh.default.gc_thresh2=4096
sudo sysctl -w net.ipv4.neigh.default.gc_thresh3=8192
```

#### Randomness

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

## Runtime

When you develop your applications for use in Celestial, there are some details
specific to the emulation environment that you may want to note.

### Networking

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
The network has a /30 mask, hence only those two are available.

`tc` is used to manipulate network performance between machines.
WireGuard is used to link machines on different hosts.

### Time

Since the user provides kernel and root filesystem, all time and clock control is
in their hands.

If you're running experiments on Celestial you might be interested in an accurate
wall clock in your VMs, e.g. to measure network delays.
There are two ways to configure clock synchronization in your VMs: NTP and PTP.
You can read a bit more about that in [the Firecracker documentation](https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md#my-guest-wall-clock-is-drifting-how-can-i-fix-it).

#### NTP

NTP is relatively simple to set up, the operating system on your root filesystem
is probably set up for it to some extent.
Choose a time server to synchronize with and off you go.

#### PTP

The downside of NTP is that all your machines synchronize with an external time server.
If you run hundreds of machines, that's quite a bit of network traffic.

PTP synchronizes your machines with the host's time using cheap para-virtualized
KVM calls.
It's a lot more accurate as well (on one machine - if you run Celestial across
multiple serves, make sure to synchronize those too, and expect some inaccuracies!).

The downside here is that both hour host and guest must support it.

On a host side, we have seen that it works with `Amazon Linux 2` and
`Ubuntu 18.04 LTS` but we weren't able to get it to work with Debian.
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

### Services

On the server side, Celestial provides two APIs for your microVMs.

#### HTTP API

First, an HTTP API lets your machines see information about the constellation and
about themselves.
For example, you may want to configure your application to do different things based
on the satellite it is deployed on.

To access the HTTP API, make an HTTP GET request to your microVM's gateway on port
80 (configurable).

##### Self

```http
  GET /self
```

Gets general information about self.
Requester is identified using their IP address.

Returns (for a ground station):

```json
{
  "type": "gst",
  "name": "berlin",
  "id": 0,
  "identifier": "berlin.gst.celestial"
}
```

Returns (for a satellite):

```json
{
  "type": "sat",
  "id": 1,
  "shell": 0,
  "identifier": "1.0.celestial"
}
```

The `id` is the identifier of the machine within its shell.
`shell` is the identifier of its shell (the index within the configuration file
is used).
For ground stations, `shell` is `-1`, `id` is the index within the configuration
file.
Here, the additional `name` parameter gives the name of the ground station.
For satellites, this is left empty.

##### Info

```http
  GET /info
```

Gets general information about constellation.

Returns:

```json
{
  "model": "Kepler",
  "shells": 2,
  "groundstations": [{ "name": "tester" }, { "name": "tester2" }]
}
```

##### Get Shell Info

```http
  GET /shell/${shell}
```

| Parameter | Type  | Description                           |
| :-------- | :---- | :------------------------------------ |
| `shell`   | `int` | **Required**. Index of shell to fetch |

Returns:

```json
{
  "planes": 6,
  "sats": 75,
  "altitude": 1325,
  "inclination": 70,
  "arcofascendingsnodes": 360,
  "eccentricity": 0,
  "activeSats": [
    { "shell": 0, "sat": 0 },
    { "shell": 0, "sat": 70 },
    { "shell": 0, "sat": 71 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 73 },
    { "shell": 0, "sat": 74 },
    { "shell": 0, "sat": 256 },
    { "shell": 0, "sat": 257 },
    { "shell": 0, "sat": 258 },
    { "shell": 0, "sat": 259 },
    { "shell": 0, "sat": 260 },
    { "shell": 0, "sat": 261 },
    { "shell": 0, "sat": 262 }
  ],
  "network": {
    "bandwidth": 10000,
    "islpropagation": 0.000003336,
    "mincommsaltitude": 100000,
    "minelevation": 40,
    "gstpropagation": 0.000006672,
    "groundstationconnectiontype": "all"
  },
  "compute": {
    "vcpu": 1,
    "mem": 128,
    "disk": 20000,
    "ht": false,
    "kernel": "test.bin",
    "rootfs": "empty.img"
  }
}
```

##### Get Satellite Info

```http
  GET /shell/${shell}/${sat}
```

| Parameter | Type  | Description                               |
| :-------- | :---- | :---------------------------------------- |
| `shell`   | `int` | **Required**. Index of shell to fetch     |
| `sat`     | `int` | **Required**. Index of satellite to fetch |

Returns:

```json
{
  "position": { "x": 7689789, "y": 105726, "z": 290480 },
  "active": true,
  "connectedSats": [
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 73 }
  ],
  "connectedgst": [{ "name": "tester" }, { "name": "tester2" }]
}
```

##### Get Ground Station Info

```http
  GET /gst/${name}
```

| Parameter | Type     | Description                                   |
| :-------- | :------- | :-------------------------------------------- |
| `name`    | `string` | **Required**. Name of ground station to fetch |

Returns:

```json
{
  "position": { "x": 6296904, "y": 752587, "z": 611161 },
  "latitude": 5.504684,
  "longitude": 5.765499,
  "network": {
    "bandwidth": 10000,
    "islpropagation": 0.000003336,
    "mincommsaltitude": 100000,
    "minelevation": 40,
    "gstpropagation": 0.000006672,
    "groundstationconnectiontype": "all"
  },
  "compute": {
    "vcpu": 2,
    "mem": 256,
    "disk": 5000,
    "ht": false,
    "kernel": "test.bin",
    "rootfs": "tester.img"
  },
  "connectedSats": [
    { "shell": 0, "sat": 0 },
    { "shell": 0, "sat": 72 },
    { "shell": 0, "sat": 73 },
    { "shell": 0, "sat": 74 },
    { "shell": 0, "sat": 258 },
    { "shell": 0, "sat": 259 },
    { "shell": 0, "sat": 260 },
    { "shell": 1, "sat": 77 },
    { "shell": 1, "sat": 78 }
  ]
}
```

##### Get Path Info

```http
  GET /path/${source_shell}/${source_sat}/${target_shell}/${target_sat}
```

| Parameter      | Type              | Description                                                                                       |
| :------------- | :---------------- | :------------------------------------------------------------------------------------------------ |
| `source_shell` | `int` or `"gst"`  | **Required**. Either ID of source shell or `gst` if ground station is desired.                    |
| `source_sat`   | `int` or `string` | **Required**. Either ID of source satellite or name of ground station if `source_shell` is `gst`. |
| `target`       | `int` or `"gst"`  | **Required**. Either ID of target shell or `gst` if ground station is desired.                    |
| `target_sat`   | `int` or `string` | **Required**. Either ID of target satellite or name of ground station if `target_shell` is `gst`. |

Returns:

```json
{
  "paths": [
    {
      "distance": 2385036,
      "delay": 15.91296,
      "bandwidth": 10000,
      "segments": [
        {
          "sourceShell": -1,
          "sourceSat": 0,
          "targetShell": 0,
          "targetSat": 258,
          "delay": 11.612529,
          "distance": 1740487,
          "bandwidth": 10000
        },
        {
          "sourceShell": -1,
          "sourceSat": 257,
          "targetShell": -1,
          "targetSat": 258,
          "delay": 2.1502154,
          "distance": 644549,
          "bandwidth": 10000
        }
      ]
    }
  ]
}
```

This returns `-1` as a shell identifier for ground stations.

#### DNS API

In addition to finding information about itself, a machine can also find the network
address of another machine by querying the provided DNS service.
This service is available at the machine's gateway on port 53.
It supports only `A` requests for the custom `.celestial` TLD.

Records are in the form `[ID].[SHELL].celestial` for satellites and `[NAME].gst.celestial`
for ground stations.
Note that all addresses are resolved if the machine is known, regardless of whether
that machine is active or can be accessed.

### Output

There are different ways to retrieve experiment results from Celestial.
You can also use your own cloud storage or logging database if your host has Internet
access.

#### stderr and stdout

If your machines have terminal devices available (not using the `8250.nr_uarts=0`
boot parameter), your software can write to `stdout` and `stderr`.
The streams of those devices will be forwarded to text files on your host.
You can see the outputs of your machines in the `/celestial/out` folder.
For each machine, there is an `out` and an `err` file, that capture `stdout` and
`stderr`, respectively.

Note that this is not recommended for performance-critical applications as writing
a lot of data to your host disk in this way can be slow.

#### Retrieving Files from microVM Disks

If your software manipulates files on your microVM filesystem, you also have the
option to retrieve those files later.
Celestial creates an overlay filesystem for each microVM as
`ce[SHELL]-[ID].ext4` for satellites or `ce[NAME].ext4` for ground stations.
Note that if you use multiple hosts, the filesystem will only be created on the
host that hosts that particular machine.

You can mount this filesystem to copy files (either directly on the host or by
downloading a copy of the filesystem).
For example, to copy a file named `output.csv` from the filesystem of satellite
840 in shell 1, do:

```sh
# create a temporary mounting point
sudo mkdir -p ./tmp-dir

# mount the filesystem
sudo mount /celestial/ce1-840.ext4 ./tmp-dir -o loop

# copy the relevant file to your directory
sudo cp ./tmp-dir/output.csv sat1-840-output.csv

# unmount the filesystem
sudo umount ./tmp-dir

# remove the mounting point
sudo rmdir ./tmp-dir
```

We recommend only mounting the filesystem after its microVM has been shut down to
avert any filesystem corruption.
Also keep in mind that you must unmount the filesystem if you want to run Celestial
again as Celestial will try to overwrite this filesystem with a fresh copy.
