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

  // ---------- preloader: a small cinematic scene, not a spinner ----------
  // Sequence: site loads underneath -> the cover + character are visible
  // and idling immediately -> percentage counts up (blended with real
  // document.fonts/window-load signals) while the character idles -> once
  // loading completes, the character (or, on small/no-WebGL screens, a CSS
  // stand-in) leans into the full-bleed cover and physically pushes it off
  // screen -> name + bio (sitting underneath the cover the whole time) are
  // revealed -> preloader removes itself.
  (() => {
    const el = document.getElementById('preloader');
    if (!el) return;
    if (document.documentElement.classList.contains('no-preloader')) { el.remove(); return; }

    const countEl = document.getElementById('preloader-count');
    const canvas = document.getElementById('preloader-canvas');
    const fallback = document.querySelector('.preloader-fallback');

    const finish = () => {
      el.classList.add('done');
      try { sessionStorage.setItem('odIntroSeen', '1'); } catch (e) {}
      setTimeout(() => el.remove(), 500);
    };
    // Failsafe: never let the intro outlive ~6.5s even if a signal above never fires.
    const failsafe = setTimeout(finish, 6500);

    if (!window.gsap) { setTimeout(finish, 300); return; }

    const smallScreen = window.innerWidth < 760;
    let hasWebGL = false;
    try {
      const t = document.createElement('canvas');
      hasWebGL = !!window.THREE && !!(t.getContext('webgl') || t.getContext('experimental-webgl'));
    } catch (e) { hasWebGL = false; }
    const useWebGL = hasWebGL && !smallScreen;

    // ---- percentage: animate to ~92%, then hold for the real load signal, then snap to 100 ----
    let realLoadDone = false;
    Promise.race([
      Promise.all([
        document.fonts ? document.fonts.ready : Promise.resolve(),
        new Promise((r) => window.addEventListener('load', r, { once: true }))
      ]),
      new Promise((r) => setTimeout(r, 2600))
    ]).then(() => { realLoadDone = true; });

    const pct = { v: 0 };
    const setPct = () => { if (countEl) countEl.textContent = String(Math.floor(pct.v)); };
    gsap.to(pct, {
      v: 92, duration: 1.3, ease: 'power2.out', onUpdate: setPct,
      onComplete: function tick() {
        if (realLoadDone) {
          gsap.to(pct, { v: 100, duration: .3, ease: 'power1.out', onUpdate: setPct, onComplete: () => scene.push() });
        } else {
          setTimeout(tick, 70);
        }
      }
    });

    // `scene` exposes idle() (called once, immediately) and push() (called once loading hits 100%).
    const scene = useWebGL ? buildWebGLScene() : buildFallbackScene();
    scene.idle();

    function buildFallbackScene() {
      fallback.classList.add('active');
      const cover = fallback.querySelector('.preloader-fallback-cover');
      const armL = fallback.querySelector('.pfc-arm-l');
      const armR = fallback.querySelector('.pfc-arm-r');
      const body = fallback.querySelector('.pfc-body');
      let idleTl;
      return {
        idle() {
          idleTl = gsap.timeline({ repeat: -1, yoyo: true })
            .to(body, { y: -4, duration: .9, ease: 'sine.inOut' })
            .to([armL, armR], { rotation: 6, duration: .9, ease: 'sine.inOut' }, '<');
        },
        push() {
          clearTimeout(failsafe);
          idleTl.kill();
          gsap.timeline({ onComplete: finish })
            .to([armL, armR], { rotation: -30, duration: .22, ease: 'power2.out' })
            .to(body, { scaleY: .93, y: 5, duration: .18, ease: 'power1.inOut' }, '<')
            .to([armL, armR], { rotation: 8, duration: .28, ease: 'power3.out' })
            .to(body, { scaleY: 1.04, y: -3, duration: .28, ease: 'power2.out' }, '<')
            .to(cover, { x: '112%', duration: .75, ease: 'power3.inOut' }, '-=.08')
            .to(el, { opacity: 0, duration: .35 }, '+=.1');
        }
      };
    }

    function buildWebGLScene() {
      canvas.style.display = 'block';
      let renderer;
      try {
        renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, premultipliedAlpha: false });
      } catch (e) { return buildFallbackScene(); }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);
      renderer.setClearAlpha(0);

      const sceneObj = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
      camera.position.z = 6;

      sceneObj.add(new THREE.AmbientLight(0xffffff, .8));
      const dLight = new THREE.DirectionalLight(0xffffff, .9);
      dLight.position.set(2, 3, 4);
      sceneObj.add(dLight);
      const fillLight = new THREE.DirectionalLight(0x8899ff, .3);
      fillLight.position.set(-3, -1, 2);
      sceneObj.add(fillLight);

      const frustum = () => {
        const h = 2 * Math.tan((camera.fov * Math.PI / 180) / 2) * camera.position.z;
        return { w: h * camera.aspect, h };
      };

      const coverMat = new THREE.MeshBasicMaterial({ color: 0x151311 });
      const cover = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), coverMat);
      sceneObj.add(cover);

      // ---- character: simple, rounded, editorial mascot built from primitives ----
      const bodyColor = 0xeeeade, accent = 0xe6b83f;
      const char = new THREE.Group();
      const torsoMat = new THREE.MeshStandardMaterial({ color: bodyColor, roughness: .7 });
      const torso = new THREE.Mesh(new THREE.SphereGeometry(.5, 24, 24), torsoMat);
      torso.scale.set(.85, 1.25, .75);
      char.add(torso);
      const head = new THREE.Mesh(new THREE.SphereGeometry(.32, 24, 24), torsoMat);
      head.position.y = .95;
      char.add(head);
      const beltMat = new THREE.MeshStandardMaterial({ color: accent, roughness: .6 });
      const belt = new THREE.Mesh(new THREE.TorusGeometry(.42, .06, 8, 24), beltMat);
      belt.rotation.x = Math.PI / 2;
      belt.position.y = -.1;
      char.add(belt);

      const makeArm = (side) => {
        const pivot = new THREE.Group();
        pivot.position.set(.5 * side, .45, .1);
        const arm = new THREE.Mesh(new THREE.CylinderGeometry(.09, .1, .75, 8), torsoMat);
        arm.position.y = -.37;
        pivot.add(arm);
        const hand = new THREE.Mesh(new THREE.SphereGeometry(.12, 12, 12), torsoMat);
        hand.position.y = -.75;
        pivot.add(hand);
        pivot.rotation.x = -.85;
        pivot.rotation.z = .15 * side;
        char.add(pivot);
        return pivot;
      };
      const armL = makeArm(-1), armR = makeArm(1);

      const makeLeg = (side) => {
        const leg = new THREE.Mesh(new THREE.CylinderGeometry(.12, .1, .6, 8), torsoMat);
        leg.position.set(.22 * side, -.85, 0);
        char.add(leg);
      };
      makeLeg(-1); makeLeg(1);

      sceneObj.add(char);

      const layout = () => {
        const { w, h } = frustum();
        cover.geometry.dispose();
        cover.geometry = new THREE.PlaneGeometry(w, h);
        const s = h * .19;
        char.scale.setScalar(s);
        char.position.set(-w * .24, -h * .05, .8);
        renderer.setSize(window.innerWidth, window.innerHeight);
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        return { w, h };
      };
      let { w: viewW } = layout();
      const onResize = () => { viewW = layout().w; };
      window.addEventListener('resize', onResize);

      const baseY = char.position.y, baseX = char.position.x;

      let raf;
      const tick = () => { renderer.render(sceneObj, camera); raf = requestAnimationFrame(tick); };
      tick();

      const cleanup = () => {
        cancelAnimationFrame(raf);
        window.removeEventListener('resize', onResize);
        renderer.dispose();
        finish();
      };

      let idleTl;
      return {
        idle() {
          // character is already standing in frame, gently breathing/swaying while loading continues
          idleTl = gsap.timeline({ repeat: -1, yoyo: true })
            .to(char.position, { y: baseY + .05, duration: 1.1, ease: 'sine.inOut' })
            .to(char.rotation, { z: .03, duration: 1.4, ease: 'sine.inOut' }, '<')
            .to([armL.rotation, armR.rotation], { x: '+=0.05', duration: 1.1, ease: 'sine.inOut' }, '<');
        },
        push() {
          clearTimeout(failsafe);
          idleTl.kill();
          char.position.y = baseY;
          gsap.timeline({ onComplete: cleanup })
            // anticipation: crouch + arms rise toward the cover
            .to(char.scale, { y: char.scale.y * .92, duration: .22, ease: 'power1.inOut' })
            .to(char.rotation, { y: -.15, duration: .25, ease: 'power1.out' }, '<')
            .to([armL.rotation, armR.rotation], { x: -.35, duration: .3, ease: 'power2.out' }, '-=.1')
            // the push: character extends, cover shoots away with a little resistance-then-release
            .to(char.scale, { y: char.scale.y * 1.08, duration: .3, ease: 'power2.out' })
            .to(char.position, { x: baseX + viewW * .08, duration: .5, ease: 'power2.out' }, '<')
            .to(cover.position, { x: viewW * .18, duration: .18, ease: 'power1.in' }, '<')
            .to(cover.position, { x: viewW * 1.3, duration: .7, ease: 'power3.in' })
            .to([armL.rotation, armR.rotation], { x: .3, duration: .4, ease: 'power1.out' }, '-=.55')
            // settle + fade the whole overlay once the cover has cleared
            .to(char.position, { y: baseY - .08, duration: .25, ease: 'power1.inOut' })
            .to(el, { opacity: 0, duration: .4 }, '+=.2');
        }
      };
    }
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
