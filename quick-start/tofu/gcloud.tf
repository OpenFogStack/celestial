#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

terraform {
  backend "local" {}
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

variable "gcp_project" {
  # default = YOUR_GCP_PROJECT_ID
}

variable "gcp_region" {
  default = "europe-west3"
}

variable "gcp_zone" {
  default = "c"
}

variable "coordinator_type" {
  default = "n2-standard-8"
}

variable "host_type" {
  default = "n2-standard-32"
}

variable "host_count" {
  default = 2
}

output "host_ip" {
  value = google_compute_instance.celestial-test-host.*.network_interface.0.access_config.0.nat_ip
}

# the zone variable must be within the region
# hence this weird setup
locals {
  zone = "${var.gcp_region}-${var.gcp_zone}"
}

# we use a version of Ubuntu 22.04 LTS
# this data item gives us the latest available image
data "google_compute_image" "ubuntu2204image" {
  family  = "ubuntu-2204-lts"
  project = "ubuntu-os-cloud"
}

# we want our instances to be able to talk to each other directly
# hence we add them all to a dedicated network
resource "google_compute_network" "celestial-test-network" {
  name                    = "celestial-test-network"
  description             = "This network connects Celestial hosts."
  auto_create_subnetworks = true
}

# we also need to enable ingress to our machines
resource "google_compute_firewall" "celestial-test-net-firewall-external" {
  name          = "celestial-test-net-firewall-external"
  description   = "This firewall allows external connections to our instance for ssh."
  network       = google_compute_network.celestial-test-network.id
  direction     = "INGRESS"
  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["22", "1969"]
  }
}

# and enable ingress between the machines
resource "google_compute_firewall" "celestial-test-net-firewall-internal" {
  name          = "celestial-test-net-firewall-internal"
  description   = "This firewall allows internal connections between our instances."
  network       = google_compute_network.celestial-test-network.id
  direction     = "INGRESS"
  source_ranges = formatlist("%s/32", google_compute_instance.celestial-test-host.*.network_interface.0.access_config.0.nat_ip)

  allow {
    protocol = "udp"
    ports    = ["1970"]
  }
  allow {
    protocol = "icmp"
  }
}


# we need to create an image for our hosts
# this needs a custom license to use nested virtualization
resource "google_compute_image" "celestial-test-host-image" {
  name         = "celestial-test-host-image"
  source_image = data.google_compute_image.ubuntu2204image.self_link
  licenses     = ["https://www.googleapis.com/compute/v1/projects/ubuntu-os-cloud/global/licenses/ubuntu-2204-lts", "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"]
}

# the host instance runs Ubuntu 22.04
resource "google_compute_instance" "celestial-test-host" {
  name         = "celestial-test-host-${count.index}"
  count        = var.host_count
  machine_type = var.host_type
  zone         = local.zone

  boot_disk {
    initialize_params {
      image = google_compute_image.celestial-test-host-image.self_link
    }
  }

  # adapter for internal network
  network_interface {
    network = google_compute_network.celestial-test-network.id
    # get an external IP address
    access_config {}
  }

  service_account {
    scopes = ["cloud-platform"]
  }
}
