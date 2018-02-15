# The Google Cloud Engine region to be used
variable "region" {default = "europe-west3"}

# The Google Cloud Engine account name
variable "account" {default = "root"}

# A mount point without "noexec".
# Mainly a problem with the COS images.
variable "script_storage" {default = "/var/lib/docker"}


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

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"
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
    startup-script = "${var.script_storage}/startup.sh"
  }

  connection {
    type     = "ssh"
    user     = "${var.account}"
    private_key = "${tls_private_key.vmkey.private_key_pem}"
    script_path = "${var.script_storage}/terraform.sh"
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
    destination = "${var.script_storage}/startup.sh"
  }

  # Run startup script in instance as last step
  # This currently fails with the Google COS image, so you have to do this manually
  provisioner "remote-exec" {
    inline = [
      "chmod u+x ${var.script_storage}/startup.sh",
      "sudo google_metadata_script_runner --script-type startup"
    ]
  }
}
