% S01_CINEMATICA  Bielă-manivelă, ferestre, supapa de evacuare, fereastra de injecție (TPI).
% Rulează singur sau din ruleaza_tot.m. Valorile vin din parametri.m.
P  = parametri();
th = (0:0.1:360)';                         % unghiul arborelui, de la PMI [grade]
[x, dx, d2x] = cinematica(th, P);

fprintf('\n=== S01 Cinematica bielă-manivelă și ferestrele ===\n');
fprintf('Cilindree: %.1f cm3, lambda = r/L = %.3f\n', P.Vd*1e6, P.r/P.L);

% --- Viteze și accelerații la turația de putere ---
w = 2*pi*P.n_putere/60;
v = dx*w;  a = d2x*w^2;
fprintf('La %d rot/min: viteza medie a pistonului %.1f m/s, maximă %.1f m/s\n', ...
        P.n_putere, 2*P.S*P.n_putere/60, max(abs(v)));
fprintf('Accelerația pistonului: %.0f m/s2 la PMI, %.0f m/s2 la PME\n', a(1), a(th == 180));
fprintf('Forța de inerție maximă: %.0f N\n', P.m_rec*max(abs(a)));

% --- Verificări ale cinematicii ---
verifica(abs(x(1)) < 1e-12 && abs(x(th == 180) - P.S) < 1e-12, 'C1', 'x(PMI) = 0 și x(PME) = cursa');
verifica(abs(P.Vd*1e6 - 124.8) < 0.2, 'C2', 'Cilindreea = 124,8 cm3 (pi/4 * B^2 * S)');
dx_num = gradient(x, th*pi/180);
d2_num = gradient(dx, th*pi/180);
verifica(max(abs(dx_num(2:end-1) - dx(2:end-1))) < 1e-5*P.S, 'C3', 'dx/dtheta analitic = derivata numerică');
verifica(max(abs(d2_num(2:end-1) - d2x(2:end-1))) < 1e-4*P.S, 'C4', 'd2x/dtheta2 analitic = derivata numerică');

% --- Ferestrele: evacuare cu supapa deschisă și închisă, transfer ---
xEO_d = cinematica(P.thEO_deschis, P);
xEO_i = cinematica(P.thEO_inchis, P);
xTO   = cinematica(P.thTO, P);
Ae_d = P.w_ev*max(0, x - xEO_d);           % aria deschisă a evacuării [m2]
Ae_i = P.w_ev*max(0, x - xEO_i);
At   = P.w_tr*max(0, x - xTO);
dur  = @(thO) 360 - 2*thO;                 % fereastră simetrică față de PME
fprintf('Durata evacuării: %d grade cu supapa deschisă, %d grade cu supapa închisă\n', ...
        dur(P.thEO_deschis), dur(P.thEO_inchis));
fprintf('Supapa coboară marginea ferestrei cu %.2f mm\n', (xEO_i - xEO_d)*1e3);
fprintf('Durata transferului: %d grade; destinderea liberă: %d grade\n', dur(P.thTO), P.thTO - P.thEO_deschis);
h_ev = P.S - xEO_d;
fprintf('Înălțimea ferestrei de evacuare: %.1f mm (%.0f%% din cursă)\n', h_ev*1e3, 100*h_ev/P.S);

% --- Timp-arie specific, după Blair [s/m] ---
thr = th*pi/180;
ta  = @(A, n) trapz(thr, A)/(2*pi*n/60)/P.Vd;
idx_bd = th >= P.thEO_deschis & th <= P.thTO;
fprintf('Timp-arie specific la %d rot/min [s/m]: evacuare %.2e, transfer %.2e, destindere liberă %.2e\n', ...
        P.n_putere, ta(Ae_d, P.n_putere), ta(At, P.n_putere), trapz(thr(idx_bd), Ae_d(idx_bd))/w/P.Vd);
fprintf('Timp-arie la evacuare, supapa închisă: %.0f%% din cel cu supapa deschisă\n', 100*ta(Ae_i, 1)/ta(Ae_d, 1));
verifica(abs(dur(P.thEO_deschis) - 196) < 1e-9, 'C5', 'Calaj simetric: închiderea evacuării la 360 - deschiderea');

