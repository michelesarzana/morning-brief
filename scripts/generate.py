#!/usr/bin/env python3
"""Morning Brief — genera index.html + archivio giornaliero (v2)."""

import json, os, sys, datetime, re
from pathlib import Path

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# ── Config ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
ROOT       = SCRIPT_DIR.parent
DOCS       = ROOT / "docs"
ARCHIVE    = DOCS / "archive"
SOURCES_F  = ROOT / "sources.json"

DOCS.mkdir(exist_ok=True)
ARCHIVE.mkdir(exist_ok=True)

DAYS_IT   = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]
MONTHS_IT = ["","gennaio","febbraio","marzo","aprile","maggio","giugno",
             "luglio","agosto","settembre","ottobre","novembre","dicembre"]

CATEGORY_EMOJI = {
    "Brand & Marketing":        "🎯",
    "Media & Piano Media":      "📡",
    "TLC & Tecnologia":         "📱",
    "Consumer Insight & NPS":   "📊",
    "Social Media & Contenuti": "💬",
    "Creatività & Design":      "🎨",
    "AI & Innovazione":         "🤖",
    "Newsletter & Substack":    "📬",
}

MAX_PER_SOURCE = 5   # max articoli per fonte
TOP_ARTICLES   = 5   # card in evidenza per categoria
SUMMARY_TOP    = 8   # notizie nel sommario iniziale

# ── Date helpers ─────────────────────────────────────────────────────────────
def it_date(dt):
    return f"{DAYS_IT[dt.weekday()]} {dt.day} {MONTHS_IT[dt.month]} {dt.year}"

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()

def truncate(text, n=200):
    text = strip_html(text)
    return text[:n] + "…" if len(text) > n else text

