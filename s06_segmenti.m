% S06_SEGMENTI  Presiunea maximă, forțele pe piston, segmenții și raclorul.
% Pachetul: 2 segmenți de compresie sus, cu știfturi (capetele nu trec prin
% ferestre), plus un raclor jos pe fustă. Carterul e uns ca la 4T, deci
% uleiul trebuie oprit înainte de ferestre: raclorul nu urcă niciodată
% peste marginea de jos a ferestrelor (brevetul CA 2674151).
P = parametri();
fprintf('\n=== S06 Presiunea maximă, pistonul și segmenții ===\n');

% --- 1. Presiunea maximă la sarcină plină (supapa de evacuare deschisă) ---
thEO = P.thEO_deschis;
[th, p0, V, dV] = presiune_cilindru(P, 0, thEO);
h = 2*pi/numel(th);
[~, p1] = presiune_cilindru(P, 1, thEO);
W0 = sum(p0.*dV)*h; W1 = sum(p1.*dV)*h;
Q  = (P.imep_plin*P.Vd - W0)/(W1 - W0);
[~, p] = presiune_cilindru(P, Q, thEO);
[pmax, kmax] = max(p);
p_pr = P.f_proiect*pmax;
fprintf('Sarcină plină, PMI %.1f bar: presiune maximă %.1f bar la %.0f grade (%.0f după PMI)\n', ...
        P.imep_plin/1e5, pmax/1e5, th(kmax), mod(th(kmax), 360));
fprintf('Presiunea de proiectare (x%.1f pentru avans și detonație): %.1f bar\n', P.f_proiect, p_pr/1e5);
verifica(abs(sum(p.*dV)*h - P.imep_plin*P.Vd)/(P.imep_plin*P.Vd) < 0.005, 'S1', ...
         'Presiunea medie indicată la sarcină plină atinsă (abatere < 0,5%)');

% --- 2. Forțele pe piston și pe bolț ---
F_gaz = (p_pr - P.p_cc)*P.Ap;
[~, ~, d2x0] = cinematica(0, P);
for n = [P.n_putere P.n_max P.n_supra]
    w = 2*pi*n/60;
    F_in = P.m_rec*d2x0*w^2;                  % inerția la PMI, spre chiulasă
    fprintf('   %5d rot/min: forța de gaze %.1f kN, inerția la PMI %.1f kN, rezultanta pe bolț %.1f kN\n', ...
            n, F_gaz/1e3, F_in/1e3, (F_gaz - F_in)/1e3);
end
% La 2T fiecare PMI e PMI de ardere. Cazul cel mai rău pentru bolț: frâna de
% motor cu injecția tăiată la supraturare, când rămâne doar compresia.
F_mot = (max(p0) - P.p_cc)*P.Ap;
F_in_s = P.m_rec*d2x0*(2*pi*P.n_supra/60)^2;
fprintf('   Frână de motor fără ardere, %d rot/min: compresia %.1f kN, inerția %.1f kN -> bolțul e tras spre chiulasă cu %.1f kN\n', ...
        P.n_supra, F_mot/1e3, F_in_s/1e3, (F_in_s - F_mot)/1e3);

