# Modelul parametric în Fusion

`parametri.m` rămâne singura sursă a cotelor. `s07_export_fusion.m` le scrie în `parametri_fusion.csv`, iar scriptul `importa_parametri.py` le pune în Fusion ca User Parameters. Când schimbi o cotă, o schimbi în `parametri.m`, rulezi `ruleaza_tot`, apoi imporți din nou în Fusion.

## Importul

1. În Fusion: Utilities > Add-Ins > Scripts and Add-Ins.
2. Create > Script > Python, cu numele `importa_parametri`.
3. Înlocuiești codul generat cu `importa_parametri.py`, salvezi și apeși Run.
4. Alegi `parametri_fusion.csv`. Mesajul de la final spune câți parametri au fost creați și câți actualizați.

Cotele derivate sunt expresii: pozițiile ferestrelor depind de unghiurile de calaj, lungimea fustei de cursă, raza contragreutăților de bielă și fustă. Dacă schimbi un unghi direct în Fusion ca să încerci ceva, fereastra se mută singură. Valoarea finală o treci apoi în `parametri.m`.

## Structura recomandată

Fiecare cotă din schițe și din feature-uri trimite la un parametru: nicio cifră scrisă direct. Componentele, în ordinea în care le desenezi:

| Componentă | Ce conține | Parametri principali |
|---|---|---|
| 00_Schelet | schițele de bază: axa cilindrului, axa arborelui, PMI, PME, marginile ferestrelor | cursa, biela_L, x_EO_deschis, x_TO |
| 10_Cilindru | cilindrul, ferestrele, locașul supapei de evacuare | alezaj, latime_evacuare, latime_transfer, x_EO_inchis |
| 20_Piston | pistonul, canalele segmenților, raclorul pe fustă | inaltime_compresie, seg_grosime, seg_inaltime_sus, adancime_raclor, lungime_fusta |
| 15_Chiulasa | chiulasa, camera de ardere, bujia | SAR, squish, diametru_bol, raza_bol |
| 21_Bolt | bolțul și siguranțele | d_bolt, l_bolt, sig_d |
| 30_Biela | biela și rulmenții cu ace | biela_L, D_cap_biela, D_picior_biela, latime_picior |
| 40_Arbore | semi-arborii, manetonul, șaibele, rulmenții paliere | raza_manivela, raza_brat, latime_ambielaj, l_maneton |
| 60_Masina_electrica | rotorul exterior și statorul, pe dreapta (-Y), în locul aprinderii; rotorul pe con 1:5 cu pană Woodruff | raza_rotor, grosime_pahar, grosime_magnet |
| 70_Variator | fuliile, cureaua, servo-ul semifuliei, pe stânga (+Y) | distanta_axe_cvt, r1_min, r1_max, r2_max, semiunghi_curea, cursa_servo_cvt |
| 70_Supapa_evacuare | supapa și pârghia servo-ului | cursa_supapa |
| 80_Toba | toba cu secțiunea telescopică | lungimea și cursa vin din s02 |
| 90_Compresor | compresorul electric și conducta spre transfer | |

Legăturile (Joints) urmează schema cinematică din dosar: rotație pentru arbore și biela, translație pentru piston, translație pentru semifulia mobilă și pentru secțiunea tobei.

## Construcția pas cu pas: `construieste/`

Scriptul `construieste/construieste.py` e înregistrat în Fusion (Scripts and Add-Ins → + → Script or add-in from device → folderul `construieste`). Designul e de tip **Hybrid Design**, ca să poată avea componente.

La fiecare rulare:

1. **Pasul 0** reîncarcă toți parametrii din `parametri_fusion.csv`. Sursa e `parametri.m`: o valoare schimbată doar în Fusion se pierde la rularea următoare.
2. **Pașii de construcție** fac doar componentele care lipsesc. Ce există și ce ai corectat tu rămâne neatins.

| Pas | Componentă | Ce conține | Verificare |
|---|---|---|---|
| 1 | `00_Schelet` | Schița „Mecanism” în planul vertical XZ: axa cilindrului, manivela, biela, pistonul, ferestrele, raclorul la PMI, cercul contragreutăților. Arborele cotit stă pe axa Y. | S1a–S1d: schița definită complet; coroana urmează formula bielă-manivelă la 5–175°; ferestrele Fusion = formula = MATLAB; fusta la 3,000 mm de contragreutăți |
| 2 | `10_Cilindru` | Cămașa Ø54/Ø66 mm, de la fusta la PME (49,75 mm) la punte (164,25 mm). Evacuarea în față (+X), 38 mm. Transferuri Schnürle cu boost: A ±62° (9 mm), B ±105° (6 mm, cu injectoarele), boost C la 180° (10 mm). Ferestrele coboară până la coroana de la PME. | C2a–C2j: corp solid; capete, raze, margini și lățimi exacte (abatere < 0,01 µm); evacuarea pe +X; fiecare transfer la unghiul și coarda lui; cinci transferuri |

