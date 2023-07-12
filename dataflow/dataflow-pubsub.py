import argparse
from datetime import datetime
import logging
import random
import requests
import json
from bs4 import BeautifulSoup
import datetime
from pytz import timezone
from google.cloud import pubsub_v1

from apache_beam import DoFn, GroupByKey, io, ParDo, Pipeline, PTransform, WindowInto, WithKeys, pvalue
from apache_beam.options.pipeline_options import PipelineOptions

class Get_Current_Price(DoFn):
    def process(self, element):
        logging.info("element inside Get_Current_Price %s",element)
        p_element=element.decode('utf-8')
        url = f"https://finance.yahoo.com/quote/{p_element}/"
        logging.info("the url is %s",url)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        tz = timezone('America/Toronto')
        now=datetime.datetime.now(tz)
        dt_string = now.strftime("%B %d %I:%M%p EDT")

        current_price = soup.find("fin-streamer", class_="Fw(b) Fz(36px) Mb(-4px) D(ib)").text
        market_change = soup.find("fin-streamer", class_="Fw(500) Pstart(8px) Fz(24px)").find("span").text
        market_change_percent = soup.find("fin-streamer", class_="Fw(500) Pstart(8px) Fz(24px)").find_next_sibling("fin-streamer").text[1:-1]
        
        if p_element[:4]=="GOOG":
            p_element="A"+p_element
        yield (
            "{"+"\"type\":\"curr_prices\",\"current_price\":{},\"market_change\":\"{}\",\"market_change_percent\":\"{}\",\"date\":\"{}\",\"symbol\":\"{}\"".format(current_price,market_change,market_change_percent,dt_string, p_element)+"}"
            )
    
class Obtain_prices(PTransform):
    
    def expand(self, pcoll):
        return (
            pcoll 
            # Get stocks prices
            | 'Prices' >> ParDo(Get_Current_Price())
        )
    
class Get_Output_Topic(DoFn):
    def __init__(self, output_topic):
        self.output_topic = output_topic

    def process(self, element):
        logging.info("element inside WriteToPubSub %s",element)
        symbol=element.rsplit(':', 1)[1].rsplit('\"')[1]
        output_topic=self.output_topic

        publisher = pubsub_v1.PublisherClient()
        message=bytes("{}".format(element), 'utf-8')
        future = publisher.publish(output_topic, message, symbol=symbol)     
        logging.info("Publishing to %s %s %s",output_topic, future.result(), symbol)

        yield element

class Obtain_Output_Topic(PTransform):
    def __init__(self, output_topic):
        self.output_topic = output_topic
    
    def expand(self, pcoll):
        return (
            pcoll 
            # Get stocks prices
            | 'Write to PubSub' >> ParDo(Get_Output_Topic(self.output_topic))
        )

def run(input_topic, output_topic,pipeline_args=None):
    pipeline_options = PipelineOptions(
        pipeline_args, streaming=True, save_main_session=True
    )
    with Pipeline(options=pipeline_options) as pipeline:
        (
            pipeline

            | "Read from Pub/Sub" >> io.ReadFromPubSub(topic=input_topic)
            | "Obtain Prices" >> Obtain_prices()
            | "Write to Pub/Sub" >>  Obtain_Output_Topic(output_topic)
        )
        
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input_topic",
        help="The Cloud Pub/Sub topic to read from."
        '"projects/<PROJECT_ID>/topics/<TOPIC_ID>".',
    )
    parser.add_argument(
        "--output_topic",
        help="The Cloud Pub/Sub topic to publidh data."
        '"projects/<PROJECT_ID>/topics/<TOPIC_ID>".',
    )

    known_args, pipeline_args = parser.parse_known_args()

    run(
        known_args.input_topic,
        known_args.output_topic, 
        pipeline_args,
    )
