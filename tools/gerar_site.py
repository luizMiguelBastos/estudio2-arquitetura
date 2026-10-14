#!/usr/bin/env python3
"""Gera as partes do site que dependem dos dados dos projetos e do domínio.

Uso:  python3 tools/gerar_site.py            (só Python 3, sem dependências)

O que ele gera/atualiza a partir de projetos.json:
  - projetos/<slug>/index.html   uma página estática por projeto (título, descrição,
                                 tags de compartilhamento e dados estruturados próprios)
  - projetos.js                  dados usados pela home (agora com o campo "slug")
  - index.html                   bloco de SEO do <head> e lista de projetos para buscadores
  - projeto.html                 redireciona os links antigos (projeto.html?id=...)
  - sitemap.xml, robots.txt, .htaccess (Hostinger), 404.html
  - img/og/*.jpg                 imagens de compartilhamento (só se o Pillow estiver instalado)

Para trocar o domínio, altere SITE abaixo e rode o script de novo.
"""
import html, json, os, re, unicodedata, datetime

SITE = "https://estudio2arquitetura.com.br"   # domínio definitivo, sem barra no final
INSTAGRAM = "https://www.instagram.com/estudio2arquitetura/"
TELEFONE = "+55-84-99413-4193"
EMAIL = "contato@estudio2arquitetura.com.br"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOJE = datetime.date.today().isoformat()
VER = datetime.date.today().strftime("%Y%m%d")
esc = html.escape
FP = ' fetchpriority="high"'


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def resumo_de(p, limite=155):
    t = p.get("resumo") or (p.get("texto") or [""])[0]
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= limite:
        return t
    corte = t[:limite].rsplit(" ", 1)[0].rstrip(",;:")
    return corte + "…"


def tipo_de(p):
    return {"casas": "Residência", "edificios": "Edifício residencial", "interiores": "Interiores",
            "urbano": "Desenho urbano"}.get(p.get("categoria"), "Projeto")


def cidade_curta(p):
    return (p.get("cidade") or "").replace(", ", "/")


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def card(p, pre):
    if p.get("placeholder") or not p.get("capa"):
        letra = p["nome"].split(" ")[-1][0]
        inner = f'<div class="ph"><b>{esc(letra)}</b>{"Em breve" if p.get("placeholder") else "Fotos em breve"}</div>'
        href = f"{pre}#projetos" if p.get("placeholder") else f'{pre}projetos/{p["slug"]}/'
    else:
        inner = f'<img src="{pre}{p["capa"]}-t.webp" alt="{esc(p["nome"])}" loading="lazy" draggable="false">'
        href = f'{pre}projetos/{p["slug"]}/'
    return (f'<a class="card" href="{href}" draggable="false">{inner}'
            f'<div class="nm">{esc(p["nome"])}<small>{esc(p.get("cat_label",""))} · {esc(p.get("cidade",""))}</small></div></a>')


# ---------------------------------------------------------------- dados
dados = json.load(open(os.path.join(ROOT, "projetos.json"), encoding="utf-8"))
P = dados["projetos"]
for p in P:
    p["slug"] = slugify(p["nome"])
