---
layout: default
title: Output
nav_order: 10
---

## Output

There are different ways to retrieve experiment results from Celestial.
You can also use your own cloud storage or logging database if your host has Internet
access.

### `stderr` and `stdout`

If your machines have terminal devices available (not using the `8250.nr_uarts=0`
boot parameter), your software can write to `stdout` and `stderr`.
The streams of those devices will be forwarded to text files on your host.
You can see the outputs of your machines in the `/celestial/out` folder.
For each machine, there is a `.out` and a `.err` file, that capture `stdout` and
`stderr`, respectively.

Note that this is not recommended for performance-critical applications as writing
a lot of data to your host disk in this way can be slow.

### Retrieving Files from microVM Disks

If your software manipulates files on your microVM file system, you also have the
option to retrieve those files later.
Celestial creates an overlay file system for each microVM as
`ce[SHELL]-[ID].ext4` for satellites or `ce[NAME].ext4` for ground stations.
Note that if you use multiple hosts, the file system will only be created on the
host that hosts that particular machine.

You can mount this file system to copy files (either directly on the host or by
downloading a copy of the file system).
For example, to copy a file named `output.csv` from the file system of satellite
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

We recommend only mounting the file system after its microVM has been shut down to
avert any file system corruption.
Also keep in mind that you must unmount the file system if you want to run Celestial
again as Celestial will try to overwrite this file system with a fresh copy.
