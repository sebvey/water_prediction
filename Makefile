# ENV VARIABLES IMPORT
include .env

mysql_connect:
	@mysql -u ${SQL_USER} --password=${SQL_PWD} -h ${SQL_HOST}\
	 --ssl-ca=${SQL_SSL_CA} --ssl-cert=${SQL_SSL_CERT} --ssl-key=${SQL_SSL_KEY}

# ----------------------------------
# Google Cloud Platform
# ----------------------------------

## GCLOUD

gcloud_prj_select:
	@echo "SELECTING GCP PROJECT ..."
	@gcloud config set project ${GCP_PRJ_ID}

gcloud_services_enable: gcloud_prj_select
	@echo "ENABLING NEEDED APIs ..."
	@gcloud services enable cloudbuild.googleapis.com
	@gcloud services enable cloudfunctions.googleapis.com
	@gcloud services enable cloudscheduler.googleapis.com

# ----------------------------------
#     DOCKER
# ----------------------------------

API_IMG="${GCR_MULTI_REGION}/${GCP_PRJ_ID}/${DOCKER_IMG}"

docker_build:
	@docker build -t ${API_IMG} .

docker_run_local:
	@docker run -e PORT=8000 -p 8080:8000 ${API_IMG}

# !! TODO : CONFIGURE DOCKER FOR GCP PUSH

docker_push:
	@docker push ${API_IMG}

gcr_deploy:
	@gcloud run deploy --image ${API_IMG} --platform managed --region ${GCR_REGION} --allow-unauthenticated --memory 1Gi
