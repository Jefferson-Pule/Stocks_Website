:Set environment variables from variables.txt
set /A suf=%RANDOM%*%RANDOM%
for /f "delims== tokens=1,2" %%G in (variables.txt) do (IF %%G==PROJECT_ID (set %%G=%%H-%suf%) ELSE (set %%G=%%H))

:Create Project and enable billing
call gcloud projects create %PROJECT_ID% --name=%NAME% --set-as-default && ^
call gcloud beta billing projects link %PROJECT_ID% --billing-account %BILLING_ACCOUNT% && ^
echo %PROJECT_ID% created

call gcloud config get-value core/project>tmp.txt && ^
set /p PROJECT_ID=<tmp.txt
del tmp.txt

:Enable APIs
echo Enable APIs
call gcloud services enable run.googleapis.com sql-component.googleapis.com sqladmin.googleapis.com compute.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com vpcaccess.googleapis.com servicenetworking.googleapis.com billingbudgets.googleapis.com dataflow.googleapis.com logging.googleapis.com storage-component.googleapis.com  storage-api.googleapis.com  pubsub.googleapis.com cloudfunctions.googleapis.com cloudscheduler.googleapis.com  && ^
echo APIs enabled

:Create Service account
call gcloud iam service-accounts create cloudrun-serviceaccount && ^
echo service account %SERVICE_ACCOUNT% created && ^
call gcloud iam service-accounts list --filter cloudrun-serviceaccount --format "value(email)">tmp.txt && ^
set /p SERVICE_ACCOUNT=<tmp.txt
del tmp.txt

:Create buckets
set GS_BUCKET_NAME=%PROJECT_ID%-media
set GS_DF_BUCKET_NAME=%PROJECT_ID%-dataflow
call gsutil mb -l %REGION% gs://%GS_BUCKET_NAME% && ^
call gsutil mb -l %REGION% gs://%GS_DF_BUCKET_NAME% && ^
echo Buckets created

:Upload file with info of S&P500 companies
call gcloud storage cp %SQL_DATA_FILE% gs://%GS_DF_BUCKET_NAME%

:Get permissions ready for PubSub Bigquery and dataflow
call gcloud projects add-iam-policy-binding %PROJECT_ID% --role=roles/iam.serviceAccountUser --member serviceAccount:%SERVICE_ACCOUNT% && ^
call gcloud projects add-iam-policy-binding %PROJECT_ID% --role=roles/dataflow.worker --member serviceAccount:%SERVICE_ACCOUNT% && ^
call gcloud projects add-iam-policy-binding %PROJECT_ID% --role=roles/storage.objectAdmin --member serviceAccount:%SERVICE_ACCOUNT% && ^
call gcloud projects add-iam-policy-binding %PROJECT_ID% --role=roles/pubsub.admin --member serviceAccount:%SERVICE_ACCOUNT% && ^
call gcloud projects add-iam-policy-binding %PROJECT_ID% --role=roles/bigquery.dataEditor --member serviceAccount:%SERVICE_ACCOUNT% && ^
call gcloud projects add-iam-policy-binding %PROJECT_ID% --role=roles/bigquery.user --member serviceAccount:%SERVICE_ACCOUNT% && ^
call gcloud projects add-iam-policy-binding %PROJECT_ID% --role=roles/cloudfunctions.developer --member serviceAccount:%SERVICE_ACCOUNT%  && ^
echo Service account ready for PubSub and Data Flow

: CreatePubSub topics for streaming
set DFLOW_TOPIC=Data_flow
call gcloud pubsub topics create %DFLOW_TOPIC%
call gcloud pubsub topics create StocksData
call gcloud pubsub topics create DailyDatatrigger
call gcloud pubsub topics create StrDatatrigger
call python ../dataflow/create-pubsub-subscriptions.py --project_id=%PROJECT_ID% --topic_id=StocksData && ^
echo Topics and subscriptions created

:Create Bigquery tables for historical info
call python ../dataflow/create-bigquery-tables.py --project_id=%PROJECT_ID% --dataset_id=Stocks_dataset --table_id=Stocks_info && ^
echo BigQuery table created

PAUSE

