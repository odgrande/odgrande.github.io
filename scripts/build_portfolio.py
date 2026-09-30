from __future__ import annotations
import json, re, shutil
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"assets"
SOURCE=ASSETS/"Odunayo Portfolio Assets"
SITE=ROOT/"site"
CONFIG=json.loads((ROOT/"scripts/site_config.json").read_text())

# Non-project buckets that live directly under assets/ or under the
# authoritative "Odunayo Portfolio Assets" folder. These are handled by
# personal_images()/awards()/certificates(), never treated as projects, and
# the deprecated slugified "projects" collection is never scanned.
NON_PROJECT_DIRS={"projects","credentials","personal","odunayo portfolio assets","certifications","personal images","personal videos","theme"}

IMG_EXT={".jpg",".jpeg",".png",".webp",".gif",".avif",".svg"}
VID_EXT={".mp4",".webm",".mov",".m4v",".ogg"}

def esc(v):
    return str(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")

def slugify(s):
    slug=re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
    return "borrowacam-project" if slug=="borrowacamera-project" else slug

def path_url(*parts):
    return "/"+"/".join(quote(str(x)) for x in parts)

def meta(slug, folder=None):
    m=dict(CONFIG["projects"].get(slug,{}))
    if folder:
        for name in ("project.json","meta.json"):
            f=folder/name
            if f.exists():
                try:m.update(json.loads(f.read_text()))
                except Exception:pass
    m.setdefault("title"," ".join(x.capitalize() for x in slug.split("-")))
    m.setdefault("client",m["title"]);m.setdefault("category","Project Archive")
    m.setdefault("services",["Web / Digital"]);m.setdefault("year","Archive")
    m.setdefault("description","Project archive entry.")
    m.setdefault("featured",False);m["slug"]=slug
    return m

def _file_count(d):
    return sum(1 for p in d.rglob("*") if p.is_file())

def discover_project_dirs():
    """Discover project asset folders, preferring the top-level copy.

    A project folder can exist both directly under assets/<name>/ and inside
    the older assets/Odunayo Portfolio Assets/ mirror. The top-level copy is
    where new/renamed/edited project folders land, while the mirror is a
    legacy bulk-import that is sometimes stale or emptied out, so it only
    fills in a project that has no top-level copy at all (or whose top-level
    copy is empty). The deprecated slugified assets/projects/ collection is
    never consulted.
    """
    found={}
    for base in (SOURCE,ASSETS):
        if not base.exists():continue
        for d in base.iterdir():
            if not d.is_dir() or d.name.casefold() in NON_PROJECT_DIRS:continue
            slug=slugify(d.name)
            if slug not in found or _file_count(d)>_file_count(found[slug]):
                found[slug]=d
    return found

def source_for(slug):
    return discover_project_dirs().get(slug)

def scan_projects():
    found=discover_project_dirs()
    projects=[]
    for slug in CONFIG["projects"]:
        d=found.get(slug)
        m=meta(slug,d);m["images"]=[];m["videos"]=[]
        if d:
            files=[p for p in d.rglob("*") if p.is_file() and p.name not in {"project.json","meta.json"}]
            m["images"]=[path_url("assets","projects",slug,*p.relative_to(d).parts) for p in files if p.suffix.lower() in IMG_EXT]
            m["videos"]=[path_url("assets","projects",slug,*p.relative_to(d).parts) for p in files if p.suffix.lower() in VID_EXT]
        projects.append(m)
    known=set(CONFIG["projects"])
    for slug,d in found.items():
        if slug not in known:
            m=meta(slug,d);files=[p for p in d.rglob("*") if p.is_file()]
            m["images"]=[path_url("assets","projects",slug,*p.relative_to(d).parts) for p in files if p.suffix.lower() in IMG_EXT]
            m["videos"]=[path_url("assets","projects",slug,*p.relative_to(d).parts) for p in files if p.suffix.lower() in VID_EXT]
            projects.append(m)
    order={s:i for i,s in enumerate(CONFIG["featuredOrder"])}
    projects.sort(key=lambda p:(0 if p.get("featured") else 1,order.get(p["slug"],999),p["title"].lower()))
    return projects

def copy_assets():
    if SITE.exists():shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    target=SITE/"assets"/"projects";target.mkdir(parents=True)
    selected={}
    for p in scan_projects():
        d=source_for(p["slug"])
        if d: selected[p["slug"]]=d
    for slug,d in selected.items():shutil.copytree(d,target/slug,dirs_exist_ok=True)
    pi=resolve_dir("Personal images")
    pv=resolve_dir("Personal Videos")
    cert=resolve_dir("Certifications")
    if pi.exists():shutil.copytree(pi,SITE/"assets"/"personal"/"images",dirs_exist_ok=True)
    if pv.exists():shutil.copytree(pv,SITE/"assets"/"personal"/"videos",dirs_exist_ok=True)
    award_src=award_dir()
    if award_src and award_src.exists():shutil.copytree(award_src,SITE/"assets"/"credentials"/"awards",dirs_exist_ok=True)
    if cert.exists():shutil.copytree(cert,SITE/"assets"/"credentials"/"certificates",dirs_exist_ok=True)
    theme=ASSETS/"theme"
    if theme.exists():shutil.copytree(theme,SITE/"assets"/"theme",dirs_exist_ok=True)
    public=ROOT/"public"
    for n in ("favicon.svg","og-image.png","odunayo-bolarinwa-portfolio.pdf"):
        f=public/n
        if f.exists():shutil.copy2(f,SITE/n)
    (SITE/"assets"/"css").mkdir(parents=True);(SITE/"assets"/"js").mkdir(parents=True)
    shutil.copy2(ROOT/"scripts"/"styles.css",SITE/"assets"/"css"/"styles.css")
    shutil.copy2(ROOT/"scripts"/"script.js",SITE/"assets"/"js"/"script.js")

# ---------- shell / chrome ----------

def head(title,desc,canonical):
    return f'''<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Odunayo Bolarinwa</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://odgrande.github.io{canonical}">
<meta property="og:title" content="{esc(title)} · Odunayo Bolarinwa"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="https://odgrande.github.io/og-image.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/css/styles.css"></head>'''

NAV_LINKS=[("HOME","/"),("WORKS","/works/"),("ABOUT","/about/"),("CREDENTIALS","/credentials/"),("CONTACT","/contact/")]

def nav():
    desktop="".join(f'<li><a href="{u}">{i+1}. {t}</a></li>' for i,(t,u) in enumerate(NAV_LINKS))
    mobile="".join(f'<li><a href="{u}">{t}</a></li>' for t,u in NAV_LINKS)
    close_icon='<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24"><path fill="#ffffff" d="M9 16h2V8H9v8Zm4 0h2V8h-2v8Zm-1 6q-2.075 0-3.9-.788t-3.175-2.137q-1.35-1.35-2.137-3.175T2 12q0-2.075.788-3.9t2.137-3.175q1.35-1.35 3.175-2.137T12 2q2.075 0 3.9.788t3.175 2.137q1.35 1.35 2.138 3.175T22 12q0 2.075-.788 3.9t-2.137 3.175q-1.35 1.35-3.175 2.138T12 22Zm0-2q3.35 0 5.675-2.325T20 12q0-3.35-2.325-5.675T12 4Q8.65 4 6.325 6.325T4 12q0 3.35 2.325 5.675T12 20Zm0-8Z"/></svg>'
    menu_icon='<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24"><path fill="#ffffff" d="m9.5 16.5l7-4.5l-7-4.5v9ZM12 22q-2.075 0-3.9-.788t-3.175-2.137q-1.35-1.35-2.137-3.175T2 12q0-2.075.788-3.9t2.137-3.175q1.35-1.35 3.175-2.137T12 2q2.075 0 3.9.788t3.175 2.137q1.35 1.35 2.138 3.175T22 12q0 2.075-.788 3.9t-2.137 3.175q-1.35 1.35-3.175 2.138T12 22Zm0-2q3.35 0 5.675-2.325T20 12q0-3.35-2.325-5.675T12 4Q8.65 4 6.325 6.325T4 12q0 3.35 2.325 5.675T12 20Zm0-8Z"/></svg>'
    return f'''<nav class="nav"><ul>{desktop}</ul><button class="menu-btn" id="nav-toggle" aria-label="Open navigation">{menu_icon}</button></nav>
<div class="mobile-nav" id="mobile-menu"><button class="close-btn" id="mobile-close" aria-label="Close navigation">{close_icon}</button><ul>{mobile}</ul></div>'''

def shell(title,desc,body,canonical="/"):
    return f'''<!doctype html><html lang="en">{head(title,desc,canonical)}<body>{nav()}<div class="wrap"><main>{body}</main>{footer()}</div><script src="/assets/js/script.js" defer></script></body></html>'''

def footer():
    site=CONFIG["site"]
    socials=[('GITHUB',site["github"])] if site.get("github") else []
    if site.get("linkedin"):socials.append(("LINKEDIN",site["linkedin"]))
    if site.get("instagram"):socials.append(("INSTAGRAM",site["instagram"]))
    if site.get("twitter"):socials.append(("TWITTER",site["twitter"]))
    social_html="".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t,u in socials)
    social_html+=f'<li><a href="mailto:{esc(site["email"])}">EMAIL</a></li>'
    nav_html="".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t,u in NAV_LINKS)
    return f'''<footer><div class="footer-cols"><div><h3 class="h6">Socials</h3><ul>{social_html}</ul></div><div><h3 class="h6">Navigation</h3><ul>{nav_html}</ul></div></div>
<div class="footer-bottom"><p>{esc(site["name"])} © 2026 All Rights Reserved</p><p>Design based on the <a class="link-inline" href="https://github.com/jessgaspardev/grunge" target="_blank" rel="noopener">Grunge</a> template by Jess Gaspar</p></div></footer>'''

