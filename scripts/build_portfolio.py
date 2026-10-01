from __future__ import annotations
import json, re, shutil
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"assets"
SOURCE=ASSETS/"Odunayo Portfolio Assets"
SITE=ROOT/"site"
CONFIG=json.loads((ROOT/"scripts/site_config.json").read_text(encoding="utf-8"))

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
                try:m.update(json.loads(f.read_text(encoding="utf-8")))
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

# This clip lives in the Olaedo Branding project folder but is a personal
# reel, not case-study material — it's pulled out of that project page and
# used on the Home page instead (see home_reel_video()).
HOME_REEL={"slug":"olaedo-branding-project","filename":"Odunayo Bolarinwa.mp4"}

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
            if slug==HOME_REEL["slug"]:
                m["videos"]=[v for v in m["videos"] if v.rsplit("/",1)[-1]!=quote(HOME_REEL["filename"])]
            hero=m.get("heroImage")
            if hero:
                match=next((im for im in m["images"] if im.rsplit("/",1)[-1]==quote(hero)),None)
                if match:m["images"]=[match]+[im for im in m["images"] if im!=match]
            # Optional distinct thumbnail for the Home page's Featured Works
            # card only — falls back to the project-page hero everywhere else
            # (work card on /works/, related-projects) when not set.
            featured_name=m.get("featuredImage")
            if featured_name:
                m["featuredHomeImage"]=next((im for im in m["images"] if im.rsplit("/",1)[-1]==quote(featured_name)),"")
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
    pv=resolve_dir("Personal Videos")
    cert=resolve_dir("Certifications")
    personal_target=SITE/"assets"/"personal"/"images";personal_target.mkdir(parents=True,exist_ok=True)
    for name,src in personal_files().items():
        shutil.copy2(src,personal_target/name)
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
    shutil.copy2(ROOT/"scripts"/"uplink-loader.html",SITE/"assets"/"theme"/"uplink-loader.html")

# ---------- shell / chrome ----------

def head(title,desc,canonical):
    return f'''<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Odunayo Bolarinwa</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://odgrande.github.io{canonical}">
<meta property="og:title" content="{esc(title)} · Odunayo Bolarinwa"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="https://odgrande.github.io/og-image.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/css/styles.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" defer></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js" defer></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js" defer></script>
</head>'''

NAV_LINKS=[("HOME","/"),("WORKS","/works/"),("ABOUT","/about/"),("CREDENTIALS","/credentials/"),("CONTACT","/contact/")]

THEME_TOGGLE_ICON='<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"><path fill="currentColor" d="M12 18a6 6 0 1 1 0-12a6 6 0 0 1 0 12Zm0-16a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0V3a1 1 0 0 1 1-1Zm0 18a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0v-1a1 1 0 0 1 1-1ZM4.22 4.22a1 1 0 0 1 1.42 0l.7.71a1 1 0 1 1-1.41 1.41l-.71-.7a1 1 0 0 1 0-1.42Zm13.44 13.44a1 1 0 0 1 1.42 0l.7.71a1 1 0 1 1-1.41 1.41l-.71-.7a1 1 0 0 1 0-1.42ZM1 12a1 1 0 0 1 1-1h1a1 1 0 1 1 0 2H2a1 1 0 0 1-1-1Zm18 0a1 1 0 0 1 1-1h1a1 1 0 1 1 0 2h-1a1 1 0 0 1-1-1ZM4.22 19.78a1 1 0 0 1 0-1.42l.7-.7a1 1 0 1 1 1.42 1.41l-.71.71a1 1 0 0 1-1.41 0Zm13.44-13.44a1 1 0 0 1 0-1.42l.71-.7a1 1 0 1 1 1.41 1.41l-.7.71a1 1 0 0 1-1.42 0Z"/></svg>'

def theme_toggle(cls=""):
    return f'<button class="theme-toggle {cls}" type="button" aria-label="Switch between dark and light mode" aria-pressed="false">{THEME_TOGGLE_ICON}</button>'

