FROM python:3.10

ARG PROJECT
WORKDIR /opt/${PROJECT}

RUN apt-get update && apt-get install -y make

COPY ./requirements.txt ${WORKDIR}
RUN python -m pip install -r requirements.txt
