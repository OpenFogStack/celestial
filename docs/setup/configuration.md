---
layout: default
title: Configuration
parent: Setup
nav_order: 4
---

## The Configuration File

All user configuration (except server-side command line flags) is
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

# Bandwidth sets the available bandwidth for each ISL in Kbit/s. Current
# estimates set this at 10Gbit/s.
bandwidth = 10_000_000

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
bandwidth = 10_000_000

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
bandwidth = 1_000_000
```