| 3 | `20_Piston` | Pistonul la PMI, pe baza YZ125: Ø53,9575 (jocul mediu), fusta 60 mm. Centura segmenților groasă de 4,35 mm, cu două canale de 0,84 mm; banda raclorului jos (56,5–58,54 mm sub coroană). Bosaje Ø25 legate de coroană, gol de 16,9 mm pentru piciorul bielei (15,9 + 2 × 0,5), alezaj de bolț Ø15,0075 cu câte un canal toric pentru siguranță la fiecare capăt. | C3a–C3e: corpuri solide; coroana și fusta; diametrul și jocul radial (0,0212 mm); fiecare canal la locul lui, cu 2 mm de perete în spate; alezajul în bosaje |
| 3b | `21_Bolt` | Bolțul tubular 15/9 × 41 mm (Wiseco 15 × 41) și două siguranțe din sârmă rotundă de 1 mm, la 0,2 mm de capetele bolțului. | C3f–C3h: bolțul de 41 mm, centrat; joc bolț–piston; două canale în piston și două siguranțe, sârma intră 0,40 mm în alezaj |
| 4 | `30_Biela` | Biela YZ125: 110 mm între axe, cap Ø28 pe maneton, picior Ø19 pe bolț, lată de 15,9 mm. Ochiuri Ø36 și Ø24, tija în I (16 → 11 mm, tălpi de 2,5 mm, inima de 3 mm), racordată R6 cu ochiurile: ~139 g. Rulmenții cu ace 22 × 28 și 15 × 19, cât lățimea bielei. | C4a–C4d: alezajele la 110 mm; lățimea și inima, simetrice; rulmenții; o singură bucată cu patru racordări |
| 5 | `40_Arbore` | Doi semi-arbori, ca la YZ125: brațe de 18,837 mm, gol 18,25 mm, ambielaj 55,925 mm. Brațele nu sunt discuri pline: contragreutate R46,75 pe ±`unghi_contragr` (56,0°, din s12), bosaj R18 în jurul manetonului și tangente între ele. Manetonul Ø22 × 54,5 presat în ei, două șaibe de 1 mm (joc lateral al capului 0,35 mm). Fusuri Ø22, rulmenți 63/22 la 0,5 mm de brațe. Capetele, de la rulment: 40 mm spre variator (stânga, +Y) și 44 mm spre mașina electrică (dreapta, −Y, în locul aprinderii). Capătul drept, ca la YZ125: con 1:5 de la Ø20 la Ø16 pe 20 mm, locaș de pană Woodruff 3 × 5 spre maneton, filet M12 × 1,25 (cosmetic, 6g) pentru piulița rotorului. | C5a–C5h: fețele brațelor și ale golului; capetele; razele și alezajul manetonului; manetonul; câte doi rulmenți și două șaibe; contragreutatea, bosajul și tangentele; conul, pana și filetul |
| 9 | `50_Carter_stanga`, `51_Carter_dreapta` | Două semicartere împărțite pe planul cilindrului (Y = 0), ca la YZ125, aluminiu turnat cu pereți de 5 mm. Cavitate R49,75 (3 mm față de contragreutăți), pereți la 2,5 mm de brațe, bosajele rulmenților la 0,5 mm. Rulmenții 63/22 în bucșe de oțel turnate (Ø64/56 × 16), simeringuri 22 × 35 × 7. Baza cilindrului la 62 mm, gura Ø66,5, 4 prezoane M8 la R48 mm, la ±40° și ±140° de evacuare (între ferestre). **Cavitatea e închisă și uscată**: uleiul stă în două băi, în față și în spate, de la axa arborelui până la cel mai de jos punct al rotorului (67,5 mm), lungi până la ±120 mm, late cât cavitatea (±30,46), teșite la 45° (jos 20, sus 25 mm). Sunt unite pe sub cavitate (tub în U, sorbul la mijloc), au câte o șicană la ±84,9 mm cu fante de 6 mm și 8 aripioare orizontale pe fiecare latură (3 mm, pas 8, până la 2 mm sub fața carterului). Pe peretele cavității, la 235° (spate-jos), sediul plan și fereastra de 30 × 12 mm ale lamelei. | C9a–C9h: simetria; fețele în lungul arborelui; bucșa, simeringul, bosajul, cavitatea; bucșa; baza, gura și prezoanele; băile și teșiturile; aripioarele; lamela, fereastra și șicanele |
| 9b | `53_Lamela` | Lamela din oțel de arc de 0,2 mm peste fereastră. Pistonul pompează carterul: la coborâre o deschide și împinge în băi uleiul scurs din rulmenți și gazele scăpate pe lângă segmenți; la urcare o închide. Lamela stă sub ulei: uleiul o etanșează (sifon) și spală gazele de ceața de ulei înainte de aerisire. | C9h; U1–U4 în s14 (sorbul la frânare și accelerare, nivelul, pompajul, aripioarele) |
| 10 | `60_Stator` | Statorul mașinii electrice, prins cu 3 șuruburi M5 în capacul din dreapta: tole de 0,2 mm, Ø110,6/Ø69,3, pachet 19,4 mm, 12 dinți (18,4 mm, vârfuri de 1,5 mm, deschiderea 2,5 mm). 12 bobine concentrate de câte 2 spire, una pe dinte, numite după fază (A+ A− C− C+ B+ B− …, factor de înfășurare 0,933); capetele ies 4,9 mm. | C10a–C10b: dinții, fundul crestăturilor, urechile, pachetul; 12 bobine, 4 pe fază |
| 11 | `61_Rotor` | Rotorul exterior: pahar de oțel C45 deschis spre capac, gros de 7,5 mm în dreptul magneților (închide fluxul la 1,6 T) și de 3 mm în rest; discul de 5 mm pe butucul conic 1:5. 14 magneți NdFeB N42SH arcuiți (4 mm, 83% din pas), polaritate alternată; întrefier 0,7 mm. Pana Woodruff 3 × 5, șaiba și piulița M12 × 1,25 la 50 N m. | C10c–C10e: 14 magneți; conul, pana, șaiba, piulița; inerția din Fusion = MATLAB (38,36 kg cm²); C8p–C8r: întrefier 0,7, disc–bobine 2,0, rotor–carter 2,0 mm |
| 12 | `11_Cilindru_corp` | Corpul cilindrului din aluminiu turnat, Ø112, de la bază la punte, cu cămașa presată. Patru prezoane M8 trec prin el până la chiulasă (strâng cilindrul și chiulasa). Jos, laturile sunt plane la fața carterului până la 69,5 mm, ca să treacă de paharul rotorului. **Galeria de admisie**: inel R33–52 mm între 70 și 105,75 mm (4 mm sub ferestre), 158 cm³, cu coloane în jurul prezoanelor. Din ea urcă cele 5 canale de transfer (A±, B±, C), late cât coarda ferestrei și adânci de 14 mm (1,12 × aria ferestrei), până la marginea transferului. În spate, racordul Ø25 cu flanșă de la compresor; în față, conducta de evacuare dreaptă (flanșa și supapa vin la evacuare). | C12a–C12d; K5–K6 în s16 |
| 13 | `90_Compresor` | Compresorul centrifugal electric, cu axa verticală în spatele cilindrului, deplasat spre dreapta cât raza spiralei, ca ieșirea tangentă să intre drept în racord. Roata Ø43,4 mm la 110.000 rot/min (anvelopa paletelor, cu arborele de 8 mm), jocul față de carcasă 0,3 mm, difuzor fără palete, spirala simplificată cu secțiune constantă Ø25. Deasupra, motorul (anvelopă Ø50 × 60 mm), cu aerul trecând pe lângă el (îl răcește) spre ochiul roții. | C13a–C13b (jocul roții, distanța de 5 mm, nicio interferență); K1–K4 în s16 |
| 14 | (materiale) | Fiecare corp primește un material propriu, copiat din Fusion Material Library: densitatea vine din `parametri.m`, iar modulul de elasticitate și limitele, de la baza cea mai apropiată. Oțel C45 ← AISI 1045 QT; AlSi9Cu3 turnat ← A356-T6; pistonul 4032 forjat ← 2014-T6; tole ← AISI 1006; bobinaj Cu 55% ← Copper; NdFeB ← fontă (fragil, ca ea). | C11: masa / volumul fiecărui corp = densitatea din `parametri.m` |
| 7 | (verificare) | Echilibrarea, cu masele pieselor din Fusion: volum × densitate (oțel 7,85, piston 4032 2,68 g/cm³), segmenții din s12. | C7a: factorul de echilibrare = 0,55; C7b: inerția arborelui din Fusion = cea din MATLAB (13,61 kg cm²) |
| 6 | `15_Chiulasa` | Chiulasa de 25 mm pe punte: banda de squish la 1,10 mm deasupra coroanei (SAR 0,45), bol sferic Ø40,05 × 10,14 mm (R24,844), alezajul bujiei Ø12,8. | C6a–C6b: volumul camerei din Fusion = cel din MATLAB (9,449 cm³); banda de squish și raza bolului |

