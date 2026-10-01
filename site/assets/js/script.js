(() => {
  const toggle = document.getElementById('nav-toggle');
  const menu = document.getElementById('mobile-menu');
  const close = document.getElementById('mobile-close');
  const open = () => { if (!menu) return; menu.classList.add('open'); document.body.classList.add('menu-open'); };
  const shut = () => { if (!menu) return; menu.classList.remove('open'); document.body.classList.remove('menu-open'); };
  toggle?.addEventListener('click', open);
  close?.addEventListener('click', shut);
  menu?.querySelectorAll('a').forEach(a => a.addEventListener('click', shut));

  document.querySelectorAll('.accordion-item').forEach((item) => {
    const trigger = item.querySelector('.accordion-trigger');
    trigger?.addEventListener('click', () => item.classList.toggle('open'));
  });

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
      if (window.gsap) gsap.to(gate, { opacity: 0, duration: .5, ease: 'power1.out', onComplete: () => gate.remove() });
      else { gate.style.transition = 'opacity .5s ease'; gate.style.opacity = '0'; setTimeout(() => gate.remove(), 500); }
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
      markSeen();
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
      const to = feedback.dataset.email || '';
      const reason = feedback.reason.value.trim();
      const email = feedback.email.value.trim();
      const subject = encodeURIComponent("Feedback from odgrande.github.io");
      const bodyLines = [reason, email ? `\nReply to: ${email}` : ''].join('\n');
      window.location.href = `mailto:${to}?subject=${subject}&body=${encodeURIComponent(bodyLines)}`;
      tryClose();
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
      const to = form.dataset.email || '';
      const idea = form.idea.value.trim();
      const email = form.email.value.trim();
      const subject = encodeURIComponent("An idea from odgrande.github.io");
      const bodyLines = [idea, email ? `\nReply to: ${email}` : ''].join('\n');
      window.location.href = `mailto:${to}?subject=${subject}&body=${encodeURIComponent(bodyLines)}`;
      closePopup();
    });

    const arm = () => {
      let seen;
      try { seen = sessionStorage.getItem(KEY); } catch (e) {}
      if (seen) { popup.remove(); return; }
      const onLeave = (e) => {
        if (e.clientY > 0) return;
        document.removeEventListener('mouseleave', onLeave);
        showPopup();
      };
      document.addEventListener('mouseleave', onLeave);
    };
    window.addEventListener('preloader:done', () => setTimeout(arm, 1200), { once: true });
  })();

  // ---------- lightbox ----------
  const lightbox = document.createElement('div');
  lightbox.className = 'lightbox';
  lightbox.innerHTML = '<button class="lightbox-close" aria-label="Close"><svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24"><path fill="#ffffff" d="M9 16h2V8H9v8Zm4 0h2V8h-2v8Zm-1 6q-2.075 0-3.9-.788t-3.175-2.137q-1.35-1.35-2.137-3.175T2 12q0-2.075.788-3.9t2.137-3.175q1.35-1.35 3.175-2.137T12 2q2.075 0 3.9.788t3.175 2.137q1.35 1.35 2.138 3.175T22 12q0 2.075-.788 3.9t-2.137 3.175q-1.35 1.35-3.175 2.138T12 22Zm0-2q3.35 0 5.675-2.325T20 12q0-3.35-2.325-5.675T12 4Q8.65 4 6.325 6.325T4 12q0 3.35 2.325 5.675T12 20Zm0-8Z"/></svg></button><img alt="">';
  document.body.appendChild(lightbox);
  const lbImg = lightbox.querySelector('img');
  const showLightbox = (src, alt) => { lbImg.src = src; lbImg.alt = alt || ''; lightbox.classList.add('open'); document.body.classList.add('menu-open'); };
  const hideLightbox = () => { lightbox.classList.remove('open'); document.body.classList.remove('menu-open'); lbImg.src = ''; };
  lightbox.addEventListener('click', (e) => { if (e.target === lightbox || e.target.closest('.lightbox-close')) hideLightbox(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideLightbox(); });
  document.querySelectorAll('.image-frame .frame-box img, .gallery-grid img, .masonry-item img').forEach((img) => {
    img.addEventListener('click', () => showLightbox(img.currentSrc || img.src, img.alt));
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
    if (!el) { window.dispatchEvent(new Event('preloader:done')); return; }
    if (document.documentElement.classList.contains('no-preloader')) { el.remove(); window.dispatchEvent(new Event('preloader:done')); return; }

    const start = () => {
      const frame = document.getElementById('preloader-frame');
      if (frame && !frame.getAttribute('src') && frame.dataset.src) frame.src = frame.dataset.src;

      const finish = () => {
        el.classList.add('done');
        setTimeout(() => el.remove(), 500);
        window.dispatchEvent(new Event('preloader:done'));
      };
      const failsafe = setTimeout(finish, 6000);

      let realLoadDone = false;
      Promise.race([
        Promise.all([
          document.fonts ? document.fonts.ready : Promise.resolve(),
          new Promise((r) => window.addEventListener('load', r, { once: true }))
        ]),
        new Promise((r) => setTimeout(r, 2600))
      ]).then(() => { realLoadDone = true; });

      const MIN_SHOW = 3700; // matches the loader's own RUN(3200)+HOLD(500) first-cycle beat
      const started = performance.now();
      const tryReveal = () => {
        if (realLoadDone && performance.now() - started >= MIN_SHOW) {
          clearTimeout(failsafe);
          if (window.gsap) gsap.to(el, { opacity: 0, duration: .45, ease: 'power1.out', onComplete: finish });
          else { el.style.transition = 'opacity .45s ease'; el.style.opacity = '0'; setTimeout(finish, 450); }
        } else {
          setTimeout(tryReveal, 100);
        }
      };
      tryReveal();
    };

    if (document.getElementById('gate')) window.addEventListener('gate:closed', start, { once: true });
    else start();
  })();

  // ---------- journey stepper: stacked sticky cards ----------
  // The "first / then / today" scroll narrative: each phrase is its own
  // full-height sticky card; later cards stack over earlier ones (z-index)
  // as they scroll up and "stick" at the top, so only one is ever visible
  // at a time — and scrolling back up un-stacks them in the same order for
  // free, since it's native CSS sticky behaviour, not scroll-position math.
  // (A GSAP ScrollTrigger pin/scrub drove the earlier version and kept
  // mis-measuring against this page's late-loading images; this sidesteps
  // that class of bug entirely. GSAP still does the actual motion: each
  // card's own text fades/scales in the first time it's reached.)
  document.querySelectorAll('.journey-pin').forEach((pin) => {
    const steps = [...pin.querySelectorAll('.journey-step')];
    if (steps.length < 2) return;
    pin.classList.add('is-pinned');
    steps.forEach((s, i) => { s.style.zIndex = i + 1; });

    if (window.gsap && window.ScrollTrigger) {
      steps.forEach((step) => {
        gsap.from(step.children, {
          opacity: 0, scale: .82, y: 30, duration: .7, ease: 'back.out(1.6)', stagger: .08,
          scrollTrigger: { trigger: step, start: 'top top', once: true }
        });
      });
    }
  });

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
      heading.innerHTML = words.map(w => `<span class="word" style="display:inline-block;overflow:hidden;vertical-align:top"><span style="display:inline-block">${w}</span></span>`).join(' ');
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
  try {
    if (window.THREE && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
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
      let raf;
      const tick = (t) => { material.uniforms.u_time.value = t * 0.001; renderer.render(scene, camera); raf = requestAnimationFrame(tick); };
      raf = requestAnimationFrame(tick);
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) cancelAnimationFrame(raf); else raf = requestAnimationFrame(tick);
      });
    }
  } catch (e) { /* WebGL unavailable — the static grain overlay in CSS already covers this */ }
})();
