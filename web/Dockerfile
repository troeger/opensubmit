# Dockerfile for OpenSubmit web application
#
# Note 1: This only works with PostgreSQL
# Note 2: A number of env variables is needed to run
#         the application. Check docker-entry.sh.

FROM ubuntu

# Prepare Apache environment
RUN apt-get update \
    && apt-get install -y locales apache2 apache2-utils python3 python3-pip libapache2-mod-wsgi-py3 netcat \
    && rm -rf /var/lib/apt/lists/* \
    && rm /etc/apache2/sites-enabled/000-default.conf \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8
COPY ./docker/httpd.conf /etc/apache2/sites-enabled/httpd.conf
COPY ./docker/docker-entry.sh /docker-entry.sh

# Install dependencies explicitely for Docker caching
RUN mkdir /install
COPY requirements.txt /install
RUN pip3 install -r /install/requirements.txt psycopg2-binary

# Install existing wheel of OpenSubmit
# Call "make" if this step fails due to missing .whl files
COPY dist/*.whl /install/
RUN pip3 install /install/*.whl

# Enable django-admin in interactive mode when running
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE opensubmit.settings

EXPOSE 80
ENTRYPOINT ["/docker-entry.sh"]
