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
