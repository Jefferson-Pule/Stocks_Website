import argparse
import logging
import requests

import json
from bs4 import BeautifulSoup
import yfinance as yf
import datetime

from google.cloud import bigquery

from apache_beam import DoFn, io, ParDo, Pipeline, PTransform, CombineGlobally, Map
from apache_beam.io.gcp.gcsio import GcsIO
from apache_beam.options.pipeline_options import PipelineOptions

class UserOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_value_provider_argument("--input")
        parser.add_value_provider_argument("--output")
        parser.add_value_provider_argument("--last_updated")

class Get_Yahoo_Data(DoFn):
    def __init__(self, last_updated):

        self.last_updated=last_updated

    def process(self, element):
        """
        Extracts Yahoo Data

        """

        element_list=element.split(',',3)
        symbol_id = element_list[0]
        symbol = element_list[1]
        name = element_list[2]
        start_date = datetime.datetime.strptime(self.last_updated.get(), "%Y-%m-%d")
        end_date = datetime.date.today()+datetime.timedelta(days=1)
        try:
            Dataset = yf.download(symbol, start = start_date, end = end_date)
            Dataset= Dataset.asfreq('D',method='ffill').reset_index()

            Data=Dataset.apply(lambda row:
                    "STRUCT<Date TIMESTAMP, Open FLOAT64, High FLOAT64, Low FLOAT64, Close FLOAT64, Adj_Close FLOAT64, Volume FLOAT64>({})".format(
                    "\""+row[0].strftime('%Y-%m-%dT%H:%M:%S')+"\""+","+str(row[1])+","+str(row[2])+","+str(row[3])+","+str(row[4])+","+str(row[5])+","+str(row[6])
                    ), axis=1)             
            struct_data="["+",".join(Data)+"]"
        
            almost_query=f"WHEN Symbol_ID={symbol_id} THEN ARRAY_CONCAT(info,{struct_data})"

            yield almost_query
        except:
            yield ""
    
class Get_Data(PTransform):
    def __init__(self, last_updated):
      self.last_updated=last_updated
    
    def expand(self, pcoll):
        return (
            pcoll 
            # Get stocks prices
            | 'Prices' >> ParDo(Get_Yahoo_Data(self.last_updated))
        )

class Write_BQ(DoFn):

    """
       Writes to BQ

    """
    def process(self, element):

        client = bigquery.Client()
        dataset_id ="{}.Stocks_dataset".format(client.project)

        table_id= dataset_id+".Stocks_info"

        QUERY=f"UPDATE `{table_id}` SET info = ( CASE \n"+element+"\n ELSE info END) WHERE Symbol_ID>=1"

        table_obj = client.get_table(table_id)
        query_job = client.query(QUERY)
        result=query_job.result()
        logging.info("Results loaded to BigQuery")
        yield datetime.date.today().isoformat()

class Write_to_BQ(PTransform):

    def combine_data(self, Data):
        return "\n".join(Data)

    def expand(self, pcoll):
        return (
            pcoll 
            # Get stocks prices
            | 'Create Query' >> CombineGlobally(self.combine_data)
            | 'Write to BQ' >> ParDo(Write_BQ())
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
            | "Get Yahoo Data" >> Get_Data(user_options.last_updated)
            | "Write to BigQuery" >> Write_to_BQ()
            | "Update Last Date"  >> io.textio.WriteToText(user_options.output, num_shards=1, file_name_suffix=".txt")
        )
        
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()

    other, pipeline_args = parser.parse_known_args()
    run( pipeline_args )
