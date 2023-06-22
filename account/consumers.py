
import json
from channels.generic.websocket import WebsocketConsumer
from datetime import datetime
import asyncio
import time

import environ
import os
import io
import google.auth

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
import random
#from .pubsub import pull

class priceConsumer(AsyncWebsocketConsumer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.m_gr=[]

    def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        if random.randint(0,1):            
            messag=json.dumps({"type":"curr_prices","current_price":180.96+random.randint(1,10),"market_change":"+0.39","market_change_percent":"+0.22","symbol":"AAPL","date":"June 10 04:59AM EDT"})
        else:
            messag=json.dumps({"type":"curr_prices","current_price":180.96+random.randint(1,10),"market_change":"-0.39","market_change_percent":"+0.22","symbol":"AAPL","date":"June 10 04:59AM EDT"})
        self.m_gr.append(message.data.decode("utf-8") )

        print(f"Received {message}.")
        message.ack()

    def pull(self, slug):
        if len(slug)>3 and slug[:4]=="GOOG":
            slug="A"+slug
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
        #print(project_id, subscription_id)

        subscriber = pubsub_v1.SubscriberClient()

        # The `subscription_path` method creates a fully qualified identifier
        # in the form `projects/{project_id}/subscriptions/{subscription_id}`
        subscription_path = subscriber.subscription_path(project_id, subscription_id)

        streaming_pull_future = subscriber.subscribe(subscription_path, callback=self.callback)
        
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
        

    async def connect(self):
        # Called on connection.
        # To accept the connection call:
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are connected to current price'
            }))

    async def receive(self, text_data=None, bytes_data=None):
        while True:
            self.m_gr=[]
            #self.m_gr.append(text_data)
            await sync_to_async(self.pull)(text_data)
            for message in self.m_gr:
                await self.send(text_data=message)
            await asyncio.sleep(2)
        
