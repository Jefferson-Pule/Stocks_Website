from googleapiclient.discovery import build
import argparse

def request_job(project, job, template, input=None, output=None):
    if input:
        parameters = {
             'input': input,
             'output': output,
         }
    else:
        parameters = {}

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project_id",
        help="The project where to run dataflow job"
    )
    parser.add_argument(
        "--job_id",
        help="Unique job name"
    )
    parser.add_argument(
        "--template_location",
        help="The location of the template"
    )
    parser.add_argument(
        "--input",
        help="The location of the input file"
    )
    parser.add_argument(
        "--output",
        help="The output root for the last_updated file"
    )

    args = parser.parse_args()

    request_job(args.project_id, args.job_id, args.template_location, args.input , args.output)
