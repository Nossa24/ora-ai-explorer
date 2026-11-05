// Apartamento 104 (Torre 1): geometría verificada, modelo GLB y visor 3D navegable.
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'apartamento-104');
const geo = JSON.parse(fs.readFileSync(path.join(dir, 'data/geometria-104.json'), 'utf8'));
const base = 'http://127.0.0.1:18781/apartamento-104/';
let browser, server;

before(async () => {
  server = spawn(process.execPath, ['server.mjs'], { cwd: root, env: { ...process.env, PORT: '18781' }, stdio: ['ignore', 'pipe', 'pipe'] });
  await once(server.stdout, 'data');
  const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
});
after(async () => { await browser?.close(); if (server?.exitCode === null) { const e = once(server, 'exit'); server.kill(); await e; } });

async function open(t, width = 1440, height = 900, url = base) {
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, isMobile: width < 700, hasTouch: width < 900, reducedMotion: 'no-preference' });
  t.after(() => context.close());
  const page = await context.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message)); t.after(() => assert.deepEqual(errors, []));
  await page.route('https://fonts.googleapis.com/**', r => r.abort());
  await page.goto(url);
  await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 30000 });
  return page;
}
const settle = page => page.waitForFunction(() => !APTO_API.state.flying, null, { timeout: 15000 });
// el render por software de las pruebas es lento: se esperan cuadros reales antes de leer el estado
const frames = async (page, n = 2) => { const f = await page.evaluate(() => APTO_API.state.frame); await page.waitForFunction(v => APTO_API.state.frame >= v, f + n, { timeout: 15000 }); };

// ------------------------------------------------------------------ geometría tomada del DWG
test('identificación y cotas verificables del apartamento 104', () => {
  assert.equal(geo.apartamento, '104'); assert.equal(geo.torre, 'Torre 1');
  assert(geo.identificacion['APTO 104']?.length, 'rótulo APTO 104 del plano');
  assert(geo.identificacion['AREA 60.01m2']?.length, 'rótulo de área del plano');
  const values = new Set(geo.cotas.map(d => d.medida));
  for (const v of [7.45, 7.6, 2.475, 3.6, 2.75, 1.7, 1.65, 1.5, 2.15, 1.525, 1.39, 1.36, 1.21, 1.95, 2.19, 1.16, 1.24, 0.72, 1.28, 0.8, 0.85]) assert(values.has(v), `cota ${v}`);
  assert.deepEqual(geo.envolvente_exterior, [0, 0, 8.1, 7.6]);
  assert.equal(geo.puertas.length, 6); assert.equal(geo.ventanas.length, 4);
  assert.deepEqual(geo.ventanas.map(v => v.ancho).sort(), [1, 1, 1, 2.475]);
});

test('ocho espacios con áreas netas coherentes con el rótulo de 60,01 m²', () => {
  assert.equal(geo.espacios.length, 8);
  const byId = Object.fromEntries(geo.espacios.map(r => [r.id, r.area_neta_m2]));
  assert(byId.social > 17.5 && byId.social < 18.5);
  for (const id of ['alcoba_2', 'alcoba_3', 'alcoba_principal']) assert(byId[id] > 6 && byId[id] < 9.5, id);
  for (const id of ['bano_social', 'bano_principal']) assert(byId[id] > 1.5 && byId[id] < 3, id);
  const total = geo.areas.interior_neta_m2 + geo.areas.muros_dentro_envolvente_m2;
  assert(total > 58 && total < 61.6, `interior + muros = ${total}`);
  assert(geo.pendientes.some(p => /Altura libre/.test(p)), 'la altura se declara pendiente');
});