def nav():
    desktop="".join(f'<li><a href="{u}">{i+1}. {t}</a></li>' for i,(t,u) in enumerate(NAV_LINKS))
    mobile="".join(f'<li><a href="{u}">{t}</a></li>' for t,u in NAV_LINKS)
    close_icon='<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24"><path fill="#ffffff" d="M9 16h2V8H9v8Zm4 0h2V8h-2v8Zm-1 6q-2.075 0-3.9-.788t-3.175-2.137q-1.35-1.35-2.137-3.175T2 12q0-2.075.788-3.9t2.137-3.175q1.35-1.35 3.175-2.137T12 2q2.075 0 3.9.788t3.175 2.137q1.35 1.35 2.138 3.175T22 12q0 2.075-.788 3.9t-2.137 3.175q-1.35 1.35-3.175 2.138T12 22Zm0-2q3.35 0 5.675-2.325T20 12q0-3.35-2.325-5.675T12 4Q8.65 4 6.325 6.325T4 12q0 3.35 2.325 5.675T12 20Zm0-8Z"/></svg>'
    menu_icon='<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24"><path fill="#ffffff" d="m9.5 16.5l7-4.5l-7-4.5v9ZM12 22q-2.075 0-3.9-.788t-3.175-2.137q-1.35-1.35-2.137-3.175T2 12q0-2.075.788-3.9t2.137-3.175q1.35-1.35 3.175-2.137T12 2q2.075 0 3.9.788t3.175 2.137q1.35 1.35 2.138 3.175T22 12q0 2.075-.788 3.9t-2.137 3.175q-1.35 1.35-3.175 2.138T12 22Zm0-2q3.35 0 5.675-2.325T20 12q0-3.35-2.325-5.675T12 4Q8.65 4 6.325 6.325T4 12q0 3.35 2.325 5.675T12 20Zm0-8Z"/></svg>'
    return f'''<nav class="nav"><ul>{desktop}</ul>{theme_toggle("desktop-only")}<button class="menu-btn" id="nav-toggle" aria-label="Open navigation">{menu_icon}</button></nav>
<div class="mobile-nav" id="mobile-menu"><button class="close-btn" id="mobile-close" aria-label="Close navigation">{close_icon}</button><ul>{mobile}</ul>{theme_toggle()}</div>'''

def preloader():
    return '''<div id="preloader"><iframe id="preloader-frame" title="Loading" data-src="/assets/theme/uplink-loader.html" sandbox="allow-scripts" loading="eager"></iframe></div>'''

def gate():
    site=CONFIG["site"]
    return f'''<div id="gate"><div class="gate-inner">
<div class="gate-question" id="gateQuestion">
<p class="t-md">Before you go in</p>
<h2 class="h2">Do you want to experience my work?</h2>
<p class="t-sm" style="color:var(--muted)">A quick yes or no — either way, thanks for stopping by.</p>
<div class="gate-actions">
<button class="btn" id="gateYes" type="button">Yes, let's go</button>
<button class="btn" id="gateNo" type="button">No, not right now</button>
</div>
</div>
<div class="gate-question" id="gatePersuade">
<p class="t-md">Wait, really?</p>
<h2 class="t-lg">15+ live products across Nigeria, the UK, Canada and the USA — and not one of them has caught fire. Give me 10 seconds of scrolling, I promise it's worth it.</h2>
<div class="gate-actions">
<button class="btn" id="gatePersuadeYes" type="button">Okay, you've convinced me</button>
<button class="btn" id="gateStillLeaving" type="button">I'm still leaving</button>
</div>
</div>
<form class="gate-feedback" id="gateFeedback" data-email="{esc(site["email"])}">
<p class="t-xl">Alright, your loss. Mind telling me why?</p>
<textarea name="reason" placeholder="What would have made you want to stay? (optional)"></textarea>
<input type="email" name="email" placeholder="Your email (optional)">
<div class="gate-actions">
<button class="btn" type="submit">Send feedback &amp; leave</button>
<button class="btn" id="gateJustLeave" type="button">Just leave</button>
<button class="btn" id="gateSkip" type="button">Actually, take me in</button>
</div>
</form>
</div></div>'''

def cookie_banner():
    return '''<div id="cookie-banner">
<p class="t-sm">This site uses a little local storage to remember your theme preference and a couple of one-time prompts — nothing is tracked or sold. See the <a class="link-inline" href="/cookies/">Cookie Policy</a>.</p>
<div class="cookie-actions">
<button class="btn cookie-accept" type="button">Got it</button>
<button class="cookie-close" type="button" aria-label="Dismiss">&times;</button>
</div>
</div>'''

def exit_popup():
    site=CONFIG["site"]
    return f'''<div id="exit-popup"><div class="exit-inner">
<button class="exit-close" id="exitClose" type="button" aria-label="Close">&times;</button>
<div class="exit-question" id="exitQuestion">
<p class="t-md">Hold up — don't go yet</p>
<h2 class="t-lg">Leaving without dropping your genius idea here is basically a crime against innovation.</h2>
<p class="t-sm" style="color:var(--muted)">(Not a real crime. Please don't call the police.) Tell me what you're dreaming up — a website, an app, a wild 2am idea — and I'll turn it into something real.</p>
<div class="gate-actions">
<button class="btn" id="exitOpenForm" type="button">Okay, take my idea</button>
<button class="btn" id="exitDismiss" type="button">Maybe later</button>
</div>
</div>
<form class="gate-feedback" id="exitForm" data-email="{esc(site["email"])}">
<p class="t-xl">Go on then, impress me.</p>
<textarea name="idea" placeholder="My brilliant idea is..." required></textarea>
<input type="email" name="email" placeholder="Where should I send updates? (optional)">
<div class="gate-actions">
<button class="btn" type="submit">Send my idea</button>
<button class="btn" id="exitSkip" type="button">Never mind</button>
</div>
</form>
</div></div>'''

