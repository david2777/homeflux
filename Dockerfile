FROM ubuntu:20.04

MAINTAINER David DuVoisin "daduvo11@gmail.com"

RUN mkdir /app

WORKDIR /app

COPY . /app/

RUN sudo apt update

RUN sudo apt sudo apt install software-properties-common

RUN sudo add-apt-repository ppa:deadsnakes/ppa

RUN sudo apt install python3.9

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

RUN python3.9 get-pip.py

RUN python3.9 -m pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app/python"

CMD ["python3.9", "-m", "homeflux.app"]
