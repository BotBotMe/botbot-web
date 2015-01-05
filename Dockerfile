FROM ubuntu:14.04
MAINTAINER Yann Malet <yann.malet@gmail.com>
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python python-pip python-dev \
    libmemcached-dev \
    build-essential locales git-core \
    libpq-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y curl

EXPOSE 8080
ADD . /srv/botbot-web
WORKDIR /srv/botbot-web

RUN pip install -r requirements.txt -e . \
    --src /srv/python-src/\
    --timeout=120

CMD manage.py runserver 0.0.0.0:8080 --settings=botbot.settings

