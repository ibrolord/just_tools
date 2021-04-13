#!/usr/local/bin/python3.8
​
import boto3
from botocore.exceptions import ClientError
​
session = boto3.Session(profile_name="tgam-master")
org_client = session.client("organizations")
sts_client = session.client("sts")
​
regions = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ca-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-central-1",
    "eu-north-1",
]
​
accounts = []
# Get the list of accounts
try:
    response = org_client.list_accounts()
except ClientError as e:
    raise SystemExit(e)
# Check for NextToken if more results are available
NextToken = response.get("NextToken")
for account in response.get("Accounts"):
    accounts.append(account["Id"])
# While NextToken exists, get the next response
while NextToken:
    try:
        response = org_client.list_accounts(NextToken=NextToken)
    except ClientError as e:
        raise SystemExit(e)
    NextToken = response.get("NextToken")
    for account in response.get("Accounts"):
        accounts.append(account["Id"])
​
for acct in accounts:
    print("")
    for region in regions:
        assumed_role_object = sts_client.assume_role(
            RoleArn="arn:aws:iam::" + acct + ":role/OrganizationAccountAccessRole",
            RoleSessionName="AssumeRoleSession1",
        )
​
        credentials = assumed_role_object["Credentials"]
​
        gd_client = boto3.client(
            "guardduty",
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=region,
        )
​
        detectors = gd_client.list_detectors()
​
        detector = detectors["DetectorIds"]
        if not detector:
            print("creating detector")
            response = gd_client.create_detector(
                Enable=True, DataSources={"S3Logs": {"Enable": False}}
            )
            print(response)
​
        if detector:
            invite = gd_client.list_invitations()
            if invite["Invitations"]:
                print("accepting invite")
                accept = gd_client.accept_invitation(
                    DetectorId=detectors["DetectorIds"][0],
                    MasterId=invite["Invitations"][0]["AccountId"],
                    InvitationId=invite["Invitations"][0]["InvitationId"],
                )
                print(accept)
​
            master = gd_client.get_master_account(
                DetectorId=detectors["DetectorIds"][0]
            )
            masteracct = ""
            if "Master" in master:
                masteracct = master["Master"]["AccountId"]
​
            print(
                "detector for account: "
                + acct
                + " in region "
                + region
                + ": "
                + detectors["DetectorIds"][0]
                + " guardduty master: "
                + masteracct
            )