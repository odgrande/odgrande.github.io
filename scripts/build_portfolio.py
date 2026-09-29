from __future__ import annotations
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
PROJECTS_DIR = ASSETS / 'projects'
SITE = ROOT / 'site'
CONFIG = json.loads((ROOT / 'scripts' / 'site_config.json').read_text())

IMG_EXT = {'.jpg','.jpeg','.png','.webp','.gif','.avif','.svg'}
VID_EXT = {'.mp4','.webm','.mov','.m4v','.ogg'}


def esc(s):
    return (str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;').replace("'",'&#39;'))

def slugify(name):
    return re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')

def url_path(*parts):
    from urllib.parse import quote
    return '/' + '/'.join(quote(p) for p in parts)

def title_from_slug(slug):
    return ' '.join(w.capitalize() for w in slug.split('-'))

def project_meta(slug):
    m = dict(CONFIG['projects'].get(slug, {}))
    d = PROJECTS_DIR / slug
    for filename in ('project.json','meta.json'):
        f = d / filename
        if f.exists():
            try:
                m.update(json.loads(f.read_text()))
            except Exception:
                pass
    m.setdefault('title', title_from_slug(slug))
    m.setdefault('client', m['title'])
    m.setdefault('category', 'Project Archive')
    m.setdefault('services', ['Web / Digital'])
    m.setdefault('year', 'Archive')
    m.setdefault('description', 'Project archive entry. Detailed case study information can be added later.')
    m.setdefault('featured', False)
    return m

def scan_projects():
    projects=[]
    seen=set()
    if PROJECTS_DIR.exists():
        for d in sorted(PROJECTS_DIR.iterdir(), key=lambda p: p.name.lower()):
            if not d.is_dir(): continue
            slug = d.name
            seen.add(slug)
            files=[p for p in d.iterdir() if p.is_file() and p.name not in {'project.json','meta.json'}]
            images=[p for p in files if p.suffix.lower() in IMG_EXT]
            videos=[p for p in files if p.suffix.lower() in VID_EXT]
            m=project_meta(slug)
            m['slug']=slug
            m['images']=[url_path('assets','projects',slug,p.name) for p in images]
            m['videos']=[url_path('assets','projects',slug,p.name) for p in videos]
            projects.append(m)
    # Preserve portfolio projects from the PDF even if an asset folder is currently empty/missing.
    for slug,m0 in CONFIG['projects'].items():
        if slug not in seen:
            m=dict(m0); m['slug']=slug; m['images']=[]; m['videos']=[]; projects.append(m)
    featured_index={s:i for i,s in enumerate(CONFIG['featuredOrder'])}
    projects.sort(key=lambda p: (0 if p.get('featured') else 1, featured_index.get(p['slug'],999), p['title'].lower()))
    return projects

def asset_copy():
    if SITE.exists(): shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    # Copy static assets. Empty folders are created with .gitkeep in source if needed.
    if ASSETS.exists(): shutil.copytree(ASSETS, SITE/'assets', dirs_exist_ok=True)
    public = ROOT / 'public'
    for name in ('favicon.svg','og-image.png','odunayo-bolarinwa-portfolio.pdf'):
        p=public/name
        if p.exists(): shutil.copy2(p, SITE/name)
    (SITE/'assets'/'css').mkdir(parents=True, exist_ok=True)
    (SITE/'assets'/'js').mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/'scripts'/'styles.css', SITE/'assets'/'css'/'styles.css')
    shutil.copy2(ROOT/'scripts'/'script.js', SITE/'assets'/'js'/'script.js')

def head(title, description, canonical=''):
    if not canonical: canonical='https://odgrande.github.io/'
    elif not canonical.startswith('http'): canonical='https://odgrande.github.io'+canonical
    return f'''<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | Odunayo Bolarinwa</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}"><meta name="theme-color" content="#11110f">
<meta property="og:type" content="website"><meta property="og:url" content="{esc(canonical)}"><meta property="og:title" content="{esc(title)} | Odunayo Bolarinwa"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="https://odgrande.github.io/og-image.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/css/styles.css">
</head>'''

