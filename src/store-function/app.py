import os
import boto3
import json

s3 = boto3.client('s3')
redshift = boto3.client('redshift-data')

def lambda_handler(event, context):
    create_redshift_table()
    # bucket_name = event['Records'][0]['s3']['bucket']['name']
    bucket_name = os.environ["BUCKET_NAME"]
    object_key = event['Records'][0]['s3']['object']['key']
    
    copy_data_to_redshift(bucket_name, object_key)
    return {
        "statusCode": 200,
        "body": "OK",
    }


def create_redshift_table():
    query = """
    CREATE TABLE IF NOT EXISTS decorated_searches
    (
      version_nb             VARCHAR(5) NOT NULL,
      search_id              VARCHAR(50) NOT NULL,
      search_country         VARCHAR(3) NOT NULL,
      search_date            DATE NOT NULL,
      search_time            TIME NOT NULL,
      origin_city            VARCHAR(3) NOT NULL,
      destination_city       VARCHAR(3) NOT NULL,
      request_dep_date       DATE NOT NULL,
      request_return_date    DATE,
      passengers_string      VARCHAR(10) NOT NULL,
      currency               VARCHAR(3) NOT NULL,
      price                  DECIMAL(10, 2) NOT NULL,
      taxes                  DECIMAL(10, 2) NOT NULL,
      fees                   DECIMAL(10, 2) NOT NULL,
      nb_of_flights          INTEGER NOT NULL,
      advance_purchase       INTERVAL DAY TO SECOND,
      price_eur              DECIMAL(10, 2) NOT NULL,
      main_airline           VARCHAR(3) NOT NULL,
      PRIMARY KEY (search_id)
    );

    CREATE TABLE IF NOT EXISTS flight_legs
    (
      search_id             VARCHAR(50) NOT NULL,
      dep_airport           VARCHAR(3) NOT NULL,
      dep_date              DATE NOT NULL,
      dep_time              TIME NOT NULL,
      arr_airport           VARCHAR(3) NOT NULL,
      arr_date              DATE NOT NULL,
      arr_time              TIME NOT NULL,
      operating_airline     VARCHAR(3) NOT NULL,
      marketing_airline     VARCHAR(3) NOT NULL,
      flight_nb             VARCHAR(10) NOT NULL,
      cabin                 VARCHAR(1) NOT NULL,
      FOREIGN KEY (search_id) REFERENCES decorated_searches(search_id)
    );
    """
    try:
        response = redshift.execute_statement(Database=os.environ["DB_NAME"], Sql=query)
        print("Table created successfully.")
    except Exception as e:
        print(f"Error creating table: {str(e)}")

def copy_data_to_redshift(bucket_name, object_key):
    try:
        copy_query = f"""
        COPY decorated_searches
        FROM 's3://{bucket_name}/{object_key}'
        IAM_ROLE 'your_redshift_iam_role_arn'
        FORMAT AS JSON 'auto';
        """
        response = redshift.execute_statement(Database='your_database_name', Sql=copy_query)
        print("Data copied successfully.")
    except Exception as e:
        print(f"Error copying data: {str(e)}")
