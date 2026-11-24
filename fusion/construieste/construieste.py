# construieste.py - script Fusion: construiește modelul pas cu pas
#
# Pasul 0: încarcă sau actualizează User Parameters din ../parametri_fusion.csv
#          (fișierul scris de s07_export_fusion.m; sursa valorilor e parametri.m).
# Pasul 1: 00_Schelet - schița bielă-manivelă: axa cilindrului, manivela, biela,
#          pistonul, ferestrele, raclorul la PMI, cercul contragreutăților.
# Pasul 2: 10_Cilindru - cămașa, cu fereastra de evacuare și cinci ferestre de transfer:
#          A± principale, B± secundare (cu injectoarele), C boost opus evacuării.
# Pasul 3: 20_Piston și 21_Bolt - pistonul (pe baza YZ125) la PMI: coroana, doi
#          segmenți, raclorul pe fustă, bosajele, canalele siguranțelor; bolțul
#          tubular 15 x 41 și siguranțele din sârmă (Wiseco CW15).
# Pasul 4: 30_Biela - biela YZ125 (110 mm, cap Ø28, picior Ø19, 15,9 mm) cu rulmenții cu ace.
# Pasul 5: 40_Arbore - ambielajul YZ125 (55,925 mm): brațe, fusuri, maneton Ø22,
#          șaibe, rulmenții paliere 63/22. Totul la PMI; arborele pe axa Y.
# Pasul 6: 15_Chiulasa - camera de ardere: banda de squish și bolul sferic, bujia.
#
# reconstruieste.txt (lângă script): numele componentelor de șters înainte de
# construcție, câte unul pe rând. Scriptul golește fișierul după folosire.
#
# Fiecare pas își construiește componenta doar dacă ea lipsește, deci corecturile
# tale rămân. Cotele sunt expresii de parametri: nimic nu e tastat ca număr.
# La final rulează verificările și scrie raport.txt lângă script.
# Designul trebuie să fie Hybrid Design, cu Z în sus.

import csv
import math
import os
import re
import traceback

import adsk.core
import adsk.fusion

AICI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(os.path.dirname(AICI), 'parametri_fusion.csv')
GRUP = 'dizertatie'
TOL = 1e-6          # [cm] = 0,01 um: toleranța numerică a verificărilor geometrice


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('Deschide un design în Fusion înainte de rulare.')
            return
        if (app.preferences.generalPreferences.defaultModelingOrientation !=
                adsk.core.DefaultModelingOrientations.ZUpModelingOrientation):
            ui.messageBox('Modelul se construiește cu Z în sus: Preferences > General > '
                          'Default modeling orientation = Z up.')
            return
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        raport = [sterge_cerute(design), importa_parametri(design), pas01_schelet(design),
                  pas02_cilindru(design), pas03_piston(design), pas03_bolt(design), pas04_biela(design),
                  pas05_arbore(design), pas06_chiulasa(design), exporta_volume(design),
                  pas09_carter(design), pas09b_lamela(design), pas10_stator(design), pas11_rotor(design),
                  pas12_cilindru_corp(design), pas12b_supapa(design), pas13_compresor(design), pas14_capac(design), pas14b_scut(design), pas14c_pompa_ulei(design), pas15_toba(design),
                  pas08_legaturi(design), aplica_materiale(design), ruleaza_cinematica(design),
                  exporta_multicorp(design), sterge_orfani(design), '']
        teste = []
        for verif in (verifica_pas01, verifica_pas02, verifica_pas03, verifica_pas04,
                      verifica_pas05, verifica_pas06, verifica_echilibrare, verifica_pas09, verifica_pas10,
                      verifica_pas12, verifica_pas14, verifica_ulei, verifica_toba, verifica_materiale, verifica_cinematica):
            try:
                teste += verif(design)
            except Exception as ex:                  # o verificare care nu poate rula pică, restul continuă
                linia = traceback.extract_tb(ex.__traceback__)[-1].lineno
                teste.append((False, '[PICAT ] {}: nu a putut rula ({}, linia {})'.format(verif.__name__, ex, linia)))
        raport += [t for _, t in teste]
        trecute = sum(1 for ok, _ in teste if ok)
        raport.append('\nRezumat: {} din {} verificări trecute'.format(trecute, len(teste)))
        with open(os.path.join(AICI, 'raport.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(raport))
        ui.messageBox('\n'.join(raport), 'Construcție')
    except Exception:
        if ui:
            ui.messageBox('Eroare:\n{}'.format(traceback.format_exc()))


# --- Pasul 0 ---------------------------------------------------------------
def importa_parametri(design):
    params = design.userParameters
    noi, actualizati, erori = 0, 0, []
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        for rand in csv.DictReader(f):
            nume, expr = rand['Nume'], rand['Expresie']
            try:
                p = params.itemByName(nume)
                if p:
                    p.expression = expr
                    p.comment = rand['Comentariu']
                    actualizati += 1
                else:
                    params.add(nume, adsk.core.ValueInput.createByString(expr),
                               rand['Unitate'], rand['Comentariu'])
                    noi += 1
            except Exception:
                erori.append(nume)
    if not params.itemByName('unghi_manivela'):
        params.add('unghi_manivela', adsk.core.ValueInput.createByString('40 deg'), 'deg',
                   'Poziția manivelei în schelet, grade după PMI (doar vizualizare)')
    text = 'Parametri: {} noi, {} actualizați.'.format(noi, actualizati)
    if erori:
        text += '\nNu s-au putut scrie: ' + ', '.join(erori)
    return text


def sterge_orfani(design):
    """Șterge parametrii utilizator care nu mai sunt în CSV (rămași de la variante vechi)."""
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        din_csv = {r['Nume'] for r in csv.DictReader(f)} | {'unghi_manivela'}
    params, sterse, ramase = design.userParameters, [], []
    for i in reversed(range(params.count)):
        p = params.item(i)
        nume = p.name
        if nume in din_csv:
            continue
        try:
            (sterse if p.deleteMe() else ramase).append(nume)
        except Exception:
            ramase.append(nume)
    text = 'Parametri orfani șterși: {}.'.format(', '.join(sterse) if sterse else 'niciunul')
    if ramase:
        text += ' Încă folosiți, rămân: ' + ', '.join(ramase)
    return text


def valori_matlab():
    """Valorile calculate de MATLAB, din comentariile CSV-ului: nume -> mm."""
    rez = {}
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        for rand in csv.DictReader(f):
            m = re.search(r'MATLAB: ([-\d.]+)', rand['Comentariu'])
            if m:
                rez[rand['Nume']] = float(m.group(1))
    return rez


# --- Utilitare ---------------------------------------------------------------
def componenta_noua(design, nume):
    """Componenta nouă în rădăcină; None dacă există deja (nu se reconstruiește)."""
    root = design.rootComponent
    for occ in root.occurrences:
        if occ.component.name == nume:
            return None
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = nume
    return occ.component


def sterge_cerute(design):
    """Șterge componentele scrise în reconstruieste.txt, apoi golește fișierul."""
    cale = os.path.join(AICI, 'reconstruieste.txt')
    if not os.path.exists(cale):
        return 'Reconstruire: nimic cerut.'
    with open(cale, encoding='utf-8') as f:
        nume = [r.strip() for r in f if r.strip()]
    sterse = []
    for n in nume:
        for occ in list(design.rootComponent.occurrences):
            if occ.component.name == n:
                occ.deleteMe()
                sterse.append(n)
    open(cale, 'w', encoding='utf-8').close()
    return 'Reconstruire: șterse {}.'.format(', '.join(sterse) if sterse else 'nimic')


def valoare(design):
    return lambda n: design.userParameters.itemByName(n).value    # cm, rad


def marcheaza(entitate, rol):
    entitate.attributes.add(GRUP, 'rol', rol)


def gaseste(design, rol):
    toate = gaseste_toate(design, rol)
    return toate[0] if toate else None


def gaseste_toate(design, rol):
    """Toate corpurile cu rolul dat (o tăietură poate împărți un corp în două)."""
    corpuri = {}
    for a in design.findAttributes(GRUP, 'rol'):
        if a.value == rol and a.parent:
            corpuri[a.parent.entityToken] = a.parent
    return list(corpuri.values())


def pe_parti(corpuri, nume, rol):
    """Denumește bucățile după partea pe care stau: _stanga (+Y, variatorul) / _dreapta (-Y, mașina electrică)."""
    for b in corpuri:
        b.name = nume + ('_stanga' if b.physicalProperties.centerOfMass.y > 0 else '_dreapta')
        marcheaza(b, rol)
    return list(corpuri)


def x_piston(r, L, th):
    """Coborârea pistonului de la PMI (formula bielă-manivelă)."""
    return r*(1 - math.cos(th)) + L*(1 - math.sqrt(1 - (r/L)**2*math.sin(th)**2))


class Schita:
    """Schiță cu puncte date în coordonatele modelului (Z în sus) și cote în
    direcțiile modelului, oricum ar fi orientate axele schiței."""

    def __init__(self, comp, plan, nume):
        self.sk = comp.sketches.add(plan)
        self.sk.name = nume
        self.sk.isComputeDeferred = True
        self.lin = self.sk.sketchCurves.sketchLines
        self.gc = self.sk.geometricConstraints
        self.dim = self.sk.sketchDimensions
        self.O = self.sk.originPoint
        x_e_vertical = abs(self.sk.xDirection.z) > 0.5
        H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
        V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
        self.cota_vert, self.cota_oriz = (H, V) if x_e_vertical else (V, H)
        self._x_vertical = x_e_vertical

    def p(self, x, y, z):
        return self.sk.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))

    def verticala(self, linie):
        (self.gc.addHorizontal if self._x_vertical else self.gc.addVertical)(linie)

    def orizontala(self, linie):
        (self.gc.addVertical if self._x_vertical else self.gc.addHorizontal)(linie)

    def cota(self, p1, p2, orientare, text, expr):
        d = self.dim.addDistanceDimension(p1, p2, orientare, text)
        d.parameter.expression = expr
        return d

    def dreptunghi(self, a, b, c, d):
        """Patru colțuri în ordine; laturile a-b și c-d orizontale în model."""
        l1 = self.lin.addByTwoPoints(a, b)
        l2 = self.lin.addByTwoPoints(l1.endSketchPoint, c)
        l3 = self.lin.addByTwoPoints(l2.endSketchPoint, d)
        l4 = self.lin.addByTwoPoints(l3.endSketchPoint, l1.startSketchPoint)
        self.orizontala(l1)
        self.orizontala(l3)
        self.verticala(l2)
        self.verticala(l4)
        return l1, l2, l3, l4

    def gata(self):
        self.sk.isComputeDeferred = False
        return self.sk


# --- Pasul 1 ---------------------------------------------------------------
def pas01_schelet(design):
    comp = componenta_noua(design, '00_Schelet')
    if comp is None:
        return 'Pasul 1: 00_Schelet există deja, l-am lăsat neatins.'

    v = valoare(design)
    r, L, hc = v('raza_manivela'), v('biela_L'), v('inaltime_compresie')
    B, S, lf = v('alezaj'), v('cursa'), v('lungime_fusta')
    th = v('unghi_manivela')
    zT = r + L + hc                                  # coroana la PMI
    zB = zT - S - lf                                 # marginea fustei la PME
    cx, cz = r*math.sin(th), r*math.cos(th)          # butonul manivelei
    zp = cz + math.sqrt(L*L - cx*cx)                 # axa bolțului
    zk = zp + hc                                     # coroana, acum

    s = Schita(comp, comp.xZConstructionPlane, 'Mecanism')
    P = lambda x, z: s.p(x, 0, z)
    V, H = s.cota_vert, s.cota_oriz
    A = adsk.fusion.DimensionOrientations.AlignedDimensionOrientation
    cer = s.sk.sketchCurves.sketchCircles
    xd = B/2 + 1.0                                   # coloana cotelor, la dreapta

    # Axa cilindrului: de la axa arborelui la coroana de la PMI
    ax = s.lin.addByTwoPoints(s.O, P(0, zT))
    ax.isConstruction = True
    s.verticala(ax)
    s.cota(ax.startSketchPoint, ax.endSketchPoint, V, P(-B/2 - 2.0, zT/2),
           'raza_manivela + biela_L + inaltime_compresie')
    T = ax.endSketchPoint
    marcheaza(T, 'coroana_PMI')

    # Manivela, biela, bolț -> coroană
    man = s.lin.addByTwoPoints(s.O, P(cx, cz))
    s.cota(man.startSketchPoint, man.endSketchPoint, A, P(cx/2 + 0.8, cz/2), 'raza_manivela')
    unghi = s.dim.addAngularDimension(ax, man, P(0.6*r*math.sin(th/2), 0.6*r*math.cos(th/2)))
    unghi.parameter.expression = 'unghi_manivela'
    bie = s.lin.addByTwoPoints(man.endSketchPoint, P(0, zp))
    s.gc.addCoincident(bie.endSketchPoint, ax)
    s.cota(bie.startSketchPoint, bie.endSketchPoint, A, P(cx/2 + 1.0, (cz + zp)/2), 'biela_L')
    bol = s.lin.addByTwoPoints(bie.endSketchPoint, P(0, zk))
    s.verticala(bol)
    s.cota(bol.startSketchPoint, bol.endSketchPoint, V, P(-1.0, (zp + zk)/2), 'inaltime_compresie')
    marcheaza(bol.endSketchPoint, 'coroana')

    # Cercurile de referință: traiectoria butonului și limita contragreutăților
    c1 = cer.addByCenterRadius(s.O, r)
    c1.isConstruction = True
    s.dim.addDiameterDimension(c1, P(-r*0.7, -r*0.7)).parameter.expression = 'cursa'
    rc = v('raza_max_contragr')
    c2 = cer.addByCenterRadius(s.O, rc)
    c2.isConstruction = True
    s.dim.addDiameterDimension(c2, P(rc*0.7, -rc*0.7)).parameter.expression = '2 * raza_max_contragr'
    marcheaza(c2, 'contragreutati')

    # Alezajul: linia coroanei la PMI, pereții, marginea fustei la PME
    l0 = s.lin.addByTwoPoints(P(-B/2, zT), P(B/2, zT))
    s.orizontala(l0)
    s.gc.addMidPoint(T, l0)
    s.cota(l0.startSketchPoint, l0.endSketchPoint, H, P(0, zT + 1.0), 'alezaj')
    ps = s.lin.addByTwoPoints(l0.startSketchPoint, P(-B/2, zB))
    pd = s.lin.addByTwoPoints(l0.endSketchPoint, P(B/2, zB))
    s.verticala(ps)
    s.verticala(pd)
    jos = s.lin.addByTwoPoints(ps.endSketchPoint, pd.endSketchPoint)
    s.orizontala(jos)
    s.cota(T, jos.startSketchPoint, V, P(xd + 3.0, (zT + zB)/2), 'cursa + lungime_fusta')
    marcheaza(jos, 'fusta_PME')
    for l in (l0, ps, pd, jos):
        l.isConstruction = True

    # Liniile de referință, măsurate de la coroana de la PMI
    for nume, dx in [('x_EO_deschis', 0.0), ('x_EO_inchis', 0.6), ('x_TO', 1.2),
                     ('cursa', 1.8), ('adancime_raclor', 2.4)]:
        z = zT - v(nume)
        l = s.lin.addByTwoPoints(P(-B/2, z), P(B/2, z))
        l.isConstruction = True
        s.gc.addCoincident(l.startSketchPoint, ps)
        s.gc.addCoincident(l.endSketchPoint, pd)
        s.orizontala(l)
        s.cota(T, l.endSketchPoint, V, P(xd + dx, z + 0.3), nume)
        marcheaza(l, 'ref_' + nume)

    # Pistonul în poziția curentă: coroana, flancurile, marginea fustei
    cp = s.lin.addByTwoPoints(P(-B/2, zk), P(B/2, zk))
    s.orizontala(cp)
    s.gc.addMidPoint(bol.endSketchPoint, cp)
    s.cota(cp.startSketchPoint, cp.endSketchPoint, H, P(0, zk + 0.5), 'alezaj')
    fs = s.lin.addByTwoPoints(cp.startSketchPoint, P(-B/2, zk - lf))
    fd = s.lin.addByTwoPoints(cp.endSketchPoint, P(B/2, zk - lf))
    s.verticala(fs)
    s.verticala(fd)
    s.cota(fs.startSketchPoint, fs.endSketchPoint, V, P(-B/2 - 1.0, zk - lf/2), 'lungime_fusta')
    s.orizontala(s.lin.addByTwoPoints(fs.endSketchPoint, fd.endSketchPoint))

    sk = s.gata()
    libere = sum(1 for c in sk.sketchCurves if not c.isFullyConstrained)
    return ('Pasul 1: 00_Schelet construit. Schița „Mecanism”: {} curbe, {} cote, '
            '{} curbe nedefinite complet.').format(sk.sketchCurves.count, sk.sketchDimensions.count, libere)


def verifica_pas01(design):
    teste = []
    def t(ok, cod, text):
        teste.append((ok, '[{}] {:5s} {}'.format('TRECUT' if ok else 'PICAT ', cod, text)))

    k = gaseste(design, 'coroana')
    if k is None:
        t(False, 'S1', '00_Schelet nu are marcajele de verificare: șterge-l și rulează din nou')
        return teste
    v = valoare(design)
    r, L, hc = v('raza_manivela'), v('biela_L'), v('inaltime_compresie')
    zT = r + L + hc
    sk = k.parentSketch
    t(all(c.isFullyConstrained for c in sk.sketchCurves), 'S1a',
      'Schița „Mecanism” e definită complet ({} curbe)'.format(sk.sketchCurves.count))

    # Mecanismul urmează formula bielă-manivelă în toată plaja unghiului
    u = design.userParameters.itemByName('unghi_manivela')
    vechi = u.expression
    err = 0.0
    for g in (5, 40, 90, 135, 175):
        u.expression = '{} deg'.format(g)
        adsk.doEvents()
        err = max(err, abs(k.worldGeometry.z - (zT - x_piston(r, L, math.radians(g)))))
    u.expression = vechi
    adsk.doEvents()
    t(err < TOL, 'S1b', 'Coroana urmează formula bielă-manivelă la 5-175° (abatere maximă {:.1e} mm)'
      .format(err*10))

    # Liniile ferestrelor: Fusion = formula = MATLAB
    m = valori_matlab()
    unghiuri = {'x_EO_deschis': 'unghi_EO_deschis', 'x_EO_inchis': 'unghi_EO_inchis', 'x_TO': 'unghi_TO'}
    for nume in ('x_EO_deschis', 'x_EO_inchis', 'x_TO', 'cursa', 'adancime_raclor'):
        l = gaseste(design, 'ref_' + nume)
        fusion = (zT - l.startSketchPoint.worldGeometry.z)*10            # mm
        formula = (x_piston(r, L, v(unghiuri[nume]))*10 if nume in unghiuri else v(nume)*10)
        ok = abs(fusion - formula) < TOL*10 and abs(fusion - m[nume]) < 1e-3
        t(ok, 'S1c', '{}: Fusion {:.3f} mm, formula {:.3f} mm, MATLAB {:.3f} mm'
          .format(nume, fusion, formula, m[nume]))

    # Fusta la PME rămâne deasupra contragreutăților, cu jocul cerut
    jos = gaseste(design, 'fusta_PME')
    cg = gaseste(design, 'contragreutati')
    joc = (jos.startSketchPoint.worldGeometry.z - cg.radius)*10
    t(abs(joc - v('joc_contragreutati')*10) < TOL*10, 'S1d',
      'Fusta la PME e cu {:.3f} mm deasupra contragreutăților (cerut {:.3f} mm)'
      .format(joc, v('joc_contragreutati')*10))
    return teste


# --- Pasul 2 ---------------------------------------------------------------
ZT = 'raza_manivela + biela_L + inaltime_compresie'          # coroana la PMI, de la axa arborelui


def pas02_cilindru(design):
    comp = componenta_noua(design, '10_Cilindru')
    if comp is None:
        return 'Pasul 2: 10_Cilindru există deja, l-am lăsat neatins.'

    v = valoare(design)
    B, t = v('alezaj'), v('grosime_perete')
    zT = v('raza_manivela') + v('biela_L') + v('inaltime_compresie')
    z_sus = zT + v('deck_peste_coroana')
    z_jos = zT - v('cursa') - v('lungime_fusta')
    z_pme = zT - v('cursa')
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation

    # 1. Cămașa: secțiunea dreptunghiulară, rotită 360° în jurul axei cilindrului (Z).
    #    Jos: marginea fustei la PME, ca fusta să fie ghidată pe toată cursa.
    s = Schita(comp, comp.xZConstructionPlane, 'Sectiune_camasa')
    l1, l2, l3, l4 = s.dreptunghi(s.p(B/2, 0, z_jos), s.p(B/2 + t, 0, z_jos),
                                  s.p(B/2 + t, 0, z_sus), s.p(B/2, 0, z_sus))
    s.cota(s.O, l4.startSketchPoint, s.cota_oriz, s.p(B/4, 0, z_sus + 0.5), 'alezaj / 2')
    s.cota(l1.startSketchPoint, l1.endSketchPoint, s.cota_oriz, s.p(B/2 + t/2, 0, z_jos - 0.5),
           'grosime_perete')
    s.cota(s.O, l1.startSketchPoint, s.cota_vert, s.p(B/2 - 0.8, 0, z_jos/2),
           ZT + ' - cursa - lungime_fusta')
    s.cota(s.O, l4.startSketchPoint, s.cota_vert, s.p(B/2 + t + 0.8, 0, z_sus/2),
           ZT + ' + deck_peste_coroana')
    sk = s.gata()
    ri = f.revolveFeatures.createInput(sk.profiles.item(0), comp.zConstructionAxis, nou)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    rev = f.revolveFeatures.add(ri)
    rev.name = 'Camasa'
    corp = rev.bodies.item(0)
    corp.name = 'Camasa'
    marcheaza(corp, 'camasa')
    adanc = lambda: adsk.core.ValueInput.createByString('alezaj / 2 + grosime_perete + 5 mm')

    # 2. Fereastra de evacuare: în față (+X), lățimea efectivă, de la marginea de sus
    #    (supapa deschisă) până la coroana la PME.
    w = v('latime_evacuare')
    s = Schita(comp, comp.yZConstructionPlane, 'Fereastra_evacuare')
    l1, l2, l3, l4 = s.dreptunghi(s.p(0, -w/2, z_pme), s.p(0, w/2, z_pme),
                                  s.p(0, w/2, zT - v('x_EO_deschis')), s.p(0, -w/2, zT - v('x_EO_deschis')))
    s.cota(s.O, l2.startSketchPoint, s.cota_oriz, s.p(0, w/4, z_pme - 0.5), 'latime_evacuare / 2')
    s.cota(s.O, l4.startSketchPoint, s.cota_oriz, s.p(0, -w/4, z_pme - 0.5), 'latime_evacuare / 2')
    s.cota(s.O, l1.startSketchPoint, s.cota_vert, s.p(0, -w/2 - 0.8, z_pme/2), ZT + ' - cursa')
    s.cota(s.O, l3.startSketchPoint, s.cota_vert, s.p(0, w/2 + 0.8, zT/2), ZT + ' - x_EO_deschis')
    sk = s.gata()
    normala = sk.xDirection.crossProduct(sk.yDirection)
    sens = (adsk.fusion.ExtentDirections.PositiveExtentDirection if normala.x > 0
            else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    ei = f.extrudeFeatures.createInput(sk.profiles.item(0), taie)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adanc()), sens)
    ei.participantBodies = [corp]
    f.extrudeFeatures.add(ei).name = 'Evacuare'

    # 3. Ferestrele de transfer: A± (principale), B± (secundare, cu injectoarele),
    #    C (boost, opus evacuării). Fiecare: dreptunghi pe un plan vertical prin axa
    #    cilindrului, perpendicular pe direcția ferestrei, tăiat spre exterior.
    #    Unghiurile și lățimile sunt parametri; toate au marginea de sus la x_TO.
    planuri = comp.constructionPlanes
    po_expr = []
    for nume, u_expr, w_expr, semn in [('A_plus', 'unghi_tA', 'latime_tA', +1), ('A_minus', 'unghi_tA', 'latime_tA', -1),
                                       ('B_plus', 'unghi_tB', 'latime_tB', +1), ('B_minus', 'unghi_tB', 'latime_tB', -1),
                                       ('C_boost', 'unghi_tC', 'latime_tC', +1)]:
        fi = v(u_expr)
        pi_ = planuri.createInput()
        pi_.setByAngle(comp.zConstructionAxis,
                       adsk.core.ValueInput.createByString('90 deg {} {}'.format('+' if semn > 0 else '-', u_expr)),
                       comp.xZConstructionPlane)
        plan = planuri.add(pi_)
        plan.name = 'Plan_transfer_' + nume
        plan.isLightBulbOn = False
        s = Schita(comp, plan, 'Transfer_' + nume)
        po = s.sk.sketchPoints.add(s.p(0, 0, 0))                    # axa cilindrului, la z = 0
        po.isFixed = True                                           # planul trece prin origine
        n = s.sk.xDirection.crossProduct(s.sk.yDirection)
        h = adsk.core.Vector3D.create(-n.y, n.x, 0)
        h.normalize()
        w = v(w_expr)
        q = lambda a, z: s.p(a*h.x, a*h.y, z)
        l1, l2, l3, l4 = s.dreptunghi(q(-w/2, z_pme), q(w/2, z_pme), q(w/2, zT - v('x_TO')), q(-w/2, zT - v('x_TO')))
        s.cota(po, l2.startSketchPoint, s.cota_oriz, q(w/4, z_pme - 0.5), w_expr + ' / 2')
        s.cota(po, l4.startSketchPoint, s.cota_oriz, q(-w/4, z_pme - 0.5), w_expr + ' / 2')
        s.cota(po, l1.startSketchPoint, s.cota_vert, q(-w/2 - 0.8, z_pme/2), ZT + ' - cursa')
        s.cota(po, l3.startSketchPoint, s.cota_vert, q(w/2 + 0.8, zT/2), ZT + ' - x_TO')
        sk = s.gata()
        # Spre exterior, pe partea ferestrei: același semn al lui X ca direcția ei
        sx = 1 if math.cos(fi) > 0 else -1
        sens = (adsk.fusion.ExtentDirections.PositiveExtentDirection if n.x*sx > 0
                else adsk.fusion.ExtentDirections.NegativeExtentDirection)
        ti = f.extrudeFeatures.createInput(sk.profiles.item(0), taie)
        ti.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adanc()), sens)
        ti.participantBodies = [corp]
        f.extrudeFeatures.add(ti).name = 'Transfer_' + nume
    return 'Pasul 2: 10_Cilindru construit: cămașa, evacuarea, transferurile A±, B± și boost-ul C.'


def verifica_pas02(design):
    teste = []
    def t(ok, cod, text):
        teste.append((ok, '[{}] {:5s} {}'.format('TRECUT' if ok else 'PICAT ', cod, text)))

    corp = gaseste(design, 'camasa')
    if corp is None:
        t(False, 'C2', '10_Cilindru nu are marcajele de verificare: șterge-l și rulează din nou')
        return teste
    v = valoare(design)
    r, L, hc = v('raza_manivela'), v('biela_L'), v('inaltime_compresie')
    B, tp = v('alezaj'), v('grosime_perete')
    zT = r + L + hc
    t(corp.isSolid, 'C2a', 'Cămașa e un corp solid')

    # Fețele plane ale ferestrelor: orizontale (sus, jos) și laterale
    oriz, lat_y, raze, sus, lat_h = [], [], [], [], []
    for fata in corp.faces:
        tip = fata.geometry.surfaceType
        if tip == adsk.core.SurfaceTypes.CylinderSurfaceType:
            raze.append(adsk.core.Cylinder.cast(fata.geometry).radius)
            continue
        if tip != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        pl = adsk.core.Plane.cast(fata.geometry)
        n, o = pl.normal, fata.pointOnFace
        if abs(abs(n.z) - 1) < 1e-9:
            oriz.append(o.z)
            sus.append(o)
            continue
        if abs(n.z) < 1e-9:
            lat_h.append((n.x, n.y, abs(n.x*o.x + n.y*o.y)))
            if abs(abs(n.y) - 1) < 1e-9 and o.x > 0:
                lat_y.append(abs(o.y))                       # pereții evacuării (+X)
    are = lambda lista, val: any(abs(z - val) < TOL for z in lista)
    z_jos, z_sus = zT - v('cursa') - v('lungime_fusta'), zT + v('deck_peste_coroana')
    t(are(oriz, z_jos) and are(oriz, z_sus), 'C2b',
      'Cămașa se întinde de la {:.3f} la {:.3f} mm de axa arborelui (fusta la PME, puntea)'
      .format(z_jos*10, z_sus*10))
    t(are(raze, B/2) and are(raze, B/2 + tp) and len(set(round(x, 9) for x in raze)) == 2, 'C2c',
      'Alezaj Ø{:.3f} mm, exterior Ø{:.3f} mm, fără alte suprafețe cilindrice'
      .format(B*10, (B + 2*tp)*10))
    z_eo = zT - x_piston(r, L, v('unghi_EO_deschis'))
    z_to = zT - x_piston(r, L, v('unghi_TO'))
    z_pme = zT - v('cursa')
    t(are(oriz, z_eo), 'C2d', 'Marginea de sus a evacuării la {:.3f} mm sub PMI (formula: {:.3f})'
      .format((zT - z_eo)*10, x_piston(r, L, v('unghi_EO_deschis'))*10))
    ev = [o.x for o in sus if abs(o.z - z_eo) < TOL]
    t(len(ev) > 0 and all(x > 0 for x in ev), 'C2i', 'Fereastra de evacuare e în față (+X), spre toba de rezonanță')
    t(are(oriz, z_to), 'C2e', 'Marginea de sus a transferului la {:.3f} mm sub PMI (formula: {:.3f})'
      .format((zT - z_to)*10, x_piston(r, L, v('unghi_TO'))*10))
    t(are(oriz, z_pme), 'C2f', 'Marginea de jos a ferestrelor la coroana de la PME ({:.3f} mm sub PMI)'
      .format(v('cursa')*10))
    t(are(lat_y, v('latime_evacuare')/2), 'C2g',
      'Evacuarea are lățimea efectivă {:.3f} mm'.format(v('latime_evacuare')*10))
    # Fiecare transfer: fețele laterale (normala orizontală, la w/2 de planul central)
    # și fereastra pe partea corectă (fața de sus la unghiul ei)
    sus_tr = [o for o in sus if abs(o.z - z_to) < TOL]
    for cod, nume, fi, w in [('C2h', 'A+', v('unghi_tA'), v('latime_tA')), ('C2h', 'A-', -v('unghi_tA'), v('latime_tA')),
                             ('C2h', 'B+', v('unghi_tB'), v('latime_tB')), ('C2h', 'B-', -v('unghi_tB'), v('latime_tB')),
                             ('C2h', 'C', v('unghi_tC'), v('latime_tC'))]:
        hx, hy = -math.sin(fi), math.cos(fi)
        laterale = [f2 for f2 in lat_h if abs(abs(f2[0]*hx + f2[1]*hy) - 1) < 1e-9 and abs(f2[2] - w/2) < TOL]
        semi = math.asin(w/2/(B/2))
        pe_loc = [o for o in sus_tr
                  if abs(math.atan2(math.sin(math.atan2(o.y, o.x) - fi), math.cos(math.atan2(o.y, o.x) - fi))) < semi]
        t(len(laterale) >= 2 and len(pe_loc) >= 1, cod,
          'Transferul {} la {:+.1f}°, coarda {:.3f} mm'.format(nume, math.degrees(fi), w*10))
    t(len(sus_tr) == 5, 'C2j', 'Cinci ferestre de transfer cu marginea de sus la {:.3f} mm sub PMI ({} găsite)'
      .format((zT - z_to)*10, len(sus_tr)))
    return teste


