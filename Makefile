PROJECT = mastodon_digest
ID = something/${PROJECT}

build:
	docker build \
		--build-arg PROJECT=${PROJECT} \
		--tag ${ID} .

run:
	docker run \
		--name ${PROJECT} \
		--hostname ${PROJECT} \
		--volume $(shell pwd):/opt/${PROJECT} \
		--interactive \
		--tty \
		--rm \
		${ID} \
		bash

exec:
	docker exec \
		--interactive \
		--tty \
		${PROJECT} \
		bash

digest:
	python run.py
