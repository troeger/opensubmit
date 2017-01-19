#!/bin/sh
#
# This installs a fresh OpenSubmit inside a fresh Ubuntu box.
# Don't use this directly. Use Vagrant or Terraform instead.
#
# Expects root rights.
#
# install.sh [host_dns_name] [random_key1] [random_key2]

export DEBIAN_FRONTEND="noninteractive"
apt-get -y update
echo "postfix postfix/main_mailer_type select Internet Site" | debconf-set-selections
echo "postfix postfix/mailname    string  $1" | debconf-set-selections
apt-get -y install python-pip libpq-dev python-dev apache2 libapache2-mod-wsgi postfix alpine
pip install --upgrade opensubmit-web
# Workaround for https://github.com/troeger/opensubmit/issues/163
pip install python-social-auth==0.2.21
opensubmit-web configure
rm -f /etc/opensubmit/settings.ini
echo "[general]"  >> /etc/opensubmit/settings.ini
echo "DEBUG: False"  >> /etc/opensubmit/settings.ini
echo "[server]"  >> /etc/opensubmit/settings.ini
echo "HOST: http://$1"  >> /etc/opensubmit/settings.ini
echo "HOST_DIR: submit"  >> /etc/opensubmit/settings.ini
echo "MEDIA_ROOT: /tmp/"  >> /etc/opensubmit/settings.ini
echo "LOG_FILE: /var/log/opensubmit.log"  >> /etc/opensubmit/settings.ini
echo "TIME_ZONE: Europe/Berlin"  >> /etc/opensubmit/settings.ini
echo "SECRET_KEY: $2"  >> /etc/opensubmit/settings.ini
echo "[database]"  >> /etc/opensubmit/settings.ini
echo "DATABASE_ENGINE: sqlite3"  >> /etc/opensubmit/settings.ini
echo "DATABASE_NAME: /tmp/database.sqlite"  >> /etc/opensubmit/settings.ini
echo "DATABASE_USER:"  >> /etc/opensubmit/settings.ini
echo "DATABASE_PASSWORD:"  >> /etc/opensubmit/settings.ini
echo "DATABASE_HOST:"  >> /etc/opensubmit/settings.ini
echo "DATABASE_PORT:"  >> /etc/opensubmit/settings.ini
echo "[executor]"  >> /etc/opensubmit/settings.ini
echo "SHARED_SECRET: $3"  >> /etc/opensubmit/settings.ini
echo "[admin]"  >> /etc/opensubmit/settings.ini
echo "ADMIN_NAME: The Admin"  >> /etc/opensubmit/settings.ini
echo "ADMIN_EMAIL: root@$1"  >> /etc/opensubmit/settings.ini
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
service apache2 restart