# --- Pasul 3 ---------------------------------------------------------------
def pas03_piston(design):
    comp = componenta_noua(design, '20_Piston')
    if comp is None:
        return 'Pasul 3: 20_Piston există deja, l-am lăsat neatins.'
    v = valoare(design)
    dm = lambda e: design.unitsManager.evaluateExpression(e, 'mm')     # -> cm
    zT = v('raza_manivela') + v('biela_L') + v('inaltime_compresie')     # coroana la PMI
    R = v('diametru_piston')/2
    Ri = R - v('grosime_fusta_p')                                         # fusta
    Rc = R - dm('canal_adancime + perete_sub_canal')                      # centura segmenților
    Rb = R - dm('raclor_grosime + joc_radial_seg + perete_sub_canal')     # banda raclorului
    zc = zT - v('grosime_coroana')                                        # tavanul interior
    zcb = zT - v('zona_centura')                                          # capătul centurii
    zbt = zT - dm('adancime_raclor - perete_sub_canal')                   # începutul benzii
    zs = zT - v('lungime_fusta')                                          # marginea fustei
    zp = zT - v('inaltime_compresie')                                     # axa bolțului
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    ax = comp.zConstructionAxis

    def schita(plan, nume):
        s = Schita(comp, plan, nume)
        po = s.sk.sketchPoints.add(s.p(0, 0, 0))
        po.isFixed = True
        return s, po

    # 1. Secțiunea: coroană plină, centura groasă a segmenților, fusta subțire,
    #    banda groasă a raclorului jos; rotită în jurul axei cilindrului.
    s, po = schita(comp.xZConstructionPlane, 'Sectiune_piston')
    P = lambda x, z: s.p(x, 0, z)
    pts = [(0, zT), (R, zT), (R, zs), (Rb, zs), (Rb, zbt), (Ri, zbt), (Ri, zcb), (Rc, zcb), (Rc, zc), (0, zc)]
    L = [s.lin.addByTwoPoints(P(*pts[0]), P(*pts[1]))]
    for k in range(2, len(pts)):
        L.append(s.lin.addByTwoPoints(L[-1].endSketchPoint, P(*pts[k])))
    L.append(s.lin.addByTwoPoints(L[-1].endSketchPoint, L[0].startSketchPoint))
    for k, l in enumerate(L):
        (s.orizontala if k % 2 == 0 else s.verticala)(l)
    s.gc.addCoincident(po, L[9])
    c = L[0].startSketchPoint
    s.cota(po, c, s.cota_vert, P(-1.0, zT/2), ZT)
    s.cota(po, L[1].startSketchPoint, s.cota_oriz, P(R/2, zT + 0.6), 'diametru_piston / 2')
    s.cota(L[1].startSketchPoint, L[1].endSketchPoint, s.cota_vert, P(R + 0.8, (zT + zs)/2), 'lungime_fusta')
    s.cota(L[2].startSketchPoint, L[2].endSketchPoint, s.cota_oriz, P((R + Rb)/2, zs - 0.5),
           'raclor_grosime + joc_radial_seg + perete_sub_canal')
    s.cota(L[3].startSketchPoint, L[3].endSketchPoint, s.cota_vert, P(Rb - 0.5, (zs + zbt)/2),
           'lungime_fusta - adancime_raclor + perete_sub_canal')
    s.cota(po, L[5].startSketchPoint, s.cota_oriz, P(Ri/2, zbt + 0.4), 'diametru_piston / 2 - grosime_fusta_p')
    s.cota(c, L[6].startSketchPoint, s.cota_vert, P(Ri - 0.5, (zT + zcb)/2), 'zona_centura')
    s.cota(po, L[7].startSketchPoint, s.cota_oriz, P(Rc/2, zcb - 0.4),
           'diametru_piston / 2 - canal_adancime - perete_sub_canal')
    s.cota(c, L[9].startSketchPoint, s.cota_vert, P(-0.6, zc + 0.2), 'grosime_coroana')
    corp = _rotire(f, s.gata().profiles.item(0), ax, nou)
    corp.name = 'Piston'
    marcheaza(corp, 'piston')

    # 2. Bosajele: bloc de la tavan până sub bolț, rotunjit jos, pe toată lățimea;
    #    ce iese din cilindrul pistonului se taie, apoi golul pentru piciorul bielei.
    rb = v('d_bosaj')/2
    s, po = schita(comp.xZConstructionPlane, 'Bosaje')
    P = lambda x, z: s.p(x, 0, z)
    arc = s.sk.sketchCurves.sketchArcs.addByThreePoints(P(-rb, zp), P(0, zp - rb), P(rb, zp))
    plus, minus = ((arc.endSketchPoint, arc.startSketchPoint)
                   if arc.endSketchPoint.geometry.distanceTo(P(rb, zp)) < 1e-6
                   else (arc.startSketchPoint, arc.endSketchPoint))
    b1 = s.lin.addByTwoPoints(plus, P(rb, zc))
    b2 = s.lin.addByTwoPoints(b1.endSketchPoint, P(-rb, zc))
    b3 = s.lin.addByTwoPoints(b2.endSketchPoint, minus)
    s.verticala(b1); s.verticala(b3); s.orizontala(b2)
    s.gc.addTangent(arc, b1); s.gc.addTangent(arc, b3)
    s.dim.addRadialDimension(arc, P(rb*0.5, zp - rb*0.8)).parameter.expression = 'd_bosaj / 2'
    s.gc.addCoincident(arc.centerSketchPoint, _axa_z(s, po))
    s.cota(po, arc.centerSketchPoint, s.cota_vert, P(-rb - 0.8, zp/2), ZT + ' - inaltime_compresie')
    s.cota(po, b2.startSketchPoint, s.cota_vert, P(rb + 0.8, zc/2), ZT + ' - grosime_coroana')
    ei = f.extrudeFeatures.createInput(s.gata().profiles.item(0), uneste)
    ei.setSymmetricExtent(adsk.core.ValueInput.createByString('diametru_piston / 2'), False)
    ei.participantBodies = [corp]
    f.extrudeFeatures.add(ei).name = 'Bosaje'

    # tăietura inelară: tot ce depășește diametrul pistonului
    s, po = schita(comp.xZConstructionPlane, 'Taiere_exterior')
    l1, l2, l3, l4 = s.dreptunghi(s.p(R, 0, zs - 0.1), s.p(R + 1.0, 0, zs - 0.1),
                                  s.p(R + 1.0, 0, zT + 0.1), s.p(R, 0, zT + 0.1))
    s.cota(po, l4.startSketchPoint, s.cota_oriz, s.p(R/2, 0, zT + 0.4), 'diametru_piston / 2')
    s.cota(l1.startSketchPoint, l1.endSketchPoint, s.cota_oriz, s.p(R + 0.5, 0, zs - 0.4), '10 mm')
    s.cota(po, l1.startSketchPoint, s.cota_vert, s.p(R + 1.4, 0, zs/2), ZT + ' - lungime_fusta - 1 mm')
    s.cota(po, l3.startSketchPoint, s.cota_vert, s.p(R + 1.8, 0, zT/2), ZT + ' + 1 mm')
    _rotire(f, s.gata().profiles.item(0), ax, taie, corp).name = 'Bosaje_la_diametru'

    # golul pentru piciorul bielei: de sub bosaje până la tavan, lățimea piciorului + jocuri
    gol = v('latime_picior') + 2*v('joc_axial_biela')
    s, po = schita(comp.yZConstructionPlane, 'Gol_picior')
    q = lambda y, z: s.p(0, y, z)
    l1, l2, l3, l4 = s.dreptunghi(q(-gol/2, zp - rb - 0.1), q(gol/2, zp - rb - 0.1), q(gol/2, zc), q(-gol/2, zc))
    s.cota(po, l2.startSketchPoint, s.cota_oriz, q(gol/4, zp - rb - 0.6), 'latime_picior / 2 + joc_axial_biela')
    s.cota(po, l4.startSketchPoint, s.cota_oriz, q(-gol/4, zp - rb - 0.6), 'latime_picior / 2 + joc_axial_biela')
    s.cota(po, l1.startSketchPoint, s.cota_vert, q(-gol/2 - 0.8, zp/2), ZT + ' - inaltime_compresie - d_bosaj / 2 - 1 mm')
    s.cota(po, l3.startSketchPoint, s.cota_vert, q(gol/2 + 0.8, zc/2), ZT + ' - grosime_coroana')
    ei = f.extrudeFeatures.createInput(s.gata().profiles.item(0), taie)
    ei.setSymmetricExtent(adsk.core.ValueInput.createByString('d_bosaj / 2 + 1 mm'), False)
    ei.participantBodies = [corp]
    f.extrudeFeatures.add(ei).name = 'Gol_picior'

    # 3. Canalele: doi segmenți în centură, raclorul în banda de jos
    for nume, sus_expr, h_expr, ad_expr in CANALE:
        z1 = zT - dm(sus_expr); z2 = z1 - dm(h_expr); x1 = R - dm(ad_expr)
        s, po = schita(comp.xZConstructionPlane, nume)
        P = lambda x, z: s.p(x, 0, z)
        l1, l2, l3, l4 = s.dreptunghi(P(x1, z2), P(R + 0.5, z2), P(R + 0.5, z1), P(x1, z1))
        s.cota(po, l4.startSketchPoint, s.cota_oriz, P(x1/2, z1 + 0.3), 'diametru_piston / 2 - ({})'.format(ad_expr))
        s.cota(po, l3.endSketchPoint, s.cota_vert, P(x1 - 0.6, (z1 + zT)/2), '{} - ({})'.format(ZT, sus_expr))
        s.cota(l4.startSketchPoint, l4.endSketchPoint, s.cota_vert, P(x1 - 0.3, (z1 + z2)/2), h_expr)
        s.cota(po, l2.startSketchPoint, s.cota_oriz, P(R, z2 - 0.3), 'diametru_piston / 2 + 5 mm')
        _rotire(f, s.gata().profiles.item(0), ax, taie, corp).name = nume

    # 4. Alezajul bolțului, prin bosaje
    s, po = schita(comp.xZConstructionPlane, 'Alezaj_bolt')
    cerc = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, 0, zp), v('alezaj_bolt')/2)
    s.dim.addDiameterDimension(cerc, s.p(v('alezaj_bolt'), 0, zp + 0.5)).parameter.expression = 'alezaj_bolt'
    s.gc.addCoincident(cerc.centerSketchPoint, _axa_z(s, po))
    s.cota(po, cerc.centerSketchPoint, s.cota_vert, s.p(-1.0, 0, zp/2), ZT + ' - inaltime_compresie')
    ei = f.extrudeFeatures.createInput(s.gata().profiles.item(0), taie)
    ei.setSymmetricExtent(adsk.core.ValueInput.createByString('diametru_piston / 2 + 1 mm'), False)
    ei.participantBodies = [corp]
    f.extrudeFeatures.add(ei).name = 'Alezaj_bolt'

    # 5. Canalele siguranțelor: tor în jurul axei bolțului, la capetele lui
    s, prof = _tor_sigurante(comp, design, 'Canale_sigurante', 'sig_d + 0.1 mm')
    ri = f.revolveFeatures.createInput(prof, s.axa, taie)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    ri.participantBodies = [corp]
    f.revolveFeatures.add(ri).name = 'Canale_sigurante'
    return 'Pasul 3: 20_Piston construit (la PMI).'


def _tor_sigurante(comp, design, nume, d_expr):
    """Schița cu cele două cercuri ale siguranțelor și axa bolțului (în planul YZ)."""
    v = valoare(design)
    dm = lambda e: design.unitsManager.evaluateExpression(e, 'mm')
    zp = v('raza_manivela') + v('biela_L')
    yc = dm('l_bolt / 2 + sig_d / 2 + 0.2 mm')
    rc = dm('alezaj_bolt / 2 + 0.1 mm')
    s = Schita(comp, comp.yZConstructionPlane, nume)
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    R = v('diametru_piston')/2
    ax = s.lin.addByTwoPoints(s.p(0, -R, zp), s.p(0, R, zp))
    ax.isConstruction = True
    s.orizontala(ax)
    s.cota(po, ax.startSketchPoint, s.cota_vert, s.p(0, -R - 0.5, zp/2), 'raza_manivela + biela_L')
    s.cota(po, ax.startSketchPoint, s.cota_oriz, s.p(0, -R/2, zp + 0.5), 'diametru_piston / 2')
    s.cota(po, ax.endSketchPoint, s.cota_oriz, s.p(0, R/2, zp + 0.5), 'diametru_piston / 2')
    cercuri = []
    for semn in (-1, 1):
        c = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, semn*yc, zp + rc), dm(d_expr)/2)
        s.dim.addDiameterDimension(c, s.p(0, semn*yc + 0.2, zp + rc + 0.2)).parameter.expression = d_expr
        s.cota(po, c.centerSketchPoint, s.cota_oriz, s.p(0, semn*yc/2, zp + rc + 0.4),
               'l_bolt / 2 + sig_d / 2 + 0.2 mm')
        s.cota(ax.startSketchPoint, c.centerSketchPoint, s.cota_vert, s.p(0, semn*(yc + 0.4), zp + rc/2),
               'alezaj_bolt / 2 + 0.1 mm')
        cercuri.append(c)
    sk = s.gata()
    s.axa = ax
    prof = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        prof.add(sk.profiles.item(i))
    return s, prof


CANALE = [('Canal_1', 'cap_sus', 'canal_1_inaltime', 'canal_adancime'),
          ('Canal_2', 'cap_sus + canal_1_inaltime + punte_seg', 'canal_2_inaltime', 'canal_adancime'),
          ('Canal_raclor', 'adancime_raclor', 'raclor_inaltime + joc_lateral_seg', 'raclor_grosime + joc_radial_seg')]


def pas03_bolt(design):
    cb = componenta_noua(design, '21_Bolt')
    if cb is None:
        return 'Pasul 3b: 21_Bolt există deja, l-am lăsat neatins.'
    v = valoare(design)
    zp = v('raza_manivela') + v('biela_L')
    s = Schita(cb, cb.xZConstructionPlane, 'Sectiune_bolt')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    ce = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, 0, zp), v('d_bolt')/2)
    ci = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, 0, zp), v('d_bolt_int')/2)
    s.gc.addConcentric(ce, ci)
    s.dim.addDiameterDimension(ce, s.p(v('d_bolt'), 0, zp + 0.6)).parameter.expression = 'd_bolt'
    s.dim.addDiameterDimension(ci, s.p(v('d_bolt_int')/2, 0, zp + 0.2)).parameter.expression = 'd_bolt_int'
    s.gc.addCoincident(ce.centerSketchPoint, _axa_z(s, po))
    s.cota(po, ce.centerSketchPoint, s.cota_vert, s.p(-1.0, 0, zp/2), 'raza_manivela + biela_L')
    sk = s.gata()
    inel = min((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda pr: abs(pr.areaProperties().area - math.pi/4*(v('d_bolt')**2 - v('d_bolt_int')**2)))
    ei = cb.features.extrudeFeatures.createInput(inel, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setSymmetricExtent(adsk.core.ValueInput.createByString('l_bolt / 2'), False)
    bolt = cb.features.extrudeFeatures.add(ei).bodies.item(0)
    bolt.name = 'Bolt'
    marcheaza(bolt, 'bolt')
    s, prof = _tor_sigurante(cb, design, 'Sigurante', 'sig_d')
    ri = cb.features.revolveFeatures.createInput(prof, s.axa, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    feat = cb.features.revolveFeatures.add(ri)
    pe_parti([feat.bodies.item(i) for i in range(feat.bodies.count)], 'Siguranta', 'sigurante')
    return ('Pasul 3b: 21_Bolt construit (tub {:.0f}/{:.0f} x {:.0f} mm) cu siguranțele din sârmă de {:.1f} mm.'
            .format(v('d_bolt')*10, v('d_bolt_int')*10, v('l_bolt')*10, v('sig_d')*10))


def _rotire(f, profil, axa, op, corp=None):
    ri = f.revolveFeatures.createInput(profil, axa, op)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    if corp is not None:
        ri.participantBodies = [corp]
    feat = f.revolveFeatures.add(ri)
    return feat if corp is not None else feat.bodies.item(0)


def _axa_z(s, po):
    """Linie de construcție verticală prin origine, pentru centre pe axa cilindrului.
    Una singură pe schiță: a doua s-ar suprapune peste prima și ar supra-constrânge."""
    if getattr(s, '_axa', None) is not None:
        return s._axa
    l = s.lin.addByTwoPoints(po, s.p(0, 0, 1.0))
    l.isConstruction = True
    s.verticala(l)
    s.cota(l.startSketchPoint, l.endSketchPoint, s.cota_vert, s.p(0.3, 0, 0.5), '10 mm')
    s._axa = l
    return l


def verifica_pas03(design):
    teste = []
    def t(ok, cod, text):
        teste.append((ok, '[{}] {:5s} {}'.format('TRECUT' if ok else 'PICAT ', cod, text)))

    pist = gaseste(design, 'piston')
    bolt = gaseste(design, 'bolt')
    if pist is None or bolt is None:
        t(False, 'C3', '20_Piston/21_Bolt nu au marcajele de verificare: șterge-le și rulează din nou')
        return teste
    v = valoare(design)
    dm = lambda e: design.unitsManager.evaluateExpression(e, 'mm')     # -> cm
    zT = v('raza_manivela') + v('biela_L') + v('inaltime_compresie')
    R = v('diametru_piston')/2
    zp = zT - v('inaltime_compresie')
    t(pist.isSolid and bolt.isSolid, 'C3a', 'Pistonul și bolțul sunt corpuri solide')

    oriz, raze_z, raze_y = [], [], []
    for fata in pist.faces:
        g = fata.geometry
        if g.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            pl = adsk.core.Plane.cast(g)
            if abs(abs(pl.normal.z) - 1) < 1e-9:
                oriz.append(fata.pointOnFace.z)
        elif g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
            cy = adsk.core.Cylinder.cast(g)
            if abs(abs(cy.axis.z) - 1) < 1e-9:
                raze_z.append(cy.radius)
            elif abs(abs(cy.axis.y) - 1) < 1e-9:
                raze_y.append(cy.radius)
    are = lambda lista, val: any(abs(x - val) < TOL for x in lista)
    t(are(oriz, zT) and are(oriz, zT - v('lungime_fusta')), 'C3b',
      'Coroana la PMI ({:.3f} mm) și fusta lungă de {:.3f} mm'.format(zT*10, v('lungime_fusta')*10))
    t(are(raze_z, R), 'C3c', 'Diametrul pistonului {:.4f} mm; jocul radial față de alezaj {:.4f} mm'
      .format(2*R*10, (v('alezaj')/2 - R)*10))
    for nume, sus_expr, h_expr, ad_expr in CANALE:
        sus, h, ad = dm(sus_expr), dm(h_expr), dm(ad_expr)
        spate = R - ad - dm('perete_sub_canal')          # raza interioară în dreptul canalului
        t(are(oriz, zT - sus) and are(oriz, zT - sus - h) and are(raze_z, R - ad) and are(raze_z, spate), 'C3d',
          '{}: {:.3f}-{:.3f} mm sub coroană, adâncime {:.3f} mm, perete în spate {:.3f} mm'
          .format(nume, sus*10, (sus + h)*10, ad*10, dm('perete_sub_canal')*10))
    t(are(raze_y, v('alezaj_bolt')/2) and are(raze_y, v('d_bosaj')/2), 'C3e',
      'Alezajul bolțului Ø{:.4f} mm în bosaje de Ø{:.1f} mm, la {:.3f} mm sub coroană'
      .format(v('alezaj_bolt')*10, v('d_bosaj')*10, v('inaltime_compresie')*10))
    yb = [fata.pointOnFace.y for fata in bolt.faces
          if fata.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType]
    lung = (max(yb) - min(yb))*10 if yb else 0
    t(abs(lung - v('l_bolt')*10) < 1e-4 and abs(max(yb) + min(yb)) < TOL, 'C3f',
      'Bolțul: lungime {:.3f} mm, centrat'.format(lung))
    t(v('alezaj_bolt') > v('d_bolt'), 'C3g', 'Jocul bolț-piston {:.4f} mm > 0'.format((v('alezaj_bolt') - v('d_bolt'))*10))
    tor = lambda corp: [adsk.core.Torus.cast(fa.geometry) for fa in corp.faces
                        if fa.geometry.surfaceType == adsk.core.SurfaceTypes.TorusSurfaceType]
    tp, ts = tor(pist), [x for c in gaseste_toate(design, 'sigurante') for x in tor(c)]
    rc = dm('alezaj_bolt / 2 + 0.1 mm')
    ok = (len(tp) == 2 and all(abs(x.majorRadius - rc) < TOL and abs(x.minorRadius - dm('sig_d + 0.1 mm')/2) < TOL for x in tp)
          and len(ts) == 2 and all(abs(x.minorRadius - v('sig_d')/2) < TOL for x in ts))
    t(ok, 'C3h', 'Două canale și două siguranțe din sârmă de {:.1f} mm; sârma intră {:.2f} mm în alezaj și oprește bolțul'
      ' (tori găsiți: piston {}, sârmă {})'
      .format(v('sig_d')*10, (v('alezaj_bolt')/2 - (rc - v('sig_d')/2))*10, len(tp), len(ts)))
    return teste


# --- Utilitare pentru pașii 4-6 -------------------------------------------------
def _cerc_pe_axa(s, po, z_expr, d_expr, z, d):
    """Cerc cu centrul pe axa Z (în planul XZ), la înălțimea z_expr, diametru d_expr."""
    c = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, 0, z), d/2)
    s.dim.addDiameterDimension(c, s.p(d/2, 0, z + 0.3)).parameter.expression = d_expr
    if abs(z) < 1e-9:
        s.gc.addCoincident(c.centerSketchPoint, po)            # centrul în origine
    else:
        s.gc.addCoincident(c.centerSketchPoint, _axa_z(s, po))
        s.cota(po, c.centerSketchPoint, s.cota_vert, s.p(-d/2 - 0.5, 0, z/2), z_expr)
    return c


def _extrudare(comp, prof, op, ext_expr, corp=None):
    ei = comp.features.extrudeFeatures.createInput(prof, op)
    ei.setSymmetricExtent(adsk.core.ValueInput.createByString(ext_expr), False)
    if corp is not None:
        ei.participantBodies = [corp]
    return comp.features.extrudeFeatures.add(ei)


def _profil_inel(sk, d_ext, d_int):
    return min((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda pr: abs(pr.areaProperties().area - math.pi/4*(d_ext**2 - d_int**2)))


def _toate(sk):
    col = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        col.add(sk.profiles.item(i))
    return col


def _laturi_tija(s, po, r, L, x_cap, x_picior, e_cap, e_picior):
    """Cele două laturi ale tijei, de la centrul capului la centrul piciorului (capetele în ochiuri)."""
    for semn in (1, -1):
        l = s.lin.addByTwoPoints(s.p(semn*x_cap, 0, r), s.p(semn*x_picior, 0, r + L))
        s.cota(po, l.startSketchPoint, s.cota_oriz, s.p(semn*x_cap/2, 0, r - 0.4), e_cap)
        s.cota(po, l.startSketchPoint, s.cota_vert, s.p(semn*(x_cap + 0.4), 0, r/2), 'raza_manivela')
        s.cota(po, l.endSketchPoint, s.cota_oriz, s.p(semn*x_picior/2, 0, r + L + 0.4), e_picior)
        s.cota(po, l.endSketchPoint, s.cota_vert, s.p(semn*(x_picior + 0.4), 0, r + L/2), 'raza_manivela + biela_L')


def _fete(corp):
    """Fețele unui corp: plane (normală, punct) și cilindri (rază, axă, origine)."""
    plane, cil = [], []
    for fa in corp.faces:
        g = fa.geometry
        if g.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            plane.append((adsk.core.Plane.cast(g).normal, fa.pointOnFace))
        elif g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
            c = adsk.core.Cylinder.cast(g)
            cil.append((c.radius, c.axis, c.origin))
    return plane, cil


def _t():
    teste = []
    def t(ok, cod, text):
        teste.append((ok, '[{}] {:5s} {}'.format('TRECUT' if ok else 'PICAT ', cod, text)))
    return teste, t


# --- Pasul 4: biela ----------------------------------------------------------
def pas04_biela(design):
    comp = componenta_noua(design, '30_Biela')
    if comp is None:
        return 'Pasul 4: 30_Biela există deja, l-am lăsat neatins.'
    v = valoare(design)
    r, L = v('raza_manivela'), v('biela_L')
    R1, R2 = v('D_ochi_cap')/2, v('D_ochi_picior')/2
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation

    # Conturul: ochiurile și tija (mai îngustă decât ochiurile), racordate
    s = Schita(comp, comp.xZConstructionPlane, 'Contur_biela')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    _cerc_pe_axa(s, po, 'raza_manivela', 'D_ochi_cap', r, 2*R1)
    _cerc_pe_axa(s, po, 'raza_manivela + biela_L', 'D_ochi_picior', r + L, 2*R2)
    _laturi_tija(s, po, r, L, v('tija_lat_cap')/2, v('tija_lat_picior')/2, 'tija_lat_cap / 2', 'tija_lat_picior / 2')
    corp = _extrudare(comp, _toate(s.gata()), nou, 'latime_picior / 2').bodies.item(0)
    corp.name = 'Biela'
    marcheaza(corp, 'biela')
    muchii = adsk.core.ObjectCollection.create()
    for e in corp.edges:                       # colțurile tijă-ochi: muchii drepte pe Y, în afara axei
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.x - b.x) < 1e-9 and abs(a.z - b.z) < 1e-9 and abs(a.x) > 1e-6:
            muchii.add(e)
    if muchii.count != 4:
        raise RuntimeError('Biela: am găsit {} colțuri tijă-ochi în loc de 4'.format(muchii.count))
    fi = comp.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(muchii, adsk.core.ValueInput.createByString('raza_racord_biela'), True)
    comp.features.filletFeatures.add(fi).name = 'Racordari'

    # Buzunarele profilului în I: unealtă pe toată grosimea, fără inimă, scăzută din bielă
    s = Schita(comp, comp.xZConstructionPlane, 'Buzunare')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    _cerc_pe_axa(s, po, 'raza_manivela', 'D_ochi_cap', r, 2*R1)
    _cerc_pe_axa(s, po, 'raza_manivela + biela_L', 'D_ochi_picior', r + L, 2*R2)
    f = v('tija_talpa')
    _laturi_tija(s, po, r, L, v('tija_lat_cap')/2 - f, v('tija_lat_picior')/2 - f,
                 'tija_lat_cap / 2 - tija_talpa', 'tija_lat_picior / 2 - tija_talpa')
    sk = s.gata()
    ochi = (math.pi*R1*R1, math.pi*R2*R2)
    buz = [sk.profiles.item(i) for i in range(sk.profiles.count)
           if all(abs(sk.profiles.item(i).areaProperties().area - a) > 1e-4 for a in ochi)]
    if len(buz) != 1:
        raise RuntimeError('Biela: {} profile de buzunar în loc de 1'.format(len(buz)))
    unealta = _extrudare(comp, buz[0], nou, 'latime_picior / 2 + 1 mm').bodies.item(0)
    s = Schita(comp, comp.xZConstructionPlane, 'Inima')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    _cerc_pe_axa(s, po, 'raza_manivela + biela_L / 2', 'biela_L * 1.5', r + L/2, 1.5*L)
    _extrudare(comp, s.gata().profiles.item(0), taie, 'tija_inima / 2', unealta).name = 'Inima'
    unelte = adsk.core.ObjectCollection.create()
    for b in comp.bRepBodies:
        if b.name != 'Biela':
            unelte.add(b)
    ci = comp.features.combineFeatures.createInput(corp, unelte)
    ci.operation = taie
    ci.isKeepToolBodies = False
    comp.features.combineFeatures.add(ci).name = 'Buzunare'

    # Alezajele capului și piciorului
    s = Schita(comp, comp.xZConstructionPlane, 'Alezaje_biela')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    _cerc_pe_axa(s, po, 'raza_manivela', 'D_cap_biela', r, v('D_cap_biela'))
    _cerc_pe_axa(s, po, 'raza_manivela + biela_L', 'D_picior_biela', r + L, v('D_picior_biela'))
    sk = s.gata()
    col = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        col.add(sk.profiles.item(i))
    _extrudare(comp, col, taie, 'latime_picior / 2 + 1 mm', corp).name = 'Alezaje'

    # Rulmenții cu ace: cap 22 x 28, picior 15 x 19, cât lățimea bielei
    for nume, z, z_expr, de, di, de_e, di_e in [
            ('Rulment_cap', r, 'raza_manivela', v('D_cap_biela'), v('d_maneton'), 'D_cap_biela', 'd_maneton'),
            ('Rulment_picior', r + L, 'raza_manivela + biela_L', v('D_picior_biela'), v('d_bolt'), 'D_picior_biela', 'd_bolt')]:
        s = Schita(comp, comp.xZConstructionPlane, nume)
        po = s.sk.sketchPoints.add(s.p(0, 0, 0))
        po.isFixed = True
        ce = _cerc_pe_axa(s, po, z_expr, de_e, z, de)
        ci = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, 0, z), di/2)
        s.gc.addConcentric(ce, ci)
        s.dim.addDiameterDimension(ci, s.p(di/4, 0, z + 0.2)).parameter.expression = di_e
        b = _extrudare(comp, _profil_inel(s.gata(), de, di), nou, 'latime_picior / 2').bodies.item(0)
        b.name = nume
        marcheaza(b, nume.lower())
    return 'Pasul 4: 30_Biela construită (110 mm între axe, tijă în I, cu rulmenții cu ace).'


def verifica_pas04(design):
    teste, t = _t()
    b = gaseste(design, 'biela')
    if b is None:
        t(False, 'C4', '30_Biela nu are marcajele de verificare: șterge-o și rulează din nou')
        return teste
    v = valoare(design)
    r, L = v('raza_manivela'), v('biela_L')
    plane, cil = _fete(b)
    ax_y = [(raza, o) for raza, a, o in cil if abs(abs(a.y) - 1) < 1e-9]
    cap = [o.z for raza, o in ax_y if abs(raza - v('D_cap_biela')/2) < TOL]
    pic = [o.z for raza, o in ax_y if abs(raza - v('D_picior_biela')/2) < TOL]
    ok = cap and pic and abs(pic[0] - cap[0] - L) < TOL and abs(cap[0] - r) < TOL
    t(bool(ok), 'C4a', 'Biela: cap Ø{:.1f} pe maneton, picior Ø{:.1f} pe bolț, {:.3f} mm între axe (YZ125: 110)'
      .format(v('D_cap_biela')*10, v('D_picior_biela')*10, (pic[0] - cap[0])*10 if ok else 0))
    lat = sorted({round(abs(o.y), 7) for n, o in plane if abs(abs(n.y) - 1) < 1e-9})
    t(len(lat) == 2 and abs(lat[0] - v('tija_inima')/2) < TOL and abs(lat[1] - v('latime_picior')/2) < TOL, 'C4b',
      'Biela e lată de {:.2f} mm, cu inima de {:.2f} mm, simetric față de planul cilindrului'
      .format(v('latime_picior')*10, v('tija_inima')*10))
    racord = [raza for raza, o in ax_y if abs(raza - v('raza_racord_biela')) < TOL]
    t(len(gaseste_toate(design, 'biela')) == 1 and len(racord) == 4, 'C4d',
      'Biela dintr-o bucată, tijă în I cu tălpi de {:.1f} mm și patru racordări R{:.0f}; volum {:.3f} cm3'
      .format(v('tija_talpa')*10, v('raza_racord_biela')*10, b.volume))
    rc, rp = gaseste(design, 'rulment_cap'), gaseste(design, 'rulment_picior')
    ok = (rc is not None and rp is not None and
          abs(rc.volume - math.pi/4*(v('D_cap_biela')**2 - v('d_maneton')**2)*v('latime_picior')) < 1e-6 and
          abs(rp.volume - math.pi/4*(v('D_picior_biela')**2 - v('d_bolt')**2)*v('latime_picior')) < 1e-6)
    t(ok, 'C4c', 'Rulmenții cu ace: {:.0f} x {:.0f} și {:.0f} x {:.0f} x {:.1f} mm, volum exact'
      .format(v('d_maneton')*10, v('D_cap_biela')*10, v('d_bolt')*10, v('D_picior_biela')*10, v('latime_picior')*10))
    return teste


