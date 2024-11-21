import pandas as pd
import datetime
from configs import SAMPLE_COUNT, SMTP_CONFIGS, IMAGE_ID, TOP_K
import smtplib
import markdown
from email.mime.text import MIMEText

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
    sps_cov = (
        data.groupby(["region", "instance"])["sps"].agg(["mean", "std"]).reset_index()
    )
    sps_cov = sps_cov.assign(sps_cov=sps_cov["std"] / sps_cov["mean"]).fillna(0)
    if_cov = (
        data.groupby(["region", "instance"])["if"].agg(["mean", "std"]).reset_index()
    )
    if_cov = if_cov.assign(if_cov=if_cov["std"] / if_cov["mean"]).fillna(0)

    score = if_cov.merge(sps_cov, on=["region", "instance"])
    score = score.assign(score=score["sps_cov"] + score["if_cov"])
    score = score[["region", "instance", "score"]]
    score.to_csv(f"collect_sps_and_if/data/score/{today}.csv", index=False)
    return score.sort_values("score", ascending=False)[:TOP_K]


def notification(to_launch: list[tuple[str, str, float]]):
    alert = []
    for region, insatnce, _ in to_launch:
        if region in IMAGE_ID and insatnce in IMAGE_ID[region]:
            continue
        alert.append((region, insatnce))

    body = []
    body.append("**Report**  ")
    body.append("Instances to be launched in tody:")
    body.append("")
    body.append("| Region | Instance | Score |")
    body.append("| ------ | -------- | ----- |")
    body.extend([f"| {x[0]} | {x[1]} | {x[2]} |" for x in to_launch])
    body.append("")
    body.append("Following instances can't find AMI:  ")
    body.extend([f"+ {x[1]} in {x[0]}  " for x in alert])
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
