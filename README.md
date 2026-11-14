# Enseada Imóveis – Makler-Template (Demo)

Statische Website für Immobilienmakler. Alle Namen, Preise und Adressen sind erfunden.

- **Jede Seite ist eine eigene HTML-Datei** (Portugiesisch, Englisch, Deutsch) – lesbar für Google und KI-Suchen, ohne dass ein Browser etwas zusammenbauen muss.
- **Im Hintergrund:** Schema-Daten je Seite, `llms.txt`, `sitemap.xml`, `robots.txt`, IndexNow, Bilder als WebP in drei Größen.
- **Pflege per Formular:** Der Makler meldet sich bei [Pages CMS](https://app.pagescms.org) an, klickt auf „Imóveis“ → „Add an entry“, füllt das Formular aus und speichert. Die Seite baut sich neu und ist in etwa zwei Minuten online.

## Für einen neuen Kunden anpassen

1. Dieses Projekt kopieren („Use this template“ bzw. „Fork“) und GitHub Pages auf „GitHub Actions“ stellen.
2. `content/site.json` ausfüllen: Name, Makler, CRECI, Telefon, WhatsApp, E-Mail, Adresse, Fotos, Zahlen.
3. Beispiel-Einträge in `content/imoveis/` und `content/blog/` durch die des Kunden ersetzen, Fotos nach `content/fotos/`.
4. Texte der Seiten (Überschriften, Über uns, FAQ) stehen in `src/views/*.html` jeweils in `addDict({pt, en, de})`.
5. Eigene Domain verbinden – dann liegen `robots.txt` und `llms.txt` im Wurzelverzeichnis, wo Suchmaschinen und KI sie lesen.

## Aufbau

| Ordner / Datei | Inhalt |
| --- | --- |
| `content/imoveis/` | ein Eintrag je Immobilie |
| `content/blog/` | ein Eintrag je Artikel |
| `content/site.json` | alle Kundendaten an einer Stelle |
| `content/fotos/` | Fotos (werden beim Bauen verkleinert) |
| `src/` | Gestaltung und Seitenbausteine |
| `build.py` | baut alles nach `dist/` |
| `.pages.yml` | Aufbau des Formulars |
| `.github/workflows/site.yml` | baut und veröffentlicht bei jeder Änderung |

## Lokal bauen

```
pip install -r requirements.txt   # dazu Node.js
python build.py
```
