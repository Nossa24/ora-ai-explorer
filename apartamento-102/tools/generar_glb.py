"""Genera el modelo 3D (GLB) de la PROPUESTA DE REDISTRIBUCIÓN del apartamento 102 (Torre 1).

Uso: python3 generar_glb.py <propuesta-102.json> <salida.glb>

REDISEÑO CONCEPTUAL / PROPUESTA COMERCIAL: no es planta verificada del proyecto.
Del DWG se conservan la envolvente (medianeros, corredor, fachada), los vanos de fachada, la puerta
de acceso y los ductos (nodo ARQ_Muros, categoria «verificado»). Los tabiques, baños, cocina, ropas y
puertas interiores son de la propuesta (categoria «propuesta», grupo «rediseno»). Mobiliario y
acabados son ilustrativos. Las primitivas y los materiales son los del modelo del apartamento 104.
"""
import json
import math
import struct
import sys

import numpy as np

g = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
PROP = g['balcon']                                                  # balcón propuesto (NO proviene del DWG)
SALA_V = next(w for w in g['ventanas'] if w['id'] == 'sala')       # ventana de la sala (2,449 m)
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

    def tris(self, mat, P_, N_, U_, T_):
        """Añade triángulos y corrige el sentido de cada uno según las normales de vértice."""
        pos, nor, uv, idx = self._get(mat)
        base = len(pos)
        pos += P_; nor += N_; uv += U_
        Pa = np.array(P_, float); Na = np.array(N_, float)
        for a, b, c in T_:
            gn = np.cross(Pa[b] - Pa[a], Pa[c] - Pa[a])
            if np.dot(gn, Na[a] + Na[b] + Na[c]) < 0:
                b, c = c, b
            idx += [base + a, base + b, base + c]

    def rbox(self, mat, x0, y0, z0, x1, y1, z1, r, k=2):
        """Caja de aristas redondeadas (radio r) en coordenadas de escena."""
        lo = np.array([min(x0, x1), min(y0, y1), min(z0, z1)]); hi = np.array([max(x0, x1), max(y0, y1), max(z0, z1)])
        c = (lo + hi) / 2; h = (hi - lo) / 2
        r = max(1e-4, min(r, h.min() * 0.98))
        off = [r * math.tan(math.pi / 4 * j / k) for j in range(k + 1)]
        def samples(hh):
            inner = hh - r
            if inner > 1e-6:
                return [-inner - o for o in reversed(off)] + [inner + o for o in off]
            return [-o for o in reversed(off)] + off[1:]
        S = [samples(h[i]) for i in range(3)]
        for ax in range(3):
            u_ax, v_ax = [a for a in range(3) if a != ax]
            for sg in (-1, 1):
                Ps, Ns, Us = [], [], []
                nu, nv = len(S[u_ax]), len(S[v_ax])
                for iu in range(nu):
                    for iv in range(nv):
                        v = np.zeros(3); v[ax] = sg * h[ax]; v[u_ax] = S[u_ax][iu]; v[v_ax] = S[v_ax][iv]
                        inner = np.clip(v, -(h - r), h - r)
                        d = v - inner; ln = np.linalg.norm(d); n = d / ln if ln > 1e-9 else np.eye(3)[ax] * sg
                        p = c + inner + n * r
                        Ps.append(p.tolist()); Ns.append(n.tolist()); Us.append([p[u_ax], p[v_ax]])
                T = []
                for iu in range(nu - 1):
                    for iv in range(nv - 1):
                        a = iu * nv + iv; b = a + nv
                        T += [(a, b, b + 1), (a, b + 1, a + 1)]
                self.tris(mat, Ps, Ns, Us, T)

    def cyl(self, mat, cx, y0, cz, r, h, seg=28, rz=None, cap=True):
        rz = rz or r
        pos, nor, uv, idx = self._get(mat)
        for i in range(seg):
            a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
            p = [(cx + r * math.cos(a), cz + rz * math.sin(a)) for a in (a0, a1)]
            n0 = [math.cos(a0) / r, 0, math.sin(a0) / rz]; n1 = [math.cos(a1) / r, 0, math.sin(a1) / rz]
            base = len(pos)
            pos += [[p[0][0], y0, p[0][1]], [p[1][0], y0, p[1][1]], [p[1][0], y0 + h, p[1][1]], [p[0][0], y0 + h, p[0][1]]]
            nor += [n0, n1, n1, n0]; uv += [[i / seg * 2 * math.pi * r, 0], [(i + 1) / seg * 2 * math.pi * r, 0], [(i + 1) / seg * 2 * math.pi * r, h], [i / seg * 2 * math.pi * r, h]]
            idx += [base, base + 2, base + 1, base, base + 3, base + 2]
            if cap:
                for yy, ny_ in ((y0 + h, 1), (y0, -1)):
                    b = len(pos)
                    pos += [[cx, yy, cz], [p[0][0], yy, p[0][1]], [p[1][0], yy, p[1][1]]]
                    nor += [[0, ny_, 0]] * 3; uv += [[cx, cz], [p[0][0], p[0][1]], [p[1][0], p[1][1]]]
                    idx += [b, b + 2, b + 1] if ny_ > 0 else [b, b + 1, b + 2]

    def cyl_axis(self, mat, c, axis, r, h, seg=28):
        """Cilindro con eje horizontal (axis 0 = X, 2 = Z de escena) que empieza en c y avanza h."""
        Ps, Ns, Us, T = [], [], [], []
        u_, v_ = [a for a in range(3) if a != axis]
        for i in range(seg + 1):
            t = 2 * math.pi * i / seg
            for k in (0, 1):
                p = list(c); p[axis] += h * k; p[u_] += r * math.cos(t); p[v_] += r * math.sin(t)
                n = [0, 0, 0]; n[u_] = math.cos(t); n[v_] = math.sin(t)
                Ps.append(p); Ns.append(n); Us.append([t * r, h * k])
        for i in range(seg):
            a = 2 * i
            T += [(a, a + 2, a + 3), (a, a + 3, a + 1)]
        for k in (0, 1):
            ci = len(Ps); p = list(c); p[axis] += h * k; n = [0, 0, 0]; n[axis] = 1 if k else -1
            Ps.append(p); Ns.append(n); Us.append([0, 0])
            for i in range(seg + 1):
                t = 2 * math.pi * i / seg; q = list(p); q[u_] += r * math.cos(t); q[v_] += r * math.sin(t)
                Ps.append(q); Ns.append(n); Us.append([math.cos(t) * r, math.sin(t) * r])
            T += [(ci, ci + 1 + i, ci + 2 + i) for i in range(seg)]
        self.tris(mat, Ps, Ns, Us, T)

    def lathe(self, mat, cx, y0, cz, prof, seg=32, sx=1.0, sz=1.0):
        """Superficie de revolución. prof = [(radio, altura)] de abajo arriba."""
        Ps, Ns, Us, T = [], [], [], []
        m = len(prof)
        segn = []
        for j in range(m):
            a = prof[max(0, j - 1)]; b = prof[min(m - 1, j + 1)]
            dr, dh = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dr, dh) or 1
            segn.append((dh / ln, -dr / ln))
        acc = 0.0
        for j in range(m):
            if j:
                acc += math.hypot(prof[j][0] - prof[j - 1][0], prof[j][1] - prof[j - 1][1])
            for i in range(seg + 1):
                t = 2 * math.pi * i / seg
                r, hh = prof[j]; nr, nh = segn[j]
                Ps.append([cx + r * sx * math.cos(t), y0 + hh, cz + r * sz * math.sin(t)])
                n = np.array([nr * math.cos(t) / sx, nh, nr * math.sin(t) / sz]); n /= (np.linalg.norm(n) or 1)
                Ns.append(n.tolist()); Us.append([i / seg * 2 * math.pi * max(r, 0.02), acc])
        for j in range(m - 1):
            for i in range(seg):
                a = j * (seg + 1) + i; b = a + seg + 1
                T += [(a, b, b + 1), (a, b + 1, a + 1)]
        T = [t for t in T if len({tuple(np.round(Ps[q], 7)) for q in t}) == 3]
        self.tris(mat, Ps, Ns, Us, T)

    def sphere(self, mat, cx, cy, cz, r, sx=1, sy=1, sz=1, seg=18):
        pos, nor, uv, idx = self._get(mat)
        base = len(pos)
        for j in range(seg + 1):
            v = math.pi * j / seg
            for i in range(seg + 1):
                u = 2 * math.pi * i / seg
                n = [math.sin(v) * math.cos(u), math.cos(v), math.sin(v) * math.sin(u)]
                pos.append([cx + r * sx * n[0], cy + r * sy * n[1], cz + r * sz * n[2]])
                nn = np.array([n[0] / sx, n[1] / sy, n[2] / sz]); nn /= (np.linalg.norm(nn) or 1)
                nor.append(nn.tolist()); uv.append([i / seg, j / seg])
        for j in range(seg):
            for i in range(seg):
                a = base + j * (seg + 1) + i; b = a + seg + 1
                idx += [a, a + 1, b, a + 1, b + 1, b]

    def drape(self, mat, a, b, z0, z1, depth, folds, steps_per_fold=8):
        """Cortina plisada entre los puntos de escena a=(x,z) y b=(x,z); `depth` = amplitud del pliegue."""
        ax, az = a; bx, bz = b
        L = math.hypot(bx - ax, bz - az); tx, tz = (bx - ax) / L, (bz - az) / L; nx, nz = -tz, tx
        n = max(2, int(folds * steps_per_fold))
        Ps, Ns, Us, T = [], [], [], []
        for i in range(n + 1):
            s = i / n; ph = 2 * math.pi * folds * s
            off = depth * 0.5 * math.sin(ph); dd = depth * 0.5 * math.cos(ph) * 2 * math.pi * folds / L
            x = ax + tx * L * s + nx * off; zz = az + tz * L * s + nz * off
            nrm = np.array([nx - tx * dd, 0, nz - tz * dd]); nrm /= np.linalg.norm(nrm)
            for y in (z0, z1):
                Ps.append([x, y, zz]); Ns.append(nrm.tolist()); Us.append([L * s, y])
        for i in range(n):
            q = 2 * i
            T += [(q, q + 2, q + 3), (q, q + 3, q + 1)]
        self.tris(mat, Ps, Ns, Us, T)

    def panel(self, mat, corners, n):
        """Cuadrilátero con UV 0..1 (cuadros, pantallas)."""
        self.quad(mat, *corners, n, [[0, 0], [1, 0], [1, 1], [0, 1]])


