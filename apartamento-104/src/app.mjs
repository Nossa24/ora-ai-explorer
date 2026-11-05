// ORA AI · Apartamento 104, Torre 1 — visor 3D navegable.
// Planta (muros, vanos, espacios, aparatos) proviene del DWG vía geometria-104.json;
// alturas, acabados y mobiliario son ilustrativos y están marcados en el GLB (extras.verificado).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const DATA = window.APTO104;
const geo = DATA.geo;
// Propuesta de balcón: NO proviene del DWG; se muestra siempre rotulada como propuesta.
const PROP = DATA.propuesta || null;
let balcony = !!PROP;
const [, , W, H] = geo.envolvente_exterior;
const EYE = 1.6;
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = s => document.querySelector(s);

// planta local (x este, y norte) ⇄ escena (X este, Z sur)
const toScene = (x, y, h = 0) => new THREE.Vector3(x - W / 2, h, H / 2 - y);
const toPlan = v => ({ x: v.x + W / 2, y: H / 2 - v.z });

// ------------------------------------------------------------------ renderizador
const canvas = $('#scene');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
} catch (error) {
  $('#error').hidden = false; document.body.classList.remove('is-loading'); throw error;
}
renderer.setPixelRatio(Math.min(devicePixelRatio, innerWidth < 700 ? 1.6 : 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.92;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const navy = new THREE.Color('#050a14');
scene.background = navy;
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.45;

// cielo exterior suave, visible por las ventanas al caminar
function skyTexture() {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const x = c.getContext('2d'); const gr = x.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, '#8fa9c2'); gr.addColorStop(.45, '#d9e2e6'); gr.addColorStop(.5, '#efe4cf'); gr.addColorStop(.53, '#b8bea5'); gr.addColorStop(1, '#7f8a6c');
  x.fillStyle = gr; x.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 32, 16), new THREE.MeshBasicMaterial({ map: skyTexture(), side: THREE.BackSide, depthWrite: false }));
sky.visible = false; scene.add(sky);

const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 200);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.minDistance = 3.2; controls.maxDistance = 40; controls.maxPolarAngle = Math.PI * 0.46;
controls.target.set(0, 0.6, 0);

// luces: sol de la tarde por el sur-oeste (fachada con ventanas), cielo y rebote cálido
const hemi = new THREE.HemisphereLight('#fff3df', '#1d222b', 0.85); scene.add(hemi);
const sun = new THREE.DirectionalLight('#ffe6c2', 2.4);
sun.position.set(-6, 9, 8); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: 1, far: 30 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
scene.add(sun);
const interiorLights = new THREE.Group(); scene.add(interiorLights);
for (const r of geo.espacios) {
  const [x0, y0, x1, y1] = r.caja;
  const l = new THREE.PointLight('#ffd6a0', r.area_neta_m2 > 5 ? 1.5 : 0.8, 5, 2);
  l.position.copy(toScene((x0 + x1) / 2, (y0 + y1) / 2, 2.15)); interiorLights.add(l);
}
interiorLights.visible = false;