PRELOADER_SKIP_INLINE='<script>if(window.matchMedia("(prefers-reduced-motion: reduce)").matches){document.documentElement.classList.add("no-preloader")}try{if(localStorage.getItem("odTheme")==="light"){document.documentElement.setAttribute("data-theme","light")}}catch(e){}try{if(sessionStorage.getItem("odGateSeen")){document.documentElement.classList.add("gate-skip")}}catch(e){}</script>'

def shell(title,desc,body,canonical="/",show_cta=True):
    return f'''<!doctype html><html lang="en">{head(title,desc,canonical)}<body>{PRELOADER_SKIP_INLINE}{gate()}{preloader()}{nav()}<div class="wrap"><main>{body}</main>{cta_band() if show_cta else ""}{footer()}</div>{cookie_banner()}{exit_popup()}<script src="/assets/js/script.js" defer></script></body></html>'''

def cta_band():
    return '''<section class="cta-band" data-reveal><div class="container container-md" style="align-items:center">
<p class="t-md text-center">What's next?</p>
<h2 class="h2 text-center cta-rotate">Let's work together.</h2>
<p class="t-sm text-center" style="max-width:34rem">Have a WordPress build, e-commerce store or digital product in mind? Let's talk about it.</p>
<a class="btn" href="/contact/">Start a project</a>
</div></section>'''

def socials_list():
    site=CONFIG["site"]
    socials=[]
    if site.get("linkedin"):socials.append(("LINKEDIN",site["linkedin"]))
    if site.get("instagram"):socials.append(("INSTAGRAM",site["instagram"]))
    if site.get("facebook"):socials.append(("FACEBOOK",site["facebook"]))
    if site.get("whatsapp"):socials.append(("WHATSAPP",site["whatsapp"]))
    if site.get("github"):socials.append(("GITHUB",site["github"]))
    if site.get("twitter"):socials.append(("TWITTER",site["twitter"]))
    return socials

def footer():
    site=CONFIG["site"]
    social_html="".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t,u in socials_list())
    social_html+=f'<li><a href="mailto:{esc(site["email"])}">EMAIL</a></li>'
    nav_html="".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t,u in NAV_LINKS)
    return f'''<footer data-reveal><div class="footer-cols"><div><h3 class="h6">Socials</h3><ul>{social_html}</ul></div><div><h3 class="h6">Navigation</h3><ul>{nav_html}</ul></div></div>
<div class="footer-bottom"><p>Developed by Odgrande Digital</p><p>{esc(site["name"])} © 2026 All Rights Reserved · <a class="legal-link" href="/privacy/">Privacy</a> · <a class="legal-link" href="/cookies/">Cookies</a></p></div></footer>'''

# ---------- shared components ----------

def image_frame(src,alt,cls=""):
    if not src:
        return f'<div class="image-frame {cls}"><div class="frame-box" style="display:grid;place-items:center;background:var(--base-300)"><span class="t-md">NO IMAGE YET</span></div></div>'
    return f'''<div class="image-frame {cls}"><img class="barcode" src="/assets/theme/barcode.svg" alt=""><div class="frame-box"><img src="{esc(src)}" alt="{esc(alt)}" loading="lazy"></div></div>'''

def masonry_gallery(images,alt):
    if not images:return ""
    items="".join(f'<div class="masonry-item"><img src="{esc(x)}" alt="{esc(alt)}" loading="lazy"></div>' for x in images)
    return f'<div class="masonry">{items}</div>'

def bottom_mark():
    return '<div class="bottom-mark"><img class="symbol" src="/assets/theme/symbol-white.svg" alt=""><img class="barcode" src="/assets/theme/barcode.svg" alt=""></div>'

