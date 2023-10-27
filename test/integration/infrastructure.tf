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
  default = "a"
}

variable "host_type" {
  default = "n2-standard-2"
}

output "zone" {
  value = local.zone
}

output "host_ip" {
  value = google_compute_instance.celestial-test-host.network_interface.0.access_config.0.nat_ip
}

output "host_name" {
  value = format("%s.%s.%s", google_compute_instance.celestial-test-host.name, local.zone, var.gcp_project)
}

output "host_id" {
  value = google_compute_instance.celestial-test-host.name
}

output "project" {
  value = var.gcp_project
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
    ports    = ["22"]
  }
}

# reserve a static external IP address
resource "google_compute_address" "celestial-test-host-ip" {
  name = "celestial-test-host-ip"
}

# we need to create an image for our hosts
# this needs a custom license to use nested virtualization
resource "google_compute_image" "celestial-test-host-image" {
  name = "celestial-test-host-image"
  #   source_disk = google_compute_disk.celestial-host-disk.self_link
  source_image = data.google_compute_image.ubuntu2204image.self_link
  licenses     = ["https://www.googleapis.com/compute/v1/projects/ubuntu-os-cloud/global/licenses/ubuntu-2204-lts", "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"]
}

# the host instance runs Ubuntu 22.04
resource "google_compute_instance" "celestial-test-host" {
  name         = "celestial-test-host"
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

    # use the static IP address
    access_config {
      nat_ip = google_compute_address.celestial-test-host-ip.address
    }
  }

  service_account {
    scopes = ["cloud-platform"]
  }
}
