# Convierte los recursos CC0 de MakeHuman en el paquete ligero que usa el juego (players/human.bin + human.json + texturas).
# Uso: python3 tools/build_humans.py <carpeta con los recursos de MakeHuman> <carpeta de salida>
import sys, os, json, struct, collections, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
S = 0.1  # MakeHuman trabaja en decímetros

def conv(p):  # MakeHuman (mira a +z, izquierda +x) -> juego (mira a -z, derecha +x), en metros
    p = np.asarray(p, dtype=np.float64) * S
    return np.stack([-p[..., 0], p[..., 1], -p[..., 2]], -1)

# ---------- malla base ----------
V, VT, F = [], [], collections.defaultdict(list)
g = None
for l in open(f'{SRC}/base.obj'):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('vt '): VT.append([float(x) for x in l.split()[1:3]])
    elif l.startswith('g '): g = l.split()[1]
    elif l.startswith('f '): F[g].append([tuple(int(y) for y in x.split('/')[:2]) for x in l.split()[1:]])
V0 = conv(np.array(V)); VT = np.array(VT); NV = len(V0)

def load_target(path):
    d = np.zeros((NV, 3))
    for l in open(path):
        if l.startswith('#') or not l.strip(): continue
        t = l.split(); d[int(t[0])] = [float(x) for x in t[1:4]]
    return conv(d)
T = lambda n: load_target(f'{SRC}/targets/{n}.target')

# atleta de base: hombre joven caucásico, musculado, proporciones ideales, espalda en V y abdomen plano
mx_av = T('macrodetails/universal-male-young-maxmuscle-averageweight')
base = V0 + T('macrodetails/caucasian-male-young') + 0.55 * mx_av \
    + 0.45 * T('macrodetails/proportions/male-young-averagemuscle-averageweight-idealproportions') \
    + 0.55 * T('macrodetails/proportions/male-young-maxmuscle-averageweight-idealproportions') \
    + 0.45 * T('torso/torso-vshape-incr') + 0.4 * T('stomach/stomach-pregnant-decr') + 0.3 * T('stomach/stomach-tone-incr')
cauc = T('macrodetails/caucasian-male-young')
targets = {
    'muscle': mx_av,  # +/- musculatura
    'heavy': T('macrodetails/universal-male-young-maxmuscle-maxweight') - mx_av,
    'lean': T('macrodetails/universal-male-young-maxmuscle-minweight') - mx_av,
    'african': T('macrodetails/african-male-young') - cauc,
    'asian': T('macrodetails/asian-male-young') - cauc,
}

# ---------- esqueleto reducido ----------
sk = json.load(open(f'{SRC}/default.mhskel'))
J = sk['joints']
def jpos(name, P=base): return P[J[name]].mean(0)
for s in 'LR':
    pass
KEEP = []  # (nombre, padre, joint cabeza, joint cola)
def kb(n, p, h, t): KEEP.append((n, p, h + '____head', t + '____tail'))
kb('root', None, 'root', 'root')
kb('spine05', 'root', 'spine05', 'spine05'); kb('spine04', 'spine05', 'spine04', 'spine04'); kb('spine03', 'spine04', 'spine03', 'spine03')
kb('spine02', 'spine03', 'spine02', 'spine02'); kb('spine01', 'spine02', 'spine01', 'spine01')
kb('neck', 'spine01', 'neck01', 'neck03'); kb('head', 'neck', 'head', 'head')
for s in 'LR':
    kb(f'eye.{s}', 'head', f'eye.{s}', f'eye.{s}')
    kb(f'lidU.{s}', 'head', f'orbicularis03.{s}', f'orbicularis03.{s}'); kb(f'lidD.{s}', 'head', f'orbicularis04.{s}', f'orbicularis04.{s}')
    kb(f'clavicle.{s}', 'spine01', f'clavicle.{s}', f'clavicle.{s}')
    kb(f'upperarm.{s}', f'clavicle.{s}', f'upperarm01.{s}', f'upperarm02.{s}')
    kb(f'lowerarm.{s}', f'upperarm.{s}', f'lowerarm01.{s}', f'lowerarm02.{s}')
    kb(f'hand.{s}', f'lowerarm.{s}', f'wrist.{s}', f'wrist.{s}')
    for f in range(1, 6):
        for k in range(1, 4):
            kb(f'f{f}-{k}.{s}', f'hand.{s}' if k == 1 else f'f{f}-{k-1}.{s}', f'finger{f}-{k}.{s}', f'finger{f}-{k}.{s}')
    kb(f'upperleg.{s}', 'root', f'upperleg01.{s}', f'upperleg02.{s}')
    kb(f'lowerleg.{s}', f'upperleg.{s}', f'lowerleg01.{s}', f'lowerleg02.{s}')
    kb(f'foot.{s}', f'lowerleg.{s}', f'foot.{s}', f'foot.{s}')
    kb(f'toe.{s}', f'foot.{s}', f'toe3-1.{s}', f'toe3-1.{s}')
