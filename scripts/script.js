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
  document.querySelectorAll('.image-frame .frame-box img, .gallery-grid img, .masonry-item img, .credential-card img').forEach((img) => {
    img.addEventListener('click', () => showLightbox(img.currentSrc || img.src, img.alt));
  });

  // ---------- preloader ----------
  (() => {
    const el = document.getElementById('preloader');
    if (!el || document.documentElement.classList.contains('no-preloader')) { el?.remove(); return; }
    const countEl = document.getElementById('preloader-count');
    const finish = () => {
      el.classList.add('done');
      try { sessionStorage.setItem('odIntroSeen', '1'); } catch (e) {}
      setTimeout(() => el.remove(), 900);
    };
    // Failsafe: never let a preloader outlive ~4.5s even if something above stalls.
    const failsafe = setTimeout(finish, 4500);
    let pct = 1;
    const tick = () => {
      pct = Math.min(100, pct + Math.ceil((100 - pct) / 10) + 1);
      if (countEl) countEl.textContent = String(pct);
      if (pct >= 100) {
        clearTimeout(failsafe);
        el.classList.add('reveal');
        if (window.gsap) {
          gsap.to(el.querySelector('.preloader-panel'), { yPercent: -100, duration: .7, ease: 'power3.inOut', delay: .15 });
          gsap.to(el.querySelector('.preloader-inner'), { opacity: 0, duration: .3 });
          gsap.to(el.querySelector('.preloader-reveal'), { opacity: 1, duration: .4, delay: .1 });
          gsap.to(el, { opacity: 0, duration: .5, delay: 1.3, onComplete: finish });
        } else {
          el.style.transition = 'opacity .5s ease';
          setTimeout(() => { el.style.opacity = '0'; setTimeout(finish, 500); }, 900);
        }
        return;
      }
      setTimeout(tick, 45 + Math.random() * 40);
    };
    if (document.getElementById('preloader-count')) {
      document.querySelector('.preloader-reveal').style.opacity = '0';
      tick();
    } else finish();
  })();

  // ---------- GSAP scroll reveals + motion ----------
  if (window.gsap && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);

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
