FROM ubuntu:14.04
MAINTAINER Yann Malet <yann.malet@gmail.com>
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python python-pip python-dev \
    build-essential locales git-core \
    libpq-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y curl

EXPOSE 8080
ADD . /srv/botbot-web
WORKDIR /srv/botbot-web

RUN pip install -r requirements.txt \
    --index-url "http://172.17.42.1:3141/root/pypi/+simple"\
    --timeout=120

CMD ["python manage.py --settings=botbot.settings"]

