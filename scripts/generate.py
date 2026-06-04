#!/usr/bin/env python3
"""Morning Brief — genera index.html + archivio giornaliero."""

import json, os, sys, datetime, textwrap
from pathlib import Path

# ── Try feedparser; fallback gracefully ──────────────────────────────────────
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

DAYS_IT = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]
MONTHS_IT = ["","gennaio","febbraio","marzo","aprile","maggio","giugno",
             "luglio","agosto","settembre","ottobre","novembre","dicembre"]

CATEGORY_EMOJI = {
    "Brand & Marketing":       "🎯",
    "Media & Piano Media":     "📡",
    "TLC & Tecnologia":        "📱",
    "Consumer Insight & NPS":  "📊",
    "Social Media & Contenuti":"💬",
    "Creatività & Design":     "🎨",
    "AI & Innovazione":        "🤖",
}

MAX_ARTICLES = 10

# ── Date helpers ─────────────────────────────────────────────────────────────
def it_date(dt):
    return f"{DAYS_IT[dt.weekday()]} {dt.day} {MONTHS_IT[dt.month]} {dt.year}"

# ── Fetch feed articles ──────────────────────────────────────────────────────
def fetch_articles(sources):
    articles = []
    count = 0
    for src in sources:
        if src.get("priority") != "Alta":
            continue
        if not src.get("rss"):
            continue
        if count >= MAX_ARTICLES:
            break
        try:
            feed = feedparser.parse(src["rss"])
            entries = feed.entries[:3] if feed.entries else []
            for entry in entries:
                if count >= MAX_ARTICLES:
                    break
                title   = getattr(entry, "title", "—")
                link    = getattr(entry, "link",  "#")
                summary = getattr(entry, "summary", "")
                summary = summary[:180] + "…" if len(summary) > 180 else summary
                # strip HTML tags from summary
                import re
                summary = re.sub(r"<[^>]+>", "", summary).strip()
                summary = summary[:180] + "…" if len(summary) > 180 else summary
                articles.append({
                    "title":    title,
                    "source":   src["name"],
                    "link":     link,
                    "excerpt":  summary,
                    "category": src["category"],
                })
                count += 1
        except Exception as e:
            print(f"  [WARN] {src['name']}: {e}", file=sys.stderr)
    return articles

