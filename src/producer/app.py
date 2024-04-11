from time import sleep
import boto3
import os
import json

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']
    file_key = os.environ['FILE_KEY']
    queue_url = os.environ['QUEUE_URL']
    
    lines = read_lines_from_s3(bucket_name, file_key)
    if lines:
        sorted_lines = sort_lines_by_datetime(lines)
        for line in sorted_lines:
            send_message_to_sqs(queue_url, line)
            print("Message sent to SQS queue.")
    else:
        print("No lines found in the CSV file.")

def read_lines_from_s3(bucket_name, file_key):
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        lines = [line.split('^') for line in response['Body'].read().decode('utf-8').split('\n')]
        return lines
    except Exception as e:
        print("An error occurred while reading file from S3:", e)
        return []

def sort_lines_by_datetime(lines):
    try : 
        sorted_lines = sorted(lines, key=lambda x: (x[3], x[4]))
        return sorted_lines
    except Exception as e:  
        print("An error occurred while sorting lines:", e)

def send_message_to_sqs(queue_url, message):
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        print(f"Message sent: {response['MessageId']}")
    except Exception as e:
        print("An error occurred while sending message to SQS queue:", e)
        raise e
