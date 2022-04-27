provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# the zone variable must be within the region
# hence this weird setup
locals {
  zone = "${var.gcp_region}-${var.gcp_zone}"
}

# we use a version of Ubuntu 18.04 LTS
# this data item gives us the latest available image
data "google_compute_image" "ubuntu1804image" {
  family  = var.image_family
  project = var.image_project
}

# we want our instances to be able to talk to each other directly
# hence we add them all to a dedicated network
resource "google_compute_network" "celestial-network" {
  name                    = "celestial-network"
  description             = "This network connects Celestial hosts and coordinator."
  auto_create_subnetworks = false
}

# within our network, we need a subnet for this region that has the correct
# IP address range
resource "google_compute_subnetwork" "celestial-subnet" {
  name          = "celestial-subnetwork"
  ip_cidr_range = "192.168.10.0/24"
  region        = var.gcp_region
  network       = google_compute_network.celestial-network.id
}

# we need to explicitly enable communication between instances in that network
# as google cloud doesn't add any rules by default
resource "google_compute_firewall" "celestial-net-firewall-internal" {
  name          = "celestial-net-firewall-internal"
  description   = "This firewall allows internal communication in the network."
  direction     = "INGRESS"
  network       = google_compute_network.celestial-network.id
  source_ranges = ["${google_compute_subnetwork.celestial-subnet.ip_cidr_range}"]

  allow {
    protocol = "all"
  }
}

# we also need to enable ssh ingress to our machines
resource "google_compute_firewall" "celestial-net-firewall-ssh" {
  name          = "celestial-net-firewall-ssh"
  description   = "This firewall allows ssh connections to our instances."
  network       = google_compute_network.celestial-network.id
  direction     = "INGRESS"
  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}


# the coordinator instance runs Ubuntu 18.04 and has Docker installed
resource "google_compute_instance" "celestial-coordinator" {
  name         = "celestial-coordinator"
  machine_type = var.coordinator_type
  zone         = local.zone

  boot_disk {

    initialize_params {
      image = data.google_compute_image.ubuntu1804image.self_link
    }
  }

  # adapter for internal network
  network_interface {
    subnetwork = google_compute_subnetwork.celestial-subnet.self_link
    network_ip = "192.168.10.2"
    # put this empty block in to get a public IP
    access_config {
    }
  }
  # install Docker
  # you can do this manually if you want or even build custom images
  # for our purposes, the metadata_startup_script is a good place to start
  metadata_startup_script = "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"

  service_account {
    scopes = ["cloud-platform"]
  }
}

# we need to create an image for our hosts
# this needs a custom license to use nested virtualization
resource "google_compute_image" "celestial-host-image" {
  name = "celestial-host-image"
  #   source_disk = google_compute_disk.celestial-host-disk.self_link
  source_image = data.google_compute_image.ubuntu1804image.self_link
  licenses     = ["https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"]
}

# the host instances run Ubuntu 18.04 and have all the necessary files
resource "google_compute_instance" "celestial-hosts" {
  name         = "celestial-host-${count.index}"
  machine_type = var.host_type
  zone         = local.zone
  count        = var.host_count

  boot_disk {

    initialize_params {
      image = google_compute_image.celestial-host-image.self_link
    }
  }

  # adapter for internal network
  network_interface {
    subnetwork = google_compute_subnetwork.celestial-subnet.self_link
    # ip addresses should be 192.168.10.{3..n}
    # if you have more than 251 hosts, that's not going to work
    network_ip = "192.168.10.${count.index + 3}"
    # put this empty block in to get a public IP
    access_config {
    }
  }

  # install Docker
  # you can do this manually if you want or even build custom images
  # for our purposes, the metadata_startup_script is a good place to start
  metadata_startup_script = <<EOF
#!/bin/bash

# we need the /celestial folder available on the hosts
sudo mkdir -p /celestial

# we also need wireguard and ipset as dependencies
sudo apt-get update
sudo apt-get install \
    --no-install-recommends \
    --no-install-suggests \
    -y wireguard ipset

# and we need firecracker on the machine
# download the current release
curl -fsSL -o firecracker-v0.25.2-x86_64.tgz \
    https://github.com/firecracker-microvm/firecracker/releases/download/v0.25.2/firecracker-v0.25.2-x86_64.tgz
tar -xvf firecracker-v0.25.2-x86_64.tgz
# and add the firecracker and jailer binaries
sudo mv release-v0.25.2-x86_64/firecracker-v0.25.2-x86_64 /usr/local/bin/firecracker
sudo mv release-v0.25.2-x86_64/seccompiler-bin-v0.25.2-x86_64 /usr/local/bin/jailer

# sometimes it can also be helpful to increase process and file handler
# limits on your host machines:
cat << END > /home/ubuntu/limits.conf
* soft nofile 64000
* hard nofile 64000
root soft nofile 64000
root hard nofile 64000
* soft nproc 64000
* hard nproc 64000
root soft nproc 64000
root hard nproc 64000
END
sudo mv /home/ubuntu/limits.conf /etc/security/limits.conf
EOF

  service_account {
    scopes = ["cloud-platform"]
  }
}
