.PHONY: run help local dev

VERSION := $(shell git describe --abbrev=0 --tags)
BUILD_DATE := "$(shell date -u)"
VCS_REF := $(shell git log -1 --pretty=%h)
NAME := $(shell pwd | xargs basename)
VENDOR := "Matt Hodges"
ORG := hodgesmr
WORKDIR := "/opt/${NAME}"

# For running locally. We default to a general python3 but depending on the
# users environment they may need to specify which version to use. python3.9
# is the lowest tested with.
SYSTEM_PYTHON ?= python3
VENV_DIR := .venv
PYTHON_BIN := $(VENV_DIR)/bin/python

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

.EXPORT_ALL_VARIABLES:
dev:
	@echo "Running with local development themes"
	docker run --env-file .env -it --rm -v "$(PWD)/render:${WORKDIR}/render" -v "$(PWD)/templates:${WORKDIR}/templates" ${ORG}/${NAME} ${FLAGS}
	python -m webbrowser -t "file://$(PWD)/render/index.html"

$(PYTHON_BIN):
	$(SYSTEM_PYTHON) -m venv $(VENV_DIR)
	$(PYTHON_BIN) -m pip install -r requirements.txt

local: $(PYTHON_BIN)
	$(PYTHON_BIN) run.py ${FLAGS}
