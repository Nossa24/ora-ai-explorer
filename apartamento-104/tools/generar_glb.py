"""Genera el modelo 3D (GLB) del apartamento 104 a partir de geometria-104.json.

Uso: python3 generar_glb.py <geometria-104.json> <salida.glb>

Blender no está disponible en el entorno de trabajo, así que el GLB se escribe
directamente (glTF 2.0 binario) con numpy. Cada nodo lleva en `extras`:
  - verificado: True  → planta tomada del DWG (muros, vanos, pisos, aparatos fijos).
  - verificado: False → elemento ilustrativo (mobiliario, hojas de puerta, vidrios, acabados).
Las alturas no existen en el DWG: se usan los SUPUESTOS declarados abajo y en `extras`.
"""
import json
import math
import struct
import sys

import numpy as np

g = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
W, H = g['envolvente_exterior'][2:]

# Supuestos de visualización (NO provienen del DWG)
SUP = {'altura_libre': 2.40, 'losa': 0.12, 'altura_puerta': 2.10, 'antepecho_ventana': 0.90, 'dintel_ventana': 2.10}
ALT = SUP['altura_libre']


def P(x, y):
    """Planta local (x este, y norte, m) → escena glTF (X este, Z sur, centrada)."""
    return x - W / 2, H / 2 - y