# ---------- shared components ----------

def image_frame(src,alt,cls=""):
    if not src:
        return f'<div class="image-frame {cls}"><div class="frame-box" style="display:grid;place-items:center;background:var(--base-300)"><span class="t-md">NO IMAGE YET</span></div></div>'
    return f'''<div class="image-frame {cls}"><img class="barcode" src="/assets/theme/barcode.svg" alt=""><div class="frame-box"><img src="{esc(src)}" alt="{esc(alt)}" loading="lazy"></div></div>'''

def bottom_mark():
    return '<div class="bottom-mark"><img class="symbol" src="/assets/theme/symbol-white.svg" alt=""><img class="barcode" src="/assets/theme/barcode.svg" alt=""></div>'

def accordion_box(items,resume=False):
    rows=[]
    for i,item in enumerate(items):
        if resume:
            title,place,period,text=item
            trigger=f'<button class="accordion-trigger" type="button"><span class="t-xl">{esc(title)}</span>{CHEVRON}</button><p class="t-md place">{esc(place)}</p><p class="t-sm period">{esc(period)}</p>'
        else:
            title,text=item
            trigger=f'<button class="accordion-trigger" type="button"><span class="t-xl"><span class="num">{i+1}.</span> {esc(title)}</span>{CHEVRON}</button>'
        rows.append(f'<div class="accordion-item">{trigger}<div class="accordion-content"><p class="t-sm">{esc(text)}</p></div></div>')
    return f'<div class="accordion-box">{"".join(rows)}</div>{bottom_mark()}'

