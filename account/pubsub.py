import environ
import os
import io
import google.auth

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1

def pull(slug):
    
    # Load the settings from the environment variable
    env = environ.Env()

    LOCAL_ENV_PATH=os.environ.get("LOCAL_ENV_PATH", None)
    if LOCAL_ENV_PATH:
        env.read_env(LOCAL_ENV_PATH)

    PROJECT_ID=env("PROJECT_ID")
    #print(PROJECT_ID)

    # TODO(developer)
    project_id = PROJECT_ID
    subscription_id = slug+"-sub"
    # Number of seconds the subscriber should listen for messages
    timeout = 5.0

    subscriber = pubsub_v1.SubscriberClient()

    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        print(f"Received {message}.")
        message.ack()


    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.
    print("finished_listening")
    
