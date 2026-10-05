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
NON_PROJECT_DIRS={"projects","credentials","personal","odunayo portfolio assets","certifications","personal images","personal videos","theme",".optimized","highlights"}

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
            # excludeImages (site_config): files sitting in a project folder that
            # don't belong to that project (stray personal photos, receipts,
            # another project's artwork) and must never be shown on it.
            skip={"project.json","meta.json",*m.get("excludeImages",[])}
            files=[p for p in d.rglob("*") if p.is_file() and p.name not in skip]
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
    # Evidence images for project "Featured build" panels.
    if (ASSETS/"highlights").exists():shutil.copytree(ASSETS/"highlights",SITE/"assets"/"highlights",dirs_exist_ok=True)
    theme=ASSETS/"theme"
    if theme.exists():shutil.copytree(theme,SITE/"assets"/"theme",dirs_exist_ok=True)
    public=ROOT/"public"
    for n in ("favicon.ico","favicon-32.png","icon-192.png","apple-touch-icon.png","og-image.jpg","odunayo-bolarinwa-portfolio.pdf","odunayo-bolarinwa-cv.pdf"):
        f=public/n
        if f.exists():shutil.copy2(f,SITE/n)
    (SITE/"assets"/"css").mkdir(parents=True);(SITE/"assets"/"js").mkdir(parents=True)
    shutil.copy2(ROOT/"scripts"/"styles.css",SITE/"assets"/"css"/"styles.css")
    shutil.copy2(ROOT/"scripts"/"script.js",SITE/"assets"/"js"/"script.js")
    # Libraries are self-hosted (same origin = no extra DNS/TLS round trip and
    # no dependency on a third-party CDN being fast before the gate works).
    shutil.copytree(ROOT/"scripts"/"vendor",SITE/"assets"/"js"/"vendor")
    shutil.copy2(ROOT/"scripts"/"uplink-loader.html",SITE/"assets"/"theme"/"uplink-loader.html")

# ---------- shell / chrome ----------

# Cache-busting: each page links styles.css / script.js with a short hash of
# the file's contents, so browsers fetch the new version after every deploy
# instead of reusing a stale cached copy.
def _short_hash(path):
    import hashlib
    return hashlib.sha1(path.read_bytes()).hexdigest()[:10]
ASSET_V={"css":_short_hash(ROOT/"scripts"/"styles.css"),"js":_short_hash(ROOT/"scripts"/"script.js")}

# Browser-tab / link-preview title: name + a short line on what I do.
TAGLINE="Full-Stack Developer Who Designs"

def page_title(title):
    if title=="Home":return f"Odunayo Bolarinwa · {TAGLINE}"
    return f"{title} · Odunayo Bolarinwa | {TAGLINE}"

def head(title,desc,canonical):
    full=esc(page_title(title)); url=f"https://odunayobolarinwa.com{canonical}"
    # Link previews (WhatsApp, X, LinkedIn, Slack...) use og-image.jpg: the
    # About page hero, framed for the 1200x630 preview format.
    return f'''<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{full}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Odunayo Bolarinwa"><meta property="og:url" content="{url}">
<meta property="og:title" content="{full}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="https://odunayobolarinwa.com/og-image.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Odunayo Bolarinwa, Odgrande Digital CEO: Let's create magic together">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:site" content="@ceodgrande"><meta name="twitter:title" content="{full}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="https://odunayobolarinwa.com/og-image.jpg">
<link rel="preload" href="/assets/theme/fonts/road-rage-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/theme/fonts/jetbrains-mono-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32"><link rel="icon" href="/icon-192.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="stylesheet" href="/assets/css/styles.css?v={ASSET_V['css']}">
<script src="/assets/js/vendor/gsap.min.js" defer></script>
<script src="/assets/js/vendor/ScrollTrigger.min.js" defer></script>
</head>'''

NAV_LINKS=[("HOME","/"),("WORKS","/works/"),("ABOUT","/about/"),("CREDENTIALS","/credentials/"),("CONTACT","/contact/")]

THEME_TOGGLE_ICON='<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"><path fill="currentColor" d="M12 18a6 6 0 1 1 0-12a6 6 0 0 1 0 12Zm0-16a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0V3a1 1 0 0 1 1-1Zm0 18a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0v-1a1 1 0 0 1 1-1ZM4.22 4.22a1 1 0 0 1 1.42 0l.7.71a1 1 0 1 1-1.41 1.41l-.71-.7a1 1 0 0 1 0-1.42Zm13.44 13.44a1 1 0 0 1 1.42 0l.7.71a1 1 0 1 1-1.41 1.41l-.71-.7a1 1 0 0 1 0-1.42ZM1 12a1 1 0 0 1 1-1h1a1 1 0 1 1 0 2H2a1 1 0 0 1-1-1Zm18 0a1 1 0 0 1 1-1h1a1 1 0 1 1 0 2h-1a1 1 0 0 1-1-1ZM4.22 19.78a1 1 0 0 1 0-1.42l.7-.7a1 1 0 1 1 1.42 1.41l-.71.71a1 1 0 0 1-1.41 0Zm13.44-13.44a1 1 0 0 1 0-1.42l.71-.7a1 1 0 1 1 1.41 1.41l-.7.71a1 1 0 0 1-1.42 0Z"/></svg>'

def xray_toggle(cls=""):
    # X-ray mode: flips the page into a blueprint that labels the tech behind
    # each section (see script.js). Off by default.
    return f'<button class="xray-toggle {cls}" type="button" aria-label="Toggle X-ray mode: see the code behind the design" aria-pressed="false" title="X-ray mode (press X)"><span aria-hidden="true">X</span></button>'

def theme_toggle(cls=""):
    return f'<button class="theme-toggle {cls}" type="button" aria-label="Switch between dark and light mode" aria-pressed="false">{THEME_TOGGLE_ICON}</button>'

LANGS=[("en","EN"),("pcm","Pidgin"),("yo","Yoruba"),("ha","Hausa"),("fr","Français")]

def lang_switcher(cls=""):
    options="".join(f'<button class="lang-option" type="button" data-lang="{code}">{esc(label)}</button>' for code,label in LANGS)
    return f'''<div class="lang-switcher {cls}">
<button class="lang-toggle" type="button" aria-label="Change language" aria-expanded="false">&#127760; <span class="lang-current">EN</span></button>
<div class="lang-menu">{options}</div>
</div>'''

NAV_KEYS=["home","works","about","credentials","contact"]

def nav(current="/"):
    # The link for the section you're in (project pages count as Works) is
    # marked aria-current="page" and drawn faded, so you always know where
    # you are.
    def cur(u):
        return ' aria-current="page"' if (current==u if u=="/" else current.startswith(u)) else ""
    desktop="".join(f'<li><a href="{u}"{cur(u)}>{i+1}. <span data-i18n="nav_{k}">{t}</span></a></li>' for i,((t,u),k) in enumerate(zip(NAV_LINKS,NAV_KEYS)))
    mobile="".join(f'<li><a href="{u}"{cur(u)}><span data-i18n="nav_{k}">{t}</span></a></li>' for (t,u),k in zip(NAV_LINKS,NAV_KEYS))
    close_icon='<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" class="close-icon" aria-hidden="true"><path d="M5 5L19 19M19 5L5 19" fill="none" stroke-width="2.2" stroke-linecap="round"/></svg>'
    # Same outlined-circle language as the theme toggle and language pill:
    # two short bars of unequal length (like the site's underlines) that
    # even out on hover/tap.
    menu_icon='''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" class="hamburger-icon" aria-hidden="true">
<rect class="menu-bar menu-bar-1" x="1" y="4" width="14" height="2" rx="1"/>
<rect class="menu-bar menu-bar-2" x="1" y="10" width="9" height="2" rx="1"/>
</svg>'''
    name=esc(CONFIG["site"]["name"])
    logo=f'<a href="/" class="nav-logo" aria-label="{name} — home"><img src="/assets/theme/logo.png" alt="" width="112" height="126"></a>'
    return f'''<nav class="nav">{logo}<ul>{desktop}</ul>{xray_toggle("desktop-only")}{theme_toggle("desktop-only")}{lang_switcher("desktop-only")}<button class="menu-btn" type="button" id="nav-toggle" aria-label="Open navigation">{menu_icon}</button></nav>
<div class="mobile-nav" id="mobile-menu"><div class="mobile-nav-controls">{xray_toggle()}{theme_toggle()}{lang_switcher()}</div><button class="close-btn" type="button" id="mobile-close" aria-label="Close navigation">{close_icon}</button><a href="/" class="mobile-nav-logo" aria-label="{name} — home"><img src="/assets/theme/logo.png" alt="" width="112" height="126"></a><ul>{mobile}</ul></div>'''

def preloader():
    return '''<div id="preloader"><iframe id="preloader-frame" title="Loading" data-src="/assets/theme/uplink-loader.html" sandbox="allow-scripts" loading="eager"></iframe></div>'''