# --- Pasul 5: arborele cotit -------------------------------------------------
def _capat_conic(comp, design, corp):
    """Capătul dinspre mașina electrică (-Y), ca la YZ125: con 1:5 după simering, filet M12 x 1,25
    la capăt și locașul penei Woodruff în con (pana doar poziționează rotorul)."""
    v = valoare(design)
    f = comp.features
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    ys_e = 'y_rulment_ext + joc_simering + simering_B + joc_con'
    ys = v('y_rulment_ext') + v('joc_simering') + v('simering_B') + v('joc_con')
    L, k = v('lungime_con'), v('conicitate')
    ye = v('y_rulment_ext') + v('capat_dreapta') + 0.1
    r_j, r1, rf = v('d_fus')/2 + 0.05, v('d_con_mare')/2, v('d_filet')/2
    r2 = r1 - L/(2*k)
    # Profilul de îndepărtat (A-F), în planul YZ. Punctele se creează ușor decalate: la
    # coordonate identice Fusion le leagă singur și cotele ar fi în plus; constrângerile
    # verticală/orizontală și cele 7 cote le duc exact la loc.
    s = Schita(comp, comp.yZConstructionPlane, 'Capat_conic')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    P = lambda y, z: s.sk.sketchPoints.add(s.p(0, -y, z))
    A, B = P(ys, r_j), P(ys + 0.013, r1)
    C, D = P(ys + L, r2), P(ys + L + 0.017, rf + 0.004)
    E, F = P(ye, rf + 0.011), P(ye + 0.019, r_j - 0.007)
    pct = [A, B, C, D, E, F]
    lin = [s.lin.addByTwoPoints(pct[i], pct[(i + 1) % 6]) for i in range(6)]
    for l in (lin[0], lin[2], lin[4]):        # AB, CD, EF: perpendiculare pe axă
        s.verticala(l)
    for l in (lin[3], lin[5]):                # DE (filetul), FA (deasupra fusului): în lungul axei
        s.orizontala(l)
    for pt, y, z, e, tip in ((A, ys, r_j, ys_e, 'y'), (A, ys, r_j, 'd_fus / 2 + 0.5 mm', 'z'),
                             (B, ys, r1, 'd_con_mare / 2', 'z'),
                             (C, ys + L, r2, ys_e + ' + lungime_con', 'y'),
                             (C, ys + L, r2, 'd_con_mare / 2 - lungime_con / (2 * conicitate)', 'z'),
                             (D, ys + L, rf, 'd_filet / 2', 'z'),
                             (E, ye, rf, 'y_rulment_ext + capat_dreapta + 1 mm', 'y')):
        if tip == 'y':
            s.cota(po, pt, s.cota_oriz, s.p(0, -y/2, z + 0.3), e)
        else:
            s.cota(po, pt, s.cota_vert, s.p(0, -y - 0.3, z/2), e)
    _rotire(f, s.gata().profiles.item(0), comp.yConstructionAxis, taie, corp).name = 'Capat_conic'
    # Locașul penei Woodruff 3 x 5: discul frezei, la mijlocul conului, spre maneton (+Z)
    yk, rk = ys + L/2, r1 - L/(4*k)
    s = Schita(comp, comp.yZConstructionPlane, 'Locas_pana')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    c = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, -yk, rk - v('pana_t1') + v('pana_D')/2), v('pana_D')/2)
    s.dim.addDiameterDimension(c, s.p(0, -yk - 0.4, rk + 0.6)).parameter.expression = 'pana_D'
    s.cota(po, c.centerSketchPoint, s.cota_oriz, s.p(0, -yk/2, rk + 1.0), ys_e + ' + lungime_con / 2')
    s.cota(po, c.centerSketchPoint, s.cota_vert, s.p(0, -yk - 0.8, rk/2),
           'd_con_mare / 2 - lungime_con / (4 * conicitate) - pana_t1 + pana_D / 2')
    _extrudare(comp, s.gata().profiles.item(0), taie, 'pana_b / 2', corp).name = 'Locas_pana'
    # Filetul M12 x 1,25 pentru piulița rotorului (cosmetic)
    fata = [fa for fa in corp.faces if fa.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType
            and abs(adsk.core.Cylinder.cast(fa.geometry).radius - rf) < TOL]
    tf = f.threadFeatures
    ti = tf.createInput(fata[0], tf.createThreadInfo(False, 'ISO Metric profile', 'M12x1.25', '6g'))
    ti.isFullLength = True
    ti.isModeled = False
    tf.add(ti).name = 'Filet_M12'


def _tangenta(E, C, Rb, parte):
    """Punctul de tangență dinspre E pe cercul (C, Rb), pe partea dată (+1 dreapta, -1 stânga)."""
    vx, vz = E[0] - C[0], E[1] - C[1]
    d = math.hypot(vx, vz)
    fi, a0 = math.acos(Rb/d), math.atan2(vz, vx)
    puncte = [(C[0] + Rb*math.cos(a0 + q*fi), C[1] + Rb*math.sin(a0 + q*fi)) for q in (1, -1)]
    return max(puncte, key=lambda T: parte*T[0])


def pas05_arbore(design):
    comp = componenta_noua(design, '40_Arbore')
    if comp is None:
        return 'Pasul 5: 40_Arbore există deja, l-am lăsat neatins.'
    v = valoare(design)
    r = v('raza_manivela')
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation

    def schita(nume):
        s = Schita(comp, comp.xZConstructionPlane, nume)
        po = s.sk.sketchPoints.add(s.p(0, 0, 0))
        po.isFixed = True
        return s, po

    # Brațele: contragreutate pe ±unghi_contragr (raza brațului), bosajul manetonului și
    # tangentele dintre ele, pe toată lățimea; apoi golul din mijloc
    s, po = schita('Brate')
    R, al, Rb = v('raza_brat'), v('unghi_contragr'), v('raza_bosaj_maneton')
    bos = _cerc_pe_axa(s, po, 'raza_manivela', '2 * raza_bosaj_maneton', r, 2*Rb)
    ps, pd = (-R*math.sin(al), -R*math.cos(al)), (R*math.sin(al), -R*math.cos(al))
    arc = s.sk.sketchCurves.sketchArcs.addByThreePoints(s.p(ps[0], 0, ps[1]), s.p(0, 0, -R), s.p(pd[0], 0, pd[1]))
    s.gc.addCoincident(arc.centerSketchPoint, po)
    s.dim.addRadialDimension(arc, s.p(R*0.3, 0, -R*0.7)).parameter.expression = 'raza_brat'
    for capat_xz, semn in ((pd, 1), (ps, -1)):
        tinta = s.p(capat_xz[0], 0, capat_xz[1])
        cp = arc.startSketchPoint if arc.startSketchPoint.geometry.distanceTo(tinta) < 1e-6 else arc.endSketchPoint
        s.cota(po, cp, s.cota_oriz, s.p(capat_xz[0]/2, 0, capat_xz[1] - 0.5), 'raza_brat * sin(unghi_contragr)')
        tx, tz = _tangenta(capat_xz, (0, r), Rb, semn)
        l = s.lin.addByTwoPoints(cp, s.p(tx, 0, tz))
        s.gc.addCoincident(l.endSketchPoint, bos)
        s.gc.addTangent(l, bos)
    amb = _extrudare(comp, _toate(s.gata()), nou, 'latime_ambielaj / 2').bodies.item(0)
    amb.name = 'Ambielaj'
    marcheaza(amb, 'ambielaj')

    # Fusurile: stânga (+Y) spre variator, dreapta (-Y) spre mașina electrică (în locul aprinderii)
    s, po = schita('Fusuri')
    _cerc_pe_axa(s, po, '', 'd_fus', 0, v('d_fus'))
    sk = s.gata()
    n = sk.xDirection.crossProduct(sk.yDirection)
    st = 'latime_ambielaj / 2 + joc_rulment + rul_B + capat_stanga'
    dr = 'latime_ambielaj / 2 + joc_rulment + rul_B + capat_dreapta'
    unu, doi = (st, dr) if n.y > 0 else (dr, st)
    ei = f.extrudeFeatures.createInput(sk.profiles.item(0), uneste)
    ei.setTwoSidesExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(unu)),
                         adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(doi)))
    ei.participantBodies = [amb]
    f.extrudeFeatures.add(ei).name = 'Fusuri'

    s, po = schita('Gol_brate')
    _cerc_pe_axa(s, po, '', '2 * raza_brat + 2 mm', 0, 2*v('raza_brat') + 0.2)
    _extrudare(comp, s.gata().profiles.item(0), taie, 'gol_brate / 2', amb).name = 'Gol_brate'
    # Golul desparte ambielajul în două semi-arbori, ca la YZ125 (presați pe maneton)
    semi = pe_parti([comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)], 'Semiarbore', 'ambielaj')

    # Manetonul: alezajul în brațe, apoi bolțul presat
    s, po = schita('Alezaj_maneton')
    _cerc_pe_axa(s, po, 'raza_manivela', 'd_maneton', r, v('d_maneton'))
    ei = f.extrudeFeatures.createInput(s.gata().profiles.item(0), taie)
    ei.setSymmetricExtent(adsk.core.ValueInput.createByString('latime_ambielaj / 2 + 1 mm'), False)
    ei.participantBodies = semi
    f.extrudeFeatures.add(ei).name = 'Alezaj_maneton'
    _capat_conic(comp, design, [b for b in semi if b.name.endswith('_dreapta')][0])
    s, po = schita('Maneton')
    _cerc_pe_axa(s, po, 'raza_manivela', 'd_maneton', r, v('d_maneton'))
    man = _extrudare(comp, s.gata().profiles.item(0), nou, 'l_maneton / 2').bodies.item(0)
    man.name = 'Maneton'
    marcheaza(man, 'maneton')

    # Șaibele: inel pe tot golul, apoi locul capului de bielă
    for nume, z, z_e, de, di, de_e, di_e, ext1, ext2, rgol in [
            ('Saibe', r, 'raza_manivela', v('D_saiba'), v('d_maneton'), 'D_saiba', 'd_maneton',
             'gol_brate / 2', 'latime_picior / 2 + joc_lateral_cap / 2', 'D_saiba + 2 mm'),
            ('Rulmenti_paliere', 0, '', v('rul_D'), v('d_fus'), 'rul_D', 'd_fus',
             'latime_ambielaj / 2 + joc_rulment + rul_B', 'latime_ambielaj / 2 + joc_rulment', 'rul_D + 2 mm')]:
        s, po = schita(nume)
        ce = _cerc_pe_axa(s, po, z_e, de_e, z, de)
        ci = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, 0, z), di/2)
        s.gc.addConcentric(ce, ci)
        s.dim.addDiameterDimension(ci, s.p(di/4, 0, z + 0.2)).parameter.expression = di_e
        cunoscute = {comp.bRepBodies.item(i).name for i in range(comp.bRepBodies.count)}
        corp = _extrudare(comp, _profil_inel(s.gata(), de, di), nou, ext1).bodies.item(0)
        s, po = schita(nume + '_mijloc')
        _cerc_pe_axa(s, po, z_e, rgol, z, de + 0.2)
        _extrudare(comp, s.gata().profiles.item(0), taie, ext2, corp).name = nume + '_mijloc'
        pe_parti([b for b in comp.bRepBodies if b.name not in cunoscute],
                 {'Saibe': 'Saiba', 'Rulmenti_paliere': 'Rulment_palier'}[nume], nume.lower())
    return ('Pasul 5: 40_Arbore construit (ambielaj 55,925 mm, maneton Ø22, rulmenți 63/22, '
            'contragreutate ±{:.1f}°).'.format(math.degrees(al)))


def verifica_pas05(design):
    teste, t = _t()
    semi = gaseste_toate(design, 'ambielaj')
    if len(semi) != 2:
        t(False, 'C5', '40_Arbore trebuie să aibă doi semi-arbori marcați (are {}): șterge-l și rulează din nou'.format(len(semi)))
        return teste
    v = valoare(design)
    dm = lambda e: design.unitsManager.evaluateExpression(e, 'mm')
    r = v('raza_manivela')
    plane, cil = [], []
    for c in semi:
        pl, cy = _fete(c)
        plane += pl
        cil += cy
    ys = [o.y for nn, o in plane if abs(abs(nn.y) - 1) < 1e-9]
    are = lambda lista, val: any(abs(x - val) < TOL for x in lista)
    g, w = v('gol_brate')/2, v('latime_ambielaj')/2
    t(all(are(ys, s*x) for s in (1, -1) for x in (g, w)), 'C5a',
      'Brațe de {:.3f} mm, gol {:.2f} mm, ambielaj {:.3f} mm (YZ125: 55,90-55,95)'
      .format(v('grosime_brat')*10, v('gol_brate')*10, v('latime_ambielaj')*10))
    t(abs(max(ys) - dm('latime_ambielaj / 2 + joc_rulment + rul_B + capat_stanga')) < TOL and
      abs(min(ys) + dm('latime_ambielaj / 2 + joc_rulment + rul_B + capat_dreapta')) < TOL, 'C5b',
      'Capetele arborelui, de la rulment: {:.1f} mm spre variator (+Y), {:.1f} mm spre mașina electrică (-Y)'
      .format(v('capat_stanga')*10, v('capat_dreapta')*10))
    raze0 = [raza for raza, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(o.z) < TOL and abs(o.x) < TOL]
    razer = [raza for raza, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(o.z - r) < TOL]
    t(are(raze0, v('raza_brat')) and are(raze0, v('d_fus')/2) and are(razer, v('d_maneton')/2), 'C5c',
      'Brațe de rază {:.2f} mm, fusuri Ø{:.0f}, alezaj de maneton Ø{:.0f} la {:.2f} mm de axă'
      .format(v('raza_brat')*10, v('d_fus')*10, v('d_maneton')*10, r*10))
    rb = [raza for raza, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(o.z - r) < TOL
          and abs(raza - v('raza_bosaj_maneton')) < TOL]
    flancuri = [nn for nn, o in plane if abs(nn.y) < 1e-9 and abs(abs(nn.x) - 1) > 1e-9]   # fără pereții penei
    t(len(rb) == 2 and len(flancuri) == 4, 'C5g',
      'Brațe cu contragreutate pe ±{:.1f}°, bosaj R{:.0f} la maneton și câte două tangente (fețe plane: {})'
      .format(math.degrees(v('unghi_contragr')), v('raza_bosaj_maneton')*10, len(flancuri)))
    k = v('conicitate')
    con = [adsk.core.Cone.cast(fa.geometry) for c in semi for fa in c.faces
           if fa.geometry.surfaceType == adsk.core.SurfaceTypes.ConeSurfaceType]
    pana = [raza for raza, a, o in cil if abs(abs(a.x) - 1) < 1e-9 and abs(raza - v('pana_D')/2) < TOL]
    # Filetul cosmetic M12 x 1,25 6g aduce fața la diametrul exterior al clasei (sub 12 mm): verific
    # filetul ca atare și diametrul feței, între limitele clasei 6g (11,794-11,974 mm)
    fil = semi[0].parentComponent.features.threadFeatures.itemByName('Filet_M12')
    d_fil = [2*raza*10 for raza, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and 0.5897 <= raza <= 0.5987 + 1e-9]
    filet = [1] if fil is not None and fil.threadInfo.threadDesignation == 'M12x1.25' and len(d_fil) == 1 else []
    unghiuri = [round(math.degrees(c.halfAngle), 4) for c in con]
    t(len(con) == 1 and abs(con[0].halfAngle - math.atan(1/(2*k))) < 1e-9 and len(pana) == 1 and len(filet) == 1, 'C5h',
      'Capătul spre mașina electrică: con 1:{:.0f} (semiunghi {:.3f}°), locașul penei Woodruff de {:.0f} mm, filet M12 x 1,25'
      ' {}, Ø{:.3f} mm'
      .format(k, math.degrees(math.atan(1/(2*k))), v('pana_b')*10, fil.threadInfo.threadClass if fil else '-',
              d_fil[0] if d_fil else float('nan')))
    man = gaseste(design, 'maneton')
    t(man is not None and abs(man.volume - math.pi/4*v('d_maneton')**2*v('l_maneton')) < 1e-6, 'C5d',
      'Manetonul Ø{:.0f} x {:.1f} mm (YZ125)'.format(v('d_maneton')*10, v('l_maneton')*10))
    vol = lambda rol: (len(gaseste_toate(design, rol)), sum(c.volume for c in gaseste_toate(design, rol)))
    n, V = vol('rulmenti_paliere')
    t(n == 2 and abs(V - 2*math.pi/4*(v('rul_D')**2 - v('d_fus')**2)*v('rul_B')) < 1e-6, 'C5e',
      'Doi rulmenți 63/22 ({:.0f} x {:.0f} x {:.0f} mm) la {:.1f} mm de brațe'
      .format(v('d_fus')*10, v('rul_D')*10, v('rul_B')*10, v('joc_rulment')*10))
    n, V = vol('saibe')
    t(n == 2 and abs(V - 2*math.pi/4*(v('D_saiba')**2 - v('d_maneton')**2)*v('saiba')) < 1e-6, 'C5f',
      'Două șaibe de {:.1f} mm; jocul lateral al capului de bielă {:.2f} mm (YZ125)'
      .format(v('saiba')*10, v('joc_lateral_cap')*10))
    return teste


# --- Pasul 6: chiulasa -------------------------------------------------------
# --- Masele: volumele pieselor mobile pentru MATLAB și verificarea echilibrării ---
ROLURI_MOBILE = ['piston', 'bolt', 'sigurante', 'rulment_picior', 'biela', 'rulment_cap', 'saibe', 'maneton', 'ambielaj']


def exporta_volume(design):
    """Scrie fusion/volume_fusion.csv: volumul și centrul de masă (z, la PMI) al pieselor mobile."""
    randuri = ['rol,volum_cm3,z_mm,bucati']
    for rol in ROLURI_MOBILE:
        corpuri = gaseste_toate(design, rol)
        if not corpuri:
            return 'Volume: lipsește {}, nu am scris volume_fusion.csv.'.format(rol)
        V = sum(c.volume for c in corpuri)
        z = sum(c.volume*c.physicalProperties.centerOfMass.z for c in corpuri)/V
        randuri.append('{},{:.9f},{:.9f},{}'.format(rol, V, z*10, len(corpuri)))
    with open(os.path.join(os.path.dirname(CSV), 'volume_fusion.csv'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(randuri) + '\n')
    return 'Volume: am scris volume_fusion.csv pentru MATLAB (s12).'


def verifica_echilibrare(design):
    teste, t = _t()
    v = valoare(design)
    um = design.userParameters
    if not all(um.itemByName(n) for n in ('factor_echilibrare', 'densitate_otel', 'J_arbore_matlab')):
        t(False, 'C7', 'Lipsesc parametrii echilibrării: rulează ruleaza_tot în MATLAB')
        return teste
    if not all(gaseste_toate(design, rol) for rol in ROLURI_MOBILE):
        t(False, 'C7', 'Lipsesc piese mobile pentru echilibrare')
        return teste
    ro_o, ro_p = v('densitate_otel'), v('densitate_piston')        # g/cm3
    r, L = v('raza_manivela'), v('biela_L')                         # cm
    m = {rol: sum(c.volume for c in gaseste_toate(design, rol))*(ro_p if rol == 'piston' else ro_o)
         for rol in ROLURI_MOBILE}                                  # g
    b = gaseste(design, 'biela')
    d = b.physicalProperties.centerOfMass.z - r
    mb_rec = m['biela']*d/L
    mb_rot = m['biela'] - mb_rec
    m_rec = m['piston'] + m['bolt'] + m['sigurante'] + m['rulment_picior'] + v('masa_segmenti') + mb_rec
    rot = [c for rol in ('ambielaj', 'maneton', 'saibe') for c in gaseste_toate(design, rol)]
    U = sum(c.volume*ro_o*c.physicalProperties.centerOfMass.z for c in rot) + (m['rulment_cap'] + mb_rot)*r
    BF = -U/(m_rec*r)                                              # U + BF*m_rec*r = 0
    t(abs(BF - v('factor_echilibrare')) < 0.005, 'C7a',
      'Factorul de echilibrare cu masele din Fusion: {:.3f} (cerut {:.2f}); masa alternativă {:.1f} g'
      .format(BF, v('factor_echilibrare'), m_rec))
    J = 0.0
    for c in rot:
        pp = c.physicalProperties
        ok, ixx, iyy, izz, ixy, iyz, ixz = pp.getXYZMomentsOfInertia()
        J += iyy*(c.volume*ro_o/1000)/pp.mass                       # kg cm2, la densitatea oțelului
    J += (m['rulment_cap'] + mb_rot)/1000*r*r
    Jm = v('J_arbore_matlab')
    t(abs(J - Jm) < 0.01*Jm, 'C7b', 'Inerția arborelui din Fusion {:.3f} kg cm2 = MATLAB {:.3f} kg cm2 (în 1%)'
      .format(J, Jm))
    return teste


def pas06_chiulasa(design):
    comp = componenta_noua(design, '15_Chiulasa')
    if comp is None:
        return 'Pasul 6: 15_Chiulasa există deja, l-am lăsat neatins.'
    v = valoare(design)
    zT = v('raza_manivela') + v('biela_L') + v('inaltime_compresie')
    zd = zT + v('deck_peste_coroana')                       # puntea cilindrului
    Re = v('corp_raza')
    H, xs, h, Rs, a = v('grosime_chiulasa'), v('joc_squish'), v('adancime_bol'), v('raza_bol'), v('diametru_bol')/2
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    ax = comp.zConstructionAxis

    # Corpul: disc pe puntea cilindrului
    s = Schita(comp, comp.xZConstructionPlane, 'Corp_chiulasa')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    l1, l2, l3, l4 = s.dreptunghi(s.p(0, 0, zd), s.p(Re, 0, zd), s.p(Re, 0, zd + H), s.p(0, 0, zd + H))
    s.gc.addCoincident(po, l4)
    s.cota(po, l1.startSketchPoint, s.cota_vert, s.p(-0.8, 0, zd/2), ZT + ' + deck_peste_coroana')
    s.cota(l1.startSketchPoint, l1.endSketchPoint, s.cota_oriz, s.p(Re/2, 0, zd - 0.4), 'corp_raza')
    s.cota(l2.startSketchPoint, l2.endSketchPoint, s.cota_vert, s.p(Re + 0.6, 0, zd + H/2), 'grosime_chiulasa')
    corp = _rotire(comp.features, s.gata().profiles.item(0), ax, nou)
    corp.name = 'Chiulasa'
    marcheaza(corp, 'chiulasa')

    # Camera: treapta de squish pe tot alezajul, apoi calota sferică a bolului
    s = Schita(comp, comp.xZConstructionPlane, 'Camera_ardere')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    P = lambda x, z: s.p(x, 0, z)
    zb = zT + xs                                            # fața benzii de squish
    zc_s = zb + h - Rs                                      # centrul sferei
    l1 = s.lin.addByTwoPoints(P(0, zd - 0.1), P(v('alezaj')/2, zd - 0.1))
    l2 = s.lin.addByTwoPoints(l1.endSketchPoint, P(v('alezaj')/2, zb))
    l3 = s.lin.addByTwoPoints(l2.endSketchPoint, P(a, zb))
    arc = s.sk.sketchCurves.sketchArcs.addByThreePoints(
        l3.endSketchPoint, P(a/2, zc_s + math.sqrt(Rs*Rs - a*a/4)), P(0, zb + h))
    sus = arc.endSketchPoint if arc.endSketchPoint.geometry.distanceTo(P(0, zb + h)) < 1e-6 else arc.startSketchPoint
    l4 = s.lin.addByTwoPoints(sus, l1.startSketchPoint)
    s.orizontala(l1); s.verticala(l2); s.orizontala(l3); s.verticala(l4)
    s.gc.addCoincident(po, l4)
    s.gc.addCoincident(arc.centerSketchPoint, l4)
    s.dim.addRadialDimension(arc, P(a*0.6, zb + h*0.6)).parameter.expression = 'raza_bol'
    s.cota(po, l1.startSketchPoint, s.cota_vert, P(-0.8, zd/2), ZT + ' + deck_peste_coroana - 1 mm')
    s.cota(po, l2.startSketchPoint, s.cota_oriz, P(v('alezaj')/4, zd - 0.4), 'alezaj / 2')
    s.cota(po, l3.startSketchPoint, s.cota_vert, P(v('alezaj')/2 + 0.6, zb/2), ZT + ' + joc_squish')
    s.cota(po, l3.endSketchPoint, s.cota_oriz, P(a/2, zb - 0.3), 'diametru_bol / 2')
    _rotire(comp.features, s.gata().profiles.item(0), ax, taie, corp).name = 'Camera_ardere'

    # Bujia: alezaj vertical prin vârful bolului
    s = Schita(comp, comp.xYConstructionPlane, 'Bujie')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    c = s.sk.sketchCurves.sketchCircles.addByCenterRadius(po, v('d_bujie')/2)
    s.dim.addDiameterDimension(c, s.p(v('d_bujie'), v('d_bujie'), 0)).parameter.expression = 'd_bujie'
    sk = s.gata()
    n = sk.xDirection.crossProduct(sk.yDirection)
    ei = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), taie)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString(ZT + ' + deck_peste_coroana + grosime_chiulasa + 1 mm')),
        adsk.fusion.ExtentDirections.PositiveExtentDirection if n.z > 0 else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    ei.participantBodies = [corp]
    comp.features.extrudeFeatures.add(ei).name = 'Bujie'
    # Ce s-a scos din chiulasă până aici e doar camera și bujia: îl țin minte pentru verificarea volumului (C6a)
    corp.attributes.add(GRUP, 'volum_camera_ref', repr(corp.volume))
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    # Prezoanele M8 trec prin chiulasă (aceleași ca la cilindru)
    pl = comp.constructionPlanes.createInput()
    pl.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByString(ZT + ' + deck_peste_coroana'))
    pl = comp.constructionPlanes.add(pl)
    pl.name = 'Puntea'
    s = Schita(comp, pl, 'Prezoane_chiulasa')
    for x, y in _prezoane_xy(v):
        _cerc_fix(s, x, y, zd, 'prezon_trecere', v('prezon_trecere'))
    _extrudare_spre(comp, _toate(s.gata()), taie, 'grosime_chiulasa + 1 mm', (0, 1), corp).name = 'Prezoane_chiulasa'
    # Trecerile apei din cilindru, aliniate cu cele din puntea lui
    zf_ = zT + xs + 0.4                                     # fundul cămășii, deasupra benzii de squish
    s = Schita(comp, pl, 'Treceri_apa_chiulasa')
    for x, y in _gauri_punte_xy(v):
        _cerc_fix(s, x, y, zd, 'gauri_punte_d', v('gauri_punte_d'))
    _extrudare_spre(comp, _toate(s.gata()), taie, 'joc_squish + 5 mm - deck_peste_coroana', (0, 1), corp).name = 'Treceri_apa_chiulasa'
    # Cămașa de apă: inel între bol și margine, cu coloane la prezoane; bujia rămâne în plin
    plj = comp.constructionPlanes.createInput()
    plj.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByString(ZT + ' + joc_squish + 4 mm'))
    plj = comp.constructionPlanes.add(plj)
    plj.name = 'Apa_chiulasa'
    s = Schita(comp, plj, 'Camasa_apa_chiulasa')
    _cerc_fix(s, 0, 0, zf_, '2 * corp_raza - 8 mm', 2*Re - 0.8)
    _cerc_fix(s, 0, 0, zf_, 'diametru_bol + 8 mm', 2*a + 0.8)
    for x, y in _prezoane_xy(v):
        _cerc_fix(s, x, y, zf_, '2 * bosaj_prezon', 2*v('bosaj_prezon'))
    sk = s.gata()
    prof = max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda q: q.areaProperties().area)
    _extrudare_spre(comp, prof, taie, 'grosime_chiulasa + deck_peste_coroana - joc_squish - 9 mm', (0, 1), corp).name = 'Camasa_apa_chiulasa'
    # Ieșirea apei, sus, în spate (spre termostat și radiator)
    plo = comp.constructionPlanes.createInput()
    plo.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByString(ZT + ' + deck_peste_coroana + grosime_chiulasa'))
    plo = comp.constructionPlanes.add(plo)
    plo.name = 'Fata_chiulasei'
    zs_ = zd + H
    s = Schita(comp, plo, 'Bosaj_iesire_apa')
    _cerc_fix(s, -4.4, 0, zs_, 'racord_apa_D + 8 mm', v('racord_apa_D') + 0.8)
    _extrudare_spre(comp, s.gata().profiles.item(0), uneste, '10 mm', (0, 1), corp).name = 'Bosaj_iesire_apa'
    s = Schita(comp, plj, 'Iesire_apa')
    _cerc_fix(s, -4.4, 0, zf_, 'racord_apa_D', v('racord_apa_D'))
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'grosime_chiulasa + deck_peste_coroana - joc_squish + 7 mm', (0, 1), corp).name = 'Iesire_apa'
    # Urechea pentru tija de la cadru, sus, în față (bujia rămâne liberă pentru cheie)
    ux, uz, au = v('ureche_chiulasa_x'), zs_ + v('ureche_chiulasa_z'), v('prindere_gaura')/2 + v('prindere_perete')
    s = Schita(comp, comp.xZConstructionPlane, 'Ureche_chiulasa')
    _dreptunghi_fix(s, [(ux - au, 0, zs_ - 0.1), (ux + au, 0, zs_ - 0.1), (ux + au, 0, uz + au), (ux - au, 0, uz + au)])
    _extrudare(comp, s.gata().profiles.item(0), uneste, 'ureche_chiulasa_y / 2', corp).name = 'Ureche_chiulasa'
    s = Schita(comp, comp.xZConstructionPlane, 'Gaura_ureche_chiulasa')
    _cerc_fix(s, ux, 0, uz, 'prindere_gaura', v('prindere_gaura'))
    _extrudare(comp, s.gata().profiles.item(0), taie, 'ureche_chiulasa_y / 2 + 1 mm', corp).name = 'Gaura_ureche_chiulasa'
    return 'Pasul 6: 15_Chiulasa construită (Ø{:.0f}, squish {:.2f} mm, bol Ø{:.2f} x {:.2f} mm, răcită cu apă, urechea tijei).'.format(2*Re*10, xs*10, 2*a*10, h*10)


