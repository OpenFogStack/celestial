---
layout: home
title: Setup
nav_order: 6
---

## Setup

Running a Celestial emulation requires two steps:

* preparing file system for your servers
* generating trajectory and network information for your constellation
* running the emulation on hosts

### Preparing File Systems

A file system is the 'disk image' of your microVMs.
As such, it requires a Linux distribution and all files required to execute
whatever code and services you would like your satellite and ground station
servers to run.

As creating Firecracker microVM root file systems can be daunting, we provide
a file system builder toolchain based on Docker that compiles your files and
scripts into the necessary file format.

As a prerequisite, make sure to have Docker installed with an option to build
and run `linux/amd64` containers.

#### Preparing the File System Builder

Use `make` to build the container:

```sh
make rootfsbuilder
```

This will leave you with a `rootfsbuilder:latest` image available locally.

#### Preparing an Application

The root file system builder allows for three ways to customize your file system:

1. Commands executed during installation
1. Commands executed on boot
1. Additional files copied as-is

Commands executed during installation must be in a `sh` script that we refer to
as the 'base script'.
You can use this to install dependencies from the web, e.g., Python, or run
other configuration.

Commands executed on boot can be used to actually run your application, e.g.,
start a Python script.
We refer to this script as the 'app script'.

Additional files are simply copied into your file system and can include, for
example, binaries or ML models.

Check the [quick start](./quickstart) for an example application.

#### Building the Root File System

Using your application files and root file system builder image, create your
file system by running the builder container with correct mounts:

```sh
docker run --rm --privileged --platform=linux/amd64 \
    -v [PATH_TO_APP_SCRIPT]:/app.sh \
    -v [OPTIONAL_PATH_TO_BASE_SCRIPT]:/base.sh \
    -v [OPTIONAL_PATH_TO_ADDITIONAL_FILES]:/files/[PATH_ON_IMAEG] \
    -v $(pwd):/opt/code rootfsbuilder:latest [OUTPUT]
```

Make sure to replace your `PATH_TO_APP_SCRIPT` with an __absolute__ path
to your app script.
Do the same for your `OPTIONAL_PATH_TO_BASE_SCRIPT` but note that this is
optional -- if you do not require installing base services or configuration,
you can skip this.
You can optionally copy as many files as you need into your image by
mounting them into the `/files` directory in the builder container.

Finally, specify the `OUTPUT` path where your final image will be copied.

### Generating Satellite Trajectories

Assuming you have a complete configuration file (see [configuration reference](./configuration)),
you can then generate satellite trajectories you can use in your Celestial
emulation.
Note that once you have generated trajectories, you can re-use them to
repeat your emulation run and reproduce results.

#### Prerequisites

Our Celestial satellite trajectory script requires Python (tested on version 3.11).
Further, you must install some dependencies.
We recommend doing this in a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Alternatively, you can also run this with Docker.
Build the `satgen-docker` image:

```sh
make satgen-docker
```

#### Running Satellite Trajectory Generation

We can then use the `satgen.py` script to generate trajectories:

```sh
python3 satgen.py [PATH_TO_CONFIG] [OUTPUT_PATH]
```

Replace `PATH_TO_CONFIG` with the path to your configuration file and the
optional `OUTPUT_PATH` with a path to your output file.

If you want to use the Docker image instead:

```sh
docker run --rm \
    -v ${pwd}:/app \
    satgen-docker \
    /app/[PATH_TO_CONFIG] \
    /app/[OUTPUT_PATH] \
```

After a few seconds to minutes (depending on the size of the constellation
you want to emulate) you will end up with a `.zip` file that you can use for
further emulation.

### Running Celestial Emulation

You can now run your emulation.
For this, you will need at least one server that can host your microVMs.

#### Host Prerequisites

Your server(s) will need to meet a few requirements:

* a Linux-based operating system (we highly recommend Ubuntu 22.04 LTS)
* a main network interface (default is `ens4`, but you can configure this)
* WireGuard installed and on your path as `wg`
* `systemd-resolved` as a DNS server
* `iptables` installed and on your path
* virtualization capabilities (for VMs, see [nested virtualization](./nestedvirtualization))
* the `firecracker` binary (version 1.x) installed and on your path (available [here](https://github.com/firecracker-microvm/firecracker/releases/tag/v1.6.0))
* when running multiple servers, network connection between them must be available

Check the [quick start](./quickstart) on installation instructions.

You also need a coordinating machine to read your Celestial trajectory archive.
This can be a separate machine or run on one of your hosts.

#### Putting Files on Your Hosts

Your hosts need access to your root file system files and microVM kernels.
Create a folder `/celestial` at the root of your drive and place your files there.

#### Running the Server Software

Simply run the compiled `celestial.bin` binary on your host:

```sh
sudo ./celestial.bin
```

Root access is required to set up all the networking between machines.
Again, don't run this on your local computer if you don't know what you're doing.

You can configure some basic stuff using command line flags:

```text
Usage of ./celestial.bin:
  -port int
        Port to bind to (default 1969)
  -dns-service-port int
        Port to bind DNS service server to (default 1970)
  -info-server-port int
        Port to bind info server to (default 80)
  -network-interface string
        Name of your main network interface (default "ens4")
  -debug
        Enable debug logging (default off)
```

#### Running the Client Software

The client software should run using a Python virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Simply run `celestial.py` with a path to your Celestial trajectory archive and
network addresses of your host(s):

```sh
python3 celestial.py [celestial.zip] [host1_addr] [host2_addr] ... [hostN_addr]
```
