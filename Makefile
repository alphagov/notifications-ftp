.DEFAULT_GOAL := help
SHELL := /bin/bash

NOTIFY_CREDENTIALS ?= ~/.notify-credentials
CF_APP = "notify-ftp"
CF_ORG = "govuk-notify"
CF_MANIFEST_PATH ?= /tmp/manifest.yml

.PHONY: run-celery
run-celery: ## Runs celery worker
	. environment.sh && celery \
		-A run_celery.notify_celery worker \
		--pidfile="/tmp/celery-ftp.pid" \
		--loglevel=INFO \
		--concurrency=1

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: generate-manifest
generate-manifest: ## Generates cf manifest
	$(if ${CF_APP},,$(error Must specify CF_APP))
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	$(if $(shell which gpg2), $(eval export GPG=gpg2), $(eval export GPG=gpg))
	$(if ${GPG_PASSPHRASE_TXT}, $(eval export DECRYPT_CMD=echo -n $$$${GPG_PASSPHRASE_TXT} | ${GPG} --quiet --batch --passphrase-fd 0 --pinentry-mode loopback -d), $(eval export DECRYPT_CMD=${GPG} --quiet --batch -d))

	@jinja2 --strict manifest.yml.j2 \
	    -D environment=${CF_SPACE} \
	    -D CF_APP=${CF_APP} \
	    --format=yaml \
	    <(${DECRYPT_CMD} ${NOTIFY_CREDENTIALS}/credentials/${CF_SPACE}/paas/ftp-environment-variables.gpg) 2>&1

.PHONY: cf-target
cf-target:
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	@cf target -o ${CF_ORG} -s ${CF_SPACE}

.PHONY: cf-deploy
cf-deploy: cf-target ## Deploys the app to Cloud Foundry
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	@cf app --guid ${CF_APP} || exit 1
	# cancel any existing deploys to ensure we can apply manifest (if a deploy is in progress you'll see ScaleDisabledDuringDeployment)
	cf cancel-deployment ${CF_APP} || true

	# generate manifest (including secrets) and write it to CF_MANIFEST_PATH (in /tmp/)
	make -s CF_APP=${CF_APP} generate-manifest > ${CF_MANIFEST_PATH}
	# reads manifest from CF_MANIFEST_PATH
	cf push ${CF_APP} --strategy=rolling -f ${CF_MANIFEST_PATH}
	# delete old manifest file
	rm ${CF_MANIFEST_PATH}


.PHONY: preview
preview: ## Set environment to preview
	$(eval export CF_SPACE=preview)
	@true

.PHONY: staging
staging: ## Set environment to staging
	$(eval export CF_SPACE=staging)
	@true

.PHONY: production
production: ## Set environment to production
	$(eval export CF_SPACE=production)
	@true

.PHONY: test
test: ## run unit tests
	./scripts/run_tests.sh

.PHONY: clean
clean:
	rm -rf cache target venv .coverage build tests/.cache wheelhouse ${CF_MANIFEST_PATH}