// suelo de contexto: un plano oscuro que recibe la sombra de la maqueta
const ground = new THREE.Mesh(new THREE.CircleGeometry(26, 64), new THREE.MeshStandardMaterial({ color: '#0b1220', roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.position.y = -0.125; ground.receiveShadow = true; scene.add(ground);

// ------------------------------------------------------------------ texturas procedurales (sin descargas)
function canvasTex(draw, size = 512, rep = 1) {
  const c = document.createElement('canvas'); c.width = c.height = size; draw(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(rep, rep); t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy()); return t;
}
const rnd = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(7);
const floorTex = {
  roble: canvasTex((x, n) => {           // tablas de 0,20 × 1,20 m en un mosaico de 1,2 m
    const plank = n / 6;
    for (let i = 0; i < 6; i++) {
      const off = (i % 2) * n / 2.4 + rnd() * 40;
      for (let k = -1; k < 2; k++) {
        const base = 170 + rnd() * 30; x.fillStyle = `rgb(${base},${base * .78},${base * .55})`;
        x.fillRect(i * plank, off + k * n, plank, n);
      }
      for (let j = 0; j < 90; j++) { x.fillStyle = `rgba(80,52,25,${.03 + rnd() * .05})`; x.fillRect(i * plank + rnd() * plank, 0, 1 + rnd() * 2, n); }
      x.fillStyle = 'rgba(60,40,20,.35)'; x.fillRect(i * plank, 0, 1.5, n); x.fillRect(i * plank, off, plank, 1.5);
    }
  }, 512, 1 / 1.2),
  porcelanato: canvasTex((x, n) => {     // losas de 0,60 m
    x.fillStyle = '#d9d2c4'; x.fillRect(0, 0, n, n);
    for (let j = 0; j < 2500; j++) { const v = 195 + rnd() * 40; x.fillStyle = `rgba(${v},${v * .97},${v * .9},.25)`; x.fillRect(rnd() * n, rnd() * n, 2 + rnd() * 6, 2 + rnd() * 6); }
    x.strokeStyle = 'rgba(120,110,95,.55)'; x.lineWidth = 2; x.strokeRect(1, 1, n / 2 - 1, n / 2 - 1); x.strokeRect(n / 2, 1, n / 2 - 1, n / 2 - 1); x.strokeRect(1, n / 2, n / 2 - 1, n / 2 - 1); x.strokeRect(n / 2, n / 2, n / 2 - 1, n / 2 - 1);
  }, 512, 1 / 1.2),
  microcemento: canvasTex((x, n) => {
    x.fillStyle = '#a9a69f'; x.fillRect(0, 0, n, n);
    for (let j = 0; j < 4000; j++) { const v = 150 + rnd() * 50; x.fillStyle = `rgba(${v},${v},${v * .97},.18)`; x.beginPath(); x.arc(rnd() * n, rnd() * n, 2 + rnd() * 14, 0, 7); x.fill(); }
  }, 512, 1 / 2),
};
const FLOORS = [
  { id: 'roble', label: 'Roble natural', color: '#ffffff', rough: .62, swatch: '#b88f62' },
  { id: 'porcelanato', label: 'Porcelanato arena', color: '#ffffff', rough: .32, swatch: '#d9d2c4' },
  { id: 'microcemento', label: 'Microcemento', color: '#ffffff', rough: .7, swatch: '#a9a69f' },
];
const WALLS = [
  { id: 'marfil', label: 'Marfil', color: '#ede6d8' }, { id: 'arena', label: 'Arena', color: '#e2d2b8' },
  { id: 'niebla', label: 'Gris niebla', color: '#cfd2cf' }, { id: 'salvia', label: 'Salvia', color: '#b9c2ad' },
];
const ceramicTex = canvasTex((x, n) => {
  x.fillStyle = '#e8e6e1'; x.fillRect(0, 0, n, n); x.strokeStyle = 'rgba(150,145,138,.6)'; x.lineWidth = 2;
  for (let i = 0; i <= 4; i++) { x.beginPath(); x.moveTo(i * n / 4, 0); x.lineTo(i * n / 4, n); x.stroke(); x.beginPath(); x.moveTo(0, i * n / 4); x.lineTo(n, i * n / 4); x.stroke(); }
}, 256, 1 / 1.2);

// ------------------------------------------------------------------ modelo
const mats = {};
const groups = { arquitectura: [], aparatos: [], ilustrativo: [], mobiliario: [], cielo: [], propuesta: [], propuesta_mobiliario: [], sin_balcon: [] };
let model = null;
const stats = { verificados: 0, ilustrativos: 0, nodos: [] };

function base64ToBuffer(b64) {
  const bin = atob(b64); const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}

new GLTFLoader().parse(base64ToBuffer(DATA.glb), '', gltf => {
  model = gltf.scene; scene.add(model);
  model.traverse(o => {
    if (o.userData && 'verificado' in o.userData) {
      (groups[o.userData.grupo] || groups.arquitectura).push(o);
      stats.nodos.push({ nombre: o.name, verificado: o.userData.verificado, grupo: o.userData.grupo });
      o.userData.verificado ? stats.verificados++ : stats.ilustrativos++;
    }
    if (o.isMesh) {
      const transparent = o.material.transparent;
      o.castShadow = !transparent && !/Cielo|Piso/.test(o.name);
      o.receiveShadow = true;
      mats[o.material.name] = o.material;
    }
  });
  mats.piso_ceramica && Object.assign(mats.piso_ceramica, { map: ceramicTex, color: new THREE.Color('#ffffff') });
  setFloor('roble'); setWall('marfil');
  groups.cielo.forEach(o => { o.visible = false; });
  buildHotspots(); buildDims(); buildTour(); applyLayers(); resetOrbit(true);
  document.body.classList.remove('is-loading');
  ready = true;
}, error => { console.error(error); $('#error').hidden = false; document.body.classList.remove('is-loading'); });

let ready = false;
let floorId = 'roble', wallId = 'marfil';
function setFloor(id) {
  const f = FLOORS.find(v => v.id === id); const m = mats.piso_madera; if (!f || !m) return;
  m.map = floorTex[id]; m.color.set(f.color); m.roughness = f.rough; m.needsUpdate = true; floorId = id;
  document.querySelectorAll('#floors button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.id === id)));
}
function setWall(id, hex) {
  const w = WALLS.find(v => v.id === id); const m = mats.muro; if (!m) return;
  m.color.set(hex || w.color); wallId = id;
  document.querySelectorAll('#walls button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.id === id)));
}
for (const f of FLOORS) {
  const b = document.createElement('button'); b.type = 'button'; b.dataset.id = f.id; b.title = 'Piso: ' + f.label; b.setAttribute('aria-label', 'Piso ' + f.label);
  b.style.background = f.swatch; b.addEventListener('click', () => setFloor(f.id)); $('#floors').append(b);
}
for (const w of WALLS) {
  const b = document.createElement('button'); b.type = 'button'; b.dataset.id = w.id; b.title = 'Muros: ' + w.label; b.setAttribute('aria-label', 'Muros ' + w.label);
  b.style.background = w.color; b.addEventListener('click', () => setWall(w.id)); $('#walls').append(b);
}

// ------------------------------------------------------------------ espacios: puntos de vista (elección de cámara, no del DWG)
const VIEWS = {
  social: { pos: [1.55, 0.75], look: [1.05, 7.2], orbit: [1.4, 3.8] },
  ropas: { pos: [1.7, 6.0], look: [3.6, 6.1], orbit: [3.4, 6.1] },
  circulacion: { pos: [3.0, 3.3], look: [5.9, 3.35], orbit: [4.2, 3.3] },
  bano_social: { pos: [3.15, 3.55], look: [3.6, 4.85], orbit: [3.7, 4.4] },
  alcoba_2: { pos: [5.0, 2.45], look: [2.9, 0.5], orbit: [4.0, 1.4] },
  alcoba_3: { pos: [5.95, 3.35], look: [7.5, 1.0], orbit: [6.7, 1.9] },
  alcoba_principal: { pos: [5.8, 4.2], look: [7.6, 6.9], orbit: [6.7, 5.7] },
  bano_principal: { pos: [5.0, 5.3], look: [4.55, 6.7], orbit: [4.7, 6.0] },
  balcon: { pos: [0.6, -0.25], look: [2.3, -1.3], orbit: [1.4, -0.8] },
};
const BALCON = PROP && { id: 'balcon', nombre: 'Balcón', area_neta_m2: PROP.area_util_m2, piso_rectangulos: [PROP.rect_util], propuesta: true };
const allRooms = () => (BALCON ? [...geo.espacios, BALCON] : geo.espacios);
const roomById = Object.fromEntries(allRooms().map(r => [r.id, r]));
const fmt = n => n.toFixed(2).replace('.', ',');
const fmtDim = n => (Math.abs(n * 100 - Math.round(n * 100)) > 1e-6 && Math.abs(n * 1000 - Math.round(n * 1000)) < 1e-6 ? n.toFixed(3) : n.toFixed(2)).replace('.', ',');   // 2,475 se muestra tal como en el plano
const roomName = r => (r.id === 'alcoba_2' ? 'Alcoba 2' : r.id === 'alcoba_3' ? 'Alcoba 3' : r.nombre);
function roomAt(p) {
  for (const r of allRooms()) if (r.propuesta && !balcony) continue; else for (const [x0, y0, x1, y1] of r.piso_rectangulos) if (p.x >= x0 && p.x <= x1 && p.y >= y0 && p.y <= y1) return r;
  return null;
}

const hotspots = [];
function buildHotspots() {
  const list = $('#rooms');
  for (const r of allRooms()) {
    const v = VIEWS[r.id];
    const hs = document.createElement('button'); hs.type = 'button'; hs.className = 'hs' + (r.propuesta ? ' prop' : ''); hs.dataset.room = r.id;
    hs.setAttribute('aria-label', `${roomName(r)}${r.propuesta ? ' propuesto' : ''}, ${fmt(r.area_neta_m2)} metros cuadrados`);
    hs.innerHTML = `<i></i><span>${roomName(r)}${r.propuesta ? ' · propuesta' : ''} · ${fmt(r.area_neta_m2)} m²</span>`;
    hs.addEventListener('click', e => { e.stopPropagation(); goRoom(r.id); });
    $('#hotspots').append(hs);
    hotspots.push({ el: hs, room: r, anchor: toScene(v.orbit[0], v.orbit[1], 1.05) });
    const li = document.createElement('li'); const b = document.createElement('button'); b.type = 'button'; b.dataset.room = r.id;
    if (r.propuesta) { li.className = 'prop'; b.title = 'Propuesta: no figura en los planos DWG'; }
    b.innerHTML = `${roomName(r)}${r.propuesta ? ' <small>propuesta</small>' : ''}<em>${fmt(r.area_neta_m2)} m²</em>`; b.addEventListener('click', () => goRoom(r.id));
    li.append(b); list.append(li);
  }
}

// ------------------------------------------------------------------ cotas del plano (capa COTAS del DWG)
const dimGroup = new THREE.Group(); dimGroup.visible = false; scene.add(dimGroup);
const dimLabels = [];
function buildDims() {
  const seen = new Set();
  const mat = new THREE.LineBasicMaterial({ color: '#f2e0b0', transparent: true, opacity: .85, depthTest: false });
  const add = (a, b, value) => {
    const key = [a.x, a.y, b.x, b.y].map(v => v.toFixed(2)).sort().join('|') + value;
    if (seen.has(key)) return; seen.add(key);
    const pa = toScene(a.x, a.y, 2.46), pb = toScene(b.x, b.y, 2.46);
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([pa, pb]), mat); line.renderOrder = 5; dimGroup.add(line);
    const el = document.createElement('span'); el.className = 'dim'; el.textContent = fmtDim(value); el.hidden = true; $('#labels').append(el);
    dimLabels.push({ el, pos: pa.clone().add(pb).multiplyScalar(.5) });
  };
  for (const d of geo.cotas) {
    if (d.medida < 0.7 || d.medida > 9) continue;
    const a = { x: d.a[0], y: d.a[1] }, b = { x: d.b[0], y: d.b[1] };
    const horiz = Math.abs(a.y - b.y) < Math.abs(a.x - b.x);
    const pb = horiz ? { x: b.x, y: a.y } : { x: a.x, y: b.y };   // la cota mide la proyección
    add(a, pb, d.medida);
  }
  add({ x: 0, y: -0.3 }, { x: W, y: -0.3 }, W);
  add({ x: W + 0.3, y: 0 }, { x: W + 0.3, y: H }, H);
  if (PROP) {   // medidas de la propuesta, rotuladas aparte
    const [x0, y0, x1, y1] = PROP.rect_util, n = dimLabels.length;
    add({ x: x0, y: y0 - 0.25 }, { x: x1, y: y0 - 0.25 }, PROP.ancho_util);
    add({ x: x1 + 0.25, y: y0 }, { x: x1 + 0.25, y: y1 }, PROP.fondo_util);
    for (const d of dimLabels.slice(n)) { d.prop = true; d.el.classList.add('prop'); }
    propDims.push(...dimGroup.children.slice(-2));
  }
}
const propDims = [];

// ------------------------------------------------------------------ capas
function applyLayers() {
  const verifiedOnly = $('#layerVerified').checked;
  const furniture = $('#layerFurniture').checked && !verifiedOnly;
  const bal = balcony && !verifiedOnly;
  groups.mobiliario.forEach(o => { o.visible = furniture; });
  groups.ilustrativo.forEach(o => { o.visible = !verifiedOnly; });
  for (const o of groups.arquitectura) if (o.userData.verificado === false) o.visible = !verifiedOnly;
  groups.propuesta.forEach(o => { o.visible = bal; });
  groups.propuesta_mobiliario.forEach(o => { o.visible = bal && furniture; });
  groups.sin_balcon.forEach(o => { o.visible = !bal && !verifiedOnly; });
  $('#layerFurniture').disabled = verifiedOnly;
  const lb = $('#layerBalcony'); if (lb) { lb.disabled = verifiedOnly; lb.checked = balcony; }
  document.body.classList.toggle('has-balcony', bal);
  document.querySelectorAll('[data-room="balcon"]').forEach(e => { e.closest('li') ? (e.closest('li').hidden = !bal) : e.classList.toggle('gone', !bal); });
  dimGroup.visible = $('#layerDims').checked && mode === 'orbit';
  propDims.forEach(l => { l.visible = bal; });
}
['#layerFurniture', '#layerDims', '#layerVerified'].forEach(s => $(s).addEventListener('change', applyLayers));
function setBalcony(on) {
  if (!PROP) return;
  balcony = !!on;
  if (!balcony && current === 'balcon') { markRoom('social'); if (mode === 'walk') goRoom('social'); }
  if (mode === 'tour') setMode('orbit');
  buildTour(); applyLayers();
}
$('#layerBalcony')?.addEventListener('change', e => setBalcony(e.target.checked));

// ------------------------------------------------------------------ cámara: vuelos suaves
let flight = null;
const ease = t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
function flyTo(pos, target, dur = 1.6, done) {
  if (reduce) dur = 0.01;
  flight = { p0: camera.position.clone(), t0: (mode === 'walk' ? lookTarget() : controls.target.clone()), p1: pos, t1: target, start: performance.now(), dur: dur * 1000, done };
}
function lookTarget() {
  return camera.position.clone().add(new THREE.Vector3(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)));
}
function resetOrbit(instant) {
  // encuadre: la maqueta completa, desplazada hacia la izquierda para no quedar bajo la ficha lateral
  const narrow = camera.aspect < 0.9;
  const vf = THREE.MathUtils.degToRad(camera.fov), hf = 2 * Math.atan(Math.tan(vf / 2) * camera.aspect);
  const fit = 6.1 / Math.sin(Math.min(vf, hf) / 2);
  const dir = new THREE.Vector3(0.52, 0.66, 0.54).normalize();
  const tgt = new THREE.Vector3(narrow ? -0.35 : 0.9, narrow ? -1.0 : 0.0, narrow ? 0.4 : 0.2);
  const pos = tgt.clone().add(dir.multiplyScalar(Math.min(fit, 34) * (narrow ? 1.05 : 0.86)));
  if (instant) { camera.position.copy(pos); controls.target.copy(tgt); camera.lookAt(tgt); controls.update(); }
  else flyTo(pos, tgt, 1.4);
}

let current = null;
function markRoom(id) {
  current = id;
  document.querySelectorAll('#rooms button').forEach(b => b.classList.toggle('on', b.dataset.room === id));
}
function caption(r) {
  if (!r) { $('#caption').classList.remove('on'); return; }
  $('#captionK').textContent = r.propuesta ? `Propuesta · ${fmt(r.area_neta_m2)} m² · no figura en los planos` : `Área neta ${fmt(r.area_neta_m2)} m²`;
  $('#captionT').textContent = roomName(r);
  $('#caption').classList.add('on');
}

function goRoom(id) {
  const r = roomById[id]; const v = VIEWS[id]; if (!r || !ready) return;
  if (r.propuesta && !(balcony && !$('#layerVerified').checked)) return;
  if (mode === 'tour') setMode('orbit');
  markRoom(id); caption(r); clearTimeout(captionTimer); captionTimer = setTimeout(() => caption(null), 2600);
  if (mode === 'walk') {
    const p = toScene(v.pos[0], v.pos[1], EYE), l = toScene(v.look[0], v.look[1], EYE - 0.15);
    flyTo(p, l, 1.4, () => { const d = l.clone().sub(p).normalize(); yaw = Math.atan2(d.x, -d.z); pitch = Math.asin(d.y); });
  } else {
    const c = toScene(v.orbit[0], v.orbit[1], 0.3);
    const off = new THREE.Vector3(1.9, 6.2, 3.4).multiplyScalar(camera.aspect < 0.9 ? 1.35 : 1);
    flyTo(c.clone().add(off), c, 1.5);
  }
}
let captionTimer = null;

// ------------------------------------------------------------------ caminar: colisiones con muros, ventanas y aparatos del DWG
const SALA_V = geo.ventanas.reduce((a, b) => (b.ancho > a.ancho ? b : a));
const baseObstacles = [
  ...geo.muros_rectangulos,
  ...geo.ventanas.filter(w => w !== SALA_V).map(w => [w.x0, w.y0, w.x1, w.y1]),
  ...geo.aparatos.filter(f => f.rect && f.tipo !== 'ducha').map(f => f.rect),
  ...geo.puertas.filter(d => d.id === 'entrada').map(d => d.rect),   // no se sale al corredor
];
const RADIUS = 0.22;
function obstaclesNow() {
  if (!(balcony && PROP && !$('#layerVerified').checked)) return [...baseObstacles, [SALA_V.x0, SALA_V.y0, SALA_V.x1, SALA_V.y1]];
  const [h0, h1] = PROP.acceso.hojas_cerradas;
  return [...baseObstacles, [h0, SALA_V.y0, h1, SALA_V.y1], [1.20, -1.10, 2.55, -0.60]];   // hojas cerradas y mesa del balcón
}
function onBalcony(x, y) {
  if (!(balcony && PROP && !$('#layerVerified').checked)) return false;
  const [x0, y0, x1] = PROP.rect_util;
  return x >= x0 + RADIUS && x <= x1 - RADIUS && y >= y0 + RADIUS && y < RADIUS + 0.01;
}
function free(x, y) {
  if (!onBalcony(x, y) && (x < RADIUS || x > W - RADIUS || y < RADIUS || y > H - RADIUS)) return false;
  return !obstaclesNow().some(([x0, y0, x1, y1]) => x > Math.min(x0, x1) - RADIUS && x < Math.max(x0, x1) + RADIUS && y > Math.min(y0, y1) - RADIUS && y < Math.max(y0, y1) + RADIUS);
}
function moveBy(dx, dy) {
  const p = toPlan(camera.position);
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dy) / 0.04));
  for (let i = 0; i < steps; i++) {
    if (free(p.x + dx / steps, p.y)) p.x += dx / steps;
    if (free(p.x, p.y + dy / steps)) p.y += dy / steps;
  }
  camera.position.copy(toScene(p.x, p.y, EYE));
}
let yaw = 0, pitch = -0.08;
const keys = new Set(); const pad = new Set();
addEventListener('keydown', e => {
  if (mode !== 'walk' || e.target.closest('input')) return;
  const k = e.key.toLowerCase();
  if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) { keys.add(k); e.preventDefault(); }
  if (k === 'escape') setMode('orbit');
});
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
addEventListener('blur', () => { keys.clear(); pad.clear(); });
document.querySelectorAll('#walkpad button').forEach(b => {
  const on = e => { e.preventDefault(); pad.add(b.dataset.move); b.setPointerCapture?.(e.pointerId); };
  const off = () => pad.delete(b.dataset.move);
  b.addEventListener('pointerdown', on); b.addEventListener('pointerup', off); b.addEventListener('pointercancel', off); b.addEventListener('lostpointercapture', off);
});
// mirar arrastrando; tocar el piso para caminar hasta ese punto
let drag = null;
canvas.addEventListener('pointerdown', e => {
  if (mode === 'tour') { setMode('orbit'); return; }
  if (mode !== 'walk') return;
  drag = { x: e.clientX, y: e.clientY, yaw, pitch, moved: false, id: e.pointerId };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', e => {
  if (!drag || e.pointerId !== drag.id) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (Math.hypot(dx, dy) > 6) drag.moved = true;
  const k = (e.pointerType === 'touch' ? 0.006 : 0.004);
  yaw = drag.yaw - dx * k; pitch = THREE.MathUtils.clamp(drag.pitch - dy * k, -1.1, 1.0);
});
const ray = new THREE.Raycaster();
canvas.addEventListener('pointerup', e => {
  if (!drag || e.pointerId !== drag.id) return;
  const wasTap = !drag.moved; drag = null;
  if (!wasTap || mode !== 'walk') return;
  const r = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const floors = []; model.traverse(o => { if (o.isMesh && (/^ARQ_Piso/.test(o.name) || (o.name === 'PROP_Balcon_losa' && o.parent?.visible !== false && o.visible))) floors.push(o); });
  const hit = ray.intersectObjects(floors, false)[0];
  if (hit) walkTo(toPlan(hit.point));
});
let walkTarget = null;
function walkTo(p) { walkTarget = p; }