def gate():
    site=CONFIG["site"]
    # Live Lagos time with an inline Nigerian flag (an SVG, not an emoji:
    # Windows doesn't render flag emoji, it shows the letters "NG").
    clock=('<div class="gate-clock" aria-label="Local time in Lagos, Nigeria">'
           '<svg class="ng-flag" viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#008751"/><rect x="2" width="1" height="2" fill="#008751"/></svg>'
           '<span class="gate-city">Lagos, Nigeria</span><span class="gate-time" id="gateTime">--:--</span></div>')
    return f'''<div id="gate">{clock}<div class="gate-controls">{theme_toggle()}{lang_switcher("gate-lang")}</div><div class="gate-inner">
<div class="gate-question" id="gateQuestion">
<p class="t-md" data-i18n="gate_eyebrow">Knock, knock</p>
<h2 class="gate-title"><span data-i18n="gate_headline">Come on in. The websites don't bite.</span> <svg class="gate-smile" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10.4" fill="none" stroke="currentColor" stroke-width="2.2"/><circle cx="8.4" cy="9.6" r="1.55" fill="currentColor"/><circle cx="15.6" cy="9.6" r="1.55" fill="currentColor"/><path d="M7.3 14.2c1.1 2.1 2.8 3.2 4.7 3.2s3.6-1.1 4.7-3.2" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg></h2>
<p class="t-sm gate-sub" style="color:var(--muted)"><span data-i18n="gate_subtext">Well, only the bugs bite, and I squashed every one of them.</span><br><span data-i18n="gate_subtext2">Ready to look around?</span></p>
<div class="gate-actions">
<button class="btn" id="gateYes" type="button" data-i18n="gate_yes">Yes, let me in</button>
<button class="btn" id="gateNo" type="button" data-i18n="gate_no">No, I'll pass</button>
</div>
</div>
<div class="gate-question" id="gatePersuade">
<p class="t-md" data-i18n="g_p_eyebrow">Wait, really?</p>
<h2 class="t-lg" data-i18n="g_p_head">15+ live products across Nigeria, the UK, Canada and the USA — and not one of them has caught fire. Give me 10 seconds of scrolling, I promise it's worth it.</h2>
<div class="gate-actions">
<button class="btn" id="gatePersuadeYes" type="button" data-i18n="g_p_yes">Okay, you've convinced me</button>
<button class="btn" id="gateStillLeaving" type="button" data-i18n="g_p_leave">I'm still leaving</button>
</div>
</div>
<form class="gate-feedback" id="gateFeedback" data-whatsapp="{esc(site["whatsapp"])}">
<p class="t-xl" data-i18n="g_f_head">Alright, your loss. Mind telling me why?</p>
<textarea name="reason" data-i18n-ph="g_f_reason_ph" placeholder="What would have made you want to stay? (optional)"></textarea>
<input type="email" name="email" data-i18n-ph="g_f_email_ph" placeholder="Your email (optional)">
<div class="gate-actions">
<button class="btn" type="submit" data-i18n="g_f_send">Send feedback &amp; leave</button>
<button class="btn" id="gateJustLeave" type="button" data-i18n="g_f_just">Just leave</button>
<button class="btn" id="gateSkip" type="button" data-i18n="g_f_skip">Actually, take me in</button>
</div>
</form>
</div></div>'''

def cookie_banner():
    return '''<div id="cookie-banner">
<p class="t-sm"><span data-i18n="ck_text">This site uses a little browser storage to remember your theme and language for this visit and a couple of one-time prompts — nothing is tracked or sold. See the</span> <a class="link-inline" href="/cookies/"><span data-i18n="ck_link">Cookie Policy</span></a>.</p>
<div class="cookie-actions">
<button class="btn cookie-accept" type="button" data-i18n="ck_ok">Got it</button>
<button class="cookie-close" type="button" aria-label="Dismiss">&times;</button>
</div>
</div>'''

def exit_popup():
    site=CONFIG["site"]
    return f'''<div id="exit-popup"><div class="exit-inner">
<button class="exit-close" id="exitClose" type="button" aria-label="Close">&times;</button>
<div class="exit-question" id="exitQuestion">
<p class="t-md" data-i18n="x_eyebrow">Hold up — don't go yet</p>
<h2 class="t-xl" data-i18n="x_head">Leaving without dropping your genius idea here is basically a crime against innovation.</h2>
<p class="t-sm" style="color:var(--muted)" data-i18n="x_sub">(Not a real crime. Please don't call the police.) Tell me what you're dreaming up — a website, an app, a wild 2am idea — and I'll turn it into something real.</p>
<div class="gate-actions">
<button class="btn" id="exitOpenForm" type="button" data-i18n="x_yes">Okay, take my idea</button>
<button class="btn" id="exitDismiss" type="button" data-i18n="x_later">Maybe later</button>
</div>
</div>
<form class="gate-feedback" id="exitForm" data-whatsapp="{esc(site["whatsapp"])}">
<p class="t-xl" data-i18n="x_f_head">Go on then, impress me.</p>
<textarea name="idea" data-i18n-ph="x_idea_ph" placeholder="My brilliant idea is..." required></textarea>
<input type="email" name="email" data-i18n-ph="x_email_ph" placeholder="Where should I send updates? (optional)">
<div class="gate-actions">
<button class="btn" type="submit" data-i18n="x_send">Send my idea</button>
<button class="btn" id="exitSkip" type="button" data-i18n="x_never">Never mind</button>
</div>
</form>
</div></div>'''

PRELOADER_SKIP_INLINE='<script>document.documentElement.classList.add("no-scroll","veil");if(window.matchMedia("(prefers-reduced-motion: reduce)").matches){document.documentElement.classList.add("no-preloader")}try{localStorage.removeItem("odTheme");if(sessionStorage.getItem("odTheme")==="light"){document.documentElement.setAttribute("data-theme","light")}}catch(e){}try{if(sessionStorage.getItem("odPreloaderSeen")){document.documentElement.classList.add("no-preloader")}}catch(e){}try{if(sessionStorage.getItem("odGateSeen")){document.documentElement.classList.add("gate-skip");setTimeout(function(){document.documentElement.classList.remove("veil","no-scroll")},12000)}}catch(e){}</script>'

def shell(title,desc,body,canonical="/",show_cta=True,bare=False):
    # bare=True (the shareable /start/ brief): no landing gate, loading screen
    # or exit pop-up, so a prospect opening the link goes straight in.
    return f'''<!doctype html><html lang="en">{head(title,desc,canonical)}<body>{PRELOADER_SKIP_INLINE}{"" if bare else gate()}{"" if bare else preloader()}{nav(canonical)}<div class="wrap"><main>{body}</main>{cta_band() if show_cta else ""}{footer()}</div>{cookie_banner()}{"" if bare else exit_popup()}<script src="/assets/js/script.js?v={ASSET_V['js']}" defer></script></body></html>'''

def cta_band():
    return '''<section class="cta-band" data-reveal><div class="cta-3d" aria-hidden="true"></div><div class="container container-md" style="align-items:center">
<p class="t-md text-center" data-i18n="footer_whats_next">What's next?</p>
<h2 class="h2 text-center cta-rotate" data-i18n="footer_cta_heading">Let's work together.</h2>
<p class="t-sm text-center" style="max-width:34rem" data-i18n="footer_cta_sub">Have a WordPress build, e-commerce store or digital product in mind? Let's talk about it.</p>
<a class="btn" href="/start/"><span data-i18n="start_project_btn">Start a project</span></a>
</div></section>'''

def socials_list():
    site=CONFIG["site"]
    socials=[]
    if site.get("linkedin"):socials.append(("LINKEDIN",site["linkedin"]))
    if site.get("instagram"):socials.append(("INSTAGRAM",site["instagram"]))
    if site.get("twitter"):socials.append(("X (TWITTER)",site["twitter"]))
    if site.get("facebook"):socials.append(("FACEBOOK",site["facebook"]))
    if site.get("whatsapp"):socials.append(("WHATSAPP",site["whatsapp"]))
    if site.get("github"):socials.append(("GITHUB",site["github"]))
    return socials

