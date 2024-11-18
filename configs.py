from dataclasses import dataclass

# Top K instances that need to collect launch time
TOP_K = 3
# How many spots should be launched
INSTANCE_COUNT = 10

# Sample random instances and collect their SPS and IF
# This value shouldn't be too large, otherwise, you may violate
# [SPS Limitations](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html#sps-limitations)
SAMPLE_COUNT = 20

# Timeout if instances not ready after 6 minutes when collecting launch time
TIMEOUT = 60 * 6

# NOTES: AMI used - Amazon Linux 2023 AMI
IMAGE_ID = {
    "sa-east-1": {
        "t3.nano": "ami-0989c1b438266c944",
        "t3.medium": "ami-0989c1b438266c944",
        "m6gd.medium": "ami-0e7b8cab1a49f3d88",
    },
    "ap-northeast-3": {
        "t4g.medium": "ami-05435b8a6f3ad2dc6",
    },
    "eu-north-1": {
        "m7gd.medium": "ami-04f0be422f752077f",
    },
    "eu-central-1": {
        "m6idn.4xlarge": "ami-017095afb82994ac7",
    },
    "us-east-1": {
        "c7gd.medium": "ami-02801556a781a4499",
    },
    "us-east-2": {
        "c7gn.2xlarge": "ami-0a7c06753900acc19",
    },
    "ap-southeast-1": {
        "r6in.2xlarge": "ami-07c9c7aaab42cba5a",
    },
    "ap-northeast-1": {
        "m5dn.4xlarge": "ami-094dc5cf74289dfbc",
        "r5ad.2xlarge": "ami-094dc5cf74289dfbc",
    },
    "ap-northeast-2": {
        "m6gd.medium": "ami-02eb6e33da0d2c404",
        "t4g.nano": "ami-02eb6e33da0d2c404",
    },
    "ca-central-1": {
        "c6gd.medium": "ami-003dc9390a1b7e12d",
    },
    "eu-west-2": {
        "r5b.2xlarge": "ami-0b2ed2e3df8cf9080",
    },
    "eu-west-3": {
        "c6gn.medium": "ami-01c5300f289d64643",
    },
}


@dataclass
class SMTPConfigs:
    password: str
    recipients: list[str]
    host: str = "smtp.gmail.com"
    port: int = 587
    sender: str = "nicklin9907@gmail.com"
    subject: str = "SPS and IF daily report"


with open("crendential.txt") as file:
    password = file.read()
recipients = ["chenliaao@gmail.com", "nicklin9907@gmail.com"]
SMTP_CONFIGS = SMTPConfigs(password=password, recipients=recipients)