# ── HTML template helpers ─────────────────────────────────────────────────────
COMMON_HEAD = '''<!DOCTYPE html>
<html lang="it" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --accent-yellow: #FDC400;
  --accent-red:    #E60000;
  --bg:       #f7f8fa;
  --bg-card:  #ffffff;
  --bg-header:#ffffff;
  --border:   #e2e5ea;
  --text:     #1a1d23;
  --text-muted:#6b7280;
  --shadow:   0 1px 4px rgba(0,0,0,.08);
}
[data-theme="dark"] {
  --bg:       #0f1117;
  --bg-card:  #1a1d23;
  --bg-header:#12151c;
  --border:   #2a2d35;
  --text:     #e8eaf0;
  --text-muted:#9ca3af;
  --shadow:   0 1px 6px rgba(0,0,0,.4);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);transition:background .25s,color .25s;min-height:100vh}
a{color:var(--accent-yellow);text-decoration:none}
a:hover{text-decoration:underline}

/* ── Header ── */
.site-header{background:var(--bg-header);border-bottom:2px solid var(--accent-yellow);padding:0 1.5rem;position:sticky;top:0;z-index:100;box-shadow:var(--shadow)}
.header-inner{max-width:1100px;margin:auto;display:flex;align-items:center;justify-content:space-between;height:60px;gap:1rem}
.logo{font-size:1.3rem;font-weight:700;letter-spacing:-.02em;display:flex;align-items:center;gap:.4rem}
.logo span.year{font-size:.8rem;font-weight:400;color:var(--text-muted);margin-left:.3rem}
.header-nav{display:flex;align-items:center;gap:1.2rem;font-size:.9rem}
.header-nav a{color:var(--text-muted);font-weight:500;transition:color .2s}
.header-nav a:hover{color:var(--accent-yellow);text-decoration:none}
.theme-toggle{background:none;border:1px solid var(--border);border-radius:8px;width:36px;height:36px;cursor:pointer;font-size:1.1rem;display:flex;align-items:center;justify-content:center;transition:border-color .2s,background .2s;flex-shrink:0}
.theme-toggle:hover{border-color:var(--accent-yellow);background:var(--bg-card)}

/* ── Layout ── */
.container{max-width:1100px;margin:0 auto;padding:2rem 1.5rem}
.date-bar{display:flex;align-items:baseline;gap:.7rem;margin-bottom:2rem;flex-wrap:wrap}
.date-label{font-size:1.5rem;font-weight:700;text-transform:capitalize}
.date-badge{background:var(--accent-yellow);color:#1a1d23;font-size:.75rem;font-weight:700;padding:.2rem .6rem;border-radius:20px;text-transform:uppercase;letter-spacing:.05em}
.section-title{font-size:1rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted);margin-bottom:1rem;padding-bottom:.4rem;border-bottom:2px solid var(--accent-yellow);display:inline-flex;align-items:center;gap:.4rem}

/* ── Article cards ── */
.articles-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.25rem;margin-bottom:3rem}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1.25rem 1.25rem 1rem;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s;display:flex;flex-direction:column;gap:.6rem}
.card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.12)}
.card-cat{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--accent-red)}
.card-title{font-size:.95rem;font-weight:600;line-height:1.4;color:var(--text)}
.card-source{font-size:.75rem;color:var(--text-muted);font-weight:500}
.card-excerpt{font-size:.82rem;color:var(--text-muted);line-height:1.55;flex:1}
.card-link{font-size:.8rem;font-weight:600;color:var(--accent-yellow);align-self:flex-start;margin-top:.4rem}
.card-link:hover{text-decoration:none;opacity:.8}

/* ── Empty state ── */
.empty-state{text-align:center;padding:4rem 2rem;color:var(--text-muted)}
.empty-state .icon{font-size:3rem;margin-bottom:1rem}
.empty-state p{font-size:.95rem;line-height:1.6;max-width:400px;margin:auto}

/* ── Sources table ── */
.sources-section{margin-bottom:3rem}
.sources-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1rem}
.source-group{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1rem}
.source-group-title{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;margin-bottom:.7rem;color:var(--text);display:flex;align-items:center;gap:.35rem}
.source-list{list-style:none;display:flex;flex-direction:column;gap:.35rem}
.source-list li{font-size:.8rem}
.source-list a{color:var(--text-muted);font-weight:500;transition:color .2s}
.source-list a:hover{color:var(--accent-yellow);text-decoration:none}
.source-priority-high::before{content:"●";color:var(--accent-yellow);margin-right:.3rem;font-size:.65rem}

/* ── Footer ── */
.site-footer{border-top:1px solid var(--border);padding:1.5rem;text-align:center;font-size:.8rem;color:var(--text-muted);margin-top:2rem}
.site-footer a{color:var(--text-muted)}
.site-footer a:hover{color:var(--accent-yellow)}

/* ── Archive page ── */
.archive-list{display:flex;flex-direction:column;gap:.6rem;max-width:600px}
.archive-item{display:flex;align-items:center;background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:.85rem 1.2rem;gap:1rem;box-shadow:var(--shadow);transition:transform .2s}
.archive-item:hover{transform:translateX(4px)}
.archive-item .ai-date{font-size:.95rem;font-weight:600;flex:1}
.archive-item .ai-icon{font-size:1.1rem}

/* ── Responsive ── */
@media(max-width:600px){
  .articles-grid{grid-template-columns:1fr}
  .sources-grid{grid-template-columns:1fr}
  .logo span.year{display:none}
}
.substack-note{background:var(--bg-card);border:1px solid var(--border);border-left:3px solid var(--accent-yellow);border-radius:8px;padding:.9rem 1.1rem;font-size:.82rem;color:var(--text-muted);margin-bottom:2rem;line-height:1.6}
.substack-note strong{color:var(--text)}
</style>
</head>
<body>'''

