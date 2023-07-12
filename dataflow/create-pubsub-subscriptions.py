import argparse
import pandas as pd
from google.cloud import pubsub_v1

def create_subscription(project_id, topic_id, symbol):

    if symbol[:4]=="GOOG":
        symbol="A"+symbol

    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    subscription_id = symbol+"-sub"
    filter = f"attributes.symbol=\"{symbol}\""
    
    topic_path = publisher.topic_path(project_id, topic_id)

    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    with subscriber:
        subscription = subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path, "filter": filter}
        )
        print(f"Created subscription with filtering enabled: {subscription}")
        
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--project_id",
        help="The Project ID."
    )
    parser.add_argument(
        "--topic_id",
        help="The Cloud Pub/Sub topic to read from."
        '"<TOPIC_ID>".',
    )

    args = parser.parse_args()

    data=pd.read_csv("../local_data/SP500_stocks_info.csv", header=None, usecols=[1])   

    for symbol in data[1]:
        create_subscription(args.project_id, args.topic_id, symbol)
    print("Subscriptions created")