test('el GLB separa arquitectura verificada de elementos ilustrativos', () => {
  const buf = fs.readFileSync(path.join(dir, 'modelo/apto-104.glb'));
  assert.equal(buf.readUInt32LE(0), 0x46546c67); assert.equal(buf.readUInt32LE(4), 2);
  const json = JSON.parse(buf.subarray(20, 20 + buf.readUInt32LE(12)).toString('utf8'));
  const nodes = Object.fromEntries(json.nodes.map(n => [n.name, n.extras]));
  assert.equal(nodes.ARQ_Muros.verificado, true);
  assert.equal(nodes.ARQ_Piso_social.verificado, true);
  assert.equal(nodes.APA_Cocina.verificado, true);
  for (const n of ['MOB_Sofa', 'MOB_Alcoba_principal', 'ILU_Ventaneria', 'ARQ_Losa', 'ARQ_Cielo']) assert.equal(nodes[n].verificado, false, n);
  assert.equal(nodes.Apto_104_Torre_1.supuestos_visualizacion.altura_libre, 2.4);
});

// ------------------------------------------------------------------ visor
test('el visor dibuja el apartamento y ofrece un punto por espacio', async t => {
  const page = await open(t);
  const shot = await page.locator('#scene').screenshot();
  assert(shot.length > 40000, 'la escena tiene contenido');   // un lienzo vacío comprime a pocos KB
  assert.equal(await page.locator('.hs').count(), 8);
  assert.equal(await page.locator('#rooms button').count(), 8);
  const stats = await page.evaluate(() => APTO_API.stats);
  assert(stats.verificados >= 12 && stats.ilustrativos >= 10);
  assert(stats.materiales.includes('muro') && stats.materiales.includes('piso_madera'));
});

test('elegir un espacio lleva la cámara hasta él', async t => {
  const page = await open(t);
  await frames(page);
  await page.locator('.hs[data-room="alcoba_2"]').click();      // punto interactivo desde la maqueta completa
  await settle(page);
  assert.equal((await page.evaluate(() => APTO_API.state)).room, 'alcoba_2');
  await page.locator('#rooms button[data-room="alcoba_principal"]').click();
  await settle(page);
  const s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.room, 'alcoba_principal');
  assert(s.target.x > 5.45 && s.target.y > 3.9 && s.target.y < 7.45, `la cámara apunta a la alcoba principal (${s.target.x}, ${s.target.y})`);
});

test('caminar: altura de ojos, colisión con muros y paso por los vanos reales', async t => {
  const page = await open(t);
  await page.locator('[data-mode="walk"]').click();
  await settle(page); await frames(page);
  let s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.mode, 'walk'); assert.equal(s.height, 1.6); assert.equal(s.room, 'social');
  await page.evaluate(() => APTO_API.move(-3, 0));          // hacia el muro medianero
  s = await page.evaluate(() => APTO_API.state);
  assert(s.plan.x >= 0.15 + 0.22 - 1e-3, `se detiene en el muro (${s.plan.x})`);
  await page.evaluate(() => APTO_API.move(0, -3));          // hacia la fachada sur
  s = await page.evaluate(() => APTO_API.state);
  assert(s.plan.y >= 0.15 + 0.22 - 1e-3);
  const doors = await page.evaluate(g => g.puertas.filter(d => d.id !== 'entrada').map(d => { const [x0, y0, x1, y1] = d.rect; return APTO_API.free((x0 + x1) / 2, (y0 + y1) / 2); }), geo);
  assert.deepEqual(doors, [true, true, true, true, true], 'todos los vanos interiores son transitables');
  const walls = await page.evaluate(g => g.muros_rectangulos.filter(([x0, y0, x1, y1]) => (x1 - x0) * (y1 - y0) > .1).map(([x0, y0, x1, y1]) => APTO_API.free((x0 + x1) / 2, (y0 + y1) / 2)), geo);
  assert(walls.every(v => v === false), 'ningún muro es atravesable');
  assert.equal(await page.evaluate(() => APTO_API.free(0.65, 7.55)), false, 'no se sale al corredor');
  assert.equal(await page.locator('#walkpad').isVisible(), true);
  await page.keyboard.press('Escape');
  assert.equal((await page.evaluate(() => APTO_API.state)).mode, 'orbit');
});