CHEVRON='<svg class="chevron" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 8 8"><path fill="#eeeade" d="M1.5 1L0 2.5l4 4l4-4L6.5 1L4 3.5L1.5 1z"/></svg>'

def work_card(p):
    img=p["images"][0] if p.get("images") else ""
    thumb=f'<img class="thumb" src="{esc(img)}" alt="{esc(p["title"])}" loading="lazy">' if img else f'<div class="empty-thumb"><span>{esc(p["title"][:2].upper())}</span></div>'
    return f'''<a class="work-card" href="/works/{esc(p["slug"])}/"><div class="frame"><div class="label"><span>{esc(p["category"])}</span><img src="/assets/theme/symbol.svg" alt=""></div><div class="texture"></div>{thumb}<div class="disk"></div></div><div class="meta"><h3 class="h4">{esc(p["title"])}</h3><p class="t-md">{esc(p["client"])}</p></div></a>'''

# ---------- personal / credential asset lookups ----------

PORTRAIT_HERO="black-white_optimized.jpg"
PORTRAIT_ABOUT="black white-1_optimized.jpg"

def resolve_dir(name):
    """Pick whichever copy of a top-level asset bucket (SOURCE vs ASSETS) has content."""
    a=SOURCE/name;b=ASSETS/name
    if a.exists() and (not b.exists() or _file_count(a)>=_file_count(b)):return a
    if b.exists():return b
    return a