names = [k[0] for k in KEEP]; BI = {n: i for i, n in enumerate(names)}
def target_bone(b):
    import re
    m = re.match(r'(.*)\.([LR])$', b); s = m.group(2) if m else None; nb = m.group(1) if m else b
    if b in BI: return b
    if nb in ('upperarm01', 'upperarm02'): return f'upperarm.{s}'
    if nb in ('lowerarm01', 'lowerarm02'): return f'lowerarm.{s}'
    if nb in ('upperleg01', 'upperleg02'): return f'upperleg.{s}'
    if nb in ('lowerleg01', 'lowerleg02'): return f'lowerleg.{s}'
    if nb == 'pelvis': return 'root'
    if nb == 'wrist' or nb.startswith('metacarpal'): return f'hand.{s}'
    if nb.startswith('finger'): f, k = nb[6:].split('-'); return f'f{f}-{k}.{s}'
    if nb.startswith('toe'): return f'toe.{s}'
    if nb in ('shoulder01', 'clavicle'): return f'clavicle.{s}'
    if nb == 'breast': return 'spine02'
    if nb in ('neck01', 'neck02', 'neck03'): return 'neck'
    if nb == 'orbicularis03': return f'lidU.{s}'
    if nb == 'orbicularis04': return f'lidD.{s}'
    if nb == 'eye': return f'eye.{s}'
    if nb == 'foot': return f'foot.{s}'
    return 'head'  # cara, mandíbula, lengua...
W = json.load(open(f'{SRC}/default_weights.mhw'))['weights']
acc = [collections.defaultdict(float) for _ in range(NV)]
for b, lst in W.items():
    tb = BI[target_bone(b)]
    for v, w in lst: acc[v][tb] += w
def top4(d, fallback):
    it = sorted(d.items(), key=lambda x: -x[1])[:4]
    s = sum(w for _, w in it)
    if s <= 1e-6: return [(fallback, 1.0)]
    return [(b, w / s) for b, w in it]

# ---------- cuerpo: vértices separados por costuras de UV ----------
body_faces = F['body']
uvmap = {}; R_v, R_uv = [], []
def rv(v, t):
    k = (v, t)
    if k not in uvmap: uvmap[k] = len(R_v); R_v.append(v - 1); R_uv.append(VT[t - 1])
    return uvmap[k]
quads = [[rv(v, t) for v, t in f] for f in body_faces]
R_v = np.array(R_v); R_uv = np.array(R_uv); NR = len(R_v)
print('cuerpo', NR, 'vértices de render,', len(quads), 'quads')

# normales del atleta base (para elegir zonas de ropa)
def vnormals(P, faces_v):
    n = np.zeros_like(P)
    for a, b, c, d in faces_v:
        fn = np.cross(P[c] - P[a], P[d] - P[b]); n[[a, b, c, d]] += fn
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
fv = [[v - 1 for v, _ in f] for f in body_faces]
N0 = vnormals(base, fv)
jp = {n: jpos(h) for n, _, h, _ in KEEP}
wb = lambda v, bones: sum(acc[v].get(BI[b], 0) for b in bones if b in BI)

# ---------- ropa (derivada del cuerpo) ----------
hipY = jp['upperleg.L'][1]; kneeY = jp['lowerleg.L'][1]; ankY = jp['foot.L'][1]; neckY = jp['neck'][1]
armB = [f'{p}.{s}' for s in 'LR' for p in ['lowerarm', 'hand'] + [f'f{f}-{k}' for f in range(1, 6) for k in range(1, 4)]]
def shirt_in(v):
    p = base[v]
    if wb(v, armB) > 0.15: return False
    if p[1] > neckY + 0.005 or p[1] < hipY + 0.02: return False
    for s in 'LR':  # manga corta: hasta el 42% del brazo
        a, b = jp[f'upperarm.{s}'], jp[f'lowerarm.{s}']; ax = b - a; t = np.dot(p - a, ax) / np.dot(ax, ax)
        if wb(v, [f'upperarm.{s}']) > 0.3 and t > 0.45: return False
    return wb(v, ['spine05', 'spine04', 'spine03', 'spine02', 'spine01', 'clavicle.L', 'clavicle.R', 'upperarm.L', 'upperarm.R', 'root', 'neck']) > 0.5
