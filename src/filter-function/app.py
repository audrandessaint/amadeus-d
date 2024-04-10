def lambda_handler(event, context):
    
    for record in event['Records']:
        # Extract message body
        message_body = record['body']
        
        reco = decode_line(message_body)
        print(reco)

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
        # array=line.rstrip().split('^')
        array=line
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