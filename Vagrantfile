VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell",
    inline: "sudo apt-get update; sudo apt-get -y install python-pip libpq-dev python-dev apache2 libapache2-mod-wsgi"
  config.vm.box = "ubuntu/trusty32"
  config.vm.network "forwarded_port", guest: 80, host: 8080
end