def accordion_box(items,resume=False):
    rows=[]
    for i,item in enumerate(items):
        if resume:
            title,place,period,text=item
            if text:
                trigger=f'<button class="accordion-trigger" type="button"><span class="t-xl">{esc(title)}</span>{CHEVRON}</button><p class="t-md place">{esc(place)}</p><p class="t-sm period">{esc(period)}</p>'
                rows.append(f'<div class="accordion-item">{trigger}<div class="accordion-content"><p class="t-sm">{esc(text)}</p></div></div>')
            else:
                static=f'<span class="t-xl">{esc(title)}</span><p class="t-md place">{esc(place)}</p><p class="t-sm period">{esc(period)}</p>'
                rows.append(f'<div class="accordion-item accordion-static">{static}</div>')
        else:
            title,text=item
            trigger=f'<button class="accordion-trigger" type="button"><span class="t-xl"><span class="num">{i+1}.</span> {esc(title)}</span>{CHEVRON}</button>'
            rows.append(f'<div class="accordion-item">{trigger}<div class="accordion-content"><p class="t-sm">{esc(text)}</p></div></div>')
    return f'<div class="accordion-box">{"".join(rows)}</div>{bottom_mark()}'

CHEVRON='<svg class="chevron" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 8 8"><path fill="#eeeade" d="M1.5 1L0 2.5l4 4l4-4L6.5 1L4 3.5L1.5 1z"/></svg>'

JOURNEY_STEPS=[
    ("First","Website Design.","GenM apprenticeship, 2018 — my start in web."),
    ("Then","Freelance Development.","Shipping for international clients on Upwork since 2021."),
    ("Today","I bridge design and code.","Founder, Odgrande Digital — 15+ live products across Nigeria, the UK, Canada and the USA."),
]

def journey_stepper():
    steps="".join(
        f'<div class="journey-step"><span class="t-md">{esc(label)}</span><p class="h3">{esc(line)}</p><p class="t-sm">{esc(sub)}</p></div>'
        for label,line,sub in JOURNEY_STEPS
    )
    return f'''<section class="container container-md" data-reveal>
<h2 class="h2 text-center">My Journey</h2>
</section>
<div class="journey-pin">{steps}</div>'''

def work_card(p,home=False):
    img=(p.get("featuredHomeImage") if home else "") or (p["images"][0] if p.get("images") else "")
    thumb=f'<img class="thumb" src="{esc(img)}" alt="{esc(p["title"])}" loading="lazy">' if img else f'<div class="empty-thumb"><span>{esc(p["title"][:2].upper())}</span></div>'
    return f'''<a class="work-card" href="/works/{esc(p["slug"])}/"><div class="frame"><div class="label"><span>{esc(p["category"])}</span><img src="/assets/theme/symbol.svg" alt=""></div><div class="texture"></div>{thumb}<div class="disk"></div></div><div class="meta"><h3 class="h4">{esc(p["title"])}</h3><p class="t-md">{esc(p["client"])}</p></div></a>'''

# ---------- personal / credential asset lookups ----------

PORTRAIT_HERO="black-white_optimized.jpg"
PORTRAIT_ABOUT="black white-1_optimized.jpg"
MAGIC_HERO="file_00000000a60881f8bf2abc22d8606f68.png"
MAGIC_STANDING="file_00000000451081f6b02cd0b215f4e2be.png"
# Mocked-up "Forbes" cover graphic — never publish it, it would falsely imply a real feature.
# Plus the ID-card photo, the two indoor/bathroom selfie shots, and low-quality
# car-interior selfies that don't belong in a curated personal archive.
ALWAYS_EXCLUDE={
    "file_0000000006cc81f9a556a2aa9b9e3550.png",
    "20260417_111702.jpg",
    "20250130_111431_optimized.jpg",
    "20250130_112225_optimized.jpg",
    "20250423_125219_optimized.jpg",
    "20250629_115614_optimized.jpg",
    "20210531_131547_optimized.jpg",
    "20210705_103013_optimized.jpg",
    "20210705_103026_optimized.jpg",
    "20210715_163148_optimized.jpg",
    "20210729_104107_optimized.jpg",
    "20210729_104127_optimized.jpg",
    "20220123_122746_optimized.jpg",
    "20230526_175357_optimized.jpg",
    "IMG_20230311_215616_130.jpg",
    # near-duplicate "magic" graphic variants — the two used elsewhere are the strongest
    "file_000000006f2c81f4aa6b0abb425255e3.png",
    "file_00000000779081f491717b18d417a638.png",
    "file_00000000b9fc81f9a34a6026ac0d5014.png",
    "file_00000000c38081f48a935ae28e6d8f27.png",
}
# A hand-picked, ordered selection for the Personal Archive — event photos,
# the studio portrait variant, and a spread of the AltSchool moments — rather
# than every file in the folder.
CURATED_ARCHIVE=[
    "IMG_20250418_220951_395_optimized.jpg",
    "IQO_8465-1_optimized.jpg",
    "20250129_092329_optimized.jpg",
    "20250128_095634_optimized.jpg",
    "IMG_20250125_163210_281.jpg",
    "20250129_092347_optimized.jpg",
    "IMG_20250125_163444_645.jpg",
    "WhatsApp Image 2026-09-29 at 1.25.13 PM.jpeg",
    "20250129_092335_optimized.jpg",
    "IMG_20250125_163806_325.jpg",
    "20250129_092352_optimized.jpg",
    "IMG_20250125_164016_488.jpg",
]

