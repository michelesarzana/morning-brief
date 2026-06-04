# ☀️ Morning Brief

Rassegna stampa mattutina automatica — Brand & Media.

## Come funziona

Una GitHub Action si attiva ogni mattina alle **07:00 Europe/Rome** (06:00 UTC):
1. Legge le fonti in `sources.json`
2. Recupera gli ultimi articoli dai feed RSS
3. Genera una pagina HTML moderna con dark/light mode
4. Pubblica su GitHub Pages via branch `gh-pages`

## Sito

👉 **https://michelesarzana.github.io/morning-brief**

## Aggiungere fonti / Substack

Modifica `sources.json`:

```json
{
  "name": "La mia newsletter",
  "url": "https://esempio.substack.com",
  "rss": "https://esempio.substack.com/feed",
  "category": "Le Mie Newsletter",
  "priority": "Alta",
  "lang": "IT"
}
```

## Avvio manuale

**Actions** → **Generate Morning Brief** → **Run workflow**

## Stack

Python 3.11 · feedparser · HTML/CSS/JS vanilla · GitHub Actions · GitHub Pages