def verifica_pas06(design):
    teste, t = _t()
    ch = gaseste(design, 'chiulasa')
    if ch is None:
        t(False, 'C6', '15_Chiulasa nu are marcajele de verificare: șterge-o și rulează din nou')
        return teste
    v = valoare(design)
    zT = v('raza_manivela') + v('biela_L') + v('inaltime_compresie')
    zd = zT + v('deck_peste_coroana')
    Re = v('corp_raza')
    H, xs, h, Rs, a, rb = (v('grosime_chiulasa'), v('joc_squish'), v('adancime_bol'), v('raza_bol'),
                           v('diametru_bol')/2, v('d_bujie')/2)
    Ab = math.pi/4*v('alezaj')**2
    V_cal = math.pi*h*(3*a*a + h*h)/6
    zb = zT + xs
    zc_s = zb + h - Rs
    z_sus = zd + H
    V_buj = math.pi*rb*rb*(z_sus - zc_s) - 2*math.pi/3*(Rs**3 - (Rs*Rs - rb*rb)**1.5)
    V_ref = float(ch.attributes.itemByName(GRUP, 'volum_camera_ref').value)
    V_camera = math.pi*Re*Re*H - V_ref - V_buj + Ab*(zd - zT)
    t(abs(V_camera - (Ab*xs + V_cal)) < 1e-6, 'C6a',
      'Volumul camerei din Fusion {:.3f} cm3 = alezaj x squish + calota ({:.3f} cm3)'.format(V_camera, Ab*xs + V_cal))
    sfere = [adsk.core.Sphere.cast(fa.geometry).radius for fa in ch.faces
             if fa.geometry.surfaceType == adsk.core.SurfaceTypes.SphereSurfaceType]
    banda = [fa.pointOnFace.z for fa in ch.faces
             if fa.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType
             and abs(abs(adsk.core.Plane.cast(fa.geometry).normal.z) - 1) < 1e-9]
    t(len(sfere) == 1 and abs(sfere[0] - Rs) < TOL and any(abs(z - zb) < TOL for z in banda), 'C6b',
      'Banda de squish la {:.2f} mm deasupra coroanei de la PMI; bolul sferic R{:.3f} mm'.format(xs*10, Rs*10))
    # Răcirea chiulasei: trecerile din punte aliniate cu ale cilindrului, cămașa, ieșirea în spate, prezoanele
    plane, cil = _fete(ch)
    vert = lambda r_: {(round(o.x, 3), round(o.y, 3)) for r, a, o in cil if abs(abs(a.z) - 1) < 1e-9 and abs(r - r_) < TOL}
    gp, pz = vert(v('gauri_punte_d')/2), vert(v('prezon_trecere')/2)
    gp_ok = all(any(math.hypot(x - cx, y - cy) < 1e-3 for cx, cy in gp) for x, y in _gauri_punte_xy(v))
    pz_ok = all(any(math.hypot(x - cx, y - cy) < 1e-3 for cx, cy in pz) for x, y in _prezoane_xy(v))
    pe_ax = lambda r_: any(abs(r - r_) < TOL and abs(o.x) < TOL and abs(o.y) < TOL for r, a, o in cil)
    zs = [o.z for n, o in plane if abs(abs(n.z) - 1) < 1e-9]
    z_apa = zb + 0.4
    iesire = any(abs(r - v('racord_apa_D')/2) < TOL and abs(o.x + 4.4) < TOL and abs(o.y) < TOL for r, a, o in cil)
    t(gp_ok and pz_ok and pe_ax(Re - 0.4) and pe_ax(a + 0.4) and any(abs(z - z_apa) < TOL for z in zs) and iesire, 'C6c',
      'Chiulasa Ø{:.0f} răcită: cămașa R{:.0f}-{:.0f} mm la {:.0f} mm deasupra benzii de squish, 5 treceri aliniate cu puntea cilindrului, '
      '4 prezoane, ieșirea Ø{:.0f} sus în spate'.format(2*Re*10, (a + 0.4)*10, (Re - 0.4)*10, (z_apa - zb)*10, v('racord_apa_D')*10))
    return teste


# --- Pasul 8: legăturile dintre piese, rularea cinematică, exportul pentru Simscape ---
# Piesele fixe sunt ancorate. Legăturile sunt „as-built”: piesele stau deja la PMI, deci
# legătura păstrează poziția. Bucla bielă-manivelă: arbore (rotație față de cilindru),
# bielă pe maneton (rotație), piston pe bolțul bielei (rotație), piston în cilindru
# (translație pe Z); bolțul e fix în piston. Aceleași legături are modelul Simscape (m02).
FIXE = ['00_Schelet', '10_Cilindru', '15_Chiulasa', '50_Carter_stanga', '51_Carter_dreapta', '53_Lamela', '60_Stator',
        '11_Cilindru_corp', '12_Supapa', '90_Compresor', '52_Capac_dreapta', '55_Scut', '56_Pompa_ulei', '80_Toba']
LEGATURI = ['Arbore_cilindru', 'Biela_maneton', 'Biela_bolt', 'Bolt_piston', 'Piston_cilindru', 'Rotor_arbore']
PAS_CINEMATICA = 2                     # [grade] între pozițiile rulării cinematice
UNGHIURI_JOCURI = (0, 90, 180, 270)    # pozițiile la care se măsoară jocurile minime
CINEMATICA = {}                        # rezultatele ultimei rulări, pentru verificare


def ocurenta(design, nume):
    for occ in design.rootComponent.occurrences:
        if occ.component.name == nume:
            return occ
    return None


def _muchie_cerc(design, occ, rol, raza, conditie):
    """Muchia circulară (în ansamblu) a corpului cu rolul dat, de rază dată, cu centrul care îndeplinește condiția."""
    for corp in gaseste_toate(design, rol):
        for e in corp.edges:
            g = e.geometry
            if (g.curveType == adsk.core.Curve3DTypes.Circle3DCurveType and abs(g.radius - raza) < TOL
                    and conditie(g.center)):
                return e.createForAssemblyContext(occ)
    raise RuntimeError('Nu găsesc muchia circulară R{:.3f} mm pe {}'.format(raza*10, rol))


def pas08_legaturi(design):
    nume = FIXE + ['20_Piston', '21_Bolt', '30_Biela', '40_Arbore', '61_Rotor']
    occ = {n: ocurenta(design, n) for n in nume}
    lipsa = [n for n in nume if occ[n] is None]
    if lipsa:
        return 'Pasul 8: lipsesc {}, nu fac legăturile.'.format(', '.join(lipsa))
    for n in FIXE:
        occ[n].isGrounded = True
    v = valoare(design)
    r, L, b2 = v('raza_manivela'), v('biela_L'), v('latime_picior')/2
    zT = r + L + v('inaltime_compresie')
    y_st = v('latime_ambielaj')/2 + v('joc_rulment') + v('rul_B') + v('capat_stanga')
    J = design.rootComponent.asBuiltJoints
    G, C = adsk.fusion.JointGeometry, adsk.fusion.JointKeyPointTypes.CenterKeyPoint
    Z = adsk.fusion.JointDirections.ZAxisJointDirection
    pe_axa = lambda c: abs(c.x) < TOL and abs(c.y) < TOL
    definitii = [
        ('Arbore_cilindru', '40_Arbore', '10_Cilindru', '40_Arbore', 'ambielaj', v('d_fus')/2,
         lambda c: abs(c.x) < TOL and abs(c.z) < TOL and abs(c.y - y_st) < TOL, 'rotatie'),
        ('Biela_maneton', '30_Biela', '40_Arbore', '30_Biela', 'biela', v('D_cap_biela')/2,
         lambda c: abs(c.x) < TOL and abs(c.z - r) < TOL and abs(c.y - b2) < TOL, 'rotatie'),
        ('Biela_bolt', '20_Piston', '30_Biela', '30_Biela', 'biela', v('D_picior_biela')/2,
         lambda c: abs(c.x) < TOL and abs(c.z - r - L) < TOL and abs(c.y - b2) < TOL, 'rotatie'),
        ('Bolt_piston', '21_Bolt', '20_Piston', '21_Bolt', 'bolt', v('d_bolt')/2,
         lambda c: abs(c.x) < TOL and abs(c.z - r - L) < TOL and abs(c.y - v('l_bolt')/2) < TOL, 'fixa'),
        ('Piston_cilindru', '20_Piston', '10_Cilindru', '20_Piston', 'piston', v('diametru_piston')/2,
         lambda c: pe_axa(c) and abs(c.z - zT) < TOL, 'translatie'),
        ('Rotor_arbore', '61_Rotor', '40_Arbore', '61_Rotor', 'rotor_pahar', v('raza_butuc'),
         lambda c: abs(c.x) < TOL and abs(c.z) < TOL and abs(c.y + v('y_carter') + v('joc_con') + v('lungime_con')) < TOL,
         'fixa')]                       # capătul butucului (marginea conului e tăiată de canalul penei)
    noi = []
    for nume_l, o1, o2, o_geom, rol, raza, cond, tip in definitii:
        if J.itemByName(nume_l):
            continue
        ji = J.createInput(occ[o1], occ[o2], G.createByCurve(_muchie_cerc(design, occ[o_geom], rol, raza, cond), C))
        if tip == 'rotatie':
            ji.setAsRevoluteJointMotion(Z)
        elif tip == 'translatie':
            ji.setAsSliderJointMotion(Z)
        else:
            ji.setAsRigidJointMotion()
        J.add(ji).name = nume_l
        noi.append(nume_l)
    return 'Pasul 8: legături {}; piese fixe: {}.'.format(', '.join(noi) if noi else 'existente', ', '.join(FIXE))


def _corpuri(design, piese):
    """Corpurile (în ansamblu) ale pieselor date ca (componentă, rol sau None); None dacă lipsește una."""
    rez = []
    for nume_occ, rol in piese:
        occ = ocurenta(design, nume_occ)
        if occ is None:
            return None
        rez += [c.createForAssemblyContext(occ) for c in occ.component.bRepBodies
                if rol is None or (c.attributes.itemByName(GRUP, 'rol') and c.attributes.itemByName(GRUP, 'rol').value == rol)]
    return rez


CARTER = [('50_Carter_stanga', None), ('51_Carter_dreapta', None)]
PERECHI_JOCURI = [('piston_cilindru', [('20_Piston', None)], [('10_Cilindru', None)]),
                  ('piston_bratele', [('20_Piston', None)], [('40_Arbore', 'ambielaj')]),
                  ('biela_piston', [('30_Biela', 'biela')], [('20_Piston', None)]),
                  ('biela_bratele', [('30_Biela', 'biela')], [('40_Arbore', 'ambielaj')]),
                  ('bratele_cilindru', [('40_Arbore', 'ambielaj')], [('10_Cilindru', None)]),
                  ('bratele_carter', [('40_Arbore', 'ambielaj')], CARTER),
                  ('biela_carter', [('30_Biela', None)], CARTER),
                  ('piston_carter', [('20_Piston', None)], CARTER),
                  ('cilindru_carter', [('10_Cilindru', None)], CARTER),
                  ('rotor_stator', [('61_Rotor', 'magnet')], [('60_Stator', 'stator_pachet')]),
                  ('rotor_bobine', [('61_Rotor', 'rotor_pahar')], [('60_Stator', 'bobina')]),
                  ('rotor_carter', [('61_Rotor', None)], CARTER)]


def _jocuri(design):
    mm = adsk.core.Application.get().measureManager
    rez = {}
    for cheie, p1, p2 in PERECHI_JOCURI:
        A, B = _corpuri(design, p1), _corpuri(design, p2)
        rez[cheie] = (min(mm.measureMinimumDistance(a, b).value for a in A for b in B)
                      if A and B else float('nan'))
    # Squish-ul: fața coroanei față de banda de squish a chiulasei (distanța minimă piston-chiulasă
    # e jocul radial de la colțul coroanei, fiindcă banda începe din peretele alezajului)
    v = valoare(design)
    z_banda = v('raza_manivela') + v('biela_L') + v('inaltime_compresie') + v('joc_squish')
    oriz = lambda corp: [f for f in corp.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType
                         and abs(abs(adsk.core.Plane.cast(f.geometry).normal.z) - 1) < 1e-9]
    pist, op = gaseste(design, 'piston'), ocurenta(design, '20_Piston')
    coroana = max(oriz(pist), key=lambda f: f.pointOnFace.z).createForAssemblyContext(op)
    oc = ocurenta(design, '15_Chiulasa')
    benzi = [f.createForAssemblyContext(oc) for c in oc.component.bRepBodies for f in oriz(c)
             if abs(f.pointOnFace.z - z_banda) < TOL]
    rez['squish'] = min(mm.measureMinimumDistance(coroana, b).value for b in benzi) if benzi else float('nan')
    return rez


def ruleaza_cinematica(design):
    """Rotește arborele 0-360° prin legătura lui și citește pozițiile bielei și pistonului."""
    CINEMATICA.clear()
    Jb = design.rootComponent.asBuiltJoints
    if any(Jb.itemByName(n) is None for n in LEGATURI):
        return 'Cinematica: lipsesc legături, n-am rulat.'
    oa, ob, op = ocurenta(design, '40_Arbore'), ocurenta(design, '30_Biela'), ocurenta(design, '20_Piston')
    mot = adsk.fusion.RevoluteJointMotion.cast(Jb.itemByName('Arbore_cilindru').jointMotion)
    pozitii, jocuri = [], {}
    try:
        for k in range(0, 360, PAS_CINEMATICA):
            mot.rotationValue = math.radians(k)
            ta, tb, tp = oa.transform2, ob.transform2, op.transform2
            fi = math.atan2(ta.getCell(0, 2), ta.getCell(0, 0))      # rotația arborelui în jurul lui Y
            psi = math.atan2(tb.getCell(0, 2), tb.getCell(0, 0))     # rotația bielei
            tr = tp.translation
            abat_rot = max(abs(tp.getCell(i, j) - (1 if i == j else 0)) for i in range(3) for j in range(3))
            pozitii.append((math.degrees(fi) % 360, -tr.z*10, math.degrees(psi), math.hypot(tr.x, tr.y)*10, abat_rot))
            if k in UNGHIURI_JOCURI:
                jocuri[k] = _jocuri(design)
            if k % 20 == 0:
                adsk.doEvents()
    finally:
        mot.rotationValue = 0
    ta, tp = oa.transform2, op.transform2
    CINEMATICA.update(pozitii=pozitii, jocuri=jocuri,
                      pmi=max(abs(ta.getCell(i, j) - (1 if i == j else 0)) for i in range(3) for j in range(4)) +
                          abs(tp.translation.z))
    with open(os.path.join(os.path.dirname(CSV), 'cinematica_fusion.csv'), 'w', encoding='utf-8') as f:
        f.write('unghi_arbore_deg,x_piston_mm,rotatie_biela_deg,abatere_laterala_mm,abatere_rotatie_piston\n')
        for rand in pozitii:
            f.write('{:.10f},{:.10f},{:.10f},{:.3e},{:.3e}\n'.format(*rand))
    return 'Cinematica: {} poziții la {}°, jocuri la {}°; am scris cinematica_fusion.csv.'.format(
        len(pozitii), PAS_CINEMATICA, '/'.join(str(u) for u in UNGHIURI_JOCURI))


def verifica_cinematica(design):
    teste, t = _t()
    Jb = design.rootComponent.asBuiltJoints
    lipsa = [n for n in LEGATURI if Jb.itemByName(n) is None]
    fixe = all(ocurenta(design, n).isGrounded for n in FIXE)
    t(not lipsa and fixe and CINEMATICA and CINEMATICA['pmi'] < 1e-9, 'C8a',
      'Legături: {}; piese fixe ancorate; mecanismul revine la PMI după rulare'
      .format(', '.join(LEGATURI) if not lipsa else 'lipsesc ' + ', '.join(lipsa)))
    if not CINEMATICA:
        return teste
    v = valoare(design)
    r, L = v('raza_manivela'), v('biela_L')
    poz = CINEMATICA['pozitii']
    ex = max(abs(x - x_piston(r, L, math.radians(fi))*10) for fi, x, psi, lat, rot in poz)
    eb = max(abs(psi + math.degrees(math.asin(r/L*math.sin(math.radians(fi))))) for fi, x, psi, lat, rot in poz)
    acop = len({round(fi) % 360 for fi, x, psi, lat, rot in poz})
    t(ex < 1e-4 and acop == len(poz), 'C8b', 'Pistonul urmează formula bielă-manivelă în {} poziții pe o rotație: abatere max. {:.1e} mm'
      .format(len(poz), ex))
    t(eb < 1e-4, 'C8c', 'Biela urmează unghiul arcsin(lambda sin theta): abatere max. {:.1e} grade'.format(eb))
    lat = max(max(p[3] for p in poz), max(p[4] for p in poz))
    t(lat < 1e-6, 'C8d', 'Pistonul rămâne pe axa cilindrului, fără rotire: abatere max. {:.1e}'.format(lat))
    jc = CINEMATICA['jocuri']
    mm = lambda e: design.unitsManager.evaluateExpression(e, 'mm')
    asteptat = [('squish', 'C8e', 'Squish la PMI, coroana-banda chiulasei', [0], mm('joc_squish'), True),
                ('piston_cilindru', 'C8f', 'Jocul radial piston-cilindru', UNGHIURI_JOCURI,
                 mm('(alezaj - diametru_piston) / 2'), True),
                ('biela_piston', 'C8g', 'Jocul axial bielă-bosaje', UNGHIURI_JOCURI, mm('joc_axial_biela'), True),
                ('biela_bratele', 'C8h', 'Jocul bielă-brațe (șaibă + jumătate din jocul lateral)', UNGHIURI_JOCURI,
                 mm('saiba + joc_lateral_cap / 2'), True),
                ('piston_bratele', 'C8i', 'Fusta-contragreutăți la PME', [180], mm('joc_contragreutati'), False),
                ('bratele_cilindru', 'C8j', 'Brațe-cămașă', UNGHIURI_JOCURI, mm('joc_contragreutati'), False),
                ('bratele_carter', 'C8k', 'Brațe-carter (fața bosajului rulmentului)', UNGHIURI_JOCURI,
                 mm('joc_rulment'), True),
                ('biela_carter', 'C8l', 'Bielă-carter', UNGHIURI_JOCURI, mm('2 * perete_minim / 3'), False),
                ('piston_carter', 'C8m', 'Piston-carter', UNGHIURI_JOCURI, mm('2 * perete_minim / 3'), False),
                ('cilindru_carter', 'C8n', 'Cămașa în gura carterului', [0], mm('joc_gura'), True),
                ('rotor_stator', 'C8p', 'Întrefierul magneți-stator', UNGHIURI_JOCURI, mm('intrefier'), True),
                ('rotor_bobine', 'C8q', 'Discul rotorului-capetele bobinelor', UNGHIURI_JOCURI, mm('joc_capete'), True),
                ('rotor_carter', 'C8r', 'Rotorul-fața carterului', UNGHIURI_JOCURI, mm('joc_con'), True)]
    for cheie, cod, text, unghiuri, val, exact in asteptat:
        mas = [jc[u][cheie] for u in unghiuri if u in jc]
        ok = len(mas) == len(unghiuri) and (all(abs(m - val) < 1e-5 for m in mas) if exact else min(mas) >= val - 1e-6)
        t(ok, cod, '{}: {} mm la {}° ({} {:.4f} mm)'.format(
            text, '/'.join('{:.4f}'.format(m*10) for m in mas), '/'.join(str(u) for u in unghiuri),
            'cerut' if exact else 'minim', val*10))
    return teste


def exporta_multicorp(design):
    """STEP-urile pieselor și masele/inerțiile corpurilor mobile, pentru modelul Simscape (m02)."""
    folder = os.path.join(os.path.dirname(CSV), 'multicorp')
    os.makedirs(folder, exist_ok=True)
    em = design.exportManager
    for nume in ('10_Cilindru', '15_Chiulasa', '20_Piston', '30_Biela', '40_Arbore', '50_Carter_stanga', '51_Carter_dreapta',
                 '60_Stator', '61_Rotor'):
        em.execute(em.createSTEPExportOptions(os.path.join(folder, nume + '.step'), ocurenta(design, nume).component))
    v = valoare(design)
    ro = lambda corp: v(DENSITATI[corp.attributes.itemByName(GRUP, 'rol').value][1])
    randuri = ['corp,masa_kg,xG_m,yG_m,zG_m,Ixx,Iyy,Izz,Iyz,Izx,Ixy']
    for nume_corp, componente in (('arbore', ['40_Arbore']), ('biela', ['30_Biela']), ('piston', ['20_Piston', '21_Bolt']),
                                  ('rotor', ['61_Rotor'])):
        m, S = 0.0, [0.0, 0.0, 0.0]
        T = [[0.0]*3 for _ in range(3)]          # tensorul de inerție față de origine [kg cm2]
        for nume in componente:
            for c in ocurenta(design, nume).component.bRepBodies:
                pp = c.physicalProperties
                mi = c.volume*ro(c)/1000.0          # kg
                k = mi/pp.mass
                ok, ixx, iyy, izz, ixy, iyz, ixz = pp.getXYZMomentsOfInertia()
                tc = [[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]]
                g = pp.centerOfMass
                m += mi
                S = [S[0] + mi*g.x, S[1] + mi*g.y, S[2] + mi*g.z]
                T = [[T[i][j] + k*tc[i][j] for j in range(3)] for i in range(3)]
        cg = [s_/m for s_ in S]
        r2 = sum(x*x for x in cg)
        TG = [[T[i][j] - m*((r2 if i == j else 0) - cg[i]*cg[j]) for j in range(3)] for i in range(3)]
        randuri.append('{},{:.9f},{:.9e},{:.9e},{:.9e},{:.9e},{:.9e},{:.9e},{:.9e},{:.9e},{:.9e}'.format(
            nume_corp, m, cg[0]/100, cg[1]/100, cg[2]/100, TG[0][0]*1e-4, TG[1][1]*1e-4, TG[2][2]*1e-4,
            TG[1][2]*1e-4, TG[0][2]*1e-4, TG[0][1]*1e-4))
    with open(os.path.join(os.path.dirname(CSV), 'inertii_fusion.csv'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(randuri) + '\n')
    return 'Multicorp: STEP-uri în fusion/multicorp, mase și inerții în inertii_fusion.csv.'


# --- Pasul 9: carterul --------------------------------------------------------------
# Două semicartere împărțite pe planul cilindrului (Y = 0). Fiecare jumătate se construiește
# întreagă, apoi se taie cu planul XZ și se păstrează partea ei (fără ambiguitatea sensului).
def pas09_carter(design):
    rez = []
    for nume, semn in (('50_Carter_stanga', 1), ('51_Carter_dreapta', -1)):
        comp = componenta_noua(design, nume)
        if comp is None:
            rez.append('{} există deja'.format(nume))
            continue
        _semicarter(comp, design, semn)
        rez.append('{} construit'.format(nume))
    return 'Pasul 9: {}.'.format('; '.join(rez))


def _dreptunghi_pe_axa(s, po, x, z1, z2, ex, ez1, ez2):
    """Dreptunghi simetric față de axa Z, de la z1 la z2; z1 = 0 se leagă de origine."""
    l1, l2, l3, l4 = s.dreptunghi(s.p(-x, 0, z1), s.p(x, 0, z1), s.p(x, 0, z2), s.p(-x, 0, z2))
    s.cota(po, l1.startSketchPoint, s.cota_oriz, s.p(-x/2, 0, z1 - 0.3), ex)
    s.cota(po, l1.endSketchPoint, s.cota_oriz, s.p(x/2, 0, z1 - 0.3), ex)
    for l, z, ez, xt in ((l1, z1, ez1, -x - 0.4), (l3, z2, ez2, x + 0.4)):
        if abs(z) < 1e-9:
            s.gc.addCoincident(po, l)                    # latura trece prin axa arborelui
        else:
            s.cota(po, l.startSketchPoint, s.cota_vert, s.p(xt, 0, z/2), ez)


def _dreptunghi_x(s, po, x1, x2, z1, z2, ex1, ex2, ez1, ez2):
    """Dreptunghi oarecare în planul XZ, cotat din origine (x1 < 0 < x2 sau ambele de aceeași parte)."""
    l1, l2, l3, l4 = s.dreptunghi(s.p(x1, 0, z1), s.p(x2, 0, z1), s.p(x2, 0, z2), s.p(x1, 0, z2))
    s.cota(po, l1.startSketchPoint, s.cota_oriz, s.p(x1/2, 0, z1 - 0.3), ex1)
    s.cota(po, l1.endSketchPoint, s.cota_oriz, s.p(x2/2, 0, z1 - 0.3), ex2)
    s.cota(po, l1.startSketchPoint, s.cota_vert, s.p(x1 - 0.4, 0, z1/2), ez1)
    s.cota(po, l3.startSketchPoint, s.cota_vert, s.p(x2 + 0.4, 0, z2/2), ez2)


def _plan_baza(comp):
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByString('baza_cilindru'))
    pl = comp.constructionPlanes.add(pi)
    pl.name = 'Baza_cilindru'
    return pl


def _taie_in_jos(comp, sk, prof, ext_expr, corp):
    n = sk.xDirection.crossProduct(sk.yDirection)
    ei = comp.features.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(ext_expr)),
                        adsk.fusion.ExtentDirections.NegativeExtentDirection if n.z > 0
                        else adsk.fusion.ExtentDirections.PositiveExtentDirection)
    ei.participantBodies = [corp]
    return comp.features.extrudeFeatures.add(ei)


def _poligon(s, puncte):
    """Contur închis din puncte fixe (x, z) în planul XZ."""
    q = [s.sk.sketchPoints.add(s.p(x, 0, z)) for x, z in puncte]
    for i in range(len(q)):
        s.lin.addByTwoPoints(q[i], q[(i + 1) % len(q)])
    _fixeaza(q)


def _contur_baie(X, zj, zs, cj, cs):
    """Băile văzute din lateral: de la zj la zs, pe ±X, cu colțurile exterioare teșite la 45°."""
    return [(-X + cj, zj), (X - cj, zj), (X, zj + cj), (X, zs - cs), (X - cs, zs), (-X + cs, zs),
            (-X, zs - cs), (-X, zj + cj)]


def _aripioare(v):
    """Fețele de jos și de sus ale aripioarelor: din pas în pas sub axă, cu 2 mm deasupra fundului."""
    ta, pas, bj = v('aripioara_grosime'), v('aripioara_pas'), v('baie_jos')
    n = int(math.floor((bj - 0.2 - ta/2)/pas + 0.5))
    return [(-pas*(k - 0.5) - ta/2, -pas*(k - 0.5) + ta/2) for k in range(1, n + 1)]


def _plan_lamela(comp, v):
    """Planul sediului lamelei: perpendicular pe raza de la unghi_lamela, la R_ext + sa_lamela."""
    th = v('unghi_lamela')
    n = (math.cos(th), math.sin(th))
    for phi in (math.pi/2 - th, th - math.pi/2):
        pi = comp.constructionPlanes.createInput()
        pi.setByAngle(comp.yConstructionAxis, adsk.core.ValueInput.createByReal(phi), comp.xYConstructionPlane)
        pl0 = comp.constructionPlanes.add(pi)
        g = pl0.geometry.normal
        if abs(abs(g.x*n[0] + g.z*n[1]) - 1) < 1e-6:
            break
        pl0.deleteMe()
    else:
        raise RuntimeError('Nu pot așeza planul lamelei la {:.1f}°'.format(math.degrees(th)))
    pl0.name = 'Raza_lamelei'
    R = v('raza_cavitate') + v('grosime_carter') + v('sa_lamela')
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(pl0, adsk.core.ValueInput.createByReal(R*(g.x*n[0] + g.z*n[1])))
    pl = comp.constructionPlanes.add(pi)
    pl.name = 'Sediul_lamelei'
    return pl, n


def _dreptunghi_lamela(s, v, n, a, b):
    """Dreptunghi pe sediul lamelei: ±a pe cerc (tangent), ±b în lungul arborelui."""
    R = v('raza_cavitate') + v('grosime_carter') + v('sa_lamela')
    t = (-n[1], n[0])
    c = [s.sk.sketchPoints.add(s.p(R*n[0] + i*a*t[0], j*b, R*n[1] + i*a*t[1]))
         for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        s.lin.addByTwoPoints(c[i], c[(i + 1) % 4])
    _fixeaza(c)


def _extrudare_spre(comp, prof, op, expr, d, corp=None):
    """Extrudare pe o parte, în direcția dată: (x, z) sau (x, y, z)."""
    sk = (prof if hasattr(prof, 'parentSketch') else prof.item(0)).parentSketch
    n = sk.xDirection.crossProduct(sk.yDirection)
    ei = comp.features.extrudeFeatures.createInput(prof, op)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(expr)),
                        adsk.fusion.ExtentDirections.PositiveExtentDirection
                        if (n.x*d[0] + n.y*d[1] + n.z*d[2] if len(d) == 3 else n.x*d[0] + n.z*d[1]) > 0
                        else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    if corp:
        ei.participantBodies = [corp]
    return comp.features.extrudeFeatures.add(ei)


