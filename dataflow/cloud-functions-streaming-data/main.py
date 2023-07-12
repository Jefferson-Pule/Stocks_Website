from concurrent import futures
from google.cloud import pubsub_v1
from typing import Callable
import os
import pandas as pd

def get_callback(
    publish_future: pubsub_v1.publisher.futures.Future, data: str
) -> Callable[[pubsub_v1.publisher.futures.Future], None]:
    def callback(publish_future: pubsub_v1.publisher.futures.Future) -> None:
        try:
            # Wait 60 seconds for the publish call to succeed.
            print(publish_future.result(timeout=60))
        except futures.TimeoutError:
            print(f"Publishing {data} timed out.")
    return callback

def request_job(data, context):

    project_id = os.environ["PROJECT_ID"]
    topic_id = os.environ["TOPIC_ID"]

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    publish_futures = []
    symbols=pd.read_csv("symbols.csv", header=None)

    for symbol in symbols[0]:
        data = symbol
        # When you publish a message, the client returns a future.
        publish_future = publisher.publish(topic_path, data.encode("utf-8"))
        # Non-blocking. Publish failures are handled in the callback function.
        publish_future.add_done_callback(get_callback(publish_future, data))
        publish_futures.append(publish_future)

    # Wait for all the publish futures to resolve before exiting.
    futures.wait(publish_futures, return_when=futures.ALL_COMPLETED)

    print(f"Published messages with error handler to {topic_path}.")