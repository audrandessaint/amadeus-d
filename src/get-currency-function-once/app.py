import subprocess
import csv
import boto3
import os
from decimal import Decimal

def lambda_handler(event, context):
    
    table_name = os.environ['CURRENCY_CACHE_TABLE']
    client = boto3.client('dynamodb')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table_scan = client.scan(TableName=table_name, Select='COUNT')
    
    if table_scan['ScannedCount'] == 0 :
        print("Table is empty !")

        currencies = ["USD", "JPY", "BGN", "CZK", "DKK", "GBP", "HUF", "PLN", "RON", "SEK", "CHF", "ISK", "NOK", "TRY", "AUD", "BRL", "CAD", "CNY", "HKD", "IDR", "ILS", "INR", "KRW", "MXN", "MYR", "NZD", "PHP", "SGD", "THB", "ZAR"]
    
        url = f"https://data-api.ecb.europa.eu/service/data/EXR/M.{'+'.join(currencies)}.EUR.SP00.A?format=csvdata&lastNObservations=1&detail=dataonly"
    
        result = subprocess.check_output(f'curl -s "{url}"', shell=True).decode("utf-8")
        reader = csv.reader(result.splitlines())
    
        # ignore first lign
        next(reader)
    
        for row in reader:
            print(f"1€ = {row[-1]} {row[2]}")
            currency_type = row[2]
            exchange_rate = Decimal(str(row[-1]))
            dateISO = row[6]
            
            table.put_item(
                Item={
                    'currency_type': currency_type,
                    'exchange_rate': exchange_rate,
                    'dateISO': dateISO,
                }
            )
    
    return {
        "statusCode": 200,
        "body": "OK",
    }