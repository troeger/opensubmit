# Dockerfile for OpenSubmit web application
#
# The following arguments must be provided and
# mostly rely on how your docker-compose.yml
# (or similar composition config) looks like.
#
# OPENSUBMIT_SERVER_HOST (depends on port mapping)
# OPENSUBMIT_SERVER_MEDIAROOT (depends on storage volume)
# OPENSUBMIT_DATABASE_NAME (depends on database image)
# OPENSUBMIT_DATABASE_USER (depends on database image)
# OPENSUBMIT_DATABASE_PASSWORD (depends on database image)
# OPENSUBMIT_DATABASE_HOST (depends on database image)
# OPENSUBMIT_DATABASE_ENGINE (depends on database image)
# OPENSUBMIT_DATABASE_DRIVER (depends on database image)

FROM ubuntu

# Prepare Apache environment
RUN apt-get update \
    && apt-get install -y apache2 apache2-utils python3 python3-pip libapache2-mod-wsgi-py3 netcat \
    && rm -rf /var/lib/apt/lists/* \
    rm /etc/apache2/sites-enabled/000-default.conf
COPY ./docker/httpd.conf /etc/apache2/sites-enabled/httpd.conf

# Install existing wheel of OpenSubmit
# Call "make" if this step fails due to missing .whl files
RUN mkdir /install
COPY dist/*.whl /install
RUN pip3 install /install/*.whl

# Enable django-admin in interactive mode when running
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE opensubmit.settings

ARG OPENSUBMIT_SERVER_HOST
ARG OPENSUBMIT_SERVER_MEDIAROOT
ARG OPENSUBMIT_DATABASE_NAME
ARG OPENSUBMIT_DATABASE_USER
ARG OPENSUBMIT_DATABASE_PASSWORD
ARG OPENSUBMIT_DATABASE_HOST
ARG OPENSUBMIT_DATABASE_ENGINE
ARG OPENSUBMIT_DATABASE_DRIVER

# Install python database driver
RUN pip3 install $OPENSUBMIT_DATABASE_DRIVER

# Create OpenSubmit and Apache configuration file
RUN opensubmit-web configcreate --server-host=$OPENSUBMIT_SERVER_HOST \
                                --server-mediaroot=$OPENSUBMIT_SERVER_MEDIAROOT \
                                --database-name=$OPENSUBMIT_DATABASE_NAME \
                                --database-user=$OPENSUBMIT_DATABASE_USER \
                                --database-password=$OPENSUBMIT_DATABASE_PASSWORD \
                                --database-host=$OPENSUBMIT_DATABASE_HOST \
                                --database-engine=$OPENSUBMIT_DATABASE_ENGINE \
 && opensubmit-web apachecreate

COPY ./docker/docker-entry.sh /docker-entry.sh
EXPOSE 80
ENTRYPOINT ["/docker-entry.sh"]