def _semicarter(comp, design, semn):
    v = valoare(design)
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    R_cav, t = v('raza_cavitate'), v('grosime_carter')
    R_ext, zb = R_cav + t, v('baza_cilindru')

    def schita(nume):
        s = Schita(comp, comp.xZConstructionPlane, nume)
        po = s.sk.sketchPoints.add(s.p(0, 0, 0))
        po.isFixed = True
        return s, po

    # Corpul: cilindrul din jurul arborelui, băile din față și din spate, gâtul de sub cilindru
    s, po = schita('Corp_cilindric')
    _cerc_pe_axa(s, po, '', '2 * (raza_cavitate + grosime_carter)', 0, 2*R_ext)
    corp = _extrudare(comp, s.gata().profiles.item(0), nou, 'y_carter').bodies.item(0)
    X, bj, cj, cs = v('baie_x'), v('baie_jos'), v('tesire_jos'), v('tesire_sus')
    s = Schita(comp, comp.xZConstructionPlane, 'Corp_baie')
    _poligon(s, _contur_baie(X, -bj, 0, cj, cs))
    _extrudare(comp, s.gata().profiles.item(0), uneste, 'y_cavitate + grosime_carter', corp).name = 'Corp_baie'
    s, po = schita('Corp_gat')
    _dreptunghi_pe_axa(s, po, v('gat_latime')/2, 0, zb, 'gat_latime / 2', '', 'baza_cilindru')
    _extrudare(comp, s.gata().profiles.item(0), uneste, 'y_carter', corp).name = 'Corp_gat'
    # Aripioarele: orizontale (în lungul vântului), pe laturile băilor, până sub fața carterului
    s = Schita(comp, comp.xZConstructionPlane, 'Aripioare')
    for z1, z2 in _aripioare(v):
        xc = lambda z: X - max(0, cj - (z + bj)) - max(0, cs + z)
        _poligon(s, [(-xc(z1), z1), (xc(z1), z1), (xc(z2), z2), (-xc(z2), z2)])
    sk = s.gata()
    _extrudare(comp, _toate(sk), uneste, 'y_aripioara', corp).name = 'Aripioare'
    # Golul băilor; peretele cavității rămâne întreg (cavitatea e închisă, doar lamela o leagă de băi)
    ci_ = (2 - math.sqrt(2))*t
    s = Schita(comp, comp.xZConstructionPlane, 'Baie')
    _poligon(s, _contur_baie(X - t, -bj + t, -t, cj - ci_, cs - ci_))
    _extrudare(comp, s.gata().profiles.item(0), taie, 'y_cavitate', corp).name = 'Baie'
    s, po = schita('Perete_cavitate')
    _cerc_pe_axa(s, po, '', '2 * (raza_cavitate + grosime_carter)', 0, 2*R_ext)
    _extrudare(comp, s.gata().profiles.item(0), uneste, 'y_cavitate', corp).name = 'Perete_cavitate'
    # Șicanele: câte un perete la mijlocul fiecărei băi, cu fante sus și jos
    sx, ts, fs = v('sicana_x'), v('sicana_grosime'), v('sicana_fanta')
    for semn_x, nume in ((1, 'Sicana_fata'), (-1, 'Sicana_spate')):
        s, po = schita(nume)
        ex = ('sicana_x - sicana_grosime / 2', 'sicana_x + sicana_grosime / 2')[::semn_x]
        _dreptunghi_x(s, po, semn_x*(sx - ts/2) if semn_x > 0 else -(sx + ts/2),
                      semn_x*(sx + ts/2) if semn_x > 0 else -(sx - ts/2), -(bj - t - fs), -(t + fs),
                      ex[0], ex[1], 'baie_jos - grosime_carter - sicana_fanta', 'grosime_carter + sicana_fanta')
        _extrudare(comp, s.gata().profiles.item(0), uneste, 'y_cavitate', corp).name = nume
    # Sediul plan al lamelei, pe peretele cavității, spre spate-jos
    pl, n_l = _plan_lamela(comp, v)
    a_s, b_s = v('fereastra_inaltime')/2 + 0.4, v('fereastra_latime')/2 + 0.4
    s = Schita(comp, pl, 'Sediu_lamela')
    _dreptunghi_lamela(s, v, n_l, a_s, b_s)
    _extrudare_spre(comp, s.gata().profiles.item(0), uneste, 'sa_lamela + grosime_carter + 3 mm',
                    (-n_l[0], -n_l[1]), corp).name = 'Sediu_lamela'

    # Cavitatea arborelui, cu fanta bielei spre gura cilindrului
    s, po = schita('Cavitate')
    _cerc_pe_axa(s, po, '', '2 * raza_cavitate', 0, 2*R_cav)
    _dreptunghi_pe_axa(s, po, v('latime_fanta')/2, 0, v('z_gura_jos') + v('perete_minim'),
                       'latime_fanta / 2', '', 'z_gura_jos + perete_minim')
    _extrudare(comp, _toate(s.gata()), taie, 'y_cavitate', corp).name = 'Cavitate'
    # Fereastra lamelei: din sediu, prin perete, în cavitate
    s = Schita(comp, pl, 'Fereastra_lamela')
    _dreptunghi_lamela(s, v, n_l, v('fereastra_inaltime')/2, v('fereastra_latime')/2)
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'sa_lamela + grosime_carter + 2 mm',
                    (-n_l[0], -n_l[1]), corp).name = 'Fereastra_lamela'
    # Bosajele rulmenților: inel până la peretele cavității, fața lui în dreptul rulmentului
    s, po = schita('Bosaje_rulmenti')
    _cerc_pe_axa(s, po, '', 'D_bosaj_rul', 0, v('D_bosaj_rul'))
    _extrudare(comp, s.gata().profiles.item(0), uneste, 'y_cavitate', corp).name = 'Bosaje_rulmenti'
    s, po = schita('Bosaje_fete')
    _cerc_pe_axa(s, po, '', 'D_bosaj_rul', 0, v('D_bosaj_rul'))
    _extrudare(comp, s.gata().profiles.item(0), taie, 'y_rulment_int', corp).name = 'Bosaje_fete'
    # Locașul bucșei și al simeringului
    for nume, d_expr, ext in (('Locas_bucsa', 'D_bucsa', 'y_rulment_ext'), ('Locas_simering', 'simering_D', 'y_carter')):
        s, po = schita(nume)
        _cerc_pe_axa(s, po, '', d_expr, 0, v(d_expr))
        _extrudare(comp, s.gata().profiles.item(0), taie, ext, corp).name = nume

    # Gura cilindrului și găurile prezoanelor, din planul bazei în jos
    pl = _plan_baza(comp)
    s = Schita(comp, pl, 'Gura_cilindru')
    po = s.sk.sketchPoints.add(s.p(0, 0, zb))
    po.isFixed = True
    c = s.sk.sketchCurves.sketchCircles.addByCenterRadius(po, v('D_gura')/2)
    s.dim.addDiameterDimension(c, s.p(v('D_gura')/2, 0.5, zb)).parameter.expression = 'D_gura'
    sk = s.gata()
    _taie_in_jos(comp, sk, sk.profiles.item(0), 'baza_cilindru - z_gura_jos', corp).name = 'Gura_cilindru'
    s = Schita(comp, pl, 'Prezoane')
    po = s.sk.sketchPoints.add(s.p(0, 0, zb))
    po.isFixed = True
    R, u = v('prezon_raza'), v('prezon_unghi')
    # Prima gaură cotată din origine; celelalte trei în oglindă față de axele schiței. Le creez
    # puțin deplasate: la coordonate identice Fusion le aliniază singur și cotele ar fi în plus.
    x, y = R*math.cos(u), R*math.sin(u)
    ax_x = s.lin.addByTwoPoints(po, s.p(1.0, 0, zb))
    ax_y = s.lin.addByTwoPoints(po, s.p(0, 1.0, zb))
    for l in (ax_x, ax_y):
        l.isConstruction = True
        s.cota(l.startSketchPoint, l.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
               s.p(0.5, 0.5, zb), '10 mm')
    s.gc.addHorizontal(ax_x)
    s.gc.addVertical(ax_y)
    cerc = lambda px, py: s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(px, py, zb), v('prezon_gaura')/2)
    c1 = cerc(x, y)
    s.cota(po, c1.centerSketchPoint, s.cota_oriz, s.p(x/2, y + 0.6, zb), 'prezon_raza * cos(prezon_unghi)')
    s.cota(po, c1.centerSketchPoint, s.cota_vert, s.p(x + 0.6, y/2, zb), 'prezon_raza * sin(prezon_unghi)')
    c2 = cerc(x + 0.05, -y - 0.05)
    s.gc.addSymmetry(c1.centerSketchPoint, c2.centerSketchPoint, ax_x)
    c3 = cerc(-x - 0.05, y + 0.05)
    s.gc.addSymmetry(c1.centerSketchPoint, c3.centerSketchPoint, ax_y)
    c4 = cerc(-x - 0.07, -y - 0.03)
    s.gc.addSymmetry(c3.centerSketchPoint, c4.centerSketchPoint, ax_x)
    for c in (c1, c2, c3, c4):
        g = c.centerSketchPoint.geometry
        s.dim.addDiameterDimension(c, adsk.core.Point3D.create(g.x + 0.4, g.y + 0.4, 0)).parameter.expression = 'prezon_gaura'
    sk = s.gata()
    _taie_in_jos(comp, sk, _toate(sk), 'prezon_adancime', corp).name = 'Prezoane'

    # Urechile de prindere pe cadru și inelul capacului din dreapta (pasul 14)
    _urechi_carter(comp, v, corp)
    v_inel = _inel_capac(comp, v, corp) + _nervura_sorb(comp, v, corp)

    # Bucșele de oțel ale rulmenților
    s, po = schita('Bucse')
    ce = _cerc_pe_axa(s, po, '', 'D_bucsa', 0, v('D_bucsa'))
    ci = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, 0, 0), v('rul_D')/2)
    s.gc.addConcentric(ce, ci)
    s.dim.addDiameterDimension(ci, s.p(v('rul_D')/4, 0, 0.3)).parameter.expression = 'rul_D'
    bucsa = _extrudare(comp, _profil_inel(s.gata(), v('D_bucsa'), v('rul_D')), nou, 'y_rulment_ext').bodies.item(0)
    s, po = schita('Bucse_mijloc')
    _cerc_pe_axa(s, po, '', 'D_bucsa + 2 mm', 0, v('D_bucsa') + 0.2)
    _extrudare(comp, s.gata().profiles.item(0), taie, 'y_rulment_int', bucsa).name = 'Bucse_mijloc'

    # Jumătatea: tai carterul cu planul XZ și păstrez partea mea (și bucșa mea)
    si = f.splitBodyFeatures.createInput(corp, comp.xZConstructionPlane, True)
    f.splitBodyFeatures.add(si)
    parte = 'stanga' if semn > 0 else 'dreapta'
    for b in list(comp.bRepBodies):
        if b.physicalProperties.centerOfMass.y*semn < 0:
            f.removeFeatures.add(b)
    for b in comp.bRepBodies:
        e_bucsa = abs(b.volume - math.pi/4*(v('D_bucsa')**2 - v('rul_D')**2)*v('rul_B')) < 1e-6
        b.name = ('Bucsa_' if e_bucsa else 'Carter_') + parte
        marcheaza(b, 'bucsa' if e_bucsa else 'carter')
        if semn < 0 and not e_bucsa:                 # inelul e doar pe dreapta: îl țin minte pentru simetrie (C9a)
            b.attributes.add(GRUP, 'volum_inel', repr(v_inel))


def verifica_pas09(design):
    teste, t = _t()
    v = valoare(design)
    jum = {}
    for nume, semn in (('50_Carter_stanga', 1), ('51_Carter_dreapta', -1)):
        occ = ocurenta(design, nume)
        if occ is None:
            t(False, 'C9', '{} lipsește'.format(nume))
            return teste
        rol = lambda c: c.attributes.itemByName(GRUP, 'rol').value if c.attributes.itemByName(GRUP, 'rol') else ''
        jum[semn] = ([c for c in occ.component.bRepBodies if rol(c) == 'carter'],
                     [c for c in occ.component.bRepBodies if rol(c) == 'bucsa'])
    ok = all(len(c) == 1 and len(b) == 1 for c, b in jum.values())
    if not ok:
        t(False, 'C9a', 'Fiecare semicarter trebuie să aibă un corp și o bucșă')
        return teste
    cs, cd = jum[1][0][0], jum[-1][0][0]
    a_i = cd.attributes.itemByName(GRUP, 'volum_inel')
    vi = float(a_i.value) if a_i else -1
    t(vi > 0 and abs(cs.volume - (cd.volume - vi)) < 1e-6 and cs.physicalProperties.centerOfMass.y > 0 > cd.physicalProperties.centerOfMass.y,
      'C9a', 'Semicarterele sunt simetrice față de planul cilindrului: {:.2f} cm3 fiecare, plus inelul capacului și nervura sorbului pe dreapta ({:.2f} cm3)'
      .format(cs.volume, vi))
    plane, cil = _fete(cs)
    ys = [o.y for n, o in plane if abs(abs(n.y) - 1) < 1e-9]
    zs = [o.z for n, o in plane if abs(abs(n.z) - 1) < 1e-9]
    ax_y = [raza for raza, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(o.x) < TOL and abs(o.z) < TOL]
    ax_z = [(raza, o) for raza, a, o in cil if abs(abs(a.z) - 1) < 1e-9]
    are = lambda lista, val: any(abs(x - val) < TOL for x in lista)
    t(all(are(ys, v(n)) for n in ('y_rulment_int', 'y_cavitate', 'y_rulment_ext', 'y_carter')) and are(ys, 0.0), 'C9b',
      'Fețe în lungul arborelui: îmbinarea la 0, bosajul la {:.4f}, cavitatea la {:.4f}, umărul rulmentului la {:.4f}, '
      'fața la {:.4f} mm'.format(*(v(n)*10 for n in ('y_rulment_int', 'y_cavitate', 'y_rulment_ext', 'y_carter'))))
    t(are(ax_y, v('D_bucsa')/2) and are(ax_y, v('simering_D')/2) and are(ax_y, v('D_bosaj_rul')/2)
      and are(ax_y, v('raza_cavitate')),
      'C9c', 'Pe axa arborelui: bucșa Ø{:.0f}, simeringul Ø{:.0f}, bosajul Ø{:.0f}, cavitatea R{:.2f} mm'
      .format(v('D_bucsa')*10, v('simering_D')*10, v('D_bosaj_rul')*10, v('raza_cavitate')*10))
    b = jum[1][1][0]
    t(abs(b.volume - math.pi/4*(v('D_bucsa')**2 - v('rul_D')**2)*v('rul_B')) < 1e-6, 'C9d',
      'Bucșa de oțel {:.0f}/{:.0f} x {:.0f} mm, cât rulmentul'.format(v('D_bucsa')*10, v('rul_D')*10, v('rul_B')*10))
    gura = [r for r, o in ax_z if abs(r - v('D_gura')/2) < TOL and abs(o.x) < TOL and abs(o.y) < TOL]
    prez = [o for r, o in ax_z if abs(r - v('prezon_gaura')/2) < TOL]
    poz_ok = all(abs(math.hypot(o.x, o.y) - v('prezon_raza')) < TOL and o.y > 0 for o in prez)
    t(len(gura) == 1 and len(prez) == 2 and poz_ok and are(zs, v('baza_cilindru')) and
      are(zs, v('baza_cilindru') - v('prezon_adancime')), 'C9e',
      'Baza la {:.1f} mm, gura Ø{:.2f}, câte două găuri M8 pe semicarter la R{:.0f} mm, adânci de {:.0f} mm'
      .format(v('baza_cilindru')*10, v('D_gura')*10, v('prezon_raza')*10, v('prezon_adancime')*10))
    xs_ = [o.x for n, o in plane if abs(abs(n.x) - 1) < 1e-9]
    X, bj, tc, cj, cs = v('baie_x'), v('baie_jos'), v('grosime_carter'), v('tesire_jos'), v('tesire_sus')
    ci_ = (2 - math.sqrt(2))*tc
    S2 = 1/math.sqrt(2)
    tes = [(1 if n.x > 0 else -1)*(n.x*o.x + n.z*o.z) for n, o in plane
           if abs(abs(n.x) - S2) < 1e-6 and abs(abs(n.z) - S2) < 1e-6 and abs(n.y) < 1e-6]
    asteptate = [sx*(Xc - c + sz*ze)*S2 for Xc, ze_j, ze_s, c_j, c_s in ((X, -bj, 0, cj, cs),
                 (X - tc, -bj + tc, -tc, cj - ci_, cs - ci_))
                 for sx in (1, -1) for sz, ze, c in ((-1, ze_j, c_j), (1, ze_s, c_s))]
    t(are(zs, -bj) and are(zs, -bj + tc) and are(zs, -tc) and are(zs, 0.0) and are(xs_, X) and are(xs_, -X)
      and are(xs_, X - tc) and are(xs_, -X + tc) and are(ys, v('y_cavitate') + tc)
      and all(are(tes, d) for d in asteptate) and abs(bj - v('raza_rotor') - v('grosime_pahar')) < 1e-9, 'C9f',
      'Băile: în față și în spate până la ±{:.0f} mm, sus la axă, jos la {:.1f} mm sub ea (cât rotorul mașinii '
      'electrice); 8 teșituri la 45° (jos {:.0f}, sus {:.0f} mm)'.format(X*10, bj*10, cj*10, cs*10))
    ar = _aripioare(v)
    t(all(are(zs, z1) and are(zs, z2) for z1, z2 in ar) and are(ys, v('y_aripioara')), 'C9g',
      'Aripioarele: {} pe fiecare latură, de {:.0f} mm, din {:.0f} în {:.0f} mm, cu vârful la {:.2f} mm '
      '({:.0f} mm sub fața carterului)'.format(len(ar), v('aripioara_grosime')*10, v('aripioara_pas')*10,
                                                v('aripioara_pas')*10, v('y_aripioara')*10,
                                                (v('y_carter') - v('y_aripioara'))*10))
    th = v('unghi_lamela')
    n_l, t_l = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
    pe_n = [(n.x*o.x + n.z*o.z)*(1 if n.x*n_l[0] + n.z*n_l[1] > 0 else -1) for n, o in plane
            if abs(n.y) < 1e-6 and abs(abs(n.x*n_l[0] + n.z*n_l[1]) - 1) < 1e-6]
    pe_t = [(n.x*o.x + n.z*o.z)*(1 if n.x*t_l[0] + n.z*t_l[1] > 0 else -1) for n, o in plane
            if abs(n.y) < 1e-6 and abs(abs(n.x*t_l[0] + n.z*t_l[1]) - 1) < 1e-6]
    sx, ts_, fs = v('sicana_x'), v('sicana_grosime'), v('sicana_fanta')
    lam = gaseste(design, 'lamela')
    h_f, w_f, tl = v('fereastra_inaltime'), v('fereastra_latime'), v('lamela_grosime')
    vol_l = (h_f + 0.4)*(w_f + 0.4)*tl
    t(are(pe_n, v('raza_cavitate') + tc + v('sa_lamela')) and are(pe_t, h_f/2) and are(pe_t, -h_f/2)
      and are(ys, w_f/2) and lam is not None and abs(lam.volume - vol_l) < 1e-6
      and all(are(xs_, d) for d in (sx - ts_/2, sx + ts_/2, -sx + ts_/2, -sx - ts_/2)), 'C9h',
      'Lamela la {:.0f}° pe cavitate: sediul plan la R{:.2f}, fereastra {:.0f} x {:.0f} mm, lamela de {:.1f} mm; '
      'șicanele la ±{:.1f} mm, cu fante de {:.0f} mm'.format(math.degrees(th), (v('raza_cavitate') + tc + v('sa_lamela'))*10,
                                                            w_f*10, h_f*10, tl*10, sx*10, fs*10))
    return teste


# --- Materialele: densitatea din parametri.m, restul proprietăților (E, nu, Rp) de la cea mai apropiată
# bază din Fusion Material Library, pentru simulările de rezistență -----------------------------------
OTEL = ('Otel C45 imbunatatit', 'densitate_otel', 'Steel AISI 1045 390 QT')       # C45 = AISI 1045
ANEXE = ('Anexe (anvelopa)', 'densitate_anexe', 'Aluminum 2014-T6')     # piese cumpărate, masa din catalog
TABLA = ('Otel tabla toba (DE CONFIRMAT)', 'densitate_otel', 'Steel AISI 1006 85 HR')   # tabla de oțel a tobei
AL_TURNAT = ('AlSi9Cu3 turnat', 'densitate_aluminiu', 'Aluminum A356 T6')           # Al-Si turnat
DENSITATI = {
    'piston': ('Al 4032 forjat', 'densitate_piston', 'Aluminum 2014-T6'),          # aliaj forjat de piston
    'carter': AL_TURNAT, 'camasa': AL_TURNAT, 'chiulasa': AL_TURNAT,
    'magnet': ('NdFeB N42SH', 'densitate_magnet', 'Iron, Cast'),                    # fragil, ca fonta
    'stator_pachet': ('Tole electrotehnice 0,2 mm', 'densitate_tole', 'Steel AISI 1006 85 HR'),
    'bobina': ('Bobinaj Cu 55%', 'densitate_bobinaj', 'Copper'),
    'corp_cilindru': AL_TURNAT, 'carcasa_compresor': AL_TURNAT, 'motor_compresor': AL_TURNAT,   # motorul: anvelopă
    'roata_compresor': ('Al 2618 forjat', 'densitate_aluminiu', 'Aluminum 2014-T6'),            # roată frezată
    'capac': AL_TURNAT, 'scut': ('Al 5754 tabla', 'densitate_aluminiu', 'Aluminum 2014-T6'),     # scutul: tablă îndoită
    'pompa_ulei': ANEXE, 'racitor_ulei': ANEXE,
    'toba': TABLA, 'flansa_toba': TABLA,
}
for _rol in ('bolt', 'sigurante', 'biela', 'rulment_cap', 'rulment_picior', 'ambielaj', 'maneton', 'saibe',
             'rulmenti_paliere', 'bucsa', 'lamela', 'rotor_pahar', 'pana', 'saiba_rotor', 'piulita', 'supapa_evacuare'):
    DENSITATI[_rol] = OTEL
MATERIALE = {}                         # numele materialului -> (densitatea cerută, baza folosită)
DENSITATE_PUSA = set()


def _materiale_biblioteci(app):
    """Toate materialele din bibliotecile Fusion, după nume (primul găsit câștigă)."""
    tot, linii = {}, []
    for i in range(app.materialLibraries.count):
        lib = app.materialLibraries.item(i)
        linii.append('# ' + lib.name)
        for j in range(lib.materials.count):
            m = lib.materials.item(j)
            tot.setdefault(m.name, m)
            linii.append(m.name)
    with open(os.path.join(AICI, 'materiale_fusion.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(linii))
    return tot


def aplica_materiale(design):
    """Copiază un material din biblioteca Fusion, îi pune densitatea din parametri și îl aplică pe roluri."""
    app = adsk.core.Application.get()
    v = valoare(design)
    bib = _materiale_biblioteci(app)
    MATERIALE.clear()
    DENSITATE_PUSA.clear()
    aplicate = 0
    for a in design.findAttributes(GRUP, 'rol'):
        corp = a.parent
        if not corp or a.value not in DENSITATI:
            continue
        nume, par, baza_nume = DENSITATI[a.value]
        mat = design.materials.itemByName(nume)
        if mat is None:
            baza = bib[baza_nume]
            mat = design.materials.addByCopy(baza, nume)
            MATERIALE[nume] = (v(par), baza.name)
        if nume not in DENSITATE_PUSA:
            dens = next(mat.materialProperties.item(i) for i in range(mat.materialProperties.count)
                        if mat.materialProperties.item(i).name == 'Density')
            dens.value = v(par)*1000.0                   # g/cm3 -> kg/m3
            DENSITATE_PUSA.add(nume)
        MATERIALE.setdefault(nume, (v(par), '-'))
        if corp.material is None or corp.material.name != nume:
            corp.material = mat
        aplicate += 1
    return 'Materiale: {} corpuri; {} materiale ({}).'.format(
        aplicate, len(MATERIALE), ', '.join('{} din {}'.format(n, b) for n, (d, b) in MATERIALE.items()))


def verifica_materiale(design):
    teste, t = _t()
    v = valoare(design)
    rau, n = [], 0
    for a in design.findAttributes(GRUP, 'rol'):
        corp = a.parent
        if not corp or a.value not in DENSITATI:
            continue
        nume, par, _ = DENSITATI[a.value]
        pp = corp.physicalProperties
        ro = pp.mass/corp.volume*1000.0                  # kg/cm3 -> g/cm3
        n += 1
        if corp.material is None or corp.material.name != nume or abs(ro - v(par)) > 1e-3*v(par):
            rau.append('{} ({:.3f} g/cm3)'.format(corp.name, ro))
    t(not rau and n > 0, 'C11', 'Materialele: {} corpuri cu densitatea din parametri.m (oțel, aluminiu, 4032, NdFeB, tole, bobinaj){}'
      .format(n, '' if not rau else '; greșite: ' + ', '.join(rau[:6])))
    return teste


# --- Lamela carterului (pasul 9b) -------------------------------------------------------
def pas09b_lamela(design):
    comp = componenta_noua(design, '53_Lamela')
    if comp is None:
        return 'Pasul 9b: 53_Lamela există deja, l-am lăsat neatins.'
    v = valoare(design)
    pl, n_l = _plan_lamela(comp, v)
    s = Schita(comp, pl, 'Lamela')
    _dreptunghi_lamela(s, v, n_l, v('fereastra_inaltime')/2 + 0.2, v('fereastra_latime')/2 + 0.2)
    lam = _extrudare_spre(comp, s.gata().profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                          'lamela_grosime', n_l).bodies.item(0)
    lam.name = 'Lamela'
    marcheaza(lam, 'lamela')
    return 'Pasul 9b: 53_Lamela construită ({:.1f} mm, peste fereastra de {:.0f} x {:.0f} mm).'.format(
        v('lamela_grosime')*10, v('fereastra_latime')*10, v('fereastra_inaltime')*10)


# --- Mașina electrică: statorul (pasul 10) și rotorul (pasul 11) --------------------------
def _plan_y(comp, expr, nume):
    """Plan paralel cu XZ la y = -(expr): partea dreaptă, a mașinii electrice."""
    for semn in ('-', ''):
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.xZConstructionPlane, adsk.core.ValueInput.createByString('{}({})'.format(semn, expr)))
        pl = comp.constructionPlanes.add(pi)
        if pl.geometry.origin.y < 0:
            pl.name = nume
            return pl
        pl.deleteMe()
    raise RuntimeError('Nu pot pune planul {} pe partea dreaptă'.format(nume))


def _faze(Q, p):
    """Steaua crestăturilor (ca în isg_geometrie.m): bobina k pe faza tensiunii k*360*p/Q."""
    nume = ['A+', 'C-', 'B+', 'A-', 'C+', 'B-']
    return [nume[int(((k*360.0*p/Q) % 360 + 30 - 1e-9) % 360 // 60)] for k in range(Q)]


def _fixeaza(puncte):
    for q in puncte:
        q.isFixed = True


def _model_la_unghi(corp):
    g = corp.physicalProperties.centerOfMass
    return math.atan2(g.z, g.x)


def pas10_stator(design):
    comp = componenta_noua(design, '60_Stator')
    if comp is None:
        return 'Pasul 10: 60_Stator există deja, l-am lăsat neatins.'
    v = valoare(design)
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    Q, p = int(round(v('nr_crestaturi'))), int(round(v('nr_poli')))//2
    Rs, Rf, Ri = v('stator_raza_ext'), v('stator_raza_fund'), v('stator_raza_int')
    Rv, bt, bo = Rs - v('dinte_varf'), v('dinte_latime'), v('deschidere_crestatura')
    L, e = v('pachet_lungime'), v('capete_bobine')
    ym = v('y_carter') + v('joc_con') + v('disc_rotor') + v('joc_capete') + e + L/2
    pl = _plan_y(comp, 'y_carter + joc_con + disc_rotor + joc_capete + capete_bobine + pachet_lungime / 2', 'Mijlocul_pachetului')
    pol = lambda r, a: (r*math.cos(a), r*math.sin(a))
    lat = lambda d, l, a: (d*math.cos(a) - l*math.sin(a), d*math.sin(a) + l*math.cos(a))
    tau = 2*math.pi/Q
    a_v = (2*math.pi*Rs/Q - bo)/(2*Rs)
    rb, rs_ = math.sqrt(Rv*Rv - bt*bt/4), math.sqrt(Rf*Rf - bt*bt/4)

    # Tolele: 12 dinți cu vârf, crestături cu fundul în arc, jugul până la Ri
    s = Schita(comp, pl, 'Tole')
    pt = lambda xz: s.sk.sketchPoints.add(s.p(xz[0], -ym, xz[1]))
    p3 = lambda xz: s.p(xz[0], -ym, xz[1])
    D = []
    for k in range(Q):
        th = math.pi/2 + k*tau
        D.append(dict(th=th, Tm=pt(pol(Rs, th - a_v)), Tp=pt(pol(Rs, th + a_v)), Um=pt(pol(Rv, th - a_v)),
                      Up=pt(pol(Rv, th + a_v)), Bm=pt(lat(rb, -bt/2, th)), Bp=pt(lat(rb, bt/2, th)),
                      Sm=pt(lat(rs_, -bt/2, th)), Sp=pt(lat(rs_, bt/2, th))))
    arcs = s.sk.sketchCurves.sketchArcs
    for k, d in enumerate(D):
        n_ = D[(k + 1) % Q]
        arcs.addByThreePoints(d['Tm'], p3(pol(Rs, d['th'])), d['Tp'])
        for a_, b_ in (('Tp', 'Up'), ('Up', 'Bp'), ('Bp', 'Sp')):
            s.lin.addByTwoPoints(d[a_], d[b_])
        arcs.addByThreePoints(d['Sp'], p3(pol(Rf, d['th'] + tau/2)), n_['Sm'])
        for a_, b_ in (('Sm', 'Bm'), ('Bm', 'Um'), ('Um', 'Tm')):
            s.lin.addByTwoPoints(n_[a_], n_[b_])
    _fixeaza([d[c] for d in D for c in ('Tm', 'Tp', 'Um', 'Up', 'Bm', 'Bp', 'Sm', 'Sp')])
    ci = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, -ym, 0), Ri)
    ci.centerSketchPoint.isFixed = True
    s.dim.addDiameterDimension(ci, s.p(Ri*0.5, -ym, Ri*0.5)).parameter.expression = '2 * stator_raza_int'
    sk = s.gata()
    prof = [sk.profiles.item(i) for i in range(sk.profiles.count)
            if abs(sk.profiles.item(i).areaProperties().area - math.pi*Ri*Ri) > 1e-3]
    miez = _extrudare(comp, prof[0], nou, 'pachet_lungime / 2').bodies.item(0)
    miez.name = 'Pachet_tole'
    marcheaza(miez, 'stator_pachet')

    # Trei urechi de prindere spre interior, cu găuri M5 (statorul se prinde de capacul din dreapta)
    s = Schita(comp, pl, 'Urechi')
    pt = lambda xz: s.sk.sketchPoints.add(s.p(xz[0], -ym, xz[1]))
    ul, uw, ug = v('ureche_lungime'), v('ureche_latime'), v('ureche_gaura')
    for a_ in (math.pi/2, math.pi/2 + 2*math.pi/3, math.pi/2 + 4*math.pi/3):
        c = [pt(lat(Ri - ul, -uw/2, a_)), pt(lat(Ri + 0.1, -uw/2, a_)), pt(lat(Ri + 0.1, uw/2, a_)), pt(lat(Ri - ul, uw/2, a_))]
        for i in range(4):
            s.lin.addByTwoPoints(c[i], c[(i + 1) % 4])
        _fixeaza(c)
        g = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(*((lat(Ri - ul/2, 0, a_)[0], -ym, lat(Ri - ul/2, 0, a_)[1]))), ug/2)
        g.centerSketchPoint.isFixed = True
        s.dim.addDiameterDimension(g, s.p(lat(Ri - ul/2, ug, a_)[0], -ym, lat(Ri - ul/2, ug, a_)[1])).parameter.expression = 'ureche_gaura'
    sk = s.gata()
    col = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        if abs(sk.profiles.item(i).areaProperties().area - math.pi*ug*ug/4) > 1e-4:
            col.add(sk.profiles.item(i))
    _extrudare(comp, col, adsk.fusion.FeatureOperations.JoinFeatureOperation, 'pachet_lungime / 2', miez).name = 'Urechi'

    # Bobinele concentrate: un sector pe dinte, mai lung cu capetele, din care scot dintele
    s = Schita(comp, pl, 'Bobina')
    pt = lambda xz: s.sk.sketchPoints.add(s.p(xz[0], -ym, xz[1]))
    r_in, r_out = Rf + 0.03, Rv - 0.03
    fi = tau/2 - 0.05/((Rf + Rv)/2)
    th = math.pi/2
    c = [pt(pol(r_in, th - fi)), pt(pol(r_out, th - fi)), pt(pol(r_out, th + fi)), pt(pol(r_in, th + fi))]
    s.lin.addByTwoPoints(c[0], c[1])
    s.sk.sketchCurves.sketchArcs.addByThreePoints(c[1], s.p(pol(r_out, th)[0], -ym, pol(r_out, th)[1]), c[2])
    s.lin.addByTwoPoints(c[2], c[3])
    s.sk.sketchCurves.sketchArcs.addByThreePoints(c[3], s.p(pol(r_in, th)[0], -ym, pol(r_in, th)[1]), c[0])
    _fixeaza(c)
    bob = _extrudare(comp, s.gata().profiles.item(0), nou, 'pachet_lungime / 2 + capete_bobine').bodies.item(0)
    unelte = adsk.core.ObjectCollection.create()
    unelte.add(miez)
    ci_ = f.combineFeatures.createInput(bob, unelte)
    ci_.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    ci_.isKeepToolBodies = True
    f.combineFeatures.add(ci_).name = 'Bobina_fara_dinte'
    ent = adsk.core.ObjectCollection.create()
    ent.add(bob)
    cp = f.circularPatternFeatures.createInput(ent, comp.yConstructionAxis)
    cp.quantity = adsk.core.ValueInput.createByReal(Q)
    cp.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    f.circularPatternFeatures.add(cp).name = 'Bobine'
    faze = _faze(Q, p)
    for b in comp.bRepBodies:
        if b.name == miez.name:
            continue
        k = int(round(((_model_la_unghi(b) - math.pi/2) % (2*math.pi))/tau)) % Q
        b.name = 'Bobina_{:02d}_{}'.format(k + 1, faze[k])
        marcheaza(b, 'bobina')
    return 'Pasul 10: 60_Stator construit ({} crestături, Ø{:.1f}/Ø{:.1f} mm, pachet {:.1f} mm, bobine {}).'.format(
        Q, 2*Rs*10, 2*Ri*10, L*10, ' '.join(faze))


def pas11_rotor(design):
    comp = componenta_noua(design, '61_Rotor')
    if comp is None:
        return 'Pasul 11: 61_Rotor există deja, l-am lăsat neatins.'
    v = valoare(design)
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    yh, Lc, k = v('y_carter') + v('joc_con'), v('lungime_con'), v('conicitate')
    r1 = v('d_con_mare')/2
    r2 = r1 - Lc/(2*k)
    Rb, td, Rr = v('raza_butuc'), v('disc_rotor'), v('raza_rotor')
    Rg, Rsub, L = Rr + v('grosime_pahar'), Rr + v('pahar_subtire'), v('pachet_lungime')
    ym0 = yh + td + v('joc_capete') + v('capete_bobine')
    yend, yg0 = ym0 + L + 0.1, ym0 - 0.1
    yh_e = 'y_carter + joc_con'
    ym0_e = yh_e + ' + disc_rotor + joc_capete + capete_bobine'

    # Paharul cu discul și butucul pe con (paharul gros doar în dreptul magneților)
    s = Schita(comp, comp.yZConstructionPlane, 'Profil_rotor')
    po = s.sk.sketchPoints.add(s.p(0, 0, 0))
    po.isFixed = True
    P = lambda y, z: s.sk.sketchPoints.add(s.p(0, -y, z))
    pts = [P(yh, r1), P(yh + Lc + 0.011, r2), P(yh + Lc, Rb + 0.013), P(yh + td + 0.017, Rb), P(yh + td, Rr + 0.019),
           P(yend + 0.023, Rr), P(yend, Rg + 0.029), P(yg0 + 0.031, Rg), P(yg0, Rsub + 0.037), P(yh + 0.041, Rsub)]
    lin = [s.lin.addByTwoPoints(pts[i], pts[(i + 1) % 10]) for i in range(10)]
    for i in (1, 3, 5, 7, 9):
        s.verticala(lin[i])
    for i in (2, 4, 6, 8):
        s.orizontala(lin[i])
    cote = [(0, 'y', yh, r1, yh_e), (0, 'z', yh, r1, 'd_con_mare / 2'),
            (1, 'y', yh + Lc, r2, yh_e + ' + lungime_con'), (1, 'z', yh + Lc, r2, 'd_con_mare / 2 - lungime_con / (2 * conicitate)'),
            (2, 'z', yh + Lc, Rb, 'raza_butuc'), (3, 'y', yh + td, Rb, yh_e + ' + disc_rotor'),
            (4, 'z', yh + td, Rr, 'raza_rotor'), (5, 'y', yend, Rr, ym0_e + ' + pachet_lungime + 1 mm'),
            (6, 'z', yend, Rg, 'raza_rotor + grosime_pahar'), (7, 'y', yg0, Rg, ym0_e + ' - 1 mm'),
            (8, 'z', yg0, Rsub, 'raza_rotor + pahar_subtire')]
    for i, tip, y, z, e in cote:
        if tip == 'y':
            s.cota(po, pts[i], s.cota_oriz, s.p(0, -y/2, z + 0.3), e)
        else:
            s.cota(po, pts[i], s.cota_vert, s.p(0, -y - 0.3, z/2), e)
    rotor = _rotire(f, s.gata().profiles.item(0), comp.yConstructionAxis, nou)
    rotor.name = 'Pahar_rotor'
    marcheaza(rotor, 'rotor_pahar')

    # Canalul penei în butuc (spre +Z, ca pana din arbore)
    t2 = v('pana_h') - v('pana_t1') + 0.02
    s = Schita(comp, comp.yZConstructionPlane, 'Canal_pana_butuc')
    c = [s.sk.sketchPoints.add(s.p(0, -y, z)) for y, z in ((yh - 0.05, r2 - 0.05), (yh + Lc + 0.05, r2 - 0.05),
                                                           (yh + Lc + 0.05, r1 + t2), (yh - 0.05, r1 + t2))]
    for i in range(4):
        s.lin.addByTwoPoints(c[i], c[(i + 1) % 4])
    _fixeaza(c)
    _extrudare(comp, s.gata().profiles.item(0), taie, 'pana_b / 2', rotor).name = 'Canal_pana_butuc'

    # Magneții: un arc lipit în pahar, apoi multiplicat pe cerc, cu polaritatea alternată
    pl = _plan_y(comp, ym0_e + ' + pachet_lungime / 2', 'Mijlocul_magnetilor')
    ym = ym0 + L/2
    s = Schita(comp, pl, 'Magnet')
    pol = lambda r, a: (r*math.cos(a), r*math.sin(a))
    pt = lambda xz: s.sk.sketchPoints.add(s.p(xz[0], -ym, xz[1]))
    Rm, am = Rr - v('grosime_magnet'), v('arc_magnet')/2
    th = math.pi/2
    c = [pt(pol(Rm, th - am)), pt(pol(Rr, th - am)), pt(pol(Rr, th + am)), pt(pol(Rm, th + am))]
    s.lin.addByTwoPoints(c[0], c[1])
    s.sk.sketchCurves.sketchArcs.addByThreePoints(c[1], s.p(pol(Rr, th)[0], -ym, pol(Rr, th)[1]), c[2])
    s.lin.addByTwoPoints(c[2], c[3])
    s.sk.sketchCurves.sketchArcs.addByThreePoints(c[3], s.p(pol(Rm, th)[0], -ym, pol(Rm, th)[1]), c[0])
    _fixeaza(c)
    mag = _extrudare(comp, s.gata().profiles.item(0), nou, 'pachet_lungime / 2').bodies.item(0)
    ent = adsk.core.ObjectCollection.create()
    ent.add(mag)
    npol = int(round(v('nr_poli')))
    cp = f.circularPatternFeatures.createInput(ent, comp.yConstructionAxis)
    cp.quantity = adsk.core.ValueInput.createByReal(npol)
    cp.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    f.circularPatternFeatures.add(cp).name = 'Magneti'
    for b in comp.bRepBodies:
        if b.name == rotor.name:
            continue
        j = int(round(((_model_la_unghi(b) - math.pi/2) % (2*math.pi))/(2*math.pi/npol))) % npol
        b.name = 'Magnet_{:02d}_{}'.format(j + 1, 'N' if j % 2 == 0 else 'S')
        marcheaza(b, 'magnet')

    # Pana Woodruff 3 x 5: discul de Ø13, tăiat la înălțimea de 5 mm
    yk, rk = yh + Lc/2, r1 - Lc/(4*k)
    zc = rk - v('pana_t1') + v('pana_D')/2
    s = Schita(comp, comp.yZConstructionPlane, 'Pana')
    cc = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, -yk, zc), v('pana_D')/2)
    cc.centerSketchPoint.isFixed = True
    s.dim.addDiameterDimension(cc, s.p(0, -yk, zc + 0.8)).parameter.expression = 'pana_D'
    pana = _extrudare(comp, s.gata().profiles.item(0), nou, 'pana_b / 2').bodies.item(0)
    z_taiere = zc - v('pana_D')/2 + v('pana_h')
    s = Schita(comp, comp.yZConstructionPlane, 'Pana_varf')
    c = [s.sk.sketchPoints.add(s.p(0, -y, z)) for y, z in ((yk - 0.8, z_taiere), (yk + 0.8, z_taiere),
                                                           (yk + 0.8, zc + 1.0), (yk - 0.8, zc + 1.0))]
    for i in range(4):
        s.lin.addByTwoPoints(c[i], c[(i + 1) % 4])
    _fixeaza(c)
    _extrudare(comp, s.gata().profiles.item(0), taie, 'pana_b', pana).name = 'Pana_varf'
    pana.name = 'Pana_Woodruff_3x5'
    marcheaza(pana, 'pana')

    # Șaiba și piulița M12 x 1,25
    y_s = yh + Lc
    gs, si, se = v('saiba_rotor_gros'), v('saiba_rotor_int')/2, v('saiba_rotor_ext')/2
    s = Schita(comp, comp.yZConstructionPlane, 'Saiba_rotor')
    c = [s.sk.sketchPoints.add(s.p(0, -y, z)) for y, z in ((y_s, si), (y_s + gs, si), (y_s + gs, se), (y_s, se))]
    for i in range(4):
        s.lin.addByTwoPoints(c[i], c[(i + 1) % 4])
    _fixeaza(c)
    saiba = _rotire(f, s.gata().profiles.item(0), comp.yConstructionAxis, nou)
    saiba.name = 'Saiba_rotor'
    marcheaza(saiba, 'saiba_rotor')
    hp, Rh = v('piulita_inaltime'), v('piulita_cheie')/math.sqrt(3)
    pl = _plan_y(comp, yh_e + ' + lungime_con + saiba_rotor_gros + piulita_inaltime / 2', 'Mijlocul_piulitei')
    yp = y_s + gs + hp/2
    s = Schita(comp, pl, 'Piulita')
    c = [s.sk.sketchPoints.add(s.p(Rh*math.cos(math.pi/6 + i*math.pi/3), -yp, Rh*math.sin(math.pi/6 + i*math.pi/3)))
         for i in range(6)]
    for i in range(6):
        s.lin.addByTwoPoints(c[i], c[(i + 1) % 6])
    _fixeaza(c)
    g = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(0, -yp, 0), v('d_filet')/2)
    g.centerSketchPoint.isFixed = True
    s.dim.addDiameterDimension(g, s.p(0.3, -yp, 0.3)).parameter.expression = 'd_filet'
    sk = s.gata()
    hexp = max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda q: q.areaProperties().area)
    piul = _extrudare(comp, hexp, nou, 'piulita_inaltime / 2').bodies.item(0)
    piul.name = 'Piulita_M12x1.25'
    marcheaza(piul, 'piulita')
    return 'Pasul 11: 61_Rotor construit (pahar Ø{:.0f}, {} magneți, pană, șaibă, piuliță M12).'.format(2*Rg*10, npol)


