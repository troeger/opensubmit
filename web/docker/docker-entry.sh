#!/bin/bash
set -e

# Docker image startup script

# (Re-)create OpenSubmit configuration from env variables
opensubmit-web configcreate 
opensubmit-web apachecreate
opensubmit-web dumpconfig

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
opensubmit-web ensureroot

# Start Apache
/etc/init.d/apache2 stop
/etc/init.d/apache2 start

tail -f /tmp/opensubmit.log  