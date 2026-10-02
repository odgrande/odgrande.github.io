(() => {
  const toggle = document.getElementById('nav-toggle');
  const menu = document.getElementById('mobile-menu');
  const close = document.getElementById('mobile-close');
  const open = () => {
    if (!menu) return;
    menu.classList.add('open');
    document.body.classList.add('menu-open');
    toggle?.setAttribute('aria-expanded', 'true');
    if (window.gsap) {
      gsap.fromTo(menu, { clipPath: 'circle(0% at calc(100% - 44px) 44px)' }, { clipPath: 'circle(150% at calc(100% - 44px) 44px)', duration: .7, ease: 'power3.inOut', clearProps: 'clipPath' });
      gsap.from(menu.querySelectorAll('ul a, .mobile-nav-logo'), { y: 40, opacity: 0, rotate: -3, duration: .6, ease: 'power3.out', stagger: .06, delay: .25 });
    }
    close?.focus({ preventScroll: true });
  };
  const shut = () => {
    if (!menu || !menu.classList.contains('open')) return;
    menu.classList.remove('open');
    document.body.classList.remove('menu-open');
    toggle?.setAttribute('aria-expanded', 'false');
  };
  toggle?.setAttribute('aria-expanded', 'false');
  toggle?.setAttribute('aria-controls', 'mobile-menu');
  toggle?.addEventListener('click', open);
  close?.addEventListener('click', () => { shut(); toggle?.focus({ preventScroll: true }); });
  menu?.querySelectorAll('a').forEach(a => a.addEventListener('click', shut));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') shut(); });
  // Rotating to desktop width with the menu open would otherwise leave the
  // page scroll-locked behind a now-hidden overlay.
  window.matchMedia('(min-width: 768px)').addEventListener?.('change', (e) => { if (e.matches) shut(); });

  document.querySelectorAll('.accordion-item').forEach((item) => {
    const trigger = item.querySelector('.accordion-trigger');
    trigger?.addEventListener('click', () => item.classList.toggle('open'));
  });

  // ---------- visitor clock: tiny local time + country flag in the footer ----------
  // One client-side lookup per session via ipwho.is (free, no key, no cookie)
  // to get the visitor's country + timezone; cached in sessionStorage so it
  // only ever runs once per visit. Disclosed in the Privacy Policy. Fails
  // silently (element just stays empty) if the request is blocked or offline.
  (() => {
    const el = document.getElementById('visitor-clock');
    const wrap = document.getElementById('visitor-clock-wrap');
    if (!el || !wrap) return;
    const KEY = 'odVisitorGeo';

    const flagFor = (cc) => {
      if (!cc || cc.length !== 2) return '';
      return [...cc.toUpperCase()].map((c) => String.fromCodePoint(127397 + c.charCodeAt(0))).join('');
    };
    const render = (cc, tz) => {
      const flag = flagFor(cc);
      const tick = () => {
        let time = '';
        try { time = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: tz || undefined }).format(new Date()); } catch (e) {}
        const text = [flag, time].filter(Boolean).join(' ');
        el.textContent = text;
        wrap.style.display = text ? '' : 'none';
      };
      tick();
      setInterval(tick, 30000);
    };

    let cached;
    try { cached = JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) {}
    if (cached) { render(cached.cc, cached.tz); return; }

    fetch('https://ipwho.is/').then((r) => r.json()).then((d) => {
      if (!d || d.success === false) return;
      const cc = d.country_code || '';
      const tz = (d.timezone && d.timezone.id) || '';
      try { sessionStorage.setItem(KEY, JSON.stringify({ cc, tz })); } catch (e) {}
      render(cc, tz);
    }).catch(() => {});
  })();

  // ---------- language switcher: Pidgin / Yoruba / Hausa / French ----------
  // Covers the gate plus every page's headings, intro copy, buttons and the
  // home FAQ (full project names, categories, skill/tech tags and legal
  // body text are intentionally left in English — see the comment on
  // TRANSLATIONS below). English is always the default: a choice lasts only
  // for the current visit (sessionStorage). Switching SETS it then reloads
  // the page, rather than live-patching the DOM: translations are applied
  // once, on load, from the server-rendered English text, which is the only
  // way that's reliably correct on every page regardless of what else ran
  // before the switch.
  (() => {
    const TRANSLATIONS = {
      pcm: {
        filter_all: "All", filter_web: "Web", filter_shop: "E-commerce", filter_brand: "Branding", filter_product: "Plugins & Products",
        journey_title: "My journey", journey_l1: "First", journey_p1: "Website Design.", journey_s1: "GenM apprenticeship, 2018 — na there I start web.", journey_l2: "Then", journey_p2: "Freelance Development.", journey_s2: "I dey ship work for international clients for Upwork since 2021.", journey_l3: "Today", journey_p3: "I join design and code together.", journey_s3: "Founder, Odgrande Digital — 15+ live products for Nigeria, UK, Canada and USA.",
        nav_home: "Home", nav_works: "Works", nav_about: "About", nav_credentials: "Credentials", nav_contact: "Contact",
        gate_eyebrow: "Before you fly", gate_headline: "Tie your seatbelt well well — you dey about to feel wetin I fit build.",
        gate_subtext: "Yes or no, Captain (na me) dey wait make you confam say you dey enter.",
        gate_yes: "Yes, tie me well", gate_no: "No, I go waka",
        hero_tagline: "How far! I be Full-Stack Web Developer & Web Designer wey get 5+ years experience dey build digital products for clients for Nigeria, UK, Canada and USA.",
        hero_badge: "I dey available for work",
        featured_heading: "Works Wey Sweet Pass", services_heading: "Wetin I Dey Do",
        about_heading: "Who I Be", about_intro: "I be Full-Stack Web Developer and Web Designer wey like the point wey design no be just picture again, e don turn to work wey dey functional.",
        faq_heading: "Questions Wey People Dey Ask",
        footer_cta_heading: "Make we build something together.",
        footer_cta_sub: "If you get WordPress build, e-commerce store or any digital product for mind, make we yarn about am.",
        faq_q_0: "Wetin be your normal project timeline?",
        faq_a_0: "E depend on how big the project be. Landing page or brand site fit land for 1-2 weeks, while full WordPress build, e-commerce store or custom plugin go normally take 3-6 weeks including revisions.",
        faq_q_1: "You dey work with WordPress page builders or custom code?",
        faq_a_1: "Both. Most projects dey start for Elementor or similar builder make e fast, then I go move enter custom PHP, JavaScript and CSS anywhere wey the build need something wey page builder no fit do alone.",
        faq_q_2: "You fit take over website wey don already dey?",
        faq_a_2: "Yes. Plenty of the work for this portfolio na maintenance, fixes and new features wey I add for sites wey I no build originally.",
        faq_q_3: "You dey work with clients remotely?",
        faq_a_3: "Yes, every project for this portfolio na remote I deliver am, for clients wey dey Nigeria, UK, Canada and USA.",
        faq_q_4: "Wetin you need from me make we start?",
        faq_a_4: "Access to the hosting/domain (or plan to get am), any brand assets wey you don already get, and short description of wetin the site need to do. I fit helep fill the gaps from there.",
        about_meet: "Meet",
        about_build_text: "I dey build, customize and maintain websites for businesses, organizations and digital products.",
        about_work_text: "My work dey sit between visual implementation and practical engineering. I sabi work inside WordPress and page builders, then I go enter PHP, JavaScript and CSS when the problem need more than visual editor.",
        about_bio_text: "Full-Stack Web Developer and Web Designer wey get 5+ years experience dey build and maintain digital products for clients for Nigeria, UK, Canada and USA.",
        magic_heading: "Make we create website magic.",
        magic_text: "Whatever the brief be — new WordPress build, e-commerce store, or digital product wey need to feel alive — I go like helep build am.",
        start_project_btn: "Start a project",
        experience_heading: "Experience", education_heading: "Education", toolkit_heading: "Toolkit",
        certifications_heading: "Certifications", designer_award_heading: "Designer Of The Year",
        testimonials_heading: "Wetin Pipo Talk", archive_heading: "Personal Archive",
        view_credentials_btn: "View Credentials", view_cv_btn: "View CV", view_full_cv_btn: "View Full CV", view_pdf_btn: "View PDF",
        works_heading: "Works", all_works_btn: "All Works", more_about_btn: "Sabi more about me",
        credentials_heading: "Credentials", contact_heading: "Contact",
        contact_tagline: "Make we build something together.",
        contact_sub: "You get website, e-commerce build, WordPress problem or digital product for mind? Tell me wetin you dey work on and I go reach you back within one or two days.",
        contact_label_email: "Email", contact_label_phone: "Phone", contact_label_location: "Location",
        footer_socials_heading: "Socials", footer_nav_heading: "Navigation",
        footer_privacy: "Privacy", footer_cookies: "Cookies", footer_sitemap: "Sitemap",
        footer_whats_next: "Wetin dey come next?",
        sitemap_sub: "Every page wey dey this site, for one place.",
        sitemap_main_pages: "Main Pages", sitemap_legal: "Legal",
        privacy_heading: "Privacy Policy", cookies_heading: "Cookie Policy",
        fact_client: "Client", fact_category: "Category", fact_services: "Services", fact_year: "Year",
        live_site_btn: "Live Site"
      },
      yo: {
        filter_all: "Gbogbo rẹ̀", filter_web: "Wẹ́ẹ̀bù", filter_shop: "Ọjà Orí Ayélujára", filter_brand: "Àmì Ìdánimọ̀", filter_product: "Àwọn Plugin & Ọjà",
        journey_title: "Ìrìn Àjò Mi", journey_l1: "Àkọ́kọ́", journey_p1: "Àpẹrẹ Wẹ́ẹ̀bù.", journey_s1: "Ìkọ́ṣẹ́ GenM, 2018 — ìbẹ̀rẹ̀ mi nínú wẹ́ẹ̀bù.", journey_l2: "Lẹ́yìn náà", journey_p2: "Ìdàgbàsókè Aládàáni.", journey_s2: "Mo ń ṣiṣẹ́ fún àwọn oníbàárà káàkiri àgbáyé lórí Upwork láti 2021.", journey_l3: "Lónìí", journey_p3: "Mo so àpẹrẹ àti kóòdù pọ̀.", journey_s3: "Olùdásílẹ̀, Odgrande Digital — ọjà 15+ tí ó wà láàyè ní Nàìjíríà, UK, Kánádà àti USA.",
        nav_home: "Ile", nav_works: "Isẹ́", nav_about: "Nipa Mi", nav_credentials: "Ẹ̀rí", nav_contact: "Kan Si Mi",
        gate_eyebrow: "Kí o tó fò", gate_headline: "Di àmùrè rẹ mú — o fẹ́ bẹ̀rẹ̀ sí nímọ̀lára ohun tí mo lè kọ́.",
        gate_subtext: "Bẹ́ẹ̀ni tàbí rárá, Kapútánì (èmi ni) ń dúró de ìjẹ́rìí wíwọ̀ ọkọ̀.",
        gate_yes: "Bẹ́ẹ̀ni, di mi mú", gate_no: "Rárá, màá rìn",
        hero_tagline: "Báwo! Èmi ni Full-Stack Web Developer àti Web Designer tó ní ìrírí ọdún 5+ nínú kíkọ́ àwọn ọjà dígítà fún àwọn oníbàárà kárí Nàìjíríà, UK, Canada àti USA.",
        hero_badge: "Mo wà ní àyè fún iṣẹ́",
        featured_heading: "Àwọn Iṣẹ́ Tó Dára Jùlọ", services_heading: "Àwọn Iṣẹ́ Tí Mo Ń Ṣe",
        about_heading: "Nípa Mi", about_intro: "Èmi ni Full-Stack Web Developer àti Web Designer tí inú rẹ̀ dùn sí ibi tí àpẹẹrẹ (design) ti máa dá ṣiṣẹ́ gẹ́gẹ́ bí ọjà gidi.",
        faq_heading: "Àwọn Ìbéèrè Tí Wọ́n Sábà Máa Ń Béèrè",
        footer_cta_heading: "Jẹ́ ká ṣiṣẹ́ papọ̀.",
        footer_cta_sub: "Tó bá jẹ́ pé o ní WordPress build, ilé ìtajà e-commerce tàbí ọjà dígítà èyíkéyìí lọ́kàn, jẹ́ ká sọ̀rọ̀ nípa rẹ̀.",
        faq_q_0: "Kí ni àkókò tí iṣẹ́ rẹ máa ń gbà déédéé?",
        faq_a_0: "Ó dá lórí bí iṣẹ́ náà ṣe tóbi tó. Ojú-ewé kan tàbí ojúlé ìkéde lè parí láàrin ọ̀sẹ̀ 1-2, nígbà tí WordPress tó pé, ilé ìtajà e-commerce tàbí plugin àdáni máa ń gba ọ̀sẹ̀ 3-6 pẹ̀lú àtúnṣe.",
        faq_q_1: "Ṣé o máa ń lo WordPress page builders tàbí koodu àdáni?",
        faq_a_1: "Méjèèjì. Ọ̀pọ̀ iṣẹ́ máa ń bẹ̀rẹ̀ nínú Elementor tàbí irú rẹ̀ fún kíákíá, lẹ́yìn náà a óò wọ inú PHP àdáni, JavaScript àti CSS níbikíbi tí iṣẹ́ náà bá nílò ohun tí page builder kò lè ṣe fúnra rẹ̀.",
        faq_q_2: "Ṣé o lè gba ojúlé tó ti wà tẹ́lẹ̀ rí?",
        faq_a_2: "Bẹ́ẹ̀ni. Ọ̀pọ̀lọ́pọ̀ iṣẹ́ nínú portfolio yìí jẹ́ ìtọ́jú, àtúnṣe àti àwọn ẹ̀yà tuntun tí mo fi kún àwọn ojúlé tí kì í ṣe èmi ni mo kọ́ wọn ní àkọ́kọ́.",
        faq_q_3: "Ṣé o máa ń ṣiṣẹ́ pẹ̀lú àwọn oníbàárà láti ọ̀nà jíjìn?",
        faq_a_3: "Bẹ́ẹ̀ni, gbogbo iṣẹ́ nínú portfolio yìí ni mo ṣe láti ọ̀nà jíjìn, fún àwọn oníbàárà kárí Nàìjíríà, UK, Canada àti USA.",
        faq_q_4: "Kí ni o nílò lọ́wọ́ mi kí a tó bẹ̀rẹ̀?",
        faq_a_4: "Ààyè sí hosting/domain (tàbí ìpinnu láti rí i gbà), àwọn èròjà àmì-ọjà tí o ti ní, àti ọ̀rọ̀ kúkúrú nípa ohun tí ojúlé náà nílò láti ṣe. Mo lè ràn ọ́ lọ́wọ́ láti kún àwọn àlàfo yòókù láti ibẹ̀.",
        about_meet: "Pàdé",
        about_build_text: "Mo máa ń kọ́, ṣe àtúnṣe àti bójútó àwọn ojúlé fún àwọn iṣẹ́, àjọ àti àwọn ọjà dígítà.",
        about_work_text: "Iṣẹ́ mi wà láàrin ìmúṣẹ wíwo àti ìmọ̀-ẹ̀rọ amúlò. Mo mọ bí a ṣe ń ṣiṣẹ́ nínú WordPress àti page builders, lẹ́yìn náà kí n wọ inú PHP, JavaScript àti CSS nígbà tí ìṣòro náà bá nílò ju ohun tí visual editor lè ṣe lọ.",
        about_bio_text: "Full-Stack Web Developer àti Web Designer tó ní ìrírí ọdún 5+ nínú kíkọ́ àti bíbójútó àwọn ọjà dígítà fún àwọn oníbàárà kárí Nàìjíríà, UK, Canada àti USA.",
        magic_heading: "Jẹ́ ká ṣẹ̀dá idán ojúlé.",
        magic_text: "Ohunkóhun tí ìbéèrè náà bá jẹ́ — WordPress tuntun, ilé ìtajà e-commerce, tàbí ọjà dígítà tí ó nílò láti dà bí ẹni tí ó wà láàyè — màá fẹ́ràn láti ran ọ́ lọ́wọ́ láti kọ́ ọ.",
        start_project_btn: "Bẹ̀rẹ̀ iṣẹ́ kan",
        experience_heading: "Ìrírí", education_heading: "Ẹ̀kọ́", toolkit_heading: "Àwọn Irinṣẹ́",
        certifications_heading: "Àwọn Ẹ̀rí", designer_award_heading: "Oníṣẹ́-aṣàpẹẹrẹ Ọdún",
        testimonials_heading: "Ọ̀rọ̀ Wọn", archive_heading: "Àkójọpọ̀ Ti Ara Ẹni",
        view_credentials_btn: "Wo Àwọn Ẹ̀rí", view_cv_btn: "Wo CV", view_full_cv_btn: "Wo CV Kíkún", view_pdf_btn: "Wo PDF",
        works_heading: "Iṣẹ́", all_works_btn: "Gbogbo Iṣẹ́", more_about_btn: "Kàwé síwájú sí mi",
        credentials_heading: "Àwọn Ẹ̀rí", contact_heading: "Kàn Sí Mi",
        contact_tagline: "Jẹ́ ká ṣiṣẹ́ papọ̀.",
        contact_sub: "Ṣé o ní ojúlé, e-commerce, ìṣòro WordPress tàbí ọjà dígítà lọ́kàn? Sọ ohun tí o ń ṣiṣẹ́ lé e fún mi, màá dá ọ padà láàrin ọjọ́ kan tàbí méjì.",
        contact_label_email: "Imeèlì", contact_label_phone: "Fóònù", contact_label_location: "Ibùdó",
        footer_socials_heading: "Àwùjọ", footer_nav_heading: "Ìtọ́sọ́nà",
        footer_privacy: "Àṣírí", footer_cookies: "Kúkì", footer_sitemap: "Àwòrán Ojúlé",
        footer_whats_next: "Kí ni ó kàn?",
        sitemap_sub: "Gbogbo ojú-ewé lórí ojúlé yìí, ní ibì kan.",
        sitemap_main_pages: "Àwọn Ojú-Ewé Pàtàkì", sitemap_legal: "Òfin",
        privacy_heading: "Ìlànà Àṣírí", cookies_heading: "Ìlànà Kúkì",
        fact_client: "Oníbàárà", fact_category: "Ẹ̀ka", fact_services: "Iṣẹ́", fact_year: "Ọdún",
        live_site_btn: "Ojúlé Tó Ń Ṣiṣẹ́"
      },
      ha: {
        filter_all: "Duka", filter_web: "Yanar Gizo", filter_shop: "Kasuwancin Intanet", filter_brand: "Alamar Kasuwanci", filter_product: "Plugins & Kayayyaki",
        journey_title: "Tafiyata", journey_l1: "Da farko", journey_p1: "Zanen Yanar Gizo.", journey_s1: "Koyon sana'a a GenM, 2018 — farkon aikina a yanar gizo.", journey_l2: "Sannan", journey_p2: "Ci gaba mai zaman kansa.", journey_s2: "Ina isar da ayyuka ga abokan ciniki na duniya a Upwork tun 2021.", journey_l3: "Yau", journey_p3: "Ina haɗa zane da lamba.", journey_s3: "Wanda ya kafa Odgrande Digital — kayayyaki 15+ masu aiki a Najeriya, UK, Kanada da Amurka.",
        nav_home: "Gida", nav_works: "Ayyuka", nav_about: "Game da Ni", nav_credentials: "Takardun Shaida", nav_contact: "Tuntuɓe Ni",
        gate_eyebrow: "Kafin ka tashi", gate_headline: "Ka ɗaura bel ɗinka — kana gab da jin abin da zan iya ginawa.",
        gate_subtext: "E ko a'a, Kyaftin (ni ne) yana jiran tabbacin shiga jirgin.",
        gate_yes: "E, ɗaura ni", gate_no: "A'a, zan yi tafiya",
        hero_tagline: "Sannu! Ni ne Full-Stack Web Developer da Web Designer mai fiye da shekaru 5 na gogewa wajen gina kayayyakin dijital ga abokan ciniki a Najeriya, Birtaniya, Kanada da Amurka.",
        hero_badge: "Ina samuwa don aiki",
        featured_heading: "Ayyukan Da Aka Fi So", services_heading: "Ayyukan Da Nake Yi",
        about_heading: "Game da Ni", about_intro: "Ni ne Full-Stack Web Developer da Web Designer wanda ke jin daɗin lokacin da zane ya daina zama hoto kawai ya koma kayan aiki mai amfani.",
        faq_heading: "Tambayoyin Da Ake Yawan Yi",
        footer_cta_heading: "Bari mu gina wani abu tare.",
        footer_cta_sub: "Idan kana da shirin WordPress, kantin e-commerce ko wani kayan dijital a zuciya, bari mu tattauna game da shi.",
        faq_q_0: "Mene ne tsarin lokacin da ake amfani da shi a aikinka?",
        faq_a_0: "Ya danganta da girman aikin. Shafin saukewa ko shafin alama na iya kammala a cikin makonni 1-2, yayin da cikakken WordPress, kantin e-commerce ko plugin na musamman yakan ɗauki makonni 3-6 tare da gyare-gyare.",
        faq_q_1: "Kana aiki da WordPress page builders ko lambar musamman?",
        faq_a_1: "Dukansu biyu. Yawancin ayyuka suna farawa a Elementor ko makamancinsa don sauri, sannan in shiga PHP, JavaScript da CSS na musamman duk inda aikin ke bukatar abin da page builder ba zai iya yi shi kaɗai ba.",
        faq_q_2: "Za ka iya karɓar gidan yanar gizo da ake da shi tun da?",
        faq_a_2: "E. Yawancin aikin da ke cikin wannan portfolio shi ne kulawa, gyare-gyare da sabbin fasaloli da na ƙara wa shafukan da ban gina su tun farko ba.",
        faq_q_3: "Kana aiki da abokan ciniki daga nesa?",
        faq_a_3: "E, kowane aiki a cikin wannan portfolio an kai shi daga nesa, ga abokan ciniki a Najeriya, Birtaniya, Kanada da Amurka.",
        faq_q_4: "Me kake bukata daga gare ni mu fara?",
        faq_a_4: "Shiga cikin hosting/domain (ko shiri na samunsa), duk wasu kayan alama da ka riga ka samu, da ɗan taƙaitaccen bayani game da abin da shafin yake bukata ya yi. Zan iya taimaka cike giɓi daga nan.",
        about_meet: "Haɗu da",
        about_build_text: "Ina ginawa, daidaitawa da kula da shafukan yanar gizo don kasuwanci, ƙungiyoyi da kayayyakin dijital.",
        about_work_text: "Aikina yana tsakanin aiwatar da gani da injiniyanci mai amfani. Ina jin daɗin yin aiki a cikin WordPress da page builders, sannan in shiga PHP, JavaScript da CSS idan matsalar ta bukaci fiye da abin da visual editor zai iya yi.",
        about_bio_text: "Full-Stack Web Developer da Web Designer mai fiye da shekaru 5 na gogewa wajen ginawa da kula da kayayyakin dijital ga abokan ciniki a Najeriya, Birtaniya, Kanada da Amurka.",
        magic_heading: "Bari mu ƙirƙiri sihirin shafin yanar gizo.",
        magic_text: "Duk abin da buƙatar take — sabon shirin WordPress, kantin e-commerce, ko kayan dijital da yake bukatar jin rai — zan so in taimaka gina shi.",
        start_project_btn: "Fara aiki",
        experience_heading: "Gogewa", education_heading: "Ilimi", toolkit_heading: "Kayan Aiki",
        certifications_heading: "Takardun Shaida", designer_award_heading: "Mai Zane Na Shekara",
        testimonials_heading: "Abin Da Suka Ce", archive_heading: "Tarin Hotuna Na Kai",
        view_credentials_btn: "Duba Takardun Shaida", view_cv_btn: "Duba CV", view_full_cv_btn: "Duba Cikakken CV", view_pdf_btn: "Duba PDF",
        works_heading: "Ayyuka", all_works_btn: "Dukkan Ayyuka", more_about_btn: "Ƙarin bayani game da ni",
        credentials_heading: "Takardun Shaida", contact_heading: "Tuntuɓe Ni",
        contact_tagline: "Bari mu gina wani abu tare.",
        contact_sub: "Kana da shafin yanar gizo, kantin e-commerce, matsalar WordPress ko kayan dijital a zuciya? Gaya mani abin da kake aiki akai, zan amsa maka cikin kwana ɗaya ko biyu.",
        contact_label_email: "Imel", contact_label_phone: "Waya", contact_label_location: "Wuri",
        footer_socials_heading: "Hanyoyin Sada Zumunta", footer_nav_heading: "Kewayawa",
        footer_privacy: "Sirri", footer_cookies: "Cookies", footer_sitemap: "Taswirar Shafi",
        footer_whats_next: "Mene ne na gaba?",
        sitemap_sub: "Kowane shafi a wannan gidan yanar gizo, a wuri ɗaya.",
        sitemap_main_pages: "Manyan Shafuka", sitemap_legal: "Shari'a",
        privacy_heading: "Manufar Sirri", cookies_heading: "Manufar Cookies",
        fact_client: "Abokin Ciniki", fact_category: "Rukuni", fact_services: "Ayyuka", fact_year: "Shekara",
        live_site_btn: "Shafin Yanar Gizo"
      },
      fr: {
        filter_all: "Tout", filter_web: "Web", filter_shop: "E-commerce", filter_brand: "Identité de marque", filter_product: "Plugins & Produits",
        journey_title: "Mon parcours", journey_l1: "D'abord", journey_p1: "Design web.", journey_s1: "Apprentissage chez GenM, 2018 — mes débuts dans le web.", journey_l2: "Puis", journey_p2: "Développement freelance.", journey_s2: "Des livraisons pour des clients internationaux sur Upwork depuis 2021.", journey_l3: "Aujourd'hui", journey_p3: "Je relie design et code.", journey_s3: "Fondateur d'Odgrande Digital — plus de 15 produits en ligne au Nigeria, au Royaume-Uni, au Canada et aux États-Unis.",
        nav_home: "Accueil", nav_works: "Travaux", nav_about: "À propos", nav_credentials: "Qualifications", nav_contact: "Contact",
        gate_eyebrow: "Avant de décoller", gate_headline: "Attachez votre ceinture — vous allez ressentir ce que je peux construire.",
        gate_subtext: "Oui ou non, le Capitaine (c'est moi) attend la confirmation d'embarquement.",
        gate_yes: "Oui, attachez-moi", gate_no: "Non, je vais marcher",
        hero_tagline: "Salut ! Je suis Développeur Web Full-Stack & Designer Web avec plus de 5 ans d'expérience dans la création de produits numériques pour des clients au Nigeria, au Royaume-Uni, au Canada et aux États-Unis.",
        hero_badge: "Disponible pour travailler",
        featured_heading: "Projets Phares", services_heading: "Services",
        about_heading: "À propos", about_intro: "Je suis Développeur Web Full-Stack et Designer Web qui aime le moment où un design cesse d'être une image pour devenir un produit fonctionnel.",
        faq_heading: "FAQ",
        footer_cta_heading: "Travaillons ensemble.",
        footer_cta_sub: "Vous avez un projet WordPress, une boutique e-commerce ou un produit numérique en tête ? Parlons-en.",
        faq_q_0: "Quel est le délai habituel d'un projet ?",
        faq_a_0: "Cela dépend de l'ampleur du projet. Une landing page ou un site de marque peut être prêt en 1 à 2 semaines, tandis qu'un site WordPress complet, une boutique e-commerce ou un plugin sur mesure prend généralement 3 à 6 semaines, révisions incluses.",
        faq_q_1: "Travaillez-vous avec des constructeurs de pages WordPress ou du code sur mesure ?",
        faq_a_1: "Les deux. La plupart des projets démarrent sur Elementor ou un outil similaire pour aller vite, puis passent au PHP, JavaScript et CSS sur mesure partout où le projet a besoin de quelque chose qu'un constructeur de pages ne peut pas faire seul.",
        faq_q_2: "Pouvez-vous reprendre un site existant ?",
        faq_a_2: "Oui. Une grande partie du travail présenté dans ce portfolio consiste en maintenance, corrections et nouvelles fonctionnalités ajoutées à des sites que je n'ai pas construits à l'origine.",
        faq_q_3: "Travaillez-vous avec des clients à distance ?",
        faq_a_3: "Oui, chaque projet de ce portfolio a été livré à distance, pour des clients au Nigeria, au Royaume-Uni, au Canada et aux États-Unis.",
        faq_q_4: "De quoi avez-vous besoin de ma part pour commencer ?",
        faq_a_4: "L'accès à l'hébergement/domaine (ou un plan pour l'obtenir), tous les éléments de marque que vous avez déjà, et une courte description de ce que le site doit faire. Je peux aider à combler les lacunes à partir de là.",
        about_meet: "Rencontrez",
        about_build_text: "Je construis, personnalise et maintiens des sites web pour des entreprises, des organisations et des produits numériques.",
        about_work_text: "Mon travail se situe entre la mise en œuvre visuelle et l'ingénierie pratique. Je suis à l'aise avec WordPress et les constructeurs de pages, puis je passe au PHP, JavaScript et CSS quand le problème demande plus qu'un éditeur visuel.",
        about_bio_text: "Développeur Web Full-Stack et Designer Web avec plus de 5 ans d'expérience dans la création et la maintenance de produits numériques pour des clients au Nigeria, au Royaume-Uni, au Canada et aux États-Unis.",
        magic_heading: "Créons de la magie web.",
        magic_text: "Quel que soit le besoin — un nouveau site WordPress, une boutique e-commerce, ou un produit numérique qui doit sembler vivant — j'aimerais vous aider à le construire.",
        start_project_btn: "Démarrer un projet",
        experience_heading: "Expérience", education_heading: "Formation", toolkit_heading: "Boîte à outils",
        certifications_heading: "Certifications", designer_award_heading: "Designer De L'Année",
        testimonials_heading: "Leurs Témoignages", archive_heading: "Archives Personnelles",
        view_credentials_btn: "Voir les qualifications", view_cv_btn: "Voir le CV", view_full_cv_btn: "Voir le CV complet", view_pdf_btn: "Voir le PDF",
        works_heading: "Travaux", all_works_btn: "Tous les travaux", more_about_btn: "En savoir plus sur moi",
        credentials_heading: "Qualifications", contact_heading: "Contact",
        contact_tagline: "Construisons quelque chose ensemble.",
        contact_sub: "Vous avez un site web, un projet e-commerce, un problème WordPress ou un produit numérique en tête ? Dites-moi sur quoi vous travaillez et je vous répondrai sous un jour ou deux.",
        contact_label_email: "E-mail", contact_label_phone: "Téléphone", contact_label_location: "Lieu",
        footer_socials_heading: "Réseaux", footer_nav_heading: "Navigation",
        footer_privacy: "Confidentialité", footer_cookies: "Cookies", footer_sitemap: "Plan du site",
        footer_whats_next: "Et maintenant ?",
        sitemap_sub: "Toutes les pages de ce site, au même endroit.",
        sitemap_main_pages: "Pages Principales", sitemap_legal: "Mentions Légales",
        privacy_heading: "Politique de Confidentialité", cookies_heading: "Politique de Cookies",
        fact_client: "Client", fact_category: "Catégorie", fact_services: "Services", fact_year: "Année",
        live_site_btn: "Site en ligne"
      }
    };
    // Project names, client names, categories, service/tech tags (WordPress,
    // Shopify, PHP, etc.), the Toolkit tag list and the full Privacy/Cookie
    // policy body text are deliberately NOT translated above — they're
    // proper nouns or technical terms that don't have a meaningful
    // translation, or (for the legal body copy) too long to hand-translate
    // reliably across four languages at launch.
    const LABELS = { en: "EN", pcm: "Pidgin", yo: "Yoruba", ha: "Hausa", fr: "Français" };
    const KEY = 'odLang';

    const apply = (lang) => {
      const dict = TRANSLATIONS[lang];
      if (!dict) return;
      document.querySelectorAll('[data-i18n]').forEach((el) => {
        const key = el.dataset.i18n;
        if (dict[key]) el.textContent = dict[key];
      });
      // Keep <html lang> honest once real translated text is on the page —
      // otherwise Chrome's own "Translate this page" can trigger on the
      // mismatch and silently rewrite everything back to the browser's
      // preferred language.
      document.documentElement.lang = lang;
    };

    let saved;
    try { localStorage.removeItem(KEY); } catch (e) {} // retire the old persistent choice
    try { saved = sessionStorage.getItem(KEY); } catch (e) {}
    if (saved && !TRANSLATIONS[saved]) saved = 'en';
    if (saved && saved !== 'en') apply(saved);
    // Shared lookup for text rendered later by script (e.g. the Vue works filter).
    window.odT = (key, fallback) => (TRANSLATIONS[saved] && TRANSLATIONS[saved][key]) || fallback;

    document.querySelectorAll('.lang-current').forEach((el) => { el.textContent = LABELS[saved] || 'EN'; });
    document.querySelectorAll('.lang-option').forEach((btn) => {
      btn.setAttribute('aria-current', btn.dataset.lang === (saved || 'en') ? 'true' : 'false');
    });

    document.querySelectorAll('.lang-switcher').forEach((sw) => {
      const toggle = sw.querySelector('.lang-toggle');
      toggle?.addEventListener('click', () => {
        const open = sw.classList.toggle('open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    document.querySelectorAll('.lang-option').forEach((btn) => {
      btn.addEventListener('click', () => {
        const lang = btn.dataset.lang;
        try { sessionStorage.setItem(KEY, lang); } catch (e) {}
        location.reload();
      });
    });
    document.addEventListener('click', (e) => {
      document.querySelectorAll('.lang-switcher.open').forEach((sw) => {
        if (!sw.contains(e.target)) sw.classList.remove('open');
      });
    });
  })();

  // ---------- theme toggle (dark default, light on request) ----------
  (() => {
    const KEY = 'odTheme';
    const root = document.documentElement;
    const apply = (theme) => {
      if (theme === 'light') root.setAttribute('data-theme', 'light');
      else root.removeAttribute('data-theme');
      document.querySelectorAll('.theme-toggle').forEach((btn) => {
        btn.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
      });
    };
    apply(root.getAttribute('data-theme') === 'light' ? 'light' : 'dark');
    document.querySelectorAll('.theme-toggle').forEach((btn) => {
      btn.addEventListener('click', () => {
        const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        apply(next);
        try { localStorage.setItem(KEY, next); } catch (e) {}
      });
    });
  })();

  // ---------- landing gate: a two-way question before the site reveals ----------
  // Shown once per session, FIRST — visible from first paint (see the CSS:
  // this element defaults to visible, it's not waiting on JS to appear), so
  // nothing underneath it is ever seen before the visitor answers. "Yes"
  // opens straight into the site (the preloader then plays fresh, see
  // below). "No" swaps in a creative one-more-try persuasion panel; if
  // they're still leaving after that, a short optional feedback form
  // appears and the tab then tries to close itself. Dispatches
  // 'gate:closed' so the preloader knows when to start.
  (() => {
    const gate = document.getElementById('gate');
    if (!gate) { window.dispatchEvent(new Event('gate:closed')); return; }
    const KEY = 'odGateSeen';
    let seen;
    try { seen = sessionStorage.getItem(KEY); } catch (e) {}
    if (seen) { gate.remove(); window.dispatchEvent(new Event('gate:closed')); return; }

    const question = document.getElementById('gateQuestion');
    const persuade = document.getElementById('gatePersuade');
    const feedback = document.getElementById('gateFeedback');
    const yesBtn = document.getElementById('gateYes');
    const noBtn = document.getElementById('gateNo');
    const persuadeYesBtn = document.getElementById('gatePersuadeYes');
    const stillLeavingBtn = document.getElementById('gateStillLeaving');
    const skipBtn = document.getElementById('gateSkip');
    const justLeaveBtn = document.getElementById('gateJustLeave');

    const markSeen = () => { try { sessionStorage.setItem(KEY, '1'); } catch (e) {} };
    const enterSite = () => {
      markSeen();
      window.dispatchEvent(new Event('gate:closed'));
      gate.classList.add('done');
      // CSS transition + timer (not a GSAP tween), so the gate is always
      // removed even if the tab is in the background (rAF paused).
      gate.style.transition = 'opacity .5s ease';
      gate.style.opacity = '0';
      setTimeout(() => gate.remove(), 500);
    };
    const swapPanel = (hide, show) => {
      hide.style.display = 'none';
      show.classList.add('show');
      if (window.gsap) gsap.from(show, { opacity: 0, y: 16, duration: .5, ease: 'power2.out' });
    };
    // Browsers only allow script to close tabs they themselves opened, so a
    // tab the visitor navigated to directly can't always be force-closed —
    // this is a best-effort attempt with a graceful, honest fallback.
    const tryClose = () => {
      try { window.open('', '_self'); } catch (e) {}
      window.close();
      setTimeout(() => {
        if (document.hidden) return;
        feedback.innerHTML = '<p class="t-xl">All set — you can close this tab now.</p><div class="gate-actions"><button class="btn" id="gateFallbackIn" type="button">Actually, take me in</button></div>';
        document.getElementById('gateFallbackIn')?.addEventListener('click', enterSite);
      }, 350);
    };

    yesBtn?.addEventListener('click', enterSite);
    noBtn?.addEventListener('click', () => swapPanel(question, persuade));
    persuadeYesBtn?.addEventListener('click', enterSite);
    stillLeavingBtn?.addEventListener('click', () => swapPanel(persuade, feedback));
    skipBtn?.addEventListener('click', enterSite);
    justLeaveBtn?.addEventListener('click', tryClose);
    feedback?.addEventListener('submit', (e) => {
      e.preventDefault();
      const wa = feedback.dataset.whatsapp || '';
      const reason = feedback.reason.value.trim();
      const email = feedback.email.value.trim();
      const lines = ["Feedback from odgrande.github.io:", reason, email ? `Reply to: ${email}` : ''].filter(Boolean).join('\n');
      // Navigating the tab to WhatsApp IS the "leave". Deliberately NOT marked
      // as seen: only "yes, take me in" lets anyone past the gate, so pressing
      // Back from WhatsApp lands on the question again.
      window.location.href = `${wa}?text=${encodeURIComponent(lines)}`;
    });

    // Back/forward cache: a page restored from history comes back exactly as
    // it was left (e.g. on the feedback form) — reload so it starts over at
    // the question, with nothing behind it.
    window.addEventListener('pageshow', (e) => {
      if (e.persisted && document.body.contains(gate)) location.reload();
    });

    if (window.gsap) gsap.from(gate.querySelector('.gate-inner'), { opacity: 0, y: 24, duration: .6, ease: 'power3.out' });
  })();

  // ---------- cookie banner: small, shows once per session, after the preloader clears ----------
  (() => {
    const banner = document.getElementById('cookie-banner');
    if (!banner) return;
    const KEY = 'odCookieNoticeSeen';
    let seen;
    try { seen = sessionStorage.getItem(KEY); } catch (e) {}
    if (seen) { banner.remove(); return; }

    const dismiss = () => {
      try { sessionStorage.setItem(KEY, '1'); } catch (e) {}
      banner.classList.remove('show');
      setTimeout(() => banner.remove(), 400);
    };
    banner.querySelector('.cookie-accept')?.addEventListener('click', dismiss);
    banner.querySelector('.cookie-close')?.addEventListener('click', dismiss);

    const reveal = () => setTimeout(() => banner.classList.add('show'), 600);
    window.addEventListener('preloader:done', () => setTimeout(reveal, 900), { once: true });
  })();

  // ---------- exit-intent popup: comical "drop your idea" prompt ----------
  // Armed only after the preloader clears (so it can't fire mid-load), shown
  // once per session the moment the cursor leaves out the top of the
  // viewport, and marked seen as soon as it's shown so it never nags twice.
  (() => {
    const popup = document.getElementById('exit-popup');
    if (!popup) return;
    const KEY = 'odExitSeen';

    const question = document.getElementById('exitQuestion');
    const form = document.getElementById('exitForm');
    const openFormBtn = document.getElementById('exitOpenForm');
    const dismissBtn = document.getElementById('exitDismiss');
    const skipBtn = document.getElementById('exitSkip');
    const closeBtn = document.getElementById('exitClose');

    const closePopup = () => {
      popup.classList.add('done');
      if (window.gsap) gsap.to(popup, { opacity: 0, duration: .4, ease: 'power1.out', onComplete: () => popup.remove() });
      else { popup.style.transition = 'opacity .4s ease'; popup.style.opacity = '0'; setTimeout(() => popup.remove(), 400); }
    };
    const showPopup = () => {
      try { sessionStorage.setItem(KEY, '1'); } catch (e) {}
      popup.classList.add('show');
      if (window.gsap) gsap.from(popup.querySelector('.exit-inner'), { opacity: 0, y: 40, scale: .92, duration: .6, ease: 'back.out(1.6)' });
    };

    closeBtn?.addEventListener('click', closePopup);
    dismissBtn?.addEventListener('click', closePopup);
    skipBtn?.addEventListener('click', closePopup);
    openFormBtn?.addEventListener('click', () => {
      question.style.display = 'none';
      form.classList.add('show');
      if (window.gsap) gsap.from(form, { opacity: 0, y: 16, duration: .5, ease: 'power2.out' });
    });
    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      const wa = form.dataset.whatsapp || '';
      const idea = form.idea.value.trim();
      const email = form.email.value.trim();
      const lines = ["Idea from odgrande.github.io:", idea, email ? `Reply to: ${email}` : ''].filter(Boolean).join('\n');
      window.open(`${wa}?text=${encodeURIComponent(lines)}`, '_blank', 'noopener');
      closePopup();
    });

    // Only real "about to leave" signals, once per session:
    //  - desktop: the pointer exits through the TOP edge of the window
    //    (heading for the tabs / address bar / close button) while moving
    //    upward — not sideways exits, not hovering an iframe, not the gate;
    //  - touch: a fast flick back up toward the address bar after reading a
    //    good way down the page (the standard mobile exit-intent signal).
    // Never in the first few seconds, and never over the menu or lightbox.
    const MIN_DWELL = 8000;
    const arm = () => {
      let seen;
      try { seen = sessionStorage.getItem(KEY); } catch (e) {}
      if (seen) { popup.remove(); return; }
      const armedAt = performance.now();
      let fired = false;
      let onScroll = null;
      const busy = () => {
        const g = document.getElementById('gate');
        return document.body.classList.contains('menu-open') || (g && !g.classList.contains('done'));
      };
      const fire = () => {
        if (fired || busy() || performance.now() - armedAt < MIN_DWELL) return;
        fired = true;
        document.removeEventListener('mouseout', onOut);
        if (onScroll) window.removeEventListener('scroll', onScroll);
        showPopup();
      };

      let lastY = null;
      document.addEventListener('mousemove', (e) => { lastY = e.clientY; }, { passive: true });
      const onOut = (e) => {
        if (e.relatedTarget || e.toElement) return;      // still inside the page
        if (e.clientY > 0) return;                       // left via side/bottom
        if (lastY !== null && lastY > 120) return;       // not travelling up toward the browser UI
        fire();
      };
      document.addEventListener('mouseout', onOut);

      if (window.matchMedia('(hover: none)').matches) {
        let prevY = window.scrollY, prevT = performance.now(), maxDepth = 0;
        onScroll = () => {
          const y = window.scrollY, t = performance.now();
          const doc = document.documentElement.scrollHeight - window.innerHeight;
          maxDepth = Math.max(maxDepth, doc > 0 ? y / doc : 0);
          const v = (y - prevY) / Math.max(t - prevT, 1);  // px per ms; negative = upward
          prevY = y; prevT = t;
          if (maxDepth > 0.35 && v < -2.2 && y < doc * 0.5) fire();
        };
        window.addEventListener('scroll', onScroll, { passive: true });
      }
    };
    window.addEventListener('preloader:done', arm, { once: true });
  })();

  // ---------- lightbox ----------
  const lightbox = document.createElement('div');
  lightbox.className = 'lightbox';
  lightbox.innerHTML = '<button class="lightbox-close" aria-label="Close"><svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24"><path d="M5 5L19 19M19 5L5 19" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round"/></svg></button><img alt="">';
  document.body.appendChild(lightbox);
  const lbImg = lightbox.querySelector('img');
  const showLightbox = (src, alt) => { lbImg.src = src; lbImg.alt = alt || ''; lightbox.classList.add('open'); document.body.classList.add('menu-open'); };
  const hideLightbox = () => { lightbox.classList.remove('open'); document.body.classList.remove('menu-open'); lbImg.src = ''; };
  lightbox.addEventListener('click', (e) => { if (e.target === lightbox || e.target.closest('.lightbox-close')) hideLightbox(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideLightbox(); });
  document.querySelectorAll('.image-frame .frame-box img, .gallery-grid img, .masonry-item img, .slider-slide img').forEach((img) => {
    img.addEventListener('click', () => showLightbox(img.dataset.full || img.currentSrc || img.src, img.alt));
  });

  // ---------- photo sliders: one per personal-photo subfolder ----------
  document.querySelectorAll('.photo-slider').forEach((slider) => {
    const track = slider.querySelector('.slider-track');
    const prev = slider.querySelector('.slider-prev');
    const next = slider.querySelector('.slider-next');
    const step = () => (track.querySelector('.slider-slide')?.offsetWidth || 300) + 16;
    prev?.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
    next?.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
  });

  // ---------- preloader: UplinkLoader (ThreeUI), embedded verbatim via iframe ----------
  // The loader document is fully self-contained (own styles/fonts/animation
  // loop) and runs independently; this just times the outer wrapper's fade
  // so it roughly lines up with the loader's own "UPLINK ESTABLISHED" beat
  // (see the RUN/HOLD constants in uplink-loader.html) while also blending
  // in a real page-load signal so the overlay never clears a half-built page.
  // Deliberately held back behind the landing gate — the iframe's src is
  // only set once 'gate:closed' fires, so the loading animation plays fresh
  // right after the visitor answers, instead of running unseen underneath.
  (() => {
    const el = document.getElementById('preloader');
    // The only place the site is ever revealed (see html.veil in the CSS).
    const unlockScroll = () => document.documentElement.classList.remove('no-scroll', 'veil');
    const revealNow = () => { unlockScroll(); window.odPreloaderDone = true; window.dispatchEvent(new Event('preloader:done')); };
    if (!el || document.documentElement.classList.contains('no-preloader')) {
      el?.remove();
      // Even with no preloader, never reveal while the gate is still asking.
      if (document.getElementById('gate')) window.addEventListener('gate:closed', revealNow, { once: true });
      else revealNow();
      return;
    }

    const start = () => {
      const frame = document.getElementById('preloader-frame');
      if (frame && !frame.getAttribute('src') && frame.dataset.src) frame.src = frame.dataset.src;

      let finished = false;
      const finish = () => {
        if (finished) return;
        finished = true;
        el.classList.add('done');
        setTimeout(() => el.remove(), 500);
        unlockScroll();
        window.odPreloaderDone = true; window.dispatchEvent(new Event('preloader:done'));
      };
      const failsafe = setTimeout(finish, 6000);

      let realLoadDone = false;
      Promise.race([
        Promise.all([
          document.fonts ? document.fonts.ready : Promise.resolve(),
          document.readyState === 'complete' ? Promise.resolve() : new Promise((r) => window.addEventListener('load', r, { once: true }))
        ]),
        new Promise((r) => setTimeout(r, 2600))
      ]).then(() => { realLoadDone = true; });

      const MIN_SHOW = 3700; // matches the loader's own RUN(3200)+HOLD(500) first-cycle beat
      const started = performance.now();
      const tryReveal = () => {
        if (realLoadDone && performance.now() - started >= MIN_SHOW) {
          clearTimeout(failsafe);
          // A CSS transition + timer rather than a GSAP tween: GSAP runs on
          // requestAnimationFrame, which browsers pause in background tabs,
          // and the reveal must never depend on that.
          // Unveil while the preloader is still fully opaque, so its fade
          // reveals the finished page rather than an empty background.
          document.documentElement.classList.remove('veil');
          el.style.transition = 'opacity .45s ease';
          el.style.opacity = '0';
          setTimeout(finish, 450);
        } else {
          setTimeout(tryReveal, 100);
        }
      };
      tryReveal();
    };

    if (document.getElementById('gate')) window.addEventListener('gate:closed', start, { once: true });
    else start();
  })();

  // ---------- "My journey": scroll-scrubbed letter narrative ----------
  // Modelled on guillaumezhu.com: the title's scattered letters gather as it
  // scrolls in, then a sticky full-screen stage shows one phrase at a time,
  // its letters rising in one after another, holding, then lifting away.
  // Everything is a pure function of the current scroll position (read from
  // getBoundingClientRect each frame), so scrolling back up plays it in
  // reverse exactly, and late-loading images above can't knock it out of
  // sync the way a pre-measured pin would. Runs after the translation module,
  // so it splits whichever language is showing.
  (() => {
    const sec = document.querySelector('.journey');
    if (!sec || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const clamp = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
    const easeOut = (t) => 1 - Math.pow(1 - t, 3);
    const easeIn = (t) => t * t * t;
    const split = (el) => {
      const text = el.textContent.trim();
      el.setAttribute('aria-label', text);
      el.textContent = '';
      text.split(/\s+/).forEach((word, wi, words) => {
        const w = document.createElement('span');
        w.className = 'jw';
        w.setAttribute('aria-hidden', 'true');
        [...word].forEach((ch) => {
          const c = document.createElement('span');
          c.className = 'jc';
          c.textContent = ch;
          w.appendChild(c);
        });
        el.appendChild(w);
        if (wi < words.length - 1) el.appendChild(document.createTextNode(' '));
      });
      return [...el.querySelectorAll('.jc')];
    };

    const heading = sec.querySelector('.journey-heading');
    const titleChars = split(heading).map((c, i) => ({
      el: c,
      // Deterministic scatter (no Math.random) so it looks the same each visit.
      y: 0.35 + ((i * 37) % 10) / 10 * 0.9,
      r: (((i * 53) % 9) - 4) * 4
    }));

    const runway = sec.querySelector('.journey-runway');
    const lines = [...sec.querySelectorAll('.journey-line')].map((line) => {
      const big = line.classList.contains('journey-label') ? line : line.querySelector('.journey-big');
      return { line, chars: split(big), sub: line.querySelector('.journey-sub'), state: '' };
    });
    sec.style.setProperty('--jl-count', lines.length);
    sec.classList.add('is-live');

    const K = 0.55; // letter stagger: how far behind the first letter the last one runs
    const setChars = (chars, fn) => {
      const n = Math.max(chars.length - 1, 1);
      chars.forEach((c, j) => { const [y, o] = fn(j / n); c.style.transform = `translate3d(0,${y}em,0)`; c.style.opacity = o; });
    };

    const update = () => {
      const vh = window.innerHeight;

      // Title: letters drop in from scattered heights as it reaches mid-screen.
      const tt = clamp((vh - heading.getBoundingClientRect().top) / (vh * 0.55));
      titleChars.forEach((c, j) => {
        const p = easeOut(clamp(tt * (1 + K) - K * (j / Math.max(titleChars.length - 1, 1))));
        c.el.style.transform = `translate3d(0,${(1 - p) * c.y * 3}em,0) rotate(${(1 - p) * c.r}deg)`;
      });

      // Stage: progress through the runway, one equal slice per line.
      const r = runway.getBoundingClientRect();
      const P = clamp(-r.top / Math.max(r.height - vh, 1));
      const seg = 1 / lines.length;
      lines.forEach((L, i) => {
        const last = i === lines.length - 1;
        const t = (P - i * seg) / seg;
        const state = t <= 0 ? 'before' : (!last && t >= 1) ? 'after' : 'active';
        if (state !== 'active' && state === L.state) return; // nothing to redraw off-screen
        L.state = state;
        if (state === 'before') { setChars(L.chars, () => [3, 0]); if (L.sub) L.sub.style.opacity = 0; return; }
        if (state === 'after') { setChars(L.chars, () => [-1.5, 0]); if (L.sub) L.sub.style.opacity = 0; return; }
        const tin = t / 0.45, tout = last ? 0 : (t - 0.72) / 0.28;
        setChars(L.chars, (f) => {
          const pin = easeOut(clamp(tin * (1 + K) - K * f));
          const pout = easeIn(clamp(tout * (1 + K) - K * f));
          return [(1 - pin) * 3 - pout * 1.5, Math.min(pin, 1 - pout)];
        });
        if (L.sub) {
          const so = clamp((t - 0.4) / 0.15) * (last ? 1 : 1 - clamp((t - 0.72) / 0.12));
          L.sub.style.opacity = so;
          L.sub.style.transform = `translateY(${(1 - so) * 12}px)`;
        }
      });
    };

    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => { ticking = false; update(); });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    update();
  })();

  // ---------- GSAP scroll reveals + motion ----------
  if (window.gsap && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);

    // Lazy-loaded images (large project/portrait photos) finish loading well
    // after ScrollTrigger's initial measurement and shift page height under
    // it, so scrub-driven triggers (journey steps, CTA settle) drift out of
    // sync with what's on screen unless positions get recomputed as each
    // image actually lands.
    let refreshTimer;
    const scheduleRefresh = () => { clearTimeout(refreshTimer); refreshTimer = setTimeout(() => ScrollTrigger.refresh(), 150); };
    document.querySelectorAll('img').forEach((img) => { if (!img.complete) img.addEventListener('load', scheduleRefresh, { once: true }); });
    window.addEventListener('load', scheduleRefresh);
    // Every trigger is first measured while the gate/preloader hold the page
    // locked (html.no-scroll: height 100%, overflow hidden), so positions
    // must be recomputed the moment the real, scrollable page is revealed.
    const refreshNow = () => setTimeout(() => ScrollTrigger.refresh(), 60);
    if (window.odPreloaderDone) refreshNow();
    else window.addEventListener('preloader:done', refreshNow, { once: true });

    document.querySelectorAll('[data-reveal]').forEach((section) => {
      const kids = section.querySelectorAll(':scope > *');
      gsap.from(kids.length ? kids : section, {
        y: 36, opacity: 0, duration: 0.9, ease: 'power3.out', stagger: 0.08,
        scrollTrigger: { trigger: section, start: 'top 85%', once: true }
      });
    });

    // Headline word-reveal (no SplitText dependency: wrap words in spans on the fly)
    document.querySelectorAll('[data-split-text]').forEach((heading) => {
      const words = heading.textContent.trim().split(/\s+/);
      heading.setAttribute('aria-label', words.join(' '));
      heading.textContent = '';
      words.forEach((w, i) => {
        const outer = document.createElement('span');
        outer.className = 'word';
        outer.setAttribute('aria-hidden', 'true');
        outer.style.cssText = 'display:inline-block;overflow:hidden;vertical-align:top';
        const inner = document.createElement('span');
        inner.style.display = 'inline-block';
        inner.textContent = w;
        outer.appendChild(inner);
        heading.appendChild(outer);
        if (i < words.length - 1) heading.appendChild(document.createTextNode(' '));
      });
      gsap.from(heading.querySelectorAll('.word > span'), {
        yPercent: 110, duration: 0.9, ease: 'power4.out', stagger: 0.06, delay: 0.2
      });
    });

    // Image reveal: clip-path wipe as frames enter view (never on .work-card
    // .frame — that element relies on overflow:visible so the vinyl disk can
    // peek out past its right edge, which a clip-path would cut off).
    gsap.utils.toArray('.image-frame .frame-box, .masonry-item').forEach((box) => {
      gsap.from(box, {
        clipPath: 'inset(0 0 100% 0)', duration: 0.9, ease: 'power3.out',
        scrollTrigger: { trigger: box, start: 'top 90%', once: true }
      });
    });

    // Subtle parallax on hero/split photography
    gsap.utils.toArray('.hero-photo, .split-photo').forEach((photo) => {
      gsap.to(photo.querySelector('.frame-box img'), {
        yPercent: 8, ease: 'none',
        scrollTrigger: { trigger: photo, start: 'top bottom', end: 'bottom top', scrub: true }
      });
    });

    gsap.utils.toArray('.work-card').forEach((card) => {
      const disk = card.querySelector('.disk');
      card.addEventListener('mouseenter', () => gsap.to(disk, { rotation: '+=45', duration: 0.6, ease: 'power2.out' }));
    });

    document.querySelectorAll('.btn').forEach((btn) => {
      btn.addEventListener('mousemove', (e) => {
        const r = btn.getBoundingClientRect();
        gsap.to(btn, { x: (e.clientX - r.left - r.width / 2) * 0.25, y: (e.clientY - r.top - r.height / 2) * 0.4, duration: 0.3, ease: 'power2.out' });
      });
      btn.addEventListener('mouseleave', () => gsap.to(btn, { x: 0, y: 0, duration: 0.4, ease: 'power3.out' }));
    });

    // Marquee "drag": the bands are tied to the scroll position itself —
    // scroll down and the paper band slides left / ink band right, scroll
    // back up and they slide back — always trailing a little behind the
    // scroll (eased) and leaning into the movement with a slight skew, so it
    // feels physically dragged. A slow idle drift keeps it alive at rest.
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.querySelectorAll('.marquee').forEach((mq) => {
        const bands = [...mq.querySelectorAll('.mq-track')].map((t, i) => ({ t, sign: i ? 1 : -1, half: 0 }));
        if (!bands.length) return;
        mq.classList.add('is-driven');
        const measure = () => bands.forEach((b) => { b.half = b.t.scrollWidth / 2; });
        measure();
        document.fonts?.ready.then(measure);
        window.addEventListener('resize', measure);
        const RATIO = 0.85;   // px of marquee travel per px scrolled
        const DRIFT = 22;     // px per second at rest
        let drift = 0, current = null;
        const wrap = (x, half) => -(((x % half) + half) % half);
        gsap.ticker.add((time, dt) => {
          drift += DRIFT * Math.min(dt, 64) / 1000;
          const target = window.scrollY * RATIO + drift;
          const r = mq.getBoundingClientRect();
          const onScreen = r.bottom > -50 && r.top < window.innerHeight + 50;
          if (current === null || !onScreen) { current = target; return; }
          // Frame-rate independent easing toward the target = the "drag".
          current += (target - current) * (1 - Math.pow(0.9, Math.min(dt, 64) / 16.7));
          const lag = target - current;
          const skew = Math.max(-9, Math.min(9, lag * 0.05));
          bands.forEach((b) => {
            if (!b.half) return;
            const x = wrap(b.sign < 0 ? current : -current, b.half);
            b.t.style.transform = `translate3d(${x}px,0,0) skewX(${b.sign * -skew}deg)`;
          });
        });
      });
    }

    // Header drops in once the preloader has cleared (or straight away when
    // it's skipped), logo first, then links and controls.
    const navItems = document.querySelectorAll('.nav-logo, .nav ul li, .nav .theme-toggle, .nav .lang-switcher, .menu-btn');
    gsap.set(navItems, { y: -24, opacity: 0 });
    const showNav = () => {
      gsap.to(navItems, { y: 0, opacity: 1, duration: .6, ease: 'power3.out', stagger: .05, clearProps: 'transform,opacity' });
      // Safety net: the header must never stay hidden if the tween stalls
      // (rAF is paused in background tabs). gsap.set applies instantly.
      setTimeout(() => gsap.set(navItems, { clearProps: 'transform,opacity' }), 1600);
    };
    if (window.odPreloaderDone) showNav();
    else window.addEventListener('preloader:done', showNav, { once: true });

    // Page fade-in on load
    gsap.from('.wrap', { opacity: 0, duration: 0.6, ease: 'power1.out' });

    // CTA band heading: settles from a slight tilt/oversize into place as it
    // scrolls into view — same "what's next" idea, in the site's own type.
    gsap.utils.toArray('.cta-rotate').forEach((el) => {
      gsap.from(el, {
        rotate: -4, scale: 1.08, opacity: 0, y: 24, duration: .9, ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 85%', once: true }
      });
    });
  }

  // ---------- Three.js grain shader (progressive enhancement, never blocks the page) ----------
  // Desktop only: on phones a full-screen shader redrawing every frame fights
  // scrolling for the GPU, and the static CSS grain (body:before) already
  // gives the same texture there.
  const isTouchOrSmall = window.matchMedia('(hover: none), (max-width: 767px)').matches;
  const initGrain = () => { try {
    if (window.THREE) {
      const canvas = document.createElement('canvas');
      canvas.id = 'grain-canvas';
      document.body.prepend(canvas);
      const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, premultipliedAlpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
      const scene = new THREE.Scene();
      const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
      const material = new THREE.ShaderMaterial({
        uniforms: { u_time: { value: 0 }, u_res: { value: new THREE.Vector2() } },
        vertexShader: 'void main(){gl_Position=vec4(position,1.0);}',
        fragmentShader: `
          precision mediump float;
          uniform float u_time;
          uniform vec2 u_res;
          float rand(vec2 co){return fract(sin(dot(co.xy,vec2(12.9898,78.233)))*43758.5453);}
          void main(){
            vec2 uv=gl_FragCoord.xy/u_res.xy;
            float n=rand(uv*u_res.xy*0.6+u_time*60.0);
            gl_FragColor=vec4(vec3(n),0.06);
          }`,
        transparent: true
      });
      scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));
      const resize = () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        material.uniforms.u_res.value.set(window.innerWidth, window.innerHeight);
      };
      resize();
      window.addEventListener('resize', resize);
      let raf, last = 0;
      const tick = (t) => {
        raf = requestAnimationFrame(tick);
        if (t - last < 42) return; // ~24fps reads as film grain and frees the GPU for scrolling
        last = t;
        material.uniforms.u_time.value = t * 0.001;
        renderer.render(scene, camera);
      };
      raf = requestAnimationFrame(tick);
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) cancelAnimationFrame(raf); else raf = requestAnimationFrame(tick);
      });
    }
  } catch (e) { /* WebGL unavailable — the static grain overlay in CSS already covers this */ } };
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // One lazy loader per library, so three.js / Vue are fetched at most once
  // and only on pages (and devices) that actually use them.
  const loaded = {};
  const loadScript = (src) => loaded[src] || (loaded[src] = new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  }));
  const THREE_SRC = '/assets/js/vendor/three.min.js';
  const VUE_SRC = '/assets/js/vendor/vue.global.prod.min.js';

  if (isTouchOrSmall) {
    const g = document.createElement('div');
    g.className = 'grain-css';
    g.setAttribute('aria-hidden', 'true');
    document.body.prepend(g);
  } else if (!reducedMotion) {
    loadScript(THREE_SRC).then(initGrain).catch(() => {});
  }

  // ---------- Three.js: floating hexagon (the OD logo's shape) in the CTA band ----------
  // A slowly turning wireframe hex prism with an orbiting dust ring, drawn in
  // the current --paper colour (so it follows light/dark mode) and tilting
  // toward the pointer. three.js is only fetched once the band is near the
  // viewport, and the loop only runs while it's actually on screen.
  (() => {
    const host = document.querySelector('.cta-3d');
    if (!host || reducedMotion || !('IntersectionObserver' in window)) return;
    let started = false;
    const near = new IntersectionObserver((entries) => {
      if (!entries.some((e) => e.isIntersecting) || started) return;
      started = true;
      near.disconnect();
      loadScript(THREE_SRC).then(() => initHex(host)).catch(() => {});
    }, { rootMargin: '400px 0px' });
    near.observe(host);

    const initHex = (el) => { try {
      const canvas = document.createElement('canvas');
      el.appendChild(canvas);
      const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: !isTouchOrSmall });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, isTouchOrSmall ? 1 : 1.5));
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
      camera.position.z = 7.2;

      const lineMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.6 });
      const dotMat = new THREE.PointsMaterial({ size: isTouchOrSmall ? 0.07 : 0.055, transparent: true, opacity: 0.85 });
      // --paper is an oklch() value, which THREE.Color can't parse; painting
      // it onto a 1px canvas converts it to plain RGB in any browser.
      const px = document.createElement('canvas').getContext('2d');
      const recolor = () => {
        px.fillStyle = '#eeeae0';
        px.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--paper').trim() || '#eeeae0';
        px.clearRect(0, 0, 1, 1);
        px.fillRect(0, 0, 1, 1);
        const [r, g, b] = px.getImageData(0, 0, 1, 1).data;
        lineMat.color.setRGB(r / 255, g / 255, b / 255);
        dotMat.color.setRGB(r / 255, g / 255, b / 255);
      };
      recolor();
      new MutationObserver(recolor).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

      const group = new THREE.Group();
      // Hexagonal prism, pointy-top like the logo, as clean edges only.
      const hex = new THREE.CylinderGeometry(1.6, 1.6, 1.1, 6, 1);
      group.add(new THREE.LineSegments(new THREE.EdgesGeometry(hex), lineMat));
      const inner = new THREE.CylinderGeometry(0.95, 0.95, 1.1, 6, 1);
      group.add(new THREE.LineSegments(new THREE.EdgesGeometry(inner), lineMat));
      group.rotation.x = Math.PI / 2;
      scene.add(group);

      const N = isTouchOrSmall ? 220 : 420;
      const pos = new Float32Array(N * 3);
      for (let i = 0; i < N; i++) {
        const a = (i / N) * Math.PI * 2 * 7.3, r = 2.6 + ((i * 73) % 100) / 100 * 1.6;
        pos[i * 3] = Math.cos(a) * r;
        pos[i * 3 + 1] = (((i * 37) % 100) / 100 - 0.5) * 0.8;
        pos[i * 3 + 2] = Math.sin(a) * r;
      }
      const dustGeo = new THREE.BufferGeometry();
      dustGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      const dust = new THREE.Points(dustGeo, dotMat);
      dust.rotation.x = 0.35;
      scene.add(dust);

      const size = () => {
        const w = el.clientWidth, h = el.clientHeight;
        if (!w || !h) return;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      };
      size();
      window.addEventListener('resize', size);

      let tx = 0, ty = 0;
      window.addEventListener('pointermove', (e) => {
        tx = (e.clientX / window.innerWidth - 0.5) * 0.6;
        ty = (e.clientY / window.innerHeight - 0.5) * 0.4;
      }, { passive: true });

      let visible = false, raf = 0, last = 0;
      const frameGap = isTouchOrSmall ? 33 : 16;
      const tick = (t) => {
        raf = requestAnimationFrame(tick);
        if (t - last < frameGap) return;
        last = t;
        const s = t * 0.001;
        group.rotation.z = s * 0.35;
        group.rotation.x = Math.PI / 2 + Math.sin(s * 0.6) * 0.25 + ty;
        group.rotation.y += (tx - group.rotation.y) * 0.05;
        dust.rotation.y = -s * 0.12;
        renderer.render(scene, camera);
      };
      const run = () => { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(tick); };
      const stop = () => { cancelAnimationFrame(raf); raf = 0; };
      new IntersectionObserver((entries) => {
        visible = entries.some((e) => e.isIntersecting);
        visible ? run() : stop();
      }).observe(el);
      document.addEventListener('visibilitychange', () => (document.hidden ? stop() : run()));
      renderer.render(scene, camera);
      if (window.gsap) gsap.from(canvas, { opacity: 0, scale: .8, duration: 1.2, ease: 'power3.out' });
    } catch (e) { el.remove(); } };
  })();

  // ---------- Vue: works page category filter ----------
  // The project cards stay server-rendered (so they're crawlable and work
  // without JS); Vue owns only the filter state and the chip bar, and shows /
  // hides cards by their data-cat. Projects can sit in several groups.
  (() => {
    const mount = document.getElementById('works-filter');
    const grid = document.getElementById('works-grid');
    if (!mount || !grid) return;
    const cards = [...grid.querySelectorAll('.work-card')];
    const T = (k, f) => (window.odT ? window.odT(k, f) : f);
    const GROUPS = [
      { id: 'all', label: T('filter_all', 'All'), test: () => true },
      { id: 'web', label: T('filter_web', 'Web'), test: (c) => /\bweb|wordpress/i.test(c) },
      { id: 'shop', label: T('filter_shop', 'E-commerce'), test: (c) => /e-commerce|shopify|marketplace/i.test(c) },
      { id: 'brand', label: T('filter_brand', 'Branding'), test: (c) => /brand/i.test(c) },
      { id: 'product', label: T('filter_product', 'Plugins & Products'), test: (c) => /plugin|product|platform|digital|saas|\bai\b/i.test(c) }
    ];

    loadScript(VUE_SRC).then(() => {
      const { createApp, ref, computed, watch, nextTick } = window.Vue;
      createApp({
        setup() {
          const active = ref('all');
          const groups = computed(() => GROUPS.map((g) => ({ ...g, count: cards.filter((c) => g.test(c.dataset.cat || '')).length })).filter((g) => g.count));
          watch(active, (id) => {
            const g = GROUPS.find((x) => x.id === id) || GROUPS[0];
            const shown = [];
            cards.forEach((c) => { const on = g.test(c.dataset.cat || ''); c.hidden = !on; if (on) shown.push(c); });
            nextTick(() => {
              if (window.gsap) gsap.fromTo(shown, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: .55, ease: 'power3.out', stagger: .05, overwrite: true });
              if (window.ScrollTrigger) ScrollTrigger.refresh();
            });
          });
          return { active, groups };
        },
        template: `<button v-for="g in groups" :key="g.id" type="button" class="filter-chip" :class="{ 'is-active': active === g.id }" :aria-pressed="active === g.id ? 'true' : 'false'" @click="active = g.id">{{ g.label }}<sup>{{ g.count }}</sup></button>`
      }).mount(mount);
      if (window.gsap) gsap.from(mount.children, { opacity: 0, y: 14, duration: .5, ease: 'power2.out', stagger: .05 });
    }).catch(() => {});
  })();
})();