# ------------------------------------------------------------------ materiales (nombres estables: el visor los reemplaza en vivo)
# nombre: (color RGBA lineal aprox., rugosidad, metalicidad, opciones)
MATS = {
    'muro': ([0.93, 0.91, 0.87, 1], 0.92, 0, {}), 'muro_corte': ([0.18, 0.17, 0.16, 1], 0.9, 0, {}), 'losa': ([0.42, 0.41, 0.40, 1], 0.95, 0, {}),
    'piso_madera': ([0.73, 0.58, 0.42, 1], 0.62, 0, {}), 'piso_ceramica': ([0.86, 0.85, 0.82, 1], 0.35, 0, {}), 'cielo': ([0.97, 0.97, 0.95, 1], 0.95, 0, {}),
    'vidrio': ([0.72, 0.84, 0.90, 0.22], 0.04, 0, {}), 'marco': ([0.22, 0.22, 0.23, 1], 0.45, 0.6, {}), 'alfeizar': ([0.90, 0.89, 0.86, 1], 0.35, 0, {}),
    'carpinteria': ([0.84, 0.78, 0.69, 1], 0.55, 0, {}), 'marco_puerta': ([0.84, 0.78, 0.69, 1], 0.55, 0, {}), 'puerta_entrada': ([0.30, 0.24, 0.19, 1], 0.5, 0, {}),
    'guardaescoba': ([0.95, 0.94, 0.92, 1], 0.5, 0, {}),
    'meson': ([0.88, 0.87, 0.84, 1], 0.22, 0, {}), 'gabinete_cocina': ([0.70, 0.56, 0.40, 1], 0.5, 0, {}), 'salpicadero': ([0.92, 0.91, 0.88, 1], 0.2, 0, {}),
    'acero': ([0.72, 0.73, 0.74, 1], 0.28, 1.0, {}), 'cromo': ([0.85, 0.85, 0.86, 1], 0.08, 1.0, {}), 'electro': ([0.62, 0.63, 0.64, 1], 0.32, 0.9, {}),
    'vidrio_negro': ([0.02, 0.02, 0.025, 1], 0.06, 0.2, {}),
    'ceramica_blanca': ([0.96, 0.96, 0.95, 1], 0.12, 0, {}), 'vidrio_ducha': ([0.85, 0.92, 0.95, 0.14], 0.03, 0, {}),
    'revestimiento_bano': ([0.88, 0.86, 0.82, 1], 0.25, 0, {}), 'revestimiento_ropas': ([0.93, 0.93, 0.92, 1], 0.2, 0, {}),
    'mueble_bano': ([0.70, 0.56, 0.40, 1], 0.5, 0, {}), 'meson_bano': ([0.90, 0.89, 0.86, 1], 0.2, 0, {}), 'espejo_principal': ([0.95, 0.96, 0.97, 1], 0.02, 1.0, {}), 'espejo_social': ([0.95, 0.96, 0.97, 1], 0.02, 1.0, {}),
    'tela_sofa': ([0.78, 0.74, 0.68, 1], 0.95, 0, {}), 'tela_acento': ([0.55, 0.36, 0.26, 1], 0.95, 0, {}), 'tela_cama': ([0.94, 0.93, 0.90, 1], 0.92, 0, {}),
    'tela_cortina': ([0.92, 0.90, 0.85, 1], 0.95, 0, {'double': True}), 'tela_silla': ([0.62, 0.58, 0.52, 1], 0.95, 0, {}),
    'madera_mueble': ([0.62, 0.47, 0.32, 1], 0.5, 0, {}), 'laca_mueble': ([0.90, 0.89, 0.86, 1], 0.35, 0, {}),
    'metal_negro': ([0.06, 0.06, 0.065, 1], 0.4, 0.8, {}), 'laton': ([0.78, 0.62, 0.36, 1], 0.3, 1.0, {}),
    'textil_tapete': ([0.74, 0.69, 0.60, 1], 1.0, 0, {}), 'planta': ([0.20, 0.36, 0.20, 1], 0.7, 0, {'double': True}), 'planta_2': ([0.30, 0.45, 0.24, 1], 0.7, 0, {'double': True}),
    'maceta': ([0.55, 0.47, 0.40, 1], 0.85, 0, {}), 'ceramica_deco': ([0.86, 0.83, 0.77, 1], 0.4, 0, {}),
    'libro_a': ([0.55, 0.30, 0.22, 1], 0.8, 0, {}), 'libro_b': ([0.25, 0.32, 0.38, 1], 0.8, 0, {}), 'libro_c': ([0.86, 0.82, 0.72, 1], 0.8, 0, {}),
    'cuadro': ([1, 1, 1, 1], 0.85, 0, {}), 'pantalla': ([0.01, 0.01, 0.012, 1], 0.08, 0.1, {}),
    'luz_calida': ([1.0, 0.92, 0.78, 1], 0.4, 0, {'emissive': [1.0, 0.82, 0.55]}), 'pantalla_lampara': ([0.95, 0.90, 0.80, 1], 0.9, 0, {'double': True, 'emissive': [0.35, 0.27, 0.16]}),
    'piso_exterior': ([0.62, 0.60, 0.56, 1], 0.8, 0, {}), 'vidrio_baranda': ([0.80, 0.90, 0.93, 0.18], 0.03, 0, {}),
    'muro_corte_propuesta': ([0.42, 0.30, 0.18, 1], 0.9, 0, {}), 'espejo_vestier': ([0.95, 0.96, 0.97, 1], 0.03, 1.0, {}),
    'cesped_maceta': ([0.42, 0.48, 0.30, 1], 0.9, 0, {}), 'toalla': ([0.93, 0.92, 0.88, 1], 1.0, 0, {}),
}

nodes = []   # (nombre, mesh, extras, translation, rotation_y_deg)
CAT = {'arquitectura': 'verificado', 'aparatos': 'verificado', 'ilustrativo': 'ilustrativo', 'acabados': 'ilustrativo', 'mobiliario': 'ilustrativo',
       'cielo': 'provisional', 'propuesta': 'propuesta', 'propuesta_mobiliario': 'propuesta', 'sin_balcon': 'provisional'}


def node(name, mesh, verified, source, t=(0, 0, 0), ry=0.0, group='arquitectura', **extra):
    cat = extra.pop('categoria', None) or ('verificado' if verified else CAT.get(group, 'ilustrativo'))
    if group == 'arquitectura' and not verified:
        cat = 'provisional'
    nodes.append((name, mesh, {'verificado': verified, 'fuente': source, 'grupo': group, 'categoria': cat, **extra}, t, ry))



# ------------------------------------------------------------------ ayudas en coordenadas de planta (x este, y norte, z altura)
def B(m, mat, x0, y0, x1, y1, z0, z1, faces='all'):
    a, b = P(x0, y0), P(x1, y1); m.box(mat, a[0], z0, a[1], b[0], z1, b[1], faces)


def RB(m, mat, x0, y0, x1, y1, z0, z1, r, k=2):
    a, b = P(x0, y0), P(x1, y1); m.rbox(mat, a[0], z0, a[1], b[0], z1, b[1], r, k)


def CY(m, mat, x, y, r, z0, h, seg=24, ry=None, cap=True):
    c = P(x, y); m.cyl(mat, c[0], z0, c[1], r, h, seg, rz=ry, cap=cap)


def LA(m, mat, x, y, z0, prof, seg=32, sx=1.0, sy=1.0):
    c = P(x, y); m.lathe(mat, c[0], z0, c[1], prof, seg, sx, sy)


def SP(m, mat, x, y, z, r, sx=1, sy=1, sz=1, seg=14):
    c = P(x, y); m.sphere(mat, c[0], z, c[1], r, sx, sz, sy, seg)


def DR(m, mat, x0, y0, x1, y1, z0, z1, depth=0.08, folds=None):
    a, b = P(x0, y0), P(x1, y1)
    L = math.hypot(x1 - x0, y1 - y0)
    m.drape(mat, a, b, z0, z1, depth, folds or max(2, round(L / 0.11)))


def wall_quad(m, mat, side, x0, y0, x1, y1, z0, z1, uv01=False):
    """Cuadrilátero vertical sobre un muro. side: 'n','s','e','o' = hacia dónde mira la cara."""
    n = {'n': [0, 0, -1], 's': [0, 0, 1], 'e': [1, 0, 0], 'o': [-1, 0, 0]}[side]
    a, b = P(x0, y0), P(x1, y1)
    pa = [a[0], z0, a[1]]; pb = [b[0], z0, b[1]]; pc = [b[0], z1, b[1]]; pd = [a[0], z1, a[1]]
    L = math.hypot(x1 - x0, y1 - y0)
    uvs = [[0, 0], [1, 0], [1, 1], [0, 1]] if uv01 else [[0, z0], [L, z0], [L, z1], [0, z1]]
    gn = np.cross(np.subtract(pb, pa), np.subtract(pd, pa))
    if np.dot(gn, n) < 0:
        pa, pb, pc, pd = pb, pa, pd, pc; uvs = [uvs[1], uvs[0], uvs[3], uvs[2]]
    m.quad(mat, pa, pb, pc, pd, n, uvs)


ROOMS = {r['id']: r for r in g['espacios']}
WALLS = g['muros_rectangulos']


def in_wall(x, y):
    return any(x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6 for x0, y0, x1, y1 in WALLS)


def wall_runs(room_id, step=0.01):
    """Tramos del perímetro de un espacio que dan contra muro (excluye vanos de puertas y ventanas)."""
    rects = ROOMS[room_id]['piso_rectangulos']
    def inside_room(x, y):
        return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in rects)
    runs = []
    for x0, y0, x1, y1 in rects:
        for side, (ax, ay, bx, by, ox, oy) in {
            's': (x0, y0, x1, y0, 0, -0.03), 'n': (x0, y1, x1, y1, 0, 0.03),
            'o': (x0, y0, x0, y1, -0.03, 0), 'e': (x1, y0, x1, y1, 0.03, 0)}.items():
            L = math.hypot(bx - ax, by - ay); n = max(1, int(round(L / step)))
            cur = None
            for i in range(n + 1):
                t = i / n; x = ax + (bx - ax) * t; y = ay + (by - ay) * t
                ok = in_wall(x + ox, y + oy) and not inside_room(x + ox * 2, y + oy * 2)
                if ok and cur is None:
                    cur = t
                if (not ok or i == n) and cur is not None:
                    t1 = t if ok else (i - 1) / n
                    if t1 - cur > 0.02 / max(L, 1e-6):
                        runs.append((side, ax + (bx - ax) * cur, ay + (by - ay) * cur, ax + (bx - ax) * t1, ay + (by - ay) * t1))
                    cur = None
    return runs


face_of = {'s': 'n', 'n': 's', 'o': 'e', 'e': 'o'}   # muro al sur → la cara mira al norte


def clad(m, mat, room_id, z0, z1, inset=0.004):
    for side, xa, ya, xb, yb in wall_runs(room_id):
        dx, dy = {'s': (0, inset), 'n': (0, -inset), 'o': (inset, 0), 'e': (-inset, 0)}[side]
        wall_quad(m, mat, face_of[side], xa + dx, ya + dy, xb + dx, yb + dy, z0, z1)



rng = np.random.default_rng(104)


def plant(m, x, y, z0, h, spread, pot_r, pot_h, pot='maceta'):
    LA(m, pot, x, y, z0, [(pot_r * 0.78, 0), (pot_r, pot_h * 0.85), (pot_r * 1.03, pot_h), (pot_r * 0.95, pot_h)], seg=28)
    CY(m, 'cesped_maceta', x, y, pot_r * 0.94, z0 + pot_h - 0.03, 0.01, seg=24)
    for i in range(3):
        CY(m, 'madera_mueble', x + rng.uniform(-0.03, 0.03), y + rng.uniform(-0.03, 0.03), 0.008, z0 + pot_h, h * rng.uniform(0.5, 0.8), seg=6)
    for i in range(30):   # follaje en racimos ovalados
        a = rng.uniform(0, 2 * math.pi); hf = rng.uniform(0.3, 1.0); rr = spread * math.sqrt(rng.uniform(0.05, 1)) * (0.5 + 0.5 * math.sin(hf * math.pi))
        zz = z0 + pot_h + h * hf
        SP(m, 'planta' if i % 3 else 'planta_2', x + rr * math.cos(a), y + rr * math.sin(a), zz, (0.05 * spread / 0.3 + 0.02),
           sx=rng.uniform(0.8, 1.3), sy=rng.uniform(0.8, 1.3), sz=rng.uniform(0.8, 1.2), seg=7)


