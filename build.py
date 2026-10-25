#!/usr/bin/env python3
"""
Spark Lab site builder.

Reads every content/*.txt file and writes a complete static website into ./docs
(GitHub Pages can serve straight from the /docs folder).

Usage:  python3 build.py
No extra packages needed (Python 3.8+).
"""
import argparse, html, json, os, re, shutil, urllib.parse
from pathlib import Path

# ---------------------------------------------------------------- settings
SITE_NAME = "Spark Lab"
TAGLINE = "Hands-on science projects for curious kids"
# Set this to your live address (e.g. "https://yourname.github.io/spark-lab")
# to generate sitemap.xml with full links. Leave empty to skip the sitemap.
SITE_URL = "https://spsolutions.tech/spark-lab"
# If you use your own domain, put it here (e.g. "www.sparklab.com", no https://).
# The build then writes docs/CNAME so GitHub Pages keeps your domain after every rebuild.
CUSTOM_DOMAIN = ""

# ---- GoatCounter analytics (privacy-friendly, no cookies) ----
# Your GoatCounter site code: the "xxx" in https://xxx.goatcounter.com. Leave empty to turn off.
GOATCOUNTER_CODE = "spsolutions"

# ---- Google Search Console ----
# Paste only the content="..." value from the HTML-tag verification method.
GOOGLE_SITE_VERIFICATION = ""

# ---- Google AdSense ----
# Your publisher ID from AdSense, e.g. "ca-pub-1234567890123456". Leave empty for no ads.
ADSENSE_CLIENT = ""
# Ad unit slot IDs (AdSense > Ads > By ad unit > Display ads). Create one unit per
# spot so AdSense can report which spot earns most. Leave a spot empty to skip it.
ADSENSE_SLOTS = {
    "project_content": "",   # project page, after "What's going on?"   (best performer)
    "project_side":    "off",   # project page, right column under the video (desktop)
    "project_bottom":  "",   # project page, above "More ... projects"
    "home":            "",   # home page, between "Classics" and "Done in 15 minutes"
    "browse":          "",   # All projects page, below the results
}
# True = draw dashed "Ad space" boxes where ads will go, so you can preview the layout
# before AdSense approves you. Set back to False before publishing.
ADS_PREVIEW = False

# ---- Ad on/off switches ----
# Master switch: False turns every ad off (the AdSense script is removed too).
ADS_ENABLED = True
# Turn individual spots on (True) or off (False). A spot shows an ad only when it is
# True here AND has a slot ID in ADSENSE_SLOTS above (or ADS_PREVIEW is on).
ADS_SPOTS_ON = {
    "project_content": True,
    "project_side":    True,
    "project_bottom":  True,
    "home":            True,
    "browse":          True,
}
# Topics with no ads at all (use topic slugs, e.g. ["body", "biology"]).
ADS_OFF_TOPICS = []
# Individual projects with no ads (use the page name without .html,
# e.g. ["lemon-battery", "classic-baking-soda-volcano"]).
ADS_OFF_PROJECTS = []
# This site is made for children. Keeping this True asks Google to treat ads as
# child-directed (no interest-based ads), which COPPA requires for kids' sites.
ADS_CHILD_DIRECTED = True
# Shown on the privacy page so visitors can reach you.
CONTACT_EMAIL = "hello@spsolutions.tech"

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "docs"

CATEGORIES = [
    # slug, name, short blurb, fill color, accent color
    ("chemistry",   "Kitchen Chemistry",        "Fizz, foam, crystals and color changes using things from the kitchen.", "#C8F0D8", "#1F8F51"),
    ("physics",     "Forces & Motion",          "Launch, roll, balance and float your way through the laws of motion.",   "#FFD8B8", "#C9581A"),
    ("electricity", "Electricity & Magnets",    "Build circuits, make magnets and power a light with a lemon.",           "#FFF1A8", "#A87F00"),
    ("light",       "Light & Color",           "Rainbows, shadows, mirrors, lenses and things that glow.",               "#FFDDEE", "#C42D7C"),
    ("sound",       "Sound & Music",            "Make instruments, see vibrations and send sound down a string.",          "#E3DBFF", "#5B3FD6"),
    ("biology",     "Living Things",            "Microbes, minibeasts, animals and the secrets of DNA.",                   "#D7F5C8", "#3F8722"),
    ("plants",      "Plants & Seeds",           "Sprout seeds, grow roots and find out how plants drink and breathe.",     "#E8F6B4", "#6A8710"),
    ("body",        "Human Body",               "Lungs, heartbeat, senses and reflexes. You are the experiment.",          "#FFD6D6", "#C23535"),
    ("earth",       "Rocks & Earth",            "Fossils, volcanoes, earthquakes and the rock cycle.",                      "#F0DFC8", "#8A5D27"),
    ("weather",     "Weather & Climate",        "Clouds, tornadoes, rain gauges and a weather station of your own.",       "#CDEBFF", "#1A78C2"),
    ("space",       "Space & Astronomy",        "Moon phases, craters, planets and the night sky.",                         "#D6DBFF", "#3440B5"),
    ("engineering", "Build & Engineer",         "Towers, bridges, cars and machines. Design, test, improve.",               "#DFE5EC", "#45566B"),
]
CAT = {c[0]: dict(slug=c[0], name=c[1], blurb=c[2], fill=c[3], accent=c[4]) for c in CATEGORIES}

