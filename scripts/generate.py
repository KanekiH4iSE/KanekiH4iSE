#!/usr/bin/env python3
"""Regenerates the animated profile cards in assets/ from live data.
Runs in GitHub Actions on a schedule; stdlib only."""
import datetime as dt, html, json, os, re, time, urllib.request

USER = "KanekiH4iSE"
SITES = [
    ("Магнат", "https://monopoly-oeep.onrender.com"),
    ("AniCase", "https://anicase-1.vercel.app"),
    ("SafePause", "https://safepause-eine-pause-bevor-das-geld.vercel.app"),
]
FONT = "'JetBrains Mono','Fira Code',Consolas,'SFMono-Regular',Menlo,monospace"
ACC, DIM, BG1, BG2 = "#e5243b", "#a39a9b", "#1a0b0d", "#0b0809"
OK, BAD = "#f4f1f1", "#f59e0b"
LANG_COLORS = ["#e5243b", "#f4f1f1", "#9b1c2c", "#8a8a8f", "#ff7a85", "#4a4a4f"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def get(url, timeout=30, api=False):
    req = urllib.request.Request(url, headers={"User-Agent": "kaneke-profile-cards"})
    tok = os.environ.get("GITHUB_TOKEN")
    if api and tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def api(path):
    try:
        return json.loads(get("https://api.github.com" + path, api=True)[1])
    except Exception as e:
        print("api failed", path, e)
        return None


def esc(s):
    return html.escape(str(s), quote=True)


# ---------------- data ----------------
def contributions():
    _, raw = get(f"https://github.com/users/{USER}/contributions")
    page = raw.decode("utf-8", "replace")
    cells = re.findall(r'data-date="([\d-]+)" id="(contribution-day-component-\d+-\d+)" data-level="(\d)"', page)
    tips = dict(re.findall(r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)</tool-tip>', page))
    days = []
    for date, cid, lvl in cells:
        m = re.match(r"(\d+) contribution", tips.get(cid, ""))
        days.append((dt.date.fromisoformat(date), int(m.group(1)) if m else 0, int(lvl)))
    days.sort()
    return days


def streaks(days):
    best = cur = 0
    for _, c, _ in days:
        cur = cur + 1 if c > 0 else 0
        best = max(best, cur)
    now = 0
    for i, (_, c, _) in enumerate(reversed(days)):
        if c > 0:
            now += 1
        elif i == 0:
            continue  # today may still be empty
        else:
            break
    return now, best


def languages():
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner") or []
    total = {}
    for r in repos:
        if r.get("fork"):
            continue
        langs = api(f"/repos/{USER}/{r['name']}/languages") or {}
        for k, v in langs.items():
            total[k] = total.get(k, 0) + v
    return sorted(total.items(), key=lambda kv: -kv[1])


# ---------------- cards ----------------
K = ["X...X", "X..X.", "X.X..", "XX...", "X.X..", "X..X.", "X...X"]


def neofetch(user, days, langs):
    total = sum(c for _, c, _ in days)
    now, best = streaks(days)
    repos = user.get("public_repos", "—") if user else "—"
    fol = user.get("followers", "—") if user else "—"
    W, H = 1000, 300
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient>',
         f'<linearGradient id="cube" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff8f99"/><stop offset=".55" stop-color="{ACC}"/><stop offset="1" stop-color="#6b0f1a"/></linearGradient></defs>',
         f'<style>text{{font-family:{FONT};font-size:14px}}.k{{fill:{ACC};font-weight:700}}.v{{fill:#f4f1f1}}.d{{fill:{DIM}}}'
         '.q{animation:q 3.2s ease-in-out infinite}@keyframes q{0%,100%{opacity:1}50%{opacity:.35}}'
         '.in{animation:in .5s ease-out both}@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}</style>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="url(#bg)" stroke="{ACC}" stroke-opacity=".28"/>']
    s, g, x0, y0 = 22, 6, 46, 44
    for r, row in enumerate(K):
        for c, ch in enumerate(row):
            if ch == "X":
                delay = (r + c) * 0.12
                o.append(f'<rect class="q" style="animation-delay:{delay:.2f}s" x="{x0+c*(s+g)}" y="{y0+r*(s+g)}" width="{s}" height="{s}" rx="5" fill="url(#cube)"/>')
            else:
                o.append(f'<rect x="{x0+c*(s+g)}" y="{y0+r*(s+g)}" width="{s}" height="{s}" rx="5" fill="{ACC}" fill-opacity=".06"/>')
    for i, col in enumerate(LANG_COLORS):
        o.append(f'<rect x="{x0+i*24}" y="{y0+7*(s+g)+14}" width="18" height="8" rx="2" fill="{col}"/>')
    tx = 250
    rows = [("role", "Software Engineering student · UE Potsdam"),
            ("based", "Berlin · from Khujand, Tajikistan"),
            ("stack", "Python · FastAPI · Java · React · Neo4j"),
            ("repos", f"{repos} public · {fol} followers"),
            ("contribs", f"{total} in the last year"),
            ("streak", f"{now} day{'' if now == 1 else 's'} now · {best} best")]
    o.append(f'<text x="{tx}" y="58" class="in"><tspan class="k">kaneke</tspan><tspan class="d">@</tspan><tspan class="k">github</tspan></text>')
    o.append(f'<text x="{tx}" y="78" class="d">{"-"*15}</text>')
    for i, (k, v) in enumerate(rows):
        o.append(f'<text x="{tx}" y="{106+i*25}" class="in" style="animation-delay:{.15+i*.12:.2f}s"><tspan class="k">{k}</tspan><tspan x="{tx+100}" class="v">{esc(v)}</tspan></text>')
    bx, by, bw = tx, 262, W - tx - 40
    langs = langs[:5]
    tot = sum(v for _, v in langs) or 1
    cx = bx
    for i, (name, v) in enumerate(langs):
        w = max(4, bw * v / tot)
        o.append(f'<rect x="{cx:.1f}" y="{by-14}" width="{w:.1f}" height="8" fill="{LANG_COLORS[i]}"/>')
        cx += w
    if not langs:
        o.append(f'<rect x="{bx}" y="{by-14}" width="{bw}" height="8" rx="4" fill="{ACC}" fill-opacity=".25"/>')
    lx = bx
    for i, (name, v) in enumerate(langs):
        label = f"{name} {round(100*v/tot)}%"
        o.append(f'<circle cx="{lx+4}" cy="{by+10}" r="4" fill="{LANG_COLORS[i]}"/><text x="{lx+13}" y="{by+14}" class="d" style="font-size:12px">{esc(label)}</text>')
        lx += 22 + 7.6 * len(label)
    o.append("</svg>")
    return "\n".join(o)


def skyline(days):
    W, H = 1180, 300
    sx, bw, dx, dy = 19, 14, 6, 7
    ox, oy = 60, 246
    total = sum(c for _, c, _ in days)
    mx = max([c for _, c, _ in days] + [1])
    first = days[0][0]
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # Sunday-based weeks
    cells = {}
    for d, c, lvl in days:
        k = (d - start).days
        cells[(k // 7, k % 7)] = (d, c)
    weeks = max(w for w, _ in cells) + 1
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient></defs>',
         f'<style>text{{font-family:{FONT};font-size:12px;fill:{DIM}}}.h{{fill:{ACC};font-weight:700;font-size:13px}}'
         '.b{transform-box:fill-box;transform-origin:50% 100%;animation:g .9s cubic-bezier(.2,.8,.2,1) both}'
         '@keyframes g{from{transform:scaleY(0)}to{transform:scaleY(1)}}</style>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="url(#bg)" stroke="{ACC}" stroke-opacity=".28"/>',
         f'<text x="28" y="34">// contribution skyline</text>',
         f'<text x="{W-28}" y="34" text-anchor="end" class="h">{total} contributions in the last year</text>']
    peak = None
    for d in range(6, -1, -1):
        for w in range(weeks - 1, -1, -1):
            if (w, d) not in cells:
                continue
            day, c = cells[(w, d)]
            X, Y = ox + w * sx + d * dx, oy - d * dy
            if c == 0:
                o.append(f'<path d="M{X} {Y}h{bw}l{dx} {-dy}h{-bw}z" fill="{ACC}" fill-opacity=".07"/>')
                continue
            h = 8 + 100 * (c / mx) ** 0.75
            t = c / mx
            front = f"rgb({int(120+109*t)},{int(16+20*t)},{int(28+31*t)})"
            top = f"rgb({int(225+19*t)},{int(110+110*t)},{int(118+102*t)})"
            side = f"rgb({int(64+50*t)},8,{int(14+10*t)})"
            o.append(f'<g class="b" style="animation-delay:{w*0.018+d*0.03:.2f}s">'
                     f'<path d="M{X} {Y}v{-h:.1f}l{dx} {-dy}v{h:.1f}z" fill="{side}"/>'
                     f'<path d="M{X} {Y-h:.1f}h{bw}l{dx} {-dy}h{-bw}z" fill="{top}"/>'
                     f'<rect x="{X}" y="{Y-h:.1f}" width="{bw}" height="{h:.1f}" fill="{front}"/></g>')
            if c == mx and peak is None:
                peak = (X + bw / 2, Y - h, c)
    if peak:
        px, py, c = peak
        py = max(py, 96)
        o.append(f'<line x1="{px:.1f}" y1="{py-6:.1f}" x2="{px:.1f}" y2="{py-22:.1f}" stroke="{ACC}"/>'
                 f'<text x="{px:.1f}" y="{py-28:.1f}" text-anchor="middle" class="h">peak : {c}</text>')
    seen = set()
    for (w, d), (day, c) in sorted(cells.items()):
        if d == 0 and day.day <= 7 and day.month not in seen:
            seen.add(day.month)
            o.append(f'<text x="{ox + w*sx}" y="{oy+26}">{day.strftime("%b").lower()}</text>')
    o.append("</svg>")
    return "\n".join(o)


def status():
    rows = []
    for name, url in SITES:
        code, ms = None, None
        for attempt in range(2):  # first request wakes free-tier hosts
            try:
                t = time.time()
                code, _ = get(url, timeout=90)
                ms = int((time.time() - t) * 1000)
            except Exception as e:
                code = getattr(e, "code", None)
                ms = None
        rows.append((name, url, code, ms))
    up = sum(1 for r in rows if r[2] and 200 <= r[2] < 400)
    W, H = 1000, 60 + 44 * len(rows) + 20
    now = dt.datetime.now(dt.timezone.utc).strftime("%d %b %H:%M UTC")
    ok = up == len(rows)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient></defs>',
         f'<style>text{{font-family:{FONT};font-size:14px}}.d{{fill:{DIM};font-size:12px}}.n{{fill:#f4f1f1;font-weight:700}}.u{{fill:{DIM};font-size:13px}}'
         '.p{animation:p 1.8s ease-in-out infinite}@keyframes p{0%{r:5;opacity:.7}70%{r:11;opacity:0}100%{r:11;opacity:0}}'
         '.w{transform-box:fill-box;transform-origin:0 50%;animation:w 1.2s ease-out both}@keyframes w{from{transform:scaleX(0)}}</style>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="url(#bg)" stroke="{ACC}" stroke-opacity=".28"/>',
         f'<text x="28" y="34" class="d">// live status of what i shipped</text>',
         f'<text x="{W-28}" y="34" text-anchor="end" class="d">checked {now}</text>',
         f'<text x="28" y="56" style="fill:{OK if ok else BAD};font-weight:700">{"all systems operational" if ok else f"{up} of {len(rows)} up"}</text>']
    for i, (name, url, code, ms) in enumerate(rows):
        y = 92 + i * 44
        good = code and 200 <= code < 400
        col = OK if good else BAD
        host = url.split("//", 1)[1]
        frac = min(1, (ms or 0) / 1500)
        o.append(f'<circle cx="38" cy="{y-5}" r="5" fill="{col}"/><circle class="p" cx="38" cy="{y-5}" r="5" fill="none" stroke="{col}"/>')
        o.append(f'<text x="58" y="{y}" class="n">{esc(name)}</text><text x="200" y="{y}" class="u">{esc(host)}</text>')
        o.append(f'<rect x="680" y="{y-9}" width="140" height="6" rx="3" fill="{ACC}" fill-opacity=".1"/>'
                 f'<rect class="w" x="680" y="{y-9}" width="{max(6, 140*frac):.0f}" height="6" rx="3" fill="{col}"/>')
        label = f"{code} · {ms} ms" if good and ms is not None else ("down" if not code else f"{code}")
        o.append(f'<text x="{W-28}" y="{y}" text-anchor="end" style="fill:{col};font-size:13px">{label}</text>')
    o.append("</svg>")
    return "\n".join(o)


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg + "\n")
    print("wrote", name, len(svg))


if __name__ == "__main__":
    days = contributions()
    write("neofetch.svg", neofetch(api(f"/users/{USER}"), days, languages()))
    write("skyline.svg", skyline(days))
    if os.environ.get("SKIP_STATUS") != "1":
        write("status.svg", status())