def books(m, x0, y, x1, z0, depth=0.20, along='x', facing=1):
    x = x0; mats_ = ['libro_a', 'libro_b', 'libro_c', 'libro_c', 'libro_b']
    i = 0
    while x < x1 - 0.03:
        t = rng.uniform(0.02, 0.045); hh = rng.uniform(0.18, 0.27)
        if along == 'x':
            B(m, mats_[i % 5], x, y, x + t, y + depth * facing, z0, z0 + hh)
        else:
            B(m, mats_[i % 5], y, x, y + depth * facing, x + t, z0, z0 + hh)
        x += t + 0.002; i += 1
        if i % 7 == 6:
            x += 0.12


def art(m, side, x0, y0, x1, y1, z0, z1, frame='metal_negro'):
    """Cuadro con marco delgado sobre un muro."""
    off = {'e': (0.02, 0), 'o': (-0.02, 0), 'n': (0, 0.02), 's': (0, -0.02)}[side]
    if side in ('e', 'o'):
        xw = x0
        B(m, frame, min(xw, xw + off[0]), y0 - 0.02, max(xw, xw + off[0]), y1 + 0.02, z0 - 0.02, z1 + 0.02)
        wall_quad(m, 'cuadro', side, xw + off[0] * 1.05, y1 if side == 'e' else y0, xw + off[0] * 1.05, y0 if side == 'e' else y1, z0, z1, uv01=True)
    else:
        yw = y0
        B(m, frame, x0 - 0.02, min(yw, yw + off[1]), x1 + 0.02, max(yw, yw + off[1]), z0 - 0.02, z1 + 0.02)
        wall_quad(m, 'cuadro', side, x0 if side == 's' else x1, yw + off[1] * 1.05, x1 if side == 's' else x0, yw + off[1] * 1.05, z0, z1, uv01=True)


def chair(m, cx, cy, facing, seat='tela_silla'):
    """Silla de comedor; facing = hacia dónde mira el usuario sentado ('n' o 's')."""
    s = 0.22
    for ex in (-1, 1):
        for ey in (-1, 1):
            CY(m, 'metal_negro', cx + ex * 0.18, cy + ey * 0.18, 0.012, 0, 0.45, seg=8)
    RB(m, seat, cx - s, cy - s, cx + s, cy + s, 0.43, 0.49, 0.025)
    by = cy - s if facing == 'n' else cy + s - 0.05
    RB(m, seat, cx - s + 0.01, by, cx + s - 0.01, by + 0.05, 0.50, 0.88, 0.025)
    for ex in (-1, 1):
        B(m, 'metal_negro', cx + ex * 0.18 - 0.006, by + 0.02, cx + ex * 0.18 + 0.006, by + 0.032, 0.45, 0.75)



def toilet(m, rect, tank_side):
    x0, y0, x1, y1 = rect
    if tank_side == 'o':   # tanque contra el muro oeste, taza hacia el este
        RB(m, 'ceramica_blanca', x0, y0 + 0.04, x0 + 0.17, y1 - 0.04, 0.40, 0.80, 0.03)
        RB(m, 'ceramica_blanca', x0 - 0.005, y0 + 0.03, x0 + 0.18, y1 - 0.03, 0.80, 0.83, 0.012, k=2)
        cx_, cy_ = x0 + 0.40, (y0 + y1) / 2; sxx, syy = 1.18, 0.9
        RB(m, 'ceramica_blanca', x0 + 0.12, cy_ - 0.13, x0 + 0.30, cy_ + 0.13, 0, 0.36, 0.06)
    else:                  # tanque contra el muro norte, taza hacia el sur
        RB(m, 'ceramica_blanca', x0 + 0.04, y1 - 0.17, x1 - 0.04, y1, 0.40, 0.80, 0.03)
        RB(m, 'ceramica_blanca', x0 + 0.03, y1 - 0.18, x1 - 0.03, y1 + 0.005, 0.80, 0.83, 0.012, k=2)
        cx_, cy_ = (x0 + x1) / 2, y1 - 0.40; sxx, syy = 0.9, 1.18
        RB(m, 'ceramica_blanca', cx_ - 0.13, y1 - 0.30, cx_ + 0.13, y1 - 0.12, 0, 0.36, 0.06)
    LA(m, 'ceramica_blanca', cx_, cy_, 0, [(0.11, 0), (0.12, 0.08), (0.15, 0.22), (0.175, 0.34), (0.18, 0.38), (0.17, 0.395)], seg=36, sx=sxx, sy=syy)
    LA(m, 'ceramica_blanca', cx_, cy_, 0.395, [(0.17, 0), (0.18, 0.012), (0.17, 0.028), (0.0, 0.03)], seg=36, sx=sxx, sy=syy)   # asiento cerrado
    if tank_side == 'o':
        CY(m, 'cromo', x0 + 0.09, (y0 + y1) / 2, 0.018, 0.83, 0.006, seg=14)
    else:
        CY(m, 'cromo', (x0 + x1) / 2, y1 - 0.09, 0.018, 0.83, 0.006, seg=14)


def vanity(m, rect, wall):
    """Mueble de lavamanos flotante con mesón y poceta de sobreponer; grifería desde el muro."""
    x0, y0, x1, y1 = rect
    RB(m, 'mueble_bano', x0 + 0.005, y0 + 0.005, x1 - 0.005, y1 - 0.005, 0.32, 0.80, 0.008, k=1)
    RB(m, 'meson_bano', x0, y0, x1, y1, 0.80, 0.825, 0.004, k=1)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    if wall == 'o':
        cx_ += 0.03
        B(m, 'cromo', x0 + 0.04, cy_ - 0.15, x0 + 0.05, cy_ + 0.15, 0.58, 0.595)       # tirador
    else:
        cy_ -= 0.03
        B(m, 'cromo', cx_ - 0.15, y0 - 0.01, cx_ + 0.15, y0, 0.58, 0.595)
    LA(m, 'ceramica_blanca', cx_, cy_, 0.825, [(0.12, 0), (0.17, 0.02), (0.19, 0.08), (0.195, 0.12), (0.185, 0.125), (0.17, 0.05), (0.03, 0.03)], seg=36, sx=1.0, sy=0.8)
    if wall == 'o':
        CY(m, 'cromo', x0 + 0.03, cy_, 0.012, 1.05, 0.05, seg=12)
        RB(m, 'cromo', x0 + 0.005, cy_ - 0.011, x0 + 0.17, cy_ + 0.011, 1.07, 1.09, 0.009, k=2)
    else:
        RB(m, 'cromo', cx_ - 0.011, y1 - 0.17, cx_ + 0.011, y1 - 0.005, 1.07, 1.09, 0.009, k=2)


def shower(m, rect, glass_side, opening):
    x0, y0, x1, y1 = rect
    RB(m, 'ceramica_blanca', x0, y0, x1, y1, 0, 0.035, 0.008, k=1)                        # plato de ducha
    B(m, 'acero', (x0 + x1) / 2 - 0.06, (y0 + y1) / 2 - 0.06, (x0 + x1) / 2 + 0.06, (y0 + y1) / 2 + 0.06, 0.035, 0.037)
    if glass_side == 's':      # mampara fija sobre el borde sur, entrada por el este
        gx1 = x1 - opening
        B(m, 'vidrio_ducha', x0, y0 + 0.01, gx1, y0 + 0.018, 0.035, 2.0)
        B(m, 'cromo', x0, y0 + 0.006, gx1, y0 + 0.022, 1.985, 2.0)
        B(m, 'cromo', gx1 - 0.012, y0 + 0.006, gx1, y0 + 0.022, 0.035, 2.0)
        hx, hy = (x0 + x1) / 2, y1 - 0.18; wall_y = y1
        RB(m, 'cromo', hx - 0.012, wall_y - 0.30, hx + 0.012, wall_y, 2.08, 2.10, 0.008, k=2)
        CY(m, 'cromo', hx, hy, 0.11, 2.065, 0.015, seg=32)
        RB(m, 'cromo', hx - 0.05, wall_y - 0.04, hx + 0.05, wall_y, 1.05, 1.15, 0.02)
        B(m, 'revestimiento_bano', x0 + 0.05, wall_y - 0.08, x0 + 0.35, wall_y - 0.002, 1.20, 1.21)   # repisa del nicho
    else:                      # mampara fija sobre el borde oeste, entrada por el norte
        gy1 = y1 - opening
        B(m, 'vidrio_ducha', x0 + 0.01, y0, x0 + 0.018, gy1, 0.035, 2.0)
        B(m, 'cromo', x0 + 0.006, y0, x0 + 0.022, gy1, 1.985, 2.0)
        B(m, 'cromo', x0 + 0.006, gy1 - 0.012, x0 + 0.022, gy1, 0.035, 2.0)
        hx, hy = x1 - 0.18, (y0 + y1) / 2; wall_x = x1
        RB(m, 'cromo', wall_x - 0.30, hy - 0.012, wall_x, hy + 0.012, 2.08, 2.10, 0.008, k=2)
        CY(m, 'cromo', hx, hy, 0.11, 2.065, 0.015, seg=32)
        RB(m, 'cromo', wall_x - 0.04, hy - 0.05, wall_x, hy + 0.05, 1.05, 1.15, 0.02)



# --- dormitorios
def bed(m, x0, y0, x1, y1, head, duvet='tela_cama', accent='tela_acento'):
    """Cama con base tapizada, colchón, duvet, almohadas y cabecero. head = muro del cabecero."""
    RB(m, 'madera_mueble', x0, y0, x1, y1, 0.06, 0.32, 0.02)
    for xx in (x0 + 0.08, x1 - 0.08):
        for yy in (y0 + 0.08, y1 - 0.08):
            CY(m, 'metal_negro', xx, yy, 0.015, 0, 0.06, seg=8)
    RB(m, 'tela_cama', x0 + 0.02, y0 + 0.02, x1 - 0.02, y1 - 0.02, 0.32, 0.52, 0.05)                  # colchón
    if head == 'e':
        RB(m, duvet, x0 - 0.01, y0 - 0.015, x1 - 0.42, y1 + 0.015, 0.36, 0.555, 0.04)                 # duvet
        RB(m, accent, x0 + 0.01, y0 - 0.02, x0 + 0.48, y1 + 0.02, 0.50, 0.575, 0.03)                  # pie de cama
        npil = 2 if (y1 - y0) > 1.2 else 1
        for k in range(npil):
            a = y0 + 0.08 + k * ((y1 - y0) - 0.16) / npil; b = a + ((y1 - y0) - 0.16) / npil - 0.04
            RB(m, 'tela_cama', x1 - 0.40, a, x1 - 0.08, b, 0.50, 0.66, 0.06)
            RB(m, accent, x1 - 0.50, a + 0.06, x1 - 0.38, b - 0.06, 0.54, 0.80, 0.06)
        RB(m, 'tela_sofa', x1, y0 - 0.06, x1 + 0.055, y1 + 0.06, 0.20, 1.15, 0.025)                   # cabecero tapizado
    elif head == 'o':
        RB(m, duvet, x0 + 0.42, y0 - 0.015, x1 + 0.01, y1 + 0.015, 0.36, 0.555, 0.04)
        RB(m, 'tela_cama', x0 + 0.08, y0 + 0.08, x0 + 0.40, y1 - 0.08, 0.50, 0.66, 0.06)
        RB(m, 'tela_sofa', x0 - 0.055, y0 - 0.04, x0, y1 + 0.04, 0.20, 1.0, 0.025)


