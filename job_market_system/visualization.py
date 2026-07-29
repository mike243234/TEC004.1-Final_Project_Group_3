import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def plot_skill_demand(top_skills_df, output_dir):
    ensure_dir(output_dir)
    data = top_skills_df.head(15)
    plt.figure(figsize=(10, 6))
    plt.barh(data["skill"][::-1], data["demand"][::-1], color="#4f46e5")
    plt.title("Top kỹ năng được yêu cầu nhiều nhất", fontsize=14, pad=12)
    plt.xlabel("Số tin tuyển dụng", fontsize=11)
    plt.tight_layout()
    path = os.path.join(output_dir, "skill_demand.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_salary_box(jobs, output_dir):
    ensure_dir(output_dir)
    order = ["Entry", "Junior", "Middle", "Senior"]
    paid = jobs[jobs["salary_mid"] > 0]
    labels = [level for level in order if not paid[paid["level"] == level].empty]
    data = [paid[paid["level"] == level]["salary_mid"].tolist() for level in labels]
    plt.figure(figsize=(9, 6))
    plt.boxplot(data, tick_labels=labels)
    plt.title("Phân bố lương theo cấp bậc (triệu VNĐ)", fontsize=14, pad=12)
    plt.ylabel("Lương (triệu VNĐ)", fontsize=11)
    plt.tight_layout()
    path = os.path.join(output_dir, "salary_box.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_posting_trend(jobs, output_dir):
    ensure_dir(output_dir)
    data = jobs.copy()
    data["posted_date"] = pd.to_datetime(data["posted_date"], errors="coerce")
    data = data.dropna(subset=["posted_date"])
    if data.empty:
        return ""
    weekly = data.groupby(data["posted_date"].dt.to_period("W")).size()
    labels = [str(period) for period in weekly.index]
    plt.figure(figsize=(11, 6))
    plt.plot(labels, weekly.values, marker="o", color="#059669")
    plt.xticks(rotation=45, ha="right")
    plt.title("Số tin tuyển dụng theo tuần", fontsize=14, pad=12)
    plt.ylabel("Số tin", fontsize=11)
    plt.tight_layout()
    path = os.path.join(output_dir, "posting_trend.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_location(location_df, output_dir):
    ensure_dir(output_dir)
    plt.figure(figsize=(8, 8))
    plt.pie(location_df["total"], labels=location_df["location"], autopct="%1.1f%%", startangle=90, colors=["#4f46e5", "#059669", "#d97706", "#dc2626", "#0891b2", "#94a3b8"])
    plt.title("Phân bố việc làm theo địa điểm", fontsize=14, pad=12)
    plt.tight_layout()
    path = os.path.join(output_dir, "location.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path
