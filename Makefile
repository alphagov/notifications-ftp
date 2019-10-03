.DEFAULT_GOAL := help
SHELL := /bin/bash
DATE = $(shell date +%Y-%m-%d:%H:%M:%S)

APP_VERSION_FILE = app/version.py

GIT_BRANCH ?= $(shell git symbolic-ref --short HEAD 2> /dev/null || echo "detached")
GIT_COMMIT ?= $(shell git rev-parse HEAD)


DOCKER_IMAGE = govuknotify/notifications-ftp
DOCKER_IMAGE_NAME = ${DOCKER_IMAGE}:master
DOCKER_BUILDER_IMAGE_NAME = govuk/notify-ftp-builder:master
DOCKER_TTY ?= $(if ${JENKINS_HOME},,t)

BUILD_TAG ?= notifications-ftp-manual
BUILD_NUMBER ?= 0
DEPLOY_BUILD_NUMBER ?= ${BUILD_NUMBER}
BUILD_URL ?=

DOCKER_CONTAINER_PREFIX = ${USER}-${BUILD_TAG}

NOTIFY_CREDENTIALS ?= ~/.notify-credentials
CF_APP = "notify-ftp"
CF_ORG = "govuk-notify"

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: generate-manifest
generate-manifest:
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
	cf v3-cancel-zdt-push ${CF_APP} || true

	cf v3-apply-manifest ${CF_APP} -f <(make -s generate-manifest)
	cf v3-zdt-push ${CF_APP} --wait-for-deploy-complete  # fails after 5 mins if deploy doesn't work

.PHONY: cf-login
cf-login: ## Log in to Cloud Foundry
	$(if ${CF_USERNAME},,$(error Must specify CF_USERNAME))
	$(if ${CF_PASSWORD},,$(error Must specify CF_PASSWORD))
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	@echo "Logging in to Cloud Foundry on ${CF_API}"
	@cf login -a "${CF_API}" -u ${CF_USERNAME} -p "${CF_PASSWORD}" -o "${CF_ORG}" -s "${CF_SPACE}"

.PHONY: check-env-vars
check-env-vars: ## Check mandatory environment variables
	$(if ${DNS_NAME},,$(error Must specify DNS_NAME))
	$(if ${AWS_ACCESS_KEY_ID},,$(error Must specify AWS_ACCESS_KEY_ID))
	$(if ${AWS_SECRET_ACCESS_KEY},,$(error Must specify AWS_SECRET_ACCESS_KEY))

.PHONY: preview
preview: ## Set environment to preview
	$(eval export CF_SPACE=preview)
	$(eval export DNS_NAME="notify.works")
	@true

.PHONY: staging
staging: ## Set environment to staging
	$(eval export CF_SPACE=staging)
	$(eval export DNS_NAME="staging-notify.works")
	@true

.PHONY: production
production: ## Set environment to production
	$(eval export CF_SPACE=production)
	$(eval export DNS_NAME="notifications.service.gov.uk")
	@true

.PHONY: _generate-version-file
_generate-version-file: ## Generates the app version file
	@echo -e "__travis_commit__ = \"${GIT_COMMIT}\"\n__time__ = \"${DATE}\"\n__travis_job_number__ = \"${BUILD_NUMBER}\"\n__travis_job_url__ = \"${BUILD_URL}\"" > ${APP_VERSION_FILE}

.PHONY: test
test: ## run unit tests
	./scripts/run_tests.sh

.PHONY: prepare-docker-build-image
prepare-docker-build-image: _generate-version-file ## Prepare the Docker builder image
	docker build -f docker/Dockerfile \
		--build-arg http_proxy="${http_proxy}" \
		--build-arg https_proxy="${https_proxy}" \
		-t ${DOCKER_IMAGE_NAME} \
		.

.PHONY: build-with-docker
build-with-docker: ;

define run_docker_container
	docker run -i${DOCKER_TTY} --rm \
		--name "${DOCKER_CONTAINER_PREFIX}-${1}" \
		-e http_proxy="${HTTP_PROXY}" \
		-e HTTP_PROXY="${HTTP_PROXY}" \
		-e https_proxy="${HTTPS_PROXY}" \
		-e HTTPS_PROXY="${HTTPS_PROXY}" \
		${DOCKER_IMAGE_NAME} \
		${2}
endef

.PHONY: test-with-docker
test-with-docker: prepare-docker-build-image ## Run tests inside a Docker container
	$(call run_docker_container,test, make test)

.PHONY: coverage-with-docker
coverage-with-docker: ;

.PHONY: clean-docker-containers
clean-docker-containers: ## Clean up any remaining docker containers
	docker rm -f $(shell docker ps -q -f "name=${DOCKER_CONTAINER_PREFIX}") 2> /dev/null || true

.PHONY: clean
clean:
	rm -rf cache target venv .coverage build tests/.cache wheelhouse

.PHONY: build-codedeploy-artifact build-paas-artifact
build-codedeploy-artifact build-paas-artifact: ## Build the deploy artifact for paas and CodeDeploy
	rm -rf target
	mkdir -p target
	zip -y -q -r -x@deploy-exclude.lst target/notifications-ftp.zip ./

.PHONY: upload-codedeploy-artifact ## Upload the deploy artifact for paas and CodeDeploy
upload-codedeploy-artifact: check-env-vars
	$(if ${DEPLOY_BUILD_NUMBER},,$(error Must specify DEPLOY_BUILD_NUMBER))
	aws s3 cp --region eu-west-1 --sse AES256 target/notifications-ftp.zip s3://${DNS_NAME}-codedeploy/notifications-ftp-${DEPLOY_BUILD_NUMBER}.zip

.PHONY: upload-paas-artifact
upload-paas-artifact:
	$(if ${AWS_ACCESS_KEY_ID},,$(error Must specify AWS_ACCESS_KEY_ID))
	$(if ${AWS_SECRET_ACCESS_KEY},,$(error Must specify AWS_SECRET_ACCESS_KEY))
	$(if ${DEPLOY_BUILD_NUMBER},,$(error Must specify DEPLOY_BUILD_NUMBER))
	$(if ${JENKINS_S3_BUCKET},,$(error Must specify JENKINS_S3_BUCKET))
	aws s3 cp --region eu-west-1 --sse AES256 target/notifications-ftp.zip s3://${JENKINS_S3_BUCKET}/build/notifications-ftp/${DEPLOY_BUILD_NUMBER}.zip

.PHONY: deploy
deploy: check-env-vars ## Trigger CodeDeploy for the api
	aws deploy create-deployment --application-name notify-ftp --deployment-config-name CodeDeployDefault.OneAtATime --deployment-group-name notify-ftp --s3-location bucket=${DNS_NAME}-codedeploy,key=notifications-ftp-${DEPLOY_BUILD_NUMBER}.zip,bundleType=zip --region eu-west-1
