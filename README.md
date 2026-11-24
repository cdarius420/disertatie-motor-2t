# Scripturi MATLAB: grup propulsor 2T hibrid

Pachetul calculează și verifică pe bucăți conceptul din propunere, exportă parametrii pentru Fusion, unde scriptul `construieste` desenează și verifică ansamblul, și construiește modelele Simulink și Simscape. Totul pleacă din `parametri.m`.

## Cum rulezi

1. Deschide folderul în MATLAB (R2020a sau mai nou, cu Simulink).
2. Scrie `ruleaza_tot` în Command Window.
3. Citește rezumatul de la final: **94 din 94** (MATLAB R2026a, 24 noiembrie 2026). Graficele și jurnalul ajung în `rezultate/`.
4. În Fusion (Z în sus): Shift+S, rulează `construieste`. Componentele trecute în `fusion/construieste/reconstruieste.txt` se șterg și se refac; raportul ajunge în `fusion/construieste/raport.txt`: **94 din 94**.

În GNU Octave merg scripturile s; `m01` și `m02` cer Simulink și Simscape și se sar.

## Fișiere

| Fișier | Ce face |
|---|---|
| `parametri.m` | Toate valorile, într-un singur loc. `[ESTIMARE]` marchează ce se înlocuiește cu datele motorului de referință. |
| `s01_cinematica.m` | Bielă-manivelă, ferestre, supapa de evacuare, timp-arie, fereastra de injecție |
| `s02_toba.m` | Lungimea acordată a tobei; cât trebuie să varieze toba variabilă și de ce |
| `s03_variator.m` | Variatorul: raportul, cursa servo-ului, reducția finală |
| `s04_masina_electrica.m` | Mașina de pe arbore: regula de tensiune, cuplul, rotorul |
| `s05_volant_activ.m` | Presiunea în cilindru, pornirea, volantul activ și dimensionarea lui |
| `s06_segmenti.m` | Presiunea maximă la sarcină plină, forțele pe bolț, segmenții de compresie, ridicarea lor în canal, raclorul pe fustă și contragreutățile |
| `s07_export_fusion.m` | Scrie `fusion/parametri_fusion.csv`: 274 de parametri Fusion, cotele derivate ca expresii, nu ca numere |
| `s08_tolerante.m` | Ajustajul piston-cilindru: clasele de sortare și jocul la cald |
| `s09_piston.m` | Pistonul și bolțul, pe baza pistonului YZ125 |
| `s10_ambielaj.m` | Biela, arborele cotit și rulmenții paliere |
| `s11_chiulasa.m` | Camera de ardere: banda de squish și bolul sferic |
| `s12_echilibrare.m` | Factorul de echilibrare, contragreutățile, inerția arborelui (cu volumele din Fusion) |
| `s13_cinematica_fusion.m` | Rularea cinematică din Fusion față de formula bielă-manivelă |
| `s14_carter.m` | Carterul: prezoanele, băile de ulei, lamela, aripioarele, pompa de ulei și bilanțul termic al uleiului, ajustajele rulmenților |
| `s15_masina_electrica.m` | Mașina de pe arbore: stator, bobine, rotor |
| `s16_compresor.m` | Compresorul electric în linie, turnat în spatele cilindrului: aerul, roata, motorul, galeria, așezarea |
| `s17_racire.m` | Răcirea cu apă: căldura, debitul, vitezele, pereții, pierderile pe circuit, pompa, radiatorul |
| `s18_capac.m` | Capacul din dreapta: jocurile față de rotor, prinderea statorului, camera de apă și temperatura modulului de putere, prinderile pe cadru, scutul |
| `s19_vehicul.m` | Viteza maximă din puterea netă de la arbore și încadrarea în L3e-A1 |
| `m01_model_arbore.m` | Construiește `model_arbore.slx` (dinamica arborelui + volantul activ) și îl compară cu s05 |
| `m02_multicorp.m` | Modelul Simscape Multibody al mecanismului, cu masele și inerțiile din Fusion |
| `fusion/` | `construieste/construieste.py` (scriptul Fusion: construiește componentele și le verifică), `README_fusion.md`, CSV-ul generat |
| `ruleaza_tot.m` | Rulează tot și scrie `rezultate/jurnal.txt` |
| funcții | `cinematica`, `presiune_cilindru`, `simuleaza_arbore`, `tabel_volant_activ`, `isg_constante`, `isg_geometrie`, `lungime_curea`, `viteza_medie`, `camera_ardere`, `echilibrare`, `geometrie_carter`, `compresor`, `racire`, `capac`, `ungere`, `evalueaza_fusion`, `verifica`, `figura_noua`, `salveaza_figura` |

