# Instead of putting the sources into the container,
# we install the official wheel. This provides
# additional testing for the PyPI install packages,
# but assumes that a build happened before.
#
# In short: Use "make docker" in the root directory

FROM ubuntu
ENV PYTHONUNBUFFERED 1
# Enable django-admin in interactive mode
ENV DJANGO_SETTINGS_MODULE opensubmit.settings

# Prepare Apache environment
RUN apt-get update \
    && apt-get install -y apache2 apache2-utils python3 python3-pip libapache2-mod-wsgi-py3 netcat \
    && rm -rf /var/lib/apt/lists/* \
    rm /etc/apache2/sites-enabled/000-default.conf
COPY ./docker/httpd.conf /etc/apache2/sites-enabled/httpd.conf

# Additionally install Postgres drivers
RUN pip3 install psycopg2

# Install existing wheel
RUN mkdir /install
COPY dist/*.whl /install
RUN pip3 install /install/*.whl

# Create OpenSubmit and Apache configuration file
RUN opensubmit-web configcreate --server-host=http://localhost:8000 \
                                --server-mediaroot=/data/media/ \
                                --database-name=opensubmit \
                                --database-user=opensubmit \
                                --database-password=opensubmit \
                                --database-host=db \
                                --database-engine=postgresql_psycopg2 \
 && opensubmit-web apachecreate

COPY ./docker/docker-entry.sh /docker-entry.sh
EXPOSE 80
ENTRYPOINT ["/docker-entry.sh"]
