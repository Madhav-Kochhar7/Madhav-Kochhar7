#!/usr/bin/env python3
"""
today.py
Generates dark_mode.svg / light_mode.svg for the profile README —

Static fields (education, languages, tools, etc.) are hardcoded below.
Dynamic fields (uptime/age, GitHub stats) are computed each run.

Run locally:            python3 today.py
Run in GitHub Actions:  ACCESS_TOKEN env var supplies a PAT with 'repo' + 'read:user' scope
"""

import os
import datetime
import requests

# ---------------------------------------------------------------------------
# STATIC CONFIG — contains my info
# ---------------------------------------------------------------------------

USERNAME = "Madhav-Kochhar7"
PROMPT = "madhav@kochhar"

BIRTH_DATE = datetime.date(2006, 12, 7)

FIELDS = [
    ("OS", "Windows 11, Linux"),
    ("Uptime", None),  # filled in dynamically
    ("Host", "Chitkara University"),               # metaphor: where I'm "hosted"
    ("Kernel", "BE CSE 3.0 (3rd Semester)"),        # metaphor: core version
    ("IDE", "VS Code, nvim, vim, nano"),
    None,  # blank line
    ("Languages.Programming", "Python, Java, C, JavaScript"),
    ("Languages.Computer", "HTML, CSS, JSON"),
    ("Frameworks.Web", "React.js, Next.js, Node.js, FastAPI"),
    ("Frameworks.Web3", "Wagmi, Viem, ConnectKit"),
    ("DevOps & Tools", "Git, Docker, Docker Compose, Redis, Bash, Linux, Celery, MySQL, MongoDB, PostgreSQL"),
    None,
    ("Currently.Learning", "LLM Internals, Full-Stack Development"),
    None,
    ("Achievements", "Best First Year Hack Winner - Eclipse 6.0"),
]

CONTACT = [
    ("Email", "kochhar.madhavv@gmail.com"),
    ("LinkedIn", "madhav--kochhar"),
]

# ---------------------------------------------------------------------------
# DYNAMIC: uptime / age
# ---------------------------------------------------------------------------

def calculate_uptime(birth_date: datetime.date) -> str:
    today = datetime.date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day

    if days < 0:
        months -= 1
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month != 1 else today.year - 1
        days_in_prev_month = (datetime.date(prev_year, prev_month % 12 + 1, 1) - datetime.timedelta(days=1)).day
        days += days_in_prev_month
    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


# ---------------------------------------------------------------------------
# DYNAMIC: GitHub stats (repos, stars, followers, commits, lines of code)
# ---------------------------------------------------------------------------

API = "https://api.github.com"


