FROM ubuntu:20.04

MAINTAINER David DuVoisin "daduvo11@gmail.com"

RUN mkdir /app

WORKDIR /app

COPY . /app/

RUN apt-get update

RUN apt-get install curl --assume-yes

RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py

RUN python get-pip.py

RUN python -m pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app/python"

CMD ["python", "-m", "homeflux.app"]