def personal_dir():
    return resolve_dir("Personal images")

def personal_images():
    d=personal_dir()
    if not d.exists():return []
    return [path_url("assets","personal","images",*p.relative_to(d).parts) for p in sorted(d.rglob("*"),key=lambda x:str(x).lower()) if p.is_file() and p.suffix.lower() in IMG_EXT and p.parent.name.casefold()!="award images"]

def find_personal(name):
    d=personal_dir()
    if not d.exists():return ""
    for p in d.rglob("*"):
        if p.is_file() and p.name==name:
            return path_url("assets","personal","images",*p.relative_to(d).parts)
    return ""

def archive_images():
    exclude={PORTRAIT_HERO,PORTRAIT_ABOUT}
    exclude|={a.rsplit("/",1)[-1] for a in awards()}
    return [x for x in personal_images() if x.rsplit("/",1)[-1] not in exclude]

def award_dir():
    """The two mirrors of "Personal images" aren't always structured the same
    way: one may keep an "Award Images" subfolder, the other may have been
    flattened so those files sit loose at the top level. Look for the
    subfolder in either mirror before giving up."""
    for base in (SOURCE,ASSETS):
        d=base/"Personal images"/"Award Images"
        if d.exists():return d
    return None

def awards():
    d=award_dir()
    if not d or not d.exists():return []
    return [path_url("assets","credentials","awards",*p.relative_to(d).parts) for p in sorted(d.rglob("*"),key=lambda x:str(x).lower()) if p.is_file() and p.suffix.lower() in IMG_EXT]

def certificates():
    d=resolve_dir("Certifications")
    if not d.exists():return []
    return [path_url("assets","credentials","certificates",*p.relative_to(d).parts) for p in sorted(d.rglob("*"),key=lambda x:str(x).lower()) if p.is_file() and p.suffix.lower() in IMG_EXT]

# ---------- pages ----------

