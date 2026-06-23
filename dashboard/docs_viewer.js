/* docs_viewer.js — site-docs 슬라이드 뷰어 (hdel·cop 공유, byte-identical). SP3.
   data.json.docs ({spec,guide}) → 레이아웃 A 슬라이드. screenshot 있으면 이미지+본문,
   없거나 kind=system 이면 본문 승격. 토글은 setRoute 로 위임(메뉴 강조 동기화). */
(function () {
  var DOCS_IDX = { spec: 0, guide: 0 };                  // 덱별 인덱스(토글 위치 보존)
  var DECK_ROUTE = { spec: 'about', guide: 'guide' };    // 덱 ↔ 메뉴 라우트
  var DECK_MOUNT = { spec: 'docs-viewer-spec', guide: 'docs-viewer-guide' };

  function docsFor(deck) {
    var docs = (window.DATA && window.DATA.docs) || {};
    var d = docs[deck];
    return d && Array.isArray(d.slides) ? d.slides : [];
  }
  function fmtDate(iso) {
    var m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
    return m ? (m[1] + '-' + m[2] + '-' + m[3]) : '';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  }
  function slideHtml(deck, slides, idx) {
    var s = slides[idx];
    var n = slides.length;
    var head =
      '<div class="docs-viewer__head">' +
        '<div class="docs-viewer__toggle">' +
          '<button type="button" class="docs-viewer__tab' + (deck === 'spec' ? ' is-active' : '') + '" data-deck="spec">명세</button>' +
          '<button type="button" class="docs-viewer__tab' + (deck === 'guide' ? ' is-active' : '') + '" data-deck="guide">가이드</button>' +
        '</div>' +
        '<div class="docs-viewer__title">' + esc(s.title) + '</div>' +
        (s.category ? '<div class="docs-viewer__chip">' + esc(s.category) + '</div>' : '') +
      '</div>';
    var hasShot = s.screenshot && s.kind !== 'system';
    var shot = hasShot
      ? '<img class="docs-viewer__shot" src="' + esc(s.screenshot) + '" alt="' + esc(s.title) + '" onerror="this.classList.add(\'is-hidden\')">'
      : '';
    var body = '<div class="docs-viewer__body">' + window.renderMarkdown(s.body_md || '') + '</div>';
    var stage = '<div class="docs-viewer__stage' + (hasShot ? '' : ' is-textonly') + '">' + shot + body + '</div>';
    var ind;
    if (n <= 12) {
      var dots = '';
      for (var i = 0; i < n; i++) dots += '<i class="docs-viewer__dot' + (i === idx ? ' is-active' : '') + '"></i>';
      ind = '<div class="docs-viewer__dots">' + dots + '</div>';
    } else {
      var pct = n > 1 ? (idx / (n - 1) * 100) : 0;
      ind = '<div class="docs-viewer__bar"><span style="width:' + pct + '%"></span></div>';
    }
    var nav =
      '<div class="docs-viewer__nav">' +
        '<button type="button" class="docs-viewer__arrow" data-nav="prev"' + (idx <= 0 ? ' disabled' : '') + '>◀</button>' +
        ind +
        '<span class="docs-viewer__count">' + (idx + 1) + ' / ' + n + '</span>' +
        '<button type="button" class="docs-viewer__arrow" data-nav="next"' + (idx >= n - 1 ? ' disabled' : '') + '>▶</button>' +
      '</div>';
    var foot = s.commit
      ? '<div class="docs-viewer__foot">updated ' + esc(fmtDate(s.updated_at)) + ' · commit ' + esc(s.commit) + '</div>'
      : '';
    return '<div class="docs-viewer" data-deck="' + deck + '">' + head + stage + nav + foot + '</div>';
  }
  function renderDocs(deck) {
    if (deck !== 'spec' && deck !== 'guide') return;
    var mount = document.getElementById(DECK_MOUNT[deck]);
    if (!mount) return;
    var slides = docsFor(deck);
    if (!slides.length) { mount.innerHTML = '<div class="docs-viewer docs-viewer--empty"><p>표시할 문서가 아직 없습니다.</p></div>'; return; }
    var idx = DOCS_IDX[deck];
    if (idx < 0) idx = 0;
    if (idx > slides.length - 1) idx = slides.length - 1;
    DOCS_IDX[deck] = idx;
    mount.innerHTML = slideHtml(deck, slides, idx);
    bind(mount, deck, slides);
  }
  function bind(mount, deck, slides) {
    var root = mount.querySelector('.docs-viewer');
    if (!root) return;
    root.querySelectorAll('[data-nav]').forEach(function (b) {
      b.addEventListener('click', function () {
        var ni = DOCS_IDX[deck] + (b.getAttribute('data-nav') === 'next' ? 1 : -1);
        if (ni < 0 || ni > slides.length - 1) return;
        DOCS_IDX[deck] = ni; renderDocs(deck);
      });
    });
    root.querySelectorAll('.docs-viewer__tab').forEach(function (t) {
      t.addEventListener('click', function () {
        var target = t.getAttribute('data-deck');
        if (target === deck) return;
        var curId = slides[DOCS_IDX[deck]] && slides[DOCS_IDX[deck]].id;
        var tslides = docsFor(target), ti = -1;
        for (var i = 0; i < tslides.length; i++) { if (tslides[i].id === curId) { ti = i; break; } }
        DOCS_IDX[target] = ti >= 0 ? ti : 0;
        window.setRoute(DECK_ROUTE[target]);   // 메뉴 라우트로 위임 → renderDocs(target) 호출됨
      });
    });
  }
  function activeDeck() {
    var a = document.getElementById('view-about'), g = document.getElementById('view-guide');
    if (a && !a.classList.contains('hidden')) return 'spec';
    if (g && !g.classList.contains('hidden')) return 'guide';
    return null;
  }
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    var tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    var deck = activeDeck();
    if (!deck) return;
    var slides = docsFor(deck);
    if (!slides.length) return;
    var ni = DOCS_IDX[deck] + (e.key === 'ArrowRight' ? 1 : -1);
    if (ni < 0 || ni > slides.length - 1) return;
    DOCS_IDX[deck] = ni; renderDocs(deck);
  });
  window.renderDocs = renderDocs;
})();