def nav(active=''):
    items=[('home','1. Home','/'),('work','2. Works','/works/'),('about','3. About','/about/'),('contact','4. Contact','/contact/')]
    desktop=''.join(f'<a class="{("active" if active==key else "")}" href="{href}">{label}</a>' for key,label,href in items)
    mobile=''.join(f'<a href="{href}">{label}</a>' for key,label,href in items) + '<a href="/credentials/">5. Credentials</a>'
    return f'''<header class="site-nav"><a href="/" class="brand"><span class="brand-mark">OD</span><span class="brand-name">ODUNAYO BOLARINWA</span></a><button class="nav-toggle" id="nav-toggle">MENU</button><nav class="desktop-nav">{desktop}</nav></header><div class="mobile-menu" id="mobile-menu" hidden><button id="mobile-close">CLOSE</button><nav>{mobile}</nav></div>'''

def barcode(code='012.0123.456.78.900'):
    return f'<div class="barcode" aria-hidden="true"><div class="barcode-bars"></div><span>{esc(code)}</span></div>'

def footer():
    return f'''<footer class="site-footer"><div class="footer-grid"><div><p class="eyebrow">LET'S BUILD SOMETHING</p><h2 class="footer-title rough">Have a project in mind?</h2><a class="display-link" href="/contact/">Start a conversation ↗</a></div><div class="footer-links"><p class="eyebrow">NAVIGATION</p><a href="/">Home</a><a href="/works/">Works</a><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/credentials/">Credentials</a></div><div class="footer-links"><p class="eyebrow">SOCIAL</p><a href="{esc(CONFIG['site']['github'])}" target="_blank" rel="noreferrer">GitHub ↗</a><a href="mailto:{esc(CONFIG['site']['email'])}">Email ↗</a><span>LinkedIn · soon</span><span>Instagram · soon</span></div></div><div class="footer-bottom"><span>© {esc(CONFIG['site'].get('year','2026'))} Odunayo Bolarinwa. All rights reserved</span><span>Site built by Odunayo Bolarinwa · Hosted on GitHub Pages</span></div></footer>'''

def shell(title, desc, active, body):
    svg_filters='<svg class="grunge-filters" aria-hidden="true"><filter id="rough-edge" x="-20%" y="-20%" width="140%" height="140%"><feTurbulence type="fractalNoise" baseFrequency="0.02 0.9" numOctaves="3" seed="6" result="noise"/><feDisplacementMap in="SourceGraphic" in2="noise" scale="7"/></filter></svg>'
    return f'''<!doctype html><html lang="en">{head(title,desc)}<body>{svg_filters}<div class="site-noise"></div>{nav(active)}<main>{body}</main>{footer()}<script src="/assets/js/script.js" defer></script></body></html>'''

def card(p):
    img=p['images'][0] if p.get('images') else ''
    media=f'<img src="{img}" alt="{esc(p["title"])}" loading="lazy">' if img else f'<div class="media-fallback">{esc(p["title"][:2])}</div>'
    return f'''<a href="/works/{esc(p["slug"])}/" class="project-card"><div class="project-media">{media}<span class="project-arrow">↗</span></div><div class="project-meta"><div><h3>{esc(p['title'])}</h3><p>{esc(p['category'])}</p></div><span class="project-location">{esc(p.get('location') or p.get('client',''))}</span></div></a>'''

