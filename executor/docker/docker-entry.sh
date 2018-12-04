#!/bin/bash
set -e

# Docker image startup script
#
# Expects the following environment variables:
#
# OPENSUBMIT_SERVER_HOST: URL of the server installation

# (Re-)create OpenSubmit configuration from env variables
opensubmit-exec configcreate $OPENSUBMIT_SERVER_HOST

echo "Waiting for web server at $OPENSUBMIT_SERVER_HOST to start ..."
# Wait for web server to come up
until $(curl --output /dev/null --silent --head --fail $OPENSUBMIT_SERVER_HOST); do
    echo '... still waiting ...'
    sleep 5
done
echo "Web server started."

# Perform config test, triggers also registration
/usr/local/bin/opensubmit-exec configtest

# Run "opensubmit-exec run" every minute
cron -f