// ------------------------------------------------------------------ recorrido cinematográfico (trayectoria por vanos reales)
const TOUR_BASE = [
  { p: [9.6, 9.0, 11.5], l: [4.05, 0.4, 3.8], t: 0, room: null },
  { p: [0.65, 3.2, 9.3], l: [0.65, 1.2, 6.8], t: 3.5, room: null },
  { p: [0.65, 1.6, 7.0], l: [1.3, 1.4, 4.5], t: 6.5, room: 'social' },          // entra por la puerta principal
  { p: [1.1, 1.6, 5.6], l: [2.2, 1.1, 7.3], t: 9.5, room: 'social' },           // cocina
  { p: [1.5, 1.6, 3.6], l: [1.0, 1.2, 0.0], t: 13, room: 'social' },            // comedor → sala y ventana
  { p: [1.7, 1.6, 1.4], l: [0.6, 1.0, 3.2], t: 16.5, room: 'social' },          // sala
  { p: [2.1, 1.6, 3.35], l: [5.6, 1.3, 3.35], t: 20, room: 'circulacion' },
  { p: [3.4, 1.6, 3.35], l: [3.2, 1.2, 4.9], t: 22.5, room: 'bano_social' },    // asoma al baño
  { p: [4.85, 1.6, 3.3], l: [4.85, 1.3, 1.5], t: 25, room: 'circulacion' },
  { p: [5.0, 1.6, 2.45], l: [2.9, 0.9, 0.5], t: 28, room: 'alcoba_2' },
  { p: [5.0, 1.6, 3.35], l: [6.5, 1.3, 3.35], t: 31, room: 'circulacion' },
  { p: [6.2, 1.6, 3.0], l: [7.5, 1.0, 1.0], t: 34, room: 'alcoba_3' },
  { p: [5.45, 1.6, 3.55], l: [5.6, 1.3, 5.6], t: 37, room: 'circulacion' },
  { p: [5.52, 1.6, 4.3], l: [7.0, 1.2, 6.2], t: 39, room: 'alcoba_principal' },  // cruza el vano de la alcoba principal
  { p: [5.8, 1.6, 4.2], l: [7.6, 0.9, 6.9], t: 41.5, room: 'alcoba_principal' },
  { p: [7.4, 1.6, 4.3], l: [5.2, 1.1, 5.4], t: 44.5, room: 'alcoba_principal' },  // mira hacia el baño
  { p: [5.2, 1.6, 5.3], l: [4.5, 1.1, 6.6], t: 47, room: 'bano_principal' },
  { p: [6.4, 2.0, 4.5], l: [5.0, 1.2, 3.0], t: 50.5, room: 'alcoba_principal' },
  { p: [12.0, 9.5, -2.0], l: [4.05, 0.4, 3.8], t: 56, room: null },
];
// con el balcón propuesto, el recorrido sale por la puerta-ventana de la sala y vuelve a entrar
const TOUR_BALCON = [
  { p: [0.9, 1.6, 0.6], l: [1.3, 1.1, -1.6], dt: 2.5, room: 'social' },
  { p: [1.0, 1.6, -0.75], l: [2.5, 1.0, -1.6], dt: 3, room: 'balcon' },
  { p: [1.05, 1.6, 0.9], l: [2.0, 1.3, 3.3], dt: 3.5, room: 'social' },
];
let TOUR = [], tourCurve, lookCurve, TOUR_LEN = 0;
function buildTour() {
  const withBal = balcony && PROP && !$('#layerVerified').checked;
  const list = []; let shift = 0;
  for (const k of TOUR_BASE) {
    list.push({ ...k, t: k.t + shift });
    if (withBal && k.t === 16.5) {
      let t = k.t;
      for (const b of TOUR_BALCON) { t += b.dt; list.push({ ...b, t }); }
      // la parada siguiente (circulación) llega 3 s después de volver a entrar a la sala
      shift = (t - k.t) + 3 - (TOUR_BASE[TOUR_BASE.indexOf(k) + 1].t - k.t);
    }
  }
  TOUR = list.map(k => ({ ...k, P: toScene(k.p[0], k.p[2], k.p[1]), L: toScene(k.l[0], k.l[2], k.l[1]) }));
  tourCurve = new THREE.CatmullRomCurve3(TOUR.map(k => k.P), false, 'centripetal');
  lookCurve = new THREE.CatmullRomCurve3(TOUR.map(k => k.L), false, 'centripetal');
  TOUR_LEN = TOUR[TOUR.length - 1].t;
}
let tourT = 0, tourRoom = undefined;
function tourParam(t) {   // tiempo → parámetro de curva (los nudos están equiespaciados en u)
  const n = TOUR.length - 1;
  let i = TOUR.findIndex((k, j) => j < n && t >= k.t && t <= TOUR[j + 1].t); if (i < 0) i = n - 1;
  const a = TOUR[i], b = TOUR[i + 1];
  const f = (t - a.t) / (b.t - a.t);
  return { u: (i + f * f * (3 - 2 * f)) / n, room: f < .5 ? a.room : b.room };
}

