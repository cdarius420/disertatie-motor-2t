# Modelul din Fusion

Modelul se construiește din script, nu se editează de mână.

1. În MATLAB, `ruleaza_tot` scrie `parametri_fusion.csv` (prin `s07_export_fusion.m`).
2. În Fusion (Z în sus, un design deschis): Shift+S, rulează `construieste` din `fusion/construieste/`.
3. Scriptul importă parametrii, construiește componentele care lipsesc, rulează verificările și scrie `raport.txt`.
4. Ca să refaci o componentă, scrie-i numele în `construieste/reconstruieste.txt`; scriptul o șterge, o reface și golește fișierul.
5. Parametrii utilizator care nu mai sunt în CSV se șterg la final (`sterge_orfani`).

Fișierele `cinematica_fusion.csv`, `inertii_fusion.csv`, `volume_fusion.csv` și `multicorp/*.step` sunt scrise de script și citite de MATLAB (s12, s13, m02).
