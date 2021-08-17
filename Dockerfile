FROM ubuntu:20.04

MAINTAINER David DuVoisin "daduvo11@gmail.com"

RUN mkdir /app

WORKDIR /app

COPY . /app/

RUN apt-get update -y

RUN apt-get install python3 python3-pip -y

RUN python3 -m pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app/python"

CMD python3 -m homeflux.app
