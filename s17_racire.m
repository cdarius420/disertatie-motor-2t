% S17_RACIRE  Răcirea cu apă: căldura, debitul, vitezele în cămașă și în treceri, pereții.
P = parametri();
W = racire(P);
mm = 1e3;
fprintf('\n=== S17 Răcirea cu apă ===\n');
fprintf('La %d rot/min: %.1f kW indicat, %.1f kW din combustibil, %.1f kW spre apă -> %.2f kg/s (%.0f L/min) la +%g K\n', ...
        P.n_putere, W.P_i/1e3, W.P_comb/1e3, W.Q/1e3, W.mdot, W.Qv*6e4, P.dT_apa);
fprintf('Cămașa cilindrului: R%.1f-%.0f mm, de la %.1f la %.2f mm (deasupra ferestrelor), în C, plină în față la ghilotină\n', ...
        W.R_apa*mm, W.z_apa*mm);
fprintf('Intrarea pe dreapta la %.0f grade; ramura lungă duce %.0f%% din debit, coloana cea mai încărcată %.0f%%\n', ...
        W.unghi_intrare, 100*W.f_ramura, 100*W.f_coloana);
verifica(max([W.v_ramura W.v_coloana W.v_punte W.v_racord]) <= P.v_apa_max, 'W1', sprintf( ...
         ['Viteza apei: %.2f m/s în cămașă (%.0f mm2), %.2f m/s pe lângă coloana prezonului (%.0f mm2), ' ...
          '%.2f m/s în cele %d treceri spre chiulasă, %.2f m/s în racord (<= %.1f)'], ...
         W.v_ramura, W.A_ramura*1e6, W.v_coloana, W.A_coloana*1e6, W.v_punte, P.n_gauri_punte, W.v_racord, P.v_apa_max));
verifica(min([W.perete_fanta W.perete_camasa W.perete_evacuare]) >= P.perete_min, 'W2', sprintf( ...
         'Pereți: %.1f mm apă-ghilotină, %.1f mm apă-cămașa cilindrului, %.1f mm apă-conducta de evacuare (>= %.0f mm)', ...
         W.perete_fanta*mm, W.perete_camasa*mm, W.perete_evacuare*mm, P.perete_min*mm));

% Circuitul întreg: căldura totală, pierderile de presiune, punctul de funcționare al pompei, radiatorul
U = ungere(P);  D = capac(P);
Q_tot = W.Q + U.Q_racitor + sum(D.pierderi);                        % motorul, uleiul, modulul de putere
dT_tot = Q_tot/(W.mdot*P.cp_apa);
q = @(v) 0.5*P.rho_apa*v^2;
Df = P.furtun_apa(1);  vf = W.Qv/(pi/4*Df^2);
f = 0.316*(P.rho_apa*vf*Df/P.mu_apa)^-0.25;                          % Blasius, furtun neted
dp = [ (f*P.furtun_apa(2)/Df + P.K_furtun)*q(vf), ...               % furtunurile, coturile
       1.5*q(D.v_apa), ...                                           % camera modulului
       q(W.v_coloana) + 1.5*q(W.v_punte), ...                        % cămașa (coloana) și trecerile din punte
       q(vf), ...                                                    % chiulasa, ieșirea
       P.K_termostat*q(vf), P.dp_radiator];                          % termostatul, radiatorul
k_sist = sum(dp)/W.Qv^2;                                             % pierderile cresc cu pătratul debitului
c = P.pompa_apa;  b = (c(2,2) - c(1,2))/((c(2,1) - c(1,1))/6e4);  a = c(1,2) - b*c(1,1)/6e4;   % pompa: dp = a + b Q
Q_op = (b + sqrt(b^2 + 4*k_sist*a))/(2*k_sist);
fprintf('Circuitul: %.1f kW în apă (motor %.1f, ulei %.2f, modul %.2f), +%.1f K; pierderi %.2f bar la %.0f L/min: %s kPa\n', ...
        Q_tot/1e3, W.Q/1e3, U.Q_racitor/1e3, sum(D.pierderi)/1e3, dT_tot, sum(dp)/1e5, W.Qv*6e4, mat2str(round(dp/1e3, 1)));
verifica(Q_op >= 1.15*W.Qv, 'W3', sprintf( ...
         ['Pompa electrică de 12 V (clasa CWA50) dă %.0f L/min pe circuitul acesta, la %.2f bar; trebuie %.0f L/min (rezervă %.0f%%, ' ...
          'turația se reduce prin PWM)'], Q_op*6e4, (a + b*Q_op)/1e5, W.Qv*6e4, 100*(Q_op/W.Qv - 1)));
ra = P.aer_radiator;  rho_aer = 101325/(287*(ra(3) + 273.15));
A_rad = Q_tot/(rho_aer*ra(1)*1005*ra(2));
T_cap = P.T_apa_modul + dT_tot;                                      % apa la ieșirea din chiulasă = intrarea în radiator
eps_rad = ra(2)/(T_cap - ra(3));
verifica(eps_rad <= 0.6 && T_cap >= P.T_termostat, 'W4', sprintf( ...
         ['Radiatorul: %.1f dm2 de miez frontal la %.0f m/s prin miez (aerul +%.0f K, eficacitate %.2f <= 0,6); apa iese din chiulasă ' ...
          'la %.0f °C, peste deschiderea termostatului (%d °C)'], A_rad*100, ra(1), ra(2), eps_rad, T_cap, P.T_termostat));