def page_home(projects):
    site=CONFIG["site"]
    hero_portrait=find_personal(PORTRAIT_HERO) or (personal_images()[0] if personal_images() else "")
    about_portrait=find_personal(PORTRAIT_ABOUT) or hero_portrait
    featured=[p for p in projects if p.get("featured")][:6]
    services=accordion_box(CONFIG["services"])
    faq=accordion_box(CONFIG["faq"])
    body=f'''<section class="container container-xl hero">
<p class="t-xl tagline">Hey there! I build and customize WordPress sites, online stores and digital products for small businesses, founders and teams who need a website that actually works.</p>
<div class="hero-main">
<div class="hero-copy">
<a class="btn" href="/contact/">Available for work</a>
<h1 class="h1">{esc(site["name"])}</h1>
</div>
<div class="hero-photo">{image_frame(hero_portrait,site["name"])}</div>
</div>
</section>

<section class="container container-lg" style="align-items:center">
<h2 class="h2 text-center">Featured Works</h2>
<div class="work-grid">{"".join(work_card(p) for p in featured)}</div>
<a class="btn" href="/works/">All Works</a>
</section>

<section class="container container-md">
<h2 class="h2 text-center">Services</h2>
{services}
</section>

<section class="container container-xl">
<h2 class="h2 text-center">About</h2>
<div class="split">
<div class="split-copy">
<p class="t-xl">I'm a WordPress developer and digital product builder who enjoys the point where a design stops being a picture and becomes a working website.</p>
<p class="t-sm">I build, customize and maintain WordPress sites, WooCommerce and Shopify stores, and custom front-end work for clients across Nigeria, the UK and the US.</p>
<p class="t-sm">When I'm not building for a client, I'm usually improving my own tools, or picking apart a site to see how it was put together.</p>
<a class="btn" href="/about/">More about me</a>
</div>
<div class="split-photo">{image_frame(about_portrait,site["name"])}</div>
</div>
</section>

<section class="container container-md">
<h2 class="h2 text-center">FAQ</h2>
{faq}
</section>'''
    return shell("Home",site["description"],body,"/")

def page_works(projects):
    body=f'''<section class="container container-lg" style="align-items:center">
<h1 class="h1 text-center">Works</h1>
<div class="work-grid">{"".join(work_card(p) for p in projects)}</div>
</section>'''
    return shell("Works","Websites, e-commerce builds, digital products, plugins and brand projects.",body,"/works/")

def page_project(p):
    hero=p["images"][0] if p.get("images") else ""
    rest=p["images"][1:] if p.get("images") else []
    facts=[("Client",p["client"]),("Category",p["category"]),("Services"," · ".join(p["services"])),("Year",p.get("year",""))]
    facts_html="".join(f'<div class="fact"><h4 class="h5">{esc(k)}</h4><p class="t-sm">{esc(v)}</p></div>' for k,v in facts)
    live_btn=f'<a class="btn" href="{esc(p["liveSite"])}" target="_blank" rel="noopener">Live Site</a>' if p.get("liveSite") else ""
    gallery=""
    if rest:
        pair=rest[:2];extra=rest[2:]
        if pair:
            gallery+=f'<div class="gallery-2">{"".join(image_frame(im,p["title"]) for im in pair)}</div>'
        if extra:
            extra_imgs="".join(f'<img src="{esc(im)}" alt="{esc(p["title"])}" loading="lazy">' for im in extra)
            gallery+=f'<div class="gallery-grid">{extra_imgs}</div>'
    body=f'''<section class="container container-xl" style="align-items:center">
<h1 class="h1 text-center">{esc(p["title"])}</h1>
<div class="hero-media" style="width:100%">{image_frame(hero,p["title"])}</div>
<div class="facts-row">{facts_html}</div>
{live_btn}
<div style="max-width:48rem"><p class="t-xl">{esc(p["description"])}</p></div>
{gallery}
<a class="btn" href="/works/">All Works</a>
</section>'''
    return shell(p["title"],p["description"],body,f'/works/{p["slug"]}/')

def page_about():
    site=CONFIG["site"]
    portrait=find_personal(PORTRAIT_ABOUT) or (personal_images()[0] if personal_images() else "")
    experience=accordion_box(CONFIG["experience"],resume=True)
    tags="".join(f"<span>{esc(x)}</span>" for x in CONFIG["capabilities"])
    gallery="".join(f'<img src="{esc(x)}" alt="{esc(site["name"])} personal archive" loading="lazy">' for x in archive_images()[:12])
    body=f'''<section class="container container-xl">
<h1 class="h1 text-center">Meet {esc(site["name"].split()[0])}</h1>
<div class="split">
<div class="split-copy">
<p class="t-xl">I build, customize and maintain websites for businesses, organizations and digital products.</p>
<p class="t-sm">My work sits between visual implementation and practical engineering. I am comfortable working inside WordPress and page builders, then dropping into PHP, JavaScript and CSS when the problem needs more than a visual editor.</p>
</div>
<div class="split-photo">{image_frame(portrait,site["name"])}</div>
</div>
</section>

<section class="container container-md">
<h2 class="h2 text-center">Experience</h2>
{experience}
</section>

<section class="container container-md">
<h2 class="h2 text-center">Toolkit</h2>
<div class="tag-list">{tags}</div>
</section>

<section class="container container-xl">
<h2 class="h2 text-center">Personal Archive</h2>
<div class="gallery-grid">{gallery}</div>
<a class="btn" href="/credentials/">View Credentials</a>
</section>'''
    return shell("About",f"About {site['name']}, WordPress developer and digital product builder.",body,"/about/")