def nightstand(m, x0, y0, x1, y1, lamp=True):
    RB(m, 'madera_mueble', x0, y0, x1, y1, 0.16, 0.52, 0.012, k=1)
    for xx in (x0 + 0.04, x1 - 0.04):
        for yy in (y0 + 0.04, y1 - 0.04):
            CY(m, 'metal_negro', xx, yy, 0.01, 0, 0.16, seg=6)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    if lamp:
        LA(m, 'ceramica_deco', cx_, cy_, 0.52, [(0.05, 0), (0.07, 0.05), (0.06, 0.15), (0.015, 0.2), (0.012, 0.3)], seg=20)
        LA(m, 'pantalla_lampara', cx_, cy_, 0.74, [(0.13, 0), (0.10, 0.18)], seg=24)


def wardrobe(m, x0, y0, x1, y1, front, h=2.25, doors=None):
    RB(m, 'laca_mueble', x0, y0, x1, y1, 0.0, h, 0.006, k=1)
    L = (x1 - x0) if front in ('n', 's') else (y1 - y0)
    n = doors or max(2, round(L / 0.55))
    for i in range(1, n):
        if front in ('n', 's'):
            xm = x0 + L * i / n; yy = y0 if front == 's' else y1
            B(m, 'metal_negro', xm - 0.002, yy - 0.003, xm + 0.002, yy + 0.003, 0.02, h - 0.02)
        else:
            ym = y0 + L * i / n; xx = x0 if front == 'o' else x1
            B(m, 'metal_negro', xx - 0.003, ym - 0.002, xx + 0.003, ym + 0.002, 0.02, h - 0.02)
    for i in range(n):   # tiradores verticales
        if front in ('n', 's'):
            xm = x0 + L * (i + 0.5) / n + (0.22 if i % 2 == 0 else -0.22) * (L / n) / 0.55
            yy = (y0 - 0.02) if front == 's' else y1
            B(m, 'laton', xm - 0.006, yy, xm + 0.006, yy + 0.02, 0.95, 1.35)
        else:
            ym = y0 + L * (i + 0.5) / n + (0.22 if i % 2 == 0 else -0.22) * (L / n) / 0.55
            xx = (x0 - 0.02) if front == 'o' else x1
            B(m, 'laton', xx, ym - 0.006, xx + 0.02, ym + 0.006, 0.95, 1.35)


def curtain(m, side, a, b, w=0.30, sheer=False):
    """Cortinas recogidas a ambos lados de una ventana. side = muro de la ventana."""
    z0, z1 = 0.02, ALT - 0.06
    if side == 's':
        y = 0.15 + 0.07
        DR(m, 'tela_cortina', a - 0.05, y, a + w - 0.05, y, z0, z1, 0.07); DR(m, 'tela_cortina', b - w + 0.05, y, b + 0.05, y, z0, z1, 0.07)
        a_, b_ = P(a - 0.10, y), P(b + 0.10, y)
        m.box('metal_negro', a_[0], z1 + 0.01, a_[1] - 0.008, b_[0], z1 + 0.026, a_[1] + 0.008)
    else:   # ventana en el muro este
        x = 7.95 - 0.07
        DR(m, 'tela_cortina', x, a - 0.05, x, a + w - 0.05, z0, z1, 0.07); DR(m, 'tela_cortina', x, b - w + 0.05, x, b + 0.05, z0, z1, 0.07)
        a_, b_ = P(x, a - 0.10), P(x, b + 0.10)
        m.box('metal_negro', a_[0] - 0.008, z1 + 0.01, a_[1], a_[0] + 0.008, z1 + 0.026, b_[1])



# ------------------------------------------------------------------ ARQUITECTURA: envolvente del DWG y tabiques de la PROPUESTA
ORIG = g['muros_origen']
HP = SUP['altura_puerta']


def node102(name, mesh, cat, source, group, **extra):
    nodes.append((name, mesh, {'verificado': cat == 'verificado', 'fuente': source, 'grupo': group, 'categoria': cat, **extra}, extra.pop('t', (0, 0, 0)) if False else (0, 0, 0), 0.0))


