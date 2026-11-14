#!/usr/bin/env python3
"""Baut die statische Website nach dist/: jede Seite als eigene HTML-Datei (pt, en, de),
Bilder als WebP in drei Größen, dazu sitemap.xml, robots.txt, llms.txt und IndexNow-Schlüssel.
Aufruf: python3 build.py   (SITE_ORIGIN und SITE_BASE kommen aus der Umgebung)"""
import os,re,json,glob,shutil,hashlib,html,threading,datetime,http.server,functools
from PIL import Image
from playwright.sync_api import sync_playwright
ORIGIN=os.environ.get('SITE_ORIGIN','https://gewarkes.github.io').rstrip('/').lower()
BASE=os.environ.get('SITE_BASE','/enseada-imoveis/')
INDEXNOW_KEY='7c1e5a9d3b2f4e6a8c0d1f2b3a4c5d6e'
LANGS=['pt','en','de'];HL={'pt':'pt-BR','en':'en','de':'de'}
D='dist';shutil.rmtree(D,ignore_errors=True);os.makedirs(D+'/assets');os.makedirs(D+'/img')
rd=lambda f:open(f,encoding='utf-8').read()
def wr(f,s):
    os.makedirs(os.path.dirname(f) or '.',exist_ok=True);open(f,'w',encoding='utf-8').write(s)

# 1 content
HERO0=(re.search(r"heroPoster:'([^']+)'",open('src/core.js',encoding='utf-8').read()) or [0,''])[1]
slug=lambda s:re.sub(r'[^a-z0-9]+','-',str(s).lower()).strip('-')
par=lambda v:[x.strip() for x in re.split(r'\n\s*\n',v) if x.strip()] if isinstance(v,str) else (v or [])
listings=sorted([json.loads(rd(f)) for f in glob.glob('content/imoveis/*.json')],key=lambda x:(x.get('ordem') or 999,x.get('slug','')))
posts=sorted([json.loads(rd(f)) for f in glob.glob('content/blog/*.json')],key=lambda x:x.get('date',''),reverse=True)
tri=lambda v:v if isinstance(v,dict) else {'pt':v or '','en':v or '','de':v or ''}
def fill(d):
    d=tri(d);base=d.get('pt') or d.get('en') or d.get('de') or ''
    return {k:(d.get(k) or base) for k in LANGS}
for l in listings:
    l['slug']=slug(l.get('slug') or l['name']);l['imgs']=l.get('imgs') or [HERO0];l['desc']=fill(l.get('desc'));l.setdefault('imgs',[]);l.setdefault('feats',[]);l.setdefault('dist',{})
    for k in ('price','beds','baths','area','lot','year','beach'):l[k]=l.get(k) or 0
for p in posts:
    p['slug']=slug(p.get('slug') or tri(p['title'])['pt'])
    for k in ('cat','title','excerpt'):p[k]=fill(p.get(k))
    b=p.get('body');b=b if isinstance(b,dict) else {'pt':b};b={k:par(b.get(k)) for k in LANGS};bb=b['pt'] or b['en'] or b['de'];p['body']={k:(b[k] or bb) for k in LANGS}
    p['img']=p.get('img') or HERO0

# 2 photos -> webp in three widths
n=0
for f in sorted(glob.glob('content/fotos/*')):
    stem=slug(os.path.splitext(os.path.basename(f))[0])
    try:im=Image.open(f).convert('RGB')
    except Exception as e:print('skip',f,e);continue
    for suf,w in (('',1400),('-s',760),('-xs',480)):
        o=f'{D}/img/{stem}{suf}.webp'
        if suf=='' and f.endswith('.webp') and im.width<=w:shutil.copy(f,o);continue
        j=im.copy();j.thumbnail((w,w*2));j.save(o,quality=60,method=6)
    n+=1
print('photos',n)

# 3 css + js
css="@font-face{font-family:'Hanken Grotesk';font-style:normal;font-weight:100 900;font-display:swap;src:url(hanken-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}\n@font-face{font-family:'Hanken Grotesk';font-style:normal;font-weight:100 900;font-display:swap;src:url(hanken-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}\n"+rd('src/base.css')
js='window.__DATA='+json.dumps({'listings':listings,'posts':posts},ensure_ascii=False,separators=(',',':'))+';\n'+rd('src/core.js')
order=['chrome','home','imoveis','imovel','sobre','blog','artigo','contato','publicar']
key=lambda f:(order.index(os.path.basename(f)[:-5]) if os.path.basename(f)[:-5] in order else 99)
for f in sorted(glob.glob('src/views/*.html'),key=key):
    s=rd(f)
    for m in re.findall(r'<style>(.*?)</style>',s,re.S):css+='\n'+m
    for m in re.findall(r'<script>(.*?)</script>',s,re.S):js+='\n'+m
js+='\nboot();'
css=re.sub(r'/\*.*?\*/','',css,flags=re.S);css=re.sub(r'\n\s*\n','\n',css)
hc=hashlib.md5(css.encode()).hexdigest()[:8];hj=hashlib.md5(js.encode()).hexdigest()[:8]
wr(f'{D}/assets/site.{hc}.css',css);wr(f'{D}/assets/site.{hj}.js',js)
for f in ('hanken-latin.woff2','hanken-latin-ext.woff2'):shutil.copy('src/'+f,f'{D}/assets/{f}')

