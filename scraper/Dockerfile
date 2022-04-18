FROM python:3.10-alpine

RUN \
    apk update \
    && apk add --no-cache \
        gcc \
        musl-dev \
        libffi-dev

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV APP_DIR=/home/scraper/
RUN mkdir $APP_DIR
WORKDIR $APP_DIR

COPY scrapy.cfg requirements.txt $APP_DIR/
RUN python -m pip install -r requirements.txt