def footer():
    site=CONFIG["site"]
    social_html="".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t,u in socials_list())
    social_html+=f'<li><a href="mailto:{esc(site["email"])}">EMAIL</a></li>'
    nav_html="".join(f'<li><a href="{u}"><span data-i18n="nav_{k}">{esc(t)}</span></a></li>' for (t,u),k in zip(NAV_LINKS,NAV_KEYS))
    return f'''<footer data-reveal><a href="/" class="footer-logo" aria-label="{esc(site["name"])} — home"><img src="/assets/theme/logo.png" alt="">{esc(site["name"])}</a><div class="footer-cols"><div><h3 class="h6" data-i18n="footer_socials_heading">Socials</h3><ul>{social_html}</ul></div><div><h3 class="h6" data-i18n="footer_nav_heading">Navigation</h3><ul>{nav_html}</ul></div></div>
<div class="footer-bottom"><p data-i18n="ft_crafted" data-i18n-n="{esc(site["name"])}">Crafted with joy by {esc(site["name"])}</p><p>© 2026 <span data-i18n="ft_rights">All Rights Reserved</span></p><p class="t-xsm"><a class="legal-link" href="/privacy/"><span data-i18n="footer_privacy">Privacy</span></a> · <a class="legal-link" href="/cookies/"><span data-i18n="footer_cookies">Cookies</span></a> · <a class="legal-link" href="/sitemap/"><span data-i18n="footer_sitemap">Sitemap</span></a><span id="visitor-clock-wrap" style="display:none"> · <span id="visitor-clock"></span></span></p></div></footer>'''

# ---------- shared components ----------

def wa_barcode(cls=""):
    # The original decorative barcode mark, unchanged in look, made tappable:
    # it opens a WhatsApp chat.
    wa=CONFIG["site"].get("whatsapp","")
    return (f'<a class="barcode-link {cls}" href="{esc(wa)}" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">'
            f'<img class="barcode" src="/assets/theme/barcode.svg" alt=""></a>')

def placeholder(title,sub=""):
    # Shown wherever a project has no visuals yet: a "case file" card in the
    # site's own language (hatched dark paper, proof corner marks, the name
    # in the display face, a tilted rubber stamp) instead of an empty box.
    return (f'<div class="ph" role="img" aria-label="{esc(title)}: visuals coming soon">'
            f'<i class="ph-corner tl"></i><i class="ph-corner tr"></i><i class="ph-corner bl"></i><i class="ph-corner br"></i>'
            f'{f"<span class=ph-cat>{esc(sub)}</span>" if sub else ""}'
            f'<span class="ph-title">{esc(title)}</span>'
            f'<span class="ph-stamp" data-i18n="ph_stamp">Visuals coming soon</span></div>')

def image_frame(src,alt,cls="",sub=""):
    if not src:
        return f'<div class="image-frame {cls}"><div class="frame-box frame-ph">{placeholder(alt,sub)}</div></div>'
    # Portraits sit at the top of Home/About: fetch them first, not lazily.
    load='loading="eager" fetchpriority="high"' if "portrait" in cls else 'loading="lazy"'
    return f'''<div class="image-frame {cls}">{wa_barcode()}<div class="frame-box"><img src="{esc(src)}" alt="{esc(alt)}" {load}></div></div>'''

MQ_KEYS={"Full-Stack Developer":"mq_fullstack","Web Designer":"mq_webdesigner","Let's Build Something Great":"mq_build","Open For Work":"mq_open","4 Countries":"mq_countries","Zero Templates":"mq_zero"}
def mq_attr(phrase):
    # Translatable marquee words; "21 Projects" keeps its live count via data-i18n-n.
    m=re.fullmatch(r"(\d+) Projects",phrase)
    if m: return f' data-i18n="mq_projects" data-i18n-n="{m.group(1)}"'
    return f' data-i18n="{MQ_KEYS[phrase]}"' if phrase in MQ_KEYS else ""

def marquee(phrases):
    # Two full-bleed bands crossing in a shallow X — a paper one and an ink
    # one, running in opposite directions. Words alternate display / mono type
    # with a spinning star between them. script.js drives the motion (and
    # couples it to scroll speed/direction); the CSS animation is the
    # no-JS fallback. Six copies of the group keep the loop seamless on
    # ultra-wide screens (the track animates exactly half its width).
    def band(cls,offset):
        words=phrases[offset:]+phrases[:offset]
        group="".join(f'<span class="mq-item{" mq-alt" if i%2 else ""}"{mq_attr(p)}>{esc(p)}</span><span class="mq-star" aria-hidden="true">✦</span>' for i,p in enumerate(words))
        return f'<div class="mq-band {cls}"><div class="mq-track">{group*6}</div></div>'
    label=esc(" · ".join(phrases))
    return f'<div class="marquee" role="img" aria-label="{label}">{band("mq-a",0)}{band("mq-b",1 if len(phrases)>1 else 0)}</div>'

def masonry_gallery(images,alt,shots=False):
    if not images:return ""
    items="".join(f'<div class="masonry-item"><img src="{esc(x)}" alt="{esc(alt)}" loading="lazy"></div>' for x in images)
    cls="masonry masonry-shots" if shots else "masonry"
    return f'<div class="{cls}">{items}</div>'

def bento_gallery(images,alt):
    # Compact square-tile grid; the first photo is a 2x2 feature tile. With 9
    # photos it fills exactly: 4 cols x 3 rows on desktop, 3 x 4 on phones.
    if not images:return ""
    items="".join(f'<figure class="bento-item{" bento-feature" if i==0 else ""}"><img src="{esc(x)}" alt="{esc(alt)}" loading="lazy"></figure>' for i,x in enumerate(images))
    return f'<div class="bento">{items}</div>'

def bottom_mark():
    return f'<div class="bottom-mark"><img class="symbol" src="/assets/theme/symbol-white.svg" alt="">{wa_barcode("barcode-sm")}</div>'

def accordion_box(items,resume=False,i18n_prefix=None):
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
            q_attr=f' data-i18n="{i18n_prefix}_q_{i}"' if i18n_prefix else ""
            a_attr=f' data-i18n="{i18n_prefix}_a_{i}"' if i18n_prefix else ""
            trigger=f'<button class="accordion-trigger" type="button"><span class="t-xl"><span class="num">{i+1}.</span> <span{q_attr}>{esc(title)}</span></span>{CHEVRON}</button>'
            rows.append(f'<div class="accordion-item">{trigger}<div class="accordion-content"><p class="t-sm"{a_attr}>{esc(text)}</p></div></div>')
    return f'<div class="accordion-box">{"".join(rows)}</div>{bottom_mark()}'

CHEVRON='<svg class="chevron" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 8 8"><path fill="#eeeade" d="M1.5 1L0 2.5l4 4l4-4L6.5 1L4 3.5L1.5 1z"/></svg>'

JOURNEY_STEPS=[
    ("First","Website Design.","GenM apprenticeship, 2018 — my start in web."),
    ("Then","Freelance Development.","Shipping for international clients on Upwork since 2021."),
    ("Today","I bridge design and code.","Founder, Odgrande Digital — 15+ live products across Nigeria, the UK, Canada and the USA."),
]

def journey_stepper():
    # Scroll-scrubbed narrative in the style of guillaumezhu.com's "My journey":
    # a big title whose scattered letters gather as it scrolls in, then a
    # sticky full-screen stage where each phrase rises in letter by letter,
    # holds, then lifts away for the next. Without JS it reads as plain text.
    lines=[]
    for i,(label,line,sub) in enumerate(JOURNEY_STEPS,1):
        lines.append(f'<p class="journey-line journey-label" data-i18n="journey_l{i}">{esc(label)}</p>')
        lines.append(f'<div class="journey-line journey-phrase"><p class="journey-big" data-i18n="journey_p{i}">{esc(line)}</p><p class="journey-sub" data-i18n="journey_s{i}">{esc(sub)}</p></div>')
    return f'''<section class="journey" id="journey">
<div class="journey-title"><h2 class="journey-heading" data-i18n="journey_title">My journey</h2></div>
<div class="journey-runway"><div class="journey-stage">{"".join(lines)}</div></div>
</section>'''

def work_card(p,home=False):
    # cardImageEverywhere (site_config): use the featured image on every card
    # (Works page, "More Work"), not only on the home page.
    img=(p.get("featuredHomeImage") if home or p.get("cardImageEverywhere") else "") or (p["images"][0] if p.get("images") else "")
    # thumbPosition (site_config) picks which part of a wide image the square card shows.
    pos=f' style="object-position:{esc(p["thumbPosition"])}"' if p.get("thumbPosition") else ""
    thumb=f'<img class="thumb" src="{esc(img)}" alt="{esc(p["title"])}" loading="lazy"{pos}>' if img else placeholder(p["title"],p["category"])
    return f'''<a class="work-card" href="/works/{esc(p["slug"])}/" data-cat="{esc(p["category"])}"><div class="frame"><div class="label"><span>{esc(p["category"])}</span><img src="/assets/theme/symbol.svg" alt=""></div><div class="texture"></div>{thumb}<div class="disk"></div></div><div class="meta"><h3 class="h4">{esc(p["title"])}</h3><p class="t-md">{esc(p["client"])}</p></div></a>'''

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
    "WhatsApp Image 2026-09-29 at 1.25.13 PM.jpeg",
    "WhatsApp Image 2026-09-29 at 1.25.13.jpeg",
    "IQO_8465-1_optimized.jpg",
    "20250129_092329_optimized.jpg",
    "20250128_095634_optimized.jpg",
    "IMG_20250125_163210_281.jpg",
    "20250129_092347_optimized.jpg",
    "IMG_20250125_163444_645.jpg",
    "IMG_20250125_163806_325.jpg",
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

