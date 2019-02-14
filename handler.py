import json
import os

import boto3 as boto3

NUMBER_OF_WORKER_ITEMS = int(os.environ['NUMBER_OF_WORKER_ITEMS'])

session = boto3.session.Session()
sqs = session.client('sqs')


def ventilator(event, context):
    print(event)

    # Create worker messages
    print("Create worker messages")
    messages = list()
    for count, _ in enumerate(range(NUMBER_OF_WORKER_ITEMS)):
        messages.append({
            'id': str(count),
        })

    # Send messages to workers in batches
    print("Send messages to workers in batches")
    messages_to_send = list()
    for count, message in enumerate(messages, 1):
        messages_to_send.append({
            'Id': str(count),
            'MessageBody': json.dumps(message),
        })
        if len(messages_to_send) == 10 or count == len(messages):
            print("Send batch with {} messages to SQS".format(len(messages_to_send)))
            sqs.send_message_batch(
                QueueUrl=os.environ['FAN_OUT_QUEUE_URL'],
                Entries=messages_to_send
            )
            messages_to_send = list()

    result = "Sent {} messages in total".format(len(messages))
    print(result)
    return result

def worker(event, context):
    for record in event['Records']:
        message = json.loads(record['body'])
        print("Received message: {}".format(message))

    return "ok"


def sink(event, context):
    print(event)

    return "ok"
