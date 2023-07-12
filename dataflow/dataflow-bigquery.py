import argparse
import logging
import requests

import json
from bs4 import BeautifulSoup
import yfinance as yf
import datetime

from google.cloud import bigquery

from apache_beam import DoFn, io, ParDo, Pipeline, PTransform, CombineGlobally
from apache_beam.io.gcp.gcsio import GcsIO
from apache_beam.options.pipeline_options import PipelineOptions

class UserOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_value_provider_argument("--input")
        parser.add_value_provider_argument("--output")

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
        dataset_id ="{}.Stocks_dataset".format(client.project)

        table_id= dataset_id+".Stocks_info"

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

class Write_to_GCS(PTransform):
    def __init__(self, output):
        self.output=output

    def combine_data(self, Data):
        start_date=datetime.date.today()-datetime.timedelta(days=365)
        end_date = datetime.date.today()- datetime.timedelta(days = 3)
        Dataset = yf.download("AAPL", start = start_date, end = end_date).reset_index()
        return Dataset["Date"].max().isoformat()[:10]

    def expand(self, pcoll):
        return (
            pcoll 
            # Get stocks prices
            | 'Get Date' >> CombineGlobally(self.combine_data)
            | 'Write to Bucket' >> io.textio.WriteToText(self.output, num_shards=1, file_name_suffix=".txt")
        )

def run(pipeline_args=None):
    pipeline_options = PipelineOptions(
        pipeline_args, streaming=False, save_main_session=True
    )
    user_options = pipeline_options.view_as(UserOptions)
    with Pipeline(options=pipeline_options) as pipeline:
        (
            pipeline
            | "Get Symbol Names" >> io.textio.ReadFromText(user_options.input)
            | "Get Yahoo Data" >> Get_Data()
            | "Write To BigQuery" >> Write_to_BQ()
            | "Write to GCS" >> Write_to_GCS(user_options.output)
        )
        
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()

    other, pipeline_args = parser.parse_known_args()
    run( pipeline_args )