PERSONAL_FOLDERS=[
    ("ALTSCHOOL - Course","AltSchool Africa"),
    ("OSUN Creative Conference- MEMBER","Osun SDG Creative Conference"),
]

def folder_images(folder_name):
    files=personal_files()
    seen=set();out=[]
    for base in (ASSETS,SOURCE):
        d=base/"Personal images"/folder_name
        if not d.exists():continue
        for p in sorted(d.iterdir(),key=lambda x:x.name.lower()):
            if p.is_file() and p.suffix.lower() in IMG_EXT and p.name not in seen and p.name in files and p.name not in ALWAYS_EXCLUDE:
                seen.add(p.name)
                out.append(path_url("assets","personal","images",p.name))
    return out

def photo_slider(title,images):
    if not images:return ""
    slides="".join(f'<div class="slider-slide"><img src="{esc(x)}" alt="{esc(title)}" loading="lazy"></div>' for x in images)
    return f'''<div class="photo-slider">
<div class="slider-head"><h3 class="h4">{esc(title)}</h3><div class="slider-controls"><button class="slider-btn slider-prev" type="button" aria-label="Previous photo">&#8592;</button><button class="slider-btn slider-next" type="button" aria-label="Next photo">&#8594;</button></div></div>
<div class="slider-track">{slides}</div>
</div>'''

def personal_sliders():
    return "".join(photo_slider(title,folder_images(folder)) for folder,title in PERSONAL_FOLDERS)

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
    faq=accordion_box(CONFIG["faq"],i18n_prefix="faq")
    reel=home_reel_video(projects)
    body=f'''<section class="container container-xl hero" data-reveal>
<p class="t-xl tagline" data-i18n="hero_tagline">Hey there! I'm a Full-Stack Web Developer &amp; Web Designer with 5+ years of experience building digital products for clients across Nigeria, the UK, Canada and the USA.</p>
<div class="hero-main">
<div class="hero-copy">
<a class="btn btn-live" href="/contact/"><i class="live-dot" aria-hidden="true"></i><span data-i18n="hero_badge">Available for work</span></a>
<h1 class="h1" data-split-text>{esc(site["name"])}</h1>
<div class="name-entry" aria-label="How to say my name">
<p class="name-head"><span class="name-phon"><span class="name-label" data-i18n="pron_label">Pronounced:</span> /ore-dune-are-your · bore-lah-rin-wah/</span> <i class="name-pos" data-i18n="pron_pos">noun</i></p>
<p class="name-def"><b>1.</b> <span data-i18n="pron_def">a full-stack web developer and web designer who bridges design and code.</span></p>
<p class="name-origin" data-i18n="pron_origin">Yoruba · Ọdúnayọ̀, “a year of joy”</p>
</div>
</div>
<div class="hero-photo">{image_frame(hero_portrait,site["name"],"portrait")}</div>
</div>
</section>

{marquee(["Full-Stack Developer","Web Designer","WordPress","Shopify","Webflow","React"])}

<section class="container container-lg" style="align-items:center" data-reveal>
<h2 class="h2 text-center" data-i18n="featured_heading">Featured Works</h2>
<div class="work-grid">{"".join(work_card(p,home=True) for p in featured)}</div>
<a class="btn" href="/works/"><span data-i18n="all_works_btn">All Works</span></a>
</section>

<section class="container container-md" data-reveal>
<h2 class="h2 text-center" data-i18n="services_heading">Services</h2>
{services}
</section>

<section class="container container-xl" data-reveal>
<h2 class="h2 text-center" data-i18n="about_heading">About</h2>
<div class="split">
<div class="split-copy">
<p class="t-xl" data-i18n="about_intro">I'm a Full-Stack Web Developer and Web Designer who enjoys the point where a design stops being a picture and becomes a working product.</p>
<p class="t-sm">I build, customize and maintain WordPress, WooCommerce and Shopify stores, Webflow sites and custom front-end work for clients across Nigeria, the UK, Canada and the USA.</p>
<p class="t-sm">When I'm not building for a client, I'm usually improving my own tools, or picking apart a site to see how it was put together.</p>
<a class="btn" href="/about/"><span data-i18n="more_about_btn">More about me</span></a>
</div>
<div class="split-photo">{image_frame(about_portrait,site["name"],"portrait")}</div>
</div>
</section>

{f'''<section class="container container-md" style="align-items:center" data-reveal>
<h2 class="h2 text-center">A Quick Hello</h2>
<div class="video-frame"><video controls preload="metadata" playsinline poster="/assets/theme/video-poster.svg"><source src="{esc(reel)}"></video></div>
</section>''' if reel else ""}

{marquee(["Let's Build Something Great","Open For Work"])}

<section class="container container-md" data-reveal>
<h2 class="h2 text-center" data-i18n="faq_heading">FAQ</h2>
{faq}
</section>'''
    return shell("Home",site["description"],body,"/")

def page_works(projects):
    body=f'''<section class="container container-lg" style="align-items:center" data-reveal>
<h1 class="h1 text-center" data-i18n="works_heading">Works</h1>
<p class="t-sm text-center" data-i18n="works_intro" data-i18n-n="{len(projects)}">{len(projects)} projects across WordPress, Shopify, Webflow, custom React &amp; PHP builds, e-commerce and brand work.</p>
</section>

{marquee([f"{len(projects)} Projects","4 Countries","Zero Templates"])}

<section class="container container-lg" style="align-items:center" data-reveal>
<div id="works-filter" class="works-filter" aria-label="Filter projects"></div>
<div class="work-grid" id="works-grid">{"".join(work_card(p) for p in projects)}</div>
</section>'''
    return shell("Works","Websites, e-commerce builds, digital products, plugins and brand projects.",body,"/works/")

def related_projects(p,projects):
    others=[x for x in projects if x["slug"]!=p["slug"] and x.get("images")]
    same_category=[x for x in others if x["category"]==p["category"]]
    picks=(same_category+[x for x in others if x not in same_category])[:3]
    if not picks:return ""
    cards="".join(work_card(x) for x in picks)
    return f'<section class="container container-lg" style="align-items:center" data-reveal><h2 class="h2 text-center" data-i18n="more_work">More Work</h2><div class="work-grid">{cards}</div></section>'

def project_highlights(p):
    # Optional "Featured build" panels (site_config: projects.<slug>.highlights)
    # for standout pieces of work inside a project, e.g. a custom plugin.
    out=[]
    for h in p.get("highlights",[]):
        paras="".join(f'<p class="t-sm">{esc(x)}</p>' for x in h.get("paragraphs",[]))
        skills="".join(f'<li>{esc(x)}</li>' for x in h.get("skills",[]))
        badge=f'<span class="fb-badge"><i aria-hidden="true"></i>{esc(h["badge"])}</span>' if h.get("badge") else ""
        pr=h.get("proof")
        ct=h.get("cta")
        cta=(f'<a class="btn fb-cta" href="{esc(ct["url"])}"><span>{esc(ct["label"])}</span></a>' if ct else "")
        proof=(f'<figure class="fb-proof"><img src="{esc(pr["image"])}" alt="{esc(pr.get("alt",""))}" loading="lazy">{f"<figcaption>{esc(pr['caption'])}</figcaption>" if pr.get("caption") else ""}</figure>' if pr else "")
        out.append(f'''<section class="feature-build" data-reveal>
<div class="fb-main"><div class="fb-top"><p class="fb-eyebrow" data-i18n="fb_eyebrow">{esc(h.get("eyebrow","Featured build"))}</p>{badge}</div><h2 class="fb-title">{esc(h["title"])}</h2><p class="fb-sub">{esc(h.get("subtitle",""))}</p>{paras}{cta}{proof}</div>
{f'<aside class="fb-skills"><h3 class="fb-skills-title" data-i18n="fb_skills">Skills it demonstrates</h3><ul>{skills}</ul></aside>' if skills else ""}
</section>''')
    return "".join(out)

