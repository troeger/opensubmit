# The Google Cloud Engine region to be used
variable "region" {default = "europe-west3"}

# Most Google images, epecially COS, do not allow root login, so we need to operate as normal user.
variable "account" {default = "ptr_troeger"}

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
    external_ip = "${google_compute_address.opensubmit.address}"
  }
}

# Create virtual machine 
resource "google_compute_instance" "opensubmit" {
  name         = "opensubmit" 
  machine_type = "f1-micro" 
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
  # This even breaks the remote_exec provisioner of TerraForm.
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
    sshKeys = "${var.account}:${tls_private_key.vmkey.public_key_openssh}"
    # Startup scripts run as root anyway, no sudo needed.
    startup-script = "/home/${var.account}/startup.sh"
  }

  connection {
    type     = "ssh"
    user     = "${var.account}"
    private_key = "${tls_private_key.vmkey.private_key_pem}"
  }

  provisioner "file" {
    content     = "${data.template_file.docker-compose-yml.rendered}"
    destination = "docker-compose.yml"
  }

  # Store the startup script in the VM
  # In short, this runs docker-compose from a docker image to fire up
  # our customized docker-compose.yml (see data.template_file.docker-compose-yml above)
  # We basically run Docker to run Docker Compose which starts our Docker images in detached mode.
  # Phew.
  provisioner "file" {
    content     = <<EOF
#!/bin/sh
docker run -v /var/run/docker.sock:/var/run/docker.sock -v "$PWD:/rootfs/$PWD" -w="/rootfs/$PWD" docker/compose:1.13.0 up -d
EOF
    destination = "/home/${var.account}/startup.sh"
  }

  # Fix permissions and run startup script in instance as last step.
  provisioner "remote-exec" {
    inline = [
      "chmod u+x startup.sh",
      "sudo /home/${var.account}/startup.sh"
    ]
  }
}
