FROM ubuntu:20.04

RUN apt-get update
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8   

EXPOSE 8080
#VOLUME /usr/src/app/public
WORKDIR /usr/src/app

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y \
        build-essential openssl libssl-dev swig libtiff5-dev libjpeg8-dev zlib1g-dev \
        libfreetype6-dev liblcms2-dev libwebp-dev tcl-dev tk-dev libpq-dev python-dev \
        python3-pip

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y uwsgi uwsgi-plugin-python3

COPY requirements/ requirements/

#RUN rm -rf public/*

RUN pip3 install --no-cache-dir -r requirements/base.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=pirra_web.settings.prod

CMD [ "uwsgi", \
               #"--socket", "0.0.0.0:8080", \
               "--http-socket", "0.0.0.0:8080", \
               "--plugins", "python3", \
               "--protocol", "uwsgi", \
               "--wsgi", "pirra_web.wsgi:application" ]