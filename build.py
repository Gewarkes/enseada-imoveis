#!/usr/bin/env python3
"""Baut die statische Website nach dist/.

Jede Seite ist eine fertige HTML-Datei je Sprache (pt, en, de). Dazu: Bilder als WebP in drei
Größen, Schema-Daten je Seite, sitemap.xml, robots.txt, llms.txt und IndexNow.

Aufruf:  python build.py     (SITE_ORIGIN und SITE_BASE kommen aus der Umgebung)

Inhalte:  content/site.json (Kundendaten) · content/imoveis/*.json · content/blog/*.json · content/fotos/
Aussehen: src/site.css · src/site.js · src/templates/*.html · src/textos.json (alle festen Texte)
"""
import os, re, json, glob, shutil, hashlib, html, datetime
from PIL import Image
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

ORIGIN = os.environ.get('SITE_ORIGIN', 'https://gewarkes.github.io').rstrip('/').lower()
BASE = os.environ.get('SITE_BASE', '/enseada-imoveis/')
INDEXNOW_KEY = '7c1e5a9d3b2f4e6a8c0d1f2b3a4c5d6e'
LANGS = ['pt', 'en', 'de']
HL = {'pt': 'pt-BR', 'en': 'en', 'de': 'de'}
D = 'dist'


def rd(f):
    return open(f, encoding='utf-8').read()


def wr(f, s):
    os.makedirs(os.path.dirname(f) or '.', exist_ok=True)
    open(f, 'w', encoding='utf-8').write(s)


def slug(s):
    s = str(s).lower()
    for a, b in zip('áàâãäéèêëíìîïóòôõöúùûüçñ', 'aaaaaeeeeiiiiooooouuuucn'):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def tri(v):
    """Text in drei Sprachen; fehlt eine Sprache, gilt Portugiesisch."""
    if not isinstance(v, dict):
        v = {'pt': v or ''}
    base = v.get('pt') or v.get('en') or v.get('de') or ''
    return {k: (v.get(k) or base) for k in LANGS}


def ik(k):
    """Dateiname eines Fotos ohne Ordner und Endung."""
    return slug(os.path.splitext(os.path.basename(str(k)))[0])


# ---------- 1 Inhalte ----------
site = json.loads(rd('content/site.json'))
for k, v in {'theme': 'light', 'instagram': '', 'brokerUrl': '', 'contactUrl': '', 'newsletterUrl': '', 'gaId': '', 'reviews': [], 'demoNote': False,
             'rate': 11.5, 'buyCosts': 0.045, 'fx': {'date': '', 'USD': 0.178, 'EUR': 0.16}, 'geo': {}, 'stats': {}, 'media': {}}.items():
    site.setdefault(k, v)
site['agent'].setdefault('photo', '')
T = json.loads(rd('src/textos.json'))
HERO = (site.get('media') or {}).get('hero') or '02'

listings = [json.loads(rd(f)) for f in sorted(glob.glob('content/imoveis/*.json'))]
for l in listings:
    l['slug'] = slug(l.get('slug') or l['name'])
    for k in ('price', 'beds', 'baths', 'area', 'lot', 'year', 'beach', 'suites', 'parking', 'condo', 'iptu'):
        l[k] = l.get(k) or 0
    l['imgs'] = [ik(x) for x in (l.get('imgs') or [HERO])]
    l['feats'] = l.get('feats') or []
    l['dist'] = l.get('dist') or {}
    l['desc'] = tri(l.get('desc'))
    l['title'] = tri(l.get('title'))
    hl = l.get('highlights') or {}
    l['highlights'] = {k: (hl.get(k) or hl.get('pt') or []) for k in LANGS}
    l['status'] = l.get('status') or 'disponivel'
    l['date'] = l.get('date') or '2026-01-01'
    l['ref'] = l.get('ref') or l['slug'].upper()[:8]
    for k in ('video', 'plan', 'lat', 'lng'):
        l.setdefault(k, '')
    l['plan'] = ik(l['plan']) if l['plan'] else ''
    l['locslug'] = slug(l.get('loc', ''))
    l['cat'] = 'terrenos' if l.get('type') == 'terreno' else ('aluguel' if l.get('deal') == 'aluguel' else 'venda')
