/* Ora AI — Explorador de torres */
(() => {
  'use strict';

  const C = window.ORA;
  const W = 1672, H = 941;
  const NS = 'http://www.w3.org/2000/svg';
  const $ = (s, r = document) => r.querySelector(s);
  const clamp = (v, a, b) => Math.min(Math.max(v, a), b);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const qs = new URLSearchParams(location.search);
  const isTouch = matchMedia('(hover: none)').matches;

  if (qs.has('debug')) document.body.classList.add('debug');

  // ---------------------------------------------------------------- DOM
  const el = {
    stage: $('#stage'), hot: $('#hot'), hud: $('#hud'), flash: $('#flash'),
    imgs: { day: $('#img-day'), night: $('#img-night') },
    tops: { day: $('#top-day'), night: $('#top-night') },
    dot: $('#dot'), line: $('#tipLine'), tip: $('#tip'), hint: $('#hintTxt'), tod: $('#tod'),
    int: $('#int'), fx: $('#fx'), vwrap: $('#vwrap'), vid: $('#vid'), snap: $('#snap'),
    back: $('#back'), backTxt: $('#backTxt'), cap: $('#cap'), capK: $('#capK'), capT: $('#capT'),
    chips: $('#chips'), panel: $('#panel'),
    nav: $('#nav'),
  };

  // marca y textos
  document.querySelectorAll('[data-brand]').forEach(n => { n.textContent = C.brand[n.dataset.brand]; });
  $('#legal').textContent = C.copy.legal;
  el.hint.textContent = isTouch ? C.copy.hintTouch : C.copy.hint;
  $('#cta').textContent = C.brand.cta.label;
  $('#cta').href = C.brand.cta.href;
  $('#pPlan').href = C.brand.cta.href;
  $('#brand').addEventListener('click', e => e.preventDefault());

  // ---------------------------------------------------------------- geometría
  // Homografía cuadrado unidad → cuadrilátero [TL, TR, BR, BL] (Heckbert).
  function quadMap(q) {
    const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
    const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3;
    const dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
    const den = dx1 * dy2 - dx2 * dy1;
    const g = den === 0 ? 0 : (dx3 * dy2 - dx2 * dy3) / den;
    const h = den === 0 ? 0 : (dx1 * dy3 - dx3 * dy1) / den;
    const a = x1 - x0 + g * x1, b = x3 - x0 + h * x3, c = x0;
    const d = y1 - y0 + g * y1, e = y3 - y0 + h * y3, f = y0;
    return (u, v) => { const w = g * u + h * v + 1; return [(a * u + b * v + c) / w, (d * u + e * v + f) / w]; };
  }
  // piso k (1 = el de abajo) de un plano con N pisos
  function floorPoly(map, N, k) {
    const vt = (N - k) / N, vb = (N - k + 1) / N;
    return [map(0, vt), map(1, vt), map(1, vb), map(0, vb)];
  }
  const centroid = p => [p.reduce((s, q) => s + q[0], 0) / p.length, p.reduce((s, q) => s + q[1], 0) / p.length];
  const mk = (tag, attrs = {}) => { const n = document.createElementNS(NS, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); return n; };

  // ---------------------------------------------------------------- estado
  let tod = qs.get('tod') === 'night' ? 'night' : 'day';
  let mode = 'res';
  let state = 'ext';           // ext | int
  let busy = false;
  let hov = null;
  let view = { tx: 0, ty: 0, s: 1 };
  let tl = null;
  let cur = null;              // sesión de interior
  const polys = { day: {}, night: {} };

  function unitFor(plane, k) {
    const T = C.towers[plane.tower];
    return k > T.floors - T.pent ? 'pent' : 'res';
  }

  // ---------------------------------------------------------------- SVG de pisos
  function buildHot() {
    el.hot.innerHTML = '';
    for (const t of ['day', 'night']) {
      const g = mk('g', { 'data-tod': t });
      const pins = mk('g', { class: 'pins' });
      polys[t] = {};
      for (const plane of C.images[t].planes) {
        const T = C.towers[plane.tower];
        const map = quadMap(plane.quad);
        polys[t][plane.id] = {};
        for (let k = 1; k <= T.floors; k++) {
          const pts = floorPoly(map, T.floors, k);
          const node = mk('polygon', { class: 'fl', points: pts.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ') });
          node.dataset.tod = t; node.dataset.plane = plane.id; node.dataset.k = k;
          if (unitFor(plane, k) === 'pent') node.dataset.pent = '1';
          const c = centroid(pts);
          polys[t][plane.id][k] = {
            node, pts, c, plane,
            minX: Math.min(...pts.map(p => p[0])), maxX: Math.max(...pts.map(p => p[0])),
          };
          g.append(node);
        }
      }
      // etiquetas de depuración
      for (const plane of C.images[t].planes) {
        const T = C.towers[plane.tower];
        for (let k = 1; k <= T.floors; k++) {
          const p = polys[t][plane.id][k];
          const tx = mk('text', { class: 'dbg', x: p.c[0], y: p.c[1] + 3, 'text-anchor': 'middle' });
          tx.textContent = T.base + k - 1;
          g.append(tx);
        }
      }
      for (const pin of C.images[t].pins || []) {
        const pg = mk('g', { class: 'pin' });
        pg.append(mk('circle', { class: 'r', cx: pin.x, cy: pin.y, r: 5 }), mk('circle', { class: 'c', cx: pin.x, cy: pin.y, r: 5.5 }));
        const lb = mk('text', { x: pin.x + 14, y: pin.y + 5 }); lb.textContent = pin.label;
        pg.append(lb); pins.append(pg);
      }
      g.append(pins);
      el.hot.append(g);
    }
    syncTodGroups();
  }
  function syncTodGroups() {
    el.hot.querySelectorAll('g[data-tod]').forEach(g => g.classList.toggle('act', g.dataset.tod === tod));
  }

  // ---------------------------------------------------------------- vista (cover)
  function fitView() {
    const vw = innerWidth, vh = innerHeight;
    const s = Math.max(vw / W, vh / H);
    const f = C.images[tod].focus;
    return {
      s,
      tx: clamp(vw / 2 - f[0] * W * s, vw - W * s, 0),
      ty: clamp(vh / 2 - f[1] * H * s, vh - H * s, 0),
    };
  }
  function applyView() { el.stage.style.transform = `translate3d(${view.tx}px,${view.ty}px,0) scale(${view.s})`; }
  const toScreen = (x, y) => [view.tx + view.s * x, view.ty + view.s * y];

  // ---------------------------------------------------------------- hover + tooltip
  let clearTimer = null;
  function info(node) {
    const t = node.dataset.tod, id = node.dataset.plane, k = +node.dataset.k;
    const poly = polys[t][id][k];
    const T = C.towers[poly.plane.tower];
    const unitKey = unitFor(poly.plane, k);
    return { node, tod: t, planeId: id, k, poly, tower: T, floorNo: T.base + k - 1, unitKey, unit: C.units[unitKey] };
  }
  function setHover(node) {
    clearTimeout(clearTimer);
    if (hov && hov.node === node) return;
    if (hov) hov.node.classList.remove('on');
    if (!node) { hov = null; hideTip(); return; }
    hov = info(node);
    node.classList.add('on');
    showTip(hov);
  }
  function scheduleClear() {
    clearTimeout(clearTimer);
    clearTimer = setTimeout(() => setHover(null), 260);
  }
  function hideTip() {
    el.tip.classList.remove('show');
    document.body.classList.remove('tip-on');
    el.dot.style.opacity = 0; el.line.style.opacity = 0;
  }
  function showTip(h) {
    const u = h.unit;
    el.tip.innerHTML =
      `<span class="num"><small>PISO</small><b>${h.floorNo}</b></span><i class="sep"></i>` +
      `<span class="body"><span class="tw">${h.tower.name}</span><strong>${u.name}</strong>` +
      `<span class="sp">${u.specs}</span><em class="chip ${h.unitKey === 'pent' ? 'ex' : ''}">${u.status}</em></span>` +
      `<span class="go" aria-hidden="true">→</span>`;
    el.tip.setAttribute('aria-label', `${h.tower.name}, piso ${h.floorNo}, ${u.name}. Entrar`);
    el.tip.classList.add('show');
    document.body.classList.add('tip-on');
    positionTip(h);
  }
  function positionTip(h) {
    if (innerWidth <= 900) return;
    const vw = innerWidth, vh = innerHeight;
    const p = h.poly;
    const [sx, sy] = toScreen(p.c[0], p.c[1]);
    const tw = el.tip.offsetWidth, th = el.tip.offsetHeight;
    let side = 'r', ex = toScreen(p.maxX, 0)[0] + 52;
    if (ex + tw > vw - 18) { side = 'l'; ex = toScreen(p.minX, 0)[0] - 52 - tw; }
    ex = clamp(ex, 14, vw - tw - 14);
    const ey = clamp(sy, th / 2 + 84, vh - th / 2 - 96);
    el.tip.style.left = ex + 'px';
    el.tip.style.top = (ey - th / 2) + 'px';
    const lx = side === 'r' ? ex : ex + tw, ly = ey;
    const dx = lx - sx, dy = ly - sy;
    el.line.style.width = Math.hypot(dx, dy) + 'px';
    el.line.style.transform = `translate(${sx}px,${sy}px) rotate(${Math.atan2(dy, dx)}rad)`;
    el.dot.style.transform = `translate(${sx}px,${sy}px)`;
    el.dot.style.opacity = 1; el.line.style.opacity = 1;
  }

  // ---------------------------------------------------------------- recorrido automático (modo escaparate)
  const SCAN = {
    res:  [['T2R', 5], ['T2R', 8], ['T2L', 11], ['T2R', 12], ['T2L', 7], ['T1', 6], ['T1', 11], ['T2R', 9]],
    pent: [['T2R', 16], ['T2R', 15], ['T1', 16], ['T1', 15]],
  };
  let scanTimer = null, scanI = 0, idleTimer = null;
  function scanStep() {
    if (state !== 'ext' || busy || mode === 'amen') return;
    const seq = SCAN[mode] || SCAN.res;
    const [id, k] = seq[scanI++ % seq.length];
    const p = polys[tod][id] && polys[tod][id][k];
    if (p) setHover(p.node);
    scanTimer = setTimeout(scanStep, 1050);
  }
  function startScan(delay = 900) { stopScan(); scanTimer = setTimeout(scanStep, delay); }
  function stopScan() { clearTimeout(scanTimer); scanTimer = null; }
  function userActive() {
    stopScan(); clearTimeout(idleTimer);
    idleTimer = setTimeout(() => { if (state === 'ext' && !busy) { setHover(null); startScan(400); } }, 14000);
  }

  // ---------------------------------------------------------------- eventos exterior
  let lastPointer = 'mouse';
  // en pantallas estrechas el edificio es más ancho que la pantalla: se arrastra con el dedo
  let drag = null, moved = false;
  el.hot.addEventListener('pointerdown', e => {
    lastPointer = e.pointerType;
    moved = false;
    if (e.pointerType === 'touch') drag = { x: e.clientX, tx: view.tx, id: e.pointerId };
  });
  addEventListener('pointermove', e => {
    if (!drag || e.pointerId !== drag.id || state !== 'ext' || busy) return;
    const dx = e.clientX - drag.x;
    if (Math.abs(dx) > 8) moved = true;
    if (moved) { view.tx = clamp(drag.tx + dx, innerWidth - W * view.s, 0); applyView(); if (hov) setHover(null); }
  });
  addEventListener('pointerup', () => { drag = null; });
  addEventListener('pointercancel', () => { drag = null; });
  el.hot.addEventListener('pointermove', e => {
    if (state !== 'ext' || busy || e.pointerType === 'touch') return;
    userActive();
    const t = e.target;
    if (t.classList && t.classList.contains('fl')) setHover(t); else scheduleClear();
  });
  el.hot.addEventListener('pointerleave', () => { if (!scanTimer) scheduleClear(); });
  el.hot.addEventListener('click', e => {
    const t = e.target;
    if (!(t.classList && t.classList.contains('fl')) || busy || state !== 'ext') return;
    if (moved) { moved = false; return; }
    userActive();
    if (lastPointer === 'touch' && (!hov || hov.node !== t)) { setHover(t); return; }
    enter(info(t));
  });
  el.tip.addEventListener('pointerenter', () => clearTimeout(clearTimer));
  el.tip.addEventListener('pointerleave', () => scheduleClear());
  el.tip.addEventListener('click', () => { if (hov && !busy) enter(hov); });
  addEventListener('keydown', e => {
    if (state === 'ext') { if (e.key === 'Enter' && hov && !busy) enter(hov); return; }
    if (e.key === 'Escape') onBack();
    if (!cur || cur.mode !== 'room') return;
    if (e.key === 'ArrowRight') goRoom((cur.room + 1) % cur.unit.rooms.length);
    if (e.key === 'ArrowLeft') goRoom((cur.room + cur.unit.rooms.length - 1) % cur.unit.rooms.length);
  });

  // día / noche
  el.tod.addEventListener('click', e => {
    const b = e.target.closest('button[data-tod]');
    if (b) setTod(b.dataset.tod);
  });
  function setTod(t) {
    if (t === tod || busy || state !== 'ext') return;
    stopScan(); setHover(null);
    tod = t; syncTodGroups();
    el.tod.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.tod === t));
    gsap.to([el.imgs.night, el.tops.night], { opacity: t === 'night' ? 1 : 0, duration: reduce ? 0 : 1.3, ease: 'power1.inOut' });
    const to = fitView();
    gsap.to(view, { ...to, duration: reduce ? 0 : 1.3, ease: 'power1.inOut', onUpdate: applyView });
    applyMode();
    userActive();
  }

  // modos del menú: residencias / penthouses / amenidades
  el.nav.addEventListener('click', e => {
    const b = e.target.closest('button[data-mode]');
    if (!b || busy || state !== 'ext') return;
    mode = b.dataset.mode;
    el.nav.querySelectorAll('button').forEach(n => n.classList.toggle('on', n === b));
    applyMode();
    setHover(null); scanI = 0;
    if (mode === 'amen') stopScan(); else startScan(500);
  });
  function applyMode() {
    document.body.classList.toggle('mode-amen', mode === 'amen');
    document.body.classList.toggle('mode-pent', mode === 'pent');
    for (const t of ['day', 'night']) for (const id in polys[t]) for (const k in polys[t][id]) {
      const n = polys[t][id][k].node;
      n.classList.toggle('pent-hint', mode === 'pent' && !!n.dataset.pent);
    }
  }

  // ---------------------------------------------------------------- transición exterior → interior
  function buildParts(t, poly, tx, ty, s) {
    el.fx.innerHTML = '';
    const [a, b, c, d] = poly.pts; // TL TR BR BL
    const yAt = (p, q, x) => p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0]);
    const X0 = -4000, X1 = 6000, Y = 8000;
    const shapes = {
      top:  [[X0, -Y], [X1, -Y], [X1, yAt(a, b, X1)], [X0, yAt(a, b, X0)]],
      band: [[X0, yAt(a, b, X0)], [X1, yAt(a, b, X1)], [X1, yAt(d, c, X1)], [X0, yAt(d, c, X0)]],
      bot:  [[X0, yAt(d, c, X0)], [X1, yAt(d, c, X1)], [X1, Y], [X0, Y]],
    };
    const out = {};
    for (const key in shapes) {
      const part = document.createElement('div'); part.className = 'part';
      const clone = document.createElement('div'); clone.className = 'clone';
      clone.style.transform = `translate3d(${tx}px,${ty}px,0) scale(${s})`;
      clone.style.clipPath = 'polygon(' + shapes[key].map(p => `${p[0].toFixed(1)}px ${p[1].toFixed(1)}px`).join(',') + ')';
      const im = new Image(); im.src = C.images[t].src; im.alt = ''; im.draggable = false;
      const topExt = document.createElement('div'); topExt.className = 'ext-top';
      const ti = new Image(); ti.src = C.images[t].src; ti.alt = ''; topExt.append(ti);
      clone.append(topExt, im); part.append(clone); el.fx.append(part);
      out[key] = part;
    }
    return out;
  }

  function enter(h) {
    if (busy || state !== 'ext') return;
    busy = true; stopScan(); clearTimeout(idleTimer);
    cur = { h, unitKey: h.unitKey, unit: h.unit, mode: 'intro', room: 0, busy: true };
    ensureSrc(h.unit.clip);
    prepareInterior();

    const vw = innerWidth, vh = innerHeight;
    const p = h.poly, bw = p.maxX - p.minX;
    const s1 = clamp(0.8 * vw / bw, view.s * 1.7, view.s * 4.4);
    const tx = vw * 0.5 - s1 * p.c[0], ty = vh * 0.5 - s1 * p.c[1];
    const parts = buildParts(h.tod, p, tx, ty, s1);
    const D = reduce ? 0.01 : 1;
    const zoomT = 1.15 * D, split = 1.05 * D;

    tl = gsap.timeline({
      paused: true,
      onComplete: () => { busy = false; state = 'int'; document.body.classList.add('is-int'); document.body.classList.remove('is-ext'); },
      onReverseComplete: afterExit,
    });
    tl.to(view, { tx, ty, s: s1, duration: zoomT, ease: 'power3.inOut', onUpdate: applyView }, 0)
      .to(el.hud, { autoAlpha: 0, duration: .3 * D, ease: 'none' }, 0)
      .fromTo(el.flash, { opacity: 0 }, { opacity: .55, duration: .4 * D, ease: 'sine.in' }, .62 * D)
      .addLabel('split', split)
      .set(el.stage, { autoAlpha: 0 }, 'split')
      .set(el.fx, { autoAlpha: 1 }, 'split')
      .set(el.int, { autoAlpha: 1 }, 'split')
      .to(el.flash, { opacity: 0, duration: .55 * D, ease: 'sine.out' }, 'split')
      .to(parts.top, { y: -vh * .9, duration: 1.2 * D, ease: 'power3.inOut' }, 'split')
      .to(parts.bot, { y: vh * .9, duration: 1.2 * D, ease: 'power3.inOut' }, 'split')
      .to(parts.band, { autoAlpha: 0, duration: .4 * D, ease: 'power1.out' }, 'split')
      .set(el.fx, { autoAlpha: 0 }, 'split+=' + (1.25 * D))
      .call(() => { if (!tl.reversed()) startInterior(); }, null, 'split+=' + (0.12 * D));
    tl.timeScale(1).play(0);
  }

  function exitToTower() {
    if (busy || state !== 'int' || !cur || cur.busy) return;
    busy = true; cur.busy = true;
    cancelStopper();
    gsap.to([el.panel, el.chips, el.cap, el.back], { autoAlpha: 0, duration: .25 });
    dissolve(0.04, { fade: .5 }).then(() => {
      document.body.classList.remove('is-int'); document.body.classList.add('is-ext');
      state = 'ext';
      tl.timeScale(1.15).reverse();
    });
  }
  function afterExit() {
    el.fx.innerHTML = '';
    gsap.set([el.stage, el.fx, el.int], { clearProps: 'visibility,opacity' });
    gsap.set(el.stage, { autoAlpha: 1 });
    gsap.set(el.fx, { autoAlpha: 0 });
    gsap.set(el.int, { autoAlpha: 0 });
    gsap.to(el.hud, { autoAlpha: 1, duration: .4 });
    view = fitView(); applyView();
    setHover(null);
    el.vid.pause(); el.vwrap.classList.remove('kb');
    cur = null; busy = false;
    userActive(); startScan(1200);
  }

  // ---------------------------------------------------------------- interior
  const vid = el.vid;
  let stopper = null;
  function cancelStopper() { if (stopper) { stopper.cancel(); stopper = null; } }
  function ensureSrc(url) {
    if (vid.dataset.src === url && vid.readyState >= 2) return Promise.resolve();
    vid.dataset.src = url; vid.src = url; vid.load();
    return new Promise(res => vid.addEventListener('loadeddata', res, { once: true }));
  }
  function prepareInterior() {
    gsap.set([el.panel, el.chips, el.cap, el.back], { autoAlpha: 0 });
    const u = cur.unit;
    // panel
    $('#pK').textContent = `PISO ${cur.h.floorNo} · ${u.status}`;
    $('#pT').textContent = u.name;
    $('#pBeds').textContent = u.beds; $('#pBaths').textContent = u.baths; $('#pArea').textContent = u.area;
    $('#pDesc').textContent = u.desc;
    const list = $('#pRooms'); list.innerHTML = '';
    u.rooms.forEach((r, i) => { const li = document.createElement('li'); const b = document.createElement('button'); b.type = 'button'; b.textContent = r.label; b.onclick = () => goRoom(i); li.append(b); list.append(li); });
    // chips
    el.chips.innerHTML = '';
    u.rooms.forEach((r, i) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = r.label; b.dataset.i = i; b.onclick = () => goRoom(i); el.chips.append(b); });
    el.vwrap.classList.remove('kb');
  }

  async function startInterior() {
    const u = cur.unit;
    await ensureSrc(u.clip);
    vid.currentTime = 0;
    try { await vid.play(); } catch (_) { /* autoplay bloqueado: se queda en el primer cuadro */ }
    playUntil(u.plan.hold, onPlan);
  }
  // Reproduce hasta el segundo t y se queda ahí. Tres seguros: callback por cuadro de video (o rAF),
  // y un temporizador por si la pestaña está en segundo plano y el navegador frena los cuadros.
  function playUntil(t, cb) {
    cancelStopper();
    let done = false, raf = 0, rvfc = 0, timer = 0;
    const cancel = () => {
      done = true; cancelAnimationFrame(raf); clearTimeout(timer);
      if (rvfc && vid.cancelVideoFrameCallback) vid.cancelVideoFrameCallback(rvfc);
    };
    const finish = () => {
      if (done) return;
      cancel(); stopper = null; vid.pause();
      if (Math.abs(vid.currentTime - t) > 0.04) vid.currentTime = t;   // cae exactamente en el cuadro de reposo
      cb && cb();
    };
    const schedule = () => { if (vid.requestVideoFrameCallback) rvfc = vid.requestVideoFrameCallback(check); else raf = requestAnimationFrame(check); };
    const check = () => { if (done) return; if (vid.currentTime >= t - 0.02 || vid.ended) finish(); else schedule(); };
    const guard = () => {
      if (done) return;
      const rem = t - vid.currentTime;
      if (rem <= 0.12 || vid.ended) finish(); else timer = setTimeout(guard, Math.max(60, rem * 1000));
    };
    stopper = { cancel };
    vid.play().catch(() => {});
    schedule();
    timer = setTimeout(guard, Math.max(60, (t - vid.currentTime) * 1000));
  }
  // disolvencia entre dos tiempos del mismo video (congela el cuadro actual en un canvas y lo desvanece)
  function dissolve(t, { fade = .5 } = {}) {
    return new Promise(res => {
      cancelStopper(); vid.pause();
      el.vwrap.classList.remove('kb');
      try {
        el.snap.width = vid.videoWidth || 1600; el.snap.height = vid.videoHeight || 874;
        el.snap.getContext('2d').drawImage(vid, 0, 0, el.snap.width, el.snap.height);
        gsap.set(el.snap, { opacity: 1 });
      } catch (_) { /* sin snapshot: salto directo */ }
      const done = () => requestAnimationFrame(() => requestAnimationFrame(() => {
        gsap.to(el.snap, { opacity: 0, duration: reduce ? 0 : fade, ease: 'power1.inOut' });
        res();
      }));
      if (Math.abs(vid.currentTime - t) < 0.01) { done(); return; }
      vid.addEventListener('seeked', done, { once: true });
      vid.currentTime = t;
    });
  }

  function showUI(list) { gsap.to(list, { autoAlpha: 1, duration: .5, ease: 'power1.out' }); }
  function hideUI(list) { gsap.to(list, { autoAlpha: 0, duration: .25 }); }

  function onPlan() {
    cur.mode = 'plan'; cur.busy = false;
    el.backTxt.textContent = 'Volver a la torre';
    showUI([el.panel, el.back]);
  }
  function enterRoom(i) {
    const u = cur.unit;
    cur.mode = 'room'; cur.room = i; cur.busy = false;
    el.capK.textContent = `PISO ${cur.h.floorNo} · ${u.name.toUpperCase()}`;
    el.capT.textContent = u.rooms[i].label;
    el.chips.querySelectorAll('button').forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    el.backTxt.textContent = 'Volver al plano';
    void el.vwrap.offsetWidth; el.vwrap.classList.add('kb');
    showUI([el.cap, el.chips, el.back]);
  }
  async function goRoom(i) {
    if (!cur || cur.busy || state !== 'int') return;
    if (cur.mode === 'room' && cur.room === i) return;
    cur.busy = true;
    const u = cur.unit;
    hideUI([el.panel, el.cap]);
    if (cur.mode === 'plan' && i === 0) {
      // vuelo de la cámara hacia la sala (el video sigue desde un punto sin rótulos)
      hideUI([el.back]);
      await dissolve(u.plan.resume, { fade: .45 });
      cur.mode = 'flying';
      playUntil(u.rooms[0].hold, () => enterRoom(0));
    } else {
      await dissolve(u.rooms[i].hold, { fade: .55 });
      enterRoom(i);
    }
  }
  async function goPlan() {
    if (!cur || cur.busy) return;
    cur.busy = true;
    hideUI([el.cap, el.chips, el.back]);
    await dissolve(cur.unit.plan.hold, { fade: .5 });
    onPlan();
  }
  function onBack() {
    if (!cur || cur.busy || state !== 'int') return;
    if (cur.mode === 'room') goPlan(); else exitToTower();
  }
  el.back.addEventListener('click', onBack);
  $('#pBack').addEventListener('click', exitToTower);
  $('#cta').addEventListener('click', e => { if (C.brand.cta.href === '#') e.preventDefault(); });
  $('#pPlan').addEventListener('click', e => { if (C.brand.cta.href === '#') e.preventDefault(); });

  // ---------------------------------------------------------------- arranque
  addEventListener('resize', () => {
    if (state !== 'ext' || busy) return;
    view = fitView(); applyView();
    if (hov) positionTip(hov);
  });

  function init() {
    buildHot();
    if (tod === 'night') {
      el.imgs.night.style.opacity = 1; el.tops.night.style.opacity = 1;
      el.tod.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.tod === 'night'));
    }
    view = fitView(); applyView();
    applyMode();
    if (qs.get('scan') !== '0') startScan(1600);
    // precarga silenciosa de los dos clips
    setTimeout(() => {
      for (const k in C.units) { const v = document.createElement('video'); v.preload = 'auto'; v.muted = true; v.src = C.units[k].clip; }
    }, 1200);
  }
  init();

  // API para pruebas y para controlarlo desde la consola
  window.ORA_API = {
    hover: (t, id, k) => { setHover(polys[t][id][k].node); },
    enter: (t, id, k) => { if (t !== tod) { tod = t; syncTodGroups(); } enter(info(polys[t][id][k].node)); },
    exit: exitToTower,
    setTod, goRoom, goPlan,
    timeline: () => tl,   // para revisar la transición cuadro por cuadro: ORA_API.timeline().pause().time(1.2)
    get state() { return { state, busy, mode: cur && cur.mode, tod, t: vid.currentTime }; },
  };
})();
