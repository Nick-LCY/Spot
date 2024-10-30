import pandas as pd
import os

# ===================================================================
# Compute CoV of SPS and IF of each instance at each region         |
# Instance/region with higher CoV of SPS/IF can train models better |
# ===================================================================

COV_PATH = "collect_launch_time/data/cov.csv"
if not os.path.exists(COV_PATH):
    data = []
    for root, dirs, files in os.walk("spot_dataset/aws/aws-2024-08"):
        for file in files:
            path = f"{root}/{file}"
            print(path)
            csv = pd.read_csv(path)[["InstanceType", "Region", "SPS", "IF"]]
            data.append(csv)
    data = pd.concat(data).rename(
        columns={"InstanceType": "instance", "Region": "region"}
    )
    data = (
        data.groupby(["instance", "region"])
        .apply(
            lambda x: pd.DataFrame(
                [
                    {
                        "sps_cov": x["SPS"].std() / x["SPS"].mean(),
                        "if_cov": x["IF"].std() / x["IF"].mean(),
                    }
                ]
            )
        )
        .reset_index()[["instance", "region", "sps_cov", "if_cov"]]
    )
    data.to_csv(COV_PATH, index=False)

data = pd.read_csv(COV_PATH)
data = data.assign(score=data["sps_cov"] * data["if_cov"])
data = data.sort_values("score", ascending=False)
data = data.loc[data["score"] != 0]
data = data.loc[~data["instance"].str.contains(r"(?:metal|large)")]
data[["instance", "region", "score"]].to_csv(
    "collect_launch_time/data/score.csv", index=False
)