def shorts_in(v):
    p = base[v]
    if wb(v, armB + ['upperarm.L', 'upperarm.R']) > 0.1: return False
    return kneeY + 0.13 < p[1] < hipY + 0.11
def socks_in(v):
    p = base[v]; return p[1] < ankY + 0.13 and wb(v, ['lowerleg.L', 'lowerleg.R', 'foot.L', 'foot.R', 'toe.L', 'toe.R']) > 0.5
def shoe_in(v):
    p = base[v]; return p[1] < ankY + 0.035 and wb(v, ['lowerleg.L', 'lowerleg.R', 'foot.L', 'foot.R', 'toe.L', 'toe.R']) > 0.5
sets = {k: np.array([f(v) for v in range(13380)]) for k, f in [('shirt', shirt_in), ('shorts', shorts_in), ('socks', socks_in), ('shoes', shoe_in)]}
sets['socks'] &= ~sets['shoes']
footBottom = base[:13380, 1].min()

def garment(name, offs):
    sel = sets[name]; fq = [q for q, f in zip(quads, fv) if all(sel[v] for v in f)]
    used = sorted({i for q in fq for i in q}); rm = {r: i for i, r in enumerate(used)}
    gv = R_v[used]; off = np.array([offs(int(v)) for v in gv], dtype=np.float32)
    idx = [rm[i] for q in fq for i in (q[0], q[1], q[2], q[0], q[2], q[3])]
    return dict(rv=np.array(used), off=off, idx=np.array(idx), fq=fq)
def shirt_off(v):
    y = base[v, 1]; return 0.006 + 0.012 * max(0, min(1, (hipY + 0.2 - y) / 0.2))
def shorts_off(v):
    y = base[v, 1]; return 0.009 + 0.008 * max(0, min(1, (hipY - 0.05 - y) / 0.25))
G = {'shirt': garment('shirt', shirt_off), 'shorts': garment('shorts', shorts_off),
     'socks': garment('socks', lambda v: 0.0025), 'shoes': garment('shoes', lambda v: 0.009 if base[v, 1] > footBottom + 0.012 else 0.004)}
# UV cilíndrica para la camiseta (espalda en u=0.5) y colores de la zapatilla
sp = jp['spine03']
def shirt_uv(v):
    p = base[v]; u = 0.5 + math.atan2(p[0] - sp[0], p[2] - sp[2]) / (2 * math.pi); vv = (p[1] - (hipY + 0.02)) / (neckY - hipY)
    return [u % 1.0, max(0, min(1, vv)) * 0.94]
G['shirt']['uv'] = np.array([shirt_uv(int(v)) for v in R_v[G['shirt']['rv']]], dtype=np.float32)
def shoe_col(v):  # 0 suela, 1 empeine, 2 detalle lateral
    p = base[v]; h = p[1] - footBottom
    if h < 0.018: return 0
    if abs(p[0]) > abs(jp['foot.L'][0]) + 0.025 and 0.025 < h < 0.06: return 2
    return 1
G['shoes']['col'] = np.array([shoe_col(int(v)) for v in R_v[G['shoes']['rv']]], dtype=np.uint8)
# el cuerpo bajo la ropa no se dibuja (evita que asome)
covered = sets['shirt'] | sets['shorts'] | sets['shoes']
inner = np.array([covered[v] for v in range(13380)])
# solo quitamos caras con todos sus vecinos también tapados (deja un borde de seguridad)
nb = collections.defaultdict(set)
for f in fv:
    for v in f: nb[v].update(f)
deep = np.array([inner[v] and all(inner[u] for u in nb[v]) for v in range(13380)])
body_q = [q for q, f in zip(quads, fv) if not all(deep[v] for v in f)]
body_idx = np.array([i for q in body_q for i in (q[0], q[1], q[2], q[0], q[2], q[3])])
print('caras de cuerpo visibles', len(body_q), 'de', len(quads))

