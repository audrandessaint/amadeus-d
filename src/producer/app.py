import json
import os
import boto3

# Adjust environment variable names to match those defined in the SAM template
QUEUE_URL = os.environ['QUEUE_URL']
BUCKET_NAME = os.environ['BUCKET_NAME']
FILE_KEY = os.environ['FILE_KEY']
MINIMUM_REMAINING_TIME_MS = int(os.getenv('MINIMUM_REMAINING_TIME_MS', '10000'))
MAX_LAMBDA_INVOCATIONS = int(os.getenv('MAX_LAMBDA_INVOCATIONS', '10'))

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
lambda_client = boto3.client('lambda')

def handler(event, context):
    # Using BUCKET_NAME and FILE_KEY directly from environment variables
    bucket_name = BUCKET_NAME
    object_key = FILE_KEY
    offset = event.get('offset', 0)
    invocation_count = event.get('invocation_count', 0)  # Track the number of invocations

    body_lines = get_object_body_lines(bucket_name, object_key, offset)

    for line in body_lines.iter_lines():
        if context.get_remaining_time_in_millis() < MINIMUM_REMAINING_TIME_MS:
            break  # Time to prepare for the next invocation

        send_message_to_sqs(line)
    
    new_offset = offset + body_lines.offset
    print("Retriggering the function with offset: {}".format(new_offset))
    print("Retriggering the function with invocation count: {}".format(invocation_count))
    if new_offset < body_lines.content_length and invocation_count < MAX_LAMBDA_INVOCATIONS:
        invoke_next_lambda(context.function_name, new_offset, invocation_count + 1)
    else:
        print("Processing complete or max invocations reached.",'new_offset: ', new_offset,'invocation_count', invocation_count  )

def get_object_body_lines(bucket_name, object_key, offset):
    resp = s3_client.get_object(Bucket=bucket_name, Key=object_key, Range=f'bytes={offset}-')
    body = resp['Body']
    content_length = int(resp['ContentLength'])
    return BodyLines(body, offset, content_length)

def send_message_to_sqs(message_body):
    if message_body.strip():
        sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
    else:
        print("Empty message body, skipping SQS send")

def invoke_next_lambda(function_name, new_offset, invocation_count):
    new_event = {
        'bucket': BUCKET_NAME,
        'object_key': FILE_KEY,
        'offset': new_offset,
        'invocation_count': invocation_count
    }
    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event',
        Payload=json.dumps(new_event).encode('utf-8')
    )

class BodyLines:
    def __init__(self, body, initial_offset, content_length):
        self.body = body
        self.offset = initial_offset
        self.content_length = content_length

    def iter_lines(self, chunk_size=1024):
        pending = b''
        for chunk in self.body.iter_chunks(chunk_size):
            lines = (pending + chunk).split(b'\n')
            for line in lines[:-1]:
                self.offset += len(line) + 1  # Counting the separator
                decoded_line = line.decode('utf-8').strip()
                if decoded_line:  # Ensure line is not empty after stripping
                    yield decoded_line
            pending = lines[-1]
        if pending.strip():  # Check the pending line is not just whitespace
            self.offset += len(pending)
            yield pending.decode('utf-8').strip()



# from time import sleep
# import boto3
# import os
# import json

# s3 = boto3.client('s3')
# sqs = boto3.client('sqs')

# def handler(event, context):
#     bucket_name = os.environ['BUCKET_NAME']
#     file_key = os.environ['FILE_KEY']
#     queue_url = os.environ['QUEUE_URL']
    
#     lines = read_lines_from_s3(bucket_name, file_key)
#     if lines:
#         batch_send_messages_to_sqs(queue_url, lines)
#     else:
#         print("No lines found in the CSV file.")

# def read_lines_from_s3(bucket_name, file_key):
#     try:
#         response = s3.get_object(Bucket=bucket_name, Key=file_key)
#         lines = [line.split('^') for line in response['Body'].read().decode('utf-8').split('\n') if line]
#         return lines
#     except Exception as e:
#         print(f"An error occurred while reading file from S3: {e}")
#         return []

# def batch_send_messages_to_sqs(queue_url, messages):
#     batchSize = 10 
#     for i in range(0, len(messages), batchSize):
#         batch = messages[i:i+batchSize]
#         entries = [{'Id': str(index), 'MessageBody': json.dumps(message)} for index, message in enumerate(batch)]
#         try:
#             response = sqs.send_message_batch(
#                 QueueUrl=queue_url,
#                 Entries=entries
#             )
#             # print(f"Batch Message sent: {response}")
#         except Exception as e:
#             print(f"An error occurred while sending messages to SQS queue: {e}")