`model_arbore.slx` e generat: nu se editează de mână. Se schimbă `parametri.m` sau `m01_model_arbore.m` și se rulează din nou. Datele stau în spațiul de lucru al modelului, deci modelul se deschide și rulează singur (cazul C).

## Ce verifică

| Cod | Verificare |
|---|---|
| C1–C5 | Cinematica: capetele cursei, cilindreea, derivatele analitice față de cele numerice, calajul simetric |
| T1–T3 | Toba: formula reproduce exemplul lui Jennings; cursa tobei; efectul variatorului |
| V1c–V2c | Variatorul: lungimea curelei constantă, raport monoton |
| E1–E2 | Mașina electrică: tensiunea indusă sub minimul bateriei; rotorul cu coeficient de siguranță ≥ 2 |
| F1a–F2e | Modelul de presiune și dinamica: presiunea medie indicată atinsă, lucrul din cuplu egal cu lucrul din p dV, simularea egală cu estimarea analitică, turația medie stabilă |
| V-VA | Volantul ușor cu comandă activă e la ralanti cel puțin la fel de liniștit ca volantul clasic |
| S1–S4 | Segmenții: presiunea medie la sarcină plină, rostul liber față de integrala numerică, segmentul nu se ridică la turația de putere, raclorul nu trece prin ferestre |
| F7a–F7e | Expresiile din Fusion, evaluate în MATLAB, dau aceleași cote ca s01, s03 și s06 |
| W1–W4 | Răcirea: vitezele apei ≤ 2,5 m/s, pereții ≥ 3 mm, pompa acoperă circuitul cu rezervă, radiatorul și termostatul |
| U5–U6 | Pompa de ulei (aspirația ≤ 1 m/s) și uleiul ≤ 110 °C la ieșirea din răcitor |
| Q1–Q3 | Capacul din dreapta (≥ 5 mm de rotor, filetul statorului ≥ 1,5 d), joncțiunea modulului ≤ 125 °C cu apa la 75 °C, prinderile M10 pe material plin |
| F7f | Fețele capacului din Fusion = s18 |
| N1–N3 | Cinematica rulată în Fusion = formula bielă-manivelă (poziția pistonului, rotația bielei, accelerația) |
| G1–G2 | Vehiculul: viteza maximă ≥ ținta la puterea netă; puterea și raportul putere/masă în limitele L3e-A1 |
| C…, S1… (Fusion) | Geometria fiecărui pas din `construieste`, jocurile în 180 de poziții, materialele, interferențele: lista completă în `raport.txt` |
| M1a–M1c | Simulink (integrare în timp, ode45) = metoda energiei pe unghi din s05, pentru volantul clasic, ușor pasiv și ușor activ: fluctuația sub 2%, turația sub 0,5% |

## Limitele modelelor

- Presiunea vine dintr-un model cu o zonă, cu ardere Wiebe și destindere simplificată. E bun pentru cuplu și dinamică, nu pentru baleiaj și unde. Pentru acelea urmează modelul 1D (EngMod2T sau un cod 1D).
- Toate valorile `[ESTIMARE]` se înlocuiesc cu motorul de referință. După înlocuire, rulezi din nou `ruleaza_tot` și verifici că testele trec.
- Pornirea nu include frecarea și ungerea la rece. Se măsoară pe motorul real.
- Turația medie e media în timp (unghi / timp, ce arată un turometru), nu media eșantioanelor pe unghi. La fluctuația de 38% (volant ușor, pasiv) cele două diferă cu 1,3%; M1b a picat până la corectarea definiției.
