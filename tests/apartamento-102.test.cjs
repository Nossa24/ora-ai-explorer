// Apartamento 102 (Torre 1): PROPUESTA DE REDISTRIBUCIÓN (rediseño conceptual, no planta verificada).
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'apartamento-102');
const g = JSON.parse(fs.readFileSync(path.join(dir, 'data/propuesta-102.json'), 'utf8'));
const orig = JSON.parse(fs.readFileSync(path.join(dir, 'data/original-102-dwg.json'), 'utf8'));
const glbBuf = fs.readFileSync(path.join(dir, 'modelo/apto-102-propuesta.glb'));
const gltf = JSON.parse(glbBuf.subarray(20, 20 + glbBuf.readUInt32LE(12)).toString('utf8'));
const nodes = Object.fromEntries(gltf.nodes.map(n => [n.name, n.extras]));
const base = 'http://127.0.0.1:18782/apartamento-102/';
const Q = '?calidad=media';
const room = id => g.espacios.find(r => r.id === id);
let browser, server;

before(async () => {
  server = spawn(process.execPath, ['server.mjs'], { cwd: root, env: { ...process.env, PORT: '18782' }, stdio: ['ignore', 'pipe', 'pipe'] });
  await once(server.stdout, 'data');
  const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
});
after(async () => { await browser?.close(); if (server?.exitCode === null) { const e = once(server, 'exit'); server.kill(); await e; } });

async function open(t, width = 960, height = 600, url = base + Q) {
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, isMobile: width < 700, hasTouch: width < 900 });
  t.after(() => context.close());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(m.text()); });
  page.on('requestfailed', r => { if (!/fonts\.(googleapis|gstatic)/.test(r.url())) errors.push('recurso: ' + r.url()); });
  t.after(() => assert.deepEqual(errors, [], 'sin errores de JavaScript ni de carga de recursos'));
  await page.route('https://fonts.googleapis.com/**', r => r.abort());
  await page.goto(url);
  await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 90000 });
  return page;
}
const settle = page => page.waitForFunction(() => !APTO_API.state.flying, null, { timeout: 60000 });
const frames = async (page, n = 2) => { await page.evaluate(() => APTO_API.render(4)); const f = await page.evaluate(() => APTO_API.state.frame); await page.waitForFunction(v => APTO_API.state.frame >= v, f + n, { timeout: 60000 }); };

// ------------------------------------------------------------------ programa y relación con el DWG
test('programa: 2 habitaciones amplias, 2 baños, sin estudio', () => {
  const ids = g.espacios.map(r => r.id).sort();
  assert.deepEqual(ids, ['bano_principal', 'bano_social', 'habitacion_2', 'hall', 'principal', 'deposito', 'social', 'vestier'].sort());
  assert(!g.espacios.some(r => /estudio/i.test(r.id + r.nombre)), 'el estudio desaparece');
  assert(room('principal').area_neta_m2 > room('habitacion_2').area_neta_m2, 'la principal es la más generosa');
  assert(room('habitacion_2').area_neta_m2 >= 8.5, 'la secundaria no es pequeña');
  assert(room('principal').area_neta_m2 >= 11, 'principal amplia');
  assert(room('social').area_neta_m2 >= 18, 'sala-comedor-cocina amplia');
  // el baño principal se abre desde la habitación principal (suite)
  const d = g.puertas.find(p => p.id === 'bano_principal'); const [x0, y0, x1, y1] = d.rect; const pr = room('principal').caja, bp = room('bano_principal').caja;
  assert(x0 >= pr[0] && x1 <= pr[2] && Math.abs(y0 - pr[3]) < 0.01 && Math.abs(y1 - bp[1]) < 0.01, 'puerta del baño principal desde la suite');
  assert(g.aparatos.filter(a => a.tipo === 'ducha').length === 2 && g.aparatos.filter(a => a.tipo === 'sanitario').length === 2);
  assert(g.aparatos.some(a => a.tipo === 'lavadora') && g.aparatos.some(a => a.tipo === 'lavadero'), 'zona de ropas resuelta');
  // barra en lugar de comedor: península de 2 puestos y sin mesa de comedor
  const pen = g.aparatos.find(a => a.id === 'peninsula');
  assert(pen && pen.barra.puestos === 2 && Math.abs(pen.rect[2] - pen.rect[0] - 1.45) < 0.01, 'barra-península de 1,45 m');
  assert(!Object.keys(g.mobiliario).some(k => /comedor/.test(k)), 'sin comedor tradicional');
  // ropas en la esquina izquierda al entrar, contra el medianero oeste y junto a la puerta de acceso
  const col = g.aparatos.find(a => a.id === 'columna_ropas').rect, ent = g.puertas.find(d => d.id === 'entrada').rect;
  assert(col[0] <= 0.16 && col[3] <= ent[1] && ent[1] - col[3] < 1.1, 'columna de ropas junto al acceso');
  assert(g.ropas.pendientes.length >= 3, 'redes de ropas marcadas como pendientes de viabilidad');
  assert.equal(g.estado, 'rediseño conceptual / propuesta comercial');
  assert.match(g.rotulo, /Propuesta de redistribución – apto 102/);
});