def page_index(projects):
    featured=[p for p in projects if p.get('featured')]
    portrait='/assets/personal/images/file_00000000a60881f8bf2abc22d8606f68.png'
    awards=list_personal_awards()
    award=awards[0] if awards else None
    blast=next((p for p in projects if p['slug']=='blast-music-fest-project'),None)
    blast_video=blast['videos'][0] if blast and blast.get('videos') else None
    proof = f'''<div class="video-wrap"><video controls preload="metadata"><source src="{blast_video}"></video></div>''' if blast_video else '''<div class="video-placeholder"><span>VIDEO / TESTIMONIAL</span><strong>BLASTFEST</strong><small>Testimonial media placeholder. Drop the future testimonial video into the BLASTFEST project folder and it will appear here automatically after the next build.</small></div>'''
    award_html=f'<img src="{award}" alt="Designer of the Year award" loading="lazy">' if award else '<div class="award-placeholder">Award asset will appear here.</div>'
    skills=''.join(f'<span>{esc(s)}</span>' for s in CONFIG['capabilities'])
    services=''.join(f'<details class="service-item" open=""><summary><span>{i:02d}</span><strong>{esc(a)}</strong><b>+</b></summary><p>{esc(b)}</p></details>' for i,(a,b) in enumerate(CONFIG['services'],1))
    body=f'''
<section class="hero section-pad"><div class="hero-kicker"><span>AVAILABLE FOR SELECT PROJECTS</span>{barcode()}</div><div class="hero-grid"><div class="hero-copy"><p class="eyebrow">WORDPRESS · E-COMMERCE · DIGITAL PRODUCTS</p><h1 class="rough">ODUNAYO<br>BOLARINWA</h1><p class="hero-lead">I build, customize and maintain WordPress websites, e-commerce experiences and digital products for businesses, agencies and growing brands.</p><div class="hero-actions"><a href="/works/" class="button button-primary">See selected work ↗</a><a href="/contact/" class="button button-outline">Work with me</a></div></div><div class="hero-visual"><img src="{portrait}" alt="Odunayo Bolarinwa" fetchpriority="high"><div class="hero-sticker">OD<br>WEB<br>DEV</div></div></div><div class="hero-bottom"><span>Based in Lagos, Nigeria</span><span>WordPress Developer · Digital Builder</span><span>{esc(CONFIG['site']['email'])}</span></div></section>
<section class="section-pad intro-strip"><div class="section-label">02 / 06</div><div class="intro-text"><span>I turn</span> designs, requirements and messy problems into reliable websites, e-commerce systems and digital products that clients can actually use and maintain.</div></section>
<section class="section-pad works-section"><div class="section-head"><div><p class="eyebrow">SELECTED WORK</p><h2 class="rough">Built in the real world.</h2></div><a href="/works/" class="text-link">View all projects ↗</a></div><div class="project-grid">{''.join(card(p) for p in featured)}</div></section>
<section class="section-pad services-section"><div class="section-label">03 / 06</div><div class="section-head"><div><p class="eyebrow">CAPABILITIES</p><h2 class="rough">A practical stack.</h2></div><p class="section-note">The goal is not to use more tools. It is to choose the right tools, ship properly and keep the result maintainable.</p></div><div class="service-list">{services}</div><div class="capability-cloud">{skills}</div></section>
<section class="section-pad about-preview"><div class="section-label">04 / 06</div><div class="about-grid"><div><p class="eyebrow">ABOUT ODUNAYO</p><h2 class="rough">Developer brain.<br>Designer eye.</h2></div><div><p class="large-copy">I work across development and visual implementation. That means I can understand the design intent, build the interface, wire the functionality, troubleshoot the hard parts and keep the site moving after launch.</p><a href="/about/" class="text-link">More about me ↗</a></div></div></section>
<section class="section-pad proof-section"><div class="section-label">05 / 06</div><div class="proof-grid"><div class="award-panel"><p class="eyebrow">RECOGNITION</p>{award_html}<h3 class="rough">Designer of the Year</h3><p>Recognition material is kept in the credentials archive.</p><a href="/credentials/" class="text-link">View credentials ↗</a></div><div class="testimonial-panel"><p class="eyebrow">CLIENT PROOF</p>{proof}<p class="muted-note">Additional testimonial media can be added to the project folder later.</p></div></div></section>
<section class="section-pad presence-section"><div class="section-label">06 / 06</div><div class="section-head"><div><p class="eyebrow">DIGITAL PRESENCE</p><h2 class="rough">More than a website.</h2></div><p class="section-note">Website development, ongoing maintenance, content systems and social presence work across professional and brand channels, including LinkedIn and Instagram.</p></div><div class="presence-cards"><div class="presence-card"><span>01</span><h3>LinkedIn</h3><p>Professional presence, page build and maintenance.</p></div><div class="presence-card"><span>02</span><h3>Instagram</h3><p>Visual page setup, content presentation and ongoing digital presence.</p></div><div class="presence-card"><span>03</span><h3>Web + Content</h3><p>Connected digital experiences across websites, campaigns and products.</p></div></div><div class="pdf-cta"><a href="/odunayo-bolarinwa-portfolio.pdf" target="_blank" class="button button-primary">View full PDF portfolio ↗</a></div></section>'''
    return shell('Home',CONFIG['site']['description'],'',body)