def _inertie_y(design, nume_comp):
    """Inerția unei componente față de axa arborelui, cu densitățile din parametri [kg cm2]."""
    v = valoare(design)
    J = 0.0
    for c in ocurenta(design, nume_comp).component.bRepBodies:
        pp = c.physicalProperties
        ok, ixx, iyy, izz, ixy, iyz, ixz = pp.getXYZMomentsOfInertia()
        J += iyy*(c.volume*v(DENSITATI[c.attributes.itemByName(GRUP, 'rol').value][1])/1000)/pp.mass
    return J


def verifica_pas10(design):
    teste, t = _t()
    v = valoare(design)
    if ocurenta(design, '60_Stator') is None or ocurenta(design, '61_Rotor') is None:
        t(False, 'C10', '60_Stator sau 61_Rotor lipsește')
        return teste
    Q, npol = int(round(v('nr_crestaturi'))), int(round(v('nr_poli')))
    miez = gaseste(design, 'stator_pachet')
    plane, cil = _fete(miez)
    varfuri = [r for r, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(r - v('stator_raza_ext')) < TOL]
    fund = [r for r, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(r - v('stator_raza_fund')) < TOL]
    gauri = [r for r, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(r - v('ureche_gaura')/2) < TOL]
    ys = sorted({round(o.y, 6) for n, o in plane if abs(abs(n.y) - 1) < 1e-9})
    lung = (ys[-1] - ys[0]) if ys else 0
    t(len(varfuri) == Q and len(fund) == Q and len(gauri) == 3 and abs(lung - v('pachet_lungime')) < TOL, 'C10a',
      'Statorul: {} dinți (vârfuri R{:.2f}), fundul crestăturilor R{:.2f}, 3 urechi M5, pachet {:.2f} mm'
      .format(len(varfuri), v('stator_raza_ext')*10, v('stator_raza_fund')*10, lung*10))
    bob = gaseste_toate(design, 'bobina')
    faze = [b.name.split('_')[-1] for b in bob]
    t(len(bob) == Q and all(sum(1 for x in faze if x[0] == f_) == Q//3 for f_ in 'ABC'), 'C10b',
      'Bobinele: {} ({}), câte {} pe fază'.format(len(bob), ' '.join(sorted(faze)), Q//3))
    mag = gaseste_toate(design, 'magnet')
    raze = set()
    for m_ in mag:
        for r, a, o in _fete(m_)[1]:
            raze.add(round(r, 6))
    t(len(mag) == npol and any(abs(r - v('raza_rotor')) < TOL for r in raze)
      and any(abs(r - v('raza_rotor') + v('grosime_magnet')) < TOL for r in raze), 'C10c',
      'Magneții: {} arce de {:.2f}°, între R{:.1f} și R{:.1f} mm'.format(len(mag), math.degrees(v('arc_magnet')),
                                                                       (v('raza_rotor') - v('grosime_magnet'))*10, v('raza_rotor')*10))
    rot = gaseste(design, 'rotor_pahar')
    con = [adsk.core.Cone.cast(fa.geometry) for fa in rot.faces if fa.geometry.surfaceType == adsk.core.SurfaceTypes.ConeSurfaceType]
    k = v('conicitate')
    t(len(con) == 1 and abs(con[0].halfAngle - math.atan(1/(2*k))) < 1e-9 and gaseste(design, 'pana') and
      gaseste(design, 'saiba_rotor') and gaseste(design, 'piulita'), 'C10d',
      'Rotorul stă pe conul 1:{:.0f} al arborelui, cu pana Woodruff, șaiba și piulița M12'.format(k))
    J, Jm = _inertie_y(design, '61_Rotor'), v('J_rotor_matlab')
    t(abs(J - Jm) < 0.02*Jm, 'C10e', 'Inerția rotorului din Fusion {:.2f} kg cm2 = MATLAB {:.2f} kg cm2 (în 2%)'.format(J, Jm))
    return teste


# --- Corpul cilindrului cu galeria de admisie (pasul 12) și compresorul electric (pasul 13) ---
def _plan_z(comp, expr, nume):
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByString(expr))
    pl = comp.constructionPlanes.add(pi)
    pl.name = nume
    return pl


def _plan_x_spate(comp, expr, nume):
    """Plan paralel cu YZ la x = -(expr): în spatele cilindrului."""
    for semn in ('-', ''):
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.yZConstructionPlane, adsk.core.ValueInput.createByString('{}({})'.format(semn, expr)))
        pl = comp.constructionPlanes.add(pi)
        if pl.geometry.origin.x < 0:
            pl.name = nume
            return pl
        pl.deleteMe()
    raise RuntimeError('Nu pot pune planul {} în spate'.format(nume))


def _plan_x_la(comp, x, nume):
    """Plan paralel cu YZ la x dat (numeric)."""
    for d in (x, -x):
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.yZConstructionPlane, adsk.core.ValueInput.createByReal(d))
        pl = comp.constructionPlanes.add(pi)
        if abs(pl.geometry.origin.x - x) < 1e-9:
            pl.name = nume
            return pl
        pl.deleteMe()
    raise RuntimeError('Nu pot pune planul {} la x = {:.2f}'.format(nume, x))


def _cerc_fix(s, x, y, z, d_expr, d):
    c = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(x, y, z), d/2)
    c.centerSketchPoint.isFixed = True
    g = c.centerSketchPoint.geometry
    s.dim.addDiameterDimension(c, adsk.core.Point3D.create(g.x + d/2, g.y + d/2, 0)).parameter.expression = d_expr
    return c


def _prezoane_xy(v):
    R, u = v('prezon_raza'), v('prezon_unghi')
    return [(R*math.cos(a), R*math.sin(a)) for a in (u, -u, math.pi - u, math.pi + u)]


TRANSFERURI = [('A_plus', 'unghi_tA', 'latime_tA', 1), ('A_minus', 'unghi_tA', 'latime_tA', -1),
               ('B_plus', 'unghi_tB', 'latime_tB', 1), ('B_minus', 'unghi_tB', 'latime_tB', -1),
               ('C_boost', 'unghi_tC', 'latime_tC', 1)]


def _plan_y_la(comp, y, nume):
    """Plan paralel cu XZ la y dat (numeric)."""
    for d in (y, -y):
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(comp.xZConstructionPlane, adsk.core.ValueInput.createByReal(d))
        pl = comp.constructionPlanes.add(pi)
        if abs(pl.geometry.origin.y - y) < 1e-9:
            pl.name = nume
            return pl
        pl.deleteMe()
    raise RuntimeError('Nu pot pune planul {} la y = {:.2f}'.format(nume, y))


def _plan_radial(comp, fi, nume):
    """Plan vertical prin axa cilindrului, care conține direcția de la unghiul fi (de la +X spre +Y)."""
    e = (math.cos(fi), math.sin(fi))
    for a in (fi, -fi, math.pi - fi, fi - math.pi):
        pi = comp.constructionPlanes.createInput()
        pi.setByAngle(comp.zConstructionAxis, adsk.core.ValueInput.createByReal(a), comp.xZConstructionPlane)
        pl = comp.constructionPlanes.add(pi)
        n = pl.geometry.normal
        if abs(n.x*e[0] + n.y*e[1]) < 1e-6 and abs(n.z) < 1e-6:
            pl.name = nume
            return pl
        pl.deleteMe()
    raise RuntimeError('Nu pot pune planul {}'.format(nume))


def _dreptunghi_fix(s, pts3):
    q = [s.sk.sketchPoints.add(s.p(*p)) for p in pts3]
    for i in range(len(q)):
        s.lin.addByTwoPoints(q[i], q[(i + 1) % len(q)])
    _fixeaza(q)


def _cilindru_apa_evacuare(comp, v, corp):
    """Corpul cilindrului: evacuarea cu tranziție și ștuț, urechile pentru arcuri, ghilotina, domurile
    injectoarelor, cămașa de apă în C cu intrarea pe dreapta și trecerile spre chiulasă."""
    f = comp.features
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    sus, spre_x = (0, 1), (1, 0)
    Rc, Rl, Rg = v('corp_raza'), v('raza_camasa'), v('galerie_raza')
    zf, ze, w = v('z_fereastra_jos'), v('z_evacuare_sus'), v('latime_evacuare')
    g = _geometrie_evacuare(v)
    zem, De, Ro = g['zem'], v('evacuare_D'), g['Ro']
    # 1. Flanșa (întâi plinul, apoi golurile): placă cu doi prezoane M8 de o parte și de alta a gurii; toba se strânge
    # pe ea cu garnitură. Placa începe la raza galeriei, ca să nu umple nimic din ea.
    yp, rb = g['y_prezon'], v('flansa_bosaj_R')
    xp = Rc - 0.4
    s = Schita(comp, _plan_x_la(comp, xp, 'Flansa_evacuare'), 'Flansa_evacuare')
    _cerc_fix(s, xp, 0, zem, 'evacuare_D + 2 * flansa_perete', 2*Ro)
    for sy in (1, -1):
        _cerc_fix(s, xp, sy*yp, zem, '2 * flansa_bosaj_R', 2*rb)
    _dreptunghi_fix(s, [(xp, -yp, zem - rb), (xp, yp, zem - rb), (xp, yp, zem + rb), (xp, -yp, zem + rb)])
    _extrudare_spre(comp, _toate(s.gata()), uneste, 'flansa_grosime + 4 mm', spre_x, corp).name = 'Flansa_evacuare'
    # 2. Tranziția dreptunghi - cerc (aceeași arie), de la capătul conductei drepte la fața corpului; gura prin flanșă
    x1 = Rl + 0.9
    s = Schita(comp, _plan_x_la(comp, x1, 'Evacuare_dreptunghi'), 'Evacuare_dreptunghi')
    _dreptunghi_fix(s, [(x1, -w/2, zf), (x1, w/2, zf), (x1, w/2, ze), (x1, -w/2, ze)])
    p1 = s.gata().profiles.item(0)
    pl_c = _plan_x_la(comp, Rc, 'Evacuare_cerc')
    s = Schita(comp, pl_c, 'Evacuare_cerc')
    _cerc_fix(s, Rc, 0, zem, 'evacuare_D', De)
    p2 = s.gata().profiles.item(0)
    li = f.loftFeatures.createInput(taie)
    li.loftSections.add(p1)
    li.loftSections.add(p2)
    li.participantBodies = [corp]
    f.loftFeatures.add(li).name = 'Evacuare_tranzitie'
    s = Schita(comp, pl_c, 'Gura_evacuare')
    _cerc_fix(s, Rc, 0, zem, 'evacuare_D', De)
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'flansa_grosime + 1 mm', spre_x, corp).name = 'Gura_evacuare'
    # 3. Găurile filetate ale prezoanelor (burghiu Ø6,8 pentru M8), cât filetul cerut
    xf = Rc + v('flansa_grosime')
    s = Schita(comp, _plan_x_la(comp, xf, 'Fata_flansei'), 'Prezoane_evacuare')
    for sy in (1, -1):
        _cerc_fix(s, xf, sy*yp, zem, '6.8 mm', 0.68)
    _extrudare_spre(comp, _toate(s.gata()), taie, 'flansa_filet', (-1, 0), corp).name = 'Prezoane_evacuare'
    # 4. Ghilotina: fanta lângă cămașă (coboară sub fereastră cât cursa, mai lată decât fereastra); deasupra,
    # buzunarul deschis în punte (lama se montează de sus, chiulasa îl închide); carcasa cu axul servomotorului
    # deasupra ștuțului, legată de buzunar printr-o fereastră pentru pârghie
    yl, xa, xb = g['y_fanta'], Rl - 0.001, g['x_fanta']
    s = Schita(comp, _plan_z(comp, 'z_evacuare_sus - cursa_supapa - 1 mm', 'Fanta_ghilotina'), 'Fanta_ghilotina')
    zz = ze - v('cursa_supapa') - 0.1
    _dreptunghi_fix(s, [(xa, -yl, zz), (xb, -yl, zz), (xb, yl, zz), (xa, yl, zz)])
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'cursa_supapa + lama_rezerva + 2 mm', sus, corp).name = 'Fanta_ghilotina'
    zk = g['z_buzunar']
    s = Schita(comp, _plan_z(comp, 'z_evacuare_sus + lama_rezerva', 'Buzunar_ghilotina'), 'Buzunar_ghilotina')
    _dreptunghi_fix(s, [(xa, -yl, zk), (Rc - 0.6, -yl, zk), (Rc - 0.6, yl, zk), (xa, yl, zk)])
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'z_punte - z_evacuare_sus - lama_rezerva + 1 mm', sus, corp).name = 'Buzunar_ghilotina'
    s = Schita(comp, comp.xZConstructionPlane, 'Carcasa_ghilotina')
    _dreptunghi_fix(s, [(Rc - 0.4, 0, g['z_carcasa']), (Rc + 1.2, 0, g['z_carcasa']), (Rc + 1.2, 0, v('z_punte')), (Rc - 0.4, 0, v('z_punte'))])
    _extrudare(comp, s.gata().profiles.item(0), uneste, 'latime_evacuare / 2 + 8 mm', corp).name = 'Carcasa_ghilotina'
    zs = g['z_ax']
    s = Schita(comp, comp.xZConstructionPlane, 'Fereastra_parghie')
    _dreptunghi_fix(s, [(Rc - 0.7, 0, zs - 0.45), (Rc + 0.9, 0, zs - 0.45), (Rc + 0.9, 0, zs + 0.45), (Rc - 0.7, 0, zs + 0.45)])
    _extrudare(comp, s.gata().profiles.item(0), taie, '4 mm', corp).name = 'Fereastra_parghie'
    s = Schita(comp, _plan_y_la(comp, w/2 + 0.81, 'Ax_servo'), 'Ax_servo')
    _cerc_fix(s, g['x_ax'], w/2 + 0.81, zs, '8 mm', 0.8)
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'latime_evacuare + 17 mm', (0, -1, 0), corp).name = 'Ax_servo'
    # 5. Cămașa de apă: inel deasupra ferestrelor, plin în față (ghilotina), coloane la prezoane ocolite pe interior
    z1 = v('apa_z1')
    s = Schita(comp, _plan_z(comp, 'apa_z1', 'Apa_jos'), 'Camasa_apa')
    _cerc_fix(s, 0, 0, z1, '2 * galerie_raza', 2*Rg)
    _cerc_fix(s, 0, 0, z1, '2 * apa_raza_int', 2*v('apa_raza_int'))
    for x, y in _prezoane_xy(v):
        _cerc_fix(s, x, y, z1, '2 * bosaj_prezon', 2*v('bosaj_prezon'))
    yf = v('apa_fata_y')
    _dreptunghi_fix(s, [(0, -yf, z1), (Rc + 1, -yf, z1), (Rc + 1, yf, z1), (0, yf, z1)])
    sk = s.gata()
    prof = max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda q: q.areaProperties().area)
    _extrudare_spre(comp, prof, taie, 'apa_z2 - apa_z1', sus, corp).name = 'Camasa_apa'
    # Intrarea apei radial, pe dreapta-spate (dinspre camera modulului din capacul drept), și trecerile spre chiulasă
    zm, fi = (z1 + v('apa_z2'))/2, v('apa_intrare_unghi')
    e = (math.cos(fi), math.sin(fi))
    pt = lambda r: (r*e[0], r*e[1], zm)
    s = Schita(comp, _plan_normal(comp, fi, Rc - 0.3, 'Intrare_apa'), 'Bosaj_apa')
    _cerc_fix(s, *pt(Rc - 0.3), 'racord_apa_D + 8 mm', v('racord_apa_D') + 0.8)
    _extrudare_spre(comp, s.gata().profiles.item(0), uneste, '13 mm', (e[0], e[1], 0), corp).name = 'Bosaj_apa'
    s = Schita(comp, _plan_normal(comp, fi, Rc + 1.0, 'Racord_apa'), 'Racord_apa')
    _cerc_fix(s, *pt(Rc + 1.0), 'racord_apa_D', v('racord_apa_D'))
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'corp_raza + 10 mm - (apa_raza_int + galerie_raza) / 2',
                    (-e[0], -e[1], 0), corp).name = 'Racord_apa'
    s = Schita(comp, _plan_z(comp, 'apa_z2', 'Apa_sus'), 'Treceri_apa')
    for x, y in _gauri_punte_xy(v):
        _cerc_fix(s, x, y, v('apa_z2'), 'gauri_punte_d', v('gauri_punte_d'))
    _extrudare_spre(comp, _toate(s.gata()), taie, 'z_punte - apa_z2 + 1 mm', sus, corp).name = 'Treceri_apa'


GAURI_PUNTE = [70, 110, 180, -110, -70]          # ca în parametri.m (unghi_gauri_punte) [grade]


def _gauri_punte_xy(v):
    R = v('gauri_punte_R')
    return [(R*math.cos(math.radians(u)), R*math.sin(math.radians(u))) for u in GAURI_PUNTE]


def _geometrie_evacuare(v):
    """Cotele evacuării și ale ghilotinei, folosite la construcție și la verificare."""
    Rc, Rl, ze, w = v('corp_raza'), v('raza_camasa'), v('z_evacuare_sus'), v('latime_evacuare')
    g = dict(zem=(v('z_fereastra_jos') + ze)/2, Ro=v('evacuare_D')/2 + v('flansa_perete'))
    g['y_prezon'] = v('flansa_prezon_y')
    g['y_fanta'] = w/2 + v('lama_margine')
    g['x_fanta'] = Rl + v('lama_grosime') + 2*v('lama_joc')
    g['z_buzunar'] = ze + v('lama_rezerva')
    g['z_carcasa'] = g['zem'] + g['Ro'] + 0.3                 # 3 mm deasupra flanșei
    g['z_ax'] = g['z_carcasa'] + 0.75                         # axul servomotorului: 3,5 mm de perete dedesubt
    g['x_ax'] = Rc + 0.5
    # Lama, la deschis: de la marginea ferestrei în sus; închisă coboară cât cursa și rămâne 3 mm în buzunar
    g['lama'] = dict(x=Rl - 0.001 + v('lama_joc'), y=g['y_fanta'] - v('lama_joc'), z=ze,
                     h=v('lama_rezerva') + v('cursa_supapa') + 0.3)
    return g


def pas12b_supapa(design):
    """Lama ghilotinei evacuării, în poziția deschisă, ca piesă separată (oțel inoxidabil)."""
    comp = componenta_noua(design, '12_Supapa')
    if comp is None:
        return 'Pasul 12b: 12_Supapa există deja, l-am lăsat neatins.'
    v = valoare(design)
    L = _geometrie_evacuare(v)['lama']
    s = Schita(comp, _plan_x_la(comp, L['x'], 'Lama'), 'Lama')
    _dreptunghi_fix(s, [(L['x'], -L['y'], L['z']), (L['x'], L['y'], L['z']), (L['x'], L['y'], L['z'] + L['h']), (L['x'], -L['y'], L['z'] + L['h'])])
    corp = _extrudare_spre(comp, s.gata().profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                           'lama_grosime', (1, 0), None).bodies.item(0)
    corp.name = 'Lama_ghilotina'
    marcheaza(corp, 'supapa_evacuare')
    return 'Pasul 12b: 12_Supapa construită (lama {:.1f} x {:.1f} x {:.1f} mm, deschisă).'.format(
        v('lama_grosime')*10, 2*L['y']*10, L['h']*10)


