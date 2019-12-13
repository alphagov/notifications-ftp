FROM python:3.6-slim

ENV PYTHONUNBUFFERED=1 \
	DEBIAN_FRONTEND=noninteractive \
	GOSU_VERSION=1.10

RUN \
	echo "Install base packages" \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		make \
		curl \
		git \
		build-essential \
		zip \
		libpq-dev

# these are declared statically here so that they're cached by the docker image - if we run after the `COPY` command
# they won't be cached so it'll re-download every time. But these don't involve the filesystem
COPY requirements.txt .
COPY requirements_for_test.txt .
RUN \
	echo "Installing python dependencies" \
	&& pip install -r requirements_for_test.txt

WORKDIR /var/project

# Copy from the real world, one dir up (project root) into the environment's current working directory
# Docker will rebuild from here down every time.
COPY . .