# ---------- máscara de barba en el espacio UV de la piel ----------
headY = jp['head'][1]
hv_ = [v for v in range(13380) if acc[v].get(BI['head'], 0) > 0.8 and base[v, 1] > neckY + 0.05]
nose = base[min(hv_, key=lambda v: base[v, 2])]
noseY = nose[1]; mouthY = noseY - 0.038; chinY = noseY - 0.095
earZ = jp['head'][2] - 0.005
print('nariz', nose, 'boca', mouthY)
def beard_w(v):
    p = base[v]
    if acc[v].get(BI['head'], 0) + acc[v].get(BI['neck'], 0) < 0.6: return 0
    x, y, z = abs(p[0]), p[1], p[2]
    if z > earZ: return 0                        # nada por detrás de la oreja
    if y > noseY - 0.012: return 0               # por encima del bigote, nada
    if y < chinY - 0.035: return 0               # cuello
    if abs(y - mouthY) < 0.011 and x < 0.027 and z < nose[2] + 0.035: return 0   # labios
    if y > mouthY + 0.008 and x > 0.03 and y > mouthY + 0.02: return 0           # mejilla alta
    w = 1.0
    if y < chinY: w *= max(0, 1 - (chinY - y) / 0.035)                            # se difumina bajo la barbilla
    if y > mouthY + 0.008 and x > 0.022: w *= 0.6
    return w
bm = Image.new('L', (1024, 1024), 0); dr = ImageDraw.Draw(bm)
bw = np.array([beard_w(v) for v in range(13380)])
for q in quads:
    ws = [bw[R_v[i]] for i in q]
    if max(ws) <= 0: continue
    pts = [(R_uv[i][0] * 1024, (1 - R_uv[i][1]) * 1024) for i in q]
    dr.polygon(pts, fill=int(255 * sum(ws) / 4))
bm = bm.filter(ImageFilter.GaussianBlur(6)); Image.merge('LA', (Image.new('L', bm.size, 255), bm)).save(f'{OUT}/beard.png', optimize=True)

# ---------- proxies (ojos, cejas, pestañas, pelo) ----------
def load_obj(path):
    v, vt, f = [], [], []
    for l in open(path):
        if l.startswith('v '): v.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('vt '): vt.append([float(x) for x in l.split()[1:3]])
        elif l.startswith('f '): f.append([tuple(int(y) if y else 0 for y in (x.split('/') + ['0'])[:2]) for x in l.split()[1:]])
    return v, vt, f
def load_proxy(dirn, name):
    refs, scales = [], {}
    inv = False
    for l in open(f'{dirn}/{name}.mhclo'):
        t = l.split()
        if not t or t[0].startswith('#'): continue
        if t[0] in ('x_scale', 'y_scale', 'z_scale'): scales[t[0][0]] = (int(t[1]), int(t[2]), float(t[3])); continue
        if t[0] == 'verts': inv = True; continue
        if inv:
            if len(t) == 9: refs.append(([int(x) for x in t[:3]], [float(x) for x in t[3:6]], [float(x) for x in t[6:9]]))
            elif len(t) == 1 and t[0].isdigit(): refs.append(([int(t[0])] * 3, [1, 0, 0], [0, 0, 0]))
            elif not t[0].lstrip('-').replace('.', '').isdigit() and refs: inv = False
    v, vt, f = load_obj(f'{dirn}/{name}.obj')
    assert len(v) == len(refs), (name, len(v), len(refs))
    # separa por UV
    um = {}; pv, puv, idx = [], [], []
    for face in f:
        ids = []
        for vi, ti in face:
            k = (vi, ti)
            if k not in um: um[k] = len(pv); pv.append(vi - 1); puv.append(vt[ti - 1] if ti else [0, 0])
            ids.append(um[k])
        for i in range(1, len(ids) - 1): idx += [ids[0], ids[i], ids[i + 1]]
    pv = np.array(pv)
    R = [refs[i] for i in pv]
    # pesos de piel: mezcla de los de sus vértices de referencia
    sw = []
    for (ix, ws, _) in R:
        d = collections.defaultdict(float)
        for i, w in zip(ix, ws):
            for b, x in acc[i].items(): d[b] += x * max(0, w)
        sw.append(top4(d, BI['head']))
    return dict(refs=R, scales=scales, uv=np.array(puv, dtype=np.float32), idx=np.array(idx), sw=sw, src=pv)