def pas12_cilindru_corp(design):
    comp = componenta_noua(design, '11_Cilindru_corp')
    if comp is None:
        return 'Pasul 12: 11_Cilindru_corp există deja, l-am lăsat neatins.'
    v = valoare(design)
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    sus, spre_x = (0, 1), (1, 0)
    Rc, Rl, Rg, Rk = v('corp_raza'), v('raza_camasa'), v('galerie_raza'), v('canal_raza')
    zb, z1, z2 = v('baza_cilindru'), v('galerie_z1'), v('galerie_z2')
    zgm = (z1 + z2)/2
    # Corpul: inel de la baza cilindrului până la punte, cămașa presată în el
    pl = _plan_baza(comp)
    s = Schita(comp, pl, 'Corp_cilindru')
    _cerc_fix(s, 0, 0, zb, '2 * corp_raza', 2*Rc)
    _cerc_fix(s, 0, 0, zb, '2 * raza_camasa', 2*Rl)
    sk = s.gata()
    corp = _extrudare_spre(comp, _profil_inel(sk, 2*Rc, 2*Rl), nou, 'z_punte - baza_cilindru', sus).bodies.item(0)
    corp.name = 'Corp_cilindru'
    marcheaza(corp, 'corp_cilindru')
    # Jos, laturile plane la fața carterului: altfel corpul, mai lat decât carterul, ar atinge paharul rotorului
    yc_ = v('y_carter')
    s = Schita(comp, pl, 'Laturi_corp')
    for sy in (1, -1):
        q = [s.sk.sketchPoints.add(s.p(x, sy*y, zb)) for x, y in ((-Rc - 0.1, yc_), (Rc + 0.1, yc_), (Rc + 0.1, Rc + 0.1), (-Rc - 0.1, Rc + 0.1))]
        for i in range(4):
            s.lin.addByTwoPoints(q[i], q[(i + 1) % 4])
        _fixeaza(q)
    sk = s.gata()
    _extrudare_spre(comp, _toate(sk), taie, 'raza_rotor + grosime_pahar + joc_con - baza_cilindru', sus, corp).name = 'Laturi_corp'
    # Prezoanele M8 trec prin cilindru până la chiulasă
    s = Schita(comp, pl, 'Prezoane_cilindru')
    for x, y in _prezoane_xy(v):
        _cerc_fix(s, x, y, zb, 'prezon_trecere', v('prezon_trecere'))
    sk = s.gata()
    _extrudare_spre(comp, _toate(sk), taie, 'z_punte - baza_cilindru', sus, corp).name = 'Prezoane_cilindru'
    # Galeria inelară, sub ferestre, cu coloane în jurul prezoanelor
    s = Schita(comp, _plan_z(comp, 'galerie_z1', 'Galerie_jos'), 'Galerie')
    _cerc_fix(s, 0, 0, z1, '2 * galerie_raza', 2*Rg)
    _cerc_fix(s, 0, 0, z1, '2 * raza_camasa', 2*Rl)
    for x, y in _prezoane_xy(v):
        _cerc_fix(s, x, y, z1, '2 * bosaj_prezon', 2*v('bosaj_prezon'))
    sk = s.gata()
    prof = max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda q: q.areaProperties().area)
    _extrudare_spre(comp, prof, taie, 'galerie_z2 - galerie_z1', sus, corp).name = 'Galerie'
    # Canalele de transfer: din galerie până la marginea de sus a fiecărei ferestre, cu pereți paraleli
    zc = z2 - 0.1
    s = Schita(comp, _plan_z(comp, 'galerie_z2 - 1 mm', 'Canale_jos'), 'Canale_transfer')
    for nume, u_expr, w_expr, semn in TRANSFERURI:
        fi, c = semn*v(u_expr), v(w_expr)
        e, t = (math.cos(fi), math.sin(fi)), (-math.sin(fi), math.cos(fi))
        q = [s.sk.sketchPoints.add(s.p(r*e[0] + w*t[0], r*e[1] + w*t[1], zc))
             for r, w in ((Rl - 0.1, -c/2), (Rk, -c/2), (Rk, c/2), (Rl - 0.1, c/2))]
        for i in range(4):
            s.lin.addByTwoPoints(q[i], q[(i + 1) % 4])
        _fixeaza(q)
    sk = s.gata()
    _extrudare_spre(comp, _toate(sk), taie, 'z_transfer_sus - galerie_z2 + 1 mm', sus, corp).name = 'Canale_transfer'
    # Conducta de evacuare, deocamdată dreaptă prin corp (flanșa și supapa vin la pasul evacuării)
    zf, w = v('z_fereastra_jos'), v('latime_evacuare')
    s = Schita(comp, _plan_z(comp, 'z_fereastra_jos', 'Fereastra_jos'), 'Conducta_evacuare')
    q = [s.sk.sketchPoints.add(s.p(x, y, zf)) for x, y in ((Rl - 0.1, -w/2), (Rl + 0.9, -w/2), (Rl + 0.9, w/2), (Rl - 0.1, w/2))]
    for i in range(4):
        s.lin.addByTwoPoints(q[i], q[(i + 1) % 4])
    _fixeaza(q)
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'z_evacuare_sus - z_fereastra_jos', sus, corp).name = 'Conducta_evacuare'
    _cilindru_apa_evacuare(comp, v, corp)
    # Colectorul compresorului, turnat cu cilindrul: inel în plan vertical în spatele cilindrului, axa
    # compresorului orizontală la y = 0; ieșirea din punctul de jos intră drept în galerie, printre prezoane.
    # Se construiește ca piesă separată (nu atinge corpul decât prin gât), se golește, apoi se unește cu corpul.
    G_ = _geometrie_compresor(v)
    s, ax = G_['schita'](comp, 'Inel_colector')
    G_['cerc'](s, G_['Rsp'], 0, G_['ra'] + G_['tc'])
    colector = _rotire(comp.features, s.gata().profiles.item(0), ax, nou)
    s, ax = G_['schita'](comp, 'Disc_colector')
    G_['poligon'](s, [(0, G_['a_sp'] - G_['tc']), (G_['Rsp'], G_['a_sp'] - G_['tc']), (G_['Rsp'], G_['a_top']), (0, G_['a_top'])])
    _rotire(comp.features, s.gata().profiles.item(0), ax, uneste, colector)
    s, ax = G_['schita'](comp, 'Intrare_aer')
    G_['poligon'](s, [(G_['Ra'], G_['a_top'] - 0.05), (G_['Ra'] + 0.2, G_['a_top'] - 0.05), (G_['Ra'] + 0.2, G_['a_m'] + G_['Lm']),
                      (G_['Ra'], G_['a_m'] + G_['Lm'])])
    _rotire(comp.features, s.gata().profiles.item(0), ax, uneste, colector)
    pl = _plan_x_la(comp, G_['xv'], 'Iesire_colector')
    s = Schita(comp, pl, 'Gat_colector')
    _cerc_fix(s, G_['xv'], 0, zgm, 'D_admisie + 2 * carcasa_grosime', 2*(G_['ra'] + G_['tc']))
    _extrudare_spre(comp, s.gata().profiles.item(0), uneste, 'abs(compresor_x) - corp_raza + 2 mm', spre_x, colector).name = 'Gat_colector'
    # Golurile: roata cu jocul ei (decalat perpendicular pe contur) și ochiul, difuzorul, inelul
    s, ax = G_['schita'](comp, 'Gol_roata')
    G_['poligon'](s, G_['gol_roata'])
    _rotire(comp.features, s.gata().profiles.item(0), ax, taie, colector)
    s, ax = G_['schita'](comp, 'Difuzor')
    G_['poligon'](s, [(G_['r2'] + G_['j']/2, -G_['b2']/2), (G_['Rsp'], -G_['b2']/2), (G_['Rsp'], G_['b2']/2), (G_['r2'] + G_['j']/2, G_['b2']/2)])
    _rotire(comp.features, s.gata().profiles.item(0), ax, taie, colector)
    s, ax = G_['schita'](comp, 'Gol_inel')
    G_['cerc'](s, G_['Rsp'], 0, G_['ra'])
    _rotire(comp.features, s.gata().profiles.item(0), ax, taie, colector)
    unelte = adsk.core.ObjectCollection.create()
    unelte.add(colector)
    ci_ = comp.features.combineFeatures.createInput(corp, unelte)
    ci_.operation = uneste
    ci_.isKeepToolBodies = False
    comp.features.combineFeatures.add(ci_).name = 'Colector_turnat'
    # Canalul din inel în galerie, prin gât și peretele corpului
    s = Schita(comp, pl, 'Canal_galerie')
    _cerc_fix(s, G_['xv'], 0, zgm, 'D_admisie', 2*G_['ra'])
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'abs(compresor_x) - galerie_raza + 2 mm', spre_x, corp).name = 'Canal_galerie'
    return 'Pasul 12: 11_Cilindru_corp construit (Ø{:.0f}, galerie {:.0f}-{:.0f} mm, 5 canale de transfer, colectorul compresorului turnat în spate).'.format(
        2*Rc*10, z1*10, z2*10)


def _geometrie_compresor(v):
    """Compresorul în linie: axa orizontală (în lungul motocicletei) la y = 0, z = compresor_z.
    Coordonate de profil: r de la axă (în sus), a în lungul axei, pozitiv spre spate (x = compresor_x - a)."""
    g = dict(xv=v('compresor_x'), zc=v('compresor_z'), Rsp=v('spirala_R'), ra=v('D_admisie')/2, tc=v('carcasa_grosime'),
             j=v('joc_roata'), r2=v('roata_D2')/2, r1=v('roata_D1')/2, b2=v('roata_b2'), Lr=v('roata_L'),
             rax=v('arbore_comp_d')/2, Rm=v('motor_comp_D')/2, Lm=v('motor_comp_L'), Ra=v('admisie_comp_R'))
    g['a_sp'] = -(g['b2']/2 + 0.2)              # spatele roții, spre cilindru
    g['a_ind'] = g['a_sp'] + g['Lr']            # intrarea în roată, spre spate
    g['a_top'] = g['ra'] + g['tc']              # fața din spate a colectorului
    g['a_m'] = g['a_top'] + 0.5                 # motorul, la 5 mm în spatele ei
    at = g['b2']/2
    dr, da = g['r1'] - g['r2'], g['a_ind'] - at
    ln = math.hypot(dr, da)
    nr, na = da/ln, -dr/ln                      # normala spre exterior a liniei paletelor
    j = g['j']
    s_a, s_b = j*(1 - nr)/dr, (dr + j*(1 - nr))/dr
    g['gol_roata'] = [(0, g['a_sp'] - j), (g['r2'] + j, g['a_sp'] - j), (g['r2'] + j, at + j*na + s_a*da),
                      (g['r1'] + j, at + j*na + s_b*da), (g['r1'] + j, g['a_top'] + 0.1), (0, g['a_top'] + 0.1)]
    g['roata'] = [(0, g['a_sp']), (g['r2'], g['a_sp']), (g['r2'], at), (g['r1'], g['a_ind']), (g['rax'], g['a_ind']),
                  (g['rax'], g['a_m']), (0, g['a_m'])]

    def schita(comp, nume):
        s = Schita(comp, comp.xZConstructionPlane, nume)
        ax = s.lin.addByTwoPoints(s.p(g['xv'] - (g['a_sp'] - 1), 0, g['zc']), s.p(g['xv'] - (g['a_m'] + g['Lm'] + 1), 0, g['zc']))
        ax.isConstruction = True
        _fixeaza([ax.startSketchPoint, ax.endSketchPoint])
        return s, ax

    def poligon(s, pts):
        q = [s.sk.sketchPoints.add(s.p(g['xv'] - a, 0, g['zc'] + r)) for r, a in pts]
        for i in range(len(q)):
            s.lin.addByTwoPoints(q[i], q[(i + 1) % len(q)])
        _fixeaza(q)

    def cerc(s, r, a, raza):
        c = s.sk.sketchCurves.sketchCircles.addByCenterRadius(s.p(g['xv'] - a, 0, g['zc'] + r), raza)
        c.centerSketchPoint.isFixed = True
        s.dim.addDiameterDimension(c, s.p(g['xv'] - a + raza, 0, g['zc'] + r + raza)).parameter.value = 2*raza

    g.update(schita=schita, poligon=poligon, cerc=cerc)
    return g


def pas13_compresor(design):
    comp = componenta_noua(design, '90_Compresor')
    if comp is None:
        return 'Pasul 13: 90_Compresor există deja, l-am lăsat neatins.'
    v = valoare(design)
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    G_ = _geometrie_compresor(v)
    # Roata (anvelopa paletelor, cu arborele până la motor) și motorul, în urma ei, în curentul de aer
    s, ax = G_['schita'](comp, 'Roata')
    G_['poligon'](s, G_['roata'])
    roata = _rotire(f, s.gata().profiles.item(0), ax, nou)
    roata.name = 'Roata_compresor'
    marcheaza(roata, 'roata_compresor')
    s, ax = G_['schita'](comp, 'Motor')
    G_['poligon'](s, [(0, G_['a_m']), (G_['Rm'], G_['a_m']), (G_['Rm'], G_['a_m'] + G_['Lm']), (0, G_['a_m'] + G_['Lm'])])
    motor = _rotire(f, s.gata().profiles.item(0), ax, nou)
    motor.name = 'Motor_compresor'
    marcheaza(motor, 'motor_compresor')
    return 'Pasul 13: 90_Compresor construit (roata Ø{:.1f} mm și motorul Ø{:.0f} x {:.0f} mm, pe axa orizontală la z = {:.1f} mm).'.format(
        2*G_['r2']*10, 2*G_['Rm']*10, G_['Lm']*10, G_['zc']*10)


# --- Capacul din dreapta, prinderile pe cadru, scutul (pasul 14) ---
def _urechi_carter(comp, v, corp):
    """Urechile de prindere pe corpul rotund al carterului, în față și în spate, deasupra băilor; gaura M10 în lungul lui Y.
    Se fac pe carterul întreg, înainte de împărțire: fiecare semicarter primește jumătatea lui."""
    ux, uz, a = v('ureche_carter_x'), v('ureche_carter_z'), v('prindere_gaura')/2 + v('prindere_perete')
    x0 = v('gat_latime')/2 - 0.5
    s = Schita(comp, comp.xZConstructionPlane, 'Urechi_prindere')
    for sx in (1, -1):
        _dreptunghi_fix(s, [(sx*x0, 0, uz - a), (sx*(ux + a), 0, uz - a), (sx*(ux + a), 0, uz + a), (sx*x0, 0, uz + a)])
    _extrudare(comp, _toate(s.gata()), adsk.fusion.FeatureOperations.JoinFeatureOperation, 'ureche_carter_y', corp).name = 'Urechi_prindere'
    s = Schita(comp, comp.xZConstructionPlane, 'Gauri_prindere')
    for sx in (1, -1):
        _cerc_fix(s, sx*ux, 0, uz, 'prindere_gaura', v('prindere_gaura'))
    _extrudare(comp, _toate(s.gata()), adsk.fusion.FeatureOperations.CutFeatureOperation, 'ureche_carter_y + 1 mm', corp).name = 'Gauri_prindere'


def _inel_capac(comp, v, corp):
    """Inelul pe care se strânge capacul din dreapta: închide camera rotorului peste vârful aripioarelor
    și ocolește corpul cilindrului cu joc_corp_cil."""
    yc, v0 = v('y_carter'), corp.volume
    s = Schita(comp, _plan_y(comp, 'y_carter', 'Inel_capac'), 'Inel_capac')
    _cerc_fix(s, 0, -yc, 0, '2 * capac_raza_ext', 2*v('capac_raza_ext'))
    _cerc_fix(s, 0, -yc, 0, '2 * raza_cavitate', 2*v('raza_cavitate'))
    _extrudare_spre(comp, _profil_inel(s.gata(), 2*v('capac_raza_ext'), 2*v('raza_cavitate')),
                    adsk.fusion.FeatureOperations.JoinFeatureOperation, 'inel_capac', (0, 1, 0), corp).name = 'Inel_capac'
    _ocoleste_cilindrul(comp, v, corp, 'Inel_ocolire_cilindru')
    return corp.volume - v0


def _ocoleste_cilindrul(comp, v, corp, nume):
    zb = v('baza_cilindru')
    s = Schita(comp, _plan_baza(comp), nume)
    _cerc_fix(s, 0, 0, zb, '2 * (corp_raza + joc_corp_cil)', 2*(v('corp_raza') + v('joc_corp_cil')))
    _extrudare_spre(comp, s.gata().profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
                    'capac_raza_ext', (0, 1), corp).name = nume


def _urechi_stator(v):
    """Centrele găurilor din urechile statorului (x, z), ca în pasul 10."""
    r = v('stator_raza_int') - v('ureche_lungime')/2
    return [(r*math.cos(a), r*math.sin(a)) for a in (math.pi/2, math.pi/2 + 2*math.pi/3, math.pi/2 + 4*math.pi/3)]


Y_URECHI_STATOR = 'y_carter + joc_con + disc_rotor + joc_capete + capete_bobine + pachet_lungime'


def pas14_capac(design):
    """Capacul din dreapta: tambur turnat peste rotor, statorul prins pe el, camera de apă a modulului de putere."""
    comp = componenta_noua(design, '52_Capac_dreapta')
    if comp is None:
        return 'Pasul 14: 52_Capac_dreapta există deja, l-am lăsat neatins.'
    v = valoare(design)
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    spre_ext, spre_int = (0, -1, 0), (0, 1, 0)
    yc, yi, ye = v('y_carter'), v('y_capac_int'), v('y_capac_ext')
    # Tamburul, plin până la fața exterioară, golit până la cea interioară; ocolește corpul cilindrului
    pl = _plan_y(comp, 'y_carter', 'Fata_carterului')
    s = Schita(comp, pl, 'Tambur')
    _cerc_fix(s, 0, -yc, 0, '2 * capac_raza_ext', 2*v('capac_raza_ext'))
    corp = _extrudare_spre(comp, s.gata().profiles.item(0), nou, 'y_capac_ext - y_carter', spre_ext).bodies.item(0)
    corp.name = 'Capac_dreapta'
    marcheaza(corp, 'capac')
    s = Schita(comp, pl, 'Camera_rotorului')
    _cerc_fix(s, 0, -yc, 0, '2 * capac_raza_int', 2*v('capac_raza_int'))
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'y_capac_int - y_carter', spre_ext, corp).name = 'Camera_rotorului'
    _ocoleste_cilindrul(comp, v, corp, 'Ocolire_cilindru')
    # Bosajele statorului, până la fața urechilor; M5 în bucșe filetate, cât bosajul
    pl = _plan_y(comp, 'y_capac_int', 'Fata_interioara')
    for nume, d_expr, op in (('Bosaje_stator', 'bosaj_stator', uneste), ('Filete_stator', '4.2 mm', taie)):
        s = Schita(comp, pl, nume)
        for x, z in _urechi_stator(v):
            _cerc_fix(s, x, -yi, z, d_expr, v('bosaj_stator') if op == uneste else 0.42)
        _extrudare_spre(comp, _toate(s.gata()), op, 'y_capac_int - (' + Y_URECHI_STATOR + ')', spre_int, corp).name = nume
    # Camera de apă în peretele exterior, sub modul; talpa modulului; racordurile (intrarea în spate)
    ya = yi + v('piele_capac_int')
    ax_, az_ = v('apa_capac_x')/2, v('apa_capac_z')/2
    s = Schita(comp, _plan_y(comp, 'y_capac_int + piele_capac_int', 'Camera_apa'), 'Camera_apa')
    _dreptunghi_fix(s, [(-ax_, -ya, -az_), (ax_, -ya, -az_), (ax_, -ya, az_), (-ax_, -ya, az_)])
    _extrudare_spre(comp, s.gata().profiles.item(0), taie, 'apa_capac_y', spre_ext, corp).name = 'Camera_apa'
    pl = _plan_y(comp, 'y_capac_ext', 'Fata_exterioara')
    mx, mz = v('modul_x')/2, v('modul_z')/2
    s = Schita(comp, pl, 'Talpa_modul')
    _dreptunghi_fix(s, [(-mx, -ye, -mz), (mx, -ye, -mz), (mx, -ye, mz), (-mx, -ye, mz)])
    _extrudare_spre(comp, s.gata().profiles.item(0), uneste, '1 mm', spre_ext, corp).name = 'Talpa_modul'
    xr = ax_ - 0.8
    s = Schita(comp, pl, 'Bosaje_racorduri')
    for sx in (1, -1):
        _cerc_fix(s, sx*xr, -ye, 0, 'racord_apa_D + 8 mm', v('racord_apa_D') + 0.8)
    _extrudare_spre(comp, _toate(s.gata()), uneste, '12 mm', spre_ext, corp).name = 'Bosaje_racorduri'
    s = Schita(comp, _plan_y(comp, 'y_capac_ext + 12 mm', 'Racorduri'), 'Racorduri')
    for sx in (1, -1):
        _cerc_fix(s, sx*xr, -(ye + 1.2), 0, 'racord_apa_D', v('racord_apa_D'))
    _extrudare_spre(comp, _toate(s.gata()), taie, '12 mm + 4 mm + 1 mm', spre_int, corp).name = 'Racorduri'
    return 'Pasul 14: 52_Capac_dreapta construit (tambur R{:.1f}, fața la {:.1f} mm, statorul pe 3 bosaje, camera de apă {:.0f} x {:.0f} mm).'.format(
        v('capac_raza_ext')*10, ye*10, 2*ax_*10, 2*az_*10)


def _z_scut(v):
    return -max(v('capac_raza_ext'), v('baie_jos') + v('nervura_inaltime')) - v('scut_joc')


def pas14b_scut(design):
    """Scutul de sub motor (tablă de aluminiu): garda la sol o dă el, nu băile sau capacul."""
    comp = componenta_noua(design, '55_Scut')
    if comp is None:
        return 'Pasul 14b: 55_Scut există deja, l-am lăsat neatins.'
    v = valoare(design)
    zt, ts, X = _z_scut(v), v('scut_grosime'), v('baie_x') + 0.5
    s = Schita(comp, comp.xZConstructionPlane, 'Scut')
    _dreptunghi_fix(s, [(-X, 0, zt - ts), (X, 0, zt - ts), (X, 0, zt), (-X, 0, zt)])
    corp = _extrudare(comp, s.gata().profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                      'y_capac_ext + 5 mm').bodies.item(0)
    corp.name = 'Scut'
    marcheaza(corp, 'scut')
    return 'Pasul 14b: 55_Scut construit (fața de sus la {:.1f} mm sub axă, {:.0f} mm grosime).'.format(-zt*10, ts*10)


def verifica_pas14(design):
    teste, t = _t()
    v = valoare(design)
    mm_ = adsk.core.Application.get().measureManager
    cap = gaseste(design, 'capac')
    if cap is None or ocurenta(design, '52_Capac_dreapta') is None or ocurenta(design, '55_Scut') is None:
        t(False, 'C14', '52_Capac_dreapta sau 55_Scut lipsește')
        return teste
    C_ = _corpuri(design, [('52_Capac_dreapta', 'capac')])[0]
    def dist(a, lista):                      # nan dacă Fusion nu poate măsura o pereche: verificarea pică vizibil
        r_ = [mm_.measureMinimumDistance(a, b) for b in lista]
        return min(x.value for x in r_) if all(r_) else float('nan')
    j_rot = dist(C_, _corpuri(design, [('61_Rotor', None)]))
    j_bob = dist(C_, _corpuri(design, [('60_Stator', 'bobina')]))
    j_cil = dist(C_, _corpuri(design, [('11_Cilindru_corp', 'corp_cilindru')]))
    plane, cil = _fete(cap)
    pe_y = lambda r_: [o for r, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(r - r_) < TOL]
    ys = [o.y for n, o in plane if abs(abs(n.y) - 1) < 1e-9]
    are = lambda lista, val: any(abs(x - val) < TOL for x in lista)
    fil = pe_y(0.21)
    fil_ok = all(any(abs(o.x - x) < TOL and abs(o.z - z) < TOL for o in fil) for x, z in _urechi_stator(v))
    ya = v('y_capac_int') + v('piele_capac_int')
    xr = v('apa_capac_x')/2 - 0.8
    rac = [o for o in pe_y(v('racord_apa_D')/2) if abs(abs(o.x) - xr) < TOL and abs(o.z) < TOL]
    t(abs(j_rot - v('joc_rotor_capac')) < 1e-4 and j_bob >= v('joc_bobine_capac') - 1e-4 and are(ys, -_y_urechi(v))
      and abs(j_cil - v('joc_corp_cil')) < 1e-4 and fil_ok and are(ys, -ya) and are(ys, -(ya + v('apa_capac_y')))
      and len({round(o.x, 3) for o in rac}) == 2, 'C14a',
      'Capacul din dreapta: {:.1f} mm până la rotor, {:.1f} mm până la bobine, statorul stă pe 3 bosaje cu M5 ({:.1f} mm filet); '
      'ocolește corpul cilindrului la {:.1f} mm; camera de apă {:.0f} x {:.0f} x {:.0f} mm cu 2 racorduri Ø{:.0f}'.format(
          j_rot*10, j_bob*10, (v('y_capac_int') - _y_urechi(v))*10, j_cil*10,
          v('apa_capac_x')*10, v('apa_capac_z')*10, v('apa_capac_y')*10, v('racord_apa_D')*10))
    # Inelul semicarterului drept și urechile de prindere
    ux, uz, rg = v('ureche_carter_x'), v('ureche_carter_z'), v('prindere_gaura')/2
    ok_u, ok_i = 0, False
    for nume_c, rol in (('50_Carter_stanga', 'carter'), ('51_Carter_dreapta', 'carter')):
        rol_ = lambda c: c.attributes.itemByName(GRUP, 'rol').value if c.attributes.itemByName(GRUP, 'rol') else ''
        cc = [b for b in ocurenta(design, nume_c).component.bRepBodies if rol_(b) == rol][0]
        pc, cc_ = _fete(cc)
        gauri = [o for r, a, o in cc_ if abs(abs(a.y) - 1) < 1e-9 and abs(r - rg) < TOL and abs(abs(o.x) - ux) < TOL and abs(o.z - uz) < TOL]
        if len({round(o.x, 3) for o in gauri}) == 2:
            ok_u += 1
        if nume_c == '51_Carter_dreapta':
            ok_i = (any(abs(r - v('capac_raza_ext')) < TOL and abs(abs(a.y) - 1) < 1e-9 for r, a, o in cc_)
                    and any(abs(abs(n.y) - 1) < 1e-9 and abs(o.y + v('y_carter') - v('inel_capac')) < TOL for n, o in pc))
    zj = uz - rg - v('prindere_perete')
    ch = gaseste(design, 'chiulasa')
    _, c_ch = _fete(ch)
    zt_ch = v('raza_manivela') + v('biela_L') + v('inaltime_compresie') + v('deck_peste_coroana') + v('grosime_chiulasa')
    u_ch = any(abs(abs(a.y) - 1) < 1e-9 and abs(r - rg) < TOL and abs(o.x - v('ureche_chiulasa_x')) < TOL
               and abs(o.z - zt_ch - v('ureche_chiulasa_z')) < TOL for r, a, o in c_ch)
    t(ok_u == 2 and ok_i and u_ch and zj >= v('perete_minim'), 'C14b',
      'Prinderile: urechi M10 față-spate pe ambele semicartere (±{:.0f} mm, z = {:.0f} mm, {:.1f} mm deasupra băilor), urechea chiulasei '
      'pentru tijă; inelul capacului pe semicarterul drept (R{:.1f}, {:.0f} mm)'.format(
          ux*10, uz*10, zj*10, v('capac_raza_ext')*10, v('inel_capac')*10))
    # Scutul și interferențele ansamblului
    S_ = _corpuri(design, [('55_Scut', None)])[0]
    j_s = dist(S_, _corpuri(design, CARTER + [('52_Capac_dreapta', None)]))
    col = adsk.core.ObjectCollection.create()
    for nume in ('10_Cilindru', '11_Cilindru_corp', '15_Chiulasa', '50_Carter_stanga', '51_Carter_dreapta', '52_Capac_dreapta',
                 '55_Scut', '56_Pompa_ulei', '60_Stator', '61_Rotor', '90_Compresor'):
        col.add(ocurenta(design, nume))
    ii = design.createInterferenceInput(col)
    ii.areCoincidentFacesIncluded = False
    inter = design.analyzeInterference(ii)
    n_int = inter.count if inter else 0
    perechi = ['{}/{}'.format(inter.item(i).entityOne.name, inter.item(i).entityTwo.name) for i in range(n_int)]
    t(abs(j_s - v('scut_joc')) < 1e-4 and n_int == 0, 'C14c',
      'Scutul la {:.1f} mm sub cel mai de jos punct (nervura sorbului), fața lui la {:.1f} mm sub axă; interferențe carter, capac, '
      'stator, rotor, cilindru, chiulasă, compresor, pompa de ulei, scut: {}{}'.format(j_s*10, -_z_scut(v)*10, n_int,
                                                                        ' (' + ', '.join(perechi) + ')' if perechi else ''))
    return teste


def _y_urechi(v):
    return (v('y_carter') + v('joc_con') + v('disc_rotor') + v('joc_capete') + v('capete_bobine') + v('pachet_lungime'))


def _plan_normal(comp, fi, r, nume):
    """Plan vertical perpendicular pe direcția radială de la unghiul fi, la distanța r de axa cilindrului."""
    e = (math.cos(fi), math.sin(fi))
    baza = None
    for a in (fi, -fi, math.pi - fi, fi - math.pi):
        pi = comp.constructionPlanes.createInput()
        pi.setByAngle(comp.zConstructionAxis, adsk.core.ValueInput.createByReal(a), comp.yZConstructionPlane)
        pl = comp.constructionPlanes.add(pi)
        n = pl.geometry.normal
        if abs(abs(n.x*e[0] + n.y*e[1]) - 1) < 1e-6:
            baza = pl
            break
        pl.deleteMe()
    if baza is None:
        raise RuntimeError('Nu pot pune planul {}'.format(nume))
    for d in (r, -r):
        pi = comp.constructionPlanes.createInput()
        pi.setByOffset(baza, adsk.core.ValueInput.createByReal(d))
        pl = comp.constructionPlanes.add(pi)
        o = pl.geometry.origin
        if abs(o.x*e[0] + o.y*e[1] - r) < 1e-6:
            pl.name = nume
            return pl
        pl.deleteMe()
    raise RuntimeError('Nu pot pune planul {} la r = {:.2f}'.format(nume, r))


def _nervura_sorb(comp, v, corp):
    """Nervura de sub fundul semicarterului drept, cu galeria de aspirație de la sorbul din mijlocul tubului în U
    până la plăcuța pompei de ulei, în fața băii din față. Întoarce volumul adăugat (doar pe dreapta)."""
    v0 = corp.volume
    bj, X, cj = v('baie_jos'), v('baie_x'), v('tesire_jos')
    hn, wn, ys, dg = v('nervura_inaltime'), v('nervura_latime'), v('y_sorb'), v('galerie_sorb')
    xf, xp, zb, zg = X - cj, X + 0.5, -bj - hn, -bj - dg/2
    yp = ys + wn/2
    s = Schita(comp, _plan_y_la(comp, yp, 'Nervura_sorb'), 'Nervura_sorb')
    _dreptunghi_fix(s, [(-0.5, yp, -bj + 0.1), (xf, yp, -bj + 0.1), (X - 0.1, yp, -bj + cj), (xp, yp, -bj + cj),
                        (xp, yp, zb), (-0.5, yp, zb)])
    _extrudare_spre(comp, s.gata().profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation,
                    'nervura_latime', (0, -1, 0), corp).name = 'Nervura_sorb'
    s = Schita(comp, _plan_x_la(comp, xp, 'Placuta_pompa_ulei'), 'Galerie_sorb')
    _cerc_fix(s, xp, ys, zg, 'galerie_sorb', dg)
    _extrudare_spre(comp, s.gata().profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
                    'baie_x + 5 mm + galerie_sorb / 2', (-1, 0), corp).name = 'Galerie_sorb'
    s = Schita(comp, _plan_z(comp, '-(baie_jos + galerie_sorb / 2)', 'Sorb'), 'Sorb')
    _cerc_fix(s, 0, ys, zg, 'galerie_sorb', dg)
    _extrudare_spre(comp, s.gata().profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
                    'galerie_sorb / 2 + grosime_carter + 0.5 mm', (0, 1), corp).name = 'Sorb'
    return corp.volume - v0


def pas14c_pompa_ulei(design):
    """Pompa electrică de ulei (gerotor, anvelopă) pe plăcuța din fața băii din față, cu răcitorul ulei-apă deasupra."""
    comp = componenta_noua(design, '56_Pompa_ulei')
    if comp is None:
        return 'Pasul 14c: 56_Pompa_ulei există deja, l-am lăsat neatins.'
    v = valoare(design)
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    R, H, ys = v('pompa_ulei_D')/2, v('pompa_ulei_H'), v('y_sorb')
    xc, z0 = v('baie_x') + 0.5 + R, -v('baie_jos') - 0.75
    s = Schita(comp, _plan_z(comp, '-(baie_jos + 7.5 mm)', 'Baza_pompei'), 'Pompa_ulei')
    _cerc_fix(s, xc, ys, z0, 'pompa_ulei_D', 2*R)
    p = _extrudare_spre(comp, s.gata().profiles.item(0), nou, 'pompa_ulei_H', (0, 1)).bodies.item(0)
    p.name = 'Pompa_ulei'
    marcheaza(p, 'pompa_ulei')
    rx, ry = v('racitor_x')/2, v('racitor_y')/2
    s = Schita(comp, _plan_z(comp, '-(baie_jos + 7.5 mm) + pompa_ulei_H', 'Baza_racitorului'), 'Racitor_ulei')
    _dreptunghi_fix(s, [(xc - rx, ys - ry, z0 + H), (xc + rx, ys - ry, z0 + H), (xc + rx, ys + ry, z0 + H), (xc - rx, ys + ry, z0 + H)])
    r = _extrudare_spre(comp, s.gata().profiles.item(0), nou, 'racitor_z', (0, 1)).bodies.item(0)
    r.name = 'Racitor_ulei'
    marcheaza(r, 'racitor_ulei')
    return 'Pasul 14c: 56_Pompa_ulei construită (pompa Ø{:.0f} x {:.0f} mm și răcitorul ulei-apă, în fața băii din față).'.format(2*R*10, H*10)