test('la envolvente, los vanos de fachada, el acceso y los ductos son los del DWG', () => {
  assert.deepEqual(g.envolvente_exterior, [0, 0, 8.074, 7.6]);
  // cada vano de fachada coincide con una línea de VENTANAS del DWG
  const vent = orig.segmentos.ventanas;
  for (const w of g.ventanas) {
    const ok = vent.some(([a, b]) => Math.abs(Math.min(a[0], b[0]) - w.x0) < 0.01 && Math.abs(Math.max(a[0], b[0]) - w.x1) < 0.01);
    assert(ok, `vano ${w.id} (${w.x0}–${w.x1}) en el DWG`);
  }
  assert.deepEqual(g.ventanas.map(w => w.ancho), [2.449, 1, 1]);
  assert.deepEqual(g.puertas.find(p => p.id === 'entrada').rect, [0.15, 7.45, 1.15, 7.6]);
  // los ductos son cuadrados de 0,25 m del DWG
  const muros = orig.segmentos.muros.flat();
  for (const [x0, y0, x1, y1] of g.ductos) assert(muros.some(p => Math.abs(p[0] - x0) < 0.01 && Math.abs(p[1] - y0) < 0.01) || muros.some(p => Math.abs(p[0] - x1) < 0.01 && Math.abs(p[1] - y1) < 0.01), 'ducto del DWG');
  const total = g.areas.interior_neta_m2 + g.areas.muros_dentro_envolvente_m2;
  assert(Math.abs(total - g.areas.envolvente_bruta_m2) < 0.1, `interior + muros = envolvente (${total})`);
  assert.equal(g.area_rotulada_dwg_m2, 60.42);
});

test('el GLB separa envolvente del DWG, propuesta e ilustrativo', () => {
  assert.equal(nodes.ARQ_Muros.categoria, 'verificado');
  assert.equal(nodes.PRO_Muros_interiores.categoria, 'propuesta'); assert.equal(nodes.PRO_Muros_interiores.grupo, 'rediseno');
  for (const [n, x] of Object.entries(nodes)) {
    if (/^APA_|^PROP_|^ARQ_Piso/.test(n)) assert.equal(x.categoria, 'propuesta', n);
    if (/^MOB_/.test(n) && n !== 'MOB_Balcon') assert.equal(x.categoria, 'ilustrativo', n);
  }
  assert.match(nodes.Apto_102_Torre_1_Propuesta.advertencia, /No es planta verificada/);
  assert.equal(gltf.nodes.filter(n => /^PROP_/.test(n.name)).length, 3);
});

// ------------------------------------------------------------------ circulación con mobiliario
const R = 0.22, prop = g.balcon, sala = g.ventanas.find(w => w.id === 'sala');
const huellas = Object.entries(nodes).filter(([n]) => /^(MOB|APA|PROP)_/.test(n)).flatMap(([, x]) => x.huella || []);
const hojas = Object.values(nodes).flatMap(x => x.segmentos || []);
function segDist(px, py, [ax, ay, bx, by]) { const dx = bx - ax, dy = by - ay, t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))); return Math.hypot(px - ax - t * dx, py - ay - t * dy); }
function libre(x, y, r = R) {
  const [bx0, by0, bx1] = prop.rect_util;
  const enBalcon = x >= bx0 + r && x <= bx1 - r && y >= by0 + r && y < r + 0.01;
  if (!enBalcon && (x < r || x > 8.074 - r || y < r || y > 7.6 - r)) return false;
  const obs = [...g.muros_rectangulos, ...g.ventanas.filter(w => w !== sala).map(w => [w.x0, w.y0, w.x1, w.y1]), g.puertas.find(d => d.id === 'entrada').rect, ...huellas,
    [prop.acceso.hojas_cerradas[0], 0, prop.acceso.hojas_cerradas[1], 0.15]];
  if (obs.some(([a, b, c, d]) => x > a - r && x < c + r && y > b - r && y < d + r)) return false;
  return !hojas.some(s => segDist(x, y, s) < r + s[4] / 2);
}
test('con el mobiliario puesto se llega caminando a todos los espacios y al balcón', () => {
  const st = 0.02, x0 = -0.2, y0 = -1.9, nx = 426, ny = 486, seen = new Uint8Array(nx * ny);
  const id = (x, y) => Math.round((y - y0) / st) * nx + Math.round((x - x0) / st);
  const q = [id(0.65, 7.0)]; seen[q[0]] = 1;
  while (q.length) {
    const k = q.pop(), i = k % nx, j = (k - i) / nx;
    for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const a = i + di, b = j + dj; if (a < 0 || b < 0 || a >= nx || b >= ny) continue;
      const kk = b * nx + a; if (!seen[kk] && libre(x0 + a * st, y0 + b * st)) { seen[kk] = 1; q.push(kk); }
    }
  }
  const puntos = { cocina: [1.3, 5.8], nevera: [3.2, 6.5], barra: [1.0, 3.75], paso_barra: [2.0, 4.6], ropas_frente: [1.2, 5.9], sala: [1.5, 0.75], hall: [4.0, 4.2], habitacion_2: [4.0, 2.8], escritorio: [4.9, 1.3],
    principal: [5.65, 2.5], ventana_principal: [6.0, 0.6], bano_principal: [5.9, 5.3], vestier: [7.0, 5.5], bano_social: [4.3, 5.2], deposito: [3.1, 5.05], balcon: [1.9, -0.8], balcon_fondo: [1.75, -1.4] };
  for (const [k, [x, y]] of Object.entries(puntos)) assert(seen[id(x, y)], `se llega a ${k}`);
});