m = Mesh(); mp_ = Mesh()
for (x0, y0, x1, y1), o in zip(g['muros_rectangulos'], ORIG):
    a, b = P(x0, y0), P(x1, y1)
    tgt = m if o == 'dwg' else mp_
    tgt.box('muro', a[0], 0, a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
    tgt.box('muro_corte' if o == 'dwg' else 'muro_corte_propuesta', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
node102('ARQ_Muros', m, 'verificado', 'Envolvente del DWG: medianeros, muro del corredor, fachada y ductos; altura supuesta', 'arquitectura')
# dinteles de las puertas de la propuesta (y vano del vestier)
for d in [*g['puertas'], *g['vanos']]:
    if d.get('origen') == 'dwg':
        continue
    x0, y0, x1, y1 = d['rect']; a, b = P(x0, y0), P(x1, y1)
    mp_.box('muro', a[0], HP, a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
node102('PRO_Muros_interiores', mp_, 'propuesta', 'Tabiques de la propuesta de redistribución (no figuran en el DWG)', 'rediseno')

m = Mesh(); m_sala = Mesh()
ent = next(d for d in g['puertas'] if d['id'] == 'entrada')
x0, y0, x1, y1 = ent['rect']; a, b = P(x0, y0), P(x1, y1)
m.box('muro', a[0], HP, a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny']); m.box('muro_corte', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
for w in g['ventanas']:
    a, b = P(w['x0'], w['y0']), P(w['x1'], w['y1'])
    (m_sala if w is SALA_V else m).box('muro', a[0], 0, a[1], b[0], SUP['antepecho_ventana'], b[1])
    m.box('muro', a[0], SUP['dintel_ventana'], a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
    m.box('muro_corte', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
node102('ARQ_Dinteles_Antepechos', m, 'provisional', 'Vanos del DWG; alturas de dintel y antepecho supuestas', 'arquitectura')
node102('ILU_Antepecho_sala', m_sala, 'provisional', 'Antepecho supuesto de la ventana de la sala (se retira con el balcón propuesto)', 'sin_balcon')

WET = ('bano_social', 'bano_principal')
for r in g['espacios']:
    m = Mesh()
    for x0, y0, x1, y1 in r['piso_rectangulos']:
        a, b = P(x0, y0), P(x1, y1)
        m.box('piso_ceramica' if r['id'] in WET else 'piso_madera', a[0], -0.02, a[1], b[0], 0, b[1], faces=['py'])
    node102(f"ARQ_Piso_{r['id']}", m, 'propuesta', f"{r['nombre']} ({r['area_neta_m2']} m² netos) · espacio de la propuesta", 'arquitectura')
m = Mesh()
for x0, y0, x1, y1 in g['umbrales']:
    a, b = P(x0, y0), P(x1, y1)
    m.box('piso_madera', a[0], -0.02, a[1], b[0], 0, b[1], faces=['py'])
node102('ARQ_Piso_umbrales', m, 'propuesta', 'Umbrales de los vanos de la propuesta', 'arquitectura')
m = Mesh(); a, b = P(0, 0), P(W, H); m.box('losa', a[0], -SUP['losa'], a[1], b[0], -0.02, b[1])
node102('ARQ_Losa', m, 'provisional', 'Losa ilustrativa: espesor no indicado en el DWG', 'arquitectura')
m = Mesh()
for r in g['espacios']:
    for x0, y0, x1, y1 in r['piso_rectangulos']:
        a, b = P(x0, y0), P(x1, y1); m.box('cielo', a[0], ALT - 0.005, a[1], b[0], ALT, b[1], faces=['ny'])
node102('ARQ_Cielo', m, 'provisional', 'Cielo raso a altura supuesta', 'cielo')

# ------------------------------------------------------------------ ventanas, puertas y marcos
def window(m, w):
    a, b = P(w['x0'], w['y0']), P(w['x1'], w['y1'])
    y0, y1 = SUP['antepecho_ventana'], SUP['dintel_ventana']
    zc = (a[1] + b[1]) / 2
    m.box('marco', a[0], y0, zc - 0.035, b[0], y0 + 0.05, zc + 0.035); m.box('marco', a[0], y1 - 0.05, zc - 0.035, b[0], y1, zc + 0.035)
    m.box('marco', a[0], y0, zc - 0.035, a[0] + 0.05, y1, zc + 0.035); m.box('marco', b[0] - 0.05, y0, zc - 0.035, b[0], y1, zc + 0.035)
    n = max(1, round((b[0] - a[0]) / 1.0))
    for i in range(1, n):
        xm = a[0] + (b[0] - a[0]) * i / n; m.box('marco', xm - 0.025, y0, zc - 0.035, xm + 0.025, y1, zc + 0.035)
    m.box('vidrio', a[0] + 0.05, y0 + 0.05, zc - 0.005, b[0] - 0.05, y1 - 0.05, zc + 0.005)
    zi = min(a[1], b[1])
    m.box('alfeizar', a[0] - 0.03, y0 - 0.025, zi - 0.045, b[0] + 0.03, y0, zc - 0.035)


m = Mesh()
for w in g['ventanas']:
    if w is not SALA_V:
        window(m, w)
node102('ILU_Ventaneria', m, 'ilustrativo', 'Marcos y vidrios ilustrativos en vanos de fachada del DWG', 'ilustrativo')
m = Mesh(); window(m, SALA_V)
node102('ILU_Ventana_sala', m, 'provisional', 'Ventana ilustrativa de la sala en el vano de 2,449 m del DWG', 'sin_balcon')

for d in g['puertas']:
    ent = d['id'] == 'entrada'
    if d['tipo'] == 'batiente':
        hx, hy = d['bisagra']; ang = d['angulo']
        wid = d['ancho'] - 0.02; th = 0.025 if ent else 0.02; mat = 'puerta_entrada' if ent else 'carpinteria'
        m = Mesh()
        m.rbox(mat, 0, 0.005, -th, wid, HP - 0.01, th, 0.004, k=1)
        if ent:
            for yy in (0.55, 1.05, 1.55):
                m.box('metal_negro', 0.08, yy, -th - 0.002, wid - 0.08, yy + 0.008, th + 0.002)
        for s in (-1, 1):
            m.cyl('cromo', wid - 0.07, 1.0, s * (th + 0.012), 0.025, 0.006, seg=16)
            m.rbox('cromo', wid - 0.20, 0.99, s * (th + 0.025) - 0.009, wid - 0.06, 1.01, s * (th + 0.025) + 0.009, 0.008, k=2)
        t = P(hx, hy)
        ex_, ey_ = hx + wid * math.cos(math.radians(ang)), hy + wid * math.sin(math.radians(ang))
        seg = [round(hx, 3), round(hy, 3), round(ex_, 3), round(ey_, 3), 0.045]
        nodes.append((f"ILU_Puerta_{d['id']}", m, {'verificado': False, 'fuente': f"Hoja ilustrativa de {d['ancho']} m" + (' en el vano de acceso del DWG' if ent else ' (puerta de la propuesta)'),
                      'grupo': 'ilustrativo' if ent else 'rediseno', 'categoria': 'ilustrativo' if ent else 'propuesta', 'segmentos': [] if ent else [seg]},
                      (t[0], 0, t[1]), ang))
    else:   # corrediza
        x0, y0, x1, y1 = d['rect']; m = Mesh()
        yc = y0 - 0.025   # cara del hall
        if d['id'] == 'bano_social':   # corrediza de granero estacionada sobre el muro, a la derecha del vano
            B(m, 'carpinteria', x1 - 0.03, yc - 0.03, x1 + d['ancho'] + 0.02, yc, 0.01, HP)
            B(m, 'metal_negro', x0 - 0.05, yc - 0.035, x1 + d['ancho'] + 0.08, yc - 0.01, HP + 0.02, HP + 0.06)
            B(m, 'metal_negro', x1 + 0.03, yc - 0.06, x1 + 0.05, yc - 0.03, 0.85, 1.25)
        else:                          # de bolsillo: la hoja se guarda dentro del muro, solo se ve el canto
            B(m, 'carpinteria', x1 - 0.04, (y0 + y1) / 2 - 0.02, x1, (y0 + y1) / 2 + 0.02, 0.01, HP)
        node102(f"ILU_Puerta_{d['id']}", m, 'propuesta', f"Puerta corrediza de {d['ancho']} m (propuesta)", 'rediseno')

m = Mesh()
for d in [*g['puertas'], *g['vanos']]:
    x0, y0, x1, y1 = d['rect']; mat = 'marco_puerta'
    if (x1 - x0) > (y1 - y0):
        B(m, mat, x0, y0 - 0.012, x0 + 0.02, y1 + 0.012, 0, HP); B(m, mat, x1 - 0.02, y0 - 0.012, x1, y1 + 0.012, 0, HP)
        B(m, mat, x0, y0 - 0.012, x1, y1 + 0.012, HP - 0.02, HP)
        for yy in (y0 - 0.014, y1):
            B(m, mat, x0 - 0.06, yy, x0 + 0.005, yy + 0.014, 0, HP + 0.06); B(m, mat, x1 - 0.005, yy, x1 + 0.06, yy + 0.014, 0, HP + 0.06)
            B(m, mat, x0 - 0.06, yy, x1 + 0.06, yy + 0.014, HP - 0.005, HP + 0.06)
    else:
        B(m, mat, x0 - 0.012, y0, x1 + 0.012, y0 + 0.02, 0, HP); B(m, mat, x0 - 0.012, y1 - 0.02, x1 + 0.012, y1, 0, HP)
        B(m, mat, x0 - 0.012, y0, x1 + 0.012, y1, HP - 0.02, HP)
        for xx in (x0 - 0.014, x1):
            B(m, mat, xx, y0 - 0.06, xx + 0.014, y0 + 0.005, 0, HP + 0.06); B(m, mat, xx, y1 - 0.005, xx + 0.014, y1 + 0.06, 0, HP + 0.06)
            B(m, mat, xx, y0 - 0.06, xx + 0.014, y1 + 0.06, HP - 0.005, HP + 0.06)
node102('ILU_Marcos_puertas', m, 'ilustrativo', 'Marcos y molduras ilustrativos', 'ilustrativo')

# ------------------------------------------------------------------ acabados
m = Mesh()
for rid in ('bano_principal', 'bano_social'):
    clad(m, 'revestimiento_bano', rid, 0, 2.10)
wall_quad(m, 'revestimiento_ropas', 'e', 0.155, 5.42, 0.155, 6.43, 0.0, 1.74)   # fondo cerámico de la columna de ropas
wall_quad(m, 'salpicadero', 's', 1.55, 7.445, 2.95, 7.445, 0.90, 1.50)
node102('ILU_Revestimientos', m, 'ilustrativo', 'Revestimientos de baños (2,10 m), fondo de la columna de ropas y salpicadero de cocina', 'acabados')
m = Mesh()
for rid in ('social', 'hall', 'habitacion_2', 'principal', 'vestier', 'deposito'):
    for side, xa, ya, xb, yb in wall_runs(rid):
        t = 0.012
        if side == 's':
            B(m, 'guardaescoba', xa, ya, xb, ya + t, 0, 0.075)
        elif side == 'n':
            B(m, 'guardaescoba', xa, ya - t, xb, ya, 0, 0.075)
        elif side == 'o':
            B(m, 'guardaescoba', xa, ya, xa + t, yb, 0, 0.075)
        else:
            B(m, 'guardaescoba', xa - t, ya, xa, yb, 0, 0.075)
node102('ILU_Guardaescobas', m, 'ilustrativo', 'Guardaescobas ilustrativos', 'acabados')
m = Mesh()
DOWN = {'social': [(1.37, 1.0), (1.37, 2.3), (1.15, 3.75), (2.1, 5.6), (1.6, 6.4), (2.9, 6.8)], 'hall': [(3.4, 4.25), (4.6, 4.25)], 'habitacion_2': [(3.4, 1.8), (4.6, 1.8)],
        'principal': [(6.0, 1.2), (7.0, 4.1)], 'bano_principal': [(5.75, 5.6), (5.75, 7.0)], 'vestier': [(7.05, 5.9)], 'bano_social': [(4.22, 5.6)], 'deposito': [(3.1, 5.0)]}
for pts in DOWN.values():
    for x, y in pts:
        CY(m, 'cromo', x, y, 0.055, ALT - 0.012, 0.008, seg=20); CY(m, 'luz_calida', x, y, 0.042, ALT - 0.016, 0.006, seg=20)
node102('ILU_Luminarias', m, 'ilustrativo', 'Luminarias empotradas ilustrativas', 'cielo', puntos=DOWN)

# ------------------------------------------------------------------ APARATOS EN POSICIÓN PROPUESTA
fx = {f['id']: f for f in g['aparatos']}
MOBI = g['mobiliario']

m = Mesh()
def counter(m, x0, y0, x1, y1, front, doors):
    """Mueble bajo con mesón; front = lado del frente ('s' o 'e')."""
    if front == 's':
        B(m, 'metal_negro', x0 + 0.02, y0 + 0.06, x1, y1, 0, 0.10); B(m, 'gabinete_cocina', x0, y0 + 0.02, x1, y1, 0.10, 0.84)
        for i in range(doors):
            xa = x0 + (x1 - x0) * i / doors + 0.002; xb = x0 + (x1 - x0) * (i + 1) / doors - 0.002
            RB(m, 'gabinete_cocina', xa, y0, xb, y0 + 0.02, 0.10, 0.84, 0.004, k=1); B(m, 'acero', xa + 0.03, y0 - 0.012, xb - 0.03, y0, 0.80, 0.81)
        RB(m, 'meson', x0 - 0.002, y0 - 0.025, x1, y1, 0.84, 0.88, 0.006, k=2)
    else:
        B(m, 'metal_negro', x0, y0 + 0.02, x1 - 0.06, y1 - 0.02, 0, 0.10); B(m, 'gabinete_cocina', x0, y0, x1 - 0.02, y1, 0.10, 0.84)
        for i in range(doors):
            ya = y0 + (y1 - y0) * i / doors + 0.002; yb = y0 + (y1 - y0) * (i + 1) / doors - 0.002
            RB(m, 'gabinete_cocina', x1 - 0.02, ya, x1, yb, 0.10, 0.84, 0.004, k=1); B(m, 'acero', x1, ya + 0.03, x1 + 0.012, yb - 0.03, 0.80, 0.81)
        RB(m, 'meson', x0, y0, x1 + 0.025, y1, 0.84, 0.88, 0.006, k=2)
counter(m, *fx['meson_norte']['rect'], 's', 3)
# barra-península: muebles bajos hacia la cocina (norte) y voladizo de 0,30 m hacia la sala para dos banquetas
px0, py0, px1, py1 = fx['peninsula']['rect']; vol = fx['peninsula']['barra']['voladizo_sur']
B(m, 'metal_negro', px0, py0 + vol + 0.02, px1 - 0.06, py1 - 0.06, 0, 0.10)
B(m, 'gabinete_cocina', px0, py0 + vol, px1 - 0.04, py1 - 0.02, 0.10, 0.84)
for i in range(3):
    xa = px0 + (px1 - 0.04 - px0) * i / 3 + 0.002; xb = px0 + (px1 - 0.04 - px0) * (i + 1) / 3 - 0.002
    RB(m, 'gabinete_cocina', xa, py1 - 0.02, xb, py1, 0.10, 0.84, 0.004, k=1); B(m, 'acero', xa + 0.03, py1, xb - 0.03, py1 + 0.012, 0.80, 0.81)
RB(m, 'gabinete_cocina', px1 - 0.04, py0, px1, py1, 0.0, 0.84, 0.004, k=1)              # costado en cascada hacia el eje de circulación
B(m, 'gabinete_cocina', px0 + 0.02, py0 + vol - 0.02, px1 - 0.04, py0 + vol, 0.0, 0.84)  # panel de rodillas
RB(m, 'meson', px0, py0, px1, py1 + 0.02, 0.84, 0.88, 0.006, k=2)
sx_, sy_ = fx['lavaplatos']['centro']           # poceta en la península, grifería hacia la barra
B(m, 'acero', sx_ - 0.24, sy_ - 0.19, sx_ + 0.24, sy_ + 0.19, 0.879, 0.882)
B(m, 'vidrio_negro', sx_ - 0.21, sy_ - 0.16, sx_ + 0.21, sy_ + 0.16, 0.8825, 0.884)
B(m, 'acero', sx_ - 0.20, sy_ - 0.15, sx_ + 0.20, sy_ + 0.15, 0.883, 0.8845)
CY(m, 'cromo', sx_, sy_ - 0.21, 0.022, 0.88, 0.05, seg=16); CY(m, 'cromo', sx_, sy_ - 0.21, 0.012, 0.93, 0.30, seg=12)
RB(m, 'cromo', sx_ - 0.012, sy_ - 0.212, sx_ + 0.012, sy_ - 0.02, 1.21, 1.235, 0.01, k=2); CY(m, 'cromo', sx_, sy_ - 0.03, 0.013, 1.12, 0.10, seg=12)
ex0, ey0, ex1, ey1 = fx['estufa']['rect']
RB(m, 'vidrio_negro', ex0, ey0, ex1, ey1, 0.88, 0.888, 0.004, k=1)
for i in range(2):
    for j in range(2):
        cx_ = ex0 + 0.15 + i * 0.30; cy_ = ey0 + 0.11 + j * 0.20
        CY(m, 'metal_negro', cx_, cy_, 0.085 - 0.015 * j, 0.888, 0.0015, seg=28); CY(m, 'vidrio_negro', cx_, cy_, 0.07 - 0.015 * j, 0.8885, 0.0015, seg=28)
my0 = fx['meson_norte']['rect'][1]
B(m, 'electro', ex0 + 0.01, my0 - 0.004, ex1 - 0.01, my0 + 0.01, 0.16, 0.75); B(m, 'vidrio_negro', ex0 + 0.06, my0 - 0.006, ex1 - 0.06, my0, 0.24, 0.58)
B(m, 'acero', ex0 + 0.07, my0 - 0.035, ex1 - 0.07, my0 - 0.02, 0.65, 0.665)
node102('APA_Cocina', m, 'propuesta', 'Cocina en U de la propuesta: mesón norte con estufa y horno y barra-península de 2 puestos con lavaplatos', 'aparatos',
        huella=[fx['meson_norte']['rect'], fx['peninsula']['rect']])

def toilet2(m, rect, tank_side):
    """Sanitario suspendido con tanque en el muro indicado ('o' oeste, 'e' este)."""
    x0, y0, x1, y1 = rect; cy_ = (y0 + y1) / 2
    if tank_side == 'o':
        RB(m, 'ceramica_blanca', x0, y0 + 0.04, x0 + 0.14, y1 - 0.04, 0.0, 1.10, 0.02); bx = x0 + 0.40; sx_ = 1.18
        B(m, 'cromo', x0 + 0.14, cy_ - 0.09, x0 + 0.145, cy_ + 0.09, 0.95, 1.05)
    else:
        RB(m, 'ceramica_blanca', x1 - 0.14, y0 + 0.04, x1, y1 - 0.04, 0.0, 1.10, 0.02); bx = x1 - 0.40; sx_ = 1.18
        B(m, 'cromo', x1 - 0.145, cy_ - 0.09, x1 - 0.14, cy_ + 0.09, 0.95, 1.05)
    LA(m, 'ceramica_blanca', bx, cy_, 0.20, [(0.10, 0), (0.14, 0.06), (0.17, 0.16), (0.18, 0.20), (0.17, 0.215)], seg=36, sx=sx_, sy=0.9)
    LA(m, 'ceramica_blanca', bx, cy_, 0.415, [(0.17, 0), (0.18, 0.012), (0.17, 0.026), (0.0, 0.028)], seg=36, sx=sx_, sy=0.9)


def vanity_e(m, rect):
    x0, y0, x1, y1 = rect
    RB(m, 'mueble_bano', x0 + 0.005, y0 + 0.005, x1 - 0.005, y1 - 0.005, 0.32, 0.80, 0.008, k=1)
    RB(m, 'meson_bano', x0, y0, x1, y1, 0.80, 0.825, 0.004, k=1)
    cx_, cy_ = (x0 + x1) / 2 - 0.03, (y0 + y1) / 2
    B(m, 'cromo', x0 - 0.01, cy_ - 0.15, x0, cy_ + 0.15, 0.58, 0.595)
    LA(m, 'ceramica_blanca', cx_, cy_, 0.825, [(0.12, 0), (0.16, 0.02), (0.18, 0.08), (0.185, 0.12), (0.175, 0.125), (0.16, 0.05), (0.03, 0.03)], seg=36, sx=0.8, sy=1.0)
    RB(m, 'cromo', x1 - 0.17, cy_ - 0.011, x1 - 0.005, cy_ + 0.011, 1.07, 1.09, 0.009, k=2)


def vanity_doble_o(m, rect):
    x0, y0, x1, y1 = rect
    RB(m, 'mueble_bano', x0 + 0.005, y0 + 0.005, x1 - 0.005, y1 - 0.005, 0.30, 0.80, 0.008, k=1)
    for k_ in (1, 2):
        yy = y0 + (y1 - y0) * k_ / 3
        B(m, 'metal_negro', x1 - 0.004, yy - 0.002, x1 + 0.001, yy + 0.002, 0.32, 0.78)
    RB(m, 'meson_bano', x0, y0, x1, y1, 0.80, 0.83, 0.004, k=1)
    for k_ in (0.27, 0.73):
        cy_ = y0 + (y1 - y0) * k_; cx_ = (x0 + x1) / 2 + 0.03
        LA(m, 'ceramica_blanca', cx_, cy_, 0.83, [(0.12, 0), (0.16, 0.02), (0.18, 0.08), (0.185, 0.12), (0.175, 0.125), (0.16, 0.05), (0.03, 0.03)], seg=36, sx=1.0, sy=0.8)
        CY(m, 'cromo', x0 + 0.03, cy_, 0.012, 1.05, 0.05, seg=12); RB(m, 'cromo', x0 + 0.005, cy_ - 0.011, x0 + 0.17, cy_ + 0.011, 1.07, 1.09, 0.009, k=2)


m = Mesh()
toilet2(m, fx['sanitario_principal']['rect'], 'e')
vanity_doble_o(m, fx['lavamanos_principal']['rect'])
shower(m, fx['ducha_principal']['rect'], 's', 0.62)
node102('APA_Bano_principal', m, 'propuesta', 'Baño principal de la propuesta: ducha amplia de 1,78 m, doble lavamanos y sanitario suspendido', 'aparatos',
        huella=[fx['sanitario_principal']['rect'], fx['lavamanos_principal']['rect']])
m = Mesh()
toilet2(m, fx['sanitario_social']['rect'], 'o')
vanity_e(m, fx['lavamanos_social']['rect'])
shower(m, fx['ducha_social']['rect'], 's', 0.45)
node102('APA_Bano_social', m, 'propuesta', 'Baño social de la propuesta: ducha, sanitario suspendido y lavamanos', 'aparatos',
        huella=[fx['sanitario_social']['rect'], fx['lavamanos_social']['rect']])
m = Mesh()
cx0, cy0, cx1, cy1 = fx['columna_ropas']['rect']
B(m, 'gabinete_cocina', cx0, cy0, cx1, cy0 + 0.02, 0, 2.28); B(m, 'gabinete_cocina', cx0, cy1 - 0.02, cx1, cy1, 0, 2.28)   # costados
B(m, 'gabinete_cocina', cx0, cy0, cx1, cy1, 2.26, 2.28)                                                                      # techo
x0, y0, x1, y1 = fx['lavadora_secadora']['rect']
for (za, zb) in ((0.02, 0.86), (0.88, 1.72)):   # lavadora y secadora apiladas, frente al este
    RB(m, 'laca_mueble', x0, y0, x1, y1 - 0.02, za, zb, 0.02)
    c = P(x1, (y0 + y1) / 2)
    m.cyl_axis('cromo', [c[0] - 0.006, (za + zb) / 2 - 0.04, c[1]], 0, 0.19, 0.022, seg=40)
    m.cyl_axis('vidrio_negro', [c[0] - 0.012, (za + zb) / 2 - 0.04, c[1]], 0, 0.15, 0.012, seg=40)
    B(m, 'metal_negro', x1 - 0.004, y0 + 0.04, x1 + 0.003, y1 - 0.08, zb - 0.10, zb - 0.04)   # panel de mandos, por fuera del canto redondeado
a0, b0, a1, b1 = fx['lavadero']['rect']                                       # lavadero compacto con mueble
RB(m, 'laca_mueble', a0, b0, a1, b1, 0, 0.86, 0.01, k=1); RB(m, 'ceramica_blanca', a0, b0, a1 + 0.01, b1, 0.86, 0.90, 0.01, k=2)
B(m, 'vidrio_negro', a0 + 0.06, b0 + 0.05, a1 - 0.05, b1 - 0.05, 0.9, 0.902)
CY(m, 'cromo', a0 + 0.04, (b0 + b1) / 2, 0.012, 1.0, 0.16, seg=10); RB(m, 'cromo', a0 + 0.03, (b0 + b1) / 2 - 0.01, a0 + 0.18, (b0 + b1) / 2 + 0.01, 1.14, 1.16, 0.008, k=1)
B(m, 'gabinete_cocina', cx0, cy0 + 0.02, cx1 - 0.02, cy1 - 0.02, 1.74, 1.76)                                         # repisa
RB(m, 'gabinete_cocina', cx1 - 0.02, cy0 + 0.02, cx1, cy1 - 0.02, 1.78, 2.26, 0.004, k=1)                             # gabinete alto
B(m, 'toalla', cx0 + 0.05, cy0 + 0.08, cx1 - 0.10, cy0 + 0.45, 1.76, 1.86); B(m, 'libro_b', cx0 + 0.05, cy0 + 0.55, cx1 - 0.10, cy0 + 0.85, 1.76, 1.92)
for k_, (ya, yb, xo) in enumerate(((cy0 + 0.01, cy0 + 0.545, 0.03), (cy0 + 0.02, cy0 + 0.555, 0.0))):   # dos hojas corredizas, recogidas sobre el lavadero
    B(m, 'gabinete_cocina', cx1 + xo, ya, cx1 + xo + 0.02, yb, 0.02, 1.76)
    B(m, 'metal_negro', cx1 + xo + 0.02, yb - 0.06, cx1 + xo + 0.025, yb - 0.04, 0.6, 1.3)
B(m, 'metal_negro', cx1, cy0, cx1 + 0.055, cy1, 1.76, 1.78)                                                             # riel
node102('APA_Ropas', m, 'propuesta', 'Zona de ropas de la propuesta: columna integrada a la cocina junto al acceso, con lavadora-secadora apilada, lavadero, almacenamiento y puertas corredizas. Desagüe y ventilación pendientes de viabilidad.', 'aparatos',
        huella=[[cx0, cy0, cx1 + 0.055, cy1]])

# ------------------------------------------------------------------ MOBILIARIO ILUSTRATIVO
def furn(name, build, huella=(), nota='Mobiliario de presentación ilustrativo', group='mobiliario', **kw):
    mm = Mesh(); build(mm); node102(name, mm, 'ilustrativo' if group == 'mobiliario' else 'propuesta', nota, group, huella=[list(map(float, h)) for h in huella], **kw)


def sofa(m):
    x0, y0, x1, y1 = MOBI['sofa']
    for yy in (y0 + 0.08, y1 - 0.08):
        for xx in (x0 + 0.1, x1 - 0.1):
            CY(m, 'metal_negro', xx, yy, 0.016, 0, 0.10, seg=10)
    RB(m, 'tela_sofa', x0 + 0.02, y0 + 0.02, x1 - 0.02, y1 - 0.02, 0.10, 0.38, 0.04)
    RB(m, 'tela_sofa', x0 + 0.02, y0 + 0.02, x1 - 0.02, y0 + 0.20, 0.10, 0.63, 0.06); RB(m, 'tela_sofa', x0 + 0.02, y1 - 0.20, x1 - 0.02, y1 - 0.02, 0.10, 0.63, 0.06)
    RB(m, 'tela_sofa', x0 + 0.02, y0 + 0.20, x0 + 0.24, y1 - 0.20, 0.38, 0.78, 0.06)
    mid = (y0 + y1) / 2
    for a_, b_ in ((y0 + 0.205, mid - 0.004), (mid + 0.004, y1 - 0.205)):
        RB(m, 'tela_sofa', x0 + 0.26, a_, x1 - 0.03, b_, 0.38, 0.53, 0.05); RB(m, 'tela_sofa', x0 + 0.22, a_ + 0.01, x0 + 0.44, b_ - 0.01, 0.50, 0.88, 0.09)
    RB(m, 'tela_acento', x0 + 0.40, y0 + 0.24, x0 + 0.53, y0 + 0.66, 0.50, 0.86, 0.08); RB(m, 'tela_acento', x0 + 0.40, y1 - 0.62, x0 + 0.53, y1 - 0.24, 0.50, 0.84, 0.08)
    RB(m, 'tela_cama', x0 + 0.30, y1 - 0.60, x1 + 0.005, y1 - 0.16, 0.525, 0.55, 0.012, k=1)


furn('MOB_Sofa', sofa, [MOBI['sofa']])


def sala(m):
    x0, y0, x1, y1 = MOBI['mesa_centro']
    RB(m, 'madera_mueble', x0, y0, x1, y1, 0.37, 0.41, 0.02); RB(m, 'madera_mueble', x0 + 0.03, y0 + 0.03, x1 - 0.03, y1 - 0.03, 0.10, 0.12, 0.01, k=1)
    for xx in (x0 + 0.04, x1 - 0.04):
        for yy in (y0 + 0.04, y1 - 0.04):
            CY(m, 'metal_negro', xx, yy, 0.012, 0, 0.37, seg=8)
    books(m, x0 + 0.08, y0 + 0.20, x0 + 0.26, 0.41, depth=0.24, along='x')
    LA(m, 'ceramica_deco', (x0 + x1) / 2, y1 - 0.22, 0.41, [(0.05, 0), (0.08, 0.06), (0.06, 0.16), (0.035, 0.2), (0.04, 0.22)], seg=24)
    RB(m, 'textil_tapete', 0.30, 1.20, 1.80, 3.05, 0, 0.012, 0.005, k=1)
    a0, b0, a1, b1 = MOBI['tv']                     # televisor a ras del muro, sin mueble: libera el eje hacia el balcón
    RB(m, 'pantalla', a0 + 0.005, (b0 + b1) / 2 - 0.62, a1 - 0.005, (b0 + b1) / 2 + 0.62, 0.95, 1.66, 0.008, k=1)
    a0, b0, a1, b1 = MOBI['butaca']                 # butaca junto a la ventana
    RB(m, 'tela_sofa', a0, b0, a1, b1, 0.12, 0.42, 0.06); RB(m, 'tela_sofa', a0, b0, a1, b0 + 0.16, 0.42, 0.82, 0.07)
    RB(m, 'tela_sofa', a0, b0, a0 + 0.12, b1, 0.42, 0.62, 0.05); RB(m, 'tela_sofa', a1 - 0.12, b0, a1, b1, 0.42, 0.62, 0.05)
    for xx in (a0 + 0.06, a1 - 0.06):
        for yy in (b0 + 0.06, b1 - 0.06):
            CY(m, 'metal_negro', xx, yy, 0.015, 0, 0.12, seg=8)
    art(m, 'e', 0.152, 1.50, 0.152, 2.70, 1.15, 1.75)
    x, y = [(MOBI['lampara_sala'][i] + MOBI['lampara_sala'][i + 2]) / 2 for i in (0, 1)]
    CY(m, 'metal_negro', x, y, 0.13, 0, 0.02, seg=24); CY(m, 'metal_negro', x, y, 0.01, 0.02, 1.38, seg=8); LA(m, 'pantalla_lampara', x, y, 1.40, [(0.19, 0), (0.15, 0.26)], seg=28)


furn('MOB_Sala', sala, [MOBI[k] for k in ('mesa_centro', 'tv', 'lampara_sala', 'butaca')])


def barra(m):
    """Dos banquetas a 0,65 m frente al voladizo de la península y dos lámparas colgantes."""
    for cx in (0.62, 1.22):
        cy = 4.27
        CY(m, 'metal_negro', cx, cy, 0.19, 0, 0.012, seg=24); CY(m, 'metal_negro', cx, cy, 0.022, 0.012, 0.60, seg=10)
        CY(m, 'metal_negro', cx, cy, 0.16, 0.30, 0.008, seg=24, cap=False)
        RB(m, 'tela_silla', cx - 0.19, cy - 0.17, cx + 0.19, cy + 0.17, 0.60, 0.67, 0.03)
        RB(m, 'tela_silla', cx - 0.17, cy - 0.17, cx + 0.17, cy - 0.12, 0.67, 0.88, 0.025)
        CY(m, 'metal_negro', cx, 4.95, 0.004, 1.55, ALT - 1.55, seg=6)
        LA(m, 'metal_negro', cx, 4.95, 1.38, [(0.0, 0.18), (0.03, 0.175), (0.10, 0.06), (0.11, 0.0)], seg=28)
        SP(m, 'luz_calida', cx, 4.95, 1.40, 0.04, seg=10)
    LA(m, 'ceramica_deco', 0.40, 4.90, 0.88, [(0.09, 0), (0.12, 0.03), (0.13, 0.05), (0.0, 0.05)], seg=24)
    for i, (dx, dy) in enumerate(((-0.03, 0.02), (0.04, -0.02), (0.0, 0.05))):
        SP(m, 'planta_2' if i else 'ceramica_deco', 0.40 + dx, 4.90 + dy, 0.96, 0.04, seg=10)


furn('MOB_Barra', barra, [MOBI['banquetas']], nota='Banquetas y lámparas ilustrativas de la barra')


def deposito(m):
    x0, y0, x1, y1 = MOBI['estantes_deposito']
    for xx in (x0 + 0.01, x1 - 0.03):
        B(m, 'laca_mueble', xx, y1 - 0.42, xx + 0.02, y1 - 0.02, 0, 2.2)
    for zz in (0.05, 0.55, 1.05, 1.55, 2.05):
        B(m, 'laca_mueble', x0 + 0.01, y1 - 0.42, x1 - 0.01, y1 - 0.02, zz, zz + 0.02)
    for i, zz in enumerate((0.57, 1.07, 1.57)):
        for j in range(3):
            xa = x0 + 0.08 + j * 0.30
            B(m, ('libro_c', 'libro_b', 'laca_mueble')[(i + j) % 3], xa, y1 - 0.38, xa + 0.24, y1 - 0.06, zz, zz + 0.28)


furn('MOB_Deposito', deposito, [[2.62, 5.53, 3.58, 5.95]], nota='Estantería ilustrativa del depósito (antiguo cuarto de ropas)')


def cocina(m):
    x0, y0, x1, y1 = fx['meson_norte']['rect']
    RB(m, 'gabinete_cocina', x0, y1 - 0.34, x1, y1, 1.50, 2.28, 0.004, k=1)
    for xm in (x0 + 0.55, x1 - 0.6):
        B(m, 'metal_negro', xm - 0.002, y1 - 0.342, xm + 0.002, y1 - 0.338, 1.5, 2.28)
    B(m, 'luz_calida', x0 + 0.03, y1 - 0.30, x1 - 0.03, y1 - 0.28, 1.495, 1.5)
    ex0, ey0, ex1, ey1 = fx['estufa']['rect']
    RB(m, 'electro', ex0, y1 - 0.48, ex1, y1 - 0.34, 1.48, 1.50, 0.004, k=1)   # campana integrada bajo el gabinete
    n0, m0, n1, m1 = fx['nevera']['rect']            # nevera de columna, frente al sur
    RB(m, 'electro', n0, m0, n1 - 0.005, m1, 0.02, 1.86, 0.012, k=2)
    B(m, 'metal_negro', n0 + 0.01, m0 - 0.002, n1 - 0.015, m0 + 0.002, 1.18, 1.185)
    for zz in ((0.55, 1.05), (1.30, 1.75)):
        B(m, 'acero', n0 + 0.06, m0 - 0.03, n0 + 0.08, m0 - 0.01, *zz)
    RB(m, 'gabinete_cocina', n0, m0 + 0.05, n1 - 0.005, m1, 1.90, 2.28, 0.004, k=1)
    RB(m, 'madera_mueble', x0 + 0.06, y1 - 0.30, x0 + 0.40, y1 - 0.06, 0.88, 0.905, 0.01, k=1)
    LA(m, 'ceramica_deco', x1 - 0.25, y1 - 0.16, 0.88, [(0.05, 0), (0.06, 0.1), (0.055, 0.16), (0.0, 0.16)], seg=20)


furn('MOB_Cocina', cocina, [fx['nevera']['rect']], nota='Gabinetes superiores, campana, nevera y accesorios ilustrativos de la propuesta')


def habitacion_2(m):
    x0, y0, x1, y1 = MOBI['cama_2']
    bed(m, x0 + 0.06, y0, x1, y1, 'o')
    for k in ('noche_2a', 'noche_2b'):
        nightstand(m, *MOBI[k])
    wardrobe(m, *MOBI['armario_2'], 's')
    a0, b0, a1, b1 = MOBI['escritorio_2']
    RB(m, 'madera_mueble', a0, b0, a1, b1, 0.72, 0.75, 0.008, k=1)
    for xx in (a0 + 0.03, a1 - 0.05):
        B(m, 'metal_negro', xx, b0 + 0.03, xx + 0.02, b1 - 0.03, 0, 0.72)
    RB(m, 'laca_mueble', a1 - 0.40, b0 + 0.02, a1 - 0.04, b1 - 0.04, 0.50, 0.70, 0.008, k=1)
    LA(m, 'laton', a0 + 0.12, b0 + 0.25, 0.75, [(0.06, 0), (0.01, 0.02), (0.008, 0.35), (0.07, 0.42), (0.05, 0.46)], seg=18)
    c0, d0, c1, d1 = MOBI['silla_2']; cx, cy = (c0 + c1) / 2, (d0 + d1) / 2
    CY(m, 'metal_negro', cx, cy, 0.025, 0.06, 0.38, seg=10); CY(m, 'metal_negro', cx, cy, 0.2, 0.02, 0.04, seg=20)
    RB(m, 'tela_acento', cx - 0.2, cy - 0.17, cx + 0.2, cy + 0.17, 0.44, 0.50, 0.04); RB(m, 'tela_acento', cx - 0.19, cy + 0.12, cx + 0.19, cy + 0.17, 0.52, 0.90, 0.03)
    RB(m, 'textil_tapete', 3.35, 0.75, 4.95, 2.75, 0, 0.012, 0.005, k=1)
    art(m, 'e', 2.752, 1.35, 2.752, 2.15, 1.25, 1.80)
    curtain(m, 's', 4.25, 5.25, w=0.24)


furn('MOB_Habitacion_2', habitacion_2, [MOBI[k] for k in ('cama_2', 'noche_2a', 'noche_2b', 'armario_2', 'escritorio_2', 'silla_2')])


def principal(m):
    x0, y0, x1, y1 = MOBI['cama_p']
    bed(m, x0, y0, x1 - 0.06, y1, 'e')
    for k in ('noche_pa', 'noche_pb'):
        nightstand(m, *MOBI[k])
    a0, b0, a1, b1 = MOBI['butaca_p']
    RB(m, 'tela_sofa', a0, b0, a1, b1, 0.12, 0.42, 0.06); RB(m, 'tela_sofa', a0, b0, a1, b0 + 0.16, 0.42, 0.82, 0.07)
    RB(m, 'tela_sofa', a0, b0, a0 + 0.12, b1, 0.42, 0.62, 0.05); RB(m, 'tela_sofa', a1 - 0.12, b0, a1, b1, 0.42, 0.62, 0.05)
    RB(m, 'tela_acento', a0 + 0.17, b0 + 0.18, a1 - 0.17, b0 + 0.30, 0.45, 0.72, 0.06)
    for xx in (a0 + 0.06, a1 - 0.06):
        for yy in (b0 + 0.06, b1 - 0.06):
            CY(m, 'madera_mueble', xx, yy, 0.015, 0, 0.12, seg=8)
    CY(m, 'metal_negro', a1 + 0.14, b1 - 0.05, 0.12, 0, 0.02, seg=20); CY(m, 'metal_negro', a1 + 0.14, b1 - 0.05, 0.01, 0.02, 1.35, seg=8)
    LA(m, 'pantalla_lampara', a1 + 0.14, b1 - 0.05, 1.37, [(0.17, 0), (0.13, 0.24)], seg=24)
    RB(m, 'textil_tapete', 5.55, 1.45, 6.75, 3.65, 0, 0.012, 0.005, k=1)
    art(m, 'o', 7.923, 2.05, 7.923, 3.05, 1.30, 1.80)
    curtain(m, 's', 5.40, 6.40, w=0.24)


furn('MOB_Habitacion_principal', principal, [MOBI[k] for k in ('cama_p', 'noche_pa', 'noche_pb', 'butaca_p')])


def vestier(m):
    wardrobe(m, *MOBI['closet_v1'], 'o', doors=3)
    wardrobe(m, *MOBI['closet_v2'], 's', doors=1)
    B(m, 'espejo_vestier', 6.775, 5.0, 6.79, 6.4, 0.25, 2.0)
    RB(m, 'tela_sofa', 6.85, 5.85, 7.25, 6.35, 0.0, 0.42, 0.05)


furn('MOB_Vestier', vestier, [MOBI['closet_v1'], MOBI['closet_v2'], [6.85, 5.85, 7.25, 6.35]])


def banos(m):
    l = fx['lavamanos_principal']['rect']
    B(m, 'metal_negro', 4.87 + 0.004, l[1] - 0.005, 4.87 + 0.016, l[3] + 0.005, 1.0, 1.85)
    B(m, 'espejo_principal', 4.87 + 0.016, l[1] + 0.005, 4.87 + 0.020, l[3] - 0.005, 1.01, 1.84)
    B(m, 'luz_calida', 4.87 + 0.02, l[1] + 0.05, 4.87 + 0.06, l[3] - 0.05, 1.90, 1.92)
    l2 = fx['lavamanos_social']['rect']
    B(m, 'metal_negro', 4.75 - 0.016, l2[1] - 0.005, 4.75 - 0.004, l2[3] + 0.005, 1.0, 1.75)
    B(m, 'espejo_social', 4.75 - 0.020, l2[1] + 0.005, 4.75 - 0.016, l2[3] - 0.005, 1.01, 1.74)
    B(m, 'cromo', 6.635, 5.9, 6.65, 6.4, 1.25, 1.265); RB(m, 'toalla', 6.60, 5.93, 6.635, 6.37, 0.75, 1.27, 0.015)
    B(m, 'cromo', 3.70, 6.0, 3.715, 6.45, 1.25, 1.265); RB(m, 'toalla', 3.715, 6.03, 3.75, 6.42, 0.80, 1.27, 0.015)
    LA(m, 'ceramica_deco', 5.10, l[1] + 0.12, 0.83, [(0.03, 0), (0.035, 0.08), (0.02, 0.1), (0.0, 0.1)], seg=16)
    plant(m, 5.12, l[3] - 0.12, 0.83, 0.20, 0.08, 0.05, 0.08, pot='ceramica_deco')


furn('MOB_Banos', banos, nota='Espejos, toalleros y accesorios ilustrativos de los baños')


def cortinas(m):
    curtain(m, 's', 0.15, 2.599, w=0.30)


furn('MOB_Cortinas_sala', cortinas, nota='Cortinas ilustrativas de la sala')

# ------------------------------------------------------------------ BALCÓN PROPUESTO (no figura en el DWG)
if PROP:
    src = PROP['fuente']
    lx0, ly0, lx1, ly1 = PROP['losa']['rect']; esp = PROP['losa']['espesor']; dn = PROP['losa']['desnivel']
    m = Mesh(); a, b = P(lx0, ly0), P(lx1, ly1)
    m.box('losa', a[0], -dn - esp, a[1], b[0], -dn - 0.02, b[1])
    m.box('piso_exterior', a[0], -dn - 0.02, a[1], b[0], -dn, b[1], faces=['py', 'pz', 'px', 'nx'])
    m.box('marco', a[0], -dn - esp - 0.01, a[1], b[0], -dn - esp, a[1] + 0.06)
    node102('PROP_Balcon_losa', m, 'propuesta', src, 'propuesta')
    m = Mesh(); hb = PROP['baranda']['altura'] - dn
    ux0, uy0, ux1, uy1 = PROP['rect_util']
    xw, xe, ys = ux0 - 0.01, ux1 + 0.01, uy0 - 0.01
    for (x0_, y0_, x1_, y1_) in ((xw - 0.012, ys, xw, uy1), (xe, ys, xe + 0.012, uy1), (xw, ys - 0.012, xe, ys)):
        p0, p1 = P(x0_, y0_), P(x1_, y1_)
        m.box('vidrio_baranda', p0[0], -dn + 0.06, p0[1], p1[0], -dn + hb - 0.05, p1[1])
        m.box('marco', p0[0] - 0.012, -dn, p0[1] - 0.012, p1[0] + 0.012, -dn + 0.06, p1[1] + 0.012)
        lo = np.minimum(p0, p1); hi = np.maximum(p0, p1)
        m.rbox('acero', lo[0] - 0.02, -dn + hb - 0.05, lo[1] - 0.02, hi[0] + 0.02, -dn + hb, hi[1] + 0.02, 0.018, k=2)
    node102('PROP_Balcon_baranda', m, 'propuesta', src + ' Baranda ilustrativa de 1,05 m.', 'propuesta')
    m = Mesh(); ac = PROP['acceso']; vx0, vy0, vx1, vy1 = ac['vano']; hp = ac['altura']
    a, b = P(vx0, vy0), P(vx1, vy1); z0_, z1_ = min(a[1], b[1]), max(a[1], b[1])
    m.box('marco', a[0], 0, z0_, b[0], 0.03, z1_); m.box('marco', a[0], hp - 0.05, z0_, b[0], hp, z1_)
    m.box('marco', a[0], 0, z0_, a[0] + 0.05, hp, z1_); m.box('marco', b[0] - 0.05, 0, z0_, b[0], hp, z1_)
    cx0, cx1 = ac['hojas_cerradas']; mid = (cx0 + cx1) / 2
    for k, (hx0, hx1) in enumerate(((cx0, mid + 0.03), (mid - 0.03, cx1))):
        za = z0_ + 0.035 + k * 0.05; p0, p1 = P(hx0, 0), P(hx1, 0)
        for (fx0, fy0, fx1, fy1) in ((p0[0], 0.03, p0[0] + 0.05, hp - 0.05), (p1[0] - 0.05, 0.03, p1[0], hp - 0.05), (p0[0], 0.03, p1[0], 0.10), (p0[0], hp - 0.12, p1[0], hp - 0.05)):
            m.box('marco', fx0, fy0, za, fx1, fy1, za + 0.04)
        m.box('vidrio', p0[0] + 0.05, 0.10, za + 0.014, p1[0] - 0.05, hp - 0.12, za + 0.026)
    node102('PROP_Puerta_ventana_sala', m, 'propuesta', src + ' Puerta-ventana corrediza en el vano de 2,449 m del DWG.', 'propuesta')

    def balcon(m):
        z = -dn
        for x0_ in (0.20, 0.73):
            x1_ = x0_ + 0.50; y0_, y1_ = -0.78, -0.25
            for xx in (x0_ + 0.04, x1_ - 0.04):
                B(m, 'metal_negro', xx - 0.012, y0_ + 0.02, xx + 0.012, y1_ - 0.02, z, z + 0.03)
                B(m, 'metal_negro', xx - 0.012, y0_ + 0.02, xx + 0.012, y0_ + 0.045, z, z + 0.62)
                B(m, 'metal_negro', xx - 0.012, y1_ - 0.045, xx + 0.012, y1_ - 0.02, z, z + 0.80)
            RB(m, 'madera_mueble', x0_ + 0.02, y0_, x1_ - 0.02, y1_, z + 0.34, z + 0.38, 0.01, k=1)
            RB(m, 'tela_cama', x0_ + 0.04, y0_ + 0.02, x1_ - 0.04, y1_ - 0.02, z + 0.38, z + 0.45, 0.03)
            RB(m, 'tela_cama', x0_ + 0.04, y1_ - 0.12, x1_ - 0.04, y1_ - 0.03, z + 0.42, z + 0.80, 0.04)
        CY(m, 'madera_mueble', 0.72, -1.17, 0.24, z + 0.42, 0.03, seg=32)
        CY(m, 'metal_negro', 0.72, -1.17, 0.015, z, 0.42, seg=8); CY(m, 'metal_negro', 0.72, -1.17, 0.16, z, 0.01, seg=24)
        LA(m, 'ceramica_deco', 0.72, -1.17, z + 0.45, [(0.04, 0), (0.05, 0.06), (0.03, 0.12)], seg=16)
        RB(m, 'maceta', *MOBI['balcon_jardinera'], z, z + 0.42, 0.02)
        for i in range(34):
            px = rng.uniform(2.31, 2.53); py = rng.uniform(-1.58, -0.89)
            SP(m, 'planta_2' if i % 2 else 'planta', px, py, z + 0.48 + rng.uniform(0, 0.12), 0.045, sx=0.45, sy=0.45, sz=rng.uniform(3, 5), seg=6)
        RB(m, 'textil_tapete', 0.17, -1.52, 1.27, -0.18, z, z + 0.008, 0.004, k=1)

    furn('MOB_Balcon', balcon, [MOBI['balcon_sillas'], MOBI['balcon_jardinera']], nota='Mobiliario ilustrativo del balcón propuesto', group='propuesta_mobiliario')

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
        col, rough, metal, opt = MATS[name]
        mt = {'name': name, 'pbrMetallicRoughness': {'baseColorFactor': col, 'roughnessFactor': rough, 'metallicFactor': metal}}
        if col[3] < 1:
            mt['alphaMode'] = 'BLEND'; mt['doubleSided'] = True
        if opt.get('double'):
            mt['doubleSided'] = True
        if opt.get('emissive'):
            mt['emissiveFactor'] = opt['emissive']
        mat_index[name] = len(materials); materials.append(mt)
    return mat_index[name]


tri_count = 0
for name, mesh, extras, t, ry in nodes:
    prims = []
    for mname, (pos, nor, uv, idx) in mesh.parts.items():
        if not idx:
            continue
        p = np.array(pos, np.float32); n = np.array(nor, np.float32); u = np.array(uv, np.float32)
        ln = np.linalg.norm(n, axis=1, keepdims=True); n = n / np.where(ln == 0, 1, ln)
        it = np.array(idx, np.uint32); tri_count += len(it) // 3
        vp, vn, vu = (add_view(a.tobytes(), 34962) for a in (p, n, u))
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

root = {'name': 'Apto_102_Torre_1_Propuesta', 'children': list(range(len(gl_nodes))),
        'extras': {'proyecto': g['proyecto'], 'torre': g['torre'], 'apartamento': g['apartamento'], 'supuestos_visualizacion': SUP,
                   'estado': g['estado'], 'rotulo': g['rotulo'], 'advertencia': g['advertencia'],
                   'propuestas': ([{k: PROP[k] for k in ('id', 'estado', 'fuente', 'area_util_m2', 'requiere_validacion')}] if PROP else []),
                   'areas': g['areas'], 'espacios': {e['id']: e['area_neta_m2'] for e in g['espacios']}, 'sistema': 'X este, Z sur, Y arriba; metros; centro = centro de la envolvente',
                   'categorias': {'verificado': 'Envolvente, vanos de fachada, acceso y ductos del DWG', 'provisional': 'Medida no documentada en el DWG (alturas, losa, cielo)',
                                  'ilustrativo': 'Mobiliario, acabados y carpintería de presentación', 'propuesta': 'Redistribución interior y balcón propuestos, sin validar'}}}
gl_nodes.append(root)
gltf = {'asset': {'version': '2.0', 'generator': 'ORA AI Explorer · apartamento-102/tools/generar_glb.py'}, 'scene': 0,
        'scenes': [{'name': 'Apartamento 102 · propuesta de redistribución', 'nodes': [len(gl_nodes) - 1]}], 'nodes': gl_nodes, 'meshes': meshes,
        'materials': materials, 'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(buf)}]}
js = json.dumps(gltf, ensure_ascii=False, separators=(',', ':')).encode('utf8')
js += b' ' * ((4 - len(js) % 4) % 4)
while len(buf) % 4:
    buf += b'\0'
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II', len(buf), 0x004E4942)); f.write(buf)
print(OUT, len(gl_nodes) - 1, 'nodos', len(materials), 'materiales', tri_count, 'triángulos', round((len(js) + len(buf)) / 1024), 'KB')