% --- Așezarea ferestrelor pe circumferință: evacuarea, A±, B±, boost ---
R = P.B/2;
cen = [0, P.tr_unghi(1), -P.tr_unghi(1), P.tr_unghi(2), -P.tr_unghi(2), P.tr_unghi(3)];
lat = [P.w_ev, P.tr_latime(1), P.tr_latime(1), P.tr_latime(2), P.tr_latime(2), P.tr_latime(3)];
semi = asind(lat/2/R);                               % semideschiderea unghiulară
[~, o] = sort(mod(cen, 360)); c = mod(cen(o), 360); sm = semi(o);
gol = mod([c(2:end) c(1)+360] - c - sm - [sm(2:end) sm(1)], 360);   % unghiul plin dintre ferestre vecine
punti = 2*R*sind(gol/2);                             % coarda punții, la alezaj
fprintf('Ferestre: evacuare 0°, A ±%d°, B ±%d°, boost %d°; puntea cea mai îngustă %.1f mm\n', ...
        P.tr_unghi, min(punti)*1e3);
verifica(abs(2*P.tr_latime(1) + 2*P.tr_latime(2) + P.tr_latime(3) - P.w_tr) < 1e-12, 'L1', ...
         'Lățimile A, B și boost însumează lățimea de transfer din timp-arie');
verifica(min(punti) >= P.punte_min, 'L2', sprintf('Puntea cea mai îngustă %.1f mm >= %.1f mm', ...
         min(punti)*1e3, P.punte_min*1e3));
d_stift = min(abs(mod(P.unghi_stift - cen + 180, 360) - 180) - semi);
verifica(2*R*sind(d_stift/2) >= P.punte_min, 'L3', sprintf(['Știftul segmenților (%d°) e pe perete ' ...
         'plin, la %.1f mm de cea mai apropiată fereastră'], P.unghi_stift, 2*R*sind(d_stift/2)*1e3));

% --- Fereastra de injecție în transfer (TPI): cât timp e deschisă fereastra de transfer ---
% Benzina intră în cilindru doar cu aerul din transfer. Momentul exact din
% fereastră se calibrează (mai târziu = mai puțină benzină scăpată pe evacuare).
thTC = 360 - P.thTO;
fer  = thTC - P.thTO;                      % [grade]
n_v  = [P.n_ralanti 6000 P.n_putere P.n_max];
fprintf('Fereastra de injecție în transfer: %d grade (de la %d la %d grade)\n', fer, P.thTO, thTC);
for k = 1:numel(n_v)
    fprintf('   %5d rot/min: %.2f ms; 1 grad = %.1f us\n', n_v(k), fer/(6*n_v(k))*1e3, 1/(6*n_v(k))*1e6);
end
thEC = 360 - P.thEO_deschis;

% --- Volumul mort din raportul de compresie reținut ---
xEC = cinematica(thEC, P);
Vc  = P.Ap*xEC/(P.CRt - 1);
fprintf('Volumul mort: %.2f cm3; raport geometric echivalent: %.1f\n', Vc*1e6, (P.Vd + Vc)/Vc);

% --- Grafice ---
f = figura_noua();
subplot(3,1,1); plot(th, x*1e3, 'LineWidth', 1.5); grid on; ylabel('x [mm]');
title(sprintf('Bielă-manivelă: %.0f x %.1f mm, L = %.0f mm', P.B*1e3, P.S*1e3, P.L*1e3));
subplot(3,1,2); plot(th, v, 'LineWidth', 1.5); grid on; ylabel('v [m/s]');
subplot(3,1,3); plot(th, a/1e3, 'LineWidth', 1.5); grid on; ylabel('a [km/s^2]'); xlabel('unghiul arborelui [grade de la PMI]');
salveaza_figura(f, 's01_cinematica');

f = figura_noua();
plot(th, Ae_d*1e4, 'LineWidth', 1.5); hold on;
plot(th, Ae_i*1e4, '--', 'LineWidth', 1.5);
plot(th, At*1e4, 'LineWidth', 1.5); grid on;
xlim([60 300]); xlabel('unghiul arborelui [grade de la PMI]'); ylabel('aria deschisă [cm^2]');
legend('evacuare, supapa deschisă', 'evacuare, supapa închisă', 'transfer', 'Location', 'north');
title('Supapa de evacuare scurtează evacuarea');
salveaza_figura(f, 's01_ferestre');
