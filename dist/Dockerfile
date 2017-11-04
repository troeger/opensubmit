# Docker file for the OpenSubmit web application
# Build the Docker image with "docker build -t opensubmit-web ." in this directory
# Run the image with "docker run -dit -p 127.0.0.1:80:80 opensubmit-web"

FROM debian:stable	

RUN apt-get update && apt-get install -y \
    apache2 \
	libapache2-mod-wsgi-py3 \
	python3-pip; \
	apt-get clean

EXPOSE 80

COPY *.whl /tmp/

RUN pip3 install /tmp/opensubmit_web*.whl

COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY settings.ini /etc/opensubmit/settings.ini

RUN opensubmit-web configure; \
	opensubmit-web createdemo

