import boto3

data = {}
for region in [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ap-south-1",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-southeast-1",
    "ap-southeast-2",
    "ca-central-1",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-north-1",
    "sa-east-1",
]:
    data[region] = {
        "x86_64": "",
        "arm64": "",
    }
    client = boto3.client("ec2", region_name=region)
    response = client.describe_images(
        Filters=[
            {"Name": "name", "Values": ["al2023-ami-*"]},
            {"Name": "architecture", "Values": ["x86_64", "arm64"]},
            {"Name": "state", "Values": ["available"]},
            {"Name": "is-public", "Values": ["true"]},
        ]
    )
    x86_64_id = sorted(
        [x for x in response["Images"] if x["Architecture"] == "x86_64"],
        key=lambda x: x["CreationDate"],
        reverse=True,
    )[0]["ImageId"]
    arm64_id = sorted(
        [x for x in response["Images"] if x["Architecture"] == "arm64"],
        key=lambda x: x["CreationDate"],
        reverse=True,
    )[0]["ImageId"]

    data[region]["x86_64"] = x86_64_id
    data[region]["arm64"] = arm64_id

print(data)
