FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1

ARG WORKDIR
ARG BUILD_DATE
ARG NAME
ARG ORG
ARG VCS_REF
ARG VENDOR
ARG VERSION

WORKDIR $WORKDIR

COPY requirements.txt . 
RUN mkdir -p venvs
RUN python3 -m venv venvs/$NAME
RUN venvs/$NAME/bin/pip install --upgrade pip
RUN venvs/$NAME/bin/pip install -r requirements.txt

COPY templates/ ./templates/
COPY *.py .

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

ENTRYPOINT ["venvs/mastodon_digest/bin/python3", "run.py"]