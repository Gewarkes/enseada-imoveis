# Enseada Imóveis – Makler-Template (Demo)

Statische Website für Immobilienmakler. Alle Namen, Preise und Adressen sind erfunden.

- **Jede Seite ist eine eigene HTML-Datei** (Portugiesisch, Englisch, Deutsch) – lesbar für Google und KI-Suchen, ohne dass ein Browser etwas zusammenbauen muss.
- **Im Hintergrund:** Schema-Daten je Seite, `llms.txt`, `sitemap.xml`, `robots.txt`, IndexNow, Bilder als WebP in drei Größen.
- **Pflege per Formular:** Der Makler meldet sich bei [Pages CMS](https://app.pagescms.org) an, klickt auf „Imóveis“ → „Add an entry“, füllt das Formular aus und speichert. Die Seite baut sich neu und ist in etwa zwei Minuten online.

## Aufbau

| Ordner / Datei | Inhalt |
| --- | --- |
| `content/imoveis/` | ein Eintrag je Immobilie |
| `content/blog/` | ein Eintrag je Artikel |
| `content/fotos/` | Fotos (werden beim Bauen verkleinert) |
| `src/` | Gestaltung und Seitenbausteine |
| `build.py` | baut alles nach `dist/` |
| `.pages.yml` | Aufbau des Formulars |
| `.github/workflows/site.yml` | baut und veröffentlicht bei jeder Änderung |

## Lokal bauen

```
pip install pillow playwright && python -m playwright install chromium
python build.py
```
