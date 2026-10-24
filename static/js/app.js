/* 博客前端交互：滚动揭示 / 阅读进度 /
   主题切换(View Transitions) / 目录高亮 / 代码复制 / 返回顶部 / 导航滚动态 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* -------------------------------------------------- 滚动揭示 --- */
  var revealTargets = document.querySelectorAll(
    '.page-head, .post-card, .hot-card, .cat-card, .year-block, .card, .collapse-card, .about-page > *, .search-page'
  );
  if (revealTargets.length && 'IntersectionObserver' in window && !reduceMotion) {
    var seen = new Map();
    Array.prototype.forEach.call(revealTargets, function (el) {
      var p = el.parentElement;
      var i = seen.get(p) || 0;
      seen.set(p, i + 1);
      el.setAttribute('data-reveal', '');
      el.style.setProperty('--reveal-i', i);
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('is-visible');
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.04 });
    revealTargets.forEach(function (el) { io.observe(el); });
  }

  /* -------------------------------------------------- 阅读进度条 --- */
  var article = document.querySelector('.post-article');
  if (article) {
    var bar = document.createElement('div');
    bar.className = 'reading-progress';
    document.body.appendChild(bar);
    var onScrollP = function () {
      var start = article.offsetTop;
      var h = article.offsetHeight - window.innerHeight;
      var scrolled = window.scrollY - start;
      var p = Math.min(1, Math.max(0, scrolled / (h || 1)));
      bar.style.width = (p * 100) + '%';
    };
    window.addEventListener('scroll', onScrollP, { passive: true });
    onScrollP();
  }

  /* -------------------------------------------------- 主题切换 --- */
  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function (e) {
      var cur = document.documentElement.getAttribute('data-theme') || 'light';
      var next = cur === 'dark' ? 'light' : 'dark';
      var apply = function () {
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem('theme', next); } catch (_) { /* 隐私模式忽略 */ }
      };
      if (document.startViewTransition) {
        var r = toggle.getBoundingClientRect();
        document.documentElement.style.setProperty('--tx', (r.left + r.width / 2) + 'px');
        document.documentElement.style.setProperty('--ty', (r.top + r.height / 2) + 'px');
        document.documentElement.classList.add('theme-anim');
        document.startViewTransition(apply);
      } else {
        apply();
      }
    });
  }

  /* -------------------------------------------------- 导航滚动态 --- */
  var header = document.querySelector('.site-header');
  if (header) {
    var onScrollH = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScrollH, { passive: true });
    onScrollH();
  }

  /* -------------------------------------------------- 目录高亮 --- */
  var toc = document.getElementById('toc');
  if (toc) {
    var links = Array.prototype.slice.call(toc.querySelectorAll('.toc-item a'));
    var map = {};
    var targets = [];
    links.forEach(function (a) {
      var id = decodeURIComponent(a.getAttribute('href').slice(1));
      var el = document.getElementById(id);
      if (el) { map[id] = a.parentNode; targets.push(el); }
    });
    if (targets.length && 'IntersectionObserver' in window) {
      var visible = {};
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { visible[en.target.id] = en.isIntersecting; });
        var current = null;
        for (var i = 0; i < targets.length; i++) {
          if (visible[targets[i].id]) { current = targets[i].id; break; }
        }
        links.forEach(function (a) { a.parentNode.classList.remove('is-active'); });
        if (current && map[current]) map[current].classList.add('is-active');
      }, { rootMargin: '-80px 0px -70% 0px' });
      targets.forEach(function (t) { observer.observe(t); });
    }
  }

  /* -------------------------------------------------- 代码复制 --- */
  document.querySelectorAll('.post-body pre, .markdown-body pre').forEach(function (pre) {
    if (pre.querySelector('.copy-btn')) return;
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = '复制';
    btn.addEventListener('click', function () {
      var code = pre.querySelector('code');
      var text = code ? code.innerText : pre.innerText;
      var done = function () {
        btn.textContent = '已复制';
        setTimeout(function () { btn.textContent = '复制'; }, 1500);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done).catch(function () { btn.textContent = '失败'; });
      } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); done(); } catch (e) { btn.textContent = '失败'; }
        document.body.removeChild(ta);
      }
    });
    pre.appendChild(btn);
  });

  /* -------------------------------------------------- 返回顶部 --- */
  var top = document.createElement('button');
  top.className = 'to-top';
  top.type = 'button';
  top.title = '返回顶部';
  top.textContent = '↑';
  top.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });
  document.body.appendChild(top);
  window.addEventListener('scroll', function () {
    if (window.scrollY > 400) { top.classList.add('show'); } else { top.classList.remove('show'); }
  });
})();
