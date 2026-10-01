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
  (() => {
    const el = document.getElementById('preloader');
    if (!el) return;
    if (document.documentElement.classList.contains('no-preloader')) { el.remove(); return; }

    const finish = () => {
      el.classList.add('done');
      setTimeout(() => el.remove(), 500);
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
  })();

  // ---------- journey stepper: sticky stage ----------
  // The "first / then / today" scroll narrative: the stage stays in view
  // via native CSS position:sticky (no GSAP pin — a pin here once
  // mis-measured against this page's late-loading images and caused a
  // visible scroll jump). Which step is "current" is tracked with a bare,
  // un-attached ScrollTrigger (no tween/timeline wired into its own
  // config — that shape was computing stale start/end on this page and
  // never self-corrected on refresh); the actual motion is done with GSAP
  // tweens fired from onUpdate, so the crossfade itself is still GSAP.
  document.querySelectorAll('.journey-pin').forEach((pin) => {
    const steps = [...pin.querySelectorAll('.journey-step')];
    if (steps.length < 2) return;
    pin.classList.add('is-pinned');
    pin.style.setProperty('--steps', steps.length);
    let active = 0;
    steps[0].classList.add('is-active');

    if (window.gsap && window.ScrollTrigger) {
      // GSAP owns opacity/transform here; the CSS transition on .journey-step
      // is only for the no-GSAP fallback below, and would otherwise fight
      // GSAP's own tween of the same properties every frame.
      steps.forEach((s) => { s.style.transition = 'none'; });
      gsap.set(steps, { opacity: 0, scale: .78, y: 22 });
      gsap.set(steps[0], { opacity: 1, scale: 1, y: 0 });
      const show = (el) => gsap.to(el, { opacity: 1, scale: 1, y: 0, duration: .6, ease: 'back.out(1.6)', overwrite: 'auto' });
      const hide = (el) => gsap.to(el, { opacity: 0, scale: .78, y: -22, duration: .45, ease: 'power2.inOut', overwrite: 'auto' });
      ScrollTrigger.create({
        trigger: pin,
        start: 'top top',
        end: 'bottom bottom',
        onUpdate: (self) => {
          const idx = Math.min(steps.length - 1, Math.floor(self.progress * steps.length));
          if (idx === active) return;
          hide(steps[active]);
          show(steps[idx]);
          active = idx;
        }
      });
    } else {
      // No-GSAP fallback: plain scroll listener + CSS transitions.
      let ticking = false;
      const update = () => {
        ticking = false;
        const rect = pin.getBoundingClientRect();
        const total = rect.height - window.innerHeight;
        const progress = total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 0;
        const idx = Math.min(steps.length - 1, Math.floor(progress * steps.length));
        if (idx === active) return;
        steps[active].classList.remove('is-active');
        steps[idx].classList.add('is-active');
        active = idx;
      };
      const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
      window.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', onScroll);
      update();
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