PX = {}
PX['eyes'] = load_proxy(f'{SRC}/eyes', 'high-poly')
PX['brows'] = load_proxy(f'{SRC}/eyebrows/eyebrow001', 'eyebrow001')
PX['lashes'] = load_proxy(f'{SRC}/eyelashes/eyelashes01', 'eyelashes01')
HAIRS = ['short02', 'short01', 'short03', 'short04', 'afro01', 'ponytail01', 'long01']
for h in HAIRS: PX['hair_' + h] = load_proxy(f'{SRC}/hair/{h}', h)
# UV propia de los ojos: proyección frontal centrada en el iris (la textura original no casa con esta malla)
ev, _, _ = load_obj(f'{SRC}/eyes/high-poly.obj'); ev = np.array(ev)
def eye_uv():
    px = PX['eyes']; out = []
    # índice de vértice original de cada vértice separado: lo recuperamos por posición de referencia
    return out
eo = {}
for side in (1, -1):
    ids = [i for i in range(len(ev)) if ev[i, 0] * side > 0]; c = ev[ids].mean(0); r = np.abs(ev[ids] - c).max(0)
    eo[side] = (c, r)
# los ojos siguen solo al hueso del ojo (por lado)
uvs = []
for o in PX['eyes']['src']:
    p = ev[o]; side = 1 if p[0] > 0 else -1; c, r = eo[side]; d = p - c
    # frente del ojo hacia +z en MakeHuman: u,v en el disco frontal; la parte de atrás va al blanco del ojo
    u = 0.5 + d[0] / r[0] * 0.5; v = 0.5 + d[1] / r[1] * 0.5
    if d[2] < 0: u, v = 0.02, 0.5
    uvs.append([u, v])
PX['eyes']['uv'] = np.array(uvs, dtype=np.float32)
for i, (ix, ws, _) in enumerate(PX['eyes']['refs']):
    x = sum(base[j][0] * w for j, w in zip(ix, ws))
    PX['eyes']['sw'][i] = [(BI['eye.R' if x > 0 else 'eye.L'], 1.0)]

# ---------- escritura binaria ----------
buf = bytearray(); meta = {'bones': [], 'targets': {}, 'proxies': {}, 'garments': {}}
def put(arr, dt):
    global buf
    a = np.ascontiguousarray(np.asarray(arr), dtype=dt)
    while len(buf) % 4: buf += b'\0'
    o = len(buf); buf += a.tobytes(); return [o, int(a.size)]
meta['nv'] = NV
meta['base'] = put(base.astype(np.float32).ravel(), '<f4')
for k, d in targets.items():
    nz = np.where(np.abs(d).max(1) > 1e-5)[0]
    meta['targets'][k] = {'i': put(nz, '<u2'), 'd': put(np.round(d[nz] / 2e-5).astype(np.int16).ravel(), '<i2')}
# cuerpo
meta['body'] = {'rv': put(R_v, '<u2'), 'uv': put(R_uv.astype(np.float32).ravel(), '<f4'), 'idx': put(body_idx, '<u2'),
                'quads': put(np.array([v for f in fv for v in f]), '<u2')}
sw = [top4(acc[v], BI['root']) for v in range(NV)]
def pack_sw(lst):
    si = np.zeros((len(lst), 4), np.uint8); ww = np.zeros((len(lst), 4), np.uint8)
    for i, l in enumerate(lst):
        for k, (b, w) in enumerate(l): si[i, k] = b; ww[i, k] = int(round(w * 255))
        ww[i, 0] = max(0, min(255, int(ww[i, 0]) + 255 - int(ww[i].astype(int).sum())))
    return si.ravel(), ww.ravel()
si, ww = pack_sw(sw); meta['skin'] = {'i': put(si, 'u1'), 'w': put(ww, 'u1')}
for k, gm in G.items():
    m = {'rv': put(gm['rv'], '<u2'), 'off': put(gm['off'], '<f4'), 'idx': put(gm['idx'], '<u2')}
    if 'uv' in gm: m['uv'] = put(gm['uv'].ravel(), '<f4')
    if 'col' in gm: m['col'] = put(gm['col'], 'u1')
    meta['garments'][k] = m
for k, p in PX.items():
    ix = np.array([r[0] for r in p['refs']]); wsx = np.array([r[1] for r in p['refs']]); of = np.array([r[2] for r in p['refs']])
    si, ww = pack_sw(p['sw'])
    meta['proxies'][k] = {'ix': put(ix.ravel(), '<u2'), 'w': put(wsx.ravel(), '<f4'), 'of': put(of.ravel(), '<f4'), 'uv': put(p['uv'].ravel(), '<f4'),
                          'idx': put(p['idx'], '<u2'), 'si': put(si, 'u1'), 'sw': put(ww, 'u1'),
                          'sc': [[p['scales'][a][0], p['scales'][a][1], p['scales'][a][2]] for a in 'xyz']}
