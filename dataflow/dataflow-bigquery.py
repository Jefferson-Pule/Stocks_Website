import argparse
import logging
import requests

import json
from bs4 import BeautifulSoup
import yfinance as yf
import datetime

from google.cloud import bigquery
from apache_beam import DoFn, io, ParDo, Pipeline, PTransform
from apache_beam.io.gcp.gcsio import GcsIO
from apache_beam.options.pipeline_options import PipelineOptions


class Get_Yahoo_Data(DoFn):

    def process(self, element):
        """
        Extracts Yahoo Data

        """
        element_list=element.split(',',3)
        symbol_id = element_list[0]
        symbol = element_list[1]
        name = element_list[2]
        
        start_date=datetime.date.today()-datetime.timedelta(days=365)
        end_date = datetime.date.today()- datetime.timedelta(days = 3)
            
        Dataset = yf.download(symbol, start = start_date, end = end_date).rename(columns={"Adj Close": "Adj_Close"})
        Dataset= Dataset.asfreq('D',method='ffill').reset_index().to_json(orient="records", date_format='iso', date_unit='s')

        Dataset_str="{"+f'\"Symbol_ID\":{symbol_id},\"Symbol\":\"{symbol}\",\"Name\": \"{name}\",\"Info\":{Dataset}'+"}"
        
        yield Dataset_str
       
    
class Get_Data(PTransform):
    
    def expand(self, pcoll):
        return (
            pcoll 
            # Get stocks prices
            | 'Prices' >> ParDo(Get_Yahoo_Data())
        )

class Write_BQ(DoFn):
    """
       Writes to BQ

    """
    def process(self, element):
        rows=[json.loads(element)]
        client = bigquery.Client()
        table_obj = client.get_table(table_id)
        errors = client.insert_rows_json(table_obj, rows)

        yield errors

class Write_to_BQ(PTransform):
    
    def expand(self, pcoll):
        return (
            pcoll 
            # Get stocks prices
            | 'Write to BQ' >> ParDo(Write_BQ())
        )

def run(input_file,table_id, pipeline_args=None):
    pipeline_options = PipelineOptions(
        pipeline_args, streaming=False, save_main_session=True
    )
    with Pipeline(options=pipeline_options) as pipeline:
        (
            pipeline
            | "Get Symbol Names" >> io.textio.ReadFromText(input_file)
            | "get yahoo data" >> Get_Data()
            | "write to bigquery" >> Write_to_BQ()
        )
        
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        dest='input',
        help="Input that contains stocks markets order"
    )

    parser.add_argument(
        "--table_id",
        help="The BQ Table id to output in format project_id.dataset.table_name"
    )

    known_args, pipeline_args = parser.parse_known_args()
    print(pipeline_args)

    run(
        known_args.input,
        known_args.table_id,
        pipeline_args 
    )
