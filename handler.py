import json
import os
import random
import time
import uuid

import boto3 as boto3

NUMBER_OF_WORKER_ITEMS = int(os.environ['NUMBER_OF_WORKER_ITEMS'])

session = boto3.session.Session()
sqs = session.client('sqs')
dynamodb = session.client('dynamodb')


def ventilator(event, context):
    print(event)

    # Generate job_id for all messages
    job_id = str(uuid.uuid4())

    # Create worker messages
    print("Create worker messages")
    messages = list()
    message_ids = list()
    for count, _ in enumerate(range(NUMBER_OF_WORKER_ITEMS)):
        message_id = str(count)
        message_ids.append(message_id)
        messages.append({
            'id': message_id,
            'job_id': job_id,
        })

    # Mark messages as pending in DynamoDB
    dynamodb.update_item(
        TableName=os.environ['FAN_IN_TABLE'],
        Key={
            'key': {'S': job_id}
        },
        UpdateExpression='SET #pending_messages = :messages, #ttl = :ttl',
        ExpressionAttributeNames={
            '#pending_messages': 'pending_messages',
            '#ttl': 'ttl'
        },
        ExpressionAttributeValues={
            ':messages': {'NS': message_ids},
            ':ttl': {'N': str(int(time.time()) + 60 * 60 * 24)},
        },
    )

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

        message_id = message['id']
        job_id = message['job_id']

        # Do the work
        print("Work!")
        time.sleep(1 + random.randrange(1, 1000) * 0.001)

        # Delete message id from pending_messages
        dynamodb.update_item(
            TableName=os.environ['FAN_IN_TABLE'],
            Key={
                'key': {'S': job_id}
            },
            UpdateExpression='DELETE #pending_messages :messages',
            ExpressionAttributeNames={
                '#pending_messages': 'pending_messages'
            },
            ExpressionAttributeValues={
                ':messages': {'NS': [message_id]},
            },
        )

    return "ok"


def sink(event, context):
    for record in event['Records']:
        if record['eventSource'] != "aws:dynamodb" or record['eventName'] != "MODIFY":
            continue
        new_image = record['dynamodb']['NewImage']
        old_image = record['dynamodb']['OldImage']
        if 'pending_messages' in old_image and len(old_image['pending_messages']['NS']) == 1 and 'pending_messages' not in new_image:
            # All workers for job are finished
            print("All workers are finished for job {}".format(new_image['key']['S']))

    return "ok"