# ── Fetch RSS ─────────────────────────────────────────────────────────────────
def parse_date(entry):
    """Best-effort: return datetime.date from entry, or None."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime.date(*t[:3])
            except Exception:
                pass
    return None

def fetch_all(sources, today):
    """
    Returns:
      articles   – list of dicts, all non-substack sources
      newsletters – list of dicts, substack sources published yesterday
    """
    articles    = []
    newsletters = []
    yesterday   = today - datetime.timedelta(days=1)

    for src in sources:
        rss = src.get("rss")
        if not rss:
            continue
        is_substack = "substack.com" in rss or src.get("category") == "Newsletter & Substack"
        try:
            feed = feedparser.parse(rss)
            entries = feed.entries[:MAX_PER_SOURCE] if feed.entries else []
            for entry in entries:
                title   = strip_html(getattr(entry, "title",   "—"))
                link    = getattr(entry, "link",  "#")
                summary = truncate(getattr(entry, "summary", ""), 220)
                pub_dt  = parse_date(entry)

                item = {
                    "title":    title,
                    "source":   src["name"],
                    "link":     link,
                    "excerpt":  summary,
                    "category": src["category"],
                    "priority": src.get("priority", "Media"),
                    "date":     pub_dt,
                }
                if is_substack:
                    # solo edizioni di ieri
                    if pub_dt == yesterday:
                        newsletters.append(item)
                else:
                    articles.append(item)
        except Exception as e:
            print(f"  [WARN] {src['name']}: {e}", file=sys.stderr)

    return articles, newsletters

# ── CSS / HEAD ────────────────────────────────────────────────────────────────
COMMON_HEAD = '''<!DOCTYPE html>
<html lang="it" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --yellow:#FDC400;--red:#E60000;--dark:#181717;
  --bg:#f0f2f5;--bg-card:#ffffff;--bg-header:#181717;
  --border:#e2e5ea;--text:#1a1d23;--muted:#6b7280;
  --shadow:0 2px 8px rgba(0,0,0,.08);
  --radius:12px;
}
[data-theme="dark"]{
  --bg:#0d0f14;--bg-card:#1a1d23;--bg-header:#0d0f14;
  --border:#2a2d35;--text:#e8eaf0;--muted:#9ca3af;
  --shadow:0 2px 8px rgba(0,0,0,.4);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
a{color:var(--yellow);text-decoration:none}
a:hover{text-decoration:underline}

/* ── Layout ── */
.wrap{max-width:1400px;margin:0 auto;padding:0 2rem}

/* ── Header ── */
.site-header{background:var(--bg-header);border-bottom:3px solid var(--yellow);padding:1rem 0;position:sticky;top:0;z-index:100}
.site-header .wrap{display:flex;align-items:center;justify-content:space-between;gap:1rem}
.logo{display:flex;align-items:center;gap:.6rem}
.logo-icon{font-size:1.6rem}
.logo-text{font-size:1.25rem;font-weight:800;color:#fff;letter-spacing:-.02em}
.logo-text span{color:var(--yellow)}
.nav-links{display:flex;gap:1.5rem;align-items:center}
.nav-links a{color:#ccc;font-size:.85rem;font-weight:500}
.nav-links a:hover{color:var(--yellow);text-decoration:none}
#theme-toggle{background:rgba(255,255,255,.1);border:none;color:#ccc;padding:.35rem .7rem;border-radius:6px;cursor:pointer;font-size:.9rem}

/* ── Hero / Stats ── */
.hero{background:var(--bg-header);padding:2.5rem 0 3rem;border-bottom:1px solid rgba(255,255,255,.05)}
.hero-date{font-size:.9rem;color:var(--yellow);font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem}
.hero-title{font-size:2.4rem;font-weight:800;color:#fff;margin-bottom:1.5rem;line-height:1.1}
.stats-row{display:flex;gap:1.5rem;flex-wrap:wrap}
.stat-card{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);border-radius:var(--radius);padding:1rem 1.4rem;min-width:140px}
.stat-num{font-size:2rem;font-weight:800;color:var(--yellow);line-height:1}
.stat-label{font-size:.78rem;color:#aaa;margin-top:.3rem;text-transform:uppercase;letter-spacing:.05em}

/* ── Main grid ── */
.main-content{padding:2rem 0}
.page-grid{display:grid;grid-template-columns:1fr 340px;gap:2rem;align-items:start}

/* ── Section titles ── */
.section-title{font-size:1rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-bottom:1.2rem;display:flex;align-items:center;gap:.5rem;padding-bottom:.5rem;border-bottom:2px solid var(--yellow)}
.section-title span{color:var(--text)}

/* ── Summary cards ── */
.summary-section{margin-bottom:2.5rem}
.summary-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem}
.summary-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.4rem;box-shadow:var(--shadow);border-left:3px solid var(--yellow);transition:transform .15s,box-shadow .15s}
.summary-card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.12)}
.summary-card .sc-source{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--yellow);margin-bottom:.4rem}
.summary-card .sc-title{font-size:.95rem;font-weight:600;color:var(--text);line-height:1.35;margin-bottom:.5rem}
.summary-card .sc-excerpt{font-size:.82rem;color:var(--muted);line-height:1.5;margin-bottom:.8rem}
.summary-card .sc-link{font-size:.78rem;font-weight:600;color:var(--yellow)}

/* ── Category sections ── */
.cat-section{margin-bottom:2.5rem}
.cat-header{display:flex;align-items:center;gap:.7rem;margin-bottom:1.2rem;padding-bottom:.5rem;border-bottom:2px solid var(--border)}
.cat-emoji{font-size:1.3rem}
.cat-name{font-size:1.1rem;font-weight:700;color:var(--text)}
.cat-count{font-size:.75rem;background:var(--yellow);color:var(--dark);border-radius:20px;padding:.1rem .6rem;font-weight:700;margin-left:auto}

/* Top 5 cards */
.top-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-bottom:1.5rem}
.art-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:1.1rem 1.3rem;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:.5rem;transition:transform .15s}
.art-card:hover{transform:translateY(-2px)}
.art-card .ac-source{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--red)}
.art-card .ac-title{font-size:.9rem;font-weight:600;color:var(--text);line-height:1.35}
.art-card .ac-excerpt{font-size:.8rem;color:var(--muted);line-height:1.5;flex:1}
.art-card .ac-link{font-size:.75rem;font-weight:600;color:var(--yellow);margin-top:auto}

/* Other articles list */
.other-list{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.other-list-title{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:.8rem 1.2rem;border-bottom:1px solid var(--border);background:rgba(0,0,0,.02)}
.other-item{display:grid;grid-template-columns:110px 1fr;gap:1rem;padding:.9rem 1.2rem;border-bottom:1px solid var(--border);align-items:start}
.other-item:last-child{border-bottom:none}
.other-item:hover{background:rgba(0,0,0,.02)}
.oi-source{font-size:.7rem;font-weight:700;text-transform:uppercase;color:var(--muted);padding-top:.1rem}
.oi-title{font-size:.85rem;font-weight:600;color:var(--text);margin-bottom:.25rem;line-height:1.3}
.oi-excerpt{font-size:.78rem;color:var(--muted);line-height:1.45;margin-bottom:.3rem}
.oi-link{font-size:.72rem;font-weight:600;color:var(--yellow)}

/* ── Sidebar ── */
.sidebar{}
.sidebar-block{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:1.2rem;margin-bottom:1.5rem;box-shadow:var(--shadow)}
.sidebar-block .sb-title{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-bottom:1rem;padding-bottom:.6rem;border-bottom:1px solid var(--border)}
.sources-list{list-style:none;display:flex;flex-direction:column;gap:.4rem}
.sources-list li a{font-size:.82rem;color:var(--text)}
.sources-list li a:hover{color:var(--yellow)}
.sources-list li .sl-cat{font-size:.68rem;color:var(--muted)}

/* ── Substack section ── */
.substack-section{margin-bottom:2.5rem}
.sub-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem}
.sub-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.4rem;box-shadow:var(--shadow);border-top:3px solid var(--red)}
.sub-card .sc2-nl{font-size:.7rem;font-weight:700;text-transform:uppercase;color:var(--red);margin-bottom:.35rem}
.sub-card .sc2-title{font-size:.9rem;font-weight:600;color:var(--text);margin-bottom:.5rem;line-height:1.35}
.sub-card .sc2-excerpt{font-size:.8rem;color:var(--muted);line-height:1.5;margin-bottom:.7rem}
.sub-card .sc2-link{font-size:.75rem;font-weight:600;color:var(--yellow)}
.sub-empty{color:var(--muted);font-size:.85rem;padding:1rem 0}

/* ── Footer ── */
.site-footer{background:var(--bg-header);border-top:1px solid rgba(255,255,255,.08);padding:1.5rem 0;margin-top:2rem}
.site-footer .wrap{display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap}
.site-footer p{font-size:.8rem;color:#888}
.site-footer a{color:var(--yellow);font-size:.8rem}

/* ── Responsive ── */
@media(max-width:1100px){.page-grid{grid-template-columns:1fr}}
@media(max-width:700px){
  .hero-title{font-size:1.6rem}
  .stats-row{gap:1rem}
  .top-grid{grid-template-columns:1fr}
  .other-item{grid-template-columns:80px 1fr;gap:.7rem}
  .wrap{padding:0 1rem}
}
</style>
</head>
<body>'''

THEME_SCRIPT = '''<script>
(function(){
  var s=localStorage.getItem("mb-theme"),sys=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";
  document.documentElement.setAttribute("data-theme",s||sys);
  document.addEventListener("DOMContentLoaded",function(){
    var btn=document.getElementById("theme-toggle");
    if(btn){
      btn.textContent=document.documentElement.getAttribute("data-theme")==="dark"?"☀️":"🌙";
      btn.addEventListener("click",function(){
        var n=document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark";
        document.documentElement.setAttribute("data-theme",n);
        localStorage.setItem("mb-theme",n);
        btn.textContent=n==="dark"?"☀️":"🌙";
      });
    }
  });
})();
</script>'''

# ── HTML builders ─────────────────────────────────────────────────────────────
def render_header(archive_link="archive/index.html", home_link=None):
    home_href = home_link or "index.html"
    return f'''
<header class="site-header">
  <div class="wrap">
    <div class="logo">
      <span class="logo-icon">☀️</span>
      <span class="logo-text">Morning <span>Brief</span></span>
    </div>
    <nav class="nav-links">
      <a href="{home_href}">Home</a>
      <a href="{archive_link}">Archivio</a>
      <button id="theme-toggle">🌙</button>
    </nav>
  </div>
</header>
{THEME_SCRIPT}'''

def render_hero(today, n_sources, n_articles, n_newsletters):
    it_today = it_date(today)
    return f'''
<section class="hero">
  <div class="wrap">
    <div class="hero-date">{today.strftime("%A %d %B %Y").upper()}</div>
    <div class="hero-title">Buongiorno 👋<br>{it_today}</div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-num">{n_sources}</div><div class="stat-label">Fonti analizzate</div></div>
      <div class="stat-card"><div class="stat-num">{n_articles}</div><div class="stat-label">Articoli trovati</div></div>
      <div class="stat-card"><div class="stat-num">{n_newsletters}</div><div class="stat-label">Newsletter di ieri</div></div>
    </div>
  </div>
</section>'''

def render_summary(articles):
    # Top SUMMARY_TOP by priority then first-come
    top = [a for a in articles if a["priority"] == "Alta"][:SUMMARY_TOP]
    if not top:
        top = articles[:SUMMARY_TOP]
    if not top:
        return ""
    cards = ""
    for a in top:
        cards += f'''<div class="summary-card">
  <div class="sc-source">{a["source"]}</div>
  <div class="sc-title">{a["title"]}</div>
  <div class="sc-excerpt">{a["excerpt"]}</div>
  <a class="sc-link" href="{a["link"]}" target="_blank" rel="noopener">Leggi →</a>
</div>'''
    return f'''<section class="summary-section">
  <div class="section-title"><span>📌 Sommario del giorno</span></div>
  <div class="summary-grid">{cards}</div>
</section>'''

def render_categories(articles):
    # Group by category
    from collections import defaultdict
    grouped = defaultdict(list)
    for a in articles:
        if a["category"] != "Newsletter & Substack":
            grouped[a["category"]].append(a)

    html = ""
    for cat, items in grouped.items():
        emoji = CATEGORY_EMOJI.get(cat, "📰")
        top5  = items[:TOP_ARTICLES]
        rest  = items[TOP_ARTICLES:]
        total = len(items)

        # Top 5 cards
        cards = ""
        for a in top5:
            cards += f'''<div class="art-card">
  <div class="ac-source">{a["source"]}</div>
  <div class="ac-title">{a["title"]}</div>
  <div class="ac-excerpt">{a["excerpt"]}</div>
  <a class="ac-link" href="{a["link"]}" target="_blank" rel="noopener">Leggi →</a>
</div>'''

        # Other items
        others_html = ""
        if rest:
            rows = ""
            for a in rest:
                rows += f'''<div class="other-item">
  <div class="oi-source">{a["source"]}</div>
  <div>
    <div class="oi-title">{a["title"]}</div>
    <div class="oi-excerpt">{a["excerpt"]}</div>
    <a class="oi-link" href="{a["link"]}" target="_blank" rel="noopener">Leggi →</a>
  </div>
</div>'''
            others_html = f'<div class="other-list"><div class="other-list-title">Altre notizie</div>{rows}</div>'

        html += f'''<section class="cat-section">
  <div class="cat-header">
    <span class="cat-emoji">{emoji}</span>
    <span class="cat-name">{cat}</span>
    <span class="cat-count">{total}</span>
  </div>
  <div class="top-grid">{cards}</div>
  {others_html}
</section>'''

    return html

def render_substack(newsletters):
    if not newsletters:
        return f'''<section class="substack-section">
  <div class="section-title"><span>📬 Newsletter Substack di ieri</span></div>
  <p class="sub-empty">Nessuna newsletter pubblicata ieri.</p>
</section>'''
    cards = ""
    for n in newsletters:
        cards += f'''<div class="sub-card">
  <div class="sc2-nl">{n["source"]}</div>
  <div class="sc2-title">{n["title"]}</div>
  <div class="sc2-excerpt">{n["excerpt"]}</div>
  <a class="sc2-link" href="{n["link"]}" target="_blank" rel="noopener">Leggi →</a>
</div>'''
    return f'''<section class="substack-section">
  <div class="section-title"><span>📬 Newsletter Substack di ieri ({len(newsletters)})</span></div>
  <div class="sub-grid">{cards}</div>
</section>'''

def render_sidebar(sources, today, archive_link="archive/index.html"):
    # Sources grouped by category
    from collections import defaultdict
    grouped = defaultdict(list)
    for s in sources:
        grouped[s["category"]].append(s)

    items = ""
    for cat, srcs in grouped.items():
        emoji = CATEGORY_EMOJI.get(cat, "📰")
        for s in srcs[:5]:  # max 5 per cat in sidebar
            items += f'<li><a href="{s["url"]}" target="_blank" rel="noopener">{s["name"]}</a><br><span class="sl-cat">{emoji} {cat}</span></li>'

    return f'''<aside class="sidebar">
  <div class="sidebar-block">
    <div class="sb-title">📚 Fonti monitorate ({len(sources)})</div>
    <ul class="sources-list">{items}</ul>
  </div>
</aside>'''

# ── Page builders ─────────────────────────────────────────────────────────────
def build_index(articles, newsletters, sources, today):
    n_sources     = len(sources)
    n_articles    = len(articles)
    n_newsletters = len(newsletters)
    page = COMMON_HEAD.replace("__TITLE__", f"Morning Brief — {it_date(today)}")
    page += render_header()
    page += render_hero(today, n_sources, n_articles, n_newsletters)
    page += f'''
<div class="wrap main-content">
  <div class="page-grid">
    <main>
      {render_summary(articles)}
      {render_categories(articles)}
      {render_substack(newsletters)}
    </main>
    {render_sidebar(sources, today)}
  </div>
</div>
<footer class="site-footer">
  <div class="wrap">
    <p>Morning Brief — generato ogni mattina alle 07:00 Europe/Rome</p>
    <a href="archive/index.html">📁 Archivio</a>
  </div>
</footer>
</body></html>'''
    return page

def build_archive_day(articles, newsletters, sources, today):
    page = COMMON_HEAD.replace("__TITLE__", f"Morning Brief — {it_date(today)} (archivio)")
    page += render_header(archive_link="../archive/index.html", home_link="../index.html")
    page += render_hero(today, len(sources), len(articles), len(newsletters))
    page += f'''
<div class="wrap main-content">
  <div class="page-grid">
    <main>
      {render_summary(articles)}
      {render_categories(articles)}
      {render_substack(newsletters)}
    </main>
    {render_sidebar(sources, today, archive_link="../archive/index.html")}
  </div>
</div>
<footer class="site-footer">
  <div class="wrap">
    <p>Morning Brief — archivio</p>
    <a href="../index.html">← Home</a>
  </div>
</footer>
</body></html>'''
    return page

def update_archive_index(today):
    """Scan archive dir and build index."""
    entries = sorted([f for f in ARCHIVE.iterdir() if f.suffix == ".html" and f.name != "index.html"], reverse=True)
    rows = ""
    for f in entries[:60]:
        name = f.stem
        try:
            dt = datetime.date.fromisoformat(name)
            label = it_date(dt)
        except Exception:
            label = name
        rows += f'<li><a href="{f.name}">📄 {label}</a></li>'

    page = COMMON_HEAD.replace("__TITLE__", "Morning Brief — Archivio")
    page += render_header(archive_link="index.html", home_link="../index.html")
    page += f'''
<div class="wrap main-content">
  <h2 style="margin-bottom:1.5rem;font-size:1.4rem">📁 Archivio edizioni</h2>
  <ul style="list-style:none;display:flex;flex-direction:column;gap:.7rem">{rows if rows else "<li style='color:var(--muted)'>Nessuna edizione ancora.</li>"}</ul>
</div>
<footer class="site-footer">
  <div class="wrap"><p>Morning Brief</p><a href="../index.html">← Home</a></div>
</footer>
</body></html>'''
    (ARCHIVE / "index.html").write_text(page, encoding="utf-8")
    print(f"  Updated archive/index.html ({len(entries)} entries)")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    sources = json.loads(SOURCES_F.read_text(encoding="utf-8"))
    print(f"Loaded {len(sources)} sources")

    today = datetime.date.today()
    print(f"Generating for {today}")

    if HAS_FEEDPARSER:
        print("Fetching RSS feeds…")
        articles, newsletters = fetch_all(sources, today)
        print(f"  Articles: {len(articles)} | Newsletters: {len(newsletters)}")
    else:
        print("feedparser not available — using empty lists")
        articles, newsletters = [], []

    index_html  = build_index(articles, newsletters, sources, today)
    archive_day = build_archive_day(articles, newsletters, sources, today)
    iso_today   = today.strftime("%Y-%m-%d")

    (DOCS / "index.html").write_text(index_html, encoding="utf-8")
    print("  Written docs/index.html")

    (ARCHIVE / f"{iso_today}.html").write_text(archive_day, encoding="utf-8")
    print(f"  Written docs/archive/{iso_today}.html")

    update_archive_index(today)
    print("Done ✓")

if __name__ == "__main__":
    main()
