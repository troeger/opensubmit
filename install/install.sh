#!/bin/sh
#
# This installs a fresh OpenSubmit inside a fresh Ubuntu box.
# Don't use this directly. Use Vagrant or Terraform instead.
#
# Expects root rights.
#
# install.sh [host_dns_name] [random_key1] [random_key2]

sudo apt-get -y update
sudo apt-get -q -y install python-pip libpq-dev python-dev apache2 libapache2-mod-wsgi postfix alpine
sudo pip install --upgrade opensubmit-web
# Workaround for https://github.com/troeger/opensubmit/issues/163
sudo pip install python-social-auth==0.2.21
sudo opensubmit-web configure
sudo rm -f /etc/opensubmit/settings.ini
sudo echo "[general]"  >> /etc/opensubmit/settings.ini
sudo echo "DEBUG: False"  >> /etc/opensubmit/settings.ini
sudo echo "[server]"  >> /etc/opensubmit/settings.ini
sudo echo "HOST: http://$1"  >> /etc/opensubmit/settings.ini
sudo echo "HOST_DIR: submit"  >> /etc/opensubmit/settings.ini
sudo echo "MEDIA_ROOT: /tmp/"  >> /etc/opensubmit/settings.ini
sudo echo "LOG_FILE: /var/log/opensubmit.log"  >> /etc/opensubmit/settings.ini
sudo echo "TIME_ZONE: Europe/Berlin"  >> /etc/opensubmit/settings.ini
sudo echo "SECRET_KEY: $2"  >> /etc/opensubmit/settings.ini
sudo echo "[database]"  >> /etc/opensubmit/settings.ini
sudo echo "DATABASE_ENGINE: sqlite3"  >> /etc/opensubmit/settings.ini
sudo echo "DATABASE_NAME: /tmp/database.sqlite"  >> /etc/opensubmit/settings.ini
sudo echo "DATABASE_USER:"  >> /etc/opensubmit/settings.ini
sudo echo "DATABASE_PASSWORD:"  >> /etc/opensubmit/settings.ini
sudo echo "DATABASE_HOST:"  >> /etc/opensubmit/settings.ini
sudo echo "DATABASE_PORT:"  >> /etc/opensubmit/settings.ini
sudo echo "[executor]"  >> /etc/opensubmit/settings.ini
sudo echo "SHARED_SECRET: $3"  >> /etc/opensubmit/settings.ini
sudo echo "[admin]"  >> /etc/opensubmit/settings.ini
sudo echo "ADMIN_NAME: The Admin"  >> /etc/opensubmit/settings.ini
sudo echo "ADMIN_EMAIL: root@$1"  >> /etc/opensubmit/settings.ini
sudo echo "[login]"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_OPENID: True"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_DESCRIPTION: StackExchange"  >> /etc/opensubmit/settings.ini
sudo echo "OPENID_PROVIDER: https://openid.stackexchange.com"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_TWITTER: False"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_TWITTER_OAUTH_KEY:"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_TWITTER_OAUTH_SECRET:"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_GOOGLE: False"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_GOOGLE_OAUTH_KEY:"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_GOOGLE_OAUTH_SECRET:"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_GITHUB: False"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_GITHUB_OAUTH_KEY:"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_GITHUB_OAUTH_SECRET:"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_SHIB: False"  >> /etc/opensubmit/settings.ini
sudo echo "LOGIN_SHIB_DESCRIPTION: Shibboleth" >> /etc/opensubmit/settings.ini
sudo service apache2 stop
sudo rm /etc/apache2/sites-enabled/000-default.conf
sudo echo "<VirtualHost *:80>" >> /etc/apache2/sites-enabled/000-default.conf
sudo echo "  Include /etc/opensubmit/apache24.conf" >> /etc/apache2/sites-enabled/000-default.conf
sudo echo "</VirtualHost>" >> /etc/apache2/sites-enabled/000-default.conf
sudo opensubmit-web configure
sudo service apache2 restart
