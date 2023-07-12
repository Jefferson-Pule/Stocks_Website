import argparse
from google.cloud import bigquery

def create_table(project_id, dataset_name, table_id):
    # Construct a BigQuery client object.
    client = bigquery.Client()
 
    try:
        dataset_id=f"{project_id}.{dataset_name}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        dataset = client.create_dataset(dataset, timeout=30)
        print("Created dataset {}.{}".format(client.project, dataset.dataset_id))

    except Exception as e:
        print(e)

    # TODO(developer): Set table_id to the ID of the table to create.
    table_id = f"{project_id}.{dataset_name}.{table_id}"

    schema=[
        bigquery.SchemaField("Symbol_ID", "INTEGER",mode='REQUIRED'),
        bigquery.SchemaField("Symbol", "STRING",mode='REQUIRED'),
        bigquery.SchemaField("Name", "STRING",mode='REQUIRED'),
        bigquery.SchemaField("Info", "RECORD",mode= "REPEATED", fields=[
            bigquery.SchemaField("Date", "TIMESTAMP",mode='REQUIRED'),
            bigquery.SchemaField("Open", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("High", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("Low", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("Close", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("Adj_Close", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("Volume", "Float", mode="NULLABLE")
        ])
    ]

    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table)  # Make an API request.
    print(
        "Created table {}.{}.{}".format(table.project, table.dataset_id, table.table_id)
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project_id",
        help="The project where to create the bigquery table"
    )
    parser.add_argument(
        "--dataset_id",
        help="The dataset where to create the bigquery table"
    )
    parser.add_argument(
        "--table_id",
        help="The dataset where to create the bigquery table"
    )
    args = parser.parse_args()

    create_table(args.project_id, args.dataset_id, args.table_id)
