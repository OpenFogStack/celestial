---
layout: default
title: Quick Start
nav_order: 3
---

## Quick Start

This quick start guide is intended to ease you into using Celestial.
In this guide, we will build Celestial, run trajectory generation, and deploy
an example application on host infrastructure.

The example application is a simple network latency measurement application
written in Python called the `validator`.
It checks network latency reported by the Database service of Celestial and
compares it to ping measurements made using the `ping3` library.

This quick start guide was created using a fresh installation of Ubuntu 22.04
LTS.
For optimal compatibility, we recommend that you use the same setup, but feel
free to ignore this advice if you know what you're doing.
As we mainly use Python and Docker, you should be able to run this quick start
from a Windows or macOS machine with slight adaptation.
Further, note that the trajectory generation and emulation coordination require
at least 4GB of memory and an adequately modern CPU.

We assume that you have access to two Ubuntu 22.04 LTS servers with virtualization
capabilities.
Those servers should be accessible to you over SSH (port `22`), and have port
`1969/tcp` open to your coordinating machine.
Further, they should be able to communicate with each other on port `1970/udp`
and to ping each other using `ICMP`.

If you do not, please refer to this manual on creating machines with Google Cloud
Platform:

<!--markdownlint-disable MD033 -->
<details markdown="block">
  <summary>
    Running on Google Cloud
  </summary>
<!--markdownlint-enable MD033 -->

### Preparing Google Cloud Infrastructure

{: .text-yellow-300 }
**Disclaimer**:
Using Google Cloud Platform (or any other cloud service) can incur costs.
Proceed at your own risk.

{: .text-red-200 }
**Warning**:
We will be starting a few cloud machines in this tutorial!
We will be using two `n2-standard-32` instances ($4 per hour) and one
`n2-standard-8` instance ($0.50 per hour).
In the EU Frankfurt region, these machines currently cost $4.50 per hour.
This does not include additional charges for data transfer or disk.
We are not responsible for any costs that your project may incur.

#### Prerequisites

