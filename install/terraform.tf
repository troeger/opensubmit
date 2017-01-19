# Terraform configuration for AWS deployment of OpenSubmit.
#
# There is no need to edit this file.
#
# Edit terraform.tfvars instead.
#

output "ssh" {
    value = "ssh ubuntu@${aws_instance.web.public_dns}"
}

output "url" {
    value = "http://${aws_instance.web.public_dns}/submit"
}

variable "ssh_key" {
  description = "Path to your SSH public key."
}

variable "aws_access_key" {
  description = "Your AWS access key."
}

variable "aws_secret_key" {
  description = "Your AWS secret key."
}

variable "aws_region" {
  description = "AWS region for your OpenSubmit installation."
}

provider "aws" {
  region = "${var.aws_region}"
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
}

resource "aws_security_group" "default" {
  name        = "OpenSubmit"
  description = "Default security group for OpenSubmit."

  # SSH access from anywhere
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "auth" {
  key_name   = "OpenSubmit Key"
  public_key = "${file(var.ssh_key)}"
}

# Ubuntu 32-Bit 14.04 LTS (Trusty Tahr)
variable "aws_amis" {
  default = {
		ap-northeast-1 = "ami-15dd9214"
		ap-southeast-1 = "ami-aa6c30f8"
		ap-southeast-2 = "ami-15b8dd2f"
		eu-west-1 = "ami-ff498688"
		sa-east-1 = "ami-910aa68c"
		us-east-1 = "ami-4e8c7f26"
		us-west-1 = "ami-806265c5"
		us-west-2 = "ami-ad40329d"
  }
}

resource "random_id" "webapp_key" {
  byte_length = 8
}

resource "random_id" "executor_key" {
  byte_length = 8
}


resource "aws_instance" "web" {
  ami = "${lookup(var.aws_amis, var.aws_region)}"
  instance_type = "t1.micro"

  key_name = "${aws_key_pair.auth.id}"
  connection {
    user = "ubuntu"
  }
  vpc_security_group_ids = ["${aws_security_group.default.id}"]

  provisioner "file" {
        source = "install.sh"
        destination = "/tmp/install.sh"
  }


  provisioner "remote-exec" {
    inline = [
      "sudo chmod +x /tmp/install.sh",
      "sudo /tmp/install.sh ${aws_instance.web.public_dns} ${random_id.webapp_key.hex} ${random_id.executor_key.hex}"
    ]
  }
}
