import boto3, logging, datetime, os
from typing import Final, Callable
from dataclasses import dataclass
from time import sleep, time
from threading import Thread
import pandas as pd
from configs import TOP_K, INSTANCE_COUNT, TIMEOUT, get_ami

# Crontab
# 00 * * * * cd ~/spot && python -m collect_launch_time
# 10 * * * * cd ~/spot && python -m collect_launch_time
# 20 * * * * cd ~/spot && python -m collect_launch_time
# 30 * * * * cd ~/spot && python -m collect_launch_time
# 40 * * * * cd ~/spot && python -m collect_launch_time
# 50 * * * * cd ~/spot && python -m collect_launch_time


@dataclass
class LaunchInfo:
    region: str
    instance: str
    instance_count: int


@dataclass
class Record(dict):
    region: str
    instance: str
    instance_count: int
    request_time: float
    current_time: float
    ready_instances: int
    hours: int
    minutes: int


DATA: Final[list[Record]] = []  # Used to store collected data

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger("collect_launch_time")
logger.setLevel(logging.DEBUG)


def record_writer(path: str):
    def write_record(record: Record):
        if os.path.exists(path):
            pd.DataFrame([record]).to_csv(path, header=False, mode="a", index=False)
        else:
            pd.DataFrame([record]).to_csv(path, index=False)

    return write_record


def launch_spot(client, image: str, launch_info: LaunchInfo):
    response = client.request_spot_instances(
        LaunchSpecification={
            "InstanceType": launch_info.instance,
            "ImageId": image,
        },
        InstanceCount=launch_info.instance_count,
    )
    logger.debug(
        f"Request {launch_info.instance_count} of {launch_info.instance} "
        f"in {launch_info.region}, response: {response}"
    )
    return [x["SpotInstanceRequestId"] for x in response["SpotInstanceRequests"]]


def get_instance_ids_of_requests(client, request_ids: list[str]) -> list[str]:
    response = client.describe_instances()
    instance_ids = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            if instance["SpotInstanceRequestId"] not in request_ids:
                continue
            instance_ids.append(instance["InstanceId"])
    return instance_ids


def count_ready_instances(client, instance_ids: list[str]) -> int:
    ready_counter = 0
    response = client.describe_instance_status(InstanceIds=instance_ids)
    for instance_status in response["InstanceStatuses"]:
        # Three steps check
        # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-system-instance-status-check.html
        if (
            "InstanceStatus" in instance_status
            and instance_status["InstanceStatus"]["Status"] != "ok"
        ):
            continue
        elif (
            "SystemStatus" in instance_status
            and instance_status["SystemStatus"]["Status"] != "ok"
        ):
            continue
        elif (
            "AttachedEbsStatus" in instance_status
            and instance_status["AttachedEbsStatus"]["Status"] != "ok"
        ):
            continue
        ready_counter += 1
    return ready_counter


def clear_resources(client, request_ids: list[str], instance_ids: list[str]):
    client.cancel_spot_instance_requests(SpotInstanceRequestIds=request_ids)
    if len(instance_ids) > 0:
        client.terminate_instances(InstanceIds=instance_ids)


def record_instance_available_time(
    client,
    launch_info: LaunchInfo,
    request_ids: list[str],
    request_time: int,
    write_record: Callable[[Record], None],
):
    ready_counter = 0
    prev_ready_counter = 0
    while ready_counter != launch_info.instance_count:
        sleep(3)

        instance_ids = get_instance_ids_of_requests(client, request_ids)
        ready_counter = count_ready_instances(client, instance_ids)
        # Record current time and number of ready instances
        now = int(time())
        
        if ready_counter != prev_ready_counter:
            prev_ready_counter = ready_counter
            record = Record(
                launch_info.region,
                launch_info.instance,
                launch_info.instance_count,
                request_time,
                now,
                ready_counter,
                datetime.datetime.fromtimestamp(request_time).hour,
                datetime.datetime.fromtimestamp(request_time).minute
            )
            write_record(record)

        if now - request_time > TIMEOUT:
            logger.warning(
                "Waiting for launching "
                f"{launch_info.instance_count} {launch_info.instance} "
                f"in {launch_info.region} timeout. Ready instances: {ready_counter}."
            )
            break

    try:
        clear_resources(client, request_ids, instance_ids)
    except:
        logger.warning(
            f"Termination of {launch_info.instance} in {launch_info.region} FAILED!"
        )


def main():
    file_name = datetime.datetime.now().strftime("%Y-%m-%d")
    threads: list[Thread] = []
    handler = logging.FileHandler(f"collect_launch_time/log/{file_name}.log")
    formatter = logging.Formatter(
        "[%(levelname)s](%(asctime)s):%(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    yesterday = (datetime.datetime.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
    score = pd.read_csv(f"collect_sps_and_if/data/score/{yesterday}.csv")
    score = score.sort_values("score", ascending=False)[:TOP_K]
    write_record = record_writer(f"collect_launch_time/data/{file_name}.csv")
    for _, (region, instance, _) in score.iterrows():
        logger.info(f"Try to launch {INSTANCE_COUNT} of {instance} in {region}")
        launch_info = LaunchInfo(region, instance, INSTANCE_COUNT)
        client = boto3.client("ec2", region_name=region)

        try:
            request_ids = launch_spot(client, get_ami(region, instance), launch_info)
        except Exception as e:
            logger.error(
                f"Failed to launch {INSTANCE_COUNT} of {instance} in {region}, "
                f"error due to: {e}",
                exc_info=True,
            )
            continue
        thread = Thread(
            target=record_instance_available_time,
            args=(client, launch_info, request_ids, int(time()), write_record),
        )

        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