:Create templates for dataflow
call python ../dataflow/dataflow-pubsub.py --project=%PROJECT_ID% --region=%REGION% --input_topic=projects/%PROJECT_ID%/topics/%DFLOW_TOPIC% --output_topic=projects/%PROJECT_ID%/topics/StocksData --runner=DataflowRunner --temp_location=gs://%GS_DF_BUCKET_NAME%/temp --template_location=gs://%GS_DF_BUCKET_NAME%/templates/dataflow-pubsub --staging_location=gs://%GS_DF_BUCKET_NAME%/staging --service_account_email=%SERVICE_ACCOUNT%
call python ../dataflow/dataflow-bigquery.py --project=%PROJECT_ID% --region=%REGION% --runner=DataflowRunner --temp_location=gs://%GS_DF_BUCKET_NAME%/temp --template_location=gs://%GS_DF_BUCKET_NAME%/templates/dataflow-bigquery --requirements_file=../dataflow/requirements.txt --staging_location=gs://%GS_DF_BUCKET_NAME%/staging --service_account_email=%SERVICE_ACCOUNT%
call python ../dataflow/dataflow-bigquery-dailydata.py --project=%PROJECT_ID% --region=%REGION% --runner=DataflowRunner --temp_location=gs://%GS_DF_BUCKET_NAME%/temp --template_location=gs://%GS_DF_BUCKET_NAME%/templates/dataflow-bigquery-dailydata --requirements_file=../dataflow/requirements.txt --staging_location=gs://%GS_DF_BUCKET_NAME%/staging --service_account_email=%SERVICE_ACCOUNT%

PAUSE

:Run DataFlow jobs
:Start streaming
call python ../dataflow/dataflow-run-template.py --project_id=%PROJECT_ID% --job_id=StreamingStocks --template_location=gs://%GS_DF_BUCKET_NAME%/templates/dataflow-pubsub && ^
call python ../dataflow/dataflow-run-template.py --project_id=%PROJECT_ID% --job_id=YahootoBigQuery --template_location=gs://%GS_DF_BUCKET_NAME%/templates/dataflow-bigquery --input=gs://%GS_DF_BUCKET_NAME%/SP500_stocks_info.csv --output=gs://%GS_DF_BUCKET_NAME%/last-updated && ^
echo DataFlow jobs submited
PAUSE

:Deploy Cloud functions to call dailydata
cd ../dataflow/cloud-functions-daily-data
call gcloud functions deploy DailyData-trigger --region=%REGION% --entry-point=request_job --set-env-vars=PROJECT_ID=%PROJECT_ID% --trigger-topic=DailyDatatrigger --runtime=python39 --service-account=%SERVICE_ACCOUNT%
call gcloud scheduler jobs create pubsub DailyData --location=us-central1 --schedule="15 21 * * 1-5"  --topic=DailyDatatrigger --message-body="daily" && ^
echo CloudFunction deployed and scheduled for 9:15pm UTC (5:15pm Toronto Time)
cd .. && cd cloud-functions-streaming-data
call gcloud functions deploy StreamingData-publisher --region=%REGION% --entry-point=request_job --set-env-vars=PROJECT_ID=%PROJECT_ID%,TOPIC_ID=%DFLOW_TOPIC% --trigger-topic=StrDatatrigger --runtime=python39 --service-account=%SERVICE_ACCOUNT%
cd .. && cd ..

PAUSE

:Create VPC Connection Host (NEEDED FOR SQL SERVER)
call gcloud compute addresses create internal-connection --global --purpose=VPC_PEERING --addresses=192.168.0.0 --prefix-length=16 --description="Stocks Website Allocate IP range" --network=default && ^
call gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com --ranges=internal-connection --network=default && ^
call gcloud compute networks vpc-access connectors create %VPC-CONNECTOR-NAME% --network default --region %REGION% --range 10.8.0.0/28
echo Private VPC connection created

:Create Sql Server database
call gcloud sql instances create %INSTANCE_NAME% --project %PROJECT_ID% --database-version SQLSERVER_2019_STANDARD --cpu 2 --memory 8 --region %REGION% --network=projects/%PROJECT_ID%/global/networks/default --assign-ip --root-password=%DJPASSWORD% && ^
call gcloud sql databases create Stocks_Website_db --instance=%INSTANCE_NAME% && ^
echo instance and database in  %PROJECT_ID%:%REGION%:%INSTANCE_NAME% Stocks_Website_db  && ^
call gcloud sql instances list --filter=name:%INSTANCE_NAME% --format="value(PRIVATE_ADDRESS)">tmp.txt && ^
set /p HOST=<tmp.txt && ^
set DBUSER=sqlserver 
del tmp.txt


: Give your service account cloud sql access
call gcloud projects add-iam-policy-binding %PROJECT_ID% --member serviceAccount:%SERVICE_ACCOUNT% --role roles/cloudsql.client