# 4 pages
def path(route,lang):
    pre='' if lang=='pt' else lang+'/'
    if route=='home':return pre
    for a,b in (('imoveis-','imoveis/'),('imovel-','imovel/'),('artigo-','blog/')):
        if route.startswith(a):return pre+b+route[len(a):]+'/'
    return pre+route+'/'
routes=['home','imoveis','imoveis-venda','imoveis-aluguel','imoveis-terrenos','sobre','blog','contato','publicar']+['imovel-'+l['slug'] for l in listings]+['artigo-'+p['slug'] for p in posts]
NOINDEX={'publicar'}
m=re.search(r"heroPoster:'([^']+)'",rd('src/core.js'));HERO=m.group(1) if m else ''
ik=lambda k:re.sub(r'^(\d+)h$',r'\1',slug(os.path.splitext(os.path.basename(str(k)))[0]))
def ogimg(route):
    k=HERO
    if route.startswith('imovel-'):
        l=[x for x in listings if x['slug']==route[7:]];k=(l and l[0]['imgs'] and l[0]['imgs'][0]) or HERO
    if route.startswith('artigo-'):
        p=[x for x in posts if x['slug']==route[7:]];k=(p and p[0].get('img')) or HERO
    return f'{ORIGIN}{BASE}img/{ik(k)}.webp'
e=lambda s:html.escape(str(s),quote=True)
def page(route,lang,r):
    url=ORIGIN+BASE+path(route,lang) if route else ''
    head=f'<title>{e(r["title"])}</title>\n<meta name="description" id="md" content="{e(r["desc"])}">\n'
    if route:
        head+=f'<link rel="canonical" href="{url}">\n'+''.join(f'<link rel="alternate" hreflang="{HL[x]}" href="{ORIGIN+BASE+path(route,x)}">\n' for x in LANGS)+f'<link rel="alternate" hreflang="x-default" href="{ORIGIN+BASE+path(route,"pt")}">\n'
        head+=f'<meta property="og:type" content="website">\n<meta property="og:title" content="{e(r["title"])}">\n<meta property="og:description" content="{e(r["desc"])}">\n<meta property="og:url" content="{url}">\n<meta property="og:image" content="{ogimg(route)}">\n<meta property="og:locale" content="{HL[lang].replace("-","_")}">\n<meta name="twitter:card" content="summary_large_image">\n'
    if route in NOINDEX or not route:head+='<meta name="robots" content="noindex">\n'
    if route=='home':head+=f'<link rel="preload" as="image" href="{BASE}img/{ik(HERO)}.webp" imagesrcset="{BASE}img/{ik(HERO)}-s.webp 760w, {BASE}img/{ik(HERO)}.webp 1400w" imagesizes="100vw" fetchpriority="high">\n'
    st={'base':BASE,'origin':ORIGIN,'lang':lang,'route':route or None}
    redir=REDIR if (route=='home' and lang=='pt') else ''
    return f'''<!DOCTYPE html>
<html lang="{HL[lang]}">
<head>
<meta charset="utf-8">
{redir}<meta name="viewport" content="width=device-width,initial-scale=1">
{head}<link rel="preload" as="font" type="font/woff2" href="{BASE}assets/hanken-latin.woff2" crossorigin>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23101514'/%3E%3Ccircle cx='16' cy='16' r='5' fill='%23ef4b2b'/%3E%3C/svg%3E">
<link rel="stylesheet" href="{BASE}assets/site.{hc}.css">
<script type="application/ld+json" id="ld">{r["ld"]}</script>
<script>window.__ST={'window.__ST||' if not route else ''}{json.dumps(st)}</script>
<script defer src="{BASE}assets/site.{hj}.js"></script>
</head>
<body>
<header id="nav">{r["nav"]}</header>
<main id="main">{r["main"]}</main>
<footer id="foot">{r["foot"]}</footer>
<div class="demo" id="demo">{e(r["demo"])}</div>
</body>
</html>
'''
# first visit on the Portuguese start page: send German and English browsers to their language, before anything else loads
REDIR='<script>try{if(!localStorage.getItem("lang")){var n=(navigator.language||"").toLowerCase(),t=n.indexOf("de")==0?"de":n.indexOf("en")==0?"en":"";localStorage.setItem("lang",t||"pt");if(t&&!/bot|crawl|spider|slurp/i.test(navigator.userAgent))location.replace("'+BASE+'"+t+"/")}}catch(e){}</script>\n'
empty={'title':'Enseada Imóveis','desc':'','ld':'{}','nav':'','main':'','foot':'','demo':''}
wr(f'{D}/404.html',page('', 'pt',empty))   # also the fallback for addresses that have no file

class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self,p):
        p=p.split('?')[0]
        if p.startswith(BASE):p='/'+p[len(BASE):]
        return super().translate_path(p)
    def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=D));port=srv.server_address[1]