listings.sort(key=lambda x: (x.get('ordem') or 999, x['slug']))

posts = [json.loads(rd(f)) for f in sorted(glob.glob('content/blog/*.json'))]
for p in posts:
    p['slug'] = slug(p.get('slug') or tri(p['title'])['pt'])
    for k in ('cat', 'title', 'excerpt'):
        p[k] = tri(p.get(k))
    b = p.get('body')
    b = b if isinstance(b, dict) else {'pt': b or ''}
    b = {k: [x.strip() for x in re.split(r'\n\s*\n', b.get(k) or '') if x.strip()] for k in LANGS}
    p['body'] = {k: (b[k] or b['pt'] or b['en'] or b['de']) for k in LANGS}
    p['img'] = ik(p.get('img') or HERO)
    p['author'] = p.get('author') or site['agent']['name']
    p['read'] = {k: max(1, round(sum(len(x.split()) for x in p['body'][k]) / 200)) for k in LANGS}
posts.sort(key=lambda x: x.get('date', ''), reverse=True)

locs = []
for l in listings:
    if l.get('loc') and l['locslug'] not in [x['slug'] for x in locs]:
        locs.append({'slug': l['locslug'], 'name': l['loc']})
for x in locs:
    mine = [l for l in listings if l['locslug'] == x['slug']]
    x['n'] = len(mine)
    x['img'] = (site.get('locPhotos') or {}).get(x['slug']) or mine[0]['imgs'][-1]
    x['img'] = ik(x['img'])
locs.sort(key=lambda x: (-x['n'], x['name']))

# ---------- 2 Fotos -> WebP in drei Breiten ----------
shutil.rmtree(D, ignore_errors=True)
os.makedirs(D + '/assets')
os.makedirs(D + '/img')
dims = {}
n = 0
for f in sorted(glob.glob('content/fotos/*')):
    stem = ik(f)
    try:
        im = Image.open(f).convert('RGB')
    except Exception as ex:
        print('Foto übersprungen:', f, ex)
        continue
    for suf, w in (('', 1400), ('-s', 760), ('-xs', 480)):
        o = f'{D}/img/{stem}{suf}.webp'
        j = im.copy()
        j.thumbnail((w, w * 3))
        j.save(o, quality=62 if suf == '' else 58, method=6)
        dims[stem + suf] = j.size
    n += 1
print('Fotos:', n)

