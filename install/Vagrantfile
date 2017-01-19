VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
  apt-get update
  sudo apt-get -y install python-pip libpq-dev python-dev apache2 libapache2-mod-wsgi postfix alpine

  pip uninstall -y opensubmit-web
  pip install --upgrade /vagrant/opensubmit-web-*
  opensubmit-web configure

  rm -f /etc/opensubmit/settings.ini
  mkdir -p /etc/opensubmit
  echo "[general]"  >> /etc/opensubmit/settings.ini
  echo "DEBUG: False"  >> /etc/opensubmit/settings.ini
  echo "[server]"  >> /etc/opensubmit/settings.ini
  echo "HOST: http://localhost:8080"  >> /etc/opensubmit/settings.ini
  echo "HOST_DIR: submit"  >> /etc/opensubmit/settings.ini
  echo "MEDIA_ROOT: /tmp/"  >> /etc/opensubmit/settings.ini
  echo "LOG_FILE: /var/log/opensubmit.log"  >> /etc/opensubmit/settings.ini
  echo "TIME_ZONE: Europe/Berlin"  >> /etc/opensubmit/settings.ini
  echo "SECRET_KEY: uzfp=4gv1u((#hb*#o3*4^v#u#g9k8-)us2nw^)@rz0-$2-23)"  >> /etc/opensubmit/settings.ini
  echo "[database]"  >> /etc/opensubmit/settings.ini
  echo "DATABASE_ENGINE: sqlite3"  >> /etc/opensubmit/settings.ini
  echo "DATABASE_NAME: /tmp/database.sqlite"  >> /etc/opensubmit/settings.ini
  echo "DATABASE_USER:"  >> /etc/opensubmit/settings.ini
  echo "DATABASE_PASSWORD:"  >> /etc/opensubmit/settings.ini
  echo "DATABASE_HOST:"  >> /etc/opensubmit/settings.ini
  echo "DATABASE_PORT:"  >> /etc/opensubmit/settings.ini
  echo "[executor]"  >> /etc/opensubmit/settings.ini
  echo "SHARED_SECRET: 49846zut93purfh977TTTiuhgalkjfnk89"  >> /etc/opensubmit/settings.ini
  echo "[admin]"  >> /etc/opensubmit/settings.ini
  echo "ADMIN_NAME: Super Admin"  >> /etc/opensubmit/settings.ini
  echo "ADMIN_EMAIL: root@localhost"  >> /etc/opensubmit/settings.ini
  echo "[login]"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_OPENID: True"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_DESCRIPTION: StackExchange"  >> /etc/opensubmit/settings.ini
  echo "OPENID_PROVIDER: https://openid.stackexchange.com"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_TWITTER: False"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_TWITTER_OAUTH_KEY:"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_TWITTER_OAUTH_SECRET:"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_GOOGLE: False"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_GOOGLE_OAUTH_KEY:"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_GOOGLE_OAUTH_SECRET:"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_GITHUB: False"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_GITHUB_OAUTH_KEY:"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_GITHUB_OAUTH_SECRET:"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_SHIB: False"  >> /etc/opensubmit/settings.ini
  echo "LOGIN_SHIB_DESCRIPTION: Shibboleth" >> /etc/opensubmit/settings.ini

  service apache2 stop
  rm /etc/apache2/sites-enabled/000-default.conf
  echo "<VirtualHost *:80>" >> /etc/apache2/sites-enabled/000-default.conf
  echo "  Include /etc/opensubmit/apache24.conf" >> /etc/apache2/sites-enabled/000-default.conf
  echo "</VirtualHost>" >> /etc/apache2/sites-enabled/000-default.conf

  opensubmit-web configure
  service apache2 start

  date > /etc/vagrant_provisioned_at
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty32"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.provision "shell", inline: $script
end
