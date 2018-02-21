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
RUN (crontab -l ; echo "* * * * * opensubmit-exec run >> /var/log/cron.log") | crontab

COPY ./docker/docker-entry.sh /docker-entry.sh
ENTRYPOINT ["/docker-entry.sh"]