THEME_SCRIPT = '''<script>
(function(){
  var saved = localStorage.getItem('mb-theme');
  var sys   = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  var theme = saved || sys;
  document.documentElement.setAttribute('data-theme', theme);
  document.addEventListener('DOMContentLoaded', function(){
    var btn = document.getElementById('theme-toggle');
    if(btn){
      btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
      btn.addEventListener('click', function(){
        var cur = document.documentElement.getAttribute('data-theme');
        var next = cur === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('mb-theme', next);
        btn.textContent = next === 'dark' ? '☀️' : '🌙';
      });
    }
  });
})();
</script>'''

def render_header(archive_link="../archive/index.html", home_link="index.html"):
    return f'''
{THEME_SCRIPT}
<header class="site-header">
  <div class="header-inner">
    <a href="{home_link}" style="text-decoration:none;color:var(--text)">
      <div class="logo">☀️ Morning Brief<span class="year">by NextMindLab</span></div>
    </a>
    <nav class="header-nav">
      <a href="{archive_link}">📁 Archivio</a>
      <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">🌙</button>
    </nav>
  </div>
</header>'''

def render_articles(articles):
    if not articles:
        return '''<div class="empty-state">
  <div class="icon">📭</div>
  <p>Nessun articolo disponibile per oggi.<br>I feed RSS verranno aggiornati alla prossima esecuzione automatica.</p>
</div>'''
    cards = ""
    for a in articles:
        emoji = CATEGORY_EMOJI.get(a["category"], "📰")
        cards += f'''
  <div class="card">
    <div class="card-cat">{emoji} {a["category"]}</div>
    <div class="card-title">{a["title"]}</div>
    <div class="card-source">via {a["source"]}</div>
    <div class="card-excerpt">{a["excerpt"]}</div>
    <a class="card-link" href="{a["link"]}" target="_blank" rel="noopener">Leggi →</a>
  </div>'''
    return f'<div class="articles-grid">{cards}</div>'

def render_sources(sources):
    # Group by category
    grouped = {}
    for s in sources:
        cat = s["category"]
        grouped.setdefault(cat, []).append(s)
    html = '<div class="sources-grid">'
    for cat, srcs in grouped.items():
        emoji = CATEGORY_EMOJI.get(cat, "📰")
        html += f'<div class="source-group"><div class="source-group-title">{emoji} {cat}</div><ul class="source-list">'
        for s in srcs:
            pri_class = "source-priority-high" if s.get("priority") == "Alta" else ""
            html += f'<li class="{pri_class}"><a href="{s["url"]}" target="_blank" rel="noopener">{s["name"]}</a></li>'
        html += '</ul></div>'
    html += '</div>'
    return html

def build_index(articles, sources, today, archive_path="archive/index.html"):
    it_today  = it_date(today)
    iso_today = today.strftime("%Y-%m-%d")
    page = COMMON_HEAD.replace("__TITLE__", f"Morning Brief — {it_today}")
    page += render_header(archive_link=archive_path)
    page += f'''
<main class="container">
  <div class="date-bar">
    <div class="date-label">{it_today}</div>
    <div class="date-badge">☀️ Buongiorno</div>
  </div>
  <div class="substack-note">
    💡 <strong>Tip:</strong> Vuoi aggiungere i tuoi Substack preferiti?
    Modifica il file <code>sources.json</code> nel repo e aggiungi le tue newsletter
    con il campo <code>"rss": "https://TUO-SUBSTACK.substack.com/feed"</code>.
  </div>
  <div class="section-title">📰 Articoli di Oggi</div>
  {render_articles(articles)}
  <div class="section-title">🔗 Tutte le Fonti</div>
  <div class="sources-section">{render_sources(sources)}</div>
</main>
<footer class="site-footer">
  Morning Brief — generato automaticamente ogni mattina alle 07:00 Europe/Rome &nbsp;|&nbsp;
  <a href="{archive_path}">📁 Archivio</a>
</footer>
</body></html>'''
    return page

