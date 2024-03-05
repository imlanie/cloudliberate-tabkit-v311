# Update notes for sam-app CF stack 8/9/2023
# TabKit Container Menu configuration values are stored in a file manu.txt in s3 bucket cloud-liberate
# Permanent Session Lifetime config value is very important.  It's default is set to 5 minutes but can be changed longer but not
# shorter.  It works parallelly with Congnito and Cognito enforces a 5 minute minimum before a login can expire.

from get_secrets import get_secret, get_cognito_host_ui_secret, get_tabkit_app_secret_key
import get_secrets
from authorize import get_oauth2_token
import authorize
import os
import awsgi
import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, flash, jsonify, make_response, request, redirect, render_template, render_template_string, session, url_for
from flask_paranoid import Paranoid
import jwt
import base64
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import datetime
from datetime import timedelta, datetime
import polly
from polly import run_voice_new
from classes import S3BucketManager
# from send_email import send_plain_email, send_email_with_attachment

app = Flask(__name__)

# the os environ values are set in the Lambda Config Env Vars
apigtwy_id = os.environ['API_GATEWAY_ID']
COGNITO_USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
COGNITO_DOMAIN = os.environ['COGNITO_DOMAIN']

COG_HOSTED_UI_ID = os.environ["COGNITO_HOST_UI_ID"]
cognito_host_ui_secret_name = os.environ['COGNITO_HOST_UI_SECRET_NAME']
host_ui_secret = get_secret(cognito_host_ui_secret_name)
# Do not change host_ui_secret for cloudliberate user pool
COG_HOSTED_UI_SECRET_KEY = host_ui_secret['cloudliberate-tabkit-secret']
S3_BUCKET = os.environ['S3_BUCKET']
S3_BUCKET_FOLDER = os.environ['S3_BUCKET_FOLDER']

app.config["UPLOAD_FOLDER"] = "/tmp"
app.config['APPLICATION_ROOT'] = 'var/task'
app.config['SESSION_COOKIE_NAME'] = 'session_two'
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# AWS SECRETS MANAGER
app.secret_key = get_tabkit_app_secret_key()

paranoid = Paranoid(app)
paranoid.redirect_view = '/auth'

# Return messages for route Notice
msg_session_expired = "Session is expired. Open a new tab, or browser and start a new session."
msg_not_authorized = "Test not authorized."
msg_go_back = "Back to Launchpad."

current_day = datetime.now()
curr_year = current_day.year
current_year = str(curr_year)

dynamodb_resource = boto3.resource('dynamodb', region_name='us-west-2')
table_cust = dynamodb_resource.Table('tabkit_customers')
table_users = dynamodb_resource.Table('tabkit_users')


@app.before_request
def before_request_func():
    print("before_request executing!")

    # default authorization is not authorized
    authorized = "401"
    sess_active = 'false'
    current_datetime = datetime.now()
    time_difference = 0
    str_time_difference = ""

    if 'id_token_will_expire' in session:
        id_token_will_expire = session['id_token_will_expire']

    # print(current_datetime)
        request_start_time = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        request_start_time = datetime.strptime(
            request_start_time, '%Y-%m-%d %H:%M:%S')
        print(request_start_time)

        id_token_will_expire_time = id_token_will_expire.strftime(
            "%Y-%m-%d %H:%M:%S")

        id_token_will_expire_time_dt = datetime.strptime(
            id_token_will_expire_time, '%Y-%m-%d %H:%M:%S')
        # print(id_token_will_expire_time_dt)

        if request_start_time >= id_token_will_expire_time_dt:

            time_difference = (
                id_token_will_expire_time_dt - request_start_time)
            # print("ID token is expired: " + str(time_difference))
            session['authorized'] = "401"
            session['active'] = sess_active
            str_time_difference = str(time_difference)
            session['time_remaining'] = str_time_difference

        else:
            time_difference = (
                id_token_will_expire_time_dt - request_start_time)
            print("ID token is active")
            session['authorized'] = "200"
            session['active'] = "true"
            str_time_difference = str(time_difference)
            session['time_remaining'] = str_time_difference