def page_credentials():
    a=awards();c=certificates()
    award_html="".join(f'<div class="credential-card">{image_frame(x,"Award")}<h3 class="h5">Designer Of The Year</h3></div>' for x in a)
    cert_html="".join(f'<div class="credential-card">{image_frame(x,"Certificate")}</div>' for x in c)
    body=f'''<section class="container container-xl">
<h1 class="h1 text-center">Credentials</h1>
<div class="credential-grid">{award_html or '<p class="t-sm text-center">No award image yet.</p>'}</div>
</section>
<section class="container container-xl">
<h2 class="h2 text-center">Certificates</h2>
<div class="credential-grid">{cert_html or '<p class="t-sm text-center">No certificates added yet.</p>'}</div>
</section>'''
    return shell("Credentials","Credentials and recognition archive.",body,"/credentials/")

def page_contact():
    site=CONFIG["site"]
    items=[("Email",site["email"],f'mailto:{site["email"]}')]
    if site.get("phone"):items.append(("Phone",site["phone"],f'tel:{site["phone"]}'))
    if site.get("location"):items.append(("Location",site["location"],None))
    if site.get("github"):items.append(("GitHub",site["github"],site["github"]))
    cards="".join(
        f'<div class="contact-item"><div class="row"><span class="t-lg">{esc(k)}</span><img src="/assets/theme/symbol-white.svg" alt=""></div><div class="divider"></div>'
        + (f'<a class="t-sm link-inline" href="{esc(href)}" target="_blank" rel="noopener">{esc(v)}</a>' if href else f'<p class="t-sm">{esc(v)}</p>')
        + '</div>'
        for k,v,href in items
    )
    body=f'''<section class="container container-xl text-center" style="align-items:center">
<h1 class="h1">Contact</h1>
<div style="max-width:44rem;display:flex;flex-direction:column;gap:1rem">
<p class="t-xl">Let's build something together.</p>
<p class="t-sm">Have a website, e-commerce build, WordPress problem or digital product in mind? Tell me what you're working on and I'll get back to you within a day or two.</p>
</div>
</section>
<section class="container container-md">
<div class="contact-grid">{cards}</div>
</section>'''
    return shell("Contact",f"Contact {site['name']} for WordPress development, e-commerce and digital product work.",body,"/contact/")

def main():
    projects=scan_projects();copy_assets()
    (SITE/"index.html").write_text(page_home(projects),encoding="utf-8")
    (SITE/"works").mkdir();(SITE/"works"/"index.html").write_text(page_works(projects),encoding="utf-8")
    for p in projects:
        d=SITE/"works"/p["slug"];d.mkdir(parents=True)
        (d/"index.html").write_text(page_project(p),encoding="utf-8")
    (SITE/"about").mkdir();(SITE/"about"/"index.html").write_text(page_about(),encoding="utf-8")
    (SITE/"credentials").mkdir();(SITE/"credentials"/"index.html").write_text(page_credentials(),encoding="utf-8")
    (SITE/"contact").mkdir();(SITE/"contact"/"index.html").write_text(page_contact(),encoding="utf-8")
    print(f"Built {len(projects)} projects")

if __name__=="__main__":main()
