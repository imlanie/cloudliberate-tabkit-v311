import json
import boto3
import requests
from requests.auth import HTTPBasicAuth
from urllib import parse
import datetime


def get_oauth2_token(COGNITO_DOMAIN, COG_HOSTED_UI_ID, COG_HOSTED_UI_SECRET_KEY, AUTHORIZATION_CODE, apigtwy_id, environment):

    response = requests.post("{}/oauth2/token".format(COGNITO_DOMAIN),
                             auth=HTTPBasicAuth(
        COG_HOSTED_UI_ID, COG_HOSTED_UI_SECRET_KEY),
        data={'grant_type': 'authorization_code',
              'client_id': COG_HOSTED_UI_ID,
              'code': AUTHORIZATION_CODE,
              'redirect_uri': 'https://{}.execute-api.us-west-2.amazonaws.com/{}/auth'.format(apigtwy_id, environment)}
    )

    # return response.json()
    return response
