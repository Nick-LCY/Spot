import boto3
import pandas as pd

data = pd.read_csv("ec2.csv")
data["family"] = data["name"].str.split(".").apply(lambda x: x[0])
data = data.loc[
    ~data["name"].isin(
        [
            "g2.2xlarge",
            "g3s.xlarge",
            "g3.4xlarge",
            "cc2.8xlarge",
            "cr1.8xlarge",
            "g2.8xlarge",
            "g3.8xlarge",
            "hpc6a.48xlarge",
            "hpc6id.32xlarge",
            "hpc7a.96xlarge",
            "hs1.8xlarge",
            "p4de.24xlarge",
            "p5e.48xlarge",
            "g3.16xlarge",
            "hpc7a.48xlarge",
            "hpc7a.24xlarge",
            "hpc7a.12xlarge",
        ]
    )
]
data = data.drop_duplicates("family")
client = boto3.client("ec2")

resp1 = client.describe_instance_types(InstanceTypes=data["name"][:50].tolist())
resp2 = client.describe_instance_types(InstanceTypes=data["name"][50:100].tolist())
resp3 = client.describe_instance_types(InstanceTypes=data["name"][100:].tolist())

resp = resp1["InstanceTypes"] + resp2["InstanceTypes"] + resp3["InstanceTypes"]
records = []
for item in resp:
    record = {
        "family": item["InstanceType"].split(".")[0],
        "arch": [
            x
            for x in item["ProcessorInfo"]["SupportedArchitectures"]
            if x in ["x86_64", "arm64"]
        ],
    }
    if len(record["arch"]) != 0:
        records.append(record)
records = pd.DataFrame(records)
records["arch"] = records["arch"].apply(lambda x: x[0])
records = {x: y for x, y in zip(records["family"], records["arch"])}

print(records)
