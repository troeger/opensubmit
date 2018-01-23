# Instead of putting the sources into the container,
# we install the official wheel. This provides
# additional testing for the PyPI install packages,
# but assumes that a build happened before.
#
# In short: Use "make docker" in the root directory

FROM ubuntu
ENV PYTHONUNBUFFERED 1

# Prepare Apache environment
RUN apt-get update; apt-get install -y apache2 apache2-utils python3 python3-pip libapache2-mod-wsgi-py3
RUN rm /etc/apache2/sites-enabled/000-default.conf
COPY dist/httpd.conf /etc/apache2/sites-enabled/httpd.conf
EXPOSE 80

# Install existing wheel
RUN mkdir /install
COPY dist/*.whl /install
RUN pip3 install /install/*.whl

# Run initial configuration of OpenSubmit
RUN mkdir -p /etc/opensubmit
COPY opensubmit/settings_template.ini /etc/opensubmit/settings.ini
RUN opensubmit-web configure

# Enable django-admin in interactive mode
# (docker run -it --entrypoint /bin/bash <id>)
ENV DJANGO_SETTINGS_MODULE opensubmit.settings

ENTRYPOINT ["apache2ctl", "-D", "FOREGROUND"]