def resolve_dir(name):
    """Pick whichever copy of a top-level asset bucket (SOURCE vs ASSETS) has content."""
    a=SOURCE/name;b=ASSETS/name
    if a.exists() and (not b.exists() or _file_count(a)>=_file_count(b)):return a
    if b.exists():return b
    return a

def personal_files():
    """Merge both mirrors of "Personal images" by filename (ASSETS' structured
    copy wins on a clash), since either mirror can be missing files the other
    has — award images and subfolders like "Internship - CareerXpress" only
    exist in the structured copy, while some files were only ever added to
    the flat SOURCE copy."""
    merged={}
    for base in (SOURCE,ASSETS):
        d=base/"Personal images"
        if not d.exists():continue
        for p in d.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMG_EXT and p.parent.name.casefold()!="award images":
                merged[p.name]=p
    return merged

def personal_images():
    files=personal_files()
    return [path_url("assets","personal","images",name) for name in sorted(files,key=str.lower) if name not in ALWAYS_EXCLUDE]

def find_personal(name):
    files=personal_files()
    return path_url("assets","personal","images",name) if name in files else ""

def archive_images():
    files=personal_files()
    exclude={PORTRAIT_HERO,PORTRAIT_ABOUT,MAGIC_HERO,MAGIC_STANDING}
    exclude|={a.rsplit("/",1)[-1] for a in awards()}
    return [path_url("assets","personal","images",name) for name in CURATED_ARCHIVE if name in files and name not in exclude]

def testimonial_video():
    d=resolve_dir("Personal Videos")
    if not d.exists():return ""
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.suffix.lower() in VID_EXT:
            return path_url("assets","personal","videos",*p.relative_to(d).parts)
    return ""

def home_reel_video(projects):
    p=next((x for x in projects if x["slug"]==HOME_REEL["slug"]),None)
    d=source_for(HOME_REEL["slug"]) if p else None
    if not d:return ""
    f=d/HOME_REEL["filename"]
    return path_url("assets","projects",HOME_REEL["slug"],f.name) if f.exists() else ""

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
    featured=[p for p in projects if p.get("featured")]
    services=accordion_box(CONFIG["services"])
    faq=accordion_box(CONFIG["faq"])
    reel=home_reel_video(projects)
    body=f'''<section class="container container-xl hero" data-reveal>
<p class="t-xl tagline">Hey there! I'm a Full-Stack Web Developer &amp; Web Designer with 5+ years of experience building digital products for clients across Nigeria, the UK, Canada and the USA.</p>
<div class="hero-main">
<div class="hero-copy">
<a class="btn" href="/contact/">Available for work</a>
<h1 class="h1" data-split-text>{esc(site["name"])}</h1>
</div>
<div class="hero-photo">{image_frame(hero_portrait,site["name"])}</div>
</div>
</section>

<section class="container container-lg" style="align-items:center" data-reveal>
<h2 class="h2 text-center">Featured Works</h2>
<div class="work-grid">{"".join(work_card(p,home=True) for p in featured)}</div>
<a class="btn" href="/works/">All Works</a>
</section>

<section class="container container-md" data-reveal>
<h2 class="h2 text-center">Services</h2>
{services}
</section>

<section class="container container-xl" data-reveal>
<h2 class="h2 text-center">About</h2>
<div class="split">
<div class="split-copy">
<p class="t-xl">I'm a Full-Stack Web Developer and Web Designer who enjoys the point where a design stops being a picture and becomes a working product.</p>
<p class="t-sm">I build, customize and maintain WordPress, WooCommerce and Shopify stores, Webflow sites and custom front-end work for clients across Nigeria, the UK, Canada and the USA.</p>
<p class="t-sm">When I'm not building for a client, I'm usually improving my own tools, or picking apart a site to see how it was put together.</p>
<a class="btn" href="/about/">More about me</a>
</div>
<div class="split-photo">{image_frame(about_portrait,site["name"])}</div>
</div>
</section>

{f'''<section class="container container-md" style="align-items:center" data-reveal>
<h2 class="h2 text-center">A Quick Hello</h2>
<div class="video-frame"><video controls preload="metadata" playsinline poster="/assets/theme/video-poster.svg"><source src="{esc(reel)}"></video></div>
</section>''' if reel else ""}

<section class="container container-md" data-reveal>
<h2 class="h2 text-center">FAQ</h2>
{faq}
</section>'''
    return shell("Home",site["description"],body,"/")