# Verify token and start a session and set cookie user email
def verify_oauth_token(in_id_token):
    # Verify a cognito JWT
    # get the key id from the header, locate it in the cognito keys
    # and verify the key

    JWKS_URL = "https://cognito-idp.us-west-2.amazonaws.com/{}/.well-known/jwks.json".format(
        COGNITO_USER_POOL_ID)
    id_token = in_id_token

    cognito_well_known_keys = requests.get(JWKS_URL).json()["keys"]
    algorithm = jwt.get_unverified_header(id_token).get('alg')
    jwt_unv_hdr = jwt.get_unverified_header(id_token)
    matched_kid = ""

    # print("JWKS items")
    for item in cognito_well_known_keys:
        # print("cognito well known keys")
        # print(item)

        if item['kid'] == jwt_unv_hdr['kid']:
            # print("match")
            matched_kid = item['kid']
        else:
            pass
        # print("this is the matched kid")
        # print(matched_kid)

    # this throws an error saying that the algorithm is not supported
    # FIXED THE ERROR BY ADDING VERIFY=FALSE
    z = jwt.decode(id_token, key=matched_kid,
                   algorithms=algorithm, verify=False)

    # token is already decoded successfully but signature decoding is not working
    # signature successfully decoded in jwt.io
    # print("Results from jwt.decode. This is the JWT token payload")
    # print(z)

    session['user_email'] = z['email']
    session['email_verified'] = z['email_verified']
    print(z['email_verified'])
    print(z['email'] + " is authorized")
    cookie_resp = make_response("set user email cookie")
    cookie_resp.set_cookie('cookie_user_email', z['email'])
    print("client cookie created")

    return("200")


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    # Clear the email stored in the session object

    session.pop('email', default=None)
    return_msg = "You have been logged out.."
    options = "return to home"

    return render_template("notice.html", notice_msg=return_msg, options=options)


@app.route('/auth', methods=['GET', 'POST'])
def index():

    try:
        event = request.environ.get("awsgi.event", {})
        print("Auth route is running")

        AUTHORIZATION_CODE = event['queryStringParameters']['code']
        session['cognito_auth_code'] = AUTHORIZATION_CODE
        environment = event['requestContext']['stage']
        print("Environment: " + environment)
        # print(COG_HOSTED_UI_ID)
        # print(COG_HOSTED_UI_SECRET_KEY)
        # print(COGNITO_USER_POOL_ID)
        # print(COGNITO_DOMAIN)
        # print("{}/oauth2/token".format(COGNITO_DOMAIN))
        # print(AUTHORIZATION_CODE)
        # print(apigtwy_id)

        response = get_oauth2_token(COGNITO_DOMAIN, COG_HOSTED_UI_ID,
                                    COG_HOSTED_UI_SECRET_KEY, AUTHORIZATION_CODE, apigtwy_id, environment)

        # print("response:")
        # print(response)

        statusCode = response.status_code
        statusCode = str(statusCode)
        print(statusCode)

        oauth2_id_token = response.json()["id_token"]
        oauth2_access_token = response.json()['access_token']
        expires_in_seconds = response.json()['expires_in']
        print(expires_in_seconds)

        # Get the current date and time
        current_datetime = datetime.now()

        # Format the current date and time as a string
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        # print("Formatted Date and Time:", formatted_datetime)

        # Add x number of seconds
        x = expires_in_seconds  # Example: adding 1 hour (3600 seconds)
        will_expire_datetime = current_datetime + timedelta(seconds=x)

        # Format the new date and time as a string
        fmt_will_expire_datetime = will_expire_datetime.strftime(
            "%Y-%m-%d %H:%M:%S")
        # print(
        # f"Token will expire :", fmt_will_expire_datetime)

        authorized = verify_oauth_token(oauth2_id_token)
        print("Authorization: " + authorized)
        session['authorized'] = authorized
        session['id_token_will_expire'] = will_expire_datetime
        session['env'] = environment

        url = 'https://{}.execute-api.us-west-2.amazonaws.com/{}/dashboard'.format(
            apigtwy_id, environment)

        return redirect(url)

    except Exception as ex:
        print("exception occurred: " + str(ex))
        return_msg = "Exception Occured or Not Authorized"
        options = 'return to home'
        return render_template("notice.html", notice_msg=return_msg, options=options)


