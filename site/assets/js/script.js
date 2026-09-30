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
})();
