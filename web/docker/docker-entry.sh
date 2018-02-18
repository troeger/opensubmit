#!/bin/bash
set -e

# Docker image startup script

# (Re-)create OpenSubmit configuration from env variables
# Create OpenSubmit and Apache configuration file
opensubmit-web configcreate --server-host=$OPENSUBMIT_SERVER_HOST \
                            --server-mediaroot=$OPENSUBMIT_SERVER_MEDIAROOT \
                            --server-hostaliases=$OPENSUBMIT_SERVER_HOST_ALIASES \
                            --database-name=$OPENSUBMIT_DATABASE_NAME \
                            --database-user=$OPENSUBMIT_DATABASE_USER \
                            --database-password=$OPENSUBMIT_DATABASE_PASSWORD \
                            --database-host=$OPENSUBMIT_DATABASE_HOST \
                            --database-engine=postgresql \
                            --login-google-oauth-key=$OPENSUBMIT_LOGIN_GOOGLE_OAUTH_KEY \
                            --login-google-oauth-secret=$OPENSUBMIT_LOGIN_GOOGLE_OAUTH_SECRET

opensubmit-web apachecreate

# Wait for postgres to come up
while ! nc -z $OPENSUBMIT_DATABASE_HOST 5432 2>/dev/null
do
    let elapsed=elapsed+1
    if [ "$elapsed" -gt 90 ] 
    then
        echo "Could not connect to database container."
        exit 1
    fi  
    sleep 1;
done
echo "Database is up."

# perform relevant database migrations
opensubmit-web configtest

# Start Apache
rm -f /var/run/apache2/apache2.pid
apache2ctl -D FOREGROUND
