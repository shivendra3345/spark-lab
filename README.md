# Spark Lab — 504 science projects for kids

A ready-to-publish GitHub Pages website with 504 hands-on science projects in 12 topics.
Every project has a materials checklist, numbered steps, the science explained, a "try this next"
idea, safety notes where needed, a video link, and a print-friendly worksheet layout.

The finished website is already built in the **`docs/`** folder. You don't need to install anything
to publish it.

---

## Publish it on GitHub Pages (about 10 minutes)

1. Sign in at github.com and click **New repository**. Name it, for example, `spark-lab`. Make it **Public**.
2. On the new repository page, click **uploading an existing file**.
3. Unzip this package on your computer, then drag **everything inside the `spark-lab` folder**
   (including the `docs` folder) into the upload area. Click **Commit changes**.
   - GitHub's web uploader accepts up to 100 files per drop. If it complains, drag the folders in a
     few batches (for example `docs/projects` in two halves), or use GitHub Desktop, which has no limit.
4. Go to **Settings → Pages**.
5. Under **Build and deployment**, set **Source** to *Deploy from a branch*, **Branch** to `main`,
   and the folder to **`/docs`**. Click **Save**.
6. Wait 1–2 minutes and refresh. Your site's address appears at the top of the Pages settings,
   e.g. `https://yourname.github.io/spark-lab/`.

To preview on your own computer first, just double-click `docs/index.html`.

---

## What's in the box

```
spark-lab/
├── docs/              ← the finished website (this is what GitHub Pages serves)
├── content/           ← all 504 projects as easy-to-edit text files, one per topic
├── static/            ← text for the Teachers & parents, About, Favorites and 404 pages
├── assets/            ← styles, scripts, logo
├── images/            ← put your own project photos here (optional)
└── build.py           ← rebuilds docs/ after you edit anything
```

Site pages: Home, All projects (search + filters by topic, age, difficulty and time),
Topics, Teachers & parents (scientific method, safety rules, classroom tips, science fair planner),
My favorites (saved in the visitor's browser), About, and 504 project pages.

---

## Editing and adding projects

Each topic is one file in `content/` (for example `content/chemistry.txt`). A project looks like this:

```
# Lava Lamp in a Bottle
e=🫧 a=5-11 d=Easy t=20 min
m: clear plastic bottle; water; vegetable oil; food coloring; fizzy antacid tablet
- Fill the bottle about one quarter full with water.
- Fill almost to the top with vegetable oil.
w: Oil is lighter than water, and the two do not mix...
x: Shine a flashlight under the bottle in a dark room.
s: Adults should handle the tablets.
```

| Line | Meaning |
|------|---------|
| `# Title` | starts a new project |
| `e=` `a=` `d=` `t=` | emoji, age range, difficulty (Easy / Medium / Hard), time |
| `m:` | materials, separated by `;` |
| `- ` | one line per step, in order |
| `w:` | the science behind it |
| `x:` | try this next (optional) |
| `s:` | safety note (optional) |

After editing, rebuild the site (needs Python 3, which is free from python.org):

```
python3 build.py
```

Then upload the updated `docs` folder to GitHub again.

### Add a specific YouTube video to a project

By default each project shows a "Watch it done on YouTube" button that opens YouTube search results
for that project, so it always works. To embed one particular video instead, find it on YouTube,
copy the ID from its address (the part after `watch?v=`, e.g. `dQw4w9WgXcQ`) and add `v=` to the
project's second line:

```
e=🌋 a=4-10 d=Easy t=20 min v=dQw4w9WgXcQ
```

Rebuild and the video plays right on the project page. Pick videos from channels you trust, and
check they allow embedding.

### Add your own photos

Put a photo in the `images/` folder (e.g. `images/volcano.jpg`) and add `i=` to that project:

```
e=🌋 a=4-10 d=Easy t=20 min i=images/volcano.jpg
```

The photo replaces the illustration on the project page and its cards. Photos you take yourself
are best. Only use pictures you have permission to use.

### Using your own domain

Open `build.py` and set `CUSTOM_DOMAIN` (e.g. `"www.sparklab.com"`) and `SITE_URL`
(e.g. `"https://www.sparklab.com"`), then rebuild. This keeps the `docs/CNAME` file GitHub needs,
so your domain survives every rebuild and re-upload.

### Google Search Console and AdSense

All settings are at the top of `build.py`:

| Setting | What to paste |
|---------|---------------|
| `SITE_URL` | your live address, e.g. `https://www.sparklab.com` (adds sitemap, robots.txt and canonical links) |
| `GOOGLE_SITE_VERIFICATION` | the code from Search Console's "HTML tag" verification method |
| `ADSENSE_CLIENT` | your AdSense publisher ID, e.g. `ca-pub-1234567890123456` (adds the AdSense script and `ads.txt`) |
| `ADSENSE_SLOTS` | one ad unit ID per spot: project_content, project_side, project_bottom, home, browse |
| `ADS_PREVIEW` | `True` shows dashed "Ad space" boxes so you can preview placement; set `False` before publishing |
| `ADS_CHILD_DIRECTED` | keep `True`: this is a kids' site, so ads are requested as child-directed |
| `CONTACT_EMAIL` | your email, shown on the privacy policy page |

Rebuild with `python3 build.py`, then commit and push.

### Sitemap for Google

Open `build.py`, set `SITE_URL` to your live address (e.g. `https://yourname.github.io/spark-lab`),
and rebuild. This adds `sitemap.xml` and `robots.txt` so search engines can find every project.

---

## A note on safety

Projects use everyday materials, and anything risky has a safety note. The Teachers & parents page
includes printable safety rules. Encourage visitors to do projects with an adult nearby.