for n, p, h, t in KEEP:
    meta['bones'].append({'n': n, 'p': BI[p] if p else -1, 'h': put(J[h], '<u2'), 't': put(J[t], '<u2')})
meta['hairs'] = HAIRS
open(f'{OUT}/human.bin', 'wb').write(bytes(buf))
json.dump(meta, open(f'{OUT}/human.json', 'w'), separators=(',', ':'))
print('human.bin', len(buf) // 1024, 'KB; huesos', len(KEEP))

# ---------- texturas (webp) ----------
def tex(src, dst, size, alpha=False, q=82):
    im = Image.open(src); im = im.convert('RGBA' if alpha else 'RGB'); im = im.resize((size, size), Image.LANCZOS)
    im.save(f'{OUT}/{dst}', 'WEBP', quality=q, method=6)
tex(f'{SRC}/skins/young_caucasian_male/young_lightskinned_male_diffuse.png', 'skin_light.webp', 1024)
tex(f'{SRC}/skins/middleage_caucasian_male/middleage_lightskinned_male_diffuse.png', 'skin_mid.webp', 1024)
tex(f'{SRC}/skins/young_asian_male/young_lightskinned_male_diffuse3.png', 'skin_tan.webp', 1024)
tex(f'{SRC}/skins/young_african_male/young_darkskinned_male_diffuse.png', 'skin_dark.webp', 1024)
# textura del ojo: blanco con venitas suaves, iris gris (se tiñe en el juego) con anillo oscuro, pupila
E = 512; im = Image.new('RGB', (E, E), (236, 230, 226)); dr = ImageDraw.Draw(im)
import random; random.seed(3)
for _ in range(40):
    a0 = random.random() * 6.28; r0 = E * 0.5; pts = []
    for k in range(6): rr = r0 - k * E * 0.03; pts.append((E / 2 + math.cos(a0 + random.uniform(-.08, .08) * k) * rr, E / 2 + math.sin(a0 + random.uniform(-.08, .08) * k) * rr))
    dr.line(pts, fill=(205, 140, 140), width=1)
IR = E * 0.235
for k in range(int(IR), 0, -1):
    t = k / IR; g = int(90 + 70 * (1 - t) + 25 * math.sin(k * 1.7))
    dr.ellipse([E / 2 - k, E / 2 - k, E / 2 + k, E / 2 + k], fill=(g, g, g))
for a0 in range(0, 360, 4):  # fibras del iris
    a1 = math.radians(a0); dr.line([(E / 2 + math.cos(a1) * IR * 0.35, E / 2 + math.sin(a1) * IR * 0.35), (E / 2 + math.cos(a1) * IR * 0.95, E / 2 + math.sin(a1) * IR * 0.95)], fill=(185, 185, 185) if a0 % 8 else (70, 70, 70), width=1)
dr.ellipse([E / 2 - IR, E / 2 - IR, E / 2 + IR, E / 2 + IR], outline=(35, 35, 35), width=int(E * 0.018))
PR = E * 0.085; dr.ellipse([E / 2 - PR, E / 2 - PR, E / 2 + PR, E / 2 + PR], fill=(8, 8, 8))
im = im.filter(ImageFilter.GaussianBlur(1.2)).transpose(Image.FLIP_TOP_BOTTOM)
im.resize((256, 256), Image.LANCZOS).save(f'{OUT}/eye.webp', 'WEBP', quality=90)
tex(f'{SRC}/eyebrows/eyebrow001/eyebrow001.png', 'brows.webp', 256, True)
tex(f'{SRC}/eyelashes/eyelashes01/eyelashes01.png', 'lashes.webp', 256, True)
HT = {'short02': 'short02_diffuse', 'short01': 'short01_diffuse', 'short03': 'short03_diffuse', 'short04': 'short04_diffuse', 'afro01': 'afro_diffuse', 'ponytail01': 'ponytail01_diffuse', 'long01': 'long01_diffuse'}
for h, t in HT.items(): tex(f'{SRC}/hair/{h}/{t}.png', f'hair_{h}.webp', 512, True, 85)
print('texturas listas')
