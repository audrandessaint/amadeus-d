import boto3
import os

sqs = boto3.client('sqs')
queue_url = os.environ['QUEUE_URL']

def lambda_handler(event, context):
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody='A',
        MessageGroupId='messageGroup1'
    )
    print(f"Sent message: to queue: {queue_url}")
    return response
