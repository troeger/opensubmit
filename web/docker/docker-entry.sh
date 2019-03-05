#!/bin/bash
set -e

# Docker image startup script

# (Re-)create OpenSubmit configuration from env variables
opensubmit-web configcreate 

# (Re-)create Apache configuration from env variables
opensubmit-web apachecreate

# Show config on stdout, for Docker debugging purposes
opensubmit-web dumpconfig

# Wait for postgres to come up
echo "Waiting for database to come up ..."
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

# perform relevant database migrations, check file permissions
opensubmit-web configtest

# Make sure Apache really loads the new configs
/etc/init.d/apache2 stop
/etc/init.d/apache2 start

tail -f /var/log/apache2/opensubmit_error.log