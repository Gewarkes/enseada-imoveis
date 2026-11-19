(function () {
  'use strict';
  var S = window.SITE || {}, T = S.t || {};
  var $ = function (q, r) { return (r || document).querySelector(q); }, $$ = function (q, r) { return Array.prototype.slice.call((r || document).querySelectorAll(q)); };
  var nf = function (n, d) { return Number(n).toLocaleString(S.lang === 'en' ? 'en-US' : (S.lang === 'es' ? 'es-AR' : (S.lang === 'de' ? 'de-DE' : 'pt-BR')), { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); };
  /* ---------- Rechner und Checklisten der Guide-Seiten ---------- */
  var num = function (v) { v = String(v || '').replace(/[^\d,.-]/g, ''); if (/,\d{1,2}$/.test(v)) v = v.replace(/\./g, '').replace(',', '.'); else v = v.replace(/[.,]/g, ''); return parseFloat(v) || 0; };
  var rs = function (v) { return 'R$ ' + nf(Math.round(v)); };
  var TX = S.taxes || {};
  $$('[data-w=buycosts]').forEach(function (w) {
    var g = function (k) { return $('[data-i=' + k + ']', w); }, o = function (k, v) { $('[data-o=' + k + ']', w).textContent = v; };
    function run() {
      var p = num(g('price').value), itiv = p * num(g('itiv').value) / 100, lo = p * ((TX.iof || {}).min || 0) / 100, hi = p * ((TX.iof || {}).max || 0.38) / 100;
      var tr = num(g('docs').value) * (TX.docPrice || 129), reg = num(g('reg').value), law = num(g('law').value);
      var nt = TX.notar || {}, nok = p === nt.example_price;
      o('itiv', rs(itiv)); o('iof', rs(lo) + ' – ' + rs(hi)); o('tr', rs(tr));
      o('not', nok ? rs(nt.value) + ' (' + T.cbNotEx + ')' : T.cbNotOpen);
      var base = itiv + tr + reg + law + (nok ? nt.value : 0);
      o('total', rs(base + lo) + ' – ' + rs(base + hi));
    }
    $$('input', w).forEach(function (i) { i.addEventListener('input', run); }); run();
  });
  $$('[data-w=gains]').forEach(function (w) {
    var g = function (k) { return $('[data-i=' + k + ']', w); }, o = function (k, v) { $('[data-o=' + k + ']', w).textContent = v; };
    function run() {
      var gain = Math.max(0, num(g('sale').value) - num(g('buy').value)), tax = 0, G = (TX.gains || {});
      if (g('who').value === 'non') tax = gain * (G.nonresident || 0.15);
      else { var prev = 0; (G.resident || []).forEach(function (b) { var top = b[0] === null ? Infinity : b[0]; if (gain > prev) tax += (Math.min(gain, top) - prev) * b[1]; prev = top; }); }
      o('gain', rs(gain)); o('tax', rs(tax)); o('net', rs(num(g('sale').value) - tax));
    }
    $$('input,select', w).forEach(function (i) { i.addEventListener('input', run); i.addEventListener('change', run); }); run();
  });
  $$('[data-chk]').forEach(function (box) {
    var boxes = $$('input[type=checkbox]', box), n = $('[data-chk-n]', box);
    var cnt = function () { n.textContent = boxes.filter(function (x) { return x.checked; }).length; }; boxes.forEach(function (b) { b.addEventListener('change', cnt); }); cnt(); addEventListener('pageshow', cnt);
    $('[data-chk-wa]', box).addEventListener('click', function () {
      var l = [box.dataset.title, ''];
      boxes.forEach(function (b) { l.push((b.checked ? '[x] ' : '[ ] ') + b.nextElementSibling.textContent); });
      window.open('https://wa.me/' + S.wa + '?text=' + encodeURIComponent(l.join('\n')), '_blank', 'noopener');
    });
  });

  /* ---------- gemeinsame Helfer ---------- */
  var V = S.v || {};
  var waLink = function (txt) { return 'https://wa.me/' + S.wa + '?text=' + encodeURIComponent(txt); };
  var LOCALE = { pt: 'pt-BR', en: 'en', es: 'es', de: 'de' }[S.lang] || 'pt-BR';
  var countries = function () {
    var dn = null; try { dn = new Intl.DisplayNames([LOCALE], { type: 'region' }); } catch (e) {}
    var top = ['AR', 'BR', 'US', 'DE', 'UY', 'CL', 'PT', 'ES', 'IT', 'FR', 'GB', 'CH'], all = (S.cc || []);
    var nm = function (c) { return dn ? (dn.of(c) || c) : c; };
    var rest = all.filter(function (c) { return top.indexOf(c) < 0; }).map(function (c) { return [c, nm(c)]; }).sort(function (a, b) { return a[1].localeCompare(b[1], LOCALE); });
    return top.filter(function (c) { return all.indexOf(c) > -1; }).map(function (c) { return [c, nm(c)]; }).concat(rest);
  };
  var fillCountries = function (sel) { countries().forEach(function (c) { var o = document.createElement('option'); o.value = c[0]; o.textContent = c[1]; sel.appendChild(o); }); };

  /* ---------- Wunsch-Knopf ---------- */
  $$('[data-wish]').forEach(function (w) {
    var st = { deal: 'buy', where: '', price: '', beds: '' }, from = $('[data-wish-from]', w);
    if (from) fillCountries(from);
    var upd = function () {
      $$('[data-wp]', w).forEach(function (g) { g.hidden = g.dataset.wp !== st.deal; });
      var lines = [V.wMsg, '', V.wMsgDeal + ': ' + (st.deal === 'buy' ? V.wBuy : V.wRent)];
      if (st.where) lines.push(V.wMsgWhere + ': ' + st.where);
      if (st.price) lines.push(V.wMsgPrice + ': R$ ' + nf(st.price));
      if (st.beds) lines.push(V.wMsgBeds + ': ' + st.beds + '+');
      if (from && from.value) lines.push(V.wMsgFrom + ': ' + from.options[from.selectedIndex].textContent);
      lines.push('', V.wMsgEnd);
      $('[data-wish-wa]', w).href = waLink(lines.join('\n'));
    };
    $$('[data-wg]', w).forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.wg; if (k === 'price' && b.getAttribute('aria-pressed') === 'true' && false) return;
        $$('[data-wg="' + k + '"]', w).forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        st[k] = b.dataset.v; if (k === 'deal') { st.price = ''; $$('[data-wg=price]', w).forEach(function (x) { x.setAttribute('aria-pressed', 'false'); }); } upd();
      });
    });
    $$('select[data-wg]', w).forEach(function (sel) {
      sel.addEventListener('change', function () {
        var k = sel.dataset.wg; st[k] = sel.value;
        if (k === 'deal') { st.price = ''; $$('select[data-wg=price]', w).forEach(function (x) { x.value = ''; }); }
        upd();
      });
    });
    if (from) from.addEventListener('change', upd);
    upd();
  });

  /* ---------- Länderauswahl ---------- */
  var UF = ['Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Distrito Federal', 'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul', 'Minas Gerais', 'Pará', 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 'Roraima', 'Santa Catarina', 'São Paulo', 'Sergipe', 'Tocantins'];
  $$('[data-cp]').forEach(function (cp) {
    var sel = $('[data-cp-sel]', cp), br = $('[data-cp-br]', cp), stt = $('[data-cp-state]', cp), city = $('[data-cp-city]', cp), out = $('[data-cp-out]', cp), wa = $('[data-cp-wa]', cp);
    fillCountries(sel);
    UF.forEach(function (u) { var o = document.createElement('option'); o.value = u; o.textContent = u; stt.appendChild(o); });
    stt.value = 'Rio Grande do Norte';
    var li = function (arr) { return '<ul class="cp-ul">' + arr.map(function (x) { return '<li><svg class="ico" viewBox="0 0 24 24"><path d="M5 12l5 5 9-10"/></svg><span>' + x + '</span></li>'; }).join('') + '</ul>'; };
    var run = function () {
      var c = sel.value; br.hidden = c !== 'BR';
      if (!c) { out.innerHTML = ''; wa.hidden = true; return; }
      var name = sel.options[sel.selectedIndex].textContent, h = '', where = name;
      if (c === 'BR') {
        h = '<p class="cp-lead">' + V.cpBr + '</p>' + li([V.cpBr1, V.cpBr2, V.cpBr3, V.cpBr4]);
        where = name + ' (' + (city.value ? city.value + ', ' : '') + stt.value + ')';
      } else {
        var ap = (S.ap || []).indexOf(c) > -1;
        h = '<p class="cp-lead ' + (ap ? 'ok' : 'warn') + '">' + (ap ? V.cpAp : V.cpNoAp) + '</p>' + li([V.cpL1, V.cpL2, ap ? V.cpL3 : V.cpL3n, ap ? V.cpL4 : V.cpL4n, V.cpL5, V.cpL6]);
        if (c === 'AR') h += '<p class="g-unclear"><svg class="ico" viewBox="0 0 24 24"><path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v6M12 7.500h.010"/></svg><span>' + V.cpAR + '</span></p>';
        else h += '<p class="g-unclear"><svg class="ico" viewBox="0 0 24 24"><path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v6M12 7.500h.010"/></svg><span>' + V.cpUn + '</span></p>';
        h += '<p class="g-p">' + V.cpTr + '</p>';
      }
      out.innerHTML = h; wa.hidden = false;
      wa.href = waLink(V.cpMsg + ' ' + where + '. ' + V.cpMsgEnd);
    };
    [sel, stt].forEach(function (x) { x.addEventListener('change', run); }); city.addEventListener('input', run);
  });

  /* ---------- Verkauf: Upload ---------- */
  $$('[data-sellup]').forEach(function (f) {
    var msg = $('.form-msg', f);
    $$('[data-up]', f).forEach(function (i) { i.addEventListener('change', function () { var n = i.parentNode.querySelector('[data-up-n]'); n.textContent = i.files.length ? i.files.length + ' ' + V.suFiles : ''; }); });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = f.elements.name.value.trim(), ph = f.elements.phone.value.trim();
      if (!name || !/^\+?[\d\s().-]{8,}$/.test(ph)) { msg.textContent = T.required || '*'; msg.className = 'form-msg err'; return; }
      var files = $$('[data-up]', f).reduce(function (a, i) { return a.concat(Array.prototype.slice.call(i.files)); }, []);
      if (files.length > 20 || files.some(function (x) { return x.size > 10 * 1024 * 1024; })) { msg.textContent = V.suMax; msg.className = 'form-msg err'; return; }
      if (!S.uploadUrl) { var wm = [V.suWaT || 'Venda', f.elements.name.value, f.elements.phone.value, f.elements.where.value, f.elements.size.value, f.elements.price.value].filter(Boolean).join('\n'); window.open('https://wa.me/' + S.wa + '?text=' + encodeURIComponent(wm), '_blank', 'noopener'); msg.textContent = V.suWaGo; msg.className = 'form-msg ok'; return; }
      var fd = new FormData(); ['name', 'phone', 'where', 'size', 'price'].forEach(function (k) { fd.append(k, f.elements[k].value); });
      fd.append('lang', S.lang); fd.append('page', location.href);
      files.forEach(function (x, i) { fd.append('file' + i, x, x.name); });
      msg.textContent = '…'; msg.className = 'form-msg';
      fetch(S.uploadUrl, { method: 'POST', body: fd }).then(function (r) { if (!r.ok) throw 0; msg.textContent = V.suOk; msg.className = 'form-msg ok'; f.reset(); $$('[data-up-n]', f).forEach(function (n) { n.textContent = ''; }); })
        .catch(function () { msg.textContent = V.suErr; msg.className = 'form-msg err'; });
    });
  });

  /* ---------- Merkliste (nur im Browser, ohne Anmeldung) ---------- */
  var FK = 'enseada_fav', favs = [];
  try { favs = JSON.parse(localStorage.getItem(FK) || '[]'); } catch (e) { favs = []; }
  var saveF = function () { try { localStorage.setItem(FK, JSON.stringify(favs)); } catch (e) {} };
  var favUrl = function (sl) { return S.base + (S.lang === 'pt' ? '' : S.lang + '/') + 'imovel/' + sl + '/'; };
  var pill = $('[data-fav-open]'), sheet = $('[data-fav-sheet]');
  var renderF = function () {
    $$('[data-fav]').forEach(function (b) { var on = favs.some(function (x) { return x.slug === b.dataset.slug; }); b.setAttribute('aria-pressed', String(on)); var tt = $('[data-fav-t]', b); if (tt) tt.textContent = on ? tt.dataset.b : tt.dataset.a; });
    if (pill) { pill.hidden = !favs.length; $('[data-fav-n]', pill).textContent = favs.length; }
    var list = $('[data-fav-list]', sheet || document);
    if (list) {
      list.innerHTML = favs.length ? favs.map(function (x) { return '<div class="fav-r"><a href="' + x.url + '">' + x.name.replace(/</g, '&lt;') + '</a><span>R$ ' + nf(x.price) + '</span><button type="button" data-fav-rm="' + x.slug + '" aria-label="×">×</button></div>'; }).join('') : '<p>' + V.mlEmpty + '</p>';
      if (window.__applyCur) window.__applyCur(); var wl = [V.mlMsg, ''].concat(favs.map(function (x) { return x.name + ' – R$ ' + nf(x.price) + '\n' + location.origin + favUrl(x.slug); }));
      var a = $('[data-fav-wa]', sheet); if (a) { a.href = waLink(wl.join('\n')); a.hidden = !favs.length; }
    }
  };
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-fav]');
    if (b) { e.preventDefault(); var s = b.dataset.slug, i = favs.findIndex(function (x) { return x.slug === s; }); if (i > -1) favs.splice(i, 1); else favs.push({ slug: s, name: b.dataset.name, url: b.dataset.url, price: +b.dataset.price }); saveF(); renderF(); return; }
    var r = e.target.closest('[data-fav-rm]'); if (r) { favs = favs.filter(function (x) { return x.slug !== r.dataset.favRm; }); saveF(); renderF(); return; }
    if (e.target.closest('[data-fav-open]')) { sheet.hidden = false; return; }
    if (e.target.closest('[data-fav-close]') || e.target === sheet) { sheet.hidden = true; }
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && sheet && !sheet.hidden) sheet.hidden = true; });
  renderF();


  /* up22: Daumen gleitet sofort, dann weicher Seitenwechsel; Sprache bleibt auf gleicher Seite */
  (function () {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches, DELAY = reduce ? 0 : 290;
    var BASE = S.base || '/', KEY = 'langScroll';
    var rel = function () { var p = location.pathname; if (p.indexOf(BASE) === 0) p = p.slice(BASE.length); return p.replace(/^(en|es|de)\//, ''); };
    /* Schalter (Sprache / Währung): Daumen unter der aktiven Taste */
    var segs = $$('.seg');
    var place = function (s) { var a = $('[aria-current=true],[aria-pressed=true]', s); if (!a || !a.offsetWidth) return; s.style.setProperty('--x', a.offsetLeft + 'px'); s.style.setProperty('--w', a.offsetWidth + 'px'); if (!s.classList.contains('rdy')) { s.classList.add('rdy'); requestAnimationFrame(function () { requestAnimationFrame(function () { s.classList.add('anim'); }); }); } };
    segs.forEach(function (s) {
      place(s);
      if ('ResizeObserver' in window) new ResizeObserver(function () { s.classList.remove('anim'); place(s); requestAnimationFrame(function () { requestAnimationFrame(function () { if (s.classList.contains('rdy')) s.classList.add('anim'); }); }); }).observe(s);
      if ('MutationObserver' in window) new MutationObserver(function () { place(s); }).observe(s, { attributes: true, subtree: true, attributeFilter: ['aria-pressed', 'aria-current'] });
    });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { segs.forEach(function (s) { s.classList.remove('anim'); place(s); requestAnimationFrame(function () { requestAnimationFrame(function () { s.classList.add('anim'); }); }); }); });
    /* Sprachlinks */
    $$('[data-lang]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
        e.preventDefault();
        var seg = a.closest('.seg'), target = a.getAttribute('href') + location.search + location.hash;
        $$('[data-lang]').forEach(function (x) { if (x.dataset.lang === a.dataset.lang) x.setAttribute('aria-current', 'true'); else x.removeAttribute('aria-current'); });
        try { sessionStorage.setItem(KEY, JSON.stringify({ p: rel(), y: window.scrollY })); } catch (er) {}
        setTimeout(function () { location.href = target; }, DELAY);
      });
    });
    /* Tabs Alle / Kaufen / Mieten */
    var nav = $('[data-slide]');
    if (nav) {
      var links = $$('a', nav), cur = links.findIndex(function (a) { return a.getAttribute('aria-current') === 'true'; }); if (cur < 0) cur = 0;
      links.forEach(function (a, i) {
        a.addEventListener('click', function (e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.button || i === cur) return;
          e.preventDefault();
          nav.style.setProperty('--i', i);
          links.forEach(function (x, n) { if (n === i) x.setAttribute('aria-current', 'true'); else x.removeAttribute('aria-current'); });
          var href = a.getAttribute('href');
          setTimeout(function () { location.href = href; }, DELAY);
        });
      });
    }
  })();

  /* Fallback ohne pagereveal (z. B. ältere Browser): Scrollposition nach Sprachwechsel */
  if (!('onpagereveal' in window)) {
    try { var sv = JSON.parse(sessionStorage.getItem('langScroll') || 'null'), pp = location.pathname; if (pp.indexOf(S.base || '/') === 0) pp = pp.slice((S.base || '/').length); pp = pp.replace(/^(en|es|de)\//, '');
      if (sv) { sessionStorage.removeItem('langScroll'); if (sv.p === pp && !location.hash) window.scrollTo(0, sv.y); } } catch (e) {}
  }
})();
