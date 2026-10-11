// Developed by AMIR AMMARZAD
(function () {
  // سایه هدر هنگام اسکرول + دکمه بازگشت به بالا
  const header = document.querySelector('header');
  const toTop = document.querySelector('.totop');
  const onScroll = () => {
    const y = window.scrollY;
    header && header.classList.toggle('scrolled', y > 8);
    toTop && toTop.classList.toggle('show', y > 600);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ظاهر شدن نرم بخش‌ها هنگام اسکرول
  const items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { threshold: 0.08 });
    items.forEach(el => io.observe(el));
  } else {
    items.forEach(el => el.classList.add('in'));
  }

  // پیام‌های موفقیت بعد از چند ثانیه محو می‌شوند
  document.querySelectorAll('.msg.success,.msg.info').forEach(m => {
    setTimeout(() => { m.style.transition = 'opacity .5s'; m.style.opacity = '0'; setTimeout(() => m.remove(), 500); }, 4500);
  });

  // به‌روزرسانی زنده هزینه ارسال و مبلغ نهایی در صفحه پرداخت (مبلغ نهایی را سرور دوباره محاسبه می‌کند)
  const sum = document.getElementById('order-sum');
  if (sum) {
    const fa = n => Number(n).toLocaleString('fa-IR');
    const base = Number(sum.dataset.base);
    document.querySelectorAll('input[name="shipping_method"]').forEach(r => {
      r.addEventListener('change', () => {
        const cost = Number(r.dataset.cost);
        document.getElementById('sum-ship').textContent = cost ? fa(cost) + ' تومان' : 'رایگان';
        document.getElementById('sum-total').textContent = fa(base + cost) + ' تومان';
      });
    });
  }
})();
