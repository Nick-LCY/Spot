import pandas as pd
import datetime
from configs import SAMPLE_COUNT, SMTP_CONFIGS, SPS_AND_IF_TOP_K, LAUNCH_TOP_K
import smtplib
import markdown
from email.mime.text import MIMEText
from functools import reduce

# Crontab
# 55 23 * * * cd ~/spot && python -m collect_sps_and_if.daily_score


def sample_potential():
    data = pd.read_csv("collect_sps_and_if/data/init_score.csv")
    pat = r".*\.(medium|[24]{0,1}xlarge)"
    data = data.loc[data["instance"].str.match(pat)]
    data.sample(SAMPLE_COUNT).to_csv(
        "collect_sps_and_if/data/potential.csv", index=False
    )


def score_today():
    today = datetime.datetime.today().strftime("%Y-%m-%d")

    data = pd.read_csv(f"collect_sps_and_if/data/sps_and_if/{today}.csv")

    def count_change(x: pd.DataFrame):
        changes = 0

        def reduce_func(prev, current):
            nonlocal changes
            if current != prev:
                changes += 1
            return current

        sps_changes = reduce(reduce_func, x["sps"].tolist(), -1)
        if_changes = reduce(reduce_func, x["if"].tolist(), -1)
        return pd.DataFrame([{"sps_changes": sps_changes, "if_changes": if_changes}])

    score = data.groupby(["region", "instance"]).apply(count_change).reset_index()
    score = score.assign(score=score["sps_changes"] / 3 + score["if_changes"] / 5)
    score = score[["region", "instance", "sps_changes", "if_changes", "score"]]
    score.to_csv(f"collect_sps_and_if/data/score/{today}.csv", index=False)
    return score.sort_values("score", ascending=False)[:SPS_AND_IF_TOP_K]


def notification(to_launch: list[tuple[str, str, float, float, float]]):
    body = []
    body.append("**Report**  ")
    body.append(
        f"Instances to be collected in tody, top {LAUNCH_TOP_K} will be launched:"
    )
    body.append("")
    body.append("| Region | Instance | SPS Chagnes | IF Changes | Score |")
    body.append("| :----: | :------: | :---------: | :--------: | :---: |")
    body.extend([f"| {x[0]} | {x[1]} | {x[2]} | {x[3]} | {x[4]} |" for x in to_launch])
    body.append("")
    body = markdown.markdown("\n".join(body), extensions=["tables"])
    content = MIMEText(body, "html")
    content["Subject"] = "SPS and IF daily report"
    content["From"] = SMTP_CONFIGS.sender
    content["To"] = ", ".join(SMTP_CONFIGS.recipients)
    content["Content-Type"] = 'text/html; charset="UTF-8"'

    with smtplib.SMTP(SMTP_CONFIGS.host, SMTP_CONFIGS.port) as smtp:
        smtp.ehlo("Gmail")
        smtp.starttls()
        smtp.login(SMTP_CONFIGS.sender, SMTP_CONFIGS.password)
        smtp.sendmail(SMTP_CONFIGS.sender, SMTP_CONFIGS.recipients, content.as_string())


if __name__ == "__main__":
    sample_potential()
    top_records = [
        tuple(dict(x).values()) for x in score_today().to_dict("index").values()
    ]
    notification(top_records)