// ------------------------------------------------------------------ visor
test('el visor rotula la propuesta y ofrece espacios, puntos y leyenda', async t => {
  const page = await open(t);
  assert.match(await page.locator('#propBanner').textContent(), /Propuesta de redistribución – apto 102/);
  assert.equal(await page.locator('#propBanner').isVisible(), true);
  assert.match(await page.locator('#card').textContent(), /2 habitaciones · 2 baños/);
  assert.equal(await page.locator('.hs').count(), 9);
  assert.equal(await page.locator('.poi').count(), 15);   // incluye barra, ropas junto al acceso y depósito
  assert(!(await page.locator('#rooms').textContent()).match(/estudio/i));
  const stats = await page.evaluate(() => APTO_API.stats);
  assert(stats.categorias.propuesta >= 10 && stats.categorias.verificado >= 1);
});

test('«Solo envolvente del DWG» oculta la propuesta y dibuja la planta original', async t => {
  const page = await open(t);
  await page.locator('#tabs [data-tab="capas"]').click();
  assert.equal(await page.evaluate(() => APTO_API.original()), false);
  await page.locator('#layerOriginal').check();
  assert.equal(await page.evaluate(() => APTO_API.original()), true, 'planta original superpuesta');
  await page.locator('#layerOriginal').uncheck();
  await page.locator('#layerVerified').check();
  const v = n => page.evaluate(n => APTO_API.visible(n), n);
  for (const n of ['PRO_Muros_interiores', 'APA_Cocina', 'MOB_Sofa', 'PROP_Balcon_losa', 'ILU_Puerta_principal']) assert.equal(await v(n), false, n);
  assert.equal(await v('ARQ_Muros'), true);
  assert.equal(await page.evaluate(() => APTO_API.original()), true);
  assert.equal(await page.evaluate(() => APTO_API.free(4.0, 3.76)), true, 'sin tabiques propuestos, el muro de la habitación 2 no existe');
  await page.locator('#layerVerified').uncheck();
  assert.equal(await v('PRO_Muros_interiores'), true);
  assert.equal(await page.evaluate(() => APTO_API.free(4.0, 3.76)), false);
});

test('caminar: colisiones con tabiques, mobiliario y hojas de puerta de la propuesta', async t => {
  const page = await open(t);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page); await frames(page);
  const s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.mode, 'walk'); assert.equal(s.height, 1.6); assert.equal(s.room, 'social');
  const f = await page.evaluate(() => ({ cama_p: APTO_API.free(6.9, 2.5), cama_2: APTO_API.free(3.7, 1.7), banquetas: APTO_API.free(1.15, 4.25), columna_ropas: APTO_API.free(0.45, 6.0), peninsula: APTO_API.free(1.0, 4.95), muro_hall: APTO_API.free(5.3, 4.73),
    vano_hab2: APTO_API.free(3.3, 3.76), vano_principal: APTO_API.free(5.33, 4.26), hoja_principal: APTO_API.free(5.45, 3.4), paso_barra: APTO_API.free(2.1, 4.6), eje_balcon: APTO_API.free(2.0, 0.3) }));
  assert.deepEqual(f, { cama_p: false, cama_2: false, banquetas: false, columna_ropas: false, peninsula: false, muro_hall: false, vano_hab2: true, vano_principal: true, hoja_principal: false, paso_barra: true, eje_balcon: true });
  await page.evaluate(() => APTO_API.goRoom('principal')); await settle(page); await frames(page);
  assert.equal((await page.evaluate(() => APTO_API.state)).room, 'principal');
});