def page_works(projects):
    body=f'''<section class="container container-lg" style="align-items:center" data-reveal>
<h1 class="h1 text-center">Works</h1>
<p class="t-sm text-center">{len(projects)} projects across WordPress, Shopify, Webflow, custom React &amp; PHP builds, e-commerce and brand work.</p>
<div class="work-grid">{"".join(work_card(p) for p in projects)}</div>
</section>'''
    return shell("Works","Websites, e-commerce builds, digital products, plugins and brand projects.",body,"/works/")

def related_projects(p,projects):
    others=[x for x in projects if x["slug"]!=p["slug"] and x.get("images")]
    same_category=[x for x in others if x["category"]==p["category"]]
    picks=(same_category+[x for x in others if x not in same_category])[:3]
    if not picks:return ""
    cards="".join(work_card(x) for x in picks)
    return f'<section class="container container-lg" style="align-items:center" data-reveal><h2 class="h2 text-center">More Work</h2><div class="work-grid">{cards}</div></section>'

def page_project(p,projects):
    hero=p["images"][0] if p.get("images") else ""
    rest=p["images"][1:] if p.get("images") else []
    facts=[("Client",p["client"]),("Category",p["category"]),("Services"," · ".join(p["services"])),("Year",p.get("year",""))]
    facts_html="".join(f'<div class="fact"><h4 class="h5">{esc(k)}</h4><p class="t-sm">{esc(v)}</p></div>' for k,v in facts)
    live_btn=f'<a class="btn" href="{esc(p["liveSite"])}" target="_blank" rel="noopener">Live Site</a>' if p.get("liveSite") else ""
    video_html=""
    if p.get("videos"):
        video_html="".join(f'<div class="project-video"><video controls preload="metadata" playsinline poster="/assets/theme/video-poster.svg"><source src="{esc(v)}"></video></div>' for v in p["videos"])
    gallery=masonry_gallery(rest,p["title"])
    body=f'''<section class="container container-xl" style="align-items:center" data-reveal>
<h1 class="h1 text-center">{esc(p["title"])}</h1>
<div class="hero-media" style="width:100%">{image_frame(hero,p["title"])}</div>
<div class="facts-row">{facts_html}</div>
{live_btn}
<div style="max-width:48rem"><p class="t-xl">{esc(p["description"])}</p></div>
{video_html}
{gallery}
<a class="btn" href="/works/">All Works</a>
</section>
{related_projects(p,projects)}'''
    return shell(p["title"],p["description"],body,f'/works/{p["slug"]}/')

def page_about():
    site=CONFIG["site"]
    magic_hero=find_personal(MAGIC_HERO)
    magic_standing=find_personal(MAGIC_STANDING)
    portrait=find_personal(PORTRAIT_ABOUT) or (personal_images()[0] if personal_images() else "")
    experience=accordion_box(CONFIG["experience"],resume=True)
    education=accordion_box(CONFIG["education"],resume=True)
    tags="".join(f"<span>{esc(x)}</span>" for x in CONFIG["capabilities"])
    certs="".join(f"<span>{esc(org)} — {esc(name)}</span>" for org,name,_,_ in CONFIG.get("certifications",[]))
    gallery=masonry_gallery(archive_images(),f'{site["name"]} personal archive')
    second_award=awards()[1] if len(awards())>1 else ""
    video=testimonial_video()
    quotes="".join(f'<blockquote class="testimonial"><p class="t-lg">&ldquo;{esc(t["quote"])}&rdquo;</p><cite class="t-md">{esc(t["name"])} · {esc(t["company"])}</cite></blockquote>' for t in CONFIG.get("testimonials",[]))
    video_html=f'<div class="video-frame"><video controls preload="metadata" playsinline poster="/assets/theme/video-poster.svg"><source src="{esc(video)}"></video></div>' if video else ""
    body=f'''<section class="container container-xl" data-reveal>
<h1 class="h1 text-center">Meet {esc(site["name"].split()[0])}</h1>
{f'<div class="magic-hero">{image_frame(magic_hero,"Let\'s create magic together")}</div>' if magic_hero else ""}
<div class="split">
<div class="split-copy">
<p class="t-xl">I build, customize and maintain websites for businesses, organizations and digital products.</p>
<p class="t-sm">My work sits between visual implementation and practical engineering. I am comfortable working inside WordPress and page builders, then dropping into PHP, JavaScript and CSS when the problem needs more than a visual editor.</p>
<p class="t-sm">Full-Stack Web Developer and Web Designer with 5+ years of experience building and maintaining digital products for clients across Nigeria, the UK, Canada and the USA.</p>
</div>
<div class="split-photo">{image_frame(portrait,site["name"])}</div>
</div>
</section>

{journey_stepper()}

{f'''<section class="container container-xl" data-reveal>
<div class="split split-reverse">
<div class="split-photo">{image_frame(magic_standing,"Let's create website magic")}</div>
<div class="split-copy">
<p class="t-xl">Let's create website magic.</p>
<p class="t-sm">Whatever the brief — a brand-new WordPress build, an e-commerce store, or a digital product that needs to feel alive — I'd love to help build it.</p>
<a class="btn" href="/contact/">Start a project</a>
<div class="social-row">{"".join(f'<a href="{esc(u)}" target="_blank" rel="noopener" class="link-inline">{esc(t)}</a>' for t,u in socials_list())}</div>
</div>
</div>
</section>''' if magic_standing else ""}

<section class="container container-md" data-reveal>
<h2 class="h2 text-center">Experience</h2>
{experience}
</section>

<section class="container container-md" data-reveal>
<h2 class="h2 text-center">Education</h2>
{education}
</section>

<section class="container container-md" data-reveal>
<h2 class="h2 text-center">Toolkit</h2>
<div class="tag-list">{tags}</div>
</section>

{f'''<section class="container container-md" data-reveal>
<h2 class="h2 text-center">Certifications</h2>
<div class="tag-list">{certs}</div>
</section>''' if certs else ""}

{f'''<section class="container container-md" data-reveal>
<div class="credential-single">{image_frame(second_award,"Designer Of The Year award")}<h3 class="h5 text-center">Designer Of The Year</h3></div>
</section>''' if second_award else ""}

{f'''<section class="container container-xl" data-reveal>
<h2 class="h2 text-center">In Their Words</h2>
<div class="testimonial-grid">{quotes}</div>
{video_html}
</section>''' if quotes or video else ""}

<section class="container container-xl" data-reveal>
<h2 class="h2 text-center">Personal Archive</h2>
{gallery}
<a class="btn" href="/credentials/">View Credentials</a>
</section>'''
    return shell("About",f"About {site['name']}, Full-Stack Web Developer and Web Designer.",body,"/about/")

