import os
import boto3
import logging
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

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger("collect_sps_and_if")
logger.setLevel(logging.DEBUG)
file_name = datetime.datetime.today().strftime("%Y-%m-%d")
handler = logging.FileHandler(f"collect_sps_and_if/log/{file_name}.log")
formatter = logging.Formatter(
    "[%(levelname)s](%(asctime)s):%(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    current_time = datetime.datetime.now().strftime("%H:%M")
    data = []
    # Collect SPS
    for region_name, instance_name in TARGETS + POTENTIALS:
        logger.info(f"Collecting SPS of {instance_name} in {region_name}")
        try:
            sps_score = get_sps(instance_name, region_name)
            data.append(
                {
                    "region": region_name,
                    "instance": instance_name,
                    "sps": sps_score,
                    "if": -1,
                    "hours": current_time.split(":")[0],
                    "minutes": current_time.split(":")[1],
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to collect SPS of {instance_name} in {region_name}, "
                f"error due to: {e}",
                exc_info=True,
            )
            continue
    data = pd.DataFrame(data)
    # Collect IF
    try:
        resp = requests.get(IF_URL)
    except Exception as e:
        logger.error(
            f"Failed to collect IF, error due to: {e}",
            exc_info=True,
        )
        return
    for region_name, region_data in dict(resp.json()["spot_advisor"]).items():
        for instance_name, instance_data in dict(region_data["Linux"]).items():
            if (region_name, instance_name) in TARGETS + POTENTIALS:
                if_score = instance_data["r"]
                data.loc[
                    (data["region"] == region_name)
                    & (data["instance"] == instance_name),
                    "if",
                ] = if_score
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    write(f"collect_sps_and_if/data/sps_and_if/{today}.csv", pd.DataFrame(data))


if __name__ == "__main__":
    main()
