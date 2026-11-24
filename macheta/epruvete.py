"""Epruvete de ajustaj pentru macheta (MR-016 A): imprimă-le cu aceleași setări ca piesele machetei.
Numărul de crestături de pe margine = indicele variantei (1 = cea mai strânsă)."""
import numpy as np, trimesh
J = [-0.2, -0.1, 0.0, 0.1, 0.2]               # abaterea de la cota nominală [mm]

def crestaturi(corp, r, k, h):
    for i in range(k):
        a = 2*np.pi*i/12
        b = trimesh.creation.box([2.0, 1.5, h + 2])
        b.apply_translation([r*np.cos(a), r*np.sin(a), h/2]); b.apply_transform(trimesh.transformations.rotation_matrix(0, [0, 0, 1]))
        R = trimesh.transformations.rotation_matrix(a, [0, 0, 1], [r*np.cos(a), r*np.sin(a), 0])
        b.apply_transform(R)
        corp = corp.difference(b)
    return corp

def inel(d_int, k, h=8, perete=4):
    c = trimesh.creation.annulus(d_int/2, d_int/2 + perete, h, sections=256); c.apply_translation([0, 0, h/2])
    return crestaturi(c, d_int/2 + perete, k, h)

def stift(d, k, h=18):
    baza = trimesh.creation.cylinder(radius=d/2 + 5, height=3, sections=256); baza.apply_translation([0, 0, 1.5])
    s = trimesh.creation.cylinder(radius=d/2, height=h, sections=256); s.apply_translation([0, 0, 3 + h/2])
    return crestaturi(baza.union(s), d/2 + 5, k, 3)

seturi = [('rulment_63-22_exterior_D56', lambda j, k: inel(56 + j, k), 72),   # alezaj pentru inelul exterior
          ('rulment_63-22_interior_d22', lambda j, k: stift(22 + j, k), 40),      # fus pentru inelul interior
          ('simering_22x35x7_D35', lambda j, k: inel(35 + j, k), 50)]            # alezaj pentru simering
for nume, f, pas in seturi:
    piese = []
    for k, j in enumerate(J, 1):
        p = f(j, k); p.apply_translation([((k - 1) % 3)*pas, ((k - 1) // 3)*pas, 0]); piese.append(p)
    m = trimesh.util.concatenate(piese); m.export(nume + '.stl')
    print(nume, [round(x, 1) for x in m.extents], 'etanș' if m.is_watertight else 'NU e etanș')
