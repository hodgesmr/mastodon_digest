.PHONY: run help

VERSION?=$(shell git describe --abbrev=0 --tags)
BUILD_DATE?="$(shell date -u)"
VCS_REF?=$(shell git log -1 --pretty=%h)
NAME?=$(shell pwd | xargs basename)
WORKDIR:=/opt/${NAME}
VENDOR="Matt Hodges"
ORG?=hodgesmr

ifeq ($(shell which python3),)
	PYTHON=python
else
	PYTHON=python3
endif

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
	@echo PYTHON=${PYTHON}
	@echo FLAGS=${FLAGS}
	@echo DOCKER_IMAGE=${DOCKER_PLATFORM}
	@echo DOCKER_TAG=${DOCKER_TAG}
	@echo DOCKER_PLATFORM=${DOCKER_PLATFORM}
	@echo DOCKER_LOAD=${DOCKER_LOAD}
	@echo DOCKER_PUSH=${DOCKER_PUSH}

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

.EXPORT_ALL_VARIABLES:
help:
	docker run --rm  -it --env-file=.env -v "$(PWD)/render:${WORKDIR}/render" ${DOCKER_IMAGE} -h

.EXPORT_ALL_VARIABLES:
run:
	docker run --rm -it --env-file=.env -v "$(PWD)/render:${WORKDIR}/render" ${DOCKER_IMAGE}:${DOCKER_TAG} ${FLAGS}
	${PYTHON} -m webbrowser -t "file://$(PWD)/render/index.html"

.EXPORT_ALL_VARIABLES:
dev:
	@echo "Running with local development themes"
	docker run --rm -it --env-file=.env -v "$(PWD)/render:${WORKDIR}/render" -v "$(PWD)/templates:${WORKDIR}/templates" ${DOCKER_IMAGE}:${DOCKER_TAG} ${FLAGS}
	${PYTHON} -m webbrowser -t "file://$(PWD)/render/index.html"