# Hand-drawn style line icons (64x64), ink stroke + accent fill.
ICONS = {
 "chemistry": '<path d="M25 8h14M28 8v17L15 50a5 5 0 0 0 4.5 7h25a5 5 0 0 0 4.5-7L36 25V8"/><path class="f" d="M20 42h24l5.4 9.3A3.5 3.5 0 0 1 46.4 56H17.6a3.5 3.5 0 0 1-3-4.7z"/><circle cx="29" cy="35" r="2.5"/><circle cx="35" cy="29" r="1.8"/>',
 "physics": '<path d="M6 54h52"/><path class="f" d="M8 54 50 26v28z"/><circle class="f2" cx="22" cy="38" r="7"/><path d="M8 24h8M4 31h9M10 17h6"/>',
 "electricity": '<path d="M32 6a17 17 0 0 0-10 30.8V44h20v-7.2A17 17 0 0 0 32 6z"/><path class="f" d="m34 13-8 14h7l-3 12 9-16h-7z"/><path d="M24 50h16M26 56h12"/>',
 "light": '<path class="f" d="M30 12 12 46h36z"/><path d="M2 34l14 1M48 30l14-8M48 34l14 0M48 38l14 8"/>',
 "sound": '<path class="f" d="M10 25h9l13-11v36L19 39h-9z"/><path d="M40 24a11 11 0 0 1 0 16M46 18a19 19 0 0 1 0 28M52 12a27 27 0 0 1 0 40"/>',
 "biology": '<ellipse class="f" cx="32" cy="32" rx="24" ry="19"/><circle class="f2" cx="35" cy="30" r="7"/><circle cx="18" cy="26" r="2"/><circle cx="21" cy="40" r="2"/><circle cx="46" cy="42" r="2"/><path d="M8 32H3M61 32h-5M32 13V8M32 56v-5"/>',
 "plants": '<path d="M32 58V28"/><path class="f" d="M32 34C32 20 20 14 8 14c0 13 10 20 24 20zM32 28c0-12 10-18 22-18 0 12-9 18-22 18z"/><path d="M18 58h28"/>',
 "body": '<path class="f" d="M32 54S8 40 8 23a12 12 0 0 1 24-4 12 12 0 0 1 24 4c0 17-24 31-24 31z"/><path d="M14 31h9l4-7 6 14 4-7h13"/>',
 "earth": '<path class="f" d="M4 54 24 20l8 10 6-8 22 32z"/><path d="M24 20l-3-8M27 18l4-7M22 19l-7-5"/><path d="M14 42h10M30 46h14"/>',
 "weather": '<path class="f" d="M18 40a10 10 0 0 1 1-20 14 14 0 0 1 27 3 9 9 0 0 1-1 17z"/><path d="M22 47l-3 8M32 47l-3 8M42 47l-3 8"/>',
 "space": '<circle class="f" cx="32" cy="32" r="14"/><path d="M8 40c-6 6 2 9 24 1s32-19 27-23c-2-2-7-1-13 1"/><path d="M52 8v8M48 12h8M12 10v6M9 13h6"/>',
 "engineering": '<path class="f" d="M28 6h8l1.5 7 5.5 2.3 6-4 5.7 5.7-4 6 2.3 5.5 7 1.5v8l-7 1.5-2.3 5.5 4 6-5.7 5.7-6-4-5.5 2.3L36 58h-8l-1.5-7-5.5-2.3-6 4-5.7-5.7 4-6-2.3-5.5L6 36v-8l7-1.5 2.3-5.5-4-6 5.7-5.7 6 4 5.5-2.3z"/><circle cx="32" cy="32" r="8"/>',
}

def icon(slug, size=48, cls="icon"):
    c = CAT[slug]
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true" '
            f'style="--f:{c["accent"]}">{ICONS[slug]}</svg>')

# ---------------------------------------------------------------- parsing
def slugify(t):
    t = t.lower().replace("&", "and")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t

def minutes(t):
    s = t.lower()
    if any(k in s for k in ["day", "week", "month", "overnight", "+"]):
        return 9999
    m = re.search(r"([\d.]+)(?:-[\d.]+)?\s*(hour|hr|min)", s)
    if not m:
        return 60
    n = float(m.group(1))
    return int(n * 60) if m.group(2).startswith("h") else int(n)

def time_bucket(mins):
    if mins <= 20: return "quick"
    if mins <= 60: return "hour"
    if mins < 9999: return "long"
    return "days"

