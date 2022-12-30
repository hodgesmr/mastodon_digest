#syntax=docker/dockerfile:1

FROM --platform=${TARGETPLATFORM} python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1

ARG WORKDIR
WORKDIR $WORKDIR

COPY requirements.txt .

# Cache pip files between runs for faster runtime
RUN --mount=type=cache,id=pip-cache-${TARGETPLATFORM},target=/root/.cache \
      set -ex \
      && mkdir -p venv \
      && python3 -m venv venv/ \
      && venv/bin/pip install --upgrade pip \
      && venv/bin/pip install -r requirements.txt

COPY templates/ ./templates/
COPY *.py ./

# Moved down to end of file to avoid messing with the pip cache always being invalidated by the values
# changing between runs (especially BUILD_DATE which is essentially "now()")
ARG BUILD_DATE
ARG NAME
ARG ORG
ARG VCS_REF
ARG VENDOR
ARG VERSION

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name=$NAME \
      org.label-schema.description="A Python script that aggregates recent popular tweets from your Mastodon timeline " \
      org.label-schema.url="https://github.com/${ORG}/${NAME}" \
      org.label-schema.vcs-url="https://github.com/${ORG}/${NAME}" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vendor=$VENDOR \
      org.label-schema.version=$VERSION \
      org.label-schema.docker.schema-version="1.0" \
      org.label-schema.docker.cmd="docker run ${ORG}/${NAME}"

ENTRYPOINT ["venv/bin/python3", "run.py"]