def verifica_ulei(design):
    teste, t = _t()
    v = valoare(design)
    occ = ocurenta(design, '51_Carter_dreapta')
    if occ is None or gaseste(design, 'pompa_ulei') is None or gaseste(design, 'racitor_ulei') is None:
        t(False, 'C14d', '51_Carter_dreapta sau 56_Pompa_ulei lipsește')
        return teste
    rol_ = lambda c: c.attributes.itemByName(GRUP, 'rol').value if c.attributes.itemByName(GRUP, 'rol') else ''
    cd = [b for b in occ.component.bRepBodies if rol_(b) == 'carter'][0]
    plane, cil = _fete(cd)
    ys, rg = v('y_sorb'), v('galerie_sorb')/2
    zg = -v('baie_jos') - rg
    gal = any(abs(abs(a.x) - 1) < 1e-9 and abs(r - rg) < TOL and abs(o.y - ys) < TOL and abs(o.z - zg) < TOL for r, a, o in cil)
    sorb = any(abs(abs(a.z) - 1) < 1e-9 and abs(r - rg) < TOL and abs(o.x) < TOL and abs(o.y - ys) < TOL for r, a, o in cil)
    placuta = any(abs(abs(n.x) - 1) < 1e-9 and abs(o.x - v('baie_x') - 0.5) < TOL for n, o in plane)
    zs = [o.z for n, o in plane if abs(abs(n.z) - 1) < 1e-9]
    nerv = any(abs(z + v('baie_jos') + v('nervura_inaltime')) < TOL for z in zs)
    t(gal and sorb and placuta and nerv, 'C14d',
      'Ungerea: sorbul la mijlocul tubului în U (x = 0), galeria Ø{:.0f} prin nervura de {:.0f} x {:.0f} mm de sub semicarterul drept, '
      'până la plăcuța pompei de la x = {:.0f} mm; pompa Ø{:.0f} x {:.0f} și răcitorul ulei-apă deasupra ei, în fața băii'
      .format(2*rg*10, v('nervura_latime')*10, v('nervura_inaltime')*10, (v('baie_x') + 0.5)*10,
              v('pompa_ulei_D')*10, v('pompa_ulei_H')*10))
    return teste


# --- Pasul 15: toba de rezonanță (MR-011) -------------------------------------------------
# Traseul ales: pe dreapta (-Y), în față și în jos, apoi pe lateral, în sus spre spate. Lungimile și diametrele vin
# din parametri (Jennings, s02); aici sunt doar direcțiile tronsoanelor. Lungimile scrise sunt în cm.
TRASEU_TOBA = [('colector', (1, 0, 0), 4.0),             # drept prin flanșă
               ('colector', (0.9, -0.2, -0.4), 7.0),
               ('colector', (0.15, -0.85, -0.5), None),   # restul colectorului: iese spre dreapta în fața capacului
               ('difuzor', (-0.85, -0.28, 0.40), None),   # trece pe lângă capac cu toba_joc
               ('burta', (-0.9, 0.0, 0.43), None),
               ('con_invers', (-0.88, 0.15, 0.46), None),
               ('iesire', (-0.9, 0.2, 0.40), None)]


def _traseu_toba(v):
    """Tronsoanele tobei: (nume, punctul de început, punctul de sfârșit, (raza la început, raza la sfârșit)), în cm."""
    g = _geometrie_evacuare(v)
    lung = {'difuzor': v('toba_L2'), 'burta': v('toba_L3'), 'con_invers': v('toba_L4'), 'iesire': v('toba_L5')}
    r1, r2, r3 = v('toba_D1')/2, v('toba_D2')/2, v('toba_D3')/2
    raze = {'colector': (r1, r1), 'difuzor': (r1, r2), 'burta': (r2, r2), 'con_invers': (r2, r3), 'iesire': (r3, r3)}
    p = (v('corp_raza') + v('flansa_grosime'), 0.0, g['zem'])
    seg, colector = [], 0.0
    for nume, d, L in TRASEU_TOBA:
        n = math.sqrt(sum(c*c for c in d))
        d = tuple(c/n for c in d)
        if nume == 'colector':
            L = L if L is not None else v('toba_L1e') - colector
            colector += L
        else:
            L = lung[nume]
        q = tuple(p[i] + L*d[i] for i in range(3))
        seg.append((nume, p, q, raze[nume]))
        p = q
    return seg


def pas15_toba(design):
    """Toba: tronsoane drepte (conuri și cilindri) cu bile la îmbinări, golită la grosimea tablei; flanșa pe cele două
    prezoane ale cilindrului; bosajul sondei lambda pe colector; catalizatorul rezervat în burtă."""
    comp = componenta_noua(design, '80_Toba')
    if comp is None:
        return 'Pasul 15: 80_Toba există deja, am lăsat-o neatinsă.'
    v = valoare(design)
    f = comp.features
    nou = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    uneste = adsk.fusion.FeatureOperations.JoinFeatureOperation
    taie = adsk.fusion.FeatureOperations.CutFeatureOperation
    seg = _traseu_toba(v)
    s = Schita(comp, comp.xYConstructionPlane, 'Traseu_toba')
    linii = [s.lin.addByTwoPoints(s.p(*a), s.p(*b)) for _, a, b, _ in seg]
    for ln in linii:
        ln.isConstruction = True
    s.gata()

    def plan(linie, t, nume):
        pi = comp.constructionPlanes.createInput()
        pi.setByDistanceOnPath(linie, adsk.core.ValueInput.createByReal(t))
        pl = comp.constructionPlanes.add(pi)
        pl.name = nume
        return pl

    def cerc(pl, centru, r, nume):
        sk = Schita(comp, pl, nume)
        sk.sk.sketchCurves.sketchCircles.addByCenterRadius(sk.p(*centru), r)
        return sk.gata().profiles.item(0)

    corpuri, planuri = [], []
    for i, ((nume, a, b, (ra, rb)), ln) in enumerate(zip(seg, linii)):
        pa, pb = plan(ln, 0.0, 'Toba_{}_inceput'.format(i)), plan(ln, 1.0, 'Toba_{}_sfarsit'.format(i))
        planuri.append((pa, pb))
        li = f.loftFeatures.createInput(nou)
        li.loftSections.add(cerc(pa, a, ra, 'Toba_{}_{}_a'.format(i, nume)))
        li.loftSections.add(cerc(pb, b, rb, 'Toba_{}_{}_b'.format(i, nume)))
        li.isSolid = True
        corpuri.append(f.loftFeatures.add(li).bodies.item(0))
        if i < len(seg) - 1:                     # bila de la îmbinare: semidisc rotit în jurul diametrului
            sk = Schita(comp, pb, 'Toba_{}_bila'.format(i))
            c = sk.p(*b)
            sk.sk.sketchCurves.sketchCircles.addByCenterRadius(c, rb)
            ax = sk.lin.addByTwoPoints(adsk.core.Point3D.create(c.x - rb, c.y, 0), adsk.core.Point3D.create(c.x + rb, c.y, 0))
            corpuri.append(_rotire(f, sk.gata().profiles.item(0), ax, nou))
    unelte = adsk.core.ObjectCollection.create()
    for b_ in corpuri[1:]:
        unelte.add(b_)
    ci = f.combineFeatures.createInput(corpuri[0], unelte)
    ci.operation = uneste
    corp = f.combineFeatures.add(ci).bodies.item(0)
    corp.name = 'Toba'
    marcheaza(corp, 'toba')
    # Golirea la grosimea tablei, cu capetele deschise
    capete = adsk.core.ObjectCollection.create()
    for pt in (seg[0][1], seg[-1][2]):
        for fa in corp.faces:
            c = fa.centroid
            if (fa.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType
                    and (c.x - pt[0])**2 + (c.y - pt[1])**2 + (c.z - pt[2])**2 < 1e-4):
                capete.add(fa)
                break
    si = f.shellFeatures.createInput(capete, False)
    si.insideThickness = adsk.core.ValueInput.createByString('toba_tabla')
    f.shellFeatures.add(si)
    # Bosajul sondei lambda, la mijlocul ultimului tronson de colector, spre exterior (dreapta-sus)
    nume, a, b, (ra, _) = seg[2]
    d = [b[i] - a[i] for i in range(3)]
    nd = math.sqrt(sum(x*x for x in d))
    d = [x/nd for x in d]
    sus = (0.0, -1.0, 0.5)
    pr = sum(sus[i]*d[i] for i in range(3))
    n = [sus[i] - pr*d[i] for i in range(3)]
    nn = math.sqrt(sum(x*x for x in n))
    n = [x/nn for x in n]
    c = [(a[i] + b[i])/2 for i in range(3)]
    t_, H = v('toba_tabla'), v('lambda_bosaj_H')
    sl = Schita(comp, comp.xYConstructionPlane, 'Axa_lambda')
    la = sl.lin.addByTwoPoints(sl.p(*c), sl.p(*[c[i] + n[i]*(ra + H) for i in range(3)]))
    la.isConstruction = True
    sl.gata()
    pl = plan(la, (ra - t_)/(ra + H), 'Plan_lambda')
    c0 = [c[i] + n[i]*(ra - t_) for i in range(3)]
    _extrudare_spre(comp, cerc(pl, c0, v('lambda_bosaj_D')/2, 'Bosaj_lambda'), uneste, 'lambda_bosaj_H + toba_tabla', tuple(n), corp)
    _extrudare_spre(comp, cerc(pl, c0, v('lambda_filet')/2, 'Gaura_lambda'), taie, 'lambda_bosaj_H + toba_tabla + 1 mm', tuple(n), corp)
    # Catalizatorul rezervat: cilindrul din burtă, la cat_joc de peretele interior (substratul DE CONFIRMAT)
    k = [i for i, x in enumerate(seg) if x[0] == 'burta'][0]
    rc = v('toba_D2')/2 - t_ - v('cat_joc')
    li = f.loftFeatures.createInput(nou)
    li.loftSections.add(cerc(planuri[k][0], seg[k][1], rc, 'Catalizator_a'))
    li.loftSections.add(cerc(planuri[k][1], seg[k][2], rc, 'Catalizator_b'))
    li.isSolid = True
    cat = f.loftFeatures.add(li).bodies.item(0)
    cat.name = 'Catalizator_rezervat'
    marcheaza(cat, 'catalizator_rezervat')
    # Flanșa pe cele două prezoane ale cilindrului, cu găurile de trecere M8 (9 mm, ISO 273 seria medie) și țeava prin ea
    g = _geometrie_evacuare(v)
    xf = seg[0][1][0]
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(comp.yZConstructionPlane, adsk.core.ValueInput.createByReal(xf))
    pf = comp.constructionPlanes.add(pi)
    pf.name = 'Plan_flansa_toba'
    sf = Schita(comp, pf, 'Flansa_toba')
    C = sf.sk.sketchCurves.sketchCircles
    zy, Rb = g['y_prezon'], v('flansa_bosaj_R')
    C.addByCenterRadius(sf.p(xf, 0, g['zem']), g['Ro'])
    for y in (zy, -zy):
        C.addByCenterRadius(sf.p(xf, y, g['zem']), Rb)
    _dreptunghi_fix(sf, [(xf, -zy, g['zem'] - Rb), (xf, zy, g['zem'] - Rb), (xf, zy, g['zem'] + Rb), (xf, -zy, g['zem'] + Rb)])
    fl = _extrudare_spre(comp, _toate(sf.gata()), nou, 'toba_flansa_grosime', (1, 0, 0)).bodies.item(0)
    fl.name = 'Flansa_toba'
    marcheaza(fl, 'flansa_toba')
    sg = Schita(comp, pf, 'Gauri_flansa_toba')
    sg.sk.sketchCurves.sketchCircles.addByCenterRadius(sg.p(xf, 0, g['zem']), v('toba_D1')/2)
    for y in (zy, -zy):
        sg.sk.sketchCurves.sketchCircles.addByCenterRadius(sg.p(xf, y, g['zem']), 0.45)
    _extrudare_spre(comp, _toate(sg.gata()), taie, 'toba_flansa_grosime + 1 mm', (1, 0, 0), fl)
    return 'Pasul 15: 80_Toba construită (colector Ø{:.1f}, burta Ø{:.0f}, ieșire Ø{:.1f} mm; {:.0f} mm de la flanșă la capăt).'.format(
        v('toba_D1')*10, v('toba_D2')*10, v('toba_D3')*10, sum(math.dist(a, b) for _, a, b, _ in seg)*10)


def verifica_toba(design):
    teste, t = _t()
    v = valoare(design)
    occ, corp, fl, cat = ocurenta(design, '80_Toba'), gaseste(design, 'toba'), gaseste(design, 'flansa_toba'), gaseste(design, 'catalizator_rezervat')
    if occ is None or corp is None or fl is None or cat is None:
        t(False, 'C15a', '80_Toba lipsește sau e incompletă')
        return teste
    seg = _traseu_toba(v)
    L = v('toba_L_port') + sum(math.dist(a, b) for n, a, b, _ in seg if n in ('colector', 'difuzor', 'burta')) + v('toba_reflexie')*v('toba_L4')
    plin = sum(math.pi/3*math.dist(a, b)*(ra*ra + ra*rb + rb*rb) for _, a, b, (ra, rb) in seg)
    gol = corp.volume < 0.2*plin
    t(abs(L - v('toba_L0')) < 0.01 and gol, 'C15a',
      'Toba: lungimea acordată pe axa modelului {:.1f} mm = {:.1f} mm din s02; golită la {:.1f} mm ({:.0f} cm3 de tablă); masa {:.2f} kg'
      .format(L*10, v('toba_L0')*10, v('toba_tabla')*10, corp.volume, corp.physicalProperties.mass))
    mm_ = adsk.core.Application.get().measureManager
    T_ = corp.createForAssemblyContext(occ)
    dist = {}
    for nume in ('10_Cilindru', '15_Chiulasa', '50_Carter_stanga', '51_Carter_dreapta', '52_Capac_dreapta', '55_Scut',
                 '56_Pompa_ulei', '90_Compresor'):
        try:
            dist[nume] = min(mm_.measureMinimumDistance(T_, b).value for b in _corpuri(design, [(nume, None)]))
        except Exception:
            dist[nume] = float('nan')
    col = adsk.core.ObjectCollection.create()
    for nume in ('11_Cilindru_corp', '15_Chiulasa', '50_Carter_stanga', '51_Carter_dreapta', '52_Capac_dreapta', '55_Scut',
                 '56_Pompa_ulei', '90_Compresor', '80_Toba'):
        col.add(ocurenta(design, nume))
    ii = design.createInterferenceInput(col)
    ii.areCoincidentFacesIncluded = False
    inter = design.analyzeInterference(ii)
    n_int = inter.count if inter else 0
    perechi = ['{}/{}'.format(inter.item(i).entityOne.name, inter.item(i).entityTwo.name) for i in range(n_int)]
    mic = min(dist, key=lambda k: dist[k] if dist[k] == dist[k] else -1)
    t(all(d >= v('toba_joc') - TOL for d in dist.values()) and n_int == 0, 'C15b',
      'Toba pe dreapta: cel mai aproape de {} ({:.1f} mm >= {:.0f} mm); pompa de ulei {:.1f} mm, capacul {:.1f} mm, scutul {:.1f} mm, '
      'compresorul {:.1f} mm; interferențe: {}{}'.format(mic, dist[mic]*10, v('toba_joc')*10, dist['56_Pompa_ulei']*10,
                                                        dist['52_Capac_dreapta']*10, dist['55_Scut']*10, dist['90_Compresor']*10,
                                                        n_int, ' (' + ', '.join(perechi) + ')' if perechi else ''))
    j_c = mm_.measureMinimumDistance(cat.createForAssemblyContext(occ), T_).value
    _, cil = _fete(corp)
    gaura = any(abs(r - v('lambda_filet')/2) < TOL for r, a, o in cil)
    t(0.9*v('cat_joc') <= j_c <= 1.05*v('cat_joc') + TOL and gaura, 'C15c',
      'Catalizatorul rezervat în burtă: Ø{:.0f} x {:.0f} mm, {:.1f} mm de perete (substratul DE CONFIRMAT); sonda lambda: gaură Ø{:.0f} pe colector'
      .format((v('toba_D2') - 2*v('toba_tabla') - 2*v('cat_joc'))*10, v('toba_L3')*10, j_c*10, v('lambda_filet')*10))
    return teste


def verifica_pas12(design):
    teste, t = _t()
    v = valoare(design)
    if ocurenta(design, '11_Cilindru_corp') is None or ocurenta(design, '90_Compresor') is None:
        t(False, 'C12', '11_Cilindru_corp sau 90_Compresor lipsește')
        return teste
    corp = gaseste(design, 'corp_cilindru')
    plane, cil = _fete(corp)
    are = lambda lista, val: any(abs(x - val) < TOL for x in lista)
    zs = [o.z for n, o in plane if abs(abs(n.z) - 1) < 1e-9]
    pe_z = lambda r_: [(r, o) for r, a, o in cil if abs(abs(a.z) - 1) < 1e-9 and abs(r - r_) < TOL]
    pe_ax = lambda r_: [o for r, o in pe_z(r_) if abs(o.x) < TOL and abs(o.y) < TOL]
    prez = [o for r, o in pe_z(v('prezon_trecere')/2) if abs(math.hypot(o.x, o.y) - v('prezon_raza')) < TOL]
    bos = [o for r, o in pe_z(v('bosaj_prezon')) if abs(math.hypot(o.x, o.y) - v('prezon_raza')) < TOL]
    ys0 = [o.y for n, o in plane if abs(abs(n.y) - 1) < 1e-9]
    z_deg = v('raza_rotor') + v('grosime_pahar') + v('joc_con')
    t(pe_ax(v('corp_raza')) and pe_ax(v('raza_camasa')) and are(zs, v('baza_cilindru')) and are(zs, v('z_punte'))
      and len({(round(o.x, 3), round(o.y, 3)) for o in prez}) == 4 and are(ys0, v('y_carter')) and are(ys0, -v('y_carter'))
      and are(zs, z_deg), 'C12a',
      'Corpul cilindrului: Ø{:.0f} de la baza ({:.0f} mm) la punte ({:.2f} mm), cămașa Ø{:.0f} presată, 4 prezoane M8 până la chiulasă; '
      'laturile plane la fața carterului (±{:.2f}) până la {:.1f} mm, deasupra rotorului'
      .format(2*v('corp_raza')*10, v('baza_cilindru')*10, v('z_punte')*10, 2*v('raza_camasa')*10, v('y_carter')*10, z_deg*10))
    t(pe_ax(v('galerie_raza')) and are(zs, v('galerie_z1')) and are(zs, v('galerie_z2'))
      and len({(round(o.x, 3), round(o.y, 3)) for o in bos}) == 4, 'C12b',
      'Galeria de admisie: R{:.0f}-{:.0f} mm, de la {:.0f} la {:.2f} mm ({:.0f} mm sub ferestre), cu 4 coloane la prezoane'
      .format(v('raza_camasa')*10, v('galerie_raza')*10, v('galerie_z1')*10, v('galerie_z2')*10, v('perete_cilindru')*10))
    bune = 0
    for nume, u_expr, w_expr, semn in TRANSFERURI:
        fi, c = semn*v(u_expr), v(w_expr)
        e, tt = (math.cos(fi), math.sin(fi)), (-math.sin(fi), math.cos(fi))
        pe = lambda d: [(n.x*o.x + n.y*o.y)*(1 if n.x*d[0] + n.y*d[1] > 0 else -1) for n, o in plane
                        if abs(n.z) < 1e-9 and abs(abs(n.x*d[0] + n.y*d[1]) - 1) < 1e-9]
        if are(pe(tt), c/2) and are(pe(tt), -c/2) and are(pe(e), v('canal_raza')):
            bune += 1
    t(bune == 5 and are(zs, v('z_transfer_sus')), 'C12c',
      'Canalele de transfer: {} din 5 (A±, B±, C), cât coarda ferestrei, până la R{:.0f} mm, din galerie până la marginea transferului ({:.2f} mm)'
      .format(bune, v('canal_raza')*10, v('z_transfer_sus')*10))
    zgm = (v('galerie_z1') + v('galerie_z2'))/2
    xv, zc = v('compresor_x'), v('compresor_z')
    rac = [o for r, a, o in cil if abs(abs(a.x) - 1) < 1e-9 and abs(r - v('D_admisie')/2) < TOL and abs(o.y) < TOL and abs(o.z - zgm) < TOL]
    gol = [o for r, a, o in cil if abs(abs(a.x) - 1) < 1e-9 and abs(r - v('roata_D2')/2 - v('joc_roata')) < TOL
           and abs(o.y) < TOL and abs(o.z - zc) < TOL]
    tor = [fa for fa in corp.faces if fa.geometry.surfaceType == adsk.core.SurfaceTypes.TorusSurfaceType]
    ys = [o.y for n, o in plane if abs(abs(n.y) - 1) < 1e-9]
    t(rac and gol and len(tor) >= 2 and are(ys, v('latime_evacuare')/2) and are(ys, -v('latime_evacuare')/2)
      and are(zs, v('z_evacuare_sus')), 'C12d',
      'Colectorul compresorului turnat în spatele cilindrului (inel R{:.1f}, axa la z = {:.1f} mm), canalul Ø{:.0f} intră în galerie '
      'la {:.1f} mm; conducta de evacuare de {:.0f} mm iese în față până la {:.2f} mm'
      .format(v('spirala_R')*10, zc*10, v('D_admisie')*10, zgm*10, v('latime_evacuare')*10, v('z_evacuare_sus')*10))
    # Cămașa de apă, intrarea pe dreapta, trecerile spre chiulasă
    vert = lambda r_: {(round(o.x, 3), round(o.y, 3)) for r, a, o in cil if abs(abs(a.z) - 1) < 1e-9 and abs(r - r_) < TOL}
    gp = vert(v('gauri_punte_d')/2)
    gp_ok = all(any(math.hypot(x - cx, y - cy) < 1e-3 for cx, cy in gp) for x, y in _gauri_punte_xy(v))
    zm = (v('apa_z1') + v('apa_z2'))/2
    fi_ = v('apa_intrare_unghi')
    e_ = (math.cos(fi_), math.sin(fi_))
    intr = [o for r, a, o in cil if abs(abs(a.x*e_[0] + a.y*e_[1]) - 1) < 1e-6 and abs(r - v('racord_apa_D')/2) < TOL
            and abs(o.x*e_[1] - o.y*e_[0]) < TOL and abs(o.z - zm) < TOL]
    h_apa = v('apa_z2') - v('apa_z1')
    A_r = (v('galerie_raza') - v('apa_raza_int'))*h_apa
    A_c = (v('prezon_raza') - v('bosaj_prezon') - v('apa_raza_int'))*h_apa
    t(pe_ax(v('apa_raza_int')) and are(zs, v('apa_z1')) and are(zs, v('apa_z2')) and gp_ok and len(gp) == 5 and intr, 'C12e',
      'Cămașa de apă: R{:.1f}-{:.0f} mm, de la {:.1f} la {:.2f} mm, plină în față pe ±{:.0f} mm; secțiunea {:.0f} mm2, {:.0f} mm2 pe lângă '
      'coloanele prezoanelor (ca în s17); intrarea Ø{:.0f} radial la {:.0f}° (dreapta-spate); 5 treceri Ø{:.0f} spre chiulasă'
      .format(v('apa_raza_int')*10, v('galerie_raza')*10, v('apa_z1')*10, v('apa_z2')*10, v('apa_fata_y')*10, A_r*100, A_c*100,
              v('racord_apa_D')*10, math.degrees(fi_), v('gauri_punte_d')*10))
    # Evacuarea: tranziția de aceeași arie, flanșa cu doi prezoane M8
    g = _geometrie_evacuare(v)
    pe_x = lambda r_: [o for r, a, o in cil if abs(abs(a.x) - 1) < 1e-9 and abs(r - r_) < TOL and abs(o.y) < TOL and abs(o.z - g['zem']) < TOL]
    A_dr = v('latime_evacuare')*(v('z_evacuare_sus') - v('z_fereastra_jos'))
    A_ce = math.pi/4*v('evacuare_D')**2
    xs_ = [o.x for n, o in plane if abs(abs(n.x) - 1) < 1e-9]
    pz_ = {round(o.y, 3) for r, a, o in cil if abs(abs(a.x) - 1) < 1e-9 and abs(r - 0.34) < TOL and abs(o.z - g['zem']) < TOL
           and abs(abs(o.y) - g['y_prezon']) < TOL}
    p_port = g['y_prezon'] - v('evacuare_D')/2 - 0.34
    cam = [fa for fa in corp.faces if fa.geometry.surfaceType not in (adsk.core.SurfaceTypes.PlaneSurfaceType,
           adsk.core.SurfaceTypes.CylinderSurfaceType, adsk.core.SurfaceTypes.TorusSurfaceType)
           and fa.boundingBox.minPoint.x > v('raza_camasa') and fa.boundingBox.maxPoint.x < v('corp_raza') + 1e-3]
    t(pe_x(v('evacuare_D')/2) and abs(A_ce/A_dr - 1) < 0.01 and cam and any(abs(x - v('corp_raza') - v('flansa_grosime')) < TOL for x in xs_)
      and len(pz_) == 2 and p_port >= v('perete_minim') - TOL and v('flansa_filet') >= 1.6, 'C12f',
      'Evacuarea: tranziție de la fereastra {:.0f} x {:.1f} mm ({:.0f} mm2) la gura Ø{:.1f} ({:.0f} mm2); flanșa la {:.0f} mm de corp, '
      '2 prezoane M8 la ±{:.0f} mm ({:.0f} mm filet, {:.1f} mm perete până la gură)'
      .format(v('latime_evacuare')*10, (v('z_evacuare_sus') - v('z_fereastra_jos'))*10, A_dr*100, v('evacuare_D')*10, A_ce*100,
              v('flansa_grosime')*10, g['y_prezon']*10, v('flansa_filet')*10, p_port*10))
    # Ghilotina: lama în fantă cu jocul ei, ghidată cât lama_rezerva, axul servomotorului în carcasă
    lama = gaseste(design, 'supapa_evacuare')
    occ_s = ocurenta(design, '12_Supapa')
    ax_s = [o for r, a, o in cil if abs(abs(a.y) - 1) < 1e-9 and abs(r - 0.4) < TOL and abs(o.x - g['x_ax']) < TOL and abs(o.z - g['z_ax']) < TOL]
    if lama is None or occ_s is None:
        t(False, 'C12g', '12_Supapa lipsește')
    else:
        mm_ = adsk.core.Application.get().measureManager
        L_ = lama.createForAssemblyContext(occ_s)
        j_c = mm_.measureMinimumDistance(L_, corp.createForAssemblyContext(ocurenta(design, '11_Cilindru_corp'))).value
        j_l = min(mm_.measureMinimumDistance(L_, b).value for b in _corpuri(design, [('10_Cilindru', None)]))
        j_h = min(mm_.measureMinimumDistance(L_, b).value for b in _corpuri(design, [('15_Chiulasa', None)]))
        h_l = lama.boundingBox.maxPoint.z - lama.boundingBox.minPoint.z
        ghidat = g['z_buzunar'] - lama.boundingBox.minPoint.z
        sus_inchis = lama.boundingBox.maxPoint.z - v('cursa_supapa') - g['z_buzunar']
        podea = g['z_carcasa'] - g['zem'] - g['Ro']
        t(abs(j_c - v('lama_joc')) < 1e-4 and j_l > 0.01 and j_h > 0.3 and ghidat >= v('lama_rezerva') - TOL and sus_inchis >= 0.3 - TOL
          and ax_s and are(zs, g['z_buzunar']) and podea >= 0.3 - TOL, 'C12g',
          'Ghilotina: lama {:.1f} x {:.0f} x {:.1f} mm, jocul în fantă {:.2f} mm, {:.2f} mm de cămașă, {:.1f} mm de chiulasă; ghidată {:.0f} mm '
          'la deschis, închisă rămâne {:.0f} mm în buzunar (pârghia); axul Ø8 al servomotorului în carcasă, {:.0f} mm deasupra gurii de evacuare'
          .format(v('lama_grosime')*10, 2*g['lama']['y']*10, h_l*10, j_c*10, j_l*10, j_h*10, ghidat*10, sus_inchis*10, podea*10))
    # Injecția este directă, în chiulasă: pe canalele B nu mai rămâne niciun dom de injector
    occ_c = ocurenta(design, '11_Cilindru_corp')
    domuri = [sk.name for sk in occ_c.component.sketches if sk.name.startswith(('Dom_Injector', 'Gaura_Injector'))] if occ_c else ['?']
    t(not domuri, 'C12h', 'Canalele B fără domuri de injector (injecția e directă, în chiulasă)' if not domuri
      else 'Au rămas schițe de injector în cilindru: ' + ', '.join(domuri))
    # Compresorul: roata și motorul pe axa orizontală, jocul față de colector, distanțele, interferențele
    roata, motor = gaseste(design, 'roata_compresor'), gaseste(design, 'motor_compresor')
    pr, cr = _fete(roata)
    ok_r = any(abs(r - v('roata_D2')/2) < TOL and abs(abs(a.x) - 1) < 1e-9 and abs(o.y) < TOL and abs(o.z - zc) < TOL for r, a, o in cr)
    lat = max(max(abs(fa.boundingBox.maxPoint.y), abs(fa.boundingBox.minPoint.y)) for fa in corp.faces
              if fa.boundingBox.maxPoint.x < -v('corp_raza') - 0.1)
    t(ok_r and lat <= v('corp_raza') + 1e-6, 'C13a',
      'Compresorul în linie: roata Ø{:.1f} mm pe axa orizontală la z = {:.1f} mm, motorul în spatele ei; partea din spatele cilindrului '
      'are ±{:.1f} mm, în lățimea cilindrului (±{:.0f})'.format(v('roata_D2')*10, zc*10, lat*10, v('corp_raza')*10))
    occ_c, occ_k = ocurenta(design, '90_Compresor'), ocurenta(design, '11_Cilindru_corp')
    mm_ = adsk.core.Application.get().measureManager
    px = lambda b: b.createForAssemblyContext(occ_c)
    joc_r = mm_.measureMinimumDistance(px(roata), corp.createForAssemblyContext(occ_k)).value
    vecini = _corpuri(design, CARTER + [('61_Rotor', None), ('15_Chiulasa', None)])
    joc_v = min(mm_.measureMinimumDistance(px(b), w).value for b in (roata, motor) for w in vecini)
    col = adsk.core.ObjectCollection.create()
    for nume in ('10_Cilindru', '11_Cilindru_corp', '12_Supapa', '15_Chiulasa', '50_Carter_stanga', '51_Carter_dreapta', '61_Rotor', '90_Compresor'):
        col.add(ocurenta(design, nume))
    ii = design.createInterferenceInput(col)
    ii.areCoincidentFacesIncluded = False
    inter = design.analyzeInterference(ii)
    n_int = inter.count if inter else 0
    perechi = []
    for i in range(n_int):
        r_ = inter.item(i)
        perechi.append('{}/{}'.format(r_.entityOne.name, r_.entityTwo.name))
    t(abs(joc_r - v('joc_roata')) < 1e-4 and joc_v >= v('joc_compresor') - 1e-4 and n_int == 0, 'C13b',
      'Jocul roată-colector {:.3f} mm (cerut {:.3f}); roata și motorul la {:.1f} mm de carter, rotor și chiulasă (>= {:.0f}); '
      'interferențe între cămașă, corp, ghilotină, chiulasă, carter, rotor și compresor: {}{}'.format(
          joc_r*10, v('joc_roata')*10, joc_v*10, v('joc_compresor')*10, n_int, ' (' + ', '.join(perechi) + ')' if perechi else ''))
    return teste