# ---------- 3 Hilfen für die Vorlagen ----------
ICONS = {
    'arrow': 'M5 12h14M13 6l6 6-6 6', 'check': 'm5 12 5 5 9-10', 'menu': 'M4 7h16M4 12h16M4 17h16', 'close': 'M6 6l12 12M18 6 6 18',
    'bed': 'M3 18v-7h13a5 5 0 0 1 5 5v2M3 11V6M3 15h18M7 11V9h5v2',
    'bath': 'M3 12h18v2a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5zM6 12V6a2 2 0 0 1 4 0M7 19l-1 2M17 19l1 2',
    'area': 'M4 4h16v16H4zM4 9h3M4 14h3M9 20v-3M14 20v-3', 'lot': 'M3 17l9 4 9-4M3 12l9 4 9-4M12 3 3 7l9 4 9-4z',
    'pin': 'M12 21s7-6.2 7-11a7 7 0 0 0-14 0c0 4.800 7 11 7 11zM12 12.500a2.500 2.500 0 1 0 0-5 2.500 2.500 0 0 0 0 5z',
    'phone': 'M5 4h4l2 5-2.500 1.500a11 11 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 4 5a1 1 0 0 1 1-1z',
    'mail': 'M3 6h18v12H3zM3 7l9 6 9-6', 'cal': 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
    'car': 'M3 13l2-5.500A2 2 0 0 1 6.900 6h10.200A2 2 0 0 1 19 7.500L21 13v5h-3v-2H6v2H3zM3 13h18M7 16h.010M17 16h.010',
    'camera': 'M4 8h3l2-3h6l2 3h3v11H4zM12 16.500a3.200 3.200 0 1 0 0-6.400 3.200 3.200 0 0 0 0 6.400z',
    'share': 'M12 15V4M8 8l4-4 4 4M5 12v7h14v-7', 'map': 'M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14',
    'list': 'M8 6h12M8 12h12M8 18h12M4 6h.010M4 12h.010M4 18h.010', 'doc': 'M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6',
    'globe': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18',
    'home': 'M4 11l8-7 8 7v9h-5v-6H9v6H4z', 'shield': 'M12 3 5 6v6c0 4.500 3 7.500 7 9 4-1.500 7-4.500 7-9V6zM9 12l2 2 4-4',
    'clock': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2', 'user': 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
    'ig': 'M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4zM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM17.500 6.500h.010',
    'tag': 'M3 12V4h8l10 10-8 8zM7.500 8.500h.010', 'sort': 'M7 4v16M3 16l4 4 4-4M17 20V4M13 8l4-4 4 4',
    'info': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v6M12 7.500h.010', 'play': 'M8 5v14l11-7z',
}
WA = 'M12 2a10 10 0 0 0-8.600 15.100L2 22l5-1.300A10 10 0 1 0 12 2zm0 1.800a8.200 8.200 0 1 1-4.200 15.300l-.300-.200-2.900.800.800-2.800-.200-.300A8.200 8.200 0 0 1 12 3.800zm-3.300 3.900c-.200 0-.500.100-.700.300-.300.300-1 1-1 2.300s1 2.700 1.200 2.900c.100.200 2 3.100 4.900 4.300 2.400.900 2.900.800 3.400.700.500 0 1.700-.700 1.900-1.300.200-.700.200-1.200.200-1.300-.100-.200-.300-.200-.600-.400l-2-.900c-.300-.100-.500-.200-.700.100l-.900 1.100c-.200.200-.300.200-.600.100-.300-.200-1.200-.500-2.300-1.400-.900-.800-1.400-1.700-1.600-2-.200-.300 0-.500.100-.600l.400-.500.300-.500v-.500l-.900-2.100c-.200-.500-.400-.500-.600-.500z'
STAR = 'M12 3.500l2.600 5.300 5.900.900-4.300 4.100 1 5.800L12 16.900 6.800 19.600l1-5.800L3.500 9.700l5.900-.900z'
MONTHS = {
    'pt': 'janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro'.split(),
    'en': 'January February March April May June July August September October November December'.split(),
    'de': 'Januar Februar März April Mai Juni Juli August September Oktober November Dezember'.split(),
}
e = lambda s: html.escape(str(s), quote=True)