# Tiny inline-SVG country flags (flag emoji don't render on Windows).
FLAGS={
 "NG":("Nigeria",'<svg viewBox="0 0 3 2"><rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#008751"/><rect x="2" width="1" height="2" fill="#008751"/></svg>'),
 "US":("United States",'<svg viewBox="0 0 19 10"><rect width="19" height="10" fill="#fff"/><path d="M0 0h19v.77H0zm0 1.54h19v.77H0zm0 1.54h19v.77H0zm0 1.54h19v.77H0zm0 1.54h19v.77H0zm0 1.54h19v.77H0zm0 1.54h19v.77H0z" fill="#B22234"/><rect width="7.6" height="5.38" fill="#3C3B6E"/></svg>'),
 "GB":("United Kingdom",'<svg viewBox="0 0 60 30"><rect width="60" height="30" fill="#012169"/><path d="M0 0l60 30M60 0L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0l60 30M60 0L0 30" stroke="#C8102E" stroke-width="2.4"/><path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/><path d="M30 0v30M0 15h60" stroke="#C8102E" stroke-width="6"/></svg>'),
 "CA":("Canada",'<svg viewBox="0 0 40 20"><rect width="40" height="20" fill="#fff"/><rect width="10" height="20" fill="#D80621"/><rect x="30" width="10" height="20" fill="#D80621"/><path d="M20 3.2l1.3 2.6 1.6-.7-.6 3.3 2.2-2.4.5 1.3 2.3-.4-.8 2.5 1 .5-3.6 3 .4 1.3-3.6-.6-.1 3.4h-1.2l-.1-3.4-3.6.6.4-1.3-3.6-3 1-.5-.8-2.5 2.3.4.5-1.3 2.2 2.4-.6-3.3 1.6.7z" fill="#D80621"/></svg>'),
}

def project_flags(p):
    out="".join(f'<span class="flag" role="img" aria-label="{FLAGS[c][0]}" title="{FLAGS[c][0]}">{FLAGS[c][1]}</span>' for c in p.get("countries",[]) if c in FLAGS)
    return f'<span class="flags">{out}</span>' if out else ""

def project_pager(p,projects):
    # Previous / All works / Next, wrapping around the list.
    i=next(n for n,x in enumerate(projects) if x["slug"]==p["slug"])
    prev,nxt=projects[i-1],projects[(i+1)%len(projects)]
    return (f'<nav class="pager" aria-label="More projects">'
            f'<a class="pager-link pager-prev" href="/works/{esc(prev["slug"])}/"><span class="pager-dir" data-i18n="pager_prev">Previous</span><span class="pager-title">{esc(prev["title"])}</span></a>'
            f'<a class="btn pager-all" href="/works/"><span data-i18n="all_works_btn">All Works</span></a>'
            f'<a class="pager-link pager-next" href="/works/{esc(nxt["slug"])}/"><span class="pager-dir" data-i18n="pager_next">Next</span><span class="pager-title">{esc(nxt["title"])}</span></a></nav>')

def page_project(p,projects):
    hero=p["images"][0] if p.get("images") else ""
    rest=p["images"][1:] if p.get("images") else []
    # Spec panel: numbered mono labels over values set in the display face,
    # services as tags, inside the site's 2px frame. Four cells on desktop,
    # a 2x2 grid on phones with services spanning the full width.
    services="".join(f'<span>{esc(x)}</span>' for x in p["services"])
    facts=[("Client","fact_client",project_flags(p)+esc(p["client"])),("Year","fact_year",esc(p.get("year",""))),("Category","fact_category",esc(p["category"])),("Services","fact_services",f'<span class="spec-tags">{services}</span>')]
    facts_html="".join(f'<div class="spec-item spec-{k_i18n[5:]}"><dt><span class="spec-n">{n:02d}</span><span data-i18n="{k_i18n}">{k}</span></dt><dd>{v}</dd></div>' for n,(k,k_i18n,v) in enumerate(facts,1))
    live_btn=f'<a class="btn" href="{esc(p["liveSite"])}" target="_blank" rel="noopener"><span data-i18n="live_site_btn">Live Site</span></a>' if p.get("liveSite") else ""
    video_html=""
    if p.get("videos"):
        video_html="".join(f'<div class="project-video"><video controls preload="metadata" playsinline poster="/assets/theme/video-poster.svg"><source src="{esc(v)}"></video></div>' for v in p["videos"])
    gallery=masonry_gallery(rest,p["title"],shots=True)
    body=f'''<section class="container container-xl" style="align-items:center" data-reveal>
<h1 class="h1 text-center">{esc(p["title"])}</h1>
<div class="hero-media" style="width:100%">{image_frame(hero,p["title"],sub=p["category"])}</div>
<dl class="spec">{facts_html}</dl>
{live_btn}
<div style="max-width:48rem"><p class="t-xl">{esc(p["description"])}</p></div>
{project_highlights(p)}
{video_html}
{gallery}
{project_pager(p,projects)}
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
    gallery=bento_gallery(archive_images(),f'{site["name"]} personal archive')
    sliders=personal_sliders()
    second_award=awards()[1] if len(awards())>1 else ""
    video=testimonial_video()
    # "In their words": real client messages (from hand-off emails), each a
    # sticky card in a stack; script.js lights the words up as you scroll and
    # tucks each card back as the next one arrives.
    tlist=CONFIG.get("testimonials",[])
    quotes="".join(
        f'<figure class="word-card" style="--i:{i}">'
        f'<span class="word-mark" aria-hidden="true">&ldquo;</span>'
        f'<blockquote class="word-quote">{esc(t["quote"])}</blockquote>'
        f'<figcaption class="word-cite"><span class="word-avatar" aria-hidden="true">{esc((t.get("brand") or t["company"].split(",")[-1].strip() or t["name"])[:1])}</span>'
        f'<span class="word-who"><b>{esc(t["name"])}</b><small>{esc(t["company"])}</small></span>'
        f'<span class="word-n" aria-hidden="true">{i+1:02d} / {len(tlist):02d}</span></figcaption></figure>'
        for i,t in enumerate(tlist))
    video_html=f'<div class="video-frame"><video controls preload="metadata" playsinline poster="/assets/theme/video-poster.svg"><source src="{esc(video)}"></video></div>' if video else ""
    body=f'''<section class="container container-xl" data-reveal>
<h1 class="h1 text-center"><span data-i18n="about_meet">Meet</span> {esc(site["name"].split()[0])}</h1>
{f'<div class="magic-hero">{image_frame(magic_hero,"Let\'s create magic together")}</div>' if magic_hero else ""}
<div class="split">
<div class="split-copy">
<p class="t-xl" data-i18n="about_build_text">I build, customize and maintain websites for businesses, organizations and digital products.</p>
<p class="t-sm" data-i18n="about_work_text">My work sits between visual implementation and practical engineering. I am comfortable working inside WordPress and page builders, then dropping into PHP, JavaScript and CSS when the problem needs more than a visual editor.</p>
<p class="t-sm" data-i18n="about_bio_text">Full-Stack Web Developer and Web Designer with 5+ years of experience building and maintaining digital products for clients across Nigeria, the UK, Canada and the USA.</p>
</div>
<div class="split-photo">{image_frame(portrait,site["name"],"portrait")}</div>
</div>
</section>

{journey_stepper()}

{f'''<section class="container container-xl" data-reveal>
<div class="split split-reverse">
<div class="split-photo">{image_frame(magic_standing,"Let's create website magic")}</div>
<div class="split-copy">
<p class="t-xl" data-i18n="magic_heading">Let's create website magic.</p>
<p class="t-sm" data-i18n="magic_text">Whatever the brief — a brand-new WordPress build, an e-commerce store, or a digital product that needs to feel alive — I'd love to help build it.</p>
<a class="btn" href="/start/"><span data-i18n="start_project_btn">Start a project</span></a>
<div class="social-row">{"".join(f'<a href="{esc(u)}" target="_blank" rel="noopener" class="link-inline">{esc(t)}</a>' for t,u in socials_list())}</div>
</div>
</div>
</section>''' if magic_standing else ""}

<section class="container container-md" data-reveal>
<h2 class="h2 text-center" data-i18n="experience_heading">Experience</h2>
{experience}
</section>

<section class="container container-md" data-reveal>
<h2 class="h2 text-center" data-i18n="education_heading">Education</h2>
{education}
</section>

<section class="container container-md" data-reveal>
<h2 class="h2 text-center" data-i18n="toolkit_heading">Toolkit</h2>
<div class="tag-list">{tags}</div>
</section>

{f'''<section class="container container-md" data-reveal>
<h2 class="h2 text-center" data-i18n="certifications_heading">Certifications</h2>
<div class="tag-list">{certs}</div>
</section>''' if certs else ""}

{f'''<section class="container container-md" data-reveal>
<div class="credential-single">{image_frame(second_award,"Designer Of The Year award")}<h3 class="h5 text-center" data-i18n="designer_award_heading">Designer Of The Year</h3></div>
</section>''' if second_award else ""}

{f'''<section class="container container-xl words-section">
<h2 class="h2 text-center" data-reveal data-i18n="testimonials_heading">In Their Words</h2>
<p class="t-sm text-center words-sub" data-i18n="testimonials_sub">Straight from the inbox: what clients wrote back after their site was handed over.</p>
<div class="words-stack">{quotes}</div>
{video_html}
</section>''' if quotes or video else ""}