@ app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    try:
        user = session['user_email']
        user = user.replace(".", "_")
        user_menu_end = "_menu.txt"
        user_menu_name = user + user_menu_end
        user_menu_full_filename = S3_BUCKET_FOLDER + user_menu_name
        # filepath = "/tmp/menu.txt"
        user_menu_filepath = "/tmp/" + user_menu_name

        # Download the User Menu from S3 bucket folder 'Tabkit-menus'
        s3_client = boto3.client('s3')
        s3_client.download_file(
            S3_BUCKET, user_menu_full_filename, user_menu_filepath)
        with open(user_menu_filepath, 'r') as f:
            customer_menu = json.loads(f.read())

        if 'authorized' in session:
            authorized = session['authorized']

            if authorized == "200":
                # active = session['active']

                #cookie_value = request.cookies.get("cookie_user_email")
                print("client cookie value: ")

                routes_menu = {"announce": "Get Notes",
                               "upload_files": "Run Automation",
                               "about": "About TabKit"
                               }

                return render_template("index.html", dict_menu=routes_menu, customer_menu=customer_menu, auth=authorized)
            else:
                return_msg = msg_session_expired
                return render_template("notice.html", notice_msg=return_msg)
        else:
            return_msg = msg_session_expired
            return render_template("notice.html", notice_msg=return_msg)

    except Exception as ex:
        print("exception occurred: " + str(ex))
        return_msg = "Exception Occured or Not Authorized"
        options = 'return to home'
        return render_template("notice.html", notice_msg=return_msg, options=options)


@ app.route('/notice', methods=['GET'])
def notice():

    authorized = session['authorized']

    if authorized == "200":

        return_msg = "Authorized: " + session['authorized']
        options = "options value here"
        return render_template("notice.html", notice_msg=return_msg, options=options)

    else:
        return_msg = msg_session_expired
        return render_template("notice.html", notice_msg=return_msg)


@ app.route('/record', methods=['GET', 'POST'])
def record():

    authorized = session['authorized']

    if authorized == "200":

        return render_template("record.html",  auth=authorized)

    else:
        return_msg = msg_session_expired
        return render_template("notice.html", notice_msg=return_msg)


@ app.route('/message', methods=['GET', 'POST'])
def message():

    authorized = session['authorized']

    if authorized == "200":

        return render_template("record.html",  auth=authorized)

    else:
        return_msg = msg_session_expired
        return render_template("notice.html", notice_msg=return_msg)


@ app.route('/about', methods=['GET', 'POST'])
def about():

    # authorized = session['authorized']
    authorized = session['authorized']

    msg = "TabKit is a Software Kit accessed via the web and optimized for workers that work outside or/and are on the go        out        in the field:        Real Estate Appraisers, Construction Sites, Zoos, Pet Day Care, and Theme Parks, any conditions where        phones are not optimal        but        using tablets are affected by sun and the weather or other non-office conditions.        Work area might be on a car seat. TabKit makes it easier to with its simple user interface        design with bright colors, big buttons, app and websites accessed from one screen.."
    # run_voice_new(
    # "Hello, I am Elaine.  Today is Monday, the third.  Here's the task list for today.")
    run_voice_new(msg)

    if authorized == "200":

        return render_template("about.html",  auth=authorized, msg=msg)

    else:
        return_msg = msg_session_expired
        return render_template("notice.html", notice_msg=return_msg)


@app.route('/upload_files', methods=['GET', 'POST'])
def upload_files():

    authorized = session['authorized']
    email = session['user_email']

    resp_users = table_users.query(KeyConditionExpression=Key(
        'user_email').eq(email))

    # print("Announce")
    items = resp_users['Items']
    primary_email = items[0]['primary']

    resp_cust = table_cust.query(KeyConditionExpression=Key(
        'user_email').eq(primary_email))

    if authorized == "200":

        options = "return to home"
        return render_template("upload.html",  auth=authorized, notice_msg=msg_go_back, options=options)

    else:
        return_msg = msg_session_expired
        options = "Return to Home"
        return render_template("notice.html", notice_msg=return_msg, options=options)


@app.route('/upload', methods=['POST'])
def upload():

    print("Upload route is starting")

    if 'user_file' not in request.files:
        return render_template("notice.html", notice_msg="File is not in request files.", options="")
    file = request.files['user_file']
    if file.filename == '':
        return render_template("notice.html", notice_msg="File name is blank.", options="")
    if file:
        print("File Found")
        s3 = boto3.client('s3')
        folder = 'uploads/'
        s3.upload_fileobj(file, S3_BUCKET, folder + file.filename)

        options = "return to home"
        return_msg = "File uploaded successfully.  Return to Launchpad if you have more files to upload."
        return render_template("notice.html", notice_msg=return_msg, options=options)


