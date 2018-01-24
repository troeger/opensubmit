#!/bin/bash
set -e

# Wait for postgres to come up
while ! nc -z db 5432 2>/dev/null
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
apache2ctl -D FOREGROUND