<section class="container container-xl" data-reveal>
<h2 class="h2 text-center" data-i18n="archive_heading">Personal Archive</h2>
{gallery}
{sliders}
<div class="gate-actions" style="justify-content:center">
<a class="btn" href="/credentials/"><span data-i18n="view_credentials_btn">View Credentials</span></a>
<a class="btn" href="/odunayo-bolarinwa-cv.pdf" target="_blank" rel="noopener"><span data-i18n="view_cv_btn">View CV</span></a>
</div>
</section>'''
    return shell("About",f"About {site['name']}, Full-Stack Web Developer and Web Designer.",body,"/about/")

def page_credentials():
    a=awards()
    award_html=f'<div class="credential-single">{image_frame(a[0],"Designer Of The Year award")}<h3 class="h5 text-center" data-i18n="designer_award_heading">Designer Of The Year</h3></div>' if a else '<p class="t-sm text-center">No award image yet.</p>'
    cert_cards=""
    for org,name,url,pdf in CONFIG.get("certifications",[]):
        pdf_link=f'<a class="t-xsm link-inline" href="{esc(pdf)}" target="_blank" rel="noopener"><span data-i18n="view_pdf_btn">View PDF</span></a>' if pdf else ""
        cert_cards+=f'<div class="contact-item"><div class="row"><span class="t-lg">{esc(org)}</span><img src="/assets/theme/symbol-white.svg" alt=""></div><div class="divider"></div><a class="t-sm link-inline" href="{esc(url or "#")}" target="_blank" rel="noopener">{esc(name)}</a>{pdf_link}</div>'
    body=f'''<section class="container container-md" data-reveal>
<h1 class="h1 text-center" data-i18n="credentials_heading">Credentials</h1>
{award_html}
</section>
<section class="container container-md" data-reveal>
<h2 class="h2 text-center" data-i18n="certifications_heading">Certifications</h2>
<div class="contact-grid">{cert_cards}</div>
<div class="gate-actions" style="justify-content:center;margin-top:2rem">
<a class="btn" href="/odunayo-bolarinwa-cv.pdf" target="_blank" rel="noopener"><span data-i18n="view_full_cv_btn">View Full CV</span></a>
</div>
</section>'''
    return shell("Credentials","Credentials and recognition archive.",body,"/credentials/")

def page_start():
    # /start/ — a shareable step-by-step project brief. Send prospects
    # /start/?for=Name for a personal greeting. Answers stay in the visitor's
    # browser (localStorage) until they send the brief by WhatsApp or email.
    site=CONFIG["site"]
    def chip(name,kind,value,key,label):
        return f'<label class="bf-chip"><input type="{kind}" name="{name}" value="{esc(value)}"><span data-i18n="{key}">{esc(label)}</span></label>'
    def chips(name,kind,opts):
        return '<div class="bf-chips">'+"".join(chip(name,kind,v,k,l) for v,k,l in opts)+'</div>'
    def field(name,key,label,ph_key,ph,kind="text",extra=""):
        return f'<label class="bf-field"><span class="bf-label" data-i18n="{key}">{esc(label)}</span><input type="{kind}" name="{name}" placeholder="{esc(ph)}" data-i18n-ph="{ph_key}"{extra}></label>'
    def step(n,q_key,q,inner,hint_key=None,hint=None):
        h=f'<p class="bf-hint" data-i18n="{hint_key}">{esc(hint)}</p>' if hint_key else ""
        return f'<fieldset class="bf-step" data-step="{n}"><legend class="bf-q" data-i18n="{q_key}">{esc(q)}</legend>{h}{inner}<p class="bf-error" role="alert"></p></fieldset>'
    needs=[("New website","bf_o_website","A new website"),("Online shop","bf_o_shop","An online shop"),("Redesign","bf_o_redesign","A redesign of my site"),
           ("WordPress plugin / custom feature","bf_o_plugin","A WordPress plugin or custom feature"),("Fix or speed up a site","bf_o_fix","Fix or speed up my site"),
           ("Branding / design","bf_o_brand","Branding or design"),("Something else","bf_o_other","Something else")]
    platforms=[("WordPress","bf_o_wp","WordPress"),("Shopify","bf_o_shopify","Shopify"),("Webflow","bf_o_webflow","Webflow"),
               ("Custom-built","bf_o_custom","Custom-built"),("Not sure, help me choose","bf_o_unsure","Not sure, help me choose")]
    features=[("Online payments","bf_o_pay","Online payments"),("Bookings / appointments","bf_o_book","Bookings or appointments"),("Event ticketing","bf_o_tickets","Event ticketing"),
              ("Multiple languages","bf_o_lang","Multiple languages"),("Blog / news","bf_o_blog","Blog or news"),("Member login","bf_o_members","Member login"),
              ("AI chatbot","bf_o_ai","AI chatbot"),("Not sure yet","bf_o_notyet","Not sure yet")]
    have=[("Logo & branding","bf_o_logo","Logo and branding"),("Text & photos","bf_o_content","Text and photos"),
          ("Domain & hosting","bf_o_domain","Domain and hosting"),("A current website","bf_o_site","A current website")]
    timeline=[("ASAP (within 2 weeks)","bf_o_asap","As soon as possible (within 2 weeks)"),("Within a month","bf_o_month","Within a month"),
              ("In 2-3 months","bf_o_quarter","In 2–3 months"),("Flexible","bf_o_flex","I'm flexible")]
    prefer=[("Email","bf_o_email","Email"),("WhatsApp","bf_o_whatsapp","WhatsApp")]
    steps="".join([
        step(1,"bf_q_you","First, who am I talking to?",
             field("name","bf_l_name","Your name","bf_ph_name","e.g. Ada Okafor",extra=' autocomplete="name"')
             +field("business","bf_l_biz","Business or brand (optional)","bf_ph_biz","e.g. Ada's Kitchen",extra=' autocomplete="organization"')
             +field("location","bf_l_country","Where are you based? (optional)","bf_ph_country","e.g. London, UK")),
        step(2,"bf_q_need","What do you need?",chips("needs","checkbox",needs),"bf_hint_multi","Pick all that apply."),
        step(3,"bf_q_platform","Any platform in mind?",chips("platform","radio",platforms)),
        step(4,"bf_q_features","Which features will it need?",chips("features","checkbox",features),"bf_hint_multi","Pick all that apply."),
        step(5,"bf_q_have","What do you already have?",chips("have","checkbox",have)
             +field("current_site","bf_l_url","Current website link (optional)","bf_ph_url","https://",kind="url")
             +f'<label class="bf-field"><span class="bf-label" data-i18n="bf_l_like">Websites you like (optional)</span><textarea name="inspiration" rows="3" placeholder="Paste a few links and say what you like about them" data-i18n-ph="bf_ph_like"></textarea></label>',
             "bf_hint_multi","Pick all that apply."),
        step(6,"bf_q_when","Timeline and budget",
             f'<p class="bf-label" data-i18n="bf_l_timeline">When do you need it?</p>'+chips("timeline","radio",timeline)
             +field("budget","bf_l_budget","Your budget (any currency, optional)","bf_ph_budget","e.g. $1,500, £1,000, ₦800,000 or not sure")),
        step(7,"bf_q_idea","Tell me about your project",
             f'<label class="bf-field"><textarea name="idea" rows="6" placeholder="My idea is..." data-i18n-ph="bf_ph_idea" aria-label="Your project idea"></textarea></label>',
             "bf_hint_idea","What it is, who it's for, and what a win looks like for you."),
        step(8,"bf_q_contact","How can I reach you?",
             field("email","bf_l_email","Email","bf_ph_email","you@example.com",kind="email",extra=' autocomplete="email"')
             +field("whatsapp","bf_l_wa","WhatsApp number (optional)","bf_ph_wa","e.g. +234 800 000 0000",kind="tel",extra=' autocomplete="tel"')
             +f'<p class="bf-label" data-i18n="bf_l_prefer">I prefer to talk on</p>'+chips("prefer","radio",prefer)),
    ])
    body=f'''<section class="container container-md brief-wrap">