% --- 3. Segmentul de compresie: dimensionare elastică (bară curbă subțire) ---
% Presiune radială uniformă p pe un inel deschis de rază medie R:
%   M(psi) = p*h*R^2*(1 - cos psi), psi de la capete
%   rostul liber A0 = 36*pi*p*R^4/(E*t^3)  (Castigliano)
%   efortul maxim, opus rostului: sigma = 3*p*(D/t - 1)^2
D = P.B; t = P.seg_t; R = (D - t)/2;
A0 = 36*pi*P.seg_pe*R^4/(P.seg_E*t^3);
psi = linspace(0, pi, 20001);
A0_num = 2*trapz(psi, (P.seg_pe*R^2*(1 - cos(psi))).*(R*(1 - cos(psi)))*R)/(P.seg_E*t^3/12);
verifica(abs(A0_num - A0)/A0 < 0.001, 'S2', 'Rostul liber: formula închisă = integrala Castigliano numerică');
sig_lucru = 3*P.seg_pe*(D/t - 1)^2;
% Montajul peste piston: diametrul interior trebuie să treacă peste D,
% adică rostul se mai deschide cu 2*pi*t - A0 față de starea liberă.
sig_mont = (8*P.seg_E/3)*(1 - A0/(2*pi*t))/(D/t - 1)^2;
fprintf('Segment %.1f x %.1f mm, presiune elastică %.2f MPa: rost liber %.1f mm\n', ...
        D*1e3, t*1e3, P.seg_pe/1e6, A0*1e3);
fprintf('   Efort în lucru %.0f MPa; efort la montaj %.0f MPa\n', sig_lucru/1e6, sig_mont/1e6);
fprintf('   Materialul trebuie să reziste la încovoiere la cel puțin %.0f MPa (coeficient %.1f)\n', ...
        P.CS_seg*max(sig_lucru, sig_mont)/1e6, P.CS_seg);
fprintf('   Forța gazelor pe segment depășește de multe ori elasticitatea: presiunea de proiectare e de %.0f ori presiunea elastică\n', ...
        p_pr/P.seg_pe);

% --- 4. Ridicarea segmentului în canal (flutter) ---
% Segmentul se ridică de pe flancul de jos când inerția lui, spre chiulasă,
% învinge diferența de presiune care îl apasă: p_cil - p_dedesubt < rho*h*a.
% Caz favorabil: sub segment e presiunea din carter (cea mai mică posibilă).
[~, ~, d2x] = cinematica(th, P);
inchis = th >= 360 - thEO | th <= thEO;     % fereastra de evacuare închisă
fprintf('Ridicarea segmentului în timpul fazei închise (etanșarea contează):\n');
fer = zeros(numel(P.seg_h), 2);
for j = 1:numel(P.seg_h)
    for k = 1:2
        n = [P.n_putere P.n_max]; w = 2*pi*n(k)/60;
        p_in = P.seg_rho*P.seg_h(j)*d2x*w^2;      % "presiunea" de inerție [Pa]
        ridica = inchis & (p - P.p_cc) < p_in & d2x > 0;
        fer(j, k) = sum(ridica)*(360/numel(th));
    end
    fprintf('   h = %.1f mm: %4.1f grade la %d rot/min, %4.1f grade la %d rot/min\n', ...
            P.seg_h(j)*1e3, fer(j,1), P.n_putere, fer(j,2), P.n_max);
end
verifica(fer(1, 2) == 0, 'S3', sprintf(['Segmentul de %.1f mm nu se ridică în faza închisă ' ...
         'până la limitator (%d rot/min)'], P.seg_h(1)*1e3, P.n_max));

% --- 5. Raclorul pe fustă și contragreutățile ---
d_rac = P.S + P.joc_raclor;                   % coroană -> marginea de sus a raclorului
l_fusta = d_rac + P.zona_raclor;
gap_pme = P.h_comp + P.L - P.r - l_fusta;     % axa arborelui -> marginea fustei, la PME
R_cg = gap_pme - P.joc_cg;
fprintf('Raclorul: la cel puțin %.1f mm sub coroană; fusta lungă de %.1f mm\n', d_rac*1e3, l_fusta*1e3);
fprintf('La PME fusta coboară la %.1f mm de axa arborelui: contragreutățile pot avea rază de cel mult %.1f mm\n', ...
        gap_pme*1e3, R_cg*1e3);
verifica(d_rac >= P.S, 'S4', 'Raclorul nu trece niciodată prin ferestre (stă sub ele și la PMI)');
fprintf('Știfturile segmenților de compresie: capetele pe peretele plin dintre ferestre; raclorul nu are nevoie de știft.\n');
