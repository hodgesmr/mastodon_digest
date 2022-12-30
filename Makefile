.PHONY: run help local dev open

VERSION?=$(shell git describe --abbrev=0 --tags)
BUILD_DATE?="$(shell date -u)"
VCS_REF?=$(shell git log -1 --pretty=%h)
NAME?=$(shell pwd | xargs basename)
WORKDIR:=/opt/${NAME}
VENDOR="Matt Hodges"
ORG?=hodgesmr

# For running locally. We default to a general python3 but depending on the
# users environment they may need to specify which version to use. python3.9
# is the lowest tested with.
ifeq ($(shell which python3),)
	SYSTEM_PYTHON?=python
else
	SYSTEM_PYTHON?=python3
endif

VENV_DIR := .venv
PYTHON_BIN := $(VENV_DIR)/bin/python

# Docker image name in format [user/repo]
DOCKER_IMAGE?=${ORG}/${NAME}

# Docker tag in addition to the [$VERSION] tag
DOCKER_TAG?=latest

# hide [Use 'docker scan' to run Snyk tests against images to find vulnerabilities and learn how to fix them] output
#
# See: https://github.com/docker/scan-cli-plugin/issues/149#issuecomment-823969364
DOCKER_SCAN_SUGGEST?=false

# [docker push] to registry after [docker build]?
#
# See: https://docs.docker.com/engine/reference/commandline/buildx_build/#push
DOCKER_PUSH?=false

# Import built image into local Docker daemon? Needed for [docker run] when using buildx
#
# See: https://docs.docker.com/engine/reference/commandline/buildx_build/#load
DOCKER_LOAD?=true

# Allow multi-arch builds of the container by setting [DOCKER_PLATFORM=linux/amd64,linux/arm64]
#
# We default to [linux] which automatically picks the correct CPU architecture from the Docker client.
#
# ! Use [DOCKER_LOAD=false] when using multi-arch - Docker can't import these manifests.
#
# See: https://docs.docker.com/engine/reference/commandline/buildx_build/#platform
# See: https://docs.docker.com/engine/reference/builder/#from
DOCKER_PLATFORM?=linux

# Additional [docker run] CLI flags - *NOT* to be confused with [FLAGS] for [mastodon_digest] CLI flags directly
#
# [--rm -it -v] is already taken care of
DOCKER_RUN_FLAGS?=--env-file=.env

# Open browser after [make run] or [make dev] rendering complete successfully
OPEN_AFTER_RUN=true

# CLI flags passed to the container command-line in [make dev] and [make run]
#
# Use [FLAGS=-h make run] to see options
FLAGS?=

print:
	@echo BUILD_DATE=${BUILD_DATE}
	@echo NAME=${NAME}
	@echo ORG=${ORG}
	@echo VCS_REF=${VCS_REF}
	@echo VENDOR=${VENDOR}
	@echo VERSION=${VERSION}
	@echo WORKDIR=${WORKDIR}
	@echo SYSTEM_PYTHON=${SYSTEM_PYTHON}
	@echo OPEN_AFTER_RUN=${OPEN_AFTER_RUN}
	@echo FLAGS=${FLAGS}
	@echo DOCKER_IMAGE=${DOCKER_PLATFORM}
	@echo DOCKER_RUN_FLAGS=${DOCKER_RUN_FLAGS}
	@echo DOCKER_TAG=${DOCKER_TAG}
	@echo DOCKER_PLATFORM=${DOCKER_PLATFORM}
	@echo DOCKER_LOAD=${DOCKER_LOAD}
	@echo DOCKER_PUSH=${DOCKER_PUSH}

# [docker buildx] is included in [Docker Desktop] and DEB/RPM installations of Docker on Linux by default since
# Docker [19.03.0] released [2019-07-22]
#
# See: https://github.com/docker/buildx#installing
# See: https://docs.docker.com/engine/release-notes/19.03/#19030
.EXPORT_ALL_VARIABLES:
build:
	docker buildx build \
	-f Dockerfile \
	. \
	-t "${DOCKER_IMAGE}:${VERSION}" \
	-t "${DOCKER_IMAGE}:${DOCKER_TAG}" \
	--push=${DOCKER_PUSH} \
	--load=${DOCKER_LOAD} \
	--platform=${DOCKER_PLATFORM} \
	--build-arg VERSION=${VERSION} \
	--build-arg BUILD_DATE=${BUILD_DATE} \
	--build-arg VCS_REF=${VCS_REF} \
	--build-arg NAME=${NAME} \
	--build-arg VENDOR=${VENDOR} \
	--build-arg ORG=${ORG} \
	--build-arg WORKDIR=${WORKDIR}

# Show the [mastodon_digest] help output and exit
.EXPORT_ALL_VARIABLES:
help:
	@$(MAKE) run FLAGS="-h" OPEN_AFTER_RUN=false DOCKER_RUN_FLAGS=""

# Run the [mastodon_digest] command in Docker and write the rendered HTML into [render/index.html]
#
# Use [FLAGS] environment variable to provide command flags to [mastodon_digest]
.EXPORT_ALL_VARIABLES:
run:
	docker run --rm -it ${DOCKER_RUN_FLAGS} -v "$(PWD)/render:${WORKDIR}/render" ${DOCKER_IMAGE}:${DOCKER_TAG} ${FLAGS}
	@$(MAKE) open

# Same as [make run], but the templates/ files are provided via Docker volume rather than being baked into the Docker image
#
# This is convinient for iterating on the templates without doing [make build && make run] if you're only tweaking teamplates
.EXPORT_ALL_VARIABLES:
dev:
	@echo "Running with local development themes"
	docker run --rm -it ${DOCKER_RUN_FLAGS} -v "$(PWD)/render:${WORKDIR}/render" -v "$(PWD)/templates:${WORKDIR}/templates" ${DOCKER_IMAGE}:${DOCKER_TAG} ${FLAGS}
	@$(MAKE) open

# Open the renderer output in the browser
#
# use [OPEN_AFTER_RUN=false] to disable this behavior
.EXPORT_ALL_VARIABLES:
open:
ifeq ($(OPEN_AFTER_RUN),true)
	${SYSTEM_PYTHON} -m webbrowser -t "file://$(PWD)/render/index.html"
endif

# Create local environment via [venv] for running [mastodon_digest]
$(PYTHON_BIN):
	$(SYSTEM_PYTHON) -m venv $(VENV_DIR)
	$(PYTHON_BIN) -m pip install -r requirements.txt

# Run [mastodon_digest] locally (requires python installed)
local: $(PYTHON_BIN)
	$(PYTHON_BIN) run.py ${FLAGS}