<div class="brief" id="brief" data-whatsapp="{esc(site["whatsapp"])}" data-email="{esc(site["email"])}" data-total="8">
<div class="bf-intro bf-step is-active" data-step="0">
<p class="fb-eyebrow" data-i18n="bf_eyebrow">Project brief</p>
<h1 class="h2 bf-title"><span class="bf-hi" hidden></span><span data-i18n="bf_title">Start a project</span></h1>
<p class="t-sm" data-i18n="bf_intro">Let's plan your project together. It takes about 3 minutes, and your answers stay in your browser until you choose to send them.</p>
<p class="bf-saved" hidden data-i18n="bf_saved">Your answers are saved on this device, so you can come back later.</p>
<button class="btn bf-begin" type="button"><span data-i18n="bf_begin">Let's start</span></button>
</div>
<form class="bf-form" novalidate>
<div class="bf-progress" hidden><span class="bf-count" aria-live="polite"></span><i class="bf-bar"><b></b></i></div>
{steps}
<div class="bf-step bf-review" data-step="9">
<p class="bf-q" data-i18n="bf_q_review">Here's your brief</p>
<p class="bf-hint" data-i18n="bf_hint_review">Check it over, then send it to me. I'll reply within a day or two.</p>
<pre class="bf-summary"></pre>
<div class="bf-send">
<button class="btn bf-wa" type="button"><span data-i18n="bf_send_wa">Send on WhatsApp</span></button>
<button class="btn bf-mail" type="button"><span data-i18n="bf_send_email">Send by email</span></button>
<button class="btn bf-copy" type="button"><span data-i18n="bf_copy">Copy brief</span></button>
</div>
<p class="bf-done" hidden data-i18n="bf_done">Almost done! Just press send in the app that opened. I'll be in touch soon.</p>
<div class="bf-review-links"><button class="bf-link bf-edit" type="button" data-i18n="bf_edit">Edit answers</button><button class="bf-link bf-restart" type="button" data-i18n="bf_restart">Start over</button></div>
</div>
<div class="bf-nav" hidden><button class="btn bf-back" type="button"><span data-i18n="bf_back">Back</span></button><button class="btn bf-next" type="submit"><span data-i18n="bf_next">Next</span></button></div>
</form>
</div>
</section>'''
    return shell("Start a project",f"Plan your website, online shop or WordPress project with {site['name']}: a 3-minute project brief.",body,"/start/",show_cta=False,bare=True)

def page_contact():
    site=CONFIG["site"]
    items=[("Email","contact_label_email",site["email"],f'mailto:{site["email"]}')]
    if site.get("phone"):items.append(("Phone","contact_label_phone",site["phone"],f'tel:{site["phone"]}'))
    if site.get("location"):items.append(("Location","contact_label_location",site["location"],None))
    for label,url in socials_list():
        items.append((label.title(),None,url,url))
    cards="".join(
        (lambda attr: f'<div class="contact-item"><div class="row"><span class="t-lg"{attr}>{esc(k)}</span><img src="/assets/theme/symbol-white.svg" alt=""></div><div class="divider"></div>'
        + (f'<a class="t-sm link-inline" href="{esc(href)}" target="_blank" rel="noopener">{esc(v)}</a>' if href else f'<p class="t-sm">{esc(v)}</p>')
        + '</div>')(f' data-i18n="{k_i18n}"' if k_i18n else '')
        for k,k_i18n,v,href in items
    )
    body=f'''<section class="container container-xl text-center" style="align-items:center" data-reveal>
<h1 class="h1" data-i18n="contact_heading">Contact</h1>
<div style="max-width:44rem;display:flex;flex-direction:column;gap:1rem">
<p class="t-xl" data-i18n="contact_tagline">Let's build something together.</p>
<p class="t-sm" data-i18n="contact_sub">Have a website, e-commerce build, WordPress problem or digital product in mind? Tell me what you're working on and I'll get back to you within a day or two.</p>
<a class="btn" href="/start/" style="align-self:center"><span data-i18n="bf_cta">Fill in a project brief</span></a>
<p class="reply-status" data-hours='{esc(json.dumps(site["replyHours"]))}' aria-live="polite"><i class="rs-dot" aria-hidden="true"></i><span class="rs-text">Based in Lagos, Nigeria (WAT).</span></p>
</div>
</section>
<section class="container container-md">
<div class="contact-grid">{cards}</div>
</section>'''
    return shell("Contact",f"Contact {site['name']} for WordPress development, e-commerce and digital product work.",body,"/contact/",show_cta=False)

def legal_page(title,desc,canonical,sections,i18n_key=None):
    body_sections="".join(
        f'<div style="display:flex;flex-direction:column;gap:.75rem"><h2 class="h3">{esc(h)}</h2><p class="t-sm">{p}</p></div>'
        for h,p in sections
    )
    title_attr=f' data-i18n="{i18n_key}"' if i18n_key else ""
    body=f'''<section class="container container-md" data-reveal>
<h1 class="h1 text-center"{title_attr}>{esc(title)}</h1>
<p class="t-sm text-center" style="color:var(--muted)">Last updated October 2026.</p>
<div style="display:flex;flex-direction:column;gap:2.5rem;margin-top:1rem">{body_sections}</div>
</section>'''
    return shell(title,desc,body,canonical,show_cta=False)

def page_privacy():
    site=CONFIG["site"]
    sections=[
        ("What this site is","This is Odunayo Bolarinwa's personal portfolio — a static site with no user accounts, no server-side database and no backend application. There is no tracking pixel, analytics script or advertising network installed on any page."),
        ("What's stored on your device","A few small, non-identifying values in your browser's own local and session storage: your light/dark theme choice, and whether you've already seen the one-time landing question, the cookie notice and the exit popup this session. None of this is sent anywhere or shared with any third party — see the <a class=\"link-inline\" href=\"/cookies/\">Cookie Policy</a> for the exact list."),
        ("The one exception: the footer clock","The small flag and local time shown in the footer come from a single client-side request this site makes, once per visit, to a free IP-geolocation service (ipwho.is) so it can show your country and local time without asking you anything. That request sends your IP address to ipwho.is the same way any website request does; this site does not see, store or log the result anywhere beyond your own browser's session storage, and ipwho.is is not used for tracking, analytics or advertising of any kind. If that single request fails or is blocked (ad blockers, offline, etc.), the clock just stays blank — nothing else on the page depends on it."),
        ("Information you choose to send","If you use the Contact page, the landing question's feedback form, or email/WhatsApp links directly, your message goes straight to Odunayo's inbox (or WhatsApp) the normal way your email client or WhatsApp sends it — this site has no form backend of its own and never stores what you write."),
        ("Hosting","This site is hosted on GitHub Pages. GitHub may keep standard server access logs (such as IP address and request time) as part of operating its hosting infrastructure; that is governed by GitHub's own privacy policy, not this one, since this site has no access to those logs."),
        ("Contact",f'Questions about this policy can be sent to <a class="link-inline" href="mailto:{esc(site["email"])}">{esc(site["email"])}</a>.'),
    ]
    return legal_page("Privacy Policy",f"Privacy policy for {site['name']}'s portfolio site.","/privacy/",sections,"privacy_heading")

def page_cookies():
    site=CONFIG["site"]
    sections=[
        ("The short version","This site doesn't use tracking or advertising cookies. It uses your browser's local and session storage — technically not cookies, but covered here for the same reason — to remember a few small preferences on your own device."),
        ("What's stored, exactly",'''<ul style="margin:0;padding-left:1.2rem;list-style:disc;display:flex;flex-direction:column;gap:.4rem">
<li><code>odBrief</code> — the answers you type into the project brief (/start/), kept on your device (local storage) so you can finish later. Nothing is sent anywhere until you choose to send it, and "Start over" clears it.</li>
<li><code>odXray</code> — whether X-ray mode is switched on, for this visit only (session storage).</li>
<li><code>odTheme</code> — your light/dark mode choice for this visit only; every new visit opens in the default dark theme (session storage).</li>
<li><code>odLang</code> — your chosen site language for this visit only; every new visit starts in English (session storage).</li>
<li><code>odGateSeen</code> — whether you've already answered the one-time landing question this browser session (session storage, cleared when you close the tab).</li>
<li><code>odPreloaderSeen</code> — whether the loading animation has already played this visit, so other pages open instantly (session storage, cleared when you close the tab).</li>
<li><code>odCookieNoticeSeen</code> — whether you've dismissed this cookie notice this session (session storage).</li>
<li><code>odExitSeen</code> — whether the exit-intent popup has already shown this session (session storage).</li>
<li><code>odVisitorGeo</code> — the country/timezone result from the footer's one-time IP lookup, cached for the rest of the session so it isn't requested again (session storage). See the <a class="link-inline" href="/privacy/">Privacy Policy</a> for how that lookup works.</li>
</ul>'''),
        ("Third parties","The site's fonts and libraries (GSAP, Three.js, Vue) are served from this site itself. The loading animation fetches one font from Google Fonts, which may see a standard request (your IP address, browser user-agent) as part of serving it — this site doesn't add any tracking on top of that."),
        ("Your control","Clearing your browser's site data for odunayobolarinwa.com removes all of the above. Since none of it is sent to a server, there's nothing further to delete on this end."),
        ("Contact",f'Questions about this policy can be sent to <a class="link-inline" href="mailto:{esc(site["email"])}">{esc(site["email"])}</a>.'),
    ]
    return legal_page("Cookie Policy",f"Cookie and local storage policy for {site['name']}'s portfolio site.","/cookies/",sections,"cookies_heading")

def page_sitemap(projects):
    site=CONFIG["site"]
    def col(heading,i18n_key,links):
        items="".join(f'<li><a class="link-inline" href="{u}">{esc(t)}</a></li>' for t,u in links)
        return f'<div style="display:flex;flex-direction:column;gap:.75rem"><h2 class="h5" data-i18n="{i18n_key}">{esc(heading)}</h2><ul style="margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:.5rem">{items}</ul></div>'
    main_pages=[("Home","/"),("Works","/works/"),("About","/about/"),("Credentials","/credentials/"),("Contact","/contact/"),("Start a project","/start/")]
    legal_pages=[("Privacy Policy","/privacy/"),("Cookie Policy","/cookies/"),("Sitemap","/sitemap/")]
    project_links=[(p["title"],f'/works/{p["slug"]}/') for p in projects]
    body=f'''<section class="container container-md" data-reveal>
