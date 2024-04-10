import os
import json

import boto3

def lambda_handler(event, context):
    s3 = boto3.client("s3")

    bucket_name = os.environ["BUCKET_NAME"]

    for record in event["Records"]:
        s3.put_object(Bucket=bucket_name, Key=f"{record["messageId"]}.json", Body=record["body"])

    return {
        'statusCode': 200,
        'body': json.dumps('Messages processed and stored in S3')
    }