def parse_file(path):
    cat = path.stem
    items = []
    cur = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("##") or not line.strip():
            continue
        if line.startswith("# "):
            cur = dict(title=line[2:].strip(), cat=cat, materials=[], steps=[], why="", tryit="", safety="",
                       emoji="🔬", age="5-12", diff="Easy", time="30 min", video="", image="")
            items.append(cur)
            continue
        if cur is None:
            continue
        if re.match(r"^[a-z]=", line):
            for k, v in re.findall(r"(\b[a-z])=(.*?)(?=\s+[a-z]=|$)", line):
                key = dict(e="emoji", a="age", d="diff", t="time", v="video", i="image").get(k)
                if key: cur[key] = v.strip()
        elif line.startswith("m:"):
            cur["materials"] = [m.strip() for m in line[2:].split(";") if m.strip()]
        elif line.startswith("- "):
            cur["steps"].append(line[2:].strip())
        elif line.startswith("w:"):
            cur["why"] = line[2:].strip()
        elif line.startswith("x:"):
            cur["tryit"] = line[2:].strip()
        elif line.startswith("s:"):
            cur["safety"] = line[2:].strip()
    return items

def load():
    projects, seen = [], set()
    for slug in CAT:
        f = CONTENT / f"{slug}.txt"
        if not f.exists():
            continue
        for p in parse_file(f):
            s = slugify(p["title"])
            base, n = s, 2
            while s in seen:
                s = f"{base}-{n}"; n += 1
            seen.add(s)
            p["slug"] = s
            a = re.findall(r"\d+", p["age"]) or ["5", "12"]
            p["amin"], p["amax"] = int(a[0]), int(a[-1])
            p["mins"] = minutes(p["time"])
            p["bucket"] = time_bucket(p["mins"])
            projects.append(p)
    return projects

# ---------------------------------------------------------------- templates
e = lambda s: html.escape(str(s), quote=True)

NAV = [("index.html", "Home"), ("projects.html", "All projects"), ("topics.html", "Topics"),
       ("grown-ups.html", "Teachers & parents"), ("favorites.html", "My favorites")]