def build_archive_day(articles, sources, today):
    it_today = it_date(today)
    page = COMMON_HEAD.replace("__TITLE__", f"Morning Brief — {it_today}")
    page += render_header(archive_link="../archive/index.html", home_link="../index.html")
    page += f'''
<main class="container">
  <div class="date-bar">
    <div class="date-label">{it_today}</div>
    <div class="date-badge">📂 Archivio</div>
  </div>
  <div class="section-title">📰 Articoli del giorno</div>
  {render_articles(articles)}
  <div class="section-title">🔗 Fonti</div>
  <div class="sources-section">{render_sources(sources)}</div>
</main>
<footer class="site-footer">
  <a href="../index.html">← Home</a> &nbsp;|&nbsp; <a href="../archive/index.html">📁 Archivio</a>
</footer>
</body></html>'''
    return page

def update_archive_index(today):
    iso_today = today.strftime("%Y-%m-%d")
    it_today  = it_date(today)
    archive_idx = ARCHIVE / "index.html"
    entries = []
    if archive_idx.exists():
        import re
        content = archive_idx.read_text(encoding="utf-8")
        entries = re.findall(r'data-date="([^"]+)"', content)
    if iso_today not in entries:
        entries.insert(0, iso_today)
    # rebuild archive index
    items_html = ""
    for iso in entries:
        dt_parts = iso.split("-")
        try:
            dt = datetime.date(int(dt_parts[0]), int(dt_parts[1]), int(dt_parts[2]))
            label = it_date(dt).capitalize()
        except:
            label = iso
        items_html += f'<a class="archive-item" href="{iso}.html" data-date="{iso}"><span class="ai-icon">📄</span><span class="ai-date">{label}</span><span style="color:var(--text-muted);font-size:.8rem">{iso}</span></a>\n'
    page = COMMON_HEAD.replace("__TITLE__", "Morning Brief — Archivio")
    page += render_header(archive_link="index.html", home_link="../index.html")
    page += f'''
<main class="container">
  <div class="date-bar">
    <div class="date-label">📁 Archivio</div>
  </div>
  <div class="archive-list">
{items_html}  </div>
  {'<p style="color:var(--text-muted);font-size:.9rem;margin-top:1.5rem">Nessuna edizione ancora disponibile.</p>' if not entries else ''}
</main>
<footer class="site-footer">
  <a href="../index.html">← Home</a>
</footer>
</body></html>'''
    archive_idx.write_text(page, encoding="utf-8")
    print(f"  Updated archive/index.html ({len(entries)} entries)")

def main():
    import urllib.request as ureq
    # Load sources
    sources = json.loads(SOURCES_F.read_text(encoding="utf-8"))
    print(f"Loaded {len(sources)} sources")

    today = datetime.date.today()
    print(f"Generating for {today}")

    # Fetch articles
    if HAS_FEEDPARSER:
        print("Fetching RSS feeds…")
        articles = fetch_articles(sources)
        print(f"  Got {len(articles)} articles")
    else:
        print("feedparser not available — using empty article list")
        articles = []

    # Build pages
    index_html   = build_index(articles, sources, today)
    archive_day  = build_archive_day(articles, sources, today)
    iso_today    = today.strftime("%Y-%m-%d")

    (DOCS / "index.html").write_text(index_html, encoding="utf-8")
    print("  Written docs/index.html")

    (ARCHIVE / f"{iso_today}.html").write_text(archive_day, encoding="utf-8")
    print(f"  Written docs/archive/{iso_today}.html")

    update_archive_index(today)
    print("Done ✓")

if __name__ == "__main__":
    main()