srv.handle_error=lambda *a:None
threading.Thread(target=srv.serve_forever,daemon=True).start()
urls=[];errs=[]
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':900})
    ctx.route(lambda u:not u.startswith('http://127.0.0.1'),lambda r:r.abort())
    pg=ctx.new_page();pg.on('pageerror',lambda x:errs.append(str(x)))
    for lang in LANGS:
        for route in routes:
            st={'base':BASE,'origin':ORIGIN,'lang':lang,'route':route,'snap':1}
            pg.close();pg=ctx.new_page();pg.on('pageerror',lambda x:errs.append(str(x)))
            pg.add_init_script('window.__ST='+json.dumps(st))
            pg.goto(f'http://127.0.0.1:{port}{BASE}404.html',wait_until='load')
            try:pg.wait_for_function('document.getElementById("main").children.length>0',timeout=8000)
            except Exception:print('FAIL',lang,route,errs[:3]);raise SystemExit(1)
            r=pg.evaluate('()=>({title:document.title,desc:document.getElementById("md").content,ld:document.getElementById("ld").textContent,nav:document.getElementById("nav").innerHTML,main:document.getElementById("main").innerHTML,foot:document.getElementById("foot").innerHTML,demo:document.getElementById("demo").textContent})')
            r['ld']=r['ld'].replace('</','<\\/')
            wr(f'{D}/{path(route,lang)}index.html',page(route,lang,r))
            if route not in NOINDEX:urls.append((route,lang))
    b.close()
srv.shutdown()
if errs:print('PAGE ERRORS',errs[:5]);raise SystemExit(1)

# 5 sitemap, robots, llms.txt, IndexNow
today=datetime.date.today().isoformat();U=lambda r,l:ORIGIN+BASE+path(r,l)
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
for r,l in urls:
    sm+=f' <url><loc>{U(r,l)}</loc><lastmod>{today}</lastmod>'+''.join(f'<xhtml:link rel="alternate" hreflang="{HL[x]}" href="{U(r,x)}"/>' for x in LANGS)+'</url>\n'
wr(f'{D}/sitemap.xml',sm+'</urlset>\n')
bots=['GPTBot','OAI-SearchBot','ChatGPT-User','ClaudeBot','Claude-SearchBot','Claude-User','PerplexityBot','Perplexity-User','Google-Extended','Bingbot','Applebot-Extended','CCBot']
wr(f'{D}/robots.txt','User-agent: *\nAllow: /\n\n'+''.join(f'User-agent: {x}\nAllow: /\n\n' for x in bots)+f'Sitemap: {ORIGIN}{BASE}sitemap.xml\n')
core=rd('src/core.js');g=lambda k:(re.search(k+r":'([^']*)'",core) or [0,''])[1]
deal={'venda':'for sale','aluguel':'for rent'}
t=f"# {g('brandFull') or 'Enseada Imóveis'}\n\n> Real estate agency in Pipa and Tibau do Sul (Rio Grande do Norte, Brazil): houses, apartments and land to buy or rent. Service in Portuguese, English and German. Prices in Brazilian reais (BRL).\n\n"
t+=f"- Phone / WhatsApp: {g('phone')}\n- Email: {g('email')}\n- Licence: {g('creci')}\n- Languages: [Português]({U('home','pt')}), [English]({U('home','en')}), [Deutsch]({U('home','de')})\n\n## Properties\n\n"
for l in listings:
    f=[deal.get(l.get('deal'),l.get('deal','')),l.get('loc',''),f"BRL {int(l['price']):,}"+(' per month' if l.get('deal')=='aluguel' else '')]
    if l['beds']:f.append(f"{l['beds']} bedrooms")
    if l['area']:f.append(f"{l['area']} m² built")
    if l['lot']:f.append(f"{l['lot']} m² plot")
    t+=f"- [{l['name']}]({U('imovel-'+l['slug'],'en')}): {', '.join(x for x in f if x)}. {l['desc']['en']}\n"
t+="\n## Guides\n\n"+''.join(f"- [{p['title']['en']}]({U('artigo-'+p['slug'],'en')}): {p['excerpt']['en']}\n" for p in posts)
t+=f"\n## Pages\n\n- [All properties]({U('imoveis','en')})\n- [Land]({U('imoveis-terrenos','en')})\n- [Rentals]({U('imoveis-aluguel','en')})\n- [About the agency]({U('sobre','en')})\n- [Contact]({U('contato','en')})\n- [Sitemap]({ORIGIN}{BASE}sitemap.xml)\n"
wr(f'{D}/llms.txt',t)
wr(f'{D}/{INDEXNOW_KEY}.txt',INDEXNOW_KEY)
wr(f'{D}/indexnow.json',json.dumps({'host':ORIGIN.split('//')[1],'key':INDEXNOW_KEY,'keyLocation':f'{ORIGIN}{BASE}{INDEXNOW_KEY}.txt','urlList':[U(r,l) for r,l in urls]}))
wr(f'{D}/.nojekyll','')
print('pages',len(urls)+len(LANGS)*len(NOINDEX),'css',len(css)//1024,'KB js',len(js)//1024,'KB')