def page_works(projects):
    cards=''.join(card(p) for p in projects)
    body=f'''<section class="section-pad page-intro"><p class="eyebrow">WORKS / 01</p><h1 class="rough">WORKS</h1><p>Websites, e-commerce builds, digital platforms, plugins, branding and product work. Each folder is treated as its own project entry.</p></section><section class="section-pad archive-section"><div class="project-grid">{cards}</div></section>'''
    return shell('Works','Websites, e-commerce builds, digital platforms, plugins, branding and product work.','work',body)

def page_project(p, related):
    details=f'''<div><span>Client</span><strong>{esc(p['client'])}</strong></div>{f'<div><span>Location</span><strong>{esc(p["location"])}</strong></div>' if p.get('location') else ''}<div><span>Services</span><strong>{esc(' · '.join(p['services']))}</strong></div>{f'<div><a class="button button-outline" href="{esc(p["liveSite"])}" target="_blank" rel="noreferrer">Live site ↗</a></div>' if p.get('liveSite') else ''}'''
    media=''
    if p.get('videos'):
        for v in p['videos']:
            media+=f'<div class="project-video"><video controls preload="metadata"><source src="{v}"></video></div>'
    elif p['slug']=='blast-music-fest-project':
        media+='<div class="video-placeholder project-video-placeholder"><span>VIDEO / TESTIMONIAL</span><strong>BLASTFEST</strong><small>Place the future testimonial or project video inside this project folder. It will appear here automatically after the next build.</small></div>'
    if p.get('images'):
        imgs=''.join(f'<figure><img src="{im}" alt="{esc(p["title"])} project image {i+1}" loading="lazy"></figure>' for i,im in enumerate(p['images']))
        media+=f'<div class="project-gallery">{imgs}</div>'
    else:
        media+='<div class="empty-gallery">No visual assets in this project folder yet. Add images or video files, push, and they will appear here automatically.</div>'
    rel=''.join(f'<a class="mini-project" href="/works/{esc(r["slug"])}/"><span>{esc(r["category"])}</span><strong>{esc(r["title"])}</strong><b>↗</b></a>' for r in related)
    body=f'''<section class="section-pad project-hero"><div class="project-hero-top"><span class="eyebrow">PROJECT / {esc(p['category'])}</span><span>{esc(p.get('year','Archive'))}</span></div><h1>{esc(p['title'])}</h1><p class="project-lead">{esc(p['description'])}</p><div class="project-facts">{details}</div></section><section class="section-pad media-stack">{media}</section><section class="section-pad project-bottom"><div><p class="eyebrow">NEXT</p><h2>More work</h2></div><div class="related-grid">{rel}</div></section>'''
    return shell(p['title'],p['description'],'work',body)

