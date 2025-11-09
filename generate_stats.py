import os
import requests
import datetime
import re

GITHUB_USER = "axrorback"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
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
    to_dt = datetime.datetime.now(datetime.timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0)
    from_dt = to_dt - datetime.timedelta(days=370)
    variables = {"login": GITHUB_USER, "from": from_dt.isoformat(), "to": to_dt.isoformat()}
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    resp = requests.post(GQL_URL, json={"query": QUERY, "variables": variables}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def compute_streak(calendar):
    days = []
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            days.append({"date": day["date"], "count": day["count"]})
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

    tz = datetime.timezone(datetime.timedelta(hours=5))
    now = datetime.datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d %H:%M:%S GMT+5")

    content = f"""### 🔥 GitHub Stats
- **User:** {GITHUB_USER}
- **Total contributions:** {total}
- **Current streak:** {streak} days
- **Last update:** {today_str}
"""

    # ===== README.md markerini yangilash =====
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            readme = f.read()

        new_readme = re.sub(
            r"<!-- AUTO-STATS:START -->.*<!-- AUTO-STATS:END -->",
            f"<!-- AUTO-STATS:START -->\n{content}\n<!-- AUTO-STATS:END -->",
            readme,
            flags=re.DOTALL
        )

        with open(readme_path, "w") as f:
            f.write(new_readme)

if __name__ == "__main__":
    main()
