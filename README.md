# AWS Lambda function to run daily backups of Opengear Lighthouse


## Required Environment Variables
- servername=lighthouse.example.com
- bucket=oglh-backup-example-bucket
- snstopic=oglh-backup-notification-sns
- username=secrets/lighthouse/username
- password=secrets/lighthouse/password
### Assign Lighthouse login info to SSM Parameter Store SecureString keys, and set those keys as environment variables

## Configure lambda IAM role
- Attach `AWSLambdaVPCAccessExectuionRole`
- Create new inline policy
```JSON
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:DescribeParameters"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:us-west-1:111122223333:parameter/secrets/lighthouse/*"
        },
        {
            "Action": [
                "s3:DescribeJob",
                "s3:GetObject",
                "s3:ListJobs",
                "s3:PutObject",
                "s3:PutObjectTagging"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::oglh-backup-example-bucket"
        },
        {
            "Effect": "Allow",
            "Action": "sns:Publish",
            "Resource": "arn:aws:sns:us-west-1:111122223333:oglh-backup-alert-sns"
        }
    ]
}
```
- Attach new inline policy


## Configure S3 Bucket Policy
```JSON
{
    "Effect": "Allow",
    "Principal": {
    "AWS": "arn:aws:iam::111122223333:role/oglh-backup-lambda-role"
    },
    "Action": [
        "s3:DeleteObject",
        "s3:GetObject",
        "s3:PutObject"
    ],
    "Resource": "arn:aws:s3:::oglh-backup-example-bucket/*"
},
{ 
    "Effect": "Allow",
    "Principal": {
        "AWS": "arn:aws:iam::111122223333:role/oglh-backup-lambda-role"
    },
    "Action": "s3:ListBucket",
    "Resource": "arn:aws:s3:::oglh-backup-example-bucket"
}
```

## Configure SNS Access Policy
```JSON
{
  "Sid": "grant-65864586-publish",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::111122223333:role/oglh-backup-lambda-role"
  },
  "Action": "sns:Publish",
  "Resource": "arn:aws:sns:us-west-1:111122223333:oglh-backup-alert-sns"
}
```

### Assign your Lambda function to a subnet within your VPC. Ensure that your Lighthouse instance allows TCP/443 from your subnet CIDR.