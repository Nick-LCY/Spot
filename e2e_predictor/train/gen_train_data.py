import pandas as pd

REPEATS = ["round"]
TESTCASE_COLS = [
    "throughput",
    "frontend_replicas",
    "profile_replicas",
    "reservation_replicas",
    "search_replicas",
]
end_to_end_data = pd.read_csv("data/collect_e2e/end_to_end_data.csv")
end_to_end_data = (
    end_to_end_data.groupby(TESTCASE_COLS + REPEATS)["trace_duration"]
    .quantile(0.95)
    .reset_index()
)
throughput_data = pd.read_csv("data/collect_e2e/throughput_data.csv")

data = (
    end_to_end_data.merge(throughput_data)
    .groupby(TESTCASE_COLS)[["trace_duration", "real_throughput"]]
    .mean()
    .reset_index()
)

data = pd.DataFrame(
    [
        {
            "input": [
                2,
                2,
                x["frontend_replicas"],
                x["search_replicas"],
                x["profile_replicas"],
                x["reservation_replicas"],
                x["throughput"],
            ],
            "p95": x["trace_duration"] / 1000,
        }
        for x in data.to_dict("index").values()
    ]
)
data.to_csv("e2e_predictor/train/train_data.csv", index=False)
