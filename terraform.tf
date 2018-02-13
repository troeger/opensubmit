# The Google Cloud Engine region to be used
variable "region" {default = "europe-west3"}

# The Google Cloud Engine account name
variable "account" {default = "ptr_troeger"}

# The name of the docker image in the public Google container registry
variable "image" {default = "eu.gcr.io/opensubmit/web:v1"}

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

# Create virtual machine with CoreOS
resource "google_compute_instance" "opensubmit-web" {
  name         = "opensubmit-web" 
  machine_type = "f1-micro" 
  zone         = "${var.region}-a" 

  depends_on = ["tls_private_key.vmkey"]

  service_account {
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  boot_disk {
    initialize_params {
      image = "coreos-cloud/coreos-stable"
    }
  }
 
  network_interface {
    network = "default"

    access_config {
      // Ephemeral IP
    }
  }

  # Store public key in meta-data for VM, inserted by Google provisioning into the OS
  # Google does that for the default user name, so we need it here
  metadata {
    sshKeys = "${var.account}:${tls_private_key.vmkey.public_key_openssh}"
  }

  # Take existing local Docker image, tag it as needed and push it into the Google registry
  provisioner "local-exec" {
    command = <<EOT
      docker tag opensubmit_web ${var.image};
      gcloud docker -- push ${var.image}
EOT
  }

  # Now pull that image in the remote VM
  # "gcloud" is needed for auth against the container registry
  # To get it, we mimic the CoreOS alias definition for it here
  provisioner "remote-exec" {
    inline = [
      "(docker images google/cloud-sdk || docker pull google/cloud-sdk) > /dev/null",
      "docker run -v /var/run/docker.sock:/var/run/docker.sock google/cloud-sdk gcloud docker -- pull ${var.image}",
      "docker run ${var.image}"
    ]
    connection {
      type     = "ssh"
      user     = "${var.account}"
      private_key = "${tls_private_key.vmkey.private_key_pem}"
    }
  }
}
