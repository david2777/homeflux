FROM ubuntu:20.04

MAINTAINER David DuVoisin "daduvo11@gmail.com"

RUN mkdir /app

WORKDIR /app

COPY . /app/

RUN apt-get update

RUN apt-get install software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get install python3-9

RUN apt-get install python3-pip

RUN python3.9 -m pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app/python"

CMD ["python3.9", "-m", "homeflux.app"]