// panel plegable en teléfono
const toggle = $('#panelToggle'), body = $('#panelBody');
const compact = matchMedia('(max-width: 700px), (max-height: 560px), (max-width: 900px) and (orientation: portrait)');
function syncPanel() { if (compact.matches || $('#panel').classList.contains('folded')) body.hidden = toggle.getAttribute('aria-expanded') !== 'true'; else body.hidden = false; }
toggle.addEventListener('click', () => { toggle.setAttribute('aria-expanded', String(toggle.getAttribute('aria-expanded') !== 'true')); syncPanel(); });
compact.addEventListener('change', syncPanel); syncPanel();

// ------------------------------------------------------------------ modos
let mode = 'orbit';
const HINTS = {
  orbit: 'Arrastra para girar la maqueta · toca un punto para ver cada espacio',
  tour: 'Recorrido automático · toca la pantalla para tomar el control',
  walk: 'Arrastra para mirar · toca el piso para caminar · WASD o flechas',
};
function setMode(next) {
  if (!ready) return;
  const prev = mode; mode = next; flight = null; keys.clear(); pad.clear(); walkTarget = null;
  controls.enabled = next === 'orbit';
  document.querySelectorAll('#modes button').forEach(b => { const on = b.dataset.mode === next; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
  $('#walkpad').hidden = next !== 'walk';
  $('#hintTxt').textContent = HINTS[next];
  const inside = next !== 'orbit';
  groups.cielo.forEach(o => { o.visible = inside && next === 'walk'; });
  interiorLights.visible = inside; sky.visible = inside; ground.visible = !inside;
  scene.background = inside ? null : navy;
  canvas.style.cursor = next === 'walk' ? 'crosshair' : '';
  camera.fov = next === 'orbit' ? 42 : (camera.aspect < 0.9 ? 78 : 64); camera.updateProjectionMatrix();
  hemi.intensity = next === 'orbit' ? 0.85 : 0.42;
  scene.environmentIntensity = next === 'orbit' ? 0.45 : 0.22;
  renderer.toneMappingExposure = next === 'orbit' ? 0.92 : 0.82;
  // dentro del apartamento la arquitectura manda: la ficha de opciones se pliega
  if (next !== 'orbit' && !compact.matches) { body.hidden = true; toggle.setAttribute('aria-expanded', 'false'); }
  if (next === 'orbit' && !compact.matches) { body.hidden = false; }
  $('#panel').classList.toggle('folded', next !== 'orbit');
  if (next === 'orbit') { caption(null); if (prev !== 'orbit') resetOrbit(); }
  if (next === 'walk') {
    const v = VIEWS[current] || VIEWS.social;
    const p = toScene(v.pos[0], v.pos[1], EYE), l = toScene(v.look[0], v.look[1], EYE - 0.15);
    flyTo(p, l, prev === 'orbit' ? 1.8 : 0.01, () => { const d = l.clone().sub(p).normalize(); yaw = Math.atan2(d.x, -d.z); pitch = Math.asin(d.y); });
  }
  if (next === 'tour') {
    tourT = 0; tourRoom = undefined;
    if (reduce) { setMode('walk'); $('#hintTxt').textContent = 'Movimiento reducido: recorre los espacios con la lista'; return; }
  }
  applyLayers();
}
document.querySelectorAll('#modes button').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));



