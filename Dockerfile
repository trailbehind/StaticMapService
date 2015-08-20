FROM ubuntu:14.04
MAINTAINER Jesse Crocker "jesse@gaiagps.com"

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C300EE8C; \
    echo "deb http://ppa.launchpad.net/nginx/development/ubuntu trusty main" > /etc/apt/sources.list.d/nginx.list; \
    apt-get update; \
    apt-get install -q -y supervisor nginx python-gdal python-mapnik2 python-pil python-dev python-virtualenv

ADD .docker/depends /depends

RUN python /depends/get-pip.py virtualenv;
RUN virtualenv --system-site-packages /opt/ve/deploy; \
    /opt/ve/deploy/bin/pip install -r /depends/requirements.txt

RUN useradd deploy

ADD staticMaps /opt/apps/staticMaps
ADD .docker/nginx /opt/nginx
ADD .docker/supervisor /opt/supervisor
ADD .docker/bin /opt/bin/deploy
ADD .docker/rsyslog.conf /etc/rsyslog.conf
EXPOSE 8000
CMD ["/opt/bin/deploy/run_supervisord.sh", "web"]