test('la trayectoria del recorrido no atraviesa muros, muebles, hojas ni baranda', async t => {
  const page = await open(t);
  for (const conBalcon of [true, false]) {
    await page.evaluate(b => APTO_API.setBalcony(b), conBalcon);
    const pts = await page.evaluate(() => APTO_API.tourSample(0.04));
    assert.equal(new Set(pts.map(p => p.c)).size, 12, 'doce capítulos');
    const muros = [...g.muros_rectangulos, ...g.ventanas.map(w => [w.x0, w.y0, w.x1, w.y1])];
    let prev = null;
    for (const p of pts) {
      if (p.h < 2.55 && p.x > 0 && p.x < 8.074 && p.y > 0 && p.y < 7.6) {
        const choca = muros.find(([a, b, c, d]) => p.x > a - 0.1 && p.x < c + 0.1 && p.y > b - 0.1 && p.y < d + 0.1 && !(conBalcon && p.y < 0.3 && p.x > prop.acceso.paso_libre[0] + 0.15 && p.x < prop.acceso.paso_libre[1] - 0.15));
        assert(!choca, `t=${p.t}: cruza un muro en (${p.x.toFixed(2)}, ${p.y.toFixed(2)})`);
        assert(!huellas.some(([a, b, c, d]) => p.x > a - 0.05 && p.x < c + 0.05 && p.y > b - 0.05 && p.y < d + 0.05), `t=${p.t}: pasa sobre un mueble en (${p.x.toFixed(2)}, ${p.y.toFixed(2)})`);
        assert(!hojas.some(s => segDist(p.x, p.y, s) < 0.1), `t=${p.t}: atraviesa una hoja de puerta`);
      }
      if (conBalcon && p.y < 0 && p.y > -1.8 && p.x > 0 && p.x < 2.8) assert(p.x > 0.15 && p.x < 2.599 && p.y > -1.65 || p.h > 1.2, `t=${p.t}: cruza la baranda`);
      if (prev) assert(Math.hypot(p.x - prev.x, p.y - prev.y, p.h - prev.h) / 0.04 < (p.h > 2.6 ? 9 : 2.0), `t=${p.t}: movimiento brusco`);
      prev = p;
    }
  }
});

test('recorrido de 12 capítulos: visita todos los espacios, se pausa y se explora desde ahí', async t => {
  const page = await open(t);
  await page.locator('[data-mode="tour"]').click();
  const ch = await page.evaluate(() => APTO_API.chapters());
  assert.equal(ch.length, 12);
  const rooms = new Set((await page.evaluate(() => APTO_API.tourSample(0.25))).map(p => p.room));
  for (const id of ['social', 'balcon', 'hall', 'habitacion_2', 'bano_social', 'principal', 'bano_principal', 'vestier']) assert(rooms.has(id), `visita ${id}`);
  await page.evaluate(() => APTO_API.tourSeek(36)); await frames(page);
  await page.locator('#scene').click({ position: { x: 300, y: 300 } });
  assert.equal((await page.evaluate(() => APTO_API.state)).tourPlaying, false);
  await page.locator('#tourExplore').click(); await frames(page);
  const s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.mode, 'walk'); assert.equal(await page.evaluate(p => APTO_API.free(p.x, p.y), s.plan), true);
});

test('acabados y responsive en teléfono', async t => {
  const page = await open(t, 390, 844);
  assert.equal((await page.evaluate(() => APTO_API.state)).preset, 'monocromatica', 'la propuesta abre en monocromática');
  for (const id of ['calida', 'sofisticada', 'luminosa']) { await page.evaluate(v => APTO_API.setPreset(v), id); assert.equal((await page.evaluate(() => APTO_API.state)).preset, id); }
  const box = sel => page.locator(sel).evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, r: r.right, b: r.bottom }; });
  const card = await box('#card'), banner = await box('#propBanner'), modes = await box('#modes'), panel = await box('#panel');
  assert(card.w <= 330 && card.h <= 110); assert(panel.h <= 50);
  assert(banner.r <= panel.x + 1 || banner.b <= panel.y, 'el rótulo no tapa las opciones');
  assert(banner.b <= modes.y + 1 && banner.x >= 0, 'el rótulo no tapa los modos');
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
});

test('abre desde el archivo (sin servidor)', async t => {
  const page = await open(t, 960, 600, 'file://' + path.join(dir, 'index.html') + Q);
  assert.equal(await page.locator('.hs').count(), 9);
});
