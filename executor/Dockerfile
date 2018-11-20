# Dockerfile for OpenSubmit executor installation

FROM ubuntu

# Prepare Apache environment
RUN apt-get update \
    && apt-get install -y locales python3 python3-pip cron gcc make autoconf curl \
    && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# Install dependencies explicitely for Docker caching
RUN mkdir /install
COPY requirements.txt /install
RUN pip3 install -r /install/requirements.txt

# Install existing wheel of OpenSubmit executor
# Call "make" if this step fails due to missing .whl files
COPY dist/*.whl /install
RUN pip3 install /install/*.whl

# Enable django-admin in interactive mode when running
ENV PYTHONUNBUFFERED 1

RUN touch /var/log/cron.log
# Redirect output directly into Docker stdout / stderr
RUN echo "* * * * * /usr/local/bin/opensubmit-exec run > /proc/1/fd/1 2>/proc/1/fd/2\n" | crontab

COPY ./docker/docker-entry.sh /docker-entry.sh
ENTRYPOINT ["/docker-entry.sh"]