// ------------------------------------------------------------------ ciclo de render
function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();

const tmp = new THREE.Vector3();
function project(v, el, hideBehind = true) {
  tmp.copy(v).project(camera);
  const vis = tmp.z < 1 && Math.abs(tmp.x) < 1.05 && Math.abs(tmp.y) < 1.05;
  if (!vis && hideBehind) { el.style.visibility = 'hidden'; return false; }
  el.style.visibility = '';
  el.style.transform = `translate(${(tmp.x * .5 + .5) * innerWidth}px, ${(-tmp.y * .5 + .5) * innerHeight}px) translate(-50%, -50%)`;
  return true;
}
let frame = 0, last = performance.now();
const occl = new THREE.Raycaster();
function tick(now) {
  requestAnimationFrame(tick);
  const dt = Math.min(0.1, (now - last) / 1000); last = now; frame++;
  if (!ready) return;

  if (flight) {
    const k = Math.min(1, (now - flight.start) / flight.dur), e = ease(k);
    camera.position.lerpVectors(flight.p0, flight.p1, e);
    const t = flight.t0.clone().lerp(flight.t1, e);
    if (mode === 'walk') camera.lookAt(t); else { controls.target.copy(t); camera.lookAt(t); }
    if (k >= 1) { const done = flight.done; flight = null; done?.(); }
  } else if (mode === 'orbit') {
    controls.update();
  } else if (mode === 'tour') {
    tourT += dt;
    if (tourT >= TOUR_LEN) { setMode('orbit'); }
    else {
      const { u, room } = tourParam(tourT);
      camera.position.copy(tourCurve.getPoint(u)); camera.lookAt(lookCurve.getPoint(u));
      if (room !== tourRoom) { tourRoom = room; caption(room ? roomById[room] : null); if (room) markRoom(room); }
      groups.cielo.forEach(o => { o.visible = camera.position.y < 2.3; });
    }
  } else if (mode === 'walk') {
    const fwd = (keys.has('w') || keys.has('arrowup') || pad.has('f') ? 1 : 0) - (keys.has('s') || keys.has('arrowdown') || pad.has('b') ? 1 : 0);
    const side = (keys.has('d') ? 1 : 0) - (keys.has('a') ? 1 : 0);
    const turn = (keys.has('arrowright') || pad.has('r') ? 1 : 0) - (keys.has('arrowleft') || pad.has('l') ? 1 : 0);
    yaw += turn * dt * 1.6;
    const sp = 1.25 * dt;
    if (fwd || side) {
      walkTarget = null;
      const dx = (Math.sin(yaw) * fwd + Math.cos(yaw) * side) * sp, dz = (-Math.cos(yaw) * fwd + Math.sin(yaw) * side) * sp;
      moveBy(dx, -dz);
    } else if (walkTarget) {
      const p = toPlan(camera.position); const dx = walkTarget.x - p.x, dy = walkTarget.y - p.y, dist = Math.hypot(dx, dy);
      if (dist < 0.05) walkTarget = null;
      else {
        const s = Math.min(dist, sp * 1.2); const before = { ...p };
        moveBy(dx / dist * s, dy / dist * s);
        const after = toPlan(camera.position); if (Math.hypot(after.x - before.x, after.y - before.y) < 1e-4) walkTarget = null;
        const targetYaw = Math.atan2(dx, dy); yaw += Math.atan2(Math.sin(targetYaw - yaw), Math.cos(targetYaw - yaw)) * Math.min(1, dt * 3);
      }
    }
    camera.lookAt(lookTarget());
    const r = roomAt(toPlan(camera.position)); if (r && r.id !== current) { markRoom(r.id); caption(r); clearTimeout(captionTimer); captionTimer = setTimeout(() => caption(null), 2200); }
  }

  // puntos interactivos y cotas
  const camP = camera.position;
  for (const h of hotspots) {
    const show = mode !== 'tour' && !(mode === 'walk' && current === h.room.id);
    h.el.classList.toggle('off', !show);
    if (!show) continue;
    const anchor = mode === 'walk' ? toScene(VIEWS[h.room.id].orbit[0], VIEWS[h.room.id].orbit[1], 1.2) : h.anchor;
    if (!project(anchor, h.el)) continue;
    if (mode === 'walk' && frame % 12 === 0) {   // en primera persona solo se ven los espacios visibles desde aquí
      occl.set(camP, anchor.clone().sub(camP).normalize()); occl.far = anchor.distanceTo(camP) - 0.3;
      const walls = groups.arquitectura.filter(o => o.name === 'ARQ_Muros' || o.name === 'ARQ_Dinteles_Antepechos');
      h.blocked = occl.intersectObjects(walls, true).length > 0;
    }
    if (mode !== 'walk') h.blocked = false;
    h.el.classList.toggle('off', !!h.blocked);
    h.el.classList.toggle('near', mode === 'walk' || current === h.room.id);
  }
  for (const d of dimLabels) { d.el.hidden = !dimGroup.visible; if (dimGroup.visible) project(d.pos, d.el); }
  renderer.render(scene, camera);
}
requestAnimationFrame(tick);

