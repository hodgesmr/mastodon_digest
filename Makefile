.PHONY: run help

VERSION := $(shell git describe --abbrev=0 --tags)
BUILD_DATE := "$(shell date -u)"
VCS_REF := $(shell git log -1 --pretty=%h)
NAME := $(shell pwd | xargs basename)
VENDOR := "Matt Hodges"
ORG := hodgesmr
WORKDIR := "/opt/${NAME}"

DOCKER_SCAN_SUGGEST=false

FLAGS ?=

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
	docker build -f Dockerfile \
	-t ${ORG}/${NAME}:${VERSION} \
	-t ${ORG}/${NAME}:latest . \
	--build-arg VERSION=${VERSION} \
	--build-arg BUILD_DATE=${BUILD_DATE} \
	--build-arg VCS_REF=${VCS_REF} \
	--build-arg NAME=${NAME} \
	--build-arg VENDOR=${VENDOR} \
	--build-arg ORG=${ORG} \
	--build-arg WORKDIR=${WORKDIR}

.EXPORT_ALL_VARIABLES:
help:
	docker run --env-file .env -it --rm -v "$(PWD)/render:${WORKDIR}/render" ${ORG}/${NAME} -h

.EXPORT_ALL_VARIABLES:
run:
	docker run --env-file .env -it --rm -v "$(PWD)/render:${WORKDIR}/render" ${ORG}/${NAME} ${FLAGS}
	python -m webbrowser -t "file://$(PWD)/render/index.html"