# ------------------------------------------------------------------ primitivas
class Mesh:
    def __init__(self):
        self.parts = {}   # material → [pos, nor, uv, idx]

    def _get(self, mat):
        return self.parts.setdefault(mat, [[], [], [], []])

    def quad(self, mat, a, b, c, d, n, uvs):
        pos, nor, uv, idx = self._get(mat)
        base = len(pos)
        pos += [a, b, c, d]; nor += [n] * 4; uv += uvs
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]

    def box(self, mat, x0, y0, z0, x1, y1, z1, faces='all'):
        """Caja alineada a ejes en coordenadas de escena (y vertical). UV en metros."""
        x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
        F = {
            'px': ([x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [1, 0, 0], [(z1, y0), (z0, y0), (z0, y1), (z1, y1)]),
            'nx': ([x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [-1, 0, 0], [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]),
            'py': ([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], [0, 1, 0], [(x0, z1), (x1, z1), (x1, z0), (x0, z0)]),
            'ny': ([x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1], [0, -1, 0], [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]),
            'pz': ([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [0, 0, 1], [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]),
            'nz': ([x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [0, 0, -1], [(-x1, y0), (-x0, y0), (-x0, y1), (-x1, y1)]),
        }
        for k, (a, b, c, d, n, uv) in F.items():
            if faces == 'all' or k in faces:
                self.quad(mat, a, b, c, d, n, [list(u) for u in uv])

    def cyl(self, mat, cx, y0, cz, r, h, seg=28, rz=None, cap=True):
        rz = rz or r
        pos, nor, uv, idx = self._get(mat)
        for i in range(seg):
            a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
            p = [(cx + r * math.cos(a), cz + rz * math.sin(a)) for a in (a0, a1)]
            n0 = [math.cos(a0), 0, math.sin(a0)]; n1 = [math.cos(a1), 0, math.sin(a1)]
            base = len(pos)
            pos += [[p[0][0], y0, p[0][1]], [p[1][0], y0, p[1][1]], [p[1][0], y0 + h, p[1][1]], [p[0][0], y0 + h, p[0][1]]]
            nor += [n0, n1, n1, n0]; uv += [[i / seg, 0], [(i + 1) / seg, 0], [(i + 1) / seg, h], [i / seg, h]]
            idx += [base, base + 2, base + 1, base, base + 3, base + 2]
            if cap:
                for yy, ny_ in ((y0 + h, 1), (y0, -1)):
                    b = len(pos)
                    pos += [[cx, yy, cz], [p[0][0], yy, p[0][1]], [p[1][0], yy, p[1][1]]]
                    nor += [[0, ny_, 0]] * 3; uv += [[cx, cz], [p[0][0], p[0][1]], [p[1][0], p[1][1]]]
                    idx += [b, b + 2, b + 1] if ny_ > 0 else [b, b + 1, b + 2]

    def sphere(self, mat, cx, cy, cz, r, sx=1, sy=1, sz=1, seg=18):
        pos, nor, uv, idx = self._get(mat)
        base = len(pos)
        for j in range(seg + 1):
            v = math.pi * j / seg
            for i in range(seg + 1):
                u = 2 * math.pi * i / seg
                n = [math.sin(v) * math.cos(u), math.cos(v), math.sin(v) * math.sin(u)]
                pos.append([cx + r * sx * n[0], cy + r * sy * n[1], cz + r * sz * n[2]]); nor.append(n); uv.append([i / seg, j / seg])
        for j in range(seg):
            for i in range(seg):
                a = base + j * (seg + 1) + i; b = a + seg + 1
                idx += [a, a + 1, b, a + 1, b + 1, b]


# ------------------------------------------------------------------ materiales (nombres estables: el visor los reemplaza en vivo)
MATS = {
    'muro': ([0.93, 0.91, 0.87, 1], 0.92, 0), 'muro_corte': ([0.18, 0.17, 0.16, 1], 0.9, 0), 'losa': ([0.42, 0.41, 0.40, 1], 0.95, 0),
    'piso_madera': ([0.73, 0.58, 0.42, 1], 0.62, 0), 'piso_ceramica': ([0.86, 0.85, 0.82, 1], 0.35, 0), 'cielo': ([0.97, 0.97, 0.95, 1], 0.95, 0),
    'vidrio': ([0.72, 0.84, 0.90, 0.28], 0.05, 0), 'marco': ([0.22, 0.22, 0.23, 1], 0.45, 0.6), 'puerta': ([0.84, 0.78, 0.69, 1], 0.6, 0),
    'meson': ([0.88, 0.87, 0.84, 1], 0.28, 0), 'gabinete': ([0.30, 0.29, 0.27, 1], 0.55, 0), 'acero': ([0.72, 0.73, 0.74, 1], 0.25, 0.9),
    'ceramica_blanca': ([0.96, 0.96, 0.95, 1], 0.18, 0), 'vidrio_ducha': ([0.85, 0.92, 0.95, 0.18], 0.05, 0),
    'tela_clara': ([0.80, 0.77, 0.72, 1], 0.95, 0), 'tela_acento': ([0.38, 0.43, 0.40, 1], 0.95, 0), 'madera_mueble': ([0.55, 0.40, 0.27, 1], 0.55, 0),
    'negro': ([0.08, 0.08, 0.09, 1], 0.35, 0.2), 'textil_tapete': ([0.74, 0.69, 0.60, 1], 1.0, 0), 'planta': ([0.25, 0.40, 0.27, 1], 0.8, 0),
    'ceramica_mate': ([0.55, 0.47, 0.40, 1], 0.85, 0), 'luz_calida': ([1.0, 0.92, 0.78, 1], 0.4, 0),
}

nodes = []   # (nombre, mesh, extras, translation, rotation_y_deg)


def node(name, mesh, verified, source, t=(0, 0, 0), ry=0.0, group='arquitectura'):
    nodes.append((name, mesh, {'verificado': verified, 'fuente': source, 'grupo': group}, t, ry))


# ------------------------------------------------------------------ ARQUITECTURA (planta del DWG; alturas supuestas)
m = Mesh()
for x0, y0, x1, y1 in g['muros_rectangulos']:
    a, b = P(x0, y0), P(x1, y1)
    m.box('muro', a[0], 0, a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
    m.box('muro_corte', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
node('ARQ_Muros', m, True, 'Capa MUROS (polilíneas cerradas); altura supuesta')

m = Mesh()
for d in g['puertas']:
    x0, y0, x1, y1 = d['rect']; a, b = P(x0, y0), P(x1, y1)
    m.box('muro', a[0], SUP['altura_puerta'], a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
    m.box('muro_corte', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
for w in g['ventanas']:
    a, b = P(w['x0'], w['y0']), P(w['x1'], w['y1'])
    m.box('muro', a[0], 0, a[1], b[0], SUP['antepecho_ventana'], b[1])
    m.box('muro', a[0], SUP['dintel_ventana'], a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
    m.box('muro_corte', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
node('ARQ_Dinteles_Antepechos', m, False, 'Vanos del DWG; alturas de dintel y antepecho supuestas')

for r in g['espacios']:
    m = Mesh()
    wet = r['id'] in ('bano_social', 'bano_principal', 'ropas')
    for x0, y0, x1, y1 in r['piso_rectangulos']:
        a, b = P(x0, y0), P(x1, y1)
        m.box('piso_ceramica' if wet else 'piso_madera', a[0], -0.02, a[1], b[0], 0, b[1], faces=['py'])
    node(f"ARQ_Piso_{r['id']}", m, True, f"Espacio {r['nombre']} ({r['area_neta_m2']} m² netos, planta del DWG)")
m = Mesh()
for x0, y0, x1, y1 in g['umbrales']:
    a, b = P(x0, y0), P(x1, y1)
    m.box('piso_madera', a[0], -0.02, a[1], b[0], 0, b[1], faces=['py'])
node('ARQ_Piso_umbrales', m, True, 'Umbrales de vanos del DWG')

m = Mesh()
a, b = P(0, 0), P(W, H)
m.box('losa', a[0], -SUP['losa'], a[1], b[0], -0.02, b[1])
node('ARQ_Losa', m, False, 'Losa ilustrativa: espesor no indicado en el DWG')

m = Mesh()
for r in g['espacios']:
    for x0, y0, x1, y1 in r['piso_rectangulos']:
        a, b = P(x0, y0), P(x1, y1)
        m.box('cielo', a[0], ALT - 0.005, a[1], b[0], ALT, b[1], faces=['ny'])
node('ARQ_Cielo', m, False, 'Cielo raso a altura supuesta', group='cielo')

# ------------------------------------------------------------------ VENTANAS Y PUERTAS (ilustrativas en vano verificado)
m = Mesh()
for w in g['ventanas']:
    a, b = P(w['x0'], w['y0']), P(w['x1'], w['y1'])
    y0, y1 = SUP['antepecho_ventana'], SUP['dintel_ventana']
    if w['fachada'] == 'sur':
        zc = (a[1] + b[1]) / 2
        m.box('marco', a[0], y0, zc - 0.03, b[0], y0 + 0.04, zc + 0.03); m.box('marco', a[0], y1 - 0.04, zc - 0.03, b[0], y1, zc + 0.03)
        m.box('marco', a[0], y0, zc - 0.03, a[0] + 0.04, y1, zc + 0.03); m.box('marco', b[0] - 0.04, y0, zc - 0.03, b[0], y1, zc + 0.03)
        n = max(1, round((b[0] - a[0]) / 1.0))
        for i in range(1, n):
            xm = a[0] + (b[0] - a[0]) * i / n; m.box('marco', xm - 0.02, y0, zc - 0.03, xm + 0.02, y1, zc + 0.03)
        m.box('vidrio', a[0] + 0.04, y0 + 0.04, zc - 0.006, b[0] - 0.04, y1 - 0.04, zc + 0.006)
    else:
        xc = (a[0] + b[0]) / 2
        m.box('marco', xc - 0.03, y0, a[1], xc + 0.03, y0 + 0.04, b[1]); m.box('marco', xc - 0.03, y1 - 0.04, a[1], xc + 0.03, y1, b[1])
        m.box('marco', xc - 0.03, y0, a[1], xc + 0.03, y1, a[1] - 0.04); m.box('marco', xc - 0.03, y0, b[1] + 0.04, xc + 0.03, y1, b[1])
        m.box('vidrio', xc - 0.006, y0 + 0.04, a[1] - 0.04, xc + 0.006, y1 - 0.04, b[1] + 0.04)
node('ILU_Ventaneria', m, False, 'Marcos y vidrios ilustrativos dentro de vanos verificados', group='ilustrativo')

# hojas de puerta: bisagra y sentido interpretados de las hojas dibujadas en el plano
hinges = {   # id: (bisagra local x, y, ángulo de la hoja abierta en grados, medido desde +x hacia +y de planta)
    'entrada': (0.178, 7.47, -80), 'bano_social': (2.775, 3.9, 75), 'alcoba_2': (5.275, 2.75, -105),
    'alcoba_3': (5.686, 3.75, -15), 'alcoba_principal': (5.55, 4.75, 15), 'bano_principal': (5.37, 4.9, 165),
}
for d in g['puertas']:
    hx, hy, ang = hinges[d['id']]
    wid = d['ancho_plano'] - 0.02
    m = Mesh()
    m.box('puerta', 0, 0, -0.02, wid, SUP['altura_puerta'] - 0.01, 0.02)
    m.cyl('acero', wid - 0.09, 1.0, 0.035, 0.012, 0.01, seg=10)
    t = P(hx, hy)
    node(f"ILU_Puerta_{d['id']}", m, False, f"Hoja ilustrativa {d['tipo']} {d['ancho_plano']} m; vano del DWG", t=(t[0], 0, t[1]), ry=ang, group='ilustrativo')

# ------------------------------------------------------------------ APARATOS FIJOS (posición del DWG, forma ilustrativa)
fx = {f['id']: f for f in g['aparatos']}


def R(f):
    x0, y0, x1, y1 = f['rect']; a, b = P(x0, y0), P(x1, y1)
    return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])


m = Mesh()
x0, z0, x1, z1 = R(fx['meson_cocina'])
m.box('gabinete', x0, 0.10, z0 + 0.03, x1, 0.86, z1)
m.box('negro', x0 + 0.02, 0, z0 + 0.08, x1 - 0.02, 0.10, z1)
m.box('meson', x0 - 0.01, 0.86, z0 - 0.01, x1, 0.90, z1)
sx, sz = P(*fx['lavaplatos']['centro'])
m.box('acero', sx - 0.22, 0.875, sz - 0.18, sx + 0.22, 0.905, sz + 0.18)
m.cyl('acero', sx, 0.9, sz - 0.2, 0.012, 0.28, seg=10)
e0, ez0, e1, ez1 = R(fx['estufa'])
m.box('negro', e0, 0.9, ez0, e1, 0.912, ez1)
for i in range(2):
    for j in range(2):
        m.cyl('acero', e0 + 0.15 + i * 0.3, 0.912, ez0 + 0.11 + j * 0.2, 0.06, 0.01, seg=16)
m.box('gabinete', x0, 1.45, z1 - 0.35, x1, 2.10, z1)
node('APA_Cocina', m, True, 'Mesón, lavaplatos y estufa: posición y dimensiones en planta del DWG; altura y acabado ilustrativos', group='aparatos')

for suf in ('principal', 'social'):
    m = Mesh()
    d0, dz0, d1, dz1 = R(fx[f'ducha_{suf}'])
    m.box('ceramica_blanca', d0, 0, dz0, d1, 0.04, dz1)
    if suf == 'principal':
        m.box('vidrio_ducha', d0, 0.04, dz1 - 0.01, d1 - 0.0, 2.0, dz1 + 0.0)   # mampara hacia el lavamanos
    else:
        m.box('vidrio_ducha', d0 - 0.005, 0.04, dz0, d0 + 0.005, 2.0, dz1)
    m.cyl('acero', (d0 + d1) / 2, 1.95, dz0 + 0.12, 0.09, 0.015, seg=18)
    t0, tz0, t1, tz1 = R(fx[f'sanitario_{suf}'])
    if suf == 'principal':   # tanque contra muro oeste, taza hacia el este
        m.box('ceramica_blanca', t0, 0.38, tz0 + 0.02, t0 + 0.18, 0.80, tz1 - 0.02)
        m.cyl('ceramica_blanca', t0 + 0.38, 0, (tz0 + tz1) / 2, 0.20, 0.40, rz=0.17)
    else:                    # tanque contra muro norte, taza hacia el sur
        m.box('ceramica_blanca', t0 + 0.02, 0.38, tz0, t1 - 0.02, 0.80, tz0 + 0.18)
        m.cyl('ceramica_blanca', (t0 + t1) / 2, 0, tz0 + 0.42, 0.17, 0.40, rz=0.21)
    l0, lz0, l1, lz1 = R(fx[f'lavamanos_{suf}'])
    m.box('gabinete', l0, 0.30, lz0, l1, 0.82, lz1)
    m.box('ceramica_blanca', l0, 0.82, lz0, l1, 0.86, lz1)
    m.cyl('acero', (l0 + l1) / 2, 0.86, (lz0 + lz1) / 2, 0.012, 0.18, seg=10)
    node(f'APA_Bano_{suf}', m, True, 'Ducha, sanitario y lavamanos: ubicación del DWG; forma ilustrativa', group='aparatos')

# ------------------------------------------------------------------ MOBILIARIO ILUSTRATIVO (no forma parte de la arquitectura verificada)
def furn(name, build):
    mm = Mesh(); build(mm); node(name, mm, False, 'Mobiliario de presentación ilustrativo', group='mobiliario')


def at(x, y):
    return P(x, y)


def sofa(mm):   # contra el muro oeste de la sala
    x0, z0 = at(0.20, 3.05); x1, z1 = at(1.05, 0.95)
    mm.box('tela_clara', x0, 0.12, z0, x1, 0.42, z1)
    mm.box('tela_clara', x0, 0.42, z0, x0 + 0.22, 0.85, z1)
    mm.box('tela_clara', x0, 0.42, z0, x1, 0.62, z0 + 0.16); mm.box('tela_clara', x0, 0.42, z1 - 0.16, x1, 0.62, z1)
    mm.box('tela_acento', x0 + 0.28, 0.42, z0 + 0.3, x0 + 0.42, 0.66, z0 + 0.62)
    for zz in (z0 + 0.05, z1 - 0.09):
        mm.box('madera_mueble', x0 + 0.05, 0, zz, x0 + 0.09, 0.12, zz + 0.04); mm.box('madera_mueble', x1 - 0.09, 0, zz, x1 - 0.05, 0.12, zz + 0.04)
furn('MOB_Sofa', sofa)


def sala(mm):
    x0, z0 = at(1.15, 1.75); x1, z1 = at(1.75, 2.35)
    mm.cyl('madera_mueble', (x0 + x1) / 2, 0.36, (z0 + z1) / 2, 0.32, 0.04)
    mm.cyl('negro', (x0 + x1) / 2, 0, (z0 + z1) / 2, 0.04, 0.36, seg=12)
    t0, tz0 = at(0.30, 3.10); t1, tz1 = at(2.30, 0.80)
    mm.box('textil_tapete', t0 + 0.6, 0, tz0, t1, 0.008, tz1)
    c0, cz0 = at(2.27, 2.80); c1, cz1 = at(2.60, 1.00)            # mueble TV contra muro este
    mm.box('madera_mueble', c0, 0.1, cz0, c1, 0.5, cz1)
    mm.box('negro', c1 - 0.06, 0.95, cz0 + 0.25, c1 - 0.03, 1.62, cz1 - 0.25)
    p0, pz0 = at(0.45, 0.45)
    mm.cyl('ceramica_mate', p0, 0, pz0, 0.16, 0.38, rz=0.16); mm.sphere('planta', p0, 0.8, pz0, 0.34, 1, 1.25, 1)
furn('MOB_Sala', sala)


def comedor(mm):
    cx, cz = at(1.40, 4.55)
    mm.box('madera_mueble', cx - 0.55, 0.72, cz - 0.40, cx + 0.55, 0.76, cz + 0.40)
    for dx in (-0.5, 0.46):
        for dz in (-0.35, 0.31):
            mm.box('madera_mueble', cx + dx, 0, cz + dz, cx + dx + 0.04, 0.72, cz + dz + 0.04)
    for dx in (-0.30, 0.30):
        for side in (-1, 1):
            zc = cz + side * 0.58
            mm.box('tela_acento', cx + dx - 0.2, 0.42, zc - 0.2, cx + dx + 0.2, 0.47, zc + 0.2)
            zb = zc + side * 0.18
            mm.box('tela_acento', cx + dx - 0.2, 0.47, min(zb, zb + side * 0.04), cx + dx + 0.2, 0.88, max(zb, zb + side * 0.04))
            for ex in (-0.17, 0.15):
                for ez in (-0.17, 0.15):
                    mm.box('negro', cx + dx + ex, 0, zc + ez, cx + dx + ex + 0.02, 0.42, zc + ez + 0.02)
    lx, lz = at(1.40, 4.55)
    mm.sphere('luz_calida', lx, 1.75, lz, 0.17, 1, .55, 1); mm.cyl('negro', lx, 1.85, lz, 0.006, ALT - 1.85, seg=6)
furn('MOB_Comedor', comedor)


def bed(mm, x0l, y0l, x1l, y1l, head):
    a, b = at(x0l, y0l), at(x1l, y1l)
    x0, x1 = min(a[0], b[0]), max(a[0], b[0]); z0, z1 = min(a[1], b[1]), max(a[1], b[1])
    mm.box('madera_mueble', x0, 0.08, z0, x1, 0.30, z1)
    mm.box('tela_clara', x0 + 0.02, 0.30, z0 + 0.02, x1 - 0.02, 0.52, z1 - 0.02)
    if head == 'n':
        mm.box('madera_mueble', x0, 0, z0 - 0.06, x1, 1.05, z0)
        mm.box('tela_acento', x0 + 0.02, 0.52, z0 + 0.65, x1 - 0.02, 0.57, z1 - 0.02)
        for k in range(2 if (x1 - x0) > 1.2 else 1):
            px = x0 + 0.12 + k * ((x1 - x0) / 2) ; mm.box('tela_clara', px, 0.52, z0 + 0.08, px + min(0.6, (x1 - x0) - 0.24), 0.66, z0 + 0.42)
    elif head == 'e':
        mm.box('madera_mueble', x1, 0, z0, x1 + 0.06, 1.05, z1)
        mm.box('tela_acento', x0 + 0.02, 0.52, z0 + 0.02, x1 - 0.65, 0.57, z1 - 0.02)
        for k in range(2 if (z1 - z0) > 1.2 else 1):
            pz = z0 + 0.12 + k * ((z1 - z0) / 2); mm.box('tela_clara', x1 - 0.42, 0.52, pz, x1 - 0.08, 0.66, pz + min(0.6, (z1 - z0) - 0.24))
    elif head == 'w':
        mm.box('madera_mueble', x0 - 0.06, 0, z0, x0, 1.0, z1)
        mm.box('tela_acento', x0 + 0.62, 0.52, z0 + 0.02, x1 - 0.02, 0.57, z1 - 0.02)
        mm.box('tela_clara', x0 + 0.08, 0.52, z0 + 0.12, x0 + 0.42, 0.66, z1 - 0.12)


def nightstand(mm, xl, yl):
    x, z = at(xl, yl)
    mm.box('madera_mueble', x - 0.22, 0, z - 0.2, x + 0.22, 0.48, z + 0.2)
    mm.cyl('ceramica_mate', x, 0.48, z, 0.07, 0.22, seg=14); mm.cyl('luz_calida', x, 0.70, z, 0.13, 0.17, seg=18)


def alcoba_principal(mm):   # cama doble con cabecero contra muro norte
    bed(mm, 5.95, 5.40, 7.55, 7.45, 'n'); nightstand(mm, 5.68, 7.18); nightstand(mm, 7.75, 7.18)
    a, b = at(7.35, 3.95), at(7.95, 5.35)
    mm.box('madera_mueble', a[0], 0, b[1], b[0], 0.75, a[1])
    t0, tz0 = at(5.80, 5.0); t1, tz1 = at(7.70, 3.95)
    mm.box('textil_tapete', t0, 0, tz0, t1 - 0.4, 0.008, tz1)
furn('MOB_Alcoba_principal', alcoba_principal)


def alcoba_3(mm):           # cama doble, cabecero contra muro este
    bed(mm, 6.00, 0.95, 7.95, 2.55, 'e'); nightstand(mm, 7.72, 0.62); nightstand(mm, 7.72, 2.85)
    a, b = at(5.45, 0.15), at(5.95, 1.6)
    mm.box('madera_mueble', a[0], 0, b[1], b[0], 1.9, a[1])
furn('MOB_Alcoba_3', alcoba_3)


def alcoba_2(mm):           # cama sencilla contra muro oeste, escritorio junto a la ventana
    bed(mm, 2.775, 0.55, 3.775, 2.55, 'w')
    d0, dz0 = at(4.25, 0.70); d1, dz1 = at(5.25, 0.15)
    mm.box('madera_mueble', d0, 0.72, dz0, d1, 0.75, dz1)
    for ex in (d0 + 0.02, d1 - 0.06):
        mm.box('madera_mueble', ex, 0, dz0 + 0.02, ex + 0.04, 0.72, dz1 - 0.02)
    cx, cz = at(4.75, 1.05)
    mm.box('tela_acento', cx - 0.21, 0.44, cz - 0.21, cx + 0.21, 0.49, cz + 0.21); mm.box('tela_acento', cx - 0.21, 0.49, cz + 0.17, cx + 0.21, 0.92, cz + 0.21)
    mm.cyl('negro', cx, 0, cz, 0.03, 0.44, seg=10)
furn('MOB_Alcoba_2', alcoba_2)


def ropas(mm):
    a, b = at(3.30, 6.30), at(3.90, 6.95)
    mm.box('ceramica_blanca', a[0], 0, b[1], b[0], 0.85, a[1])
    mm.cyl('negro', (a[0] + b[0]) / 2, 0.25, a[1] - 0.001, 0.18, 0.002, seg=24, cap=False)
    c, d = at(2.80, 6.55), at(3.25, 6.95)
    mm.box('ceramica_blanca', c[0], 0.0, d[1], d[0], 0.85, c[1])
furn('MOB_Ropas', ropas)

# ------------------------------------------------------------------ escritura GLB
buf = bytearray(); views = []; accessors = []; meshes = []; gl_nodes = []; materials = []; mat_index = {}


def add_view(data, target):
    global buf
    while len(buf) % 4:
        buf += b'\0'
    off = len(buf); buf += data
    views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data), 'target': target})
    return len(views) - 1


def mat_id(name):
    if name not in mat_index:
        col, rough, metal = MATS[name]
        mt = {'name': name, 'pbrMetallicRoughness': {'baseColorFactor': col, 'roughnessFactor': rough, 'metallicFactor': metal}}
        if col[3] < 1:
            mt['alphaMode'] = 'BLEND'; mt['doubleSided'] = True
        if name == 'luz_calida':
            mt['emissiveFactor'] = [1.0, 0.82, 0.55]
        mat_index[name] = len(materials); materials.append(mt)
    return mat_index[name]


for name, mesh, extras, t, ry in nodes:
    prims = []
    for mname, (pos, nor, uv, idx) in mesh.parts.items():
        if not idx:
            continue
        p = np.array(pos, np.float32); n = np.array(nor, np.float32); u = np.array(uv, np.float32)
        ln = np.linalg.norm(n, axis=1, keepdims=True); n = n / np.where(ln == 0, 1, ln)
        it = np.array(idx, np.uint32)
        vp, vn, vu, vi = (add_view(a.tobytes(), 34962) for a in (p, n, u)), None, None, None
        vp, vn, vu = list(vp)
        vi = add_view(it.tobytes(), 34963)
        a0 = len(accessors)
        accessors += [
            {'bufferView': vp, 'componentType': 5126, 'count': len(p), 'type': 'VEC3', 'min': p.min(0).tolist(), 'max': p.max(0).tolist()},
            {'bufferView': vn, 'componentType': 5126, 'count': len(n), 'type': 'VEC3'},
            {'bufferView': vu, 'componentType': 5126, 'count': len(u), 'type': 'VEC2'},
            {'bufferView': vi, 'componentType': 5125, 'count': len(it), 'type': 'SCALAR'},
        ]
        prims.append({'attributes': {'POSITION': a0, 'NORMAL': a0 + 1, 'TEXCOORD_0': a0 + 2}, 'indices': a0 + 3, 'material': mat_id(mname)})
    if not prims:
        continue
    meshes.append({'name': name, 'primitives': prims})
    nd = {'name': name, 'mesh': len(meshes) - 1, 'extras': extras}
    if any(t):
        nd['translation'] = list(t)
    if ry:
        h = math.radians(ry) / 2
        nd['rotation'] = [0, math.sin(h), 0, math.cos(h)]
    gl_nodes.append(nd)

root = {'name': 'Apto_104_Torre_1', 'children': list(range(len(gl_nodes))),
        'extras': {'proyecto': g['proyecto'], 'torre': g['torre'], 'apartamento': g['apartamento'], 'supuestos_visualizacion': SUP,
                   'areas': g['areas'], 'pendientes': g['pendientes'], 'sistema': 'X este, Z sur, Y arriba; metros; centro = centro de la envolvente'}}
gl_nodes.append(root)
gltf = {'asset': {'version': '2.0', 'generator': 'ORA AI Explorer · generar_glb.py'}, 'scene': 0,
        'scenes': [{'name': 'Apartamento 104', 'nodes': [len(gl_nodes) - 1]}], 'nodes': gl_nodes, 'meshes': meshes,
        'materials': materials, 'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(buf)}]}
js = json.dumps(gltf, ensure_ascii=False, separators=(',', ':')).encode('utf8')
js += b' ' * ((4 - len(js) % 4) % 4)
while len(buf) % 4:
    buf += b'\0'
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II', len(buf), 0x004E4942)); f.write(buf)
print(OUT, len(gl_nodes) - 1, 'nodos', len(materials), 'materiales', round((len(js) + len(buf)) / 1024), 'KB')