def page_credentials():
    a=awards()
    award_html=f'<div class="credential-single">{image_frame(a[0],"Designer Of The Year award")}<h3 class="h5 text-center">Designer Of The Year</h3></div>' if a else '<p class="t-sm text-center">No award image yet.</p>'
    cert_cards=""
    for org,name,url,pdf in CONFIG.get("certifications",[]):
        pdf_link=f'<a class="t-xsm link-inline" href="{esc(pdf)}" target="_blank" rel="noopener">View PDF</a>' if pdf else ""
        cert_cards+=f'<div class="contact-item"><div class="row"><span class="t-lg">{esc(org)}</span><img src="/assets/theme/symbol-white.svg" alt=""></div><div class="divider"></div><a class="t-sm link-inline" href="{esc(url or "#")}" target="_blank" rel="noopener">{esc(name)}</a>{pdf_link}</div>'
    body=f'''<section class="container container-md" data-reveal>
<h1 class="h1 text-center">Credentials</h1>
{award_html}
</section>
<section class="container container-md" data-reveal>
<h2 class="h2 text-center">Certificates</h2>
<div class="contact-grid">{cert_cards}</div>
</section>'''
    return shell("Credentials","Credentials and recognition archive.",body,"/credentials/")

def page_contact():
    site=CONFIG["site"]
    items=[("Email",site["email"],f'mailto:{site["email"]}')]
    if site.get("phone"):items.append(("Phone",site["phone"],f'tel:{site["phone"]}'))
    if site.get("location"):items.append(("Location",site["location"],None))
    for label,url in socials_list():
        items.append((label.title(),url,url))
    cards="".join(
        f'<div class="contact-item"><div class="row"><span class="t-lg">{esc(k)}</span><img src="/assets/theme/symbol-white.svg" alt=""></div><div class="divider"></div>'
        + (f'<a class="t-sm link-inline" href="{esc(href)}" target="_blank" rel="noopener">{esc(v)}</a>' if href else f'<p class="t-sm">{esc(v)}</p>')
        + '</div>'
        for k,v,href in items
    )
    body=f'''<section class="container container-xl text-center" style="align-items:center" data-reveal>
<h1 class="h1">Contact</h1>
<div style="max-width:44rem;display:flex;flex-direction:column;gap:1rem">
<p class="t-xl">Let's build something together.</p>
<p class="t-sm">Have a website, e-commerce build, WordPress problem or digital product in mind? Tell me what you're working on and I'll get back to you within a day or two.</p>
</div>
</section>
<section class="container container-md">
<div class="contact-grid">{cards}</div>
</section>'''
    return shell("Contact",f"Contact {site['name']} for WordPress development, e-commerce and digital product work.",body,"/contact/",show_cta=False)

