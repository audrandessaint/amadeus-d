import os
import csv

import boto3


def lambda_handler(event, context):
    bucket_name = os.environ["BUCKET_NAME"]
    filename = "/tmp/batch.csv"
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    headers = list(event["Records"][0]["body"].keys())

    batch = [headers] 
    for record in event["Records"]:
        body = record["body"]
        batch.append([body[header] for header in headers])

    with open(filename, 'w', newline='') as batch_output:
        writer = csv.writer(batch_output, delimiter='^')
        writer.writerows(batch)
        
    bucket.upload_file(filename, "tmp-key")

    return {
        "StatusCode": 200,
        "Body": "OK"
    }