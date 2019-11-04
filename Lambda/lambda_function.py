import json
import boto3
from botocore.exceptions import ClientError
import jwt.jwt.api_jwt as jwt
import os
import botocore.vendored.requests as requests

SENDER = "Lambda Test <rkmcd93@gmail.com>"
RECIPIENT = "rkmcd93@gmail.com"
AWS_REGION = "us-east-1"
SUBJECT = "Lambda Test"
BODY_HTML = """<html>
<head></head>
<body>
  <h1>Amazon SES Test (SDK for Python)</h1>
  <p>This email was sent with
    <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
    <a href='https://aws.amazon.com/sdk-for-python/'>
      AWS SDK for Python (Boto)</a>.</p>
      <form action="http://google.com">
        <input type="submit" value="Go to Google" />
    </form>
    <p>A really cool verification link would look like:{}
</body>
</html>
            """

# The character encoding for the email.
CHARSET = "UTF-8"

# Create a new SES resource and specify a region.
client = boto3.client('ses', region_name=AWS_REGION)


# Try to send the email.
def send_email(em):
    encoded_jwt = jwt.encode({'email': em, 'secret':os.environ['SECRET']}, os.environ['KEY'], algorithm='HS256').decode('utf-8')
    BODY_TEXT = ("Welcome to our sweet cloud app!\r\n" +
                 "Your verification link is " + os.environ['API_GATEWAY_ENDPOINT'] + '?token=' + encoded_jwt)
    try:
        print("em = ", em)
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    em
                ],
            },
            Message={
                'Body': {
                    # 'Html': {
                    #     'Charset': CHARSET,
                    #     'Data': BODY_HTML,
                    # },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def handle_sns_event(records):
    sns_event = records[0]['Sns']
    topic_arn = sns_event.get("TopicArn", None)
    topic_subject = sns_event.get("Subject", None)
    topic_msg = sns_event.get("Message", None)

    print("SNS Subject = ", topic_subject)
    if topic_msg:
        json_msg = None
        try:
            json_msg = json.loads(topic_msg)
            print("Message = ", json.dumps(json_msg, indent=2))
        except:
            print("Could not parse message.")

        em = json_msg["customers_email"]
        send_email(em)
    return respond(None, {"cool": "example"})

def handle_api_gw_event(event):
    try:
        params = event.get("queryStringParameters",None)
        encoded_jwt = params.get("token",None)
        decoded_jwt = jwt.decode(encoded_jwt, os.environ['KEY'], algorithms=['HS256'])
        secret = decoded_jwt.get('secret')
        email = decoded_jwt.get('email')
        if secret == os.environ['SECRET'] and email:
            userInfo = requests.get(os.environ['EB_ENDPOINT'] + "/api/user/" + email).json()
            print(userInfo)
            if userInfo['status'] == 'ACTIVE':
                return respondHtml('Looks like this user is already activated!')
            elif userInfo['status'] == 'SUSPENDED' or userInfo['status'] == 'DELETED':
                return respondHtml('Looks like this user has been suspended or deleted!')
            elif userInfo['status'] == 'PENDING':
                jsonBody = {'status':'ACTIVE'}
                requests.put(os.environ['EB_ENDPOINT']+"/api/user/"+email,json=jsonBody)
                return respondHtml('Thanks for verifying your email! Your account is now active!')
            else:
                return respondHtml('Looks like this user has an unknown status!')
        else:
            return respondHtml('There was a problem verifying your email.  Please ensure you clicked the correct link!')
    except Exception as e:
        # raise
        return respondHtml('There was a problem verifying your email.  Please ensure you clicked the correct link!')

def respondHtml(text):
    return {
        'statusCode': '200',
        # 'body': "<script>alert('" + text + "')</script>",
        'body': text,
        'headers': {
            'Content-Type': 'text/html',
        },
    }

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def lambda_handler(event, context):

    records = event.get("Records", None)
    method = event.get("httpMethod", None)

    if records is not None:
        print("I got an SNS event.")
        response = handle_sns_event(records)
    elif method is not None:
        print("I got an API GW proxy event.")
        response = handle_api_gw_event(event)
    else:
        print("Not sure what I got.")
        response = respond(None, {"cool": "example"})
    return response