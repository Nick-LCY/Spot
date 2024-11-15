import pandas as pd
import datetime
from configs import SAMPLE_COUNT

# Crontab
# 01 00 * * * cd ~/spot && python -m collect_sps_and_if.daily_score

data = pd.read_csv("collect_sps_and_if/data/init_score.csv")
pat = r".*\.(medium|[24]{0,1}xlarge)"
data = data.loc[data["instance"].str.match(pat)]
data.sample(SAMPLE_COUNT).to_csv("collect_sps_and_if/data/potential.csv", index=False)

yesterday = (datetime.datetime.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")

data = pd.read_csv(f"collect_sps_and_if/data/sps_and_if/{yesterday}.csv")
sps_cov = data.groupby(["region", "instance"])["sps"].agg(["mean", "std"]).reset_index()
sps_cov = sps_cov.assign(sps_cov=sps_cov["std"] / sps_cov["mean"]).fillna(0)
if_cov = data.groupby(["region", "instance"])["if"].agg(["mean", "std"]).reset_index()
if_cov = if_cov.assign(if_cov=if_cov["std"] / if_cov["mean"]).fillna(0)

score = if_cov.merge(sps_cov, on=["region", "instance"])
score = score.assign(score=score["sps_cov"] + score["if_cov"])
score[["region", "instance", "score"]].to_csv(
    f"collect_sps_and_if/data/score/{yesterday}.csv", index=False
)