def icon(n, cls='ico'):
    return Markup(f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="{ICONS[n]}"/></svg>')


def wa_icon(cls='ico-wa'):
    return Markup(f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="{WA}"/></svg>')


def stars():
    return Markup('<div class="stars" aria-hidden="true">' + f'<svg viewBox="0 0 24 24"><path d="{STAR}"/></svg>' * 5 + '</div>')


def path(route, lang):
    pre = '' if lang == 'pt' else lang + '/'
    if route == 'home':
        return pre
    for a, b in (('imoveis-', 'imoveis/'), ('imovel-', 'imovel/'), ('artigo-', 'blog/')):
        if route.startswith(a):
            return pre + b + route[len(a):] + '/'
    return pre + route + '/'


def nf(n, lang, d=0):
    s = f'{n:,.{d}f}'
    return s if lang == 'en' else s.replace(',', '§').replace('.', ',').replace('§', '.')


def make_ctx(lang, route):
    yrs = int((site.get('stats') or {}).get('years') or 0)
    fill = lambda s: s.replace('{years}', str(yrs)).replace('{since}', str(datetime.date.today().year - yrs))
    t = {k: fill((v.get(lang) or v.get('pt') or '') if isinstance(v, dict) else v) for k, v in T.items()}
    L = lambda o: '' if o is None else (o if isinstance(o, str) else (o.get(lang) or o.get('pt') or ''))
    url = lambda r, lg=None: BASE + path(r, lg or lang)

    def pic(k, sizes='100vw', alt='', cls='', eager=False, defer=False):
        k = ik(k)
        dm = dims.get(k, (1400, 933))
        src = f'{BASE}img/{k}-s.webp' if not eager else f'{BASE}img/{k}.webp'
        ss = f'{BASE}img/{k}-xs.webp 480w, {BASE}img/{k}-s.webp 760w, {BASE}img/{k}.webp 1400w'
        extra = 'fetchpriority="high" decoding="async"' if eager else 'loading="lazy" decoding="async"'
        c = f' class="{cls}"' if cls else ''
        if defer:   # Foto wird erst geladen, wenn der Besucher die Karte berührt
            return Markup(f'<img{c} data-src="{src}" data-srcset="{ss}" sizes="{sizes}" width="{dm[0]}" height="{dm[1]}" alt="{e(alt)}" decoding="async">')
        return Markup(f'<img{c} src="{src}" srcset="{ss}" sizes="{sizes}" width="{dm[0]}" height="{dm[1]}" alt="{e(alt)}" {extra}>')

    def money(v):
        return 'R$ ' + nf(round(v), lang)

    def price(l, tag='span'):
        suf = t['perMonth'] if l['deal'] == 'aluguel' else ''
        return Markup(f'<{tag} data-brl="{int(l["price"])}">{money(l["price"])}</{tag}>' + (f'<small>{e(suf)}</small>' if suf else ''))

    def fdate(d):
        y, m, dd = [int(x) for x in d.split('-')]
        mo = MONTHS[lang][m - 1]
        return {'pt': f'{dd} de {mo} de {y}', 'en': f'{dd} {mo} {y}', 'de': f'{dd}. {mo} {y}'}[lang]

    def plural(n, one, many):
        return f'{n} {t[one] if n == 1 else t[many]}'

    def wa(text=''):
        from urllib.parse import quote
        return f'https://wa.me/{site["wa"]}' + (f'?text={quote(text)}' if text else '')

    def facts(l):
        """Eckdaten einer Anzeige als Liste (Symbol, Zahl, Wort)."""
        o = []
        if l['beds']:
            o.append(('bed', l['beds'], t['bed1'] if l['beds'] == 1 else t['beds']))
        if l['baths']:
            o.append(('bath', l['baths'], t['bath1'] if l['baths'] == 1 else t['baths']))
        if l['area']:
            o.append(('area', nf(l['area'], lang), 'm²'))
        if l['lot'] and (l['type'] == 'terreno' or not l['area']):
            o.append(('lot', nf(l['lot'], lang), 'm² ' + t['lotWord']))
        return o

    return dict(lang=lang, hl=HL[lang], route=route, t=t, L=L, url=url, pic=pic, money=money, price=price, fdate=fdate,
                plural=plural, wa=wa, facts=facts, icon=icon, wa_icon=wa_icon, stars=stars, nf=lambda n, d=0: nf(n, lang, d),
                site=site, listings=listings, posts=posts, locs=locs, langs=LANGS, base=BASE, origin=ORIGIN,
                alt_url=lambda lg: BASE + path(route, lg), abs=lambda r, lg=None: ORIGIN + BASE + path(r, lg or lang),
                img=lambda k, s='': f'{BASE}img/{ik(k)}{s}.webp', imgabs=lambda k: f'{ORIGIN}{BASE}img/{ik(k)}.webp',
                year=datetime.date.today().year, demo=bool(site.get('demoNote')))


# ---------- 4 Stil und Skript ----------
css = rd('src/site.css')
css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
css = re.sub(r'\s*\n\s*', '\n', css).strip()
js = rd('src/site.js')
hc = hashlib.md5(css.encode()).hexdigest()[:8]
hj = hashlib.md5(js.encode()).hexdigest()[:8]
wr(f'{D}/assets/site.{hc}.css', css)
wr(f'{D}/assets/site.{hj}.js', js)
for f in glob.glob('src/fonts/*.woff2'):
    shutil.copy(f, f'{D}/assets/{os.path.basename(f)}')
lcss = rd('src/vendor/leaflet.css')
lcss = re.sub(r'url\(images/[^)]*\)', 'none', lcss)   # Standard-Marker werden nicht benutzt
wr(f'{D}/assets/leaflet.css', lcss)
shutil.copy('src/vendor/leaflet.js', f'{D}/assets/leaflet.js')

env = Environment(loader=FileSystemLoader('src/templates'), autoescape=True, undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
env.globals.update(css_file=f'{BASE}assets/site.{hc}.css', js_file=f'{BASE}assets/site.{hj}.js')
env.filters['tojson_safe'] = lambda o: Markup(json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))


# ---------- 5 Schema-Daten ----------
def org_ld(lang):
    a = site.get('geo') or {}
    return {'@type': 'RealEstateAgent', '@id': ORIGIN + BASE + '#org', 'name': site['brandFull'], 'url': ORIGIN + BASE + path('home', lang),
            'image': f'{ORIGIN}{BASE}img/{ik(HERO)}.webp', 'telephone': site['phone'], 'email': site['email'],
            'address': {'@type': 'PostalAddress', 'streetAddress': site['address'].split('·')[0].strip(), 'addressLocality': site.get('city', ''),
                        'addressRegion': site.get('state', ''), 'addressCountry': 'BR'},
            'geo': {'@type': 'GeoCoordinates', 'latitude': a.get('lat'), 'longitude': a.get('lng')},
            'openingHours': site.get('openingHours', ''), 'areaServed': [x['name'] for x in locs], 'knowsLanguage': ['pt-BR', 'en', 'de'],
            'priceRange': 'R$', **({'sameAs': [site['instagram']]} if site.get('instagram') else {})}


def crumbs_ld(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


def listing_ld(l, lang, c):
    kind = {'casa': 'SingleFamilyResidence', 'apartamento': 'Apartment'}.get(l['type'], 'Place')
    ent = {'@type': kind, 'name': l['name'], 'address': {'@type': 'PostalAddress', 'addressLocality': l.get('loc', ''), 'addressRegion': site.get('state', ''), 'addressCountry': 'BR'}}
    if l.get('lat'):
        ent['geo'] = {'@type': 'GeoCoordinates', 'latitude': l['lat'], 'longitude': l['lng']}
    if l['beds']:
        ent['numberOfBedrooms'] = l['beds']
    if l['baths']:
        ent['numberOfBathroomsTotal'] = l['baths']
    if l['area']:
        ent['floorSize'] = {'@type': 'QuantitativeValue', 'value': l['area'], 'unitCode': 'MTK'}
    if l['year']:
        ent['yearBuilt'] = l['year']
    return {'@type': 'RealEstateListing', 'name': f"{l['name']} – {l['title'][lang]}", 'description': l['desc'][lang].split('\n')[0],
            'url': c['abs']('imovel-' + l['slug']), 'datePosted': l['date'], 'identifier': l['ref'], 'inLanguage': HL[lang],
            'image': [c['imgabs'](k) for k in l['imgs']],
            'offers': {'@type': 'Offer', 'price': int(l['price']), 'priceCurrency': 'BRL',
                       'availability': 'https://schema.org/' + ('LimitedAvailability' if l['status'] == 'reservado' else 'InStock'),
                       'businessFunction': 'http://purl.org/goodrelations/v1#' + ('LeaseOut' if l['deal'] == 'aluguel' else 'Sell'),
                       'seller': {'@id': ORIGIN + BASE + '#org'}},
            'mainEntity': ent}


def clip(s, n=155):
    """Kürzt am Satzende, sonst am Wortende."""
    if len(s) <= n:
        return s
    cut = s[:n]
    i = cut.rfind('. ')
    return cut[:i + 1] if i > 60 else cut[:cut.rfind(' ')] + '…'


def ld(graph):
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


# ---------- 6 Seiten ----------
CATS = {'imoveis': None, 'imoveis-venda': 'venda', 'imoveis-aluguel': 'aluguel', 'imoveis-terrenos': 'terrenos'}
routes = ['home', 'imoveis', 'imoveis-venda', 'imoveis-aluguel', 'imoveis-terrenos', 'sobre', 'blog', 'contato', 'privacidade'] \
    + ['imovel-' + l['slug'] for l in listings] + ['artigo-' + p['slug'] for p in posts]
urls = []


def pins(ls, c):
    return [{'slug': l['slug'], 'name': l['name'], 'loc': l.get('loc', ''), 'lat': l['lat'], 'lng': l['lng'], 'price': int(l['price']),
             'rent': l['deal'] == 'aluguel', 'img': c['img'](l['imgs'][0], '-xs'), 'url': c['url']('imovel-' + l['slug'])} for l in ls if l.get('lat')]


for lang in LANGS:
    for route in routes:
        c = make_ctx(lang, route)
        t = c['t']
        brand = site['brandFull']
        home = (t['navHome'], c['abs']('home'))
        graph = [org_ld(lang)]
        if route == 'home':
            tpl = 'home.html'
            title, desc = f"{brand} · {t['metaHomeTitle']}", t['metaHome']
            feat = [l for l in listings if l['cat'] != 'terrenos'][:6]
            c.update(featured=feat, pins=pins(listings, c), calc_price=int(next((l['price'] for l in listings if l['deal'] == 'venda'), 1000000)))
            graph += [{'@type': 'WebSite', 'name': brand, 'url': c['abs']('home'), 'inLanguage': HL[lang]},
                      {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': t[f'fq{i}'], 'acceptedAnswer': {'@type': 'Answer', 'text': t[f'fq{i}a']}} for i in range(1, 6)]}]
        elif route in CATS:
            tpl = 'lista.html'
            cat = CATS[route]
            ls = [l for l in listings if (cat is None or l['cat'] == cat)]
            key = {'venda': 'Venda', 'aluguel': 'Aluguel', 'terrenos': 'Terrenos', None: 'All'}[cat]
            title, desc = f"{t['list' + key + 'H']} · {brand}", t['list' + key + 'D']
            c.update(cat=cat, items=ls, h1=t['list' + key + 'H'], lead=t['list' + key + 'D'], pins=pins(ls, c),
                     maxopts=[3000, 5000, 10000, 20000] if cat == 'aluguel' else [500000, 1000000, 2000000, 3000000, 5000000])
            graph += [crumbs_ld([home, (t['navAll'], c['abs']('imoveis'))] + ([(t['list' + key + 'H'], c['abs'](route))] if cat else [])),
                      {'@type': 'ItemList', 'numberOfItems': len(ls), 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': c['abs']('imovel-' + l['slug']), 'name': l['name']} for i, l in enumerate(ls)]}]
        elif route.startswith('imovel-'):
            tpl = 'imovel.html'
            l = next(x for x in listings if x['slug'] == route[7:])
            sim = [x for x in listings if x['slug'] != l['slug'] and x['cat'] == l['cat']]
            sim = sorted(sim, key=lambda x: abs(x['price'] - l['price']))[:3]
            catroute = 'imoveis-' + l['cat']
            catname = t[{'venda': 'navBuy', 'aluguel': 'navRent', 'terrenos': 'navLand'}[l['cat']]]
            title = f"{l['name']}, {l['loc']} · {brand}"
            desc = clip(l['title'][lang] + '. ' + l['desc'][lang].split('\n')[0])
            c.update(msg=f"{t['waInterest']} {l['name']} ({l['ref']}).", l=l, similar=sim, catroute=catroute, catname=catname, pins=pins([l], c), calc_price=int(l['price']))
            graph += [crumbs_ld([home, (catname, c['abs'](catroute)), (l['name'], c['abs'](route))]), listing_ld(l, lang, c)]
        elif route == 'sobre':
            tpl, title, desc = 'sobre.html', f"{t['aboutTitle']} · {brand}", t['aboutMeta']
            graph += [crumbs_ld([home, (t['navAbout'], c['abs'](route))])]
        elif route == 'blog':
            tpl, title, desc = 'blog.html', f"{t['blogH']} · {brand}", t['blogLead']
            graph += [crumbs_ld([home, (t['navGuide'], c['abs'](route))]),
                      {'@type': 'Blog', 'name': t['blogH'], 'url': c['abs'](route), 'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'][lang], 'url': c['abs']('artigo-' + p['slug']), 'datePublished': p['date']} for p in posts]}]
        elif route.startswith('artigo-'):
            tpl = 'artigo.html'
            p = next(x for x in posts if x['slug'] == route[7:])
            title, desc = f"{p['title'][lang]} · {brand}", p['excerpt'][lang]
            rel = [l for l in listings if l['status'] != 'reservado'][:3]
            c.update(p=p, others=[x for x in posts if x['slug'] != p['slug']][:3], rel=rel)
            graph += [crumbs_ld([home, (t['navGuide'], c['abs']('blog')), (p['title'][lang], c['abs'](route))]),
                      {'@type': 'BlogPosting', 'headline': p['title'][lang], 'description': p['excerpt'][lang], 'image': c['imgabs'](p['img']), 'datePublished': p['date'],
                       'dateModified': p.get('updated') or p['date'], 'inLanguage': HL[lang], 'mainEntityOfPage': c['abs'](route),
                       'author': {'@type': 'Person', 'name': p['author']}, 'publisher': {'@id': ORIGIN + BASE + '#org'}}]
        elif route == 'contato':
            tpl, title, desc = 'contato.html', f"{t['contactH']} · {brand}", t['contactMeta']
            graph += [crumbs_ld([home, (t['navContact'], c['abs'](route))])]
        else:
            tpl, title, desc = 'privacidade.html', f"{t['privH']} · {brand}", t['privMeta']
        og = c['imgabs'](c['l']['imgs'][0] if 'l' in c else (c['p']['img'] if 'p' in c else HERO))
        c.update(oglocale={'pt': 'pt_BR', 'en': 'en_US', 'de': 'de_DE'}[lang], title=title, desc=desc, canonical=c['abs'](route), ogimg=og, ld=Markup(ld(graph)), noindex=False,
                 alts=[(HL[x], ORIGIN + BASE + path(route, x)) for x in LANGS], xdef=ORIGIN + BASE + path(route, 'pt'))
        out = env.get_template(tpl).render(**c)
        wr(f'{D}/{path(route, lang)}index.html', out)
        urls.append((route, lang))

c = make_ctx('pt', 'home')
c.update(oglocale='pt_BR', title=site['brandFull'], desc='', canonical='', ogimg='', ld=Markup('{}'), noindex=True, alts=[], xdef='')
wr(f'{D}/404.html', env.get_template('404.html').render(**c))

# ---------- 7 sitemap, robots, llms.txt, IndexNow ----------
today = datetime.date.today().isoformat()
U = lambda r, l: ORIGIN + BASE + path(r, l)
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
for r, l in urls:
    lm = next((p.get('updated') or p.get('date') for p in posts if r == 'artigo-' + p['slug']), None) \
        or next((x['date'] for x in listings if r == 'imovel-' + x['slug']), today)
    sm += f' <url><loc>{U(r, l)}</loc><lastmod>{lm}</lastmod>' + ''.join(f'<xhtml:link rel="alternate" hreflang="{HL[x]}" href="{U(r, x)}"/>' for x in LANGS) + '</url>\n'
wr(f'{D}/sitemap.xml', sm + '</urlset>\n')
bots = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot', 'Perplexity-User', 'Google-Extended', 'Bingbot', 'Applebot-Extended', 'CCBot']
wr(f'{D}/robots.txt', 'User-agent: *\nAllow: /\n\n' + ''.join(f'User-agent: {x}\nAllow: /\n\n' for x in bots) + f'Sitemap: {ORIGIN}{BASE}sitemap.xml\n')

te = {k: (v.get('en') or v.get('pt')) if isinstance(v, dict) else v for k, v in T.items()}
deal = {'venda': 'for sale', 'aluguel': 'for rent'}
x = f"# {site['brandFull']}\n\n> Real estate agency in Pipa and Tibau do Sul (Rio Grande do Norte, Brazil): houses, apartments and land to buy or rent. Service in Portuguese, English and German. Prices in Brazilian reais (BRL).\n\n"
x += f"- Phone / WhatsApp: {site['phone']}\n- Email: {site['email']}\n- Licence: {site['agent']['creci']}\n- Address: {site['address']}\n- Opening hours: {site['hours']['en']}\n- Languages: [Português]({U('home', 'pt')}), [English]({U('home', 'en')}), [Deutsch]({U('home', 'de')})\n\n## Properties\n\n"
for l in listings:
    f = [deal.get(l.get('deal'), ''), l.get('loc', ''), f"BRL {int(l['price']):,}" + (' per month' if l['deal'] == 'aluguel' else ''), 'ref ' + l['ref']]
    if l['beds']:
        f.append(f"{l['beds']} bedroom" + ('s' if l['beds'] != 1 else ''))
    if l['baths']:
        f.append(f"{l['baths']} bathroom" + ('s' if l['baths'] != 1 else ''))
    if l['area']:
        f.append(f"{l['area']:,} m² built")
    if l['lot']:
        f.append(f"{l['lot']:,} m² plot")
    if l['status'] == 'reservado':
        f.append('reserved')
    x += f"- [{l['name']}]({U('imovel-' + l['slug'], 'en')}): {', '.join(v for v in f if v)}. {l['desc']['en'].split(chr(10))[0]} ([Português]({U('imovel-' + l['slug'], 'pt')}), [Deutsch]({U('imovel-' + l['slug'], 'de')}))\n"
x += "\n## Guides\n\n" + ''.join(f"- [{p['title']['en']}]({U('artigo-' + p['slug'], 'en')}): {p['excerpt']['en']}\n" for p in posts)
x += '\n## Frequently asked questions\n\n' + ''.join(f"- **{te['fq' + str(i)]}** {te['fq' + str(i) + 'a']}\n" for i in range(1, 6))
x += f"\n## Pages\n\n- [All properties]({U('imoveis', 'en')})\n- [For sale]({U('imoveis-venda', 'en')})\n- [Rentals]({U('imoveis-aluguel', 'en')})\n- [Land]({U('imoveis-terrenos', 'en')})\n- [About the agency]({U('sobre', 'en')})\n- [Contact]({U('contato', 'en')})\n- [Sitemap]({ORIGIN}{BASE}sitemap.xml)\n"
wr(f'{D}/llms.txt', x)
wr(f'{D}/{INDEXNOW_KEY}.txt', INDEXNOW_KEY)
wr(f'{D}/indexnow.json', json.dumps({'host': ORIGIN.split('//')[1], 'key': INDEXNOW_KEY, 'keyLocation': f'{ORIGIN}{BASE}{INDEXNOW_KEY}.txt', 'urlList': [U(r, l) for r, l in urls]}))
wr(f'{D}/.nojekyll', '')
print('Seiten:', len(urls), '· CSS', len(css) // 1024, 'KB · JS', len(js) // 1024, 'KB')
