from dataclasses import dataclass
from instance_arch_and_ami_id import IMAGE_ID, FAMILY_ARCH

# Top K instances that need to collect launch time
LAUNCH_TOP_K = 3
# How many spots should be launched
INSTANCE_COUNT = 10

# Sample random instances and collect their SPS and IF
# This value shouldn't be too large, otherwise, you may violate
# [SPS Limitations](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html#sps-limitations)
SAMPLE_COUNT = 20
# Top K instances that need to select from yeseterday data
SPS_AND_IF_TOP_K = 10
# Notes, total number of instance that will collect SPS and IF = SAMPLE_COUNT + SPS_AND_IF_TOP_K

# Timeout if instances not ready after 6 minutes when collecting launch time
TIMEOUT = 60 * 6


@dataclass
class SMTPConfigs:
    password: str
    recipients: list[str]
    host: str = "smtp.gmail.com"
    port: int = 587
    sender: str = "nicklin9907@gmail.com"


with open("crendential.txt") as file:
    password = file.read()
recipients = ["chenliaao@gmail.com", "nicklin9907@gmail.com"]
SMTP_CONFIGS = SMTPConfigs(password=password, recipients=recipients)


def get_ami(region: str, instance: str) -> str:
    family, _ = instance.split(".")
    arch = FAMILY_ARCH[family]
    ami = IMAGE_ID[region][arch]
    return ami