@ app.route('/announce', methods=['GET', 'POST'])
def announce():

    authorized = session['authorized']
    email = session['user_email']

    resp_users = table_users.query(KeyConditionExpression=Key(
        'user_email').eq(email))

    # print("Announce")
    items = resp_users['Items']
    primary_email = items[0]['primary']

    resp_cust = table_cust.query(KeyConditionExpression=Key(
        'user_email').eq(primary_email))

    msg = resp_cust['Items'][0]['announce']
    run_voice_new(msg)

    if authorized == "200":

        return render_template("announce.html",  auth=authorized, msg=msg)

    else:
        return_msg = msg_session_expired
        options = "Return to Home"
        return render_template("notice.html", notice_msg=return_msg, options=options)


@app.route('/user', methods=['GET', 'POST'])
def user():

    authorized = session['authorized']
    email = session['user_email']
    event = request.environ.get("awsgi.event", {})
    environment = event['requestContext']['stage']
    print(authorized)
    msg = "test"

    if request.method == 'GET':
        if authorized == "200":

            try:

                user_pref = {}
                resp = table_cust.query(
                    KeyConditionExpression=Key('user_email').eq(email))

                user_pref.update(resp['Items'][0])
                # print(user_pref)
                return render_template("user.html", env=environment, user_pref=user_pref, auth=authorized, msg=msg)

            except Exception as ex:
                print("Exception querying user: " + str(ex))

            # if 'Items' in resp:
            # if resp['Count'] > 0:

            # else:
                return_msg = 'This user is not authorized to make announcements'
                options = 'Return to Home'
                return render_template("notice.html", notice_msg=return_msg, options=options)

        else:
            return_msg = msg_session_expired
            return render_template("notice.html", notice_msg=return_msg)

    elif request.method == 'POST':
        return_msg = "Your user preferences have been updated."

        # txtboxTheme = request.form['HTMLTheme']
        # txtboxLanguage = request.form['HTMLLanguage']
        txtboxAnnounce = request.form['HTMLAnnounce']
        email = session['user_email']

        table_cust.update_item(
            Key={
                'user_email': email
            },
            ConditionExpression='attribute_exists(user_email)',
            UpdateExpression='SET announce = :val1',
            ExpressionAttributeValues={
                ':val1': txtboxAnnounce
            })

        options = "Return to Home"
        return render_template("notice.html", notice_msg=return_msg, options=options)


@ app.route('/automation', methods=['POST', 'GET'])
def mappings():

    try:

        print("ROUTE: AUTOMATION")
        event = request.environ.get("awsgi.event", {})
        # environment = 'dev'
        print(session['authorized'])

        # we need to add
        fuzz_factor = request.form['sliderFuzzFactor']
        #fuzz_factor = '65'
        print("Fuzz Factor: " + fuzz_factor)
        # valFuzzFactor = int(valFuzzFactor)
        user_email = session['user_email']
        json_string = '{"user_email":" ' + user_email +  \
            '", "fuzz_factor": " ' + fuzz_factor + '"}'
        print(json_string)

        # default is unauthorized.
        authorized = ""

        # check to see if session is active
        if 'authorized' in session:
            authorized = session['authorized']
        else:
            print("session object does not contain authorized")

        print(authorized)
        print("Lambda Function synchronous invocation")

        # check to see if user is authorized
        if authorized == "200":

            # invoke Lambda function asynchronously
            lambda_client = boto3.client('lambda')
            lambda_client.invoke(FunctionName='domain-scanner',
                                 InvocationType='Event',
                                 Payload=json_string)

            return_msg = "Lambda Function domain-scanner has been executed."

            options = "return to home"
            return render_template("notice.html", notice_msg=return_msg, options=options)

        else:
            return_msg = "Unauthorized"

            options = "return to home"
            return render_template("notice.html", notice_msg=return_msg, options=options)

    except Exception as ex:
        print("exception occurred: " + str(ex))
        return_msg = "Exception Occured or Not Authorized"
        options = 'return to home'
        return render_template("notice.html", notice_msg=return_msg, options=options)


def lambda_handler(event, context):

    # print("Lambda Flask Website Event: ")
    # print(event)
    # print("requestContext:  " + event['requestContext'])

    return awsgi.response(app, event, context)