: Save environment variables 
echo HOST="%HOST%"> .env
echo INSTANCE_NAME="%INSTANCE_NAME%">> .env
echo DBUSER=%DBUSER%>> .env
echo DJPASSWORD=%DJPASSWORD%>> .env
echo PROJECT_ID="%PROJECT_ID%">> .env
echo GS_BUCKET_NAME=%GS_BUCKET_NAME%>> .env
echo REGION="%REGION%">>.env
echo DBUG="%DBUG%">>.env
echo SQL_DATA_FILE="local_data/SP500_stocks_info.csv">>.env
echo FIRST_MIGRATE=True>>.env

:Create a secret
call gcloud secrets create application_settings --data-file .env && ^
echo Secrets created
del .env

:Create a cloud build account and update secrets permissions
call gcloud projects describe %PROJECT_ID% --format value(projectNumber)>>tmp.txt && ^
set /p PROJECTNUM=<tmp.txt
del tmp.txt
set CLOUDBUILD=%PROJECTNUM%@cloudbuild.gserviceaccount.com && ^
set CLOUDBUILD 
call gcloud secrets add-iam-policy-binding application_settings --member serviceAccount:%CLOUDBUILD% --role roles/secretmanager.secretAccessor && ^
call gcloud secrets add-iam-policy-binding Bigquery_key --member serviceAccount:%CLOUDBUILD% --role roles/secretmanager.secretAccessor && ^
call gcloud projects add-iam-policy-binding %PROJECT_ID% --member serviceAccount:%CLOUDBUILD% --role roles/cloudsql.client && ^
echo Iam Policy updated for %CLOUDBUILD%
call gcloud secrets add-iam-policy-binding application_settings --member serviceAccount:%SERVICE_ACCOUNT% --role roles/secretmanager.secretAccessor && ^
call gcloud secrets add-iam-policy-binding Bigquery_key --member serviceAccount:%SERVICE_ACCOUNT% --role roles/secretmanager.secretAccessor && ^
echo Service account ready for secrets

:Create docker image
cd ..
echo FROM gcr.io/%PROJECT_ID%/myimage:latest > tmp | type docker_template\Dockerfile_temp >> tmp | (Echo YES|move tmp Dockerfile)
call gcloud builds submit --pack image=gcr.io/%PROJECT_ID%/myimage && ^
echo Image created
call gcloud artifacts repositories create "my-full-image" --repository-format=Docker --location=us-central1 --description="Web Stocks Docker repository" && ^
call gcloud builds submit --tag us-central1-docker.pkg.dev/%PROJECT_ID%/my-full-image/myfullimage && ^
echo Full Image created

:Submit migrations
call gcloud builds submit --config migrate.yaml && ^
echo Migrations applied

:Deploy
call gcloud run deploy stocks-website --platform managed --region %REGION% --image %REGION%-docker.pkg.dev/%PROJECT_ID%/my-full-image/myfullimage:latest  --set-cloudsql-instances %PROJECT_ID%:%REGION%:%INSTANCE_NAME% --set-secrets APPLICATION_SETTINGS=application_settings:latest --service-account %SERVICE_ACCOUNT% --allow-unauthenticated --vpc-connector %VPC-CONNECTOR-NAME% && ^
echo fist deployment ready 

:Add Host to Trusted Hosts
cd ../dependencies
call gcloud run services describe stocks-website --platform managed --region %REGION% --format value(status.url)>>tmp.txt
set /p CLOUDRUN_SERVICE_URL=<tmp.txt
del tmp.txt

: Save environment variables 
echo HOST="%HOST%"> temp_settings
echo INSTANCE_NAME="%INSTANCE_NAME%">> temp_settings
echo DBUSER=%DBUSER%>> temp_settings
echo DJPASSWORD=%DJPASSWORD%>> temp_settings
echo PROJECT_ID="%PROJECT_ID%">> temp_settings
echo GS_BUCKET_NAME=%GS_BUCKET_NAME%>> temp_settings
echo REGION="%REGION%">>temp_settings
echo DBUG="%DBUG%">> temp_settings

echo CLOUDRUN_SERVICE_URL=%CLOUDRUN_SERVICE_URL%>>temp_settings
call gcloud secrets versions add application_settings --data-file temp_settings
del temp_settings
call gcloud run services update stocks-website --platform managed --region %REGION% --image %REGION%-docker.pkg.dev/%PROJECT_ID%/my-full-image/myfullimage:latest && ^
echo finished deployment SQL SERVER %PROJECT_ID%:%REGION%:%INSTANCE_NAME% running GS_BUCKET_NAME=%GS_BUCKET_NAME%

PAUSE 