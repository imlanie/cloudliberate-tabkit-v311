# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
import json
from botocore.exceptions import ClientError


def get_secret(in_secret_name):

    secret_name = in_secret_name
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    # print(get_secret_value_response)
    secret = get_secret_value_response['SecretString']
    # print(secret)

    json_secret = json.loads(secret)
    # print(type(json_secret))
    # print(json_secret)

    return json_secret


def get_cognito_host_ui_secret():

    secret_name = "cognito-hosted-ui-secret"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as ex:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        print(ex)
        # Decrypts secret using the associated KMS key.
        secret = get_secret_value_response['SecretString']

        json_secret = json.loads(secret)
        # print(type(json_secret))
        # print(json_secret)
        # print(json_secret["cognito-hosted-ui-secret"])
        return json_secret


def get_tabkit_app_secret_key():

    secret_name = "tabkit-app-secret-key"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    # print(get_secret_value_response)
    secret = get_secret_value_response['SecretString']
    # print(secret)

    json_secret = json.loads(secret)
    # print(type(json_secret))
    # print(json_secret)

    return json_secret