json.dump(dados, open(os.path.join(ROOT, "projetos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(os.path.join(ROOT, "projetos.js"), "w", encoding="utf-8").write(
    "window.PROJETOS=" + json.dumps(dados, ensure_ascii=False) + ";\n")
reais = [p for p in P if not p.get("placeholder") and p.get("fotos")]

ESTUDIO_ID = SITE + "/#estudio"


# ---------------------------------------------------------------- imagens de compartilhamento
def gerar_og():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("Pillow não encontrado: imagens de compartilhamento mantidas como estão.")
        return
    os.makedirs(os.path.join(ROOT, "img", "og"), exist_ok=True)

    def corta(src, dst, y=0.5):
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        W, H = im.size
        alvo = 1200 / 630
        if W / H > alvo:
            w = round(H * alvo); x = (W - w) // 2; im = im.crop((x, 0, x + w, H))
        else:
            h = round(W / alvo); top = round((H - h) * y); im = im.crop((0, top, W, top + h))
        im.resize((1200, 630), Image.LANCZOS).save(dst, "JPEG", quality=82, optimize=True, progressive=True)

    corta(os.path.join(ROOT, "img/hero/agnus.webp"), os.path.join(ROOT, "img/og/home.jpg"), 0.45)
    for p in reais:
        corta(os.path.join(ROOT, p["capa"] + ".webp"), os.path.join(ROOT, f'img/og/{p["slug"]}.jpg'), 0.42)


gerar_og()

# ---------------------------------------------------------------- páginas de projeto
NAV = lambda pre: (f'<header class="nav solid" id="nav"><div class="wrap">\n'
                   f'  <a class="brand" href="{pre}"><i><img src="{pre}img/e2.svg" alt="" width="19" height="22"></i>estudio2arquitetura</a>\n'
                   f'  <nav class="menu"><a href="{pre}#sobre">Sobre</a><a href="{pre}#estudio">Estúdio</a><a href="{pre}#destaques">Destaques</a><a href="{pre}#projetos" class="on">Projetos</a><a href="{pre}#contato">Contato</a></nav>\n'
                   f'  <a class="btn" href="{pre}#contato">Entre em contato</a>\n'
                   f'</div></header>')

SCRIPT_PROJETO = r"""<script>
(function(){
  document.documentElement.classList.add("has-js");
  var $=function(s,c){return (c||document).querySelector(s)},$$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
  $("#yr").textContent=new Date().getFullYear();
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target)}})},{threshold:.1});
  $$(".rv,[data-stagger]").forEach(function(el){io.observe(el)});
  /* lightbox */
  var links=$$("#gal a"),fotos=links.map(function(a){return a.getAttribute("href")}),cur=0,lb=$("#lb"),lbi=$("#lbi"),lbc=$("#lbc");
  function show(i){cur=(i+fotos.length)%fotos.length;lbi.src=fotos[cur];lbi.alt=links[cur].querySelector("img").alt;lbc.textContent=(cur+1)+" / "+fotos.length}
  function open(i){show(i);lb.classList.add("open");document.body.style.overflow="hidden"}
  function close(){lb.classList.remove("open");document.body.style.overflow=""}
  links.forEach(function(a,i){a.onclick=function(e){e.preventDefault();open(i)}});
  $("#lbx").onclick=close;$("#lbl").onclick=function(){show(cur-1)};$("#lbr").onclick=function(){show(cur+1)};
  lb.addEventListener("click",function(e){if(e.target===lb)close()});
  addEventListener("keydown",function(e){if(!lb.classList.contains("open"))return;if(e.key==="Escape")close();if(e.key==="ArrowRight")show(cur+1);if(e.key==="ArrowLeft")show(cur-1)});
  /* reel drag */
  var reel=$("#reel"),down=false,sx=0,sl=0,moved=false;
  reel.addEventListener("pointerdown",function(e){if(e.pointerType!=="mouse")return;down=true;moved=false;sx=e.clientX;sl=reel.scrollLeft;reel.classList.add("drag")});
  addEventListener("pointermove",function(e){if(!down)return;var dx=e.clientX-sx;if(Math.abs(dx)>4)moved=true;reel.scrollLeft=sl-dx});
  addEventListener("pointerup",function(){if(!down)return;down=false;reel.classList.remove("drag")});
  reel.addEventListener("click",function(e){if(moved){e.preventDefault();e.stopPropagation()}},true);
})();
</script>"""


def head_comum(pre, title, desc, url, og_img, og_type="website", extra=""):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0A0C0A">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Estúdio2 Arquitetura">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=Inter:wght@300;400;500&display=swap">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{pre}favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="{pre}apple-touch-icon.png">
<link rel="stylesheet" href="{pre}shared.css?v={VER}">
{extra}"""


os.makedirs(os.path.join(ROOT, "projetos"), exist_ok=True)
for p in reais:
    pre = "../../"
    url = f'{SITE}/projetos/{p["slug"]}/'
    cid = cidade_curta(p)
    title = f'{p["nome"]} · {tipo_de(p)} em {cid} | Estúdio2 Arquitetura'
    desc = resumo_de(p)
    og = f'{SITE}/img/og/{p["slug"]}.jpg'
    partes = p["nome"].split(" ")
    h1 = (esc(" ".join(partes[:-1])) + " <em>" + esc(partes[-1]) + "</em>") if len(partes) > 1 else esc(p["nome"])
    k = esc(p.get("cat_label", "")) + " · " + esc(p.get("cidade", "")) + (" · " + esc(p["ano"]) if p.get("ano") else "")
    ficha = []
    for rot, val in (("Área", p.get("area")), ("Ano", p.get("ano")), ("Local", p.get("cidade")), ("Status", p.get("status")),
                     ("Tipologia", (p.get("tipologia") or "").split(" · ")[0])):
        if val:
            ficha.append(f"<div><b>{esc(val)}</b><span>{rot}</span></div>")
    n = len(p["fotos"])
    gal = "".join(
        f'<a href="{pre}{f}.webp"><img src="{pre}{f}{"" if i == 0 else "-t"}.webp" alt="{esc(p["nome"])}, {esc(cid)}: foto {i + 1} de {n}" '
        f'loading="{"eager" if i < 3 else "lazy"}"{FP if i == 0 else ""}></a>'
        for i, f in enumerate(p["fotos"]))
    corpo = "".join(f"<p>{esc(t)}</p>" for t in p.get("texto") or [])
    prog = f'<small>Programa</small><p>{esc(p["programa"])}</p>' if p.get("programa") else ""
    lede = f'<p class="lede">{esc(p["resumo"])}</p>' if p.get("resumo") else ""
    outros = "".join(card(o, pre) for o in P if o is not p)
    dados_ld = ld({"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Estúdio2 Arquitetura", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Projetos", "item": SITE + "/#projetos"},
            {"@type": "ListItem", "position": 3, "name": p["nome"], "item": url}]},
        {"@type": "CreativeWork", "@id": url + "#projeto", "name": p["nome"], "description": desc, "url": url,
         "genre": tipo_de(p), "inLanguage": "pt-BR",
         **({"dateCreated": p["ano"]} if p.get("ano") else {}),
         "image": [f"{SITE}/{f}.webp" for f in p["fotos"][:6]],
         "creator": {"@id": ESTUDIO_ID},
         "locationCreated": {"@type": "Place", "address": {"@type": "PostalAddress",
                             "addressLocality": (p.get("cidade") or "").split(",")[0], "addressRegion": "RN", "addressCountry": "BR"}}}]})
    page = head_comum(pre, title, desc, url, og, "article",
                      f'<link rel="stylesheet" href="{pre}projeto.css?v={VER}">\n{dados_ld}\n') + f"""</head>
<body>
{NAV(pre)}

<main>
<section class="pj"><div class="wrap">
  <a class="back" href="{pre}#projetos">← Voltar aos projetos</a>
  <div class="pj-head rv"><p class="k">{k}</p><h1>{h1}</h1>{lede}</div>
  <div class="ficha">{"".join(ficha)}</div>
  <div class="gal" id="gal" data-stagger>{gal}</div>
  <div class="txt"><h2 class="rv">Sobre o <em>projeto</em></h2><div><div class="body rv">{corpo}</div><div class="prog rv">{prog}</div></div></div>
</div></section>
<section class="outros"><div class="wrap">
  <div class="head rv"><div><p class="k">Portfólio</p><h2 style="margin-top:10px">Outros <em>projetos</em></h2></div><span class="hint"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M3 12h18M15 6l6 6-6 6"/></svg>Arraste</span></div>
  <div class="reel" id="reel">{outros}</div>
</div></section>
</main>
<footer class="foot"><div class="wrap"><span>© <span id="yr">2026</span> Estúdio2 Arquitetura · Fabrício Lira</span><span>Av. das Tulipas, 1914 · Natal, RN</span></div></footer>

<div class="lb" id="lb"><button class="x" id="lbx" aria-label="Fechar">×</button><button class="n l" id="lbl" aria-label="Anterior">‹</button><img id="lbi" alt=""><button class="n r" id="lbr" aria-label="Próxima">›</button><span class="c" id="lbc"></span></div>

{SCRIPT_PROJETO}
</body>
</html>
"""
    d = os.path.join(ROOT, "projetos", p["slug"])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

# remove páginas de projetos que não existem mais
validos = {p["slug"] for p in reais}
for nome in os.listdir(os.path.join(ROOT, "projetos")):
    caminho = os.path.join(ROOT, "projetos", nome, "index.html")
    if nome not in validos and os.path.isfile(caminho):
        os.remove(caminho); os.rmdir(os.path.dirname(caminho))

# ---------------------------------------------------------------- home: bloco de SEO e lista para buscadores
home_title = "Estúdio2 Arquitetura | Arquiteto em Natal e Parnamirim · Fabrício Lira"
home_desc = ("Escritório de arquitetura em Natal/RN liderado pelo arquiteto Fabrício Lira: casas de alto padrão, "
             "interiores e desenho urbano em Natal e Parnamirim.")
home_ld = ld({"@context": "https://schema.org", "@graph": [
    {"@type": ["LocalBusiness", "ProfessionalService"], "@id": ESTUDIO_ID, "name": "Estúdio2 Arquitetura",
     "alternateName": "estudio2arquitetura", "description": home_desc, "url": SITE + "/",
     "logo": SITE + "/apple-touch-icon.png", "image": SITE + "/img/og/home.jpg",
     "telephone": TELEFONE, "email": EMAIL,
     "address": {"@type": "PostalAddress", "streetAddress": "Av. das Tulipas, 1914 - Capim Macio",
                 "addressLocality": "Natal", "addressRegion": "RN", "postalCode": "59078-220", "addressCountry": "BR"},
     "areaServed": ["Natal", "Parnamirim", "Rio Grande do Norte"],
     "knowsAbout": ["Arquitetura residencial", "Casas de alto padrão", "Design de interiores", "Desenho urbano", "Gestão de obras"],
     "founder": {"@id": SITE + "/#fabricio"}, "sameAs": [INSTAGRAM]},
    {"@type": "Person", "@id": SITE + "/#fabricio", "name": "Fabrício Lira", "jobTitle": "Arquiteto e urbanista",
     "image": SITE + "/img/fabricio.webp", "worksFor": {"@id": ESTUDIO_ID}},
    {"@type": "WebSite", "@id": SITE + "/#site", "url": SITE + "/", "name": "Estúdio2 Arquitetura",
     "inLanguage": "pt-BR", "publisher": {"@id": ESTUDIO_ID}}]})
seo = head_comum("", home_title, home_desc, SITE + "/", SITE + "/img/og/home.jpg", extra=home_ld + "\n")
seo = seo.split("<head>\n", 1)[1]  # só o conteúdo do <head>

idx_path = os.path.join(ROOT, "index.html")
idx = open(idx_path, encoding="utf-8").read()
ini, fim = "<!--SEO-->", "<!--/SEO-->"
if ini not in idx:  # primeira execução: troca o início do <head> até a folha de estilos pelo bloco gerado
    a = idx.index("<head>\n") + len("<head>\n")
    b = idx.index("<script src=\"projetos.js")
    idx = idx[:a] + ini + "\n" + fim + "\n" + idx[b:]
idx = re.sub(re.escape(ini) + r".*?" + re.escape(fim), lambda m: ini + "\n" + seo + fim, idx, flags=re.S)
idx = re.sub(r'<script src="projetos\.js(\?v=\d+)?"></script>', f'<script src="projetos.js?v={VER}"></script>', idx)
lista = "".join(f'<li><a href="projetos/{p["slug"]}/">{esc(p["nome"])} · {esc(p.get("cidade", ""))}</a></li>' for p in reais)
bloco = f'<noscript><ul class="ns-list">{lista}</ul></noscript>'
ini2, fim2 = "<!--LISTA-PROJETOS-->", "<!--/LISTA-PROJETOS-->"
if ini2 in idx:
    idx = re.sub(re.escape(ini2) + r".*?" + re.escape(fim2), lambda m: ini2 + bloco + fim2, idx, flags=re.S)
else:
    print("Aviso: marcador LISTA-PROJETOS não encontrado no index.html")
open(idx_path, "w", encoding="utf-8").write(idx)

# ---------------------------------------------------------------- links antigos
mapa = {p["id"]: p["slug"] for p in reais}
open(os.path.join(ROOT, "projeto.html"), "w", encoding="utf-8").write(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<title>Estúdio2 Arquitetura</title>
<script>(function(){{var m={json.dumps(mapa)},id=new URLSearchParams(location.search).get("id");location.replace(m[id]?"projetos/"+m[id]+"/":"./#projetos")}})();</script>
</head><body><a href="./#projetos">Ver projetos</a></body></html>
""")

# ---------------------------------------------------------------- 404
open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>Página não encontrada · Estúdio2 Arquitetura</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;1,400&family=Inter:wght@400;500&display=swap">
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#0A0C0A;color:#E6E3DA;font:400 15px/1.6 Inter,Arial,sans-serif;text-align:center;padding:24px}}
h1{{font:400 clamp(40px,7vw,72px)/1 "Cormorant Garamond",Georgia,serif;margin:0 0 16px}}h1 em{{color:#A3B18A}}a{{color:#DAD7CD;letter-spacing:.2em;text-transform:uppercase;font-size:11px;border:1px solid rgba(218,215,205,.3);padding:14px 22px;display:inline-block;margin-top:22px;text-decoration:none}}</style>
</head><body><div><img src="/img/e2.svg" alt="" width="38" height="44"><h1>Página <em>não encontrada</em></h1><p>O endereço pode ter mudado. Os projetos continuam todos no portfólio.</p><a href="/">Ir para o início</a></div></body></html>
""")

# ---------------------------------------------------------------- sitemap e robots
urls = [(SITE + "/", ["img/og/home.jpg", "img/fabricio.webp"])] + [
    (f'{SITE}/projetos/{p["slug"]}/', [f + ".webp" for f in p["fotos"]]) for p in reais]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
for u, imgs in urls:
    sm.append(f"  <url><loc>{u}</loc><lastmod>{HOJE}</lastmod>" +
              "".join(f"<image:image><image:loc>{SITE}/{i}</image:loc></image:image>" for i in imgs) + "</url>")
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

# ---------------------------------------------------------------- .htaccess (Hostinger)
redir = "\n".join(
    f"RewriteCond %{{QUERY_STRING}} (^|&)id={pid}(&|$)\nRewriteRule ^projeto\\.html$ /projetos/{slug}/? [R=301,L]"
    for pid, slug in mapa.items())
open(os.path.join(ROOT, ".htaccess"), "w", encoding="utf-8").write(f"""# Estúdio2 Arquitetura · configuração para a Hostinger (gerado por tools/gerar_site.py)
Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_rewrite.c>
RewriteEngine On

# Sempre HTTPS e sem "www"
RewriteCond %{{HTTPS}} off [OR]
RewriteCond %{{HTTP_HOST}} ^www\\. [NC]
RewriteCond %{{HTTP_HOST}} ^(?:www\\.)?(.+)$ [NC]
RewriteRule ^ https://%1%{{REQUEST_URI}} [R=301,L]

# Links antigos (projeto.html?id=...) para as páginas novas
{redir}

# index.html no endereço vira a pasta (evita conteúdo duplicado)
RewriteCond %{{THE_REQUEST}} \\s/+(.*/)?index\\.html[\\s?] [NC]
RewriteRule ^(.*/)?index\\.html$ /$1 [R=301,L]
</IfModule>

# Compressão
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css application/javascript text/javascript application/json image/svg+xml application/xml text/xml text/plain
</IfModule>

# Cache: imagens por 1 ano; CSS/JS por 1 mês (os links têm ?v=data, então atualizam na hora); HTML sempre conferido
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType image/webp "access plus 1 year"
ExpiresByType image/jpeg "access plus 1 year"
ExpiresByType image/png "access plus 1 year"
ExpiresByType image/svg+xml "access plus 1 year"
ExpiresByType text/css "access plus 1 month"
ExpiresByType application/javascript "access plus 1 month"
ExpiresByType text/javascript "access plus 1 month"
ExpiresByType text/html "access plus 0 seconds"
</IfModule>
<IfModule mod_headers.c>
<FilesMatch "\\.(html)$">
Header set Cache-Control "no-cache"
</FilesMatch>
Header always set X-Content-Type-Options "nosniff"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
""")

print(f"ok · {len(reais)} páginas de projeto · domínio {SITE}")
