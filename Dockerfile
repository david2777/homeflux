FROM ubuntu:20.04

MAINTAINER David DuVoisin "daduvo11@gmail.com"

RUN mkdir /app

WORKDIR /app

COPY . /app/

RUN apt update

RUN apt apt install software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt install python3.9

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

RUN python3.9 get-pip.py

RUN python3.9 -m pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app/python"

CMD ["python3.9", "-m", "homeflux.app"]
