/* 博客前端交互：主题切换 / 目录高亮 / 代码复制 / 返回顶部 */
(function () {
  'use strict';

  // ---------------- 主题切换 ----------------
  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') || 'light';
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* 隐私模式忽略 */ }
    });
  }

  // ---------------- 目录高亮 ----------------
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

  // ---------------- 代码复制 ----------------
  document.querySelectorAll('.markdown-body pre').forEach(function (pre) {
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

  // ---------------- 返回顶部 ----------------
  var top = document.createElement('button');
  top.className = 'to-top';
  top.type = 'button';
  top.title = '返回顶部';
  top.textContent = '↑';
  top.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  document.body.appendChild(top);
  window.addEventListener('scroll', function () {
    if (window.scrollY > 400) { top.classList.add('show'); } else { top.classList.remove('show'); }
  });
})();