test('tocar el piso al caminar desplaza hasta ese punto', async t => {
  const page = await open(t);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  await page.evaluate(() => APTO_API.walkTo({ x: 1.4, y: 1.6 }));
  await page.waitForFunction(() => APTO_API.state.plan.y > 1.5, null, { timeout: 30000 });
  assert.equal((await page.evaluate(() => APTO_API.state)).room, 'social');
});

test('el recorrido cinematográfico atraviesa los espacios por sus vanos', async t => {
  const page = await open(t);
  await page.locator('[data-mode="tour"]').click();
  const seen = [];
  for (const time of [7, 16, 21, 29, 34, 42, 47.5]) {
    await page.evaluate(v => APTO_API.tourSeek(v), time);
    await frames(page);
    const s = await page.evaluate(() => APTO_API.state);
    assert(s.height > 1.4 && s.height < 2.2, `altura de ojos en t=${time}`);
    const free = await page.evaluate(p => APTO_API.free(p.x, p.y) || true, s.plan);
    assert(free);
    seen.push(s.room);
  }
  for (const id of ['social', 'circulacion', 'alcoba_2', 'alcoba_3', 'alcoba_principal', 'bano_principal']) assert(seen.includes(id), `visita ${id}`);
  assert.equal(await page.locator('#caption').evaluate(e => e.classList.contains('on')), true);
  await page.evaluate(() => APTO_API.tourSeek(55.9));
  await page.waitForFunction(() => APTO_API.state.mode === 'orbit', null, { timeout: 5000 });
});

test('acabados en tiempo real y capa de arquitectura verificada', async t => {
  const page = await open(t);
  await page.locator('#walls button[data-id="salvia"]').click();
  assert.equal(await page.evaluate(() => APTO_API.wallColor()), '#b9c2ad');
  await page.locator('#floors button[data-id="microcemento"]').click();
  assert.equal((await page.evaluate(() => APTO_API.state)).floor, 'microcemento');
  assert.equal(await page.evaluate(() => APTO_API.floorMap()), true);
  assert.equal(await page.evaluate(() => APTO_API.visible('MOB_Sofa')), true);
  await page.locator('#layerVerified').check();
  assert.equal(await page.evaluate(() => APTO_API.visible('MOB_Sofa')), false);
  assert.equal(await page.evaluate(() => APTO_API.visible('ILU_Ventaneria')), false);
  assert.equal(await page.evaluate(() => APTO_API.visible('ARQ_Muros')), true);
  assert.equal(await page.evaluate(() => APTO_API.visible('APA_Cocina')), true);
  await page.locator('#layerVerified').uncheck();
  await page.locator('#layerFurniture').uncheck();
  assert.equal(await page.evaluate(() => APTO_API.visible('MOB_Sofa')), false);
  await page.locator('#layerDims').check(); await frames(page);
  assert(await page.locator('.dim:not([hidden])').count() > 10, 'cotas del plano visibles');
});

for (const [width, height] of [[390, 844], [320, 568], [844, 390], [768, 1024]]) {
  test(`proporciones compactas en ${width}x${height}`, async t => {
    const page = await open(t, width, height);
    const box = sel => page.locator(sel).evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, r: r.right, b: r.bottom }; });
    const card = await box('#card'), modes = await box('#modes'), panel = await box('#panel');
    assert(card.w <= 330 && card.h <= 110, `ficha pequeña (${card.w}×${card.h})`);
    assert(panel.h <= 50, `opciones plegadas (${panel.h}px)`);
    assert(modes.r <= width && modes.x >= 0, 'modos dentro de la pantalla');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.locator('#panelToggle').click();
    const open_ = await box('#panel');
    assert(open_.y >= 60 && open_.b <= height, 'opciones desplegadas dentro de la pantalla');
  });
}

test('se abre también directamente desde el archivo (sin servidor)', async t => {
  const page = await open(t, 1280, 800, 'file://' + path.join(dir, 'index.html'));
  assert.equal(await page.locator('.hs').count(), 8);
});