// ------------------------------------------------------------------ API para pruebas y consola
window.APTO_API = {
  get ready() { return ready; },
  get state() {
    const p = toPlan(camera.position);
    const q = toPlan(controls.target);
    return { mode, balcony: balcony && !$('#layerVerified').checked, tourLen: TOUR_LEN, room: current, plan: { x: +p.x.toFixed(3), y: +p.y.toFixed(3) }, target: { x: +q.x.toFixed(3), y: +q.y.toFixed(3) }, height: +camera.position.y.toFixed(3), tour: +tourT.toFixed(2), floor: floorId, wall: wallId, flying: !!flight, frame };
  },
  get stats() { return { ...stats, materiales: Object.keys(mats) }; },
  setMode, goRoom, setFloor, setWall, walkTo, setBalcony,
  move: (dx, dy) => moveBy(dx, dy), free,
  wallColor: () => '#' + (mats.muro?.color.getHexString() || ''),
  floorMap: () => mats.piso_madera?.map === floorTex[floorId],
  visible: name => { let v = null; model?.traverse(o => { if (o.name === name) { v = true; let q = o; while (q) { if (!q.visible) v = false; q = q.parent; } } }); return v; },
  tourSeek: t => { tourT = t; },
  topView: () => { if (mode !== 'orbit') setMode('orbit'); flight = null; camera.position.set(0, 17 / Math.min(1, camera.aspect), 0.0001); controls.target.set(0, 0, 0); camera.lookAt(0, 0, 0); controls.update(); },
};
