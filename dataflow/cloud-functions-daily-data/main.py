from googleapiclient.discovery import build
from google.cloud import storage
import os
from yfinance import download as yfdownload
import datetime

storage_client = storage.Client()
def request_job(data, context):
   
    Dataset = yfdownload("AAPL", start = datetime.date.today(), end = datetime.date.today()+datetime.timedelta(days=1))

    if len(Dataset)!=0:

        project=os.environ["PROJECT_ID"]
        template=f"gs://{project}-dataflow/templates/dataflow-bigquery-dailydata"
        job="daily-update-bigquery"
        output=f"gs://{project}-dataflow/last-updated"

        # Get last_update

        bucket = storage_client.get_bucket(f"{project}-dataflow")
        blob = bucket.blob("last-updated-00000-of-00001.txt")
        contents = blob.download_as_string()
        last_updated = contents.decode()[:-1]

        # Send request
        
        parameters = {
                'input': f"gs://{project}-dataflow/SP500_stocks_info.csv",
                'output': output,
                'last_updated': last_updated,
            }

        dataflow = build("dataflow", "v1b3")
        request = (
            dataflow.projects()
            .templates()
            .launch(
                projectId=project,
                gcsPath=template,
                body={
                    "jobName": job,
                    "parameters": parameters,
                },
            )
        )

        response = request.execute()

        return response
    else:
        return "No data found or dataflow job not excecuted" 
