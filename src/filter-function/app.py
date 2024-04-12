import os
import boto3
from boto3.dynamodb.conditions import Key
import json
import datetime


def lambda_handler(event, context):
    
    for record in event['Records']:
        # Extract message body
        message_body = record['body']
        
        reco = decode_line(message_body)

        send_to_queue(reco,'BACKUP_STORAGE_QUEUE_URL')

        # Get exchange_rate from CurrencyCacheTable if currency != EUR
        exchange_rate = 1
        if reco['currency'] != "EUR":
            year, month, day = reco['search_date'].split('-')
            exchange_rate = get_exchange_rate(reco['currency'],"2024-03")
        
        decorated_reco = decorate(reco,exchange_rate)
        print(decorated_reco)

        send_to_queue(decorated_reco,'OUTPUT_QUEUE_URL')

    return {
        "statusCode": 200,
        "body": "OK",
    }


_RECO_LAYOUT = ["version_nb", "search_id", "search_country",
                "search_date", "search_time", "origin_city", "destination_city", "request_dep_date",
                "request_return_date", "passengers_string",
                "currency", "price", "taxes", "fees", "nb_of_flights"]


_FLIGHT_LAYOUT = ["dep_airport", "dep_date", "dep_time",
                  "arr_airport", "arr_date", "arr_time",
                  "operating_airline", "marketing_airline", "flight_nb", "cabin"]



def decode_line(line):
    """
    Decodes a CSV line based on _RECO_LAYOUT and _FLIGHT_LAYOUT
    :param line: string containing a CSV line
    :return reco: dict with decoded CSV fields
    """
    
    try:
        # converting to text string
        if isinstance(line, bytes):
            line = line.decode()

        # splitting the CSV line
        array=line.rstrip().split('^')
        if len(array)<=1:
            print("Empty line")
            return None # skip empty line
    
        # decoding fields prior to flight details
        reco = dict(zip(_RECO_LAYOUT, array))
        read_columns_nb=len(_RECO_LAYOUT)

        # convert to integer
        reco["nb_of_flights"] = int(reco["nb_of_flights"])

        # decoding flights details
        reco["flights"]=[]
        for i in range(0, reco["nb_of_flights"]):
            flight=dict(zip(_FLIGHT_LAYOUT, array[read_columns_nb:]))
            read_columns_nb+=len(_FLIGHT_LAYOUT)
            reco["flights"].append(flight)

    except:
        print("Failed at decoding CSV line: %s" % line.rstrip())
        return None
    
    return reco

def send_to_queue(reco,queue_name):
    sqs = boto3.client('sqs')
    # Convert reco dictionary to JSON string
    message_body = json.dumps(reco, indent=4, sort_keys=True, default=str)#json.dumps(reco)
    
    response = sqs.send_message(
        QueueUrl=os.environ[queue_name],
        MessageBody=message_body
    )
    
    print(f"Message sent to {queue_name} Queue:", response)


def get_exchange_rate(currency, dateISO):
    dynamodb = boto3.resource('dynamodb')
    currency_cache_table = dynamodb.Table(os.environ['CURRENCY_CACHE_TABLE_NAME'])
    response = currency_cache_table.query(
        KeyConditionExpression=Key('currency_type').eq(currency) & Key('dateISO').eq(dateISO),
        ProjectionExpression='exchange_rate'
    )
    items = response['Items']
    if items:
        return items[0]['exchange_rate']
    else:
        return None
        
        
def decorate(reco,exchange_rate):
    
    decorated_reco = reco.copy()
    
    search_date = datetime.datetime.strptime(reco["search_date"], '%Y-%m-%d')
    dep_date = datetime.datetime.strptime(reco["request_dep_date"], '%Y-%m-%d')
    advance_purchase = dep_date - search_date
    
    stay_duration = 0
    
    if reco["request_return_date"] != "":
        return_date = datetime.datetime.strptime(reco["request_return_date"], '%Y-%m-%d')
        stay_duration = return_date - dep_date
        decorated_reco["stay_duration"] = stay_duration
        
        
    flights = reco["flights"]
    price_eur = round(float(reco["price"])/float(exchange_rate), 2)
    marketing_airlines = {}
    for flight in flights:
        market_airline = flight["marketing_airline"]
        if not( market_airline in marketing_airlines.keys()):
            marketing_airlines[market_airline] = 1
        else:
            marketing_airlines[market_airline] += 1
    main_airline = max(marketing_airlines, key=marketing_airlines.get)
    decorated_reco["advance_purchase"] = advance_purchase
    decorated_reco["price_eur"] = price_eur
    decorated_reco["main_airline"] = main_airline
    
    return decorated_reco
    