# generate_stats.py
import os
import requests
import datetime

GITHUB_USER = "axrorback"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub Actions secrets orqali olinadi

GQL_URL = "https://api.github.com/graphql"

QUERY = """
query ($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_calendar():
    to_dt = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=23, minute=59, second=59, microsecond=0
    )
    from_dt = to_dt - datetime.timedelta(days=370)
    variables = {
        "login": GITHUB_USER,
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat()
    }
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    resp = requests.post(GQL_URL, json={"query": QUERY, "variables": variables}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def compute_streak(calendar):
    days = []
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            days.append({"date": day["date"], "count": day["contributionCount"]})
    days.sort(key=lambda x: x["date"])
    day_map = {datetime.date.fromisoformat(d["date"]): d["count"] for d in days}
    today = datetime.datetime.now(datetime.timezone.utc).date()
    streak = 0
    cur = today
    while day_map.get(cur, 0) > 0:
        streak += 1
        cur -= datetime.timedelta(days=1)
    return streak, calendar["totalContributions"]

def main():
    calendar = fetch_calendar()
    streak, total = compute_streak(calendar)
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    content = f"""### 📊 GitHub Stats
- **User:** {GITHUB_USER}
- **Total contributions:** {total}
- **Current streak:** {streak} days
- **Last update:** {today}
"""
    with open("STATS.md", "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
