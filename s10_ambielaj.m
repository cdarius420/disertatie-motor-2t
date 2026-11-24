% S10_AMBIELAJ  Biela, arborele cotit și rulmenții paliere, după YZ125.
% Rulmenții: durata L10 = (C/P)^3 milioane de rotații (ISO 281, bile), cu P
% sarcina echivalentă pe ciclu, P = (media |F|^3)^(1/3). Forța pe piston
% (gaze + inerție) se împarte egal pe cei doi rulmenți.
% Forța reziduală a echilibrării (s12) se adaugă acoperitor la vârful gazelor (A5).
% Limită: nu include tragerea curelei CVT; rulmenții cu ace din bielă nu sunt verificați încă.
P = parametri();
fprintf('\n=== S10 Biela, arborele cotit și rulmenții ===\n');
mm = 1e3;

% 1. Pachetul ambielajului: brațe + cap de bielă + șaibe + joc = lățimea YZ125
gol = P.b_picior + 2*P.saiba + P.joc_lat_cap;        % între brațe
t_brat = (P.latime_amb - gol)/2;
pres = (P.l_maneton - gol)/2;                          % cât intră manetonul în fiecare braț
fprintf('Ambielaj %.3f mm: brațe de %.2f mm, gol %.2f mm; manetonul intră %.2f mm în fiecare braț\n', ...
        P.latime_amb*mm, t_brat*mm, gol*mm, pres*mm);
verifica(P.l_maneton <= P.latime_amb && pres >= 0.9*t_brat, 'A1', sprintf( ...
         'Manetonul (%.1f mm) stă în brațe pe %.0f%% din grosime și nu iese în afară', P.l_maneton*mm, 100*pres/t_brat));
R_brat = P.h_comp + P.L - P.r - (P.S + P.joc_raclor + P.zona_raclor) - P.joc_cg;   % = raza max. a contragreutăților
fprintf('Brațele: rază %.2f mm (fusta la PME trece la %.1f mm deasupra)\n', R_brat*mm, P.joc_cg*mm);
verifica(R_brat > P.r + P.D_ochi_cap/2, 'A2', sprintf('Capul bielei (Ø%.0f) încape în brațe: %.1f mm până la marginea lor', ...
         P.D_ochi_cap*mm, (R_brat - P.r - P.D_ochi_cap/2)*mm));

% 2. Forța pe rulmenți de-a lungul ciclului
cazuri = {'oraș', 4000, 3e5; 'putere maximă', P.n_putere, P.imep_plin};
L10h = zeros(1, 2);
for k = 1:2
    n = cazuri{k,2}; w = 2*pi*n/60;
    thEO = P.thEO_deschis;
    [th, p0, V, dV] = presiune_cilindru(P, 0, thEO); h = 2*pi/numel(th);
    [~, p1] = presiune_cilindru(P, 1, thEO);
    W0 = sum(p0.*dV)*h; W1 = sum(p1.*dV)*h;
    [~, p] = presiune_cilindru(P, (cazuri{k,3}*P.Vd - W0)/(W1 - W0), thEO);
    [~, ~, d2x] = cinematica(th, P);
    F = (p - P.p_cc)*P.Ap - P.m_rec*d2x*w^2;          % pe axa cilindrului [N]
    Fr = abs(F)/2;                                      % pe fiecare rulment
    Peq = mean(Fr.^3)^(1/3);
    L10h(k) = (P.rul_C/Peq)^3*1e6/(60*n);
    fprintf('   %-14s %5d rot/min, PMI %.0f bar: P echivalent %.2f kN, vârf %.2f kN, L10 = %.0f h\n', ...
            cazuri{k,1}, n, cazuri{k,3}/1e5, Peq/1e3, max(Fr)/1e3, L10h(k));
end
% Vârful: forța de proiectare a gazelor (s06), la turație mică, fără inerție care s-o scadă
thEO = P.thEO_deschis;
[th, p0, V, dV] = presiune_cilindru(P, 0, thEO); h = 2*pi/numel(th);
[~, p1] = presiune_cilindru(P, 1, thEO);
W0 = sum(p0.*dV)*h; W1 = sum(p1.*dV)*h;
[~, p] = presiune_cilindru(P, (P.imep_plin*P.Vd - W0)/(W1 - W0), thEO);
Pmax = (P.f_proiect*max(p) - P.p_cc)*P.Ap/2;
s0 = P.rul_C0/Pmax;
verifica(s0 >= 1, 'A3', sprintf('Rulmenții 63/22 la forța de proiectare (%.1f kN fiecare): s0 = C0/P = %.2f >= 1', ...
         Pmax/1e3, s0));
verifica(L10h(1) >= P.L10h_min, 'A4', sprintf('Durata L10 la mers prin oraș: %.0f h >= %d h', L10h(1), P.L10h_min));
fprintf('   La putere maximă continuă: %.0f h.\n', L10h(2));

% 3. Forța reziduală după echilibrare (s12), la limitator, adunată la vârful gazelor
E = echilibrare(P);
F_rez = max(P.BF, 1 - P.BF)*E.m_rec*P.r*(2*pi*P.n_max/60)^2/2;     % pe fiecare rulment
verifica(P.rul_C0/(Pmax + F_rez) >= 1, 'A5', sprintf( ...
         'Rulmenții cu forța reziduală la %d rot/min (%.1f kN fiecare, adunată la gaze): s0 = %.2f >= 1', ...
         P.n_max, F_rez/1e3, P.rul_C0/(Pmax + F_rez)));

% 4. Rotorul mașinii electrice pe conul arborelui: cuplul îl ține frecarea (pana doar poziționează)
I = isg_constante(P);
F_ax = P.M_piulita/(P.K_piulita*P.d_filet);                          % forța din piuliță
al_con = atan(1/(2*P.conicitate));                                   % semiunghiul conului 1:5
r_m = (P.con(1) - P.con(2)/(2*P.conicitate))/2;                      % raza medie a conului
T_con = P.mu_con*F_ax*r_m/(sin(al_con) + P.mu_con*cos(al_con));
verifica(T_con >= P.CS_con*I.T_max, 'A7', sprintf( ...
         'Rotorul pe con 1:%d cu piulița M12 la %d N m: frecarea ține %.0f N m >= %d x %.1f N m (cuplul maxim al mașinii)', ...
         P.conicitate, P.M_piulita, T_con, P.CS_con, I.T_max));

% 5. Tija bielei în I, în secțiunea cea mai mică (unde iese din ochiul piciorului)
w_min = P.tija_lat(2) + (P.tija_lat(1) - P.tija_lat(2))*(P.D_ochi_picior/2)/P.L;
A_min = w_min*P.b_picior - (w_min - 2*P.tija_talpa)*(P.b_picior - P.tija_inima);
sig = 2*Pmax/A_min;
verifica(sig <= P.Re_biela/3, 'A6', sprintf( ...
         'Tija în I (%.1f mm2): compresiune %.0f MPa <= Re/3 = %.0f MPa la forța de proiectare', ...
         A_min*1e6, sig/1e6, P.Re_biela/3e6));