def list_personal_images():
    d=ASSETS/'personal'/'images'
    if not d.exists(): return []
    return [url_path('assets','personal','images',p.name) for p in sorted(d.iterdir(), key=lambda x:x.name.lower()) if p.is_file() and p.suffix.lower() in IMG_EXT]

def list_personal_awards():
    d=ASSETS/'../credentials/awards'  # normalized below
    d=(ASSETS/'credentials'/'awards')
    if not d.exists(): return []
    return [url_path('assets','credentials','awards',p.name) for p in sorted(d.iterdir(), key=lambda x:x.name.lower()) if p.is_file() and p.suffix.lower() in IMG_EXT]

def list_credentials():
    d=ASSETS/'credentials'/'certificates'
    if not d.exists(): return []
    return [url_path('assets','credentials','certificates',p.name) for p in sorted(d.iterdir(), key=lambda x:x.name.lower()) if p.is_file() and p.name != '.gitkeep' and p.suffix.lower() not in {'.md','.txt'}]

def page_about():
    images=list_personal_images(); portrait=next((x for x in images if 'a60881f8' in x.lower()), images[0] if images else '')
    skill=''.join(f'<span>{esc(s)}</span>' for s in CONFIG['capabilities'])
    exp=''.join(f'<details class="service-item timeline-item" open><summary><span>{esc(period)}</span><strong>{esc(role)}<br><small>{esc(org)}</small></strong><b>+</b></summary><p>{esc(detail)}</p></details>' for role,org,period,detail in CONFIG['experience'])
    gallery=''.join(f'<img src="{im}" alt="Odunayo personal archive {i+1}" loading="lazy">' for i,im in enumerate(images))
    body=f'''<section class="section-pad page-intro"><h1 class="rough">MEET ODUNAYO</h1></section><section class="section-pad about-intro"><div><p class="eyebrow">ABOUT / 02</p><h2 class="rough">Developer brain.<br>Designer eye.</h2></div><div class="about-intro-copy"><p>I build, customize and maintain websites for real businesses, organizations and digital products. My work sits between visual implementation and practical engineering.</p><p>I am comfortable getting into the code when the page builder stops being enough, while still caring about the details a user actually sees.</p></div></section><section class="section-pad portrait-section"><div class="portrait-wrap">{f'<img src="{portrait}" alt="Odunayo Bolarinwa" loading="lazy">' if portrait else ''}</div><div class="portrait-note"><p class="eyebrow">ODUNAYO BOLARINWA</p><p>WordPress Developer · Web Developer · Digital Product Builder</p><p class="muted-note">Lagos, Nigeria</p>{barcode()}</div></section><section class="section-pad timeline-section"><p class="eyebrow">EXPERIENCE</p><div class="service-list timeline">{exp}</div></section><section class="section-pad skills-section"><div><p class="eyebrow">TOOLKIT</p><h2 class="rough">What I work with.</h2></div><div class="capability-cloud capability-cloud-large">{skill}</div></section><section class="section-pad personal-gallery-section"><div class="section-head"><div><p class="eyebrow">PERSONAL / VISUAL ARCHIVE</p><h2 class="rough">Beyond client work.</h2></div><p class="section-note">Personal images dropped into the personal images folder are surfaced here automatically.</p></div><div class="personal-grid">{gallery}</div></section>'''
    return shell('About','About Odunayo Bolarinwa.','about',body)

