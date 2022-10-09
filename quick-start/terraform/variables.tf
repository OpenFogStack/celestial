variable "gcp_project" {}

variable "gcp_region" {}

variable "gcp_zone" {}

variable "coordinator_type" {
  default = "n2-standard-8"
}

variable "host_type" {
  default = "n2-standard-32"
}

variable "host_count" {
  default = 2
}

# change this only if you know what you're doing!
variable "image_family" {
  default = "ubuntu-1804-lts"
}

variable "image_project" {
  default = "ubuntu-os-cloud"
}