1. Install OpenTofu following the [official OpenTofu documentation](https://opentofu.org/docs/intro/install/):

    ```sh
    curl --proto '=https' --tlsv1.2 -fsSL \
        https://get.opentofu.org/install-opentofu.sh \
         -o install-opentofu.sh

    chmod +x install-opentofu.sh
    ./install-opentofu.sh --install-method deb
    rm install-opentofu.sh
    ```

    OpenTofu is a free alternative to Terraform.

1. We will be using Google Cloud Platform to host our Celestial servers.
    That means that you should set up a Google Cloud Platform project in your account.
    Read more about it [here](https://cloud.google.com/docs/concepts/projects).

    You should note the name of your project and install and configure the Google
    Cloud CLI accordingly (in this example, our project will be called `celestial-quick-start`).
    This setup is adapted from the [CLI documentation](https://cloud.google.com/sdk/docs/install):

    ```sh
    $ sudo snap install google-cloud-cli --classic
    $ gcloud init
    ...
    # press Y when asked to log in
    # follow the steps required to log in to your account

    $ gcloud auth application-default login
    # add your gcloud accoount to the Application Default Credentials
    # this lets OpenTofu use it
    ```

#### Starting Celestial on Google Cloud Platform

To run Celestial on Google Cloud Platform, we need to create a few Google Compute
Engine instances.
In this quick start, we will use OpenTofu to deploy two
host instances (`n2-standard-32`) and one instance for the coordinator:

```sh
cd ~/celestial/quick-start/tofu
tofu init

# change these values to match your project
GCP_PROJECT="celestial-quick-start"
GCP_REGION="europe-west3"
GCP_ZONE="c"

# this will give you an overview of what OpenTofu is about to do
# check to see if everything looks right
tofu plan \
    -var gcp_project=$GCP_PROJECT \
    -var gcp_region=$GCP_REGION \
    -var gcp_zone=$GCP_ZONE

# type yes to confirm
tofu apply \
    -var gcp_project=$GCP_PROJECT \
    -var gcp_region=$GCP_REGION \
    -var gcp_zone=$GCP_ZONE
```

If you get an error that your Google Cloud quota is exceeded, log into the
Google Cloud Console and increase your quotas accordingly.

You can verify that the instances are running by running the following command:

```sh
# confirm that you see:
#   - celestial-host-0
#   - celestial-host-1
gcloud compute instances list --zones "$GCP_REGION-$GCP_ZONE"
```

Finally, configure SSH access to your machines:

```sh
gcloud compute config-ssh
```

This will let you access Google Cloud Compute instances over SSH without explicit
username or key.
Note that while you can access these instances over SSH using their complete
hostname, you will need to use their external IP addresses to start Celestial.
You can find them in the Google Cloud Console or by using OpenTofu:

```sh
tofu output
```

Proceed with the remainder of this quick start introduction.

#### Destroying Cloud Infrastructure

At the end of your experiments, do not forget to destroy your infrastructure again!

```sh
cd ~/celestial/quick-start/tofu
tofu destroy -auto-approve
```

</details>
<!--markdownlint-enable MD033 -->

### Install and Set Up Dependencies

Before we can start setting up Celestial, there are some dependencies we need
to take care of.
These steps are correct as of January 2024, but things change quickly, so please
don't worry if your output looks slightly dissimilar.

1. Set up Docker to build everything.
    This follows the official [Docker documentation](https://docs.docker.com/engine/install/ubuntu/):

    ```sh
    sudo apt-get remove docker docker-engine docker.io containerd runc
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    ```

    Proceed with the [post-installation steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/):

    ```sh
    sudo groupadd docker
    sudo usermod -aG docker $USER
    ```

    Log out of your machine and log back in to see the changes.
    Upon re-login, running `docker ps` should work without error.

1. Install the other dependencies:

    ```sh
    sudo apt-get update

    # this only installs python3.10, but that's enough
    sudo apt-get install -y make git python3 python3-venv python3-pip
    ```

    Note that development on Celestial used Python 3.11, but we have ensured
    compatibility with Python 3.10.

1. Clone the Celestial repository:

    ```sh
    cd ~
    git clone https://github.com/OpenFogStack/celestial
    ```

1. Activate the Celestial virtual environment and install Python dependencies:

    ```sh
    cd ~/celestial
    # create a new virtual environment in the .venv directory
    python3 -m venv .venv
    # activate the virtual environment
    source .venv/bin/activate
    # install dependencies
    python3 -m pip install -r requirements.txt
    ```

### Build Celestial

To build Celestial, your best option is to use the `celestial-make` Docker
image.
Build this image with:

```sh
docker build -f compile.Dockerfile -t celestial-make .
```

Then build `celestial.bin` with:

```sh
docker run --rm -v $(pwd):/celestial celestial-make celestial.bin
```

This will build the executable `celestial.bin` in the current directory.
This binary is what runs on your Celestial hosts.

The software on your Celestial coordinator can run with Python and does not need
compilation beyond building the protocol buffer files.

### Building the Application

Applications on Celestial are embedded into a root file system that the microVMs
use.
This file system has an operating system, a set of packages, and any software
you need.
The easiest way to build a root file system is to use the provided Docker-based
builder tool chain.
Build this Docker image with:

```sh
make rootfsbuilder
```

This will give you the `rootfsbuilder:latest` Docker image locally.
This Docker image already includes a copy of Alpine Linux v3.18.0.

We can now build the root file system for the validator application and for our
servers:

```sh
cd ~/celestial/quick-start/validator
docker run --rm \
    -v "$(pwd)/validator.py":/files/validator.py \
    -v "$(pwd)/validator.sh":/app.sh \
    -v "$(pwd)/validator-base.sh":/base.sh \
    -v "$(pwd)":/opt/code \
    --platform linux/amd64 \
    --privileged rootfsbuilder validator.img

docker run --rm \
    -v "$(pwd)/server.sh":/app.sh \
    -v "$(pwd)":/opt/code \
    --platform linux/amd64 \
    --privileged rootfsbuilder server.img
```

This builds the images `validator.img` and `server.img` in the current directory.
Any file mounted into the `/files` directory will be copied into the image
directly.
The `base.sh` file is a shell script that is run on the image while it is built,
which we use to install any necessary dependencies or to change any
configuration.
`app.sh` is the main application script that is run on the image when it is run.
Feel free to check out the respective files to find out what they do!

You will also need a Linux kernel.
You can compile your own using the [manual we provide](./kernel)
(it's really easy!) or download one from us:

```sh
cd ~/celestial/quick-start
curl -fsSL \
    -o vmlinux-5.12.bin \
    "https://tubcloud.tu-berlin.de/s/fcLHfyeQSZwWi5k/download/vmlinux-5.12.bin"
```

Note that the kernel we provided is of version `v5.12` and follows the configuration
you find in [`./kernel/config-5.12`](https://github.com/OpenFogStack/celestial/blob/kernel/config-5.12).
Notably, this includes the `CONFIG_RANDOM_TRUST_CPU=y` option.

### Running Trajectory and Network Generation

Before any emulation can happen, we have to generate trajectory and network
state for the duration of our emulation.
We use the `satgen.py` generator for this, pointing it to our Celestial
configuration.
Make sure to execute this in your virtual environment:

```sh
cd ~/celestial
python3 satgen.py ./quick-start/quickstart.toml ./quick-start/quickstart.zip
```

This can take a few minutes to complete and should leave you with the `quickstart.zip`
file that has all the necessary information to run an emulation.

### Preparing Servers

Before our servers can run `celestial.bin`, we need to install a few dependencies:

* WireGuard (`wg`)
* Firecracker
* the `celestial.bin`
* a `/celestial` source folder for our guest kernel and root file systems
* increased file handler and process limits

We repeat the steps below **for each host server we want to run Celestial on**!

```sh
# adapt this ip address or hostname according to your infrastructure
CELESTIAL_HOST="192.168.0.8"

# make sure to repeat the steps below for each server!
# CELESTIAL_HOST="192.168.0.9"
```

```sh
# install wireguard
ssh $CELESTIAL_HOST sudo apt-get update
ssh $CELESTIAL_HOST sudo apt-get install wireguard -y

# download and install Firecracker v1.6.0
ssh $CELESTIAL_HOST curl -fsSL -o firecracker-v1.6.0-x86_64.tgz \
    https://github.com/firecracker-microvm/firecracker/releases/download/v1.6.0/firecracker-v1.6.0-x86_64.tgz
ssh $CELESTIAL_HOST tar -xvf firecracker-v1.6.0-x86_64.tgz
# and add the firecracker and jailer binaries to PATH
ssh $CELESTIAL_HOST  sudo mv \
    release-v1.6.0-x86_64/firecracker-v1.6.0-x86_64 \
    /usr/local/bin/firecracker
ssh $CELESTIAL_HOST sudo mv \
    release-v1.6.0-x86_64/seccompiler-bin-v1.6.0-x86_64 \
    /usr/local/bin/jailer

# upload the celestial.bin
cd ~/celestial
scp celestial.bin $CELESTIAL_HOST:.

# create a /celestial directory on the server
ssh $CELESTIAL_HOST sudo mkdir -p /celestial

# now upload our guest kernel and file system
scp ./quick-start/vmlinux-5.12.bin $CELESTIAL_HOST:.
scp ./quick-start/validator/server.img $CELESTIAL_HOST:.
scp ./quick-start/validator/validator.img $CELESTIAL_HOST:.

# and make sure to move them to the correct folder
ssh $CELESTIAL_HOST sudo mv vmlinux-5.12.bin /celestial/
ssh $CELESTIAL_HOST sudo mv server.img /celestial/
ssh $CELESTIAL_HOST sudo mv validator.img /celestial/

# finally, increase the file handler limits on your machine
cat << END > limits.conf
* soft nofile 64000
* hard nofile 64000
root soft nofile 64000
root hard nofile 64000
* soft nproc 64000
* hard nproc 64000
root soft nproc 64000
root hard nproc 64000
END

scp limits.conf $CELESTIAL_HOST:.
ssh $CELESTIAL_HOST sudo mv ./limits.conf /etc/security/limits.conf
rm limits.conf

# you may need to reboot for this to take effect
ssh $CELESTIAL_HOST sudo reboot now
```

### Starting the Experiments

We may now start the experiments.
To do so, we need to start the Celestial binary on each host, and we must start
the coordinator locally.

We recommend running these commands in different terminal windows or `screen`
sessions:

```sh
# start the hosts first:
# make sure to adapt this ip or hostname according to your infrastructure
$ CELESTIAL_HOST_1="192.168.0.8"
$ ssh $CELESTIAL_HOST_1
host1 $  sudo ./celestial.bin -debug
...

# in a second terminal window, start the second host
$ CELESTIAL_HOST_2="192.168.0.8"
$ ssh $CELESTIAL_HOST_
host2 $  sudo ./celestial.bin -debug
...

# in a third terminal window, start the coordinator
# make sure to run in venv
$ source .venv/bin/activate
$ python3 celestial.py ./quick-start/quickstart.zip $CELESTIAL_HOST_1 $CELESTIAL_HOST_2
...
```

Your experiments are now running.
Leave them running for however long you want, for at least a few minutes.
Note that they will automatically end when the `duration` configured in our
configuration file has been reached.
But you can stop them earlier by stopping the coordinator.

### Monitoring the Experiments

There are a few things you can monitor while the experiments are running.
Of course there is the output of the coordinator, which tells you how long
individual updates took.
At the beginning of the emulation, starting everything can also take a long time
(up to 2 minutes in our experiments).

The output of the hosts tells you about booting microVMs (you can adapt the
log level in the binary as well) and any errors that occur.

Any output of your microVMs' `stdout` and `stderr` is appended to individual
files, which you can view live.
For example, to follow the output of the validator, run this on the host that
is running the validator ground station:

```sh
$ tail -f /celestial/out/gst-validator.out
trying sat 1442 shell 0
expect 10.811155/10.811155 for sat 1442 shell 0 and found 22.423506
trying sat 1443 shell 0
expect 4.217975/4.217975 for sat 1443 shell 0 and found 9.413958
trying sat 1464 shell 0
expect 12.332064/12.332064 for sat 1464 shell 0 and found 25.309563
trying sat 1465 shell 0
expect 5.738477/5.738477 for sat 1465 shell 0 and found 12.450695
trying sat 1486 shell 0
expect 13.849221/13.849221 for sat 1486 shell 0 and found 28.427362
trying sat 1487 shell 0
expect 7.255186/7.255186 for sat 1487 shell 0 and found 15.675306
...
```

Similarly, to follow the output of the satellite `1420` in shell `0`:

```sh
$ tail -f /celestial/out/0-1420.out
Wed Apr 27 11:48:46 UTC 2022: satellite server running
Wed Apr 27 11:49:46 UTC 2022: satellite server running
Wed Apr 27 11:50:46 UTC 2022: satellite server running
...
```

### Stopping Experiments and Downloading Results

To stop the experiments, simply execute Ctrl+C on the terminal windows of the
coordinator.

Our validator application creates a local file `validator.csv` in its file system.
To download the file from the file system, we must mount it on the first host:

```sh
$ CELESTIAL_HOST_1="192.168.0.8"
$ ssh $CELESTIAL_HOST_1
ubuntu@celestial-host-1:~$ mkdir -p ./tmp
ubuntu@celestial-host-1:~$ sudo mount /celestial/ce-validator.ext4 ./tmp -o loop
ubuntu@celestial-host-1:~$ cp ./tmp/root/validator.csv .
ubuntu@celestial-host-1:~$ sudo umount ./tmp
ubuntu@celestial-host-1:~$ rmdir ./tmp
# now get back out of the host
ubuntu@celestial-host-0:~$ exit
$ scp $CELESTIAL_HOST_1:./validator.csv ~/celestial/quick-start/results.csv
```

You now have `results.csv` on your machine and can continue to analysis.

### Analysis

With our results files in hand, we can execute the `check_validator.py` script
to generate graphs that will help us understand the results.
To execute the script:

```sh
cd ~/celestial
source .venv/bin/activate
cd ./quick-start
# pandas is additionally required as a dependency for this script
python3 -m pip install -r requirements.txt
python3 check_validator.py results.py
```

In the `graphs` folder, you should now see a few graphs:

```sh
$ ls -l graphs
total 432
-rw-r--r-- 1 root root 122402 Jan 27 13:40 actual_line.png
-rw-r--r-- 1 root root  13795 Jan 27 13:40 diff_ecdf.png
-rw-r--r-- 1 root root 122954 Jan 27 13:40 expected_line.png
-rw-r--r-- 1 root root  68932 Jan 27 13:40 reachable_actual.png
-rw-r--r-- 1 root root  67517 Jan 27 13:40 reachable_expected.png
-rw-r--r-- 1 root root  35348 Jan 27 13:40 results_scatter.png
```

Let's first look at `results_scatter.png`, which has all results plotted by time
with the color giving whether the difference between expected and actual was
acceptable:

![Scatter plot of our results](./assets/results_scatter.png "Scatter plot of our results")

It looks like almost all measurements turned out OK, there was only one measurement
where something was off.

Next, `diff_ecdf.png` shows the ECDF of the differences between expected and actual:

![ECDF of our results](./assets/diff_ecdf.png "ECDF of our results")

We see that around 60% of the measurements were spot-on, for 95% there was a difference
of 4ms or less.
Note that this could also happen when the expected value changes during a measurement
as we only log the median actual measurement.
Extending our application to capture and measure these effects is left as an exercise
for the reader.

Finally, we can compare `expected_line.png` and `actual_line.png` to see how the
expected and actual values change over time:

![Expected values](./assets/expected_line.png "Expected values")
![Actual values](./assets/actual_line.png "Actual values")

Note that these are different graphs.
They look almost exactly the same because the accuracy in Celestial is so high.

Filtering out measurements that are at 1e7, i.e., unreachable:

![Expected reachable values](./assets/reachable_expected.png "Expected reachable")
![Actual reachable values](./assets/reachable_actual.png "Actual reachable")

Again, there is hardly a difference.

### Conclusion

In this quick start tutorial, we have seen how to run a simple experiment with
Celestial.
Although even such a simple experiment requires a lot of setup, rest assured that
we have covered large parts of Celestial already.
Advanced use includes compiling custom kernels, tuning parameters, and building
custom applications.
