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

# hide [Use 'docker scan' to run Snyk tests against images to find vulnerabilities and learn how to fix them] output
DOCKER_SCAN_SUGGEST?=false

# push to registry on build?
DOCKER_PUSH?=false

# import to local docker on build?
DOCKER_LOAD?=true

# image name in format [user/repo]
DOCKER_IMAGE?=${ORG}/${NAME}

# named tag (in addition to the [$VERSION] tag)
DOCKER_TAG?=latest

# allow multi-arch builds of the container by setting [DOCKER_PLATFORM=linux/amd64,linux/arm64] for example
#
# NOTE: use [DOCKER_LOAD=false] when using multi-arch, Docker can't import these manifests
DOCKER_PLATFORM?=linux

# CLI flags passed to the container runtime
FLAGS?=

print:
	@echo BUILD_DATE=${BUILD_DATE}
	@echo NAME=${NAME}
	@echo ORG=${ORG}
	@echo VCS_REF=${VCS_REF}
	@echo VENDOR=${VENDOR}
	@echo VERSION=${VERSION}
	@echo WORKDIR=${WORKDIR}
	@echo USER_OPTIONS=${USER_OPTIONS}

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
	docker run --env-file .env -it --rm -v "$(PWD)/render:${WORKDIR}/render" ${DOCKER_IMAGE} -h

.EXPORT_ALL_VARIABLES:
run:
	docker run --env-file .env -it --rm -v "$(PWD)/render:${WORKDIR}/render" ${DOCKER_IMAGE}:${DOCKER_TAG} ${FLAGS}
	${PYTHON} -m webbrowser -t "file://$(PWD)/render/index.html"

.EXPORT_ALL_VARIABLES:
dev:
	@echo "Running with local development themes"
	docker run --env-file .env -it --rm -v "$(PWD)/render:${WORKDIR}/render" -v "$(PWD)/templates:${WORKDIR}/templates" ${DOCKER_IMAGE}:${DOCKER_TAG} ${FLAGS}
	${PYTHON} -m webbrowser -t "file://$(PWD)/render/index.html"