Rezultatele verificărilor ajung în `construieste/raport.txt` la fiecare rulare.

Ca să reconstruiești o componentă generată, scrie-i numele în `construieste/reconstruieste.txt`, câte unul pe rând, apoi rulează. Scriptul o șterge, o construiește din nou și golește fișierul.

Boost-ul nu se alimentează prin ferestre în piston, ca la un 2T clasic: pistonul trebuie să rămână plin, ca raclorul să țină uleiul din carter sub ferestre. Boost-ul primește un canal propriu de la compresor.

## Legăturile dintre piese și rularea (pasul 8)

Piesele fixe sunt ancorate (Ground): `00_Schelet`, `10_Cilindru`, `15_Chiulasa`, `50_Carter_stanga`, `51_Carter_dreapta`, `53_Lamela`, `60_Stator`, `11_Cilindru_corp`, `90_Compresor`. Legăturile sunt „as-built” (piesele stau deja la PMI):

| Legătură | Piese | Tip |
|---|---|---|
| `Arbore_cilindru` | arbore – cilindru | rotație în jurul axei Y |
| `Biela_maneton` | bielă – arbore | rotație pe maneton |
| `Biela_bolt` | piston – bielă | rotație pe bolț |
| `Bolt_piston` | bolț – piston | fixă |
| `Piston_cilindru` | piston – cilindru | translație pe Z |
| `Rotor_arbore` | rotor – arbore | fixă (conul și pana) |

