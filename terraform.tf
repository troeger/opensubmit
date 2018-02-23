# A Terraform configuration to deploy the OpenSubmit stack
# on the Google cloud.
#
# The main idea is the execution of three Docker containers
# (web frontend, one test machine, PostgreSQL database)
# on one machine in the Google Compute Engine cloud.
#
# The Docker execution relies on a slightly modified version
# of our Docker Compose file (docker-compose-terraform.yml).
#

# The Google Cloud Engine region to be used
variable "region" {default = "europe-west3"}

# The Google Cloud user name, everything before the "@" sign.
variable "google_account" {default = "ptr_troeger"}

# The DNS zone for the installation, managed by the Google Cloud.
variable "dnszone" {default = "demo.open-submit.org"}

# Set through an external TFVARS file
variable "google_oauth_key" {}  
variable "google_oauth_secret" {} 
variable "twitter_oauth_key" {}
variable "twitter_oauth_secret" {}
variable "github_oauth_key" {}
variable "github_oauth_secret" {}

provider "google" {
  project     = "opensubmit"
  region      = "${var.region}"
  # get a service account key file at https://console.cloud.google.com/apis/credentials/serviceaccountkey
  credentials = "${file("google_account.json")}"
}

# Generate SSH key for further access
resource "tls_private_key" "vmkey" {
    algorithm = "RSA"
    rsa_bits = 4096
}

# Generate static address for web server
resource "google_compute_address" "opensubmit" {
  name = "opensubmit"
}

# Prepare tailored docker-compose file
data "template_file" "docker-compose-yml" {
  template = "${file("${path.module}/docker-compose-terraform.yml")}"

  vars {
    # Remove trailing dot from DNS entry name
    external_adr = "${substr(google_dns_record_set.www.name,0,length(google_dns_record_set.www.name)-1)}"
    external_ip = "${google_compute_address.opensubmit.address}"
    google_oauth_key="${var.google_oauth_key}"
    google_oauth_secret="${var.google_oauth_secret}"
    twitter_oauth_key="${var.twitter_oauth_key}"
    twitter_oauth_secret="${var.twitter_oauth_secret}"
    github_oauth_key="${var.github_oauth_key}"
    github_oauth_secret="${var.github_oauth_secret}"    
  }
}

# Create virtual machine 
resource "google_compute_instance" "opensubmit" {
  name         = "opensubmit" 
  machine_type = "g1-small" 
  zone         = "${var.region}-a" 
  allow_stopping_for_update = "true"

  # Automatically configure firewall rules for ingress HTTP
  tags = ["http-server"]

  service_account {
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  # Google COS does not work with this setup, since they have no mount point to
  # store and (sudo-)run executable scripts. Docker only. Everything is "noexec" or root-only,
  # and root account is forbidden.
  # This breaks the remote_exec provisioner of TerraForm.
  boot_disk {
    initialize_params {
      image = "coreos-cloud/coreos-stable"
    }
  }
 
  network_interface {
    network = "default"
    access_config {
         nat_ip = "${google_compute_address.opensubmit.address}"
    }
  }

  # Configure instance metadata
  metadata {
    # Establish our custom SSH key, so that the file provisioner can copy stuff
    sshKeys = "${var.google_account}:${tls_private_key.vmkey.public_key_openssh}"

    # Store cloud-init configuration which configers systemd to start our containers
    # In short, this runs docker-compose from a docker image to fire up
    # our customized docker-compose.yml (see data.template_file.docker-compose-yml above)
    # We basically run Docker to run Docker Compose which starts our Docker images in detached mode.
    # Phew.
    user-data = <<EOF
#cloud-config
write_files:
- path: /etc/systemd/system/opensubmit.service
  permissions: 0644
  owner: root
  content: |
    [Unit]
    Description=Start the OpenSubmit docker containers
    Requires=docker.service
    After=docker.service

    [Service]
    Restart=Always
    WorkingDirectory=/home/${var.google_account}

    ExecStart=/usr/bin/docker run -v /var/run/docker.sock:/var/run/docker.sock -v "/home/${var.google_account}:/rootfs/home/${var.google_account}" -w="/rootfs/home/${var.google_account}" docker/compose:1.13.0 up
    TimeoutSec=600

    ExecStop=/usr/bin/docker run -v /var/run/docker.sock:/var/run/docker.sock -v "/home/${var.google_account}:/rootfs/home/${var.google_account}" -w="/rootfs/home/${var.google_account}" docker/compose:1.13.0 down

    [Install]
    WantedBy=multi-user.target
EOF
  }

  connection {
    type     = "ssh"
    user     = "${var.google_account}"
    private_key = "${tls_private_key.vmkey.private_key_pem}"
  }

  provisioner "file" {
    content     = "${data.template_file.docker-compose-yml.rendered}"
    destination = "docker-compose.yml"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo systemctl enable opensubmit.service",
      "sudo systemctl start opensubmit.service"
    ]
  }
}

resource "google_dns_managed_zone" "opensubmit-zone" {
  name     = "opensubmit-zone"
  dns_name = "${var.dnszone}."

  # Google DNS uses rotating nameservers for the zones,
  # so ye need to change the parent DNS NS entry everytime
  # this resource is destroyed and re-created
  lifecycle {
      prevent_destroy = "true"
  }

}

output "name_servers" {
  value = "${google_dns_managed_zone.opensubmit-zone.name_servers}"
}


resource "google_dns_record_set" "www" {
  name = "www.${google_dns_managed_zone.opensubmit-zone.dns_name}"
  type = "A"
  ttl  = 300

  managed_zone = "${google_dns_managed_zone.opensubmit-zone.name}"

  rrdatas = ["${google_compute_address.opensubmit.address}"]
}