<h1 class="h1 text-center" data-i18n="footer_sitemap">Sitemap</h1>
<p class="t-sm text-center" style="color:var(--muted)" data-i18n="sitemap_sub">Every page on this site, in one place.</p>
<div style="display:flex;flex-direction:column;gap:2.5rem;margin-top:1rem">
{col("Main Pages","sitemap_main_pages",main_pages)}
{col("Works","works_heading",project_links)}
{col("Legal","sitemap_legal",legal_pages)}
</div>
</section>'''
    return shell("Sitemap",f"Full page listing for {site['name']}'s portfolio site.",body,"/sitemap/",show_cta=False)

# ---------- image optimisation ----------
# Source assets are full-resolution PNG screenshots / phone photos (up to
# 25 MB each, ~320 MB in total), far too heavy to serve. Every raster image
# under site/assets (except the small theme files referenced from CSS) is
# re-encoded to WebP at two widths — FULL for the lightbox / large screens,
# SMALL for cards and phones — and the HTML is rewritten to use them with
# srcset + intrinsic width/height (no layout shift) + lazy loading.
# Encodes are cached in assets/.optimized/ keyed by a hash of the source
# bytes and committed, so CI and repeat builds just copy them.
OPT_DIR=ASSETS/".optimized"
RASTER_EXT={".png",".jpg",".jpeg"}
FULL_W,SMALL_W,MAX_H=1600,800,16000

def _encode(job):
    src,h=job
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS=None
    out={}
    with Image.open(src) as im:
        im=ImageOps.exif_transpose(im)
        alpha=im.mode in ("RGBA","LA") or (im.mode=="P" and "transparency" in im.info)
        im=im.convert("RGBA" if alpha else "RGB")
        for tag,maxw in (("full",FULL_W),("small",SMALL_W)):
            w,hh=im.size
            scale=min(1,maxw/w,MAX_H/hh)
            frame=im.resize((max(1,round(w*scale)),max(1,round(hh*scale))),Image.LANCZOS) if scale<1 else im
            frame.save(OPT_DIR/f"{h}-{tag}.webp","WEBP",quality=76,method=4)
            out[tag]=list(frame.size)
    return h,out

def optimize_images():
    import hashlib
    from concurrent.futures import ProcessPoolExecutor
    OPT_DIR.mkdir(exist_ok=True)
    manifest_f=OPT_DIR/"manifest.json"
    manifest=json.loads(manifest_f.read_text()) if manifest_f.exists() else {}
    files=[p for p in (SITE/"assets").rglob("*") if p.is_file() and p.suffix.lower() in RASTER_EXT and p.parent.name!="theme"]
    hashes={p:hashlib.sha1(p.read_bytes()).hexdigest()[:24] for p in files}
    todo=sorted({(str(p),h) for p,h in hashes.items() if h not in manifest or not (OPT_DIR/f"{h}-full.webp").exists()},key=lambda x:x[1])
    seen=set();todo=[t for t in todo if not (t[1] in seen or seen.add(t[1]))]
    if todo:
        print(f"Optimising {len(todo)} images...")
        with ProcessPoolExecutor() as ex:
            for h,dims in ex.map(_encode,todo):manifest[h]=dims
        manifest_f.write_text(json.dumps(manifest,indent=0,sort_keys=True))
    mapping={}
    for p,h in hashes.items():
        full=p.with_name(p.stem+".webp")
        if full.exists():full=p.with_name(p.name+".webp")
        small=full.with_name(full.stem+"-sm.webp")
        shutil.copy2(OPT_DIR/f"{h}-full.webp",full);shutil.copy2(OPT_DIR/f"{h}-small.webp",small)
        p.unlink()
        rel=lambda x:"/"+x.relative_to(SITE).as_posix()
        mapping[rel(p)]=(rel(full),rel(small),manifest[h]["full"],manifest[h]["small"])
    return mapping

def rewrite_images(mapping):
    from urllib.parse import unquote as _unquote
    from html import unescape
    unquote=lambda s:_unquote(unescape(s))
    q=lambda path:quote(path)
    img_re=re.compile(r"<img\b[^>]*>")
    def fix_img(m):
        tag=m.group(0)
        sm=re.search(r'\ssrc="([^"]+)"',tag)
        if not sm:return tag
        hit=mapping.get(unquote(sm.group(1)))
        if hit:
            full,small,(fw,fh),(sw,_)=hit
            tag=tag.replace(sm.group(0),f' src="{q(small)}" srcset="{q(small)} {sw}w, {q(full)} {fw}w" sizes="(max-width: 700px) 100vw, 700px" data-full="{q(full)}"',1)
            if " width=" not in tag:tag=tag.replace("<img",f'<img width="{fw}" height="{fh}"',1)
        if " loading=" not in tag:tag=tag.replace("<img",'<img loading="lazy"',1)
        if " decoding=" not in tag:tag=tag.replace("<img",'<img decoding="async"',1)
        return tag
    attr_re=re.compile(r'((?:href|data-src|poster)=")(/assets/[^"]+)(")')
    def fix_attr(m):
        hit=mapping.get(unquote(m.group(2)))
        return m.group(1)+q(hit[0])+m.group(3) if hit else m.group(0)
    for f in SITE.rglob("*.html"):
        if "theme" in f.parts:continue
        s=f.read_text(encoding="utf-8")
        s2=attr_re.sub(fix_attr,img_re.sub(fix_img,s))
        if s2!=s:f.write_text(s2,encoding="utf-8")

def page_404():
    body='''<section class="container container-md notfound" style="align-items:center" data-reveal>
<p class="t-md text-center" data-i18n="nf_eyebrow">Error 404</p>
<h1 class="h1 text-center" data-i18n="nf_heading">Lost in the code.</h1>
<p class="t-sm text-center" style="max-width:32rem" data-i18n="nf_text">This page doesn't exist (or it moved while I was refactoring). Let's get you somewhere useful.</p>
<div class="gate-actions"><a class="btn" href="/"><span data-i18n="nf_home">Back home</span></a><a class="btn" href="/works/"><span data-i18n="all_works_btn">All Works</span></a></div>
</section>'''
    return shell("Page not found","This page doesn't exist.",body,"/404.html",show_cta=False)

def write_seo_files(projects):
    # robots.txt + sitemap.xml so search engines find every page.
    base="https://odunayobolarinwa.com"
    paths=["/","/works/","/about/","/credentials/","/contact/","/start/","/privacy/","/cookies/","/sitemap/"]+[f"/works/{p['slug']}/" for p in projects]
    urls="".join(f"<url><loc>{base}{u}</loc></url>" for u in paths)
    (SITE/"sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',encoding="utf-8")
    # Custom domain (also set in the repo's Pages settings).
    (SITE/"CNAME").write_text("odunayobolarinwa.com\n",encoding="utf-8")
    (SITE/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n",encoding="utf-8")

def main():
    projects=scan_projects();copy_assets()
    image_map=optimize_images()
    (SITE/"index.html").write_text(page_home(projects),encoding="utf-8")
    (SITE/"works").mkdir();(SITE/"works"/"index.html").write_text(page_works(projects),encoding="utf-8")
    for p in projects:
        d=SITE/"works"/p["slug"];d.mkdir(parents=True)
        (d/"index.html").write_text(page_project(p,projects),encoding="utf-8")
    (SITE/"about").mkdir();(SITE/"about"/"index.html").write_text(page_about(),encoding="utf-8")
    (SITE/"credentials").mkdir();(SITE/"credentials"/"index.html").write_text(page_credentials(),encoding="utf-8")
    (SITE/"contact").mkdir();(SITE/"contact"/"index.html").write_text(page_contact(),encoding="utf-8")
    (SITE/"start").mkdir();(SITE/"start"/"index.html").write_text(page_start(),encoding="utf-8")
    (SITE/"privacy").mkdir();(SITE/"privacy"/"index.html").write_text(page_privacy(),encoding="utf-8")
    (SITE/"cookies").mkdir();(SITE/"cookies"/"index.html").write_text(page_cookies(),encoding="utf-8")
    (SITE/"sitemap").mkdir();(SITE/"sitemap"/"index.html").write_text(page_sitemap(projects),encoding="utf-8")
    (SITE/"404.html").write_text(page_404(),encoding="utf-8")
    write_seo_files(projects)
    rewrite_images(image_map)
    print(f"Built {len(projects)} projects")

if __name__=="__main__":main()