def legal_page(title,desc,canonical,sections):
    body_sections="".join(
        f'<div style="display:flex;flex-direction:column;gap:.75rem"><h2 class="h3">{esc(h)}</h2><p class="t-sm">{p}</p></div>'
        for h,p in sections
    )
    body=f'''<section class="container container-md" data-reveal>
<h1 class="h1 text-center">{esc(title)}</h1>
<p class="t-sm text-center" style="color:var(--muted)">Last updated October 2026.</p>
<div style="display:flex;flex-direction:column;gap:2.5rem;margin-top:1rem">{body_sections}</div>
</section>'''
    return shell(title,desc,body,canonical,show_cta=False)

def page_privacy():
    site=CONFIG["site"]
    sections=[
        ("What this site is","This is Odunayo Bolarinwa's personal portfolio — a static site with no user accounts, no server-side database and no backend application. There is no tracking pixel, analytics script or advertising network installed on any page."),
        ("What's stored on your device","A few small, non-identifying values in your browser's own local and session storage: your light/dark theme choice, and whether you've already seen the one-time landing question and the cookie notice this session. None of this is sent anywhere or shared with any third party — see the <a class=\"link-inline\" href=\"/cookies/\">Cookie Policy</a> for the exact list."),
        ("Information you choose to send","If you use the Contact page, the landing question's feedback form, or email/WhatsApp links directly, your message goes straight to Odunayo's inbox (or WhatsApp) the normal way your email client or WhatsApp sends it — this site has no form backend of its own and never stores what you write."),
        ("Hosting","This site is hosted on GitHub Pages. GitHub may keep standard server access logs (such as IP address and request time) as part of operating its hosting infrastructure; that is governed by GitHub's own privacy policy, not this one, since this site has no access to those logs."),
        ("Contact",f'Questions about this policy can be sent to <a class="link-inline" href="mailto:{esc(site["email"])}">{esc(site["email"])}</a>.'),
    ]
    return legal_page("Privacy Policy",f"Privacy policy for {site['name']}'s portfolio site.","/privacy/",sections)

def page_cookies():
    site=CONFIG["site"]
    sections=[
        ("The short version","This site doesn't use tracking or advertising cookies. It uses your browser's local and session storage — technically not cookies, but covered here for the same reason — to remember a few small preferences on your own device."),
        ("What's stored, exactly",'''<ul style="margin:0;padding-left:1.2rem;list-style:disc;display:flex;flex-direction:column;gap:.4rem">
<li><code>odTheme</code> — your light/dark mode choice, kept until you change it again (local storage).</li>
<li><code>odGateSeen</code> — whether you've already answered the one-time landing question this browser session (session storage, cleared when you close the tab).</li>
<li><code>odCookieNoticeSeen</code> — whether you've dismissed this cookie notice this session (session storage).</li>
</ul>'''),
        ("Third parties","Fonts are loaded from Google Fonts, and the animation libraries (GSAP, Three.js) are loaded from the cdnjs CDN. Both may see a standard request (your IP address, browser user-agent) as part of serving those files, the same as any site that loads a web font or script from a CDN — this site doesn't add any tracking on top of that."),
        ("Your control","Clearing your browser's site data for odgrande.github.io removes all of the above. Since none of it is sent to a server, there's nothing further to delete on this end."),
        ("Contact",f'Questions about this policy can be sent to <a class="link-inline" href="mailto:{esc(site["email"])}">{esc(site["email"])}</a>.'),
    ]
    return legal_page("Cookie Policy",f"Cookie and local storage policy for {site['name']}'s portfolio site.","/cookies/",sections)

def main():
    projects=scan_projects();copy_assets()
    (SITE/"index.html").write_text(page_home(projects),encoding="utf-8")
    (SITE/"works").mkdir();(SITE/"works"/"index.html").write_text(page_works(projects),encoding="utf-8")
    for p in projects:
        d=SITE/"works"/p["slug"];d.mkdir(parents=True)
        (d/"index.html").write_text(page_project(p,projects),encoding="utf-8")
    (SITE/"about").mkdir();(SITE/"about"/"index.html").write_text(page_about(),encoding="utf-8")
    (SITE/"credentials").mkdir();(SITE/"credentials"/"index.html").write_text(page_credentials(),encoding="utf-8")
    (SITE/"contact").mkdir();(SITE/"contact"/"index.html").write_text(page_contact(),encoding="utf-8")
    (SITE/"privacy").mkdir();(SITE/"privacy"/"index.html").write_text(page_privacy(),encoding="utf-8")
    (SITE/"cookies").mkdir();(SITE/"cookies"/"index.html").write_text(page_cookies(),encoding="utf-8")
    print(f"Built {len(projects)} projects")

if __name__=="__main__":main()
