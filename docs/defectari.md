# Tabelul de defectări al anexelor (MR-010)

Motorul depinde de anexe electrice: fără compresor nu se baleiază, fără pompa de ulei se gripează, fără pompa de apă se supraîncălzește. Fiecare defect de mai jos are o detecție și o reacție a ECU. Pragurile marcate DE CONFIRMAT se fixează după fișele produselor alese; cele din `parametri.m` sunt citate cu numele lor.

| # | Defectul | Efectul | Detecția | Reacția ECU |
|---|---|---|---|---|
| 1 | Compresorul se oprește sau se blochează | fără baleiaj: rateuri, apoi oprire; mecanic nu e periculos | turația motorului compresorului (din driverul lui) și presiunea din galerie | tăierea injecției; avertizare; deplasare pe ISG cât permite bateria |
| 2 | Presiune prea mare în galerie | detonație, suprasarcină | presiunea din galerie peste prag (DE CONFIRMAT) | scăderea turației compresorului |
| 3 | Presiunea uleiului scade (sorb înfundat, supapa de presiune blocată deschis, gerotorul uzat; pompa e mecanică, pe arbore) | gripare la rulmenți și piston | presiunea din galeria de ulei sub prag (nominal `p_ulei`, pragul DE CONFIRMAT) | oprire controlată: tăierea injecției, avertizare |
| 4 | Uleiul se supraîncălzește | ungere slabă | temperatura uleiului peste `T_ulei_max` | reducerea puterii |
| 5 | Pompa de apă se oprește sau se pierde lichid | supraîncălzirea chiulasei și a cilindrului | temperatura apei din chiulasă peste prag (DE CONFIRMAT) și curentul pompei | reducerea puterii, apoi oprire controlată |
| 6 | Presiunea benzinei scade (pompa de înaltă presiune) | amestec sărac, rateuri | presiunea din rampă sub prag (DE CONFIRMAT) | limitarea sarcinii |
| 7 | Presiunea benzinei crește peste limită | conducta și injectorul suprasolicitate | supapa de limitare (mecanică) deschide; presiunea din rampă | tăierea injecției |
| 8 | Injectorul rămâne deschis | amestec bogat, filmul de ulei spălat | presiunea din rampă scade, sonda lambda arată bogat | oprirea injectorului și a pompei |
| 9 | Tensiunea bateriei scade sub minim | anexele se opresc | tensiunea pe celule sub `V_cel_min` (BMS) | consumatorii neesențiali opriți, apoi oprire controlată; contactorul deschis |
| 10 | Convertorul 48/12 V cade | pompa de apă se oprește | tensiunea pe 12 V | oprire controlată (ca la 5) |
| 11 | Modulul invertorului ISG se supraîncălzește | modulul se distruge | temperatura modulului peste `Tj_max` (senzor în modul) | reducerea curentului ISG |
| 12 | Senzorul de poziție a arborelui cade | injecția și aprinderea pierd sincronizarea | plauzibilitate față de poziția din ISG | oprire controlată |
| 13 | Gripare în mers | roata din spate se poate frâna brusc | căderea bruscă a turației | DE CONFIRMAT: cât de repede decuplează ambreiajul centrifugal nu este analizat |

## Senzorii care rezultă

| Senzorul | Locul | MR care îi face bosajul |
|---|---|---|
| Presiune și temperatură aer | galeria compresorului | MR-008 / MR-010 |
| Presiune ulei | galeria principală de ulei, în carterul drept | MR-009 / MR-010 |
| Temperatură ulei | după răcitor | MR-009 / MR-010 |
| Temperatură apă | chiulasa, lângă termostat | MR-006 |
| Presiunea benzinei | rampa sau conducta de înaltă presiune | MR-007 |
| Sonda lambda | toba | MR-011 |
| Poziția arborelui | DE CONFIRMAT: senzorul ISG sau o roată dințată separată | MR-010 |
| Tensiunea celulelor | bateria (BMS) | în afara motorului |
| Temperatura modulului | modulul invertorului, în capacul din dreapta | existent în s18 |
