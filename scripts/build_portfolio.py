from __future__ import annotations
import json, re, shutil
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"assets"
SOURCE=ASSETS/"Odunayo Portfolio Assets"
LEGACY=ASSETS/"projects"
SITE=ROOT/"site"
CONFIG=json.loads((ROOT/"scripts/site_config.json").read_text())

IMG_EXT={".jpg",".jpeg",".png",".webp",".gif",".avif",".svg"}
VID_EXT={".mp4",".webm",".mov",".m4v",".ogg"}

def esc(v):
    return str(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")

def slugify(s):
    return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")

def path_url(*parts):
    return "/"+"/".join(quote(str(x)) for x in parts)

def meta(slug, folder=None):
    m=dict(CONFIG["projects"].get(slug,{}))
    folder=folder or LEGACY/slug
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

def source_for(slug):
    if SOURCE.exists():
        for d in SOURCE.iterdir():
            if d.is_dir() and slugify(d.name)==slug:
                return d
    return LEGACY/slug if (LEGACY/slug).exists() else None

def scan_projects():
    found={}
    roots=[]
    if SOURCE.exists(): roots += [d for d in SOURCE.iterdir() if d.is_dir() and d.name.casefold() not in {"personal images","personal videos","certifications"}]
    if LEGACY.exists():
        roots += [d for d in LEGACY.iterdir() if d.is_dir()]
    for d in roots:
        slug=slugify(d.name)
        if slug=="borrowacamera-project":slug="borrowacam-project"
        if slug not in found or d.parent==SOURCE: found[slug]=d
    projects=[]
    for slug,m0 in CONFIG["projects"].items():
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
    pi=SOURCE/"Personal images"
    pv=SOURCE/"Personal Videos"
    cert=SOURCE/"Certifications"
    if pi.exists():shutil.copytree(pi,SITE/"assets"/"personal"/"images",dirs_exist_ok=True)
    if pv.exists():shutil.copytree(pv,SITE/"assets"/"personal"/"videos",dirs_exist_ok=True)
    awards=pi/"Award Images"
    if awards.exists():shutil.copytree(awards,SITE/"assets"/"credentials"/"awards",dirs_exist_ok=True)
    if cert.exists():shutil.copytree(cert,SITE/"assets"/"credentials"/"certificates",dirs_exist_ok=True)
    public=ROOT/"public"
    for n in ("favicon.svg","og-image.png","odunayo-bolarinwa-portfolio.pdf"):
        f=public/n
        if f.exists():shutil.copy2(f,SITE/n)
    (SITE/"assets"/"css").mkdir(parents=True);(SITE/"assets"/"js").mkdir(parents=True)
    shutil.copy2(ROOT/"scripts"/"styles.css",SITE/"assets"/"css"/"styles.css")
    shutil.copy2(ROOT/"scripts"/"script.js",SITE/"assets"/"js"/"script.js")

def head(title,desc,canonical):
    return f'''<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Odunayo Bolarinwa</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://odgrande.github.io{canonical}">
<meta property="og:title" content="{esc(title)} · Odunayo Bolarinwa"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="https://odgrande.github.io/og-image.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/css/styles.css"></head>'''

def nav(active=""):
    links=[("home","01","HOME","/"),("work","02","WORKS","/works/"),("about","03","ABOUT","/about/"),("contact","04","CONTACT","/contact/")]
    return '<header class="nav"><a class="nav-logo" href="/"><b>OD</b><span>ODUNAYO<br>BOLARINWA</span></a><nav>'+''.join(f'<a class="{"on" if active==k else ""}" href="{u}"><i>{n}</i>{t}</a>' for k,n,t,u in links)+'</nav><button class="menu-btn" id="nav-toggle">MENU</button></header><div class="mobile-nav" id="mobile-menu" hidden><button id="mobile-close">CLOSE</button>'+''.join(f'<a href="{u}"><i>{n}</i>{t}</a>' for _,n,t,u in links)+'<a href="/credentials/"><i>05</i>CREDENTIALS</a></div>'

def shell(title,desc,active,body,canonical="/"):
    return f'''<!doctype html><html lang="en">{head(title,desc,canonical)}<body>{nav(active)}<main>{body}</main>{footer()}<script src="/assets/js/script.js" defer></script></body></html>'''

def footer():
    return f'''<footer><div class="footer-top"><div><small>HAVE A PROJECT IN MIND?</small><h2>LET'S MAKE<br>SOMETHING.</h2><a class="footer-cta" href="/contact/">START A CONVERSATION ↗</a></div><div class="footer-nav"><small>INDEX</small><a href="/">HOME</a><a href="/works/">WORKS</a><a href="/about/">ABOUT</a><a href="/credentials/">CREDENTIALS</a><a href="/contact/">CONTACT</a></div><div class="footer-nav"><small>ELSEWHERE</small><a href="https://github.com/odgrande" target="_blank">GITHUB ↗</a><a href="mailto:{esc(CONFIG["site"]["email"])}">EMAIL ↗</a></div></div><div class="footer-bottom"><span>© 2026 ODUNAYO BOLARINWA</span><span>LAGOS, NIGERIA · WORDPRESS DEVELOPER</span></div></footer>'''

def image_card(p,index=0):
    img=p["images"][0] if p.get("images") else ""
    media=f'<img src="{img}" alt="{esc(p["title"])}" loading="lazy">' if img else f'<div class="empty-media"><span>{esc(p["title"][:2].upper())}</span></div>'
    return f'''<a class="work-card" href="/works/{esc(p["slug"])}/"><div class="work-image">{media}<span class="work-no">0{index+1}</span><b>↗</b></div><div class="work-info"><div><h3>{esc(p["title"])}</h3><p>{esc(p["category"])}</p></div><span>{esc(p.get("year",""))}</span></div></a>'''

def personal_images():
    d=SOURCE/"Personal images"
    if not d.exists():return []
    return [path_url("assets","personal","images",*p.relative_to(d).parts) for p in sorted(d.rglob("*"),key=lambda x:str(x).lower()) if p.is_file() and p.suffix.lower() in IMG_EXT and p.parent.name.casefold()!="award images"]

def awards():
    d=SOURCE/"Personal images"/"Award Images"
    if not d.exists():return []
    return [path_url("assets","credentials","awards",*p.relative_to(d).parts) for p in sorted(d.rglob("*"),key=lambda x:str(x).lower()) if p.is_file() and p.suffix.lower() in IMG_EXT]

def certificates():
    d=SOURCE/"Certifications"
    if not d.exists():return []
    return [path_url("assets","credentials","certificates",*p.relative_to(d).parts) for p in sorted(d.rglob("*"),key=lambda x:str(x).lower()) if p.is_file() and p.suffix.lower() not in {".txt",".md"}]

def page_home(projects):
    featured=[p for p in projects if p.get("featured")][:4]
    portrait=next((x for x in personal_images() if any(k in x.lower() for k in ["portrait","headshot","profile","a60881f8"])), "")
    award=awards()[0] if awards() else ""
    blast=next((p for p in projects if p["slug"]=="blast-music-fest-project"),None)
    proof=f'<video controls preload="metadata"><source src="{blast["videos"][0]}"></video>' if blast and blast.get("videos") else '<div class="video-placeholder"><small>CLIENT PROOF · BLASTFEST</small><strong>VIDEO / TESTIMONIAL<br>COMING FROM PROJECT FOLDER</strong><p>Drop the testimonial video into the BLAST Music Fest project folder. The build will place it here automatically.</p></div>'
    services="".join(f'<details><summary><i>0{i}</i><strong>{esc(a)}</strong><b>+</b></summary><p>{esc(d)}</p></details>' for i,(a,d) in enumerate(CONFIG["services"],1))
    body=f'''<section class="home-hero"><div class="hero-meta"><span>01 / 05</span><span>WORDPRESS · E-COMMERCE · DIGITAL PRODUCTS</span><span>AVAILABLE FOR SELECT PROJECTS</span></div><div class="hero-title"><p>WEB DEVELOPER<br>BASED IN LAGOS, NIGERIA</p><h1>ODUNAYO<br><em>BOLARINWA</em></h1></div><div class="hero-foot"><span>SCROLL TO EXPLORE ↓</span><span>EST. 2018 · ODGRANDE DIGITAL</span></div></section>
<section class="home-intro"><div class="index-mark">02 / 05</div><div><p class="eyebrow">WHAT I DO</p><h2>I BUILD DIGITAL EXPERIENCES THAT ARE <em>USEFUL, FAST AND BUILT TO LAST.</em></h2><p class="body-copy">WordPress development, e-commerce, custom functionality, front-end implementation and digital product work. I bridge design intent and practical engineering.</p></div></section>
<section class="selected"><div class="section-bar"><span>SELECTED WORK</span><a href="/works/">VIEW ALL WORK ↗</a></div><div class="selected-grid">{''.join(image_card(p,i) for i,p in enumerate(featured))}</div></section>
<section class="services"><div class="index-mark">03 / 05</div><div class="section-heading"><p class="eyebrow">CAPABILITIES</p><h2>THE<br><em>STACK.</em></h2></div><div class="service-list">{services}</div></section>
<section class="home-about"><div class="index-mark">04 / 05</div><div class="about-split"><div><p class="eyebrow">A LITTLE ABOUT ME</p><h2>DEVELOPER<br><em>BRAIN.</em><br>DESIGNER EYE.</h2></div><div><p class="big-copy">I am a WordPress developer who enjoys the point where a design stops being a picture and becomes a working product.</p><a class="line-link" href="/about/">MEET ODUNAYO ↗</a></div></div>{f'<div class="award-proof"><img src="{award}" alt="Designer of the Year award"><div><small>RECOGNITION</small><h3>DESIGNER<br>OF THE YEAR</h3><a class="line-link" href="/credentials/">VIEW CREDENTIALS ↗</a></div></div>' if award else ""}</section>
<section class="client-proof"><div class="index-mark">05 / 05</div><div class="proof-layout"><div><p class="eyebrow">CLIENT PROOF</p><h2>WORK<br>IN THE<br><em>REAL WORLD.</em></h2></div><div>{proof}</div></div></section>'''
    return shell("Home",CONFIG["site"]["description"],"",body)

def page_works(projects):
    cards="".join(image_card(p,i%3) for i,p in enumerate(projects))
    body=f'''<section class="page-hero"><span>01 / WORKS</span><h1>WORKS</h1><p>A selection of websites, e-commerce builds, digital products, plugins and brand projects. Every project remains independent and its media comes from its own folder.</p></section><section class="archive"><div class="archive-head"><span>{len(projects):02d} PROJECTS</span><span>WEB · PRODUCT · BRAND</span></div><div class="archive-grid">{cards}</div></section>'''
    return shell("Works","Websites, e-commerce builds, digital products, plugins and brand projects.","work",body,"/works/")

def page_project(p,related):
    media=""
    if p.get("videos"):
        media="".join(f'<div class="case-video"><video controls preload="metadata"><source src="{v}"></video></div>' for v in p["videos"])
    elif p["slug"]=="blast-music-fest-project":
        media='<div class="video-placeholder case-placeholder"><small>VIDEO / TESTIMONIAL</small><strong>BLASTFEST<br>MEDIA SLOT</strong><p>Add the real testimonial video to this project folder and it will appear after the next build.</p></div>'
    if p.get("images"):
        media+='<div class="case-gallery">'+''.join(f'<figure><img src="{im}" alt="{esc(p["title"])} project image {i+1}" loading="lazy"></figure>' for i,im in enumerate(p["images"]))+'</div>'
    else:media+='<div class="empty-gallery">NO MEDIA YET · DROP FILES INTO THIS PROJECT FOLDER</div>'
    facts=f'<div><small>CLIENT</small><strong>{esc(p["client"])}</strong></div>'+ (f'<div><small>LOCATION</small><strong>{esc(p["location"])}</strong></div>' if p.get("location") else "")+f'<div><small>SERVICES</small><strong>{esc(" · ".join(p["services"]))}</strong></div>'+ (f'<div><a class="line-link" href="{esc(p["liveSite"])}" target="_blank">VISIT LIVE SITE ↗</a></div>' if p.get("liveSite") else "")
    rel="".join(f'<a class="next-work" href="/works/{r["slug"]}/"><small>{esc(r["category"])}</small><strong>{esc(r["title"])}</strong><b>↗</b></a>' for r in related[:3])
    body=f'''<section class="case-hero"><div class="case-meta"><span>PROJECT / {esc(p["category"])}</span><span>{esc(p.get("year",""))}</span></div><h1>{esc(p["title"])}</h1><p>{esc(p["description"])}</p><div class="case-facts">{facts}</div></section><section class="case-media">{media}</section><section class="next-section"><div><small>NEXT / SELECTED WORK</small><h2>KEEP<br>SCROLLING.</h2></div><div class="next-grid">{rel}</div></section>'''
    return shell(p["title"],p["description"],"work",body,f'/works/{p["slug"]}/')

def page_about():
    imgs=personal_images();portrait=next((x for x in imgs if any(k in x.lower() for k in ["portrait","headshot","profile","a60881f8"])),imgs[0] if imgs else "")
    exp="".join(f'<article><div><span>{esc(period)}</span><h3>{esc(role)}</h3><small>{esc(org)}</small></div><p>{esc(detail)}</p></article>' for role,org,period,detail in CONFIG["experience"])
    skills="".join(f"<span>{esc(x)}</span>" for x in CONFIG["capabilities"])
    gallery="".join(f'<img src="{x}" alt="Odunayo personal archive" loading="lazy">' for x in imgs)
    body=f'''<section class="page-hero about-title"><span>02 / ABOUT</span><h1>MEET<br>ODUNAYO</h1></section><section class="about-intro"><div><p class="eyebrow">THE PERSON BEHIND THE WORK</p><p class="about-big">I build, customize and maintain websites for businesses, organizations and digital products.</p></div><div class="body-copy"><p>My work sits between visual implementation and practical engineering. I am comfortable working inside WordPress and page builders, then dropping into PHP, JavaScript and CSS when the problem needs more than a visual editor.</p><p>I care about the small things too: responsive behaviour, clean content structures, useful interactions, performance and what happens after launch.</p></div></section><section class="portrait-block">{f'<img src="{portrait}" alt="Odunayo Bolarinwa">' if portrait else '<div class="empty-gallery">PORTRAIT ASSET</div>'}<div><small>ODUNAYO BOLARINWA</small><p>WORDPRESS DEVELOPER<br>WEB DEVELOPER<br>DIGITAL PRODUCT BUILDER</p><span>LAGOS, NIGERIA</span></div></section><section class="experience"><div class="section-bar"><span>EXPERIENCE</span><span>02 / 04</span></div><div>{exp}</div></section><section class="toolkit"><div><p class="eyebrow">TOOLKIT</p><h2>WHAT I<br><em>WORK WITH.</em></h2></div><div class="skill-cloud">{skills}</div></section><section class="personal-archive"><div class="section-bar"><span>PERSONAL ARCHIVE</span><span>SELECTED IMAGES</span></div><div class="personal-grid">{gallery}</div></section>'''
    return shell("About","About Odunayo Bolarinwa, WordPress developer and digital product builder.","about",body,"/about/")

def page_credentials():
    a=awards();c=certificates()
    award_html="".join(f'<article class="credential-card"><img src="{x}" alt="Designer of the Year award" loading="lazy"><small>RECOGNITION</small><h2>DESIGNER<br>OF THE YEAR</h2></article>' for x in a)
    cert_html="".join(f'<a href="{x}" target="_blank">{esc(x.rsplit("/",1)[-1])} ↗</a>' for x in c)
    body=f'''<section class="page-hero"><span>03 / CREDENTIALS</span><h1>PROOF<br>OF WORK.</h1><p>Recognition and certification files are kept here as a verifiable archive. New files dropped into the credentials folders are included automatically.</p></section><section class="credentials">{award_html or '<div class="empty-gallery">NO AWARD IMAGE YET</div>'}</section><section class="certificates"><div class="section-bar"><span>CERTIFICATIONS</span><span>{len(c):02d} FILES</span></div>{f'<div class="cert-list">{cert_html}</div>' if c else '<div class="credential-placeholder"><strong>VERIFICATION ARCHIVE</strong><p>Add certificates to <code>Certifications</code> inside the portfolio assets folder.</p></div>'}</section>'''
    return shell("Credentials","Credentials and recognition archive.","",body,"/credentials/")

def page_contact():
    body=f'''<section class="contact-page"><span>04 / CONTACT</span><h1>LET'S<br><em>TALK.</em></h1><p>Have a website, e-commerce build, WordPress problem or digital product in mind? Tell me what you are working on.</p><a class="contact-email" href="mailto:{esc(CONFIG["site"]["email"])}">{esc(CONFIG["site"]["email"])}</a></section><section class="contact-details"><div><small>LOCATION</small><h2>LAGOS,<br>NIGERIA</h2></div><div><small>ELSEWHERE</small><a href="https://github.com/odgrande" target="_blank">GITHUB ↗</a><span>LINKEDIN · ADD WHEN READY</span><span>INSTAGRAM · ADD WHEN READY</span><a href="/odunayo-bolarinwa-portfolio.pdf" target="_blank">PDF PORTFOLIO ↗</a></div></section>'''
    return shell("Contact","Contact Odunayo Bolarinwa for WordPress development, e-commerce and digital product work.","contact",body,"/contact/")

def main():
    projects=scan_projects();copy_assets()
    (SITE/"index.html").write_text(page_home(projects))
    (SITE/"works").mkdir();(SITE/"works"/"index.html").write_text(page_works(projects))
    for p in projects:
        d=SITE/"works"/p["slug"];d.mkdir(parents=True)
        related=[x for x in projects if x["slug"]!=p["slug"]]
        (d/"index.html").write_text(page_project(p,related))
    (SITE/"about").mkdir();(SITE/"about"/"index.html").write_text(page_about())
    (SITE/"credentials").mkdir();(SITE/"credentials"/"index.html").write_text(page_credentials())
    (SITE/"contact").mkdir();(SITE/"contact"/"index.html").write_text(page_contact())
    print(f"Built {len(projects)} projects")

if __name__=="__main__":main()
