#!make

# ENV VARIABLES IMPORT
include .env


# ----------------------------------
# Google Cloud Platform
# ----------------------------------

gcloud_config_activate:
	@echo "ACTIVATING GCLOUD CONFIGURATION..."
	@gcloud config configurations activate ${GCP_CONFIG}

# To use once to create the gcloud configuration
gcloud_config_init:
	@echo "CREATING GCLOUD CONFIGURATION..."
	@gcloud config configurations create --activate ${GCP_CONFIG}
	@gcloud config set account ${GCP_ACCOUNT}
	@gcloud config set project ${GCP_PRJ_ID}
	@gcloud config set artifacts/repository ${ART_REPO}
	@gcloud config set artifacts/location ${ART_LOCATION}

# To use once to artifacts configuration (apis, repo)
gcloud_artifacts_init: gcloud_config_activate
	@echo "ENABLING NEEDED APIs ..."
	@gcloud services enable artifactregistry.googleapis.com
	@echo "CREATING ARTIFACT REPOSITORY..."
	@gcloud artifacts repositories create ${ART_REPO} --repository-format=docker \
		--location=${ART_LOCATION}

gcloud_run_deploy: gcloud_config_activate
	@gcloud run deploy --image ${API_IMG} --platform managed \
		--region ${GCR_REGION} --allow-unauthenticated --memory 1Gi



# ----------------------------------
#     DOCKER
# ----------------------------------

DOCKER_IMG=${ART_LOCATION}-docker.pkg.dev/${GCP_PRJ_ID}/${ART_REPO}/${ART_IMG}

docker_config:
	@echo "CONFIGURING DOCKER..."
	@gcloud auth configure-docker ${ART_LOCATION}-docker.pkg.dev

docker_build:
	@docker build -t ${DOCKER_IMG} .

docker_run_local:
	@docker run -p 8080:8000 --rm -e PORT=8000 ${DOCKER_IMG}

docker_push:
	@docker push ${DOCKER_IMG}


# ----------------------------------
#     MYSQL CONNECTION
# ----------------------------------

mysql_connect:
	@mysql -u ${SQL_USER} --password=${SQL_PWD} -h ${SQL_HOST}\
	 --ssl-ca=${SQL_SSL_CA} --ssl-cert=${SQL_SSL_CERT} --ssl-key=${SQL_SSL_KEY}
