import os
import boto3
import requests
import pandas as pd
from typing import Final
from configs import TOP_K, INSTANCE_COUNT
import datetime

# Crontab
# 00 * * * * cd ~/spot && python -m collect_sps_and_if
# 10 * * * * cd ~/spot && python -m collect_sps_and_if
# 20 * * * * cd ~/spot && python -m collect_sps_and_if
# 30 * * * * cd ~/spot && python -m collect_sps_and_if
# 40 * * * * cd ~/spot && python -m collect_sps_and_if
# 50 * * * * cd ~/spot && python -m collect_sps_and_if

yesterday = (datetime.datetime.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
score = pd.read_csv(f"collect_sps_and_if/data/score/{yesterday}.csv")
potential = pd.read_csv("collect_sps_and_if/data/potential.csv")

TARGETS: Final = [
    (x["region"], x["instance"])
    for _, x in score.sort_values("score")[:TOP_K].iterrows()
]
POTENTIALS: Final = [(x["region"], x["instance"]) for _, x in potential.iterrows()]

CLIENT: Final = boto3.client("ec2")
IF_URL: Final[str] = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"


def get_sps(instance_type: str, region: str) -> int:
    response = CLIENT.get_spot_placement_scores(
        TargetCapacity=INSTANCE_COUNT,
        InstanceTypes=[instance_type],
        TargetCapacityUnitType="units",
        RegionNames=[region],
    )
    return response["SpotPlacementScores"][0]["Score"]


def write(path: str, data: pd.DataFrame):
    if len(data) == 0:
        return
    if os.path.exists(path):
        data.to_csv(path, header=False, mode="a", index=False)
    else:
        data.to_csv(path, index=False)


def main():
    resp = requests.get(IF_URL)
    data = []
    for region_name, region_data in dict(resp.json()["spot_advisor"]).items():
        for instance_name, instance_data in dict(region_data["Linux"]).items():
            if (region_name, instance_name) in TARGETS + POTENTIALS:
                print(f"Collecting {region_name}, {instance_name}")
                if_score = instance_data["r"]
                try:
                    sps_score = get_sps(instance_name, region_name)
                    data.append(
                        {
                            "region": region_name,
                            "instance": instance_name,
                            "if": if_score,
                            "sps": sps_score,
                        }
                    )
                except:
                    continue
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    write(f"collect_sps_and_if/data/sps_and_if/{today}.csv", pd.DataFrame(data))


if __name__ == "__main__":
    main()
