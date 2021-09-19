import requests
import os
import boto3
import io

def validate_response(response):
    """Validate an HTTP/200 OK response from the API"""
    if response.status_code == 200:
        return True
    else:
        send_alert(response)
        raise Exception('Validation failed')


def send_alert(response):
    """Send an alert to AWS SNS with the HTTP error code and reason"""
    # To do: Send notification to AWS SNS
    sns_topic = os.environ['snstopic'] # Full ARN of the SNS topic
    sns = boto3.client('sns')
    sns.publish(TopicArn=sns_topic, Subject='Lighthouse backup failed. Error code: ' + str(response.status_code) + ' ' + response.reason, Message='Backup failed. Error code: ' + str(response.status_code) + ' ' + response.reason)


def get_secret(parameter_name):
    """Get a parameter from SSM Parameter store and decrypt it"""
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )['Parameter']['Value']
    return parameter


def write_to_bucket(bucket_name, filename, backup_data):
    """Write a series of bytes to an S3 bucket as an object"""
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    file = io.BytesIO(backup_data.content)
    bucket_object = bucket.Object(filename)
    bucket_object.upload_fileobj(file)


def lambda_handler(event, context):
    # Set 'servername' 'username' and 'password' variables to the path of the SSM Parameter Store Keys
    login = {
        "username": get_secret(os.environ['username']),
        "password": get_secret(os.environ['password'])
    }
    url = "https://" + os.environ['servername'] + "/api/v3.7"
    bucket_name = os.environ['bucket'] # Bucket name only


    # Authenticate to Lighthouse and grab the API token
    headers = {"Content-Type": "application/json"}
    requests.packages.urllib3.disable_warnings()
    session = requests.request("POST", url + '/sessions', verify=False, headers=headers, json=login)
    if validate_response(session):
        token = session.json()['session']


    # Create the system config backup
    headers['Authorization'] = "Token " + token
    config_backup = requests.request("POST", url + '/system/config_backup', headers=headers, verify=False, json={})
    if validate_response(config_backup):
        download_url = url + "/system/config_backup?id=" + config_backup.json()['system_config_backup']['id']


    # Download the system config backup file
    headers['Content-Type'] = "application/octet-stream"
    backup_data = requests.request("GET", download_url, verify=False, headers=headers)
    if validate_response(backup_data):
        filename = 'lighthouse/' + backup_data.headers.get("Content-Disposition").split("filename=")[1]
    write_to_bucket(bucket_name, filename, backup_data)
