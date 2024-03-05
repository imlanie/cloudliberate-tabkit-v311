import boto3
from email import encoders
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import listdir
from os.path import join, isfile
import time


def send_plain_email(user_email):
    ses_client = boto3.client("ses", region_name="us-west-2")
    CHARSET = "UTF-8"

    user_email = user_email

    response = ses_client.send_email(
        Destination={
            "ToAddresses": [
                user_email
            ],
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": CHARSET,
                    "Data": "Reports were generated",
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "GFE Automation",
            },
        },
        Source="owner@cloudliberate.me",
    )
    # print(response)


# send_plain_email()

def send_email_with_attachment(user_email):
    msg = MIMEMultipart()
    msg["Subject"] = "GFE Automation files attached here...."
    msg["From"] = "owner@cloudliberate.me"
    msg["To"] = user_email

    # Set message body
    body = MIMEText("", "plain")
    msg.attach(body)

    filename = "outfile.txt"  # In same directory as script

    path = "/tmp"
    filefound = ""

    for file_in_dir in listdir(path):  # iterates over all the files in 'path'
        full_path = join(path, file_in_dir)  # joins the path with the filename
        if isfile(full_path) and full_path.find('dbe_') < 1:  # validate that it is a file
            with open(full_path, "rb") as f:  # open the file
                part = MIMEApplication(f.read())
                # print(full_path)
                filefound = full_path[5:]
                print("File found: " + filefound)
                part.add_header("Content-Disposition",
                                "attachment", filename=filefound)
        else:
            print("Files not found")
        msg.attach(part)
        # time.sleep(5)

    # Convert message to string and send
    ses_client = boto3.client("ses", region_name="us-west-2")
    response = ses_client.send_raw_email(
        Source="elainebirdsall@gmail.com",
        Destinations=[user_email],
        RawMessage={"Data": msg.as_string()}
    )
    print(response)


# send_email_with_attachment()