def page_credentials():
    awards=list_personal_awards(); certs=list_credentials()
    award_html=''.join(f'<article class="credential-card"><img src="{a}" alt="Designer of the Year award" loading="lazy"><h2 class="rough">Designer of the Year</h2><p>Recognition asset</p></article>' for a in awards) or '<div class="empty-state">No award assets added yet.</div>'
    cert_html=''.join(f'<a href="{c}" target="_blank" rel="noreferrer">Open certificate ↗</a>' for c in certs) or '<div class="credential-placeholder"><strong>Certificate vault</strong><p>Drop certificate PDFs, images or supporting files into <code>assets/credentials/certificates/</code>. They will be listed here automatically after the next build.</p></div>'
    body=f'''<section class="section-pad page-intro"><h1 class="rough">CREDENTIALS</h1><p>A dedicated place for awards, certificates and supporting verification material. New credential files can be dropped into the credentials folders and will surface here after the next build.</p></section><section class="section-pad credentials-section"><p class="eyebrow">AWARDS</p><div class="credential-grid">{award_html}</div></section><section class="section-pad credentials-section"><p class="eyebrow">CERTIFICATES</p><div class="credential-file-list">{cert_html}</div></section>'''
    return shell('Credentials','Awards, certificates and supporting verification material.','credentials',body)

def page_contact():
    body=f'''<section class="section-pad contact-hero"><h1 class="rough">CONTACT</h1><p class="contact-lead">Let&rsquo;s make the next thing useful. For website builds, WordPress development, e-commerce, maintenance, digital products or technical support, send me a note.</p><a class="contact-email" href="mailto:{esc(CONFIG['site']['email'])}">{esc(CONFIG['site']['email'])} ↗</a><p class="contact-note">Open to new projects. Typical response time: 24&ndash;48 hours.</p></section><section class="section-pad contact-grid-section"><div><p class="eyebrow">DETAILS</p><h2>{esc(CONFIG['site']['location'])}</h2><p><a href="tel:{esc(CONFIG['site']['phone'])}">{esc(CONFIG['site']['phone'])}</a></p></div><div class="contact-links"><a href="{esc(CONFIG['site']['github'])}" target="_blank" rel="noreferrer">GitHub ↗</a><span>LinkedIn · link can be added later</span><span>Instagram · link can be added later</span><a href="/odunayo-bolarinwa-portfolio.pdf" target="_blank">Full PDF portfolio ↗</a></div></section>'''
    return shell('Contact','Contact Odunayo Bolarinwa.','contact',body)

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(data, encoding='utf-8')

def main():
    asset_copy()
    projects=scan_projects()
    write(SITE/'index.html',page_index(projects))
    write(SITE/'works'/'index.html',page_works(projects))
    write(SITE/'about'/'index.html',page_about())
    write(SITE/'credentials'/'index.html',page_credentials())
    write(SITE/'contact'/'index.html',page_contact())
    related_pool=projects
    for i,p in enumerate(projects):
        related=[x for x in related_pool if x['slug']!=p['slug']][:3]
        write(SITE/'works'/p['slug']/'index.html',page_project(p,related))
    write(SITE/'404.html',shell('Not found','Page not found.','','<section class="section-pad page-intro"><p class="eyebrow">404</p><h1>That page wandered off.</h1><p>Go back to the work archive and keep exploring.</p><a href="/works/" class="button button-primary">Back to work ↗</a></section>'))
    # Basic crawlability for a static GitHub Pages portfolio.
    urls=['https://odgrande.github.io/','https://odgrande.github.io/works/','https://odgrande.github.io/about/','https://odgrande.github.io/credentials/','https://odgrande.github.io/contact/'] + [f'https://odgrande.github.io/works/{p["slug"]}/' for p in projects]
    sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u}</loc></url>' for u in urls)+'</urlset>'
    write(SITE/'sitemap.xml',sitemap)
    write(SITE/'robots.txt','User-agent: *\nAllow: /\nSitemap: https://odgrande.github.io/sitemap.xml\n')
    # keep a human-readable inventory for future edits
    (SITE/'assets'/'site-data.json').write_text(json.dumps(projects,indent=2),encoding='utf-8')
    print(f'Built {len(projects)} projects')
    print(f'Personal images: {len(list_personal_images())}; awards: {len(list_personal_awards())}; certificates: {len(list_credentials())}')

if __name__=='__main__': main()
