% S02_TOBA  Lungimea acordată a tobei: cât trebuie să varieze și de ce.
% Relația lui Jennings: L = a * theta_ev / (12 * n), cu a viteza undei [m/s],
% theta_ev durata evacuării [grade], n turația [rot/min], L [m].
% Împărțirea rolurilor: variatorul ține turația, toba variabilă compensează
% temperatura gazelor, care schimbă viteza undei.
P = parametri();
fprintf('\n=== S02 Toba de rezonanță: lungimea acordată ===\n');
a_und = @(T_C) sqrt(P.gamma_ev*P.R_ev*(T_C + 273.15));   % viteza undei [m/s]
L_acord = @(a, th_e, n) a.*th_e./(12*n);
th_e = 360 - 2*P.thEO_deschis;

% Verificare: exemplul lui Jennings (1973) în unități imperiale:
% 1700 ft/s, 190 grade, 9000 rot/min dau 35,9 inci.
L_j = L_acord(1700*0.3048, 190, 9000)/0.0254;
verifica(abs(L_j - 35.9) < 0.2, 'T1', sprintf('Formula reproduce exemplul Jennings: %.1f inci', L_j));

a_ref = a_und(P.EGT_ref);
L0 = L_acord(a_ref, th_e, P.n_putere);
fprintf('Viteza undei la %d grade C: %.0f m/s\n', P.EGT_ref, a_ref);
fprintf('Lungimea acordată la %d rot/min: %.0f mm\n', P.n_putere, L0*1e3);

% 1) Toba fixă: turația de acord se mută cu temperatura
n_acord = @(T_C) a_und(T_C)*th_e/(12*L0);
fprintf('Toba fixă: acordul se mută de la %.0f la %.0f rot/min între %d și %d grade C\n', ...
        n_acord(P.EGT_min), n_acord(P.EGT_max), P.EGT_min, P.EGT_max);

% 2) Cât trebuie să varieze lungimea, pe roluri
banda = P.n_putere*[1 - P.toleranta_cvt, 1 + P.toleranta_cvt];
dL_T  = L_acord(a_und(P.EGT_max), th_e, P.n_putere) - L_acord(a_und(P.EGT_min), th_e, P.n_putere);
dL_n  = abs(diff(L_acord(a_ref, th_e, banda)));
dL_TN = L_acord(a_und(P.EGT_max), th_e, banda(1)) - L_acord(a_und(P.EGT_min), th_e, banda(2));
dL_tr = abs(diff(L_acord(a_ref, th_e, P.banda_fara_cvt)));
fprintf('Doar temperatura (%d-%d grade C), turație fixă: %.0f mm (%.1f%%)  <- rolul tobei\n', ...
        P.EGT_min, P.EGT_max, dL_T*1e3, 100*dL_T/L0);
fprintf('Doar abaterea variatorului (+-%.0f%%): %.0f mm (%.1f%%)\n', 100*P.toleranta_cvt, dL_n*1e3, 100*dL_n/L0);
fprintf('Ambele, cazul cel mai rău: %.0f mm (%.1f%%)\n', dL_TN*1e3, 100*dL_TN/L0);
fprintf('Fără variator, banda %d-%d rot/min: %.0f mm (%.1f%%)  <- de ce tobele variabile singure n-au prins\n', ...
        P.banda_fara_cvt, dL_tr*1e3, 100*dL_tr/L0);
verifica(dL_T < 0.10*L0, 'T2', 'Compensarea temperaturii cere sub 10% din lungime: realizabil telescopic');
verifica(dL_TN < dL_tr/3, 'T3', 'Cu variatorul, toba variază de peste 3 ori mai puțin decât fără el');

% --- Grafic ---
n = linspace(5000, 12000, 200);
f = figura_noua(); hold on;
for T = [P.EGT_min P.EGT_ref P.EGT_max]
    plot(n, L_acord(a_und(T), th_e, n)*1e3, 'LineWidth', 1.5);
end
plot([P.n_putere P.n_putere], [L_acord(a_und(P.EGT_min), th_e, P.n_putere) ...
      L_acord(a_und(P.EGT_max), th_e, P.n_putere)]*1e3, 'k', 'LineWidth', 3);
grid on; xlabel('turația [rot/min]'); ylabel('lungimea acordată [mm]');
legend(sprintf('%d grade C', P.EGT_min), sprintf('%d grade C', P.EGT_ref), ...
       sprintf('%d grade C', P.EGT_max), 'cursa tobei: doar temperatura');
title('Variatorul ține turația; toba compensează temperatura gazelor');
salveaza_figura(f, 's02_toba');
