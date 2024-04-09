def lambda_handler(event, context):
    for record in event['Records']:
        print(f"Message received: {record['body']}")
    return {'status': 'done'}