def gh_headers():
    token = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def safe_get(url, params=None):
    try:
        r = requests.get(url, headers=gh_headers(), params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    return None


def fetch_basic_stats(username: str) -> dict:
    """Repos, followers, stars — cheap REST calls, no cloning required."""
    stats = {"repos": 0, "followers": 0, "stars": 0}

    user = safe_get(f"{API}/users/{username}")
    if user:
        stats["repos"] = user.get("public_repos", 0)
        stats["followers"] = user.get("followers", 0)

    page = 1
    stars = 0
    while True:
        repos = safe_get(f"{API}/users/{username}/repos", params={"per_page": 100, "page": page})
        if not repos:
            break
        stars += sum(r.get("stargazers_count", 0) for r in repos)
        if len(repos) < 100:
            break
        page += 1
    stats["stars"] = stars
    return stats


def fetch_commit_total(username: str) -> int:
    """
    Approximate total commit count via the Search API (author:USERNAME).
    Requires an authenticated token for reasonable rate limits.
    """
    result = safe_get(f"{API}/search/commits", params={"q": f"author:{username}"})
    if result and "total_count" in result:
        return result["total_count"]
    return 0


def fetch_lines_of_code(username: str, cache_dir="cache"):
    """
    Placeholder for the full clone-and-diff LOC calculation. Cloning + `git log
    --numstat` across every repo is expensive, so this is intentionally left as
    a stub that reads/writes a cache file. Wire in the full clone loop here if
    you want exact LOC tracking; until then it returns cached values (0 on
    first run) so the workflow never fails.
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "loc_cache.txt")
    added, removed = 0, 0
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            line = f.read().strip()
            if line:
                parts = line.split(",")
                if len(parts) == 2:
                    added, removed = int(parts[0]), int(parts[1])
    else:
        with open(cache_file, "w") as f:
            f.write(f"{added},{removed}")
    return added, removed, added - removed


# ---------------------------------------------------------------------------
# SVG RENDERING — CLI / terminal style, CSS-classed colors, no art
# ---------------------------------------------------------------------------

FONT_SIZE = 16
LINE_HEIGHT = 20
PAD_X = 24
PAD_TOP = 34
PAD_BOTTOM = 24
CHAR_W = FONT_SIZE * 0.6   # monospace advance-width estimate at this font size


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_rows(uptime: str, stats: dict, commits: int, loc):
    """Returns a list of row descriptors."""
    added, removed, net = loc
    rows = [("prompt", PROMPT)]

    for item in FIELDS:
        if item is None:
            rows.append(("blank",))
            continue
        label, value = item
        if label == "Uptime":
            value = uptime
        rows.append(("field", label, value))

    rows.append(("blank",))
    rows.append(("section", "Contact"))
    for label, value in CONTACT:
        rows.append(("field", label, value))

    rows.append(("blank",))
    rows.append(("section", "GitHub Stats"))
    rows.append(("statline", [("Repos", f"{stats['repos']:,}"), ("Stars", f"{stats['stars']:,}")]))
    rows.append(("statline", [("Commits", f"{commits:,}"), ("Followers", f"{stats['followers']:,}")]))
    rows.append(("loc", net, added, removed))
    return rows


def field_parts(label: str, value, target_chars: int = None) -> tuple:
    """Returns (label_txt, dots, value_str).
    If target_chars is given, dots are stretched so the rendered line
    (". " + label + " " + dots + " " + value) exactly reaches target_chars —
    i.e. the label sits flush left and the value lands flush right.
    Falls back to a minimum of 3 dots when no target is given yet (sizing pass).
    """
    label_txt = f"{label}:"
    value_str = str(value)
    if target_chars is None:
        dots_len = 3
    else:
        fixed_len = 2 + len(label_txt) + 1 + 1 + len(value_str)  # ". " + label + " " + " " + value
        dots_len = max(target_chars - fixed_len, 3)
    dots = "." * dots_len
    return label_txt, dots, value_str


def row_char_len(row) -> int:
    if row[0] == "field":
        _, label, value = row
        label_txt, dots, value_str = field_parts(label, value)  # minimum-dots pass
        return 2 + len(label_txt) + 1 + len(dots) + 1 + len(value_str)
    if row[0] == "prompt":
        return len(row[1]) + 3
    if row[0] == "section":
        return len(row[1]) + 3
    if row[0] == "statline":
        text = "   |   ".join(f"{k}: {v}" for k, v in row[1])
        return len(text)
    if row[0] == "loc":
        _, net, added, removed = row
        return len(f". Lines of Code: {net:,} ( {added:,}++, {removed:,}-- )")
    return 0


def render_svg(mode: str, uptime: str, stats: dict, commits: int, loc) -> str:
    if mode == "dark":
        bg = "#161b22"
        base_text = "#c9d1d9"
        key_color = "#ffa657"
        cc_color = "#616e7f"
        value_color = "#a5d6ff"
        add_color = "#3fb950"
        del_color = "#f85149"
    else:
        bg = "#ffffff"
        base_text = "#1f2328"
        key_color = "#b1740f"
        cc_color = "#6e7781"
        value_color = "#0969da"
        add_color = "#1a7f37"
        del_color = "#cf222e"

    rows = build_rows(uptime, stats, commits, loc)
    max_chars = max(row_char_len(r) for r in rows)
    text_x = PAD_X
    width = int(text_x + max_chars * CHAR_W + PAD_X)
    target_chars = int((width - PAD_X - text_x) / CHAR_W)  # right edge, in characters

    dash_count_prompt = max(target_chars - len(PROMPT) - 1, 10)
    dash_count_section = max(target_chars - 20, 10)

    body = []
    y = PAD_TOP
    for row in rows:
        kind = row[0]
        if kind == "blank":
            y += LINE_HEIGHT
            continue
        if kind == "prompt":
            divider = "-" * dash_count_prompt
            body.append(
                f"<tspan x='{text_x}' y='{y}'>{esc(row[1])}</tspan>"
                f"<tspan class='cc'> {divider}</tspan>"
            )
        elif kind == "section":
            divider = "-" * dash_count_section
            body.append(
                f"<tspan x='{text_x}' y='{y}'>- {esc(row[1])} </tspan>"
                f"<tspan class='cc'>{divider}</tspan>"
            )
        elif kind == "field":
            _, label, value = row
            label_txt, dots, value_str = field_parts(label, value, target_chars)
            body.append(
                f"<tspan x='{text_x}' y='{y}' class='cc'>. </tspan>"
                f"<tspan class='key'>{esc(label_txt)}</tspan>"
                f"<tspan class='cc'> {esc(dots)} </tspan>"
                f"<tspan class='value'>{esc(value_str)}</tspan>"
            )
        elif kind == "statline":
            pairs = row[1]
            segs = [f"<tspan x='{text_x}' y='{y}' class='cc'>. </tspan>"]
            for i, (k, v) in enumerate(pairs):
                if i > 0:
                    segs.append("<tspan> | </tspan>")
                segs.append(f"<tspan class='key'>{esc(k)}</tspan><tspan class='cc'>: </tspan><tspan class='value'>{esc(v)}</tspan>")
            body.append("".join(segs))
        elif kind == "loc":
            _, net, added, removed = row
            body.append(
                f"<tspan x='{text_x}' y='{y}' class='cc'>. </tspan>"
                f"<tspan class='key'>Lines of Code</tspan>"
                f"<tspan class='cc'>: </tspan>"
                f"<tspan class='value'>{net:,}</tspan>"
                f"<tspan> ( </tspan>"
                f"<tspan class='addColor'>{added:,}++</tspan>"
                f"<tspan>, </tspan>"
                f"<tspan class='delColor'>{removed:,}--</tspan>"
                f"<tspan> )</tspan>"
            )
        y += LINE_HEIGHT

    height = y + PAD_BOTTOM

    svg = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns='http://www.w3.org/2000/svg' font-family='Consolas, Menlo, "Courier New", monospace' width='{width}px' height='{height}px' font-size='{FONT_SIZE}px'>
<style>
.key {{ fill: {key_color}; }}
.value {{ fill: {value_color}; }}
.cc {{ fill: {cc_color}; }}
.addColor {{ fill: {add_color}; }}
.delColor {{ fill: {del_color}; }}
text, tspan {{ white-space: pre; }}
</style>
<rect width='{width}px' height='{height}px' fill='{bg}' rx='12'/>
<text fill='{base_text}'>
{''.join(body)}
</text>
</svg>"""
    return svg


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    uptime = calculate_uptime(BIRTH_DATE)
    stats = fetch_basic_stats(USERNAME)
    commits = fetch_commit_total(USERNAME)
    loc = fetch_lines_of_code(USERNAME)

    dark_svg = render_svg("dark", uptime, stats, commits, loc)
    light_svg = render_svg("light", uptime, stats, commits, loc)

    with open("dark_mode.svg", "w") as f:
        f.write(dark_svg)
    with open("light_mode.svg", "w") as f:
        f.write(light_svg)

    print("Generated dark_mode.svg and light_mode.svg")
    print(f"Uptime: {uptime}")
    print(f"Stats: {stats}, commits={commits}, loc={loc}")


if __name__ == "__main__":
    main()
