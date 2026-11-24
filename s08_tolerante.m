% S08_TOLERANTE  Ajustajul piston-cilindru: clasele de sortare și jocul la cald.
% Jocul la cald = jocul la rece + D*(alfa_cil*dT_cil - alfa_pist*dT_fusta).
% Pistonul se dilată mai mult decât cămașa, deci jocul scade la cald.
P = parametri();
fprintf('\n=== S08 Ajustajul piston-cilindru ===\n');
um = 1e6; D = P.B;
pas = P.alezaj_tol/(P.n_clase - 0.5);          % 4 clase pe 14 um: benzi de 2 um la pas de 4 um
banda_cil = pas/2;
banda_pist = diff(P.joc_piston) - banda_cil;     % ce rămâne pentru piston din plaja jocului
fprintf('Alezaj Ø%.0f +0/+%.0f um, %d clase; joc la rece %.0f-%.0f um pe pereche\n', ...
        D*1e3, P.alezaj_tol*um, P.n_clase, P.joc_piston*um);
fprintf('   Clasa   Alezaj [mm]          Piston [mm]\n');
for k = 0:P.n_clase - 1
    c = D + k*pas + [0 banda_cil];
    p = [c(2) - P.joc_piston(2), c(1) - P.joc_piston(1)];
    fprintf('   %c       %.3f-%.3f        %.3f-%.3f\n', 'A' + k, c*1e3, p*1e3);
end
fara = [P.joc_piston(1), P.joc_piston(1) + P.alezaj_tol + banda_pist];
fprintf('Fără sortare, cu aceleași toleranțe, jocul ar fi %.0f-%.0f um: de aceea se sortează.\n', fara*um);

d_cald = D*(P.alfa_cil*(P.T_cil - P.T_ref) - P.alfa_pist*(P.T_fusta - P.T_ref));
cald = P.joc_piston + d_cald;
fprintf('La sarcină plină (cămașa %d °C, fusta %d °C) jocul se schimbă cu %+.1f um: %.1f-%.1f um\n', ...
        P.T_cil, P.T_fusta, d_cald*um, cald*um);
verifica(cald(1) >= P.joc_cald_min, 'J1', sprintf(['Jocul minim la cald %.1f um >= %.0f um ' ...
         '(filmul de ulei)'], cald(1)*um, P.joc_cald_min*um));
fprintf('   Limită: pornirea la rece, cu pistonul încălzit înaintea cămășii, nu e acoperită.\n');
fprintf('   Calculatorul limitează sarcina până se încălzește lichidul de răcire.\n');