def head_extras(path):
    out = []
    if GOOGLE_SITE_VERIFICATION:
        out.append(f'<meta name="google-site-verification" content="{e(GOOGLE_SITE_VERIFICATION)}">')
    if SITE_URL and path is not None:
        url = SITE_URL.rstrip("/") + "/" + ("" if path == "index.html" else path)
        out.append(f'<link rel="canonical" href="{e(url)}">')
        out.append(f'<meta property="og:url" content="{e(url)}">')
    out.append('<meta property="og:type" content="website">')
    out.append(f'<meta property="og:site_name" content="{e(SITE_NAME)}">')
    if GOATCOUNTER_CODE:
        out.append(f'<script data-goatcounter="https://{e(GOATCOUNTER_CODE)}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>')
    if ADSENSE_CLIENT and ADS_ENABLED and not ADS_PREVIEW:
        out.append(f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={e(ADSENSE_CLIENT)}" crossorigin="anonymous"></script>')
    return "\n".join(out)

AD_LABELS = {
    "project_content": "After the science explanation",
    "project_side": "Right column, under the video",
    "project_bottom": "Above related projects",
    "home": "Between home page sections",
    "browse": "Below the project list",
}

def ad_unit(spot, extra_class="", project=None):
    if not ADS_ENABLED or not ADS_SPOTS_ON.get(spot, False):
        return ""
    if project and (project["cat"] in ADS_OFF_TOPICS or project["slug"] in ADS_OFF_PROJECTS):
        return ""
    slot = ADSENSE_SLOTS.get(spot, "")
    cls = f"ad-slot ad-{spot} no-print {extra_class}".strip()
    if ADS_PREVIEW:
        return (f'<div class="{cls} ad-preview" aria-hidden="true"><p class="small">Advertisement</p>'
                f'<div class="ad-box"><strong>Ad space</strong><span>{e(AD_LABELS.get(spot, spot))}</span>'
                f'<code>{e(spot)}</code></div></div>')
    if not (ADSENSE_CLIENT and slot):
        return ""
    age = ' data-tag-for-age-treatment="1"' if ADS_CHILD_DIRECTED else ""
    return (f'<div class="{cls}"><p class="small">Advertisement</p>'
            f'<ins class="adsbygoogle" style="display:block" data-ad-client="{e(ADSENSE_CLIENT)}" '
            f'data-ad-slot="{e(slot)}" data-ad-format="auto" data-full-width-responsive="true"{age}></ins>'
            f'<script>(function(s){{if(s.parentNode.offsetWidth>0)(adsbygoogle=window.adsbygoogle||[]).push({{}});}})(document.currentScript);</script></div>')

def page(title, body, base="", desc=TAGLINE, active="", body_class="", extra_head="", path=None):
    nav = "".join(
        f'<a href="{base}{href}"{" aria-current=\"page\"" if active == href else ""}>{e(label)}</a>'
        for href, label in NAV)
    full_title = f"{title} | {SITE_NAME}" if title != SITE_NAME else f"{SITE_NAME}: {TAGLINE}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<link rel="icon" href="{base}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Baloo+2:wght@600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{base}assets/css/style.css">
{head_extras(path)}
{extra_head}
</head>
<body class="{body_class}" data-base="{base}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="{base}index.html" aria-label="{SITE_NAME} home">
      <img src="{base}assets/img/logo.svg" alt="" width="40" height="40"><span>{SITE_NAME}</span>
    </a>
    <button class="menu-btn" aria-expanded="false" aria-controls="site-nav">Menu</button>
    <nav id="site-nav" class="site-nav" aria-label="Main">{nav}</nav>
    <form class="header-search" action="{base}projects.html" role="search">
      <label class="sr" for="hq">Search projects</label>
      <input id="hq" name="q" type="search" placeholder="Search 500+ projects" autocomplete="off">
    </form>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div>
      <p class="footer-logo"><img src="{base}assets/img/logo.svg" alt="" width="32" height="32"> {SITE_NAME}</p>
      <p>{e(TAGLINE)}. Always do experiments with a grown-up nearby, and read the safety notes first.</p>
    </div>
    <div class="footer-links">
      <a href="{base}projects.html">All projects</a>
      <a href="{base}topics.html">Topics</a>
      <a href="{base}grown-ups.html">Teachers &amp; parents</a>
      <a href="{base}grown-ups.html#safety">Safety rules</a>
      <a href="{base}about.html">About</a>
      <a href="{base}contact.html">Contact</a>
      <a href="{base}privacy.html">Privacy policy</a>
    </div>
  </div>
</footer>
<script src="{base}assets/js/projects-data.js"></script>
<script src="{base}assets/js/app.js"></script>
</body>
</html>
"""

def diff_dots(d):
    n = {"Easy": 1, "Medium": 2, "Hard": 3}.get(d, 1)
    dots = "".join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(3))
    return f'<span class="diff" title="{e(d)}"><span class="dots" aria-hidden="true">{dots}</span>{e(d)}</span>'

def art(p, base, big=False):
    c = CAT[p["cat"]]
    if p.get("image"):
        return (f'<div class="art has-photo" style="--fill:{c["fill"]}">'
                f'<img src="{base}{e(p["image"])}" alt="{e(p["title"])}" loading="lazy"></div>')
    return (f'<div class="art{" art-big" if big else ""}" style="--fill:{c["fill"]};--accent:{c["accent"]}">'
            f'{icon(p["cat"], 160 if big else 92, "art-icon")}'
            f'<span class="art-emoji" aria-hidden="true">{p["emoji"]}</span></div>')

def card(p, base):
    c = CAT[p["cat"]]
    return f"""<article class="card" style="--accent:{c['accent']};--fill:{c['fill']}">
  <a href="{base}projects/{p['slug']}.html" class="card-link">
    {art(p, base)}
    <div class="card-body">
      <p class="card-cat">{e(c['name'])}</p>
      <h3>{e(p['title'])}</h3>
      <p class="meta"><span>Ages {e(p['age'])}</span><span>{e(p['time'])}</span>{diff_dots(p['diff'])}</p>
    </div>
  </a>
</article>"""

def sticker(slug, base, count, tilt):
    c = CAT[slug]
    return f"""<a class="sticker" href="{base}projects.html?topic={slug}" style="--fill:{c['fill']};--accent:{c['accent']};--tilt:{tilt}deg">
  {icon(slug, 56)}
  <span class="sticker-name">{e(c['name'])}</span>
  <span class="sticker-count">{count} projects</span>
</a>"""

TILTS = [-3, 2, -1.5, 3, -2.5, 1.5, -1, 2.5, -2, 1, -3, 2]

# ---------------------------------------------------------------- pages
def build_home(projects, counts):
    by = {p["slug"]: p for p in projects}
    classics = ["classic-baking-soda-volcano", "lava-lamp-in-a-bottle", "oobleck-solid-or-liquid", "lemon-battery",
                "cloud-in-a-jar", "strawberry-dna-extraction", "string-telephone", "spaghetti-marshmallow-tower"]
    def spread(pool, n, skip=()):
        # one project per topic, round-robin, so every row mixes subjects
        groups = {s: [p for p in pool if p["cat"] == s and p["slug"] not in skip] for s in CAT}
        out = []
        while len(out) < n and any(groups.values()):
            for s in CAT:
                if groups[s] and len(out) < n:
                    out.append(groups[s].pop(0))
        return out
    quick = spread([p for p in projects if p["mins"] <= 15 and p["diff"] == "Easy"], 8, classics)
    little = spread([p for p in projects if p["amin"] <= 5], 8, classics + [q["slug"] for q in quick])
    stickers = "".join(sticker(s, "", counts[s], TILTS[i]) for i, s in enumerate(CAT))
    def row(items): return '<div class="grid">' + "".join(card(p, "") for p in items) + "</div>"
    total = len(projects)
    body = f"""
<section class="hero">
  <div class="wrap hero-inner">
    <div class="hero-copy">
      <h1>What do you want to find out today?</h1>
      <p class="lede">{total} science projects you can do at home or in class, each with a materials list, step-by-step guide, video and the science explained in plain words.</p>
      <form class="big-search" action="projects.html" role="search">
        <label class="sr" for="bq">Search projects</label>
        <input id="bq" name="q" type="search" placeholder="Try volcano, magnets, slime, rainbow…" autocomplete="off">
        <button type="submit">Search</button>
      </form>
      <p class="hero-actions"><a class="btn btn-ghost" href="#" data-random>Surprise me with a random project</a></p>
    </div>
    <div class="hero-stickers" aria-hidden="true">
      {''.join(f'<span class="hs" style="--fill:{CAT[s]["fill"]};--accent:{CAT[s]["accent"]};--tilt:{TILTS[i]*2}deg">{icon(s,64)}</span>' for i,s in enumerate(["chemistry","space","electricity","plants","light","weather"]))}
    </div>
  </div>
</section>

<section class="section wrap">
  <div class="section-head"><h2>Pick a topic</h2><a href="topics.html">About each topic</a></div>
  <div class="stickers">{stickers}</div>
</section>

<section class="section wrap">
  <div class="section-head"><h2>Classics to start with</h2><a href="projects.html">See all {total}</a></div>
  {row([by[s] for s in classics if s in by])}
</section>

<div class="wrap">{ad_unit('home')}</div>

<section class="section wrap">
  <div class="section-head"><h2>Done in 15 minutes</h2><a href="projects.html?time=quick">More quick projects</a></div>
  {row(quick)}
</section>

<section class="section wrap">
  <div class="section-head"><h2>For little scientists, ages 3 to 5</h2><a href="projects.html?age=4">More for young kids</a></div>
  {row(little)}
</section>

<section class="section wrap">
  <div class="grownups-band">
    <div>
      <h2>Teaching or parenting a young scientist?</h2>
      <p>Get the scientific method on one page, a science fair planner, safety rules to print and tips for running projects with a whole class.</p>
    </div>
    <a class="btn" href="grown-ups.html">Read the guide for grown-ups</a>
  </div>
</section>
"""
    return page(SITE_NAME, body, "", active="index.html", body_class="home", path="index.html")

def build_browse(projects):
    topic_opts = "".join(f'<label class="chip"><input type="checkbox" name="topic" value="{s}"><span style="--accent:{c["accent"]};--fill:{c["fill"]}">{e(c["name"])}</span></label>' for s, c in CAT.items())
    age_opts = "".join(f'<option value="{a}">{a} years old</option>' for a in range(3, 15))
    body = f"""
<section class="page-head wrap">
  <h1>All projects</h1>
  <p class="lede">Filter by topic, age, difficulty and time. Every project has a printable step-by-step guide.</p>
</section>
<div class="wrap browse">
  <aside class="filters" aria-label="Filters">
    <div class="filter-block">
      <label for="fq" class="filter-title">Search</label>
      <input id="fq" type="search" placeholder="Name or material, e.g. balloon" autocomplete="off">
    </div>
    <fieldset class="filter-block"><legend class="filter-title">Topic</legend><div class="chips">{topic_opts}</div></fieldset>
    <div class="filter-block">
      <label for="fage" class="filter-title">Child's age</label>
      <select id="fage"><option value="">Any age</option>{age_opts}</select>
    </div>
    <fieldset class="filter-block"><legend class="filter-title">Difficulty</legend>
      <div class="chips">
        <label class="chip"><input type="checkbox" name="diff" value="Easy"><span>Easy</span></label>
        <label class="chip"><input type="checkbox" name="diff" value="Medium"><span>Medium</span></label>
        <label class="chip"><input type="checkbox" name="diff" value="Hard"><span>Hard</span></label>
      </div>
    </fieldset>
    <fieldset class="filter-block"><legend class="filter-title">Time</legend>
      <div class="chips">
        <label class="chip"><input type="checkbox" name="time" value="quick"><span>20 min or less</span></label>
        <label class="chip"><input type="checkbox" name="time" value="hour"><span>Up to 1 hour</span></label>
        <label class="chip"><input type="checkbox" name="time" value="long"><span>A few hours</span></label>
        <label class="chip"><input type="checkbox" name="time" value="days"><span>Over several days</span></label>
      </div>
    </fieldset>
    <button type="button" class="btn btn-ghost btn-small" id="clear">Clear filters</button>
  </aside>
  <section class="results" aria-live="polite">
    <div class="results-bar">
      <p id="count">Loading projects…</p>
      <label class="sort">Sort by
        <select id="sort">
          <option value="topic">Topic</option>
          <option value="az">Name A to Z</option>
          <option value="easy">Easiest first</option>
          <option value="quick">Quickest first</option>
          <option value="young">Youngest age first</option>
        </select>
      </label>
    </div>
    <div class="grid" id="results"></div>
    <div class="empty" id="empty" hidden>
      <h2>No projects match those filters</h2>
      <p>Try removing a filter or searching for a simpler word, like "water" or "paper".</p>
      <button type="button" class="btn" data-clear>Clear all filters</button>
    </div>
    <button type="button" class="btn btn-ghost more" id="more" hidden>Show more projects</button>
    {ad_unit('browse', 'ad-browse')}
  </section>
</div>
"""
    return page("All projects", body, "", desc=f"Browse and filter {len(projects)} kids science projects by topic, age, difficulty and time.",
                active="projects.html", body_class="browse-page", path="projects.html")

def build_topics(projects, counts):
    blocks = []
    for i, (s, c) in enumerate(CAT.items()):
        sample = [p for p in projects if p["cat"] == s][:6]
        li = "".join(f'<li><a href="projects/{p["slug"]}.html">{p["emoji"]} {e(p["title"])}</a></li>' for p in sample)
        blocks.append(f"""<section class="topic" id="{s}" style="--fill:{c['fill']};--accent:{c['accent']}">
  <div class="topic-badge">{icon(s, 72)}</div>
  <div class="topic-text">
    <h2>{e(c['name'])}</h2>
    <p>{e(c['blurb'])}</p>
    <ul class="topic-list">{li}</ul>
    <a class="btn btn-small" href="projects.html?topic={s}">See all {counts[s]} {e(c['name'].lower())} projects</a>
  </div>
</section>""")
    body = f"""<section class="page-head wrap"><h1>Topics</h1>
<p class="lede">Twelve areas of science, from the kitchen to outer space. Each topic mixes quick wins for young kids with bigger challenges for older ones.</p></section>
<div class="wrap topics">{''.join(blocks)}</div>"""
    return page("Topics", body, "", active="topics.html", path="topics.html")

def build_project(p, projects, idx_in_cat, cat_list):
    c = CAT[p["cat"]]
    base = "../"
    mats = "".join(f'<li><label><input type="checkbox" data-key="m{i}"><span>{e(m)}</span></label></li>' for i, m in enumerate(p["materials"]))
    steps = "".join(f'<li><label><input type="checkbox" data-key="s{i}"><span>{e(s)}</span></label></li>' for i, s in enumerate(p["steps"]))
    q = urllib.parse.quote_plus(f'{p["title"]} science experiment for kids')
    yt = f"https://www.youtube.com/results?search_query={q}"
    if p.get("video"):
        video = f"""<div class="video-frame"><iframe src="https://www.youtube-nocookie.com/embed/{e(p['video'])}" title="Video: {e(p['title'])}" loading="lazy" allow="accelerometer; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>
<p class="small"><a href="{yt}" target="_blank" rel="noopener">More videos of this project on YouTube</a></p>"""
    else:
        video = f"""<a class="video-card" href="{yt}" target="_blank" rel="noopener">
  <span class="play" aria-hidden="true"><svg viewBox="0 0 24 24" width="28" height="28"><path d="M8 5v14l11-7z" fill="currentColor"/></svg></span>
  <span><strong>Watch it done on YouTube</strong><br><span class="small">Opens videos of “{e(p['title'])}” in a new tab. Grown-ups, preview videos before showing kids.</span></span>
</a>"""
    safety = f'<aside class="safety" role="note"><h2>Safety first</h2><p>{e(p["safety"])}</p></aside>' if p["safety"] else ""
    prev_p = cat_list[idx_in_cat - 1] if idx_in_cat > 0 else None
    next_p = cat_list[idx_in_cat + 1] if idx_in_cat < len(cat_list) - 1 else None
    related = [x for x in cat_list if x is not p]
    start = idx_in_cat % max(1, len(related))
    related = (related[start:] + related[:start])[:4]
    pn = '<nav class="prevnext" aria-label="More in this topic">'
    pn += f'<a class="prev" href="{prev_p["slug"]}.html"><span class="small">Previous</span>{e(prev_p["title"])}</a>' if prev_p else "<span></span>"
    pn += f'<a class="next" href="{next_p["slug"]}.html"><span class="small">Next</span>{e(next_p["title"])}</a>' if next_p else "<span></span>"
    pn += "</nav>"
    desc = f'{p["title"]}: a {p["diff"].lower()} science project for ages {p["age"]}. ' + (p["why"][:110] + "…" if len(p["why"]) > 110 else p["why"])
    jsonld = {
        "@context": "https://schema.org", "@type": "HowTo", "name": p["title"],
        "description": p["why"], "supply": [{"@type": "HowToSupply", "name": m} for m in p["materials"]],
        "step": [{"@type": "HowToStep", "text": s} for s in p["steps"]],
    }
    body = f"""
<article class="project" data-slug="{p['slug']}" style="--fill:{c['fill']};--accent:{c['accent']}">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{base}index.html">Home</a> / <a href="{base}projects.html?topic={p['cat']}">{e(c['name'])}</a></nav>
    <header class="project-head">
      <div class="project-title">
        <h1>{e(p['title'])}</h1>
        <dl class="facts">
          <div><dt>Ages</dt><dd>{e(p['age'])}</dd></div>
          <div><dt>Time</dt><dd>{e(p['time'])}</dd></div>
          <div><dt>Difficulty</dt><dd>{diff_dots(p['diff'])}</dd></div>
          <div><dt>Topic</dt><dd><a href="{base}projects.html?topic={p['cat']}">{e(c['name'])}</a></dd></div>
        </dl>
        <div class="project-actions">
          <button type="button" class="btn fav-btn" data-fav="{p['slug']}" aria-pressed="false">Save to favorites</button>
          <button type="button" class="btn btn-ghost" data-print>Print this guide</button>
        </div>
      </div>
      {art(p, base, big=True)}
    </header>

    <div class="project-body">
      <div class="col-main">
        {safety}
        <section class="steps-sec">
          <h2>Step by step</h2>
          <p class="small no-print">Tick each step as you go. Your progress is saved on this device.</p>
          <ol class="steps">{steps}</ol>
        </section>
        <section class="science">
          <h2>What's going on?</h2>
          <p>{e(p['why'])}</p>
        </section>
        {ad_unit('project_content', project=p)}
        {f'<section class="tryit"><h2>Try this next</h2><p>{e(p["tryit"])}</p></section>' if p['tryit'] else ''}
        <section class="journal no-screen">
          <h2>My lab notes</h2>
          <p>I predict that…</p><div class="lines"></div>
          <p>What happened…</p><div class="lines"></div>
        </section>
      </div>
      <aside class="col-side">
        <section class="materials">
          <h2>You will need</h2>
          <ul class="checklist">{mats}</ul>
        </section>
        <section class="video no-print">
          <h2>Video</h2>
          {video}
        </section>
        {ad_unit('project_side', 'ad-side', project=p)}
      </aside>
    </div>

    {pn}
    {ad_unit('project_bottom', project=p)}
    <section class="related no-print">
      <h2>More {e(c['name'].lower())} projects</h2>
      <div class="grid">{''.join(card(r, base) for r in related)}</div>
    </section>
  </div>
</article>
"""
    head = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
    return page(p["title"], body, base, desc=desc, body_class="project-page", extra_head=head, path=f"projects/{p['slug']}.html")

def build_static_page(name, title, active):
    body = (STATIC / name).read_text(encoding="utf-8")
    body = body.replace("{{CONTACT_EMAIL}}", e(CONTACT_EMAIL)).replace("{{SITE_NAME}}", e(SITE_NAME))
    body = body.replace("{{ADS_SECTION}}", ADS_PRIVACY if ADSENSE_CLIENT else "")
    body = body.replace("{{ANALYTICS_SECTION}}", ANALYTICS_PRIVACY if GOATCOUNTER_CODE else "")
    return page(title, body, "", active=active, path=name)

ANALYTICS_PRIVACY = """<section>
    <h2>Visitor statistics</h2>
    <p>We count visits with GoatCounter, a privacy-friendly analytics service. It doesn't use cookies and doesn't build profiles of visitors. It records things like which pages are viewed, the referring website, browser type, screen size and country, so we can see which projects are popular and improve the site.</p>
  </section>"""

ADS_PRIVACY = """<section>
    <h2>Advertising</h2>
    <p>This site shows ads served by Google AdSense to help cover its costs. Because the site is made for children, we ask Google to treat our pages as child-directed, which turns off interest-based (personalized) advertising and remarketing.</p>
    <p>Google and its partners may still use cookies or similar technology to serve and measure ads, limit how often you see an ad, and prevent fraud. You can learn more at <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">How Google uses information from sites that use its services</a>, and manage ad settings at <a href="https://adssettings.google.com" rel="noopener">Google Ad Settings</a>.</p>
  </section>"""

# ---------------------------------------------------------------- main
def parse_args():
    global ADS_ENABLED, ADS_PREVIEW
    spots = list(ADS_SPOTS_ON)
    ap = argparse.ArgumentParser(description="Build the Spark Lab website into ./docs")
    ap.add_argument("--no-ads", action="store_true", help="turn every ad off for this build")
    ap.add_argument("--preview", action="store_true", help="show dashed 'Ad space' boxes instead of real ads")
    ap.add_argument("--only", metavar="SPOTS", help="comma list: show ads ONLY in these spots, e.g. --only project_content,home")
    ap.add_argument("--disable", metavar="SPOTS", help="comma list: turn these spots off, e.g. --disable project_side,browse")
    ap.add_argument("--enable", metavar="SPOTS", help="comma list: turn these spots on")
    a = ap.parse_args()
    def lst(v):
        out = [x.strip() for x in (v or "").split(",") if x.strip()]
        bad = [x for x in out if x not in spots]
        if bad:
            ap.error(f"unknown spot(s): {', '.join(bad)}. Valid spots: {', '.join(spots)}")
        return out
    if a.no_ads: ADS_ENABLED = False
    if a.preview: ADS_PREVIEW = True
    if a.only is not None:
        keep = lst(a.only)
        for k in spots: ADS_SPOTS_ON[k] = k in keep
    for k in lst(a.disable): ADS_SPOTS_ON[k] = False
    for k in lst(a.enable): ADS_SPOTS_ON[k] = True

def ad_report():
    if not ADS_ENABLED:
        return "  Ads: OFF (master switch)"
    mode = "PREVIEW boxes" if ADS_PREVIEW else ("live" if ADSENSE_CLIENT else "no publisher ID yet, nothing shown")
    lines = [f"  Ads: {mode}"]
    for k, on in ADS_SPOTS_ON.items():
        state = "off" if not on else ("on" if (ADS_PREVIEW or ADSENSE_SLOTS.get(k)) else "on, but no slot ID")
        lines.append(f"    {k:<16} {state}")
    if ADS_OFF_TOPICS: lines.append(f"    no ads in topics: {', '.join(ADS_OFF_TOPICS)}")
    if ADS_OFF_PROJECTS: lines.append(f"    no ads on {len(ADS_OFF_PROJECTS)} project page(s)")
    return "\n".join(lines)

def main():
    parse_args()
    projects = load()
    counts = {s: sum(1 for p in projects if p["cat"] == s) for s in CAT}
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "projects").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    if (ROOT / "images").exists():
        shutil.copytree(ROOT / "images", OUT / "images")
    (OUT / ".nojekyll").write_text("")
    if CUSTOM_DOMAIN:
        (OUT / "CNAME").write_text(CUSTOM_DOMAIN.strip() + "\n")

    # data for search/filter
    data = [dict(s=p["slug"], t=p["title"], c=p["cat"], e=p["emoji"], a=p["age"], a0=p["amin"], a1=p["amax"],
                 d=p["diff"], tm=p["time"], m=p["mins"], b=p["bucket"], k=" ".join(p["materials"]).lower(),
                 i=p.get("image", "")) for p in projects]
    cats = {s: dict(n=c["name"], f=c["fill"], a=c["accent"], svg=ICONS[s]) for s, c in CAT.items()}
    (OUT / "assets/js/projects-data.js").write_text(
        "window.SPARK=" + json.dumps(dict(projects=data, cats=cats), ensure_ascii=False, separators=(",", ":")) + ";",
        encoding="utf-8")

    (OUT / "index.html").write_text(build_home(projects, counts), encoding="utf-8")
    (OUT / "projects.html").write_text(build_browse(projects), encoding="utf-8")
    (OUT / "topics.html").write_text(build_topics(projects, counts), encoding="utf-8")
    (OUT / "grown-ups.html").write_text(build_static_page("grown-ups.html", "For teachers and parents", "grown-ups.html"), encoding="utf-8")
    (OUT / "favorites.html").write_text(build_static_page("favorites.html", "My favorites", "favorites.html"), encoding="utf-8")
    (OUT / "about.html").write_text(build_static_page("about.html", "About", ""), encoding="utf-8")
    (OUT / "privacy.html").write_text(build_static_page("privacy.html", "Privacy policy", ""), encoding="utf-8")
    (OUT / "contact.html").write_text(build_static_page("contact.html", "Contact", ""), encoding="utf-8")
    if ADSENSE_CLIENT:
        pub = ADSENSE_CLIENT.replace("ca-", "")
        (OUT / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n")
    (OUT / "404.html").write_text(page("Page not found", (STATIC / "404.html").read_text(encoding="utf-8"), "" if SITE_URL == "" else SITE_URL.rstrip("/") + "/"), encoding="utf-8")

    for s in CAT:
        lst = [p for p in projects if p["cat"] == s]
        for i, p in enumerate(lst):
            (OUT / "projects" / f"{p['slug']}.html").write_text(build_project(p, projects, i, lst), encoding="utf-8")

    if SITE_URL:
        u = SITE_URL.rstrip("/")
        urls = ["", "projects.html", "topics.html", "grown-ups.html", "about.html", "privacy.html", "contact.html"] + [f"projects/{p['slug']}.html" for p in projects]
        (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(f"  <url><loc>{u}/{x}</loc></url>" for x in urls) + "\n</urlset>\n", encoding="utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {u}/sitemap.xml\n")

    print(f"Built {len(projects)} projects into {OUT}")
    for s in CAT:
        print(f"  {CAT[s]['name']:<24} {counts[s]}")
    print(ad_report())

if __name__ == "__main__":
    main()