La fiecare rulare, scriptul rotește arborele 0–360° (din 2 în 2°) prin `Arbore_cilindru`, citește pozițiile pistonului și ale bielei, măsoară jocurile minime la 0/90/180/270° (inclusiv față de carter: brațe 0,5 mm, bielă ≥ 4,5 mm, cămașa în gură 0,25 mm; întrefierul 0,7 mm) și readuce mecanismul la PMI (C8a–C8r, fără C8o). Pozițiile ajung în `cinematica_fusion.csv` (s13 le compară cu formula). Tot aici scrie STEP-urile pieselor în `fusion/multicorp` și masele/inerțiile corpurilor mobile în `inertii_fusion.csv`, pentru modelul Simscape (m02), care are aceleași legături.

Ca să vezi mișcarea: în browser, la Joints, clic dreapta pe `Arbore_cilindru` → Drive Joints (sau Motion Study). În MATLAB: deschizi `model_multicorp.slx` și apeși Run; Mechanics Explorer arată mecanismul cu piesele din Fusion.

Ordinea, când pornești de la zero sau schimbi o piesă mobilă: `construieste` în Fusion → `ruleaza_tot` în MATLAB → `40_Arbore` în `reconstruieste.txt` și `construieste` din nou.

## Masele și echilibrarea: drumul Fusion → MATLAB → Fusion

La fiecare rulare, scriptul scrie `fusion/volume_fusion.csv`: volumul și centrul de masă (la PMI) ale pieselor mobile. `echilibrare.m` (s12) le înmulțește cu densitățile din `parametri.m`, calculează unghiul contragreutății pentru factorul cerut și îl pune în CSV-ul de parametri (s07). Brațele se desenează cu unghiul acesta, iar C7 recalculează factorul cu masele din Fusion.

Când schimbi o piesă mobilă (pistonul, bolțul, biela, manetonul):

1. rulezi `construieste` (scrie volumele noi);
2. rulezi `ruleaza_tot` (unghi nou; B5 îți spune dacă `m_rec` din `parametri.m` mai corespunde);
3. scrii `40_Arbore` în `reconstruieste.txt` și rulezi `construieste`. C7a trebuie să arate factorul cerut (acum 0,55).

Rulmenții din model sunt inele pline cu dimensiunile exterioare exacte (63/22, K22×28, K15×19). Biblioteca McMaster-Carr din Fusion nu are aceste tipuri: nu are 22 × 56, iar la 22 × 28 are doar rulmenți cu ace în bucșă trasă, nepotriviți pentru capul de bielă. McMaster rămâne bună pentru șuruburi, prezoane, piulițe, știfturi și O-ringuri, la pașii următori.

Ce lipsește încă din cilindru, ca pași separați: înclinarea canalelor de transfer (unghiurile de jet, după modelul 1D), flanșa evacuării și locașul supapei, bosajele injectoarelor în canalele B, garnitura bazei, răcirea. Mai lipsesc razele de racordare a ferestrelor, ca segmentul să nu se agațe; ele vin cu pistonul.

`unghi_manivela` mută mecanismul (1…179°). E un parametru doar pentru vizualizare și nu vine din CSV.
