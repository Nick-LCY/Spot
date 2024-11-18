# Collection SPS and IF
[Spot placement score](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html) and interference-free score[^spotlake] are two score that used to measure spot availability.

[Spotlake](https://spotlake.ddps.cloud/) has provided a comprehensive dataset, but the size of full dataset is too large and therefore they don't provide a real-time API to access these data. However, while collecting instance launch time, I figured out that I need a way to collect SPS and IF at real time, so, I turned to collect SPS and IF by myself.

**!NOTES!** All path (including script execution path) in this document based on the project root folder, which is the parent of `collect_sps_and_if`.

## Prerequisite
* Python version == 3.11.4
* Make sure you have checked dependencies in `requirements.txt`.
* You have created and configured your AWS Access Key ID/AWS Secret Access Key correctly so that `boto3` can create spot instances.
* Donwnload and extract [Spotlake](https://spotlake.ddps.cloud/) dataset at `spot_dataset/aws`.
* Create required folders:
  ```Bash
  mkdir -p collect_sps_and_if/data/score collect_sps_and_if/data/sps_and_if
  ```

## File Navigation


## SPS
I collect SPS with [`get_spot_placement_scores`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/get_spot_placement_scores.html) method. The major problem here is the anti-crawler mechanism of AWS. It only allow you to send ~50 types of SPS query request every 24 hours. And on each request, you can only get SPS of **ONE** instance among all regions. Fortunately, it seems that there is no limitation of how many requests sent of each type.

As this circumstance, I need to pick those most valuable instances and query their SPS. Typically, I will based on the SPS and IF I collected in yesterday to decide which instances to collect today. I compute the score of variance of SPS and IF (check [here](../collect_launch_time/README.md) to see how do I define score) and find the `TOP_K` (can be configured) largest instances. In addition, I randomly select `SAMPLE_COUNT` (also configurable) instances and collect their SPS and IF, this is like a exploration step, hope the random selection can find some valuable instances.

At the first day of collection, I don't have any data, so I use data provided by [Spotlake](https://spotlake.ddps.cloud/) to compute an initial score. It is saved in `data/init_score.csv`, to compute that, you need to run the following commands:
```Bash
python collect_sps_and_if/score_by_spotlake_data.py
```

## IF
By contrast, collecting IF is way more easy. AWS provide a site to query interruption frequency [here](https://aws.amazon.com/ec2/spot/instance-advisor/), and I found out their data is exactly comes from this link:
```
https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json
```
So I just collect simply request and collect them.

## Crontab
I collect SPS and IF in 10 minutes interval, and at the end of each day, I will compute the score based on today's data, and send an email to me for notification. The notification including those TOP_K instacnes and a warning if I don't set the AMI id of types of instace. Check the crontab jobs below:
```Crontab
# Collecting SPS and IF
00 * * * * cd ~/spot && python -m collect_sps_and_if
10 * * * * cd ~/spot && python -m collect_sps_and_if
20 * * * * cd ~/spot && python -m collect_sps_and_if
30 * * * * cd ~/spot && python -m collect_sps_and_if
40 * * * * cd ~/spot && python -m collect_sps_and_if
50 * * * * cd ~/spot && python -m collect_sps_and_if
# Compute score at 23:55
55 23 * * * cd ~/spot && python -m collect_sps_and_if.daily_score
```

**References**  
[^spotlake]: Lee, S., Hwang, J., & Lee, K. (2022, November). Spotlake: Diverse spot instance dataset archive service. In 2022 IEEE International Symposium on Workload Characterization (IISWC) (pp. 242-255). IEEE.