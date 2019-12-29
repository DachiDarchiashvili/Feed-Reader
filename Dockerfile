FROM python:3.7.6-alpine

MAINTAINER Dachi Darchiashvili <darchiashvilidachi@yahoo.com>


RUN mkdir -p /src/feed_reader
WORKDIR /src/feed_reader

ADD apps /src/feed_reader/apps
ADD feed_fetcher /src/feed_reader/feed_fetcher
ADD feed_reader /src/feed_reader/feed_reader
ADD static /src/feed_reader/static
ADD templates /src/feed_reader/templates
ADD manage.py /src/feed_reader/manage.py
ADD requirements.txt /src/feed_reader/requirements.txt

RUN apk add --update --no-cache \
        build-base \
        gcc musl-dev \
        linux-headers \
        pcre-dev \
        postgresql-libs \
        && apk add --no-cache --virtual \
        .build-deps \
        postgresql-dev

RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir
RUN rm -rf requirements.txt

EXPOSE 8000

CMD [ "uwsgi", \
      "--vacuum", \
      "--master", \
      "--enable-threads", \
      "--process", "10", \
      "--chdir", "/src/feed_reader", \
      "--http-socket", "0.0.0.0:8000", \
      "--socket", "0.0.0.0:8000", \
      "--wsgi-file", "feed_reader/wsgi.py", \
      "--module", "feed_reader.wsgi:application" ]