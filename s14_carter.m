% S14_CARTER  Carterul: prezoanele bazei, băile de ulei și lamela, ajustajele rulmenților paliere.
% Geometria vine din geometrie_carter.m; Fusion o construiește în pasul 9 (C9).
P = parametri();
G = geometrie_carter(P);
fprintf('\n=== S14 Carterul ===\n');
mm = 1e3; um = 1e6;
fprintf('Cavitate R%.2f mm, pereți la ±%.2f mm; rulmenții între %.2f și %.2f mm; fața carterului la ±%.2f mm\n', ...
        G.R_cav*mm, G.y_cav*mm, G.y_ri*mm, G.y_re*mm, G.y_ext*mm);
fprintf('Fusurile ies din carter cu %.0f mm spre variator (stânga) și %.0f mm spre mașina electrică (dreapta)\n', G.capete_libere*mm);
fprintf('Băile: %.2f L în față și în spate, până la ±%.0f mm, de la %.1f mm sub axă (fundul rotorului) până la axă;\n', ...
        P.V_ulei*1e3, P.baie_x*mm, -G.z_jos*mm);
fprintf('   nivelul la repaus %.1f mm sub axă; sorbul la x = 0, %.1f mm sub axă; lamela la %d° pe cavitate\n', ...
        -G.z_nivel*mm, -G.z_sorb*mm, P.unghi_lamela);

% 1. Prezoanele: peretele până la fanta bielei, cavitatea arborelui și gura cilindrului
xs = G.prezoane(1); ys = G.prezoane(2); rg = P.prezon(2)/2;
z_jos = P.baza_cil - P.prezon(3);
in_banda = ys - rg < G.y_cav;                                        % gaura trece prin dreptul cavității
p_fanta = (xs - rg) - G.x_fanta;
p_cav = hypot(xs, z_jos) - rg - G.R_cav;
p_gura = P.prezon_raza - rg - G.D_gura/2;
p_min = min([p_gura, in_banda*min(p_fanta, p_cav) + ~in_banda*Inf]);
verifica(p_min >= P.perete_min, 'R1', sprintf( ...
         'Prezoanele M8 la ±%d° și ±%d°: pereți de %.1f mm la fantă, %.1f mm la cavitate, %.1f mm la gură (>= %.0f mm)', ...
         P.prezon_unghi, 180 - P.prezon_unghi, p_fanta*mm, p_cav*mm, p_gura*mm, P.perete_min*mm));
verifica(P.prezon(3) - 2e-3 >= 2*P.prezon(1), 'R2', sprintf('Filetul prezoanelor în aluminiu: %.0f mm >= 2 d', (P.prezon(3) - 2e-3)*mm));

% 1b. Băile sunt un tub în U: la accelerația a, suprafața e planul z = z0 + k x, cu k = a/g
% (la frânare uleiul fuge în față, k > 0). Volumul rămâne același; sorbul de la x = 0 vede z0.
z0 = @(k) fzero(@(z) G.volum(z, k) - P.V_ulei, [G.z_fund - G.x_i*abs(k) - 0.01, G.z_tavan + G.x_i*abs(k) + 0.01]);
d_fr = z0(P.a_frana) - G.z_sorb;  d_ac = z0(-P.a_accel) - G.z_sorb;
verifica(min(d_fr, d_ac) >= P.sorb_min, 'U1', sprintf( ...
         'Sorbul de sub arbore rămâne acoperit: %.0f mm de ulei la repaus, %.0f mm la frânare cu %.1f g, %.0f mm la accelerare cu %.1f g (>= %.0f mm)', ...
         (G.z_nivel - G.z_sorb)*mm, d_fr*mm, P.a_frana, d_ac*mm, P.a_accel, P.sorb_min*mm));
umplere = P.V_ulei/G.volum(0, 0);
sub_lamela = G.z_nivel - G.lamela_sus;  aer = G.z_tavan - G.z_nivel;  canal = G.z_nivel + G.R_ext;
verifica(sub_lamela >= 5e-3 && aer >= 10e-3 && canal >= 10e-3, 'U2', sprintf( ...
         ['La repaus: lamela e sub ulei cu %.1f mm (sifon: o etanșează și spală gazele), canalul de sub arbore e plin ' ...
          '(+%.0f mm), %.0f mm de aer sub tavan; băile sunt pline %.0f%%'], sub_lamela*mm, canal*mm, aer*mm, 100*umplere));

% 1c. Pistonul pompează carterul: cu lamela, aerul închis se comprimă până la presiunea băilor la
% PME și se destinde la PMI. Volumul liber al cavității: cilindrul cavității minus arborele și biela
% (acoperitor: fusurile ies din cavitate), plus alezajul de sub fustă la PMI.
E = echilibrare(P);
V_pme = pi*G.R_cav^2*2*G.y_cav - (E.m_arbore + E.m.biela)/P.rho_otel;
V_pmi = V_pme + P.Vd;
p_min = 1e5*(V_pme/V_pmi)^P.n_carter;
[~, p0, ~, dV] = presiune_cilindru(P, 0, P.thEO_deschis);  [~, p1] = presiune_cilindru(P, 1, P.thEO_deschis);
h = 2*pi/numel(p0);  W0 = sum(p0.*dV)*h;  W1 = sum(p1.*dV)*h;        % ca în s06: sarcina plină
[~, p] = presiune_cilindru(P, (P.imep_plin*P.Vd - W0)/(W1 - W0), P.thEO_deschis);
F_gaz = (max(p) - P.p_cc)*P.Ap;                                      % forța maximă pe piston
coloana = P.rho_ulei*9.81*(G.z_nivel - G.lamela_c(2));               % uleiul de deasupra lamelei
verifica(p_min >= P.p_cc && (1e5 - p_min) >= 100*coloana, 'U3', sprintf( ...
         ['Pistonul pompează carterul între %.2f și 1 bar (%.0f/%.0f cm3): de %.0f ori coloana de ulei de deasupra ' ...
          'lamelei (%.0f Pa); forțele sunt calculate cu %.2f bar la PMI (acoperitor, %.1f%% din forța maximă)'], ...
          p_min/1e5, V_pme*1e6, V_pmi*1e6, (1e5 - p_min)/coloana, coloana, P.p_cc/1e5, 100*(p_min - P.p_cc)*P.Ap/F_gaz));

% 1d. Aripioarele, pompa de ulei și bilanțul termic (ungere.m)
U = ungere(P);
verifica(U.ta >= 2.5e-3 && U.gol >= U.ta && U.ha/U.gol <= 4 && G.y_ar <= G.y_ext - P.joc_capac + 1e-12, 'U4', sprintf( ...
         ['Aripioarele: %d pe fiecare latură, %.0f mm groase, gol %.0f mm, înalte de %.0f mm (raport %.1f <= 4), ' ...
          '%.0f mm sub fața carterului; suprafața băilor x%.1f, ~%.0f W la %.0f km/h și %.0f K'], U.nr_aripioare, U.ta*mm, ...
          U.gol*mm, U.ha*mm, U.ha/U.gol, P.joc_capac*mm, U.raport_A, U.Q_aripioare, P.aer_racire(1)*3.6, P.aer_racire(2)));
verifica(U.v_sorb <= 1 && U.dT_jet <= 25, 'U5', sprintf( ...
         ['Pompa de ulei: %.2f L/min la %.1f bar (duze %s mm: %.2f + %.2f + %.2f L/min), %.0f W electric; aspirația %.2f m/s ' ...
          'prin galeria Ø%.0f (<= 1 m/s); uleiul se încălzește cu %.0f K pe la jeturi'], U.Q*6e4, U.dp/1e5, mat2str(P.jet_ulei*mm), ...
          U.Q_jet*6e4, U.P_el, U.v_sorb, P.galerie_sorb*mm, U.dT_jet));
verifica(U.T_ulei <= P.T_ulei_max, 'U6', sprintf( ...
         ['Bilanțul uleiului: %.0f W intră (jetul de sub piston și rulmenții), aripioarele scot %.0f W, răcitorul ulei-apă %.0f W; ' ...
          'uleiul iese din răcitor la %.0f °C cu apa la %d °C (<= %d)'], U.Q_ulei, U.Q_aripioare, U.Q_racitor, U.T_ulei, ...
          P.T_apa_modul, P.T_ulei_max));

% 2. Ajustajele rulmenților 63/22: strângerea pe fus (k5) și în bucșă (M7), jocul rămas din C4
s_int = [P.tol_fus(1) - P.tol_rul_d(2), P.tol_fus(2) - P.tol_rul_d(1)];          % strângerea pe fus
s_ext = [P.tol_rul_D(1) - P.tol_bucsa(2), P.tol_rul_D(2) - P.tol_bucsa(1)];      % negativ = joc
joc_termic = P.alfa_otel*P.dT_inele*(P.d_fus + P.rul(2))/2;                       % inelul interior mai cald
red = @(si, se) P.k_inel(1)*si + P.k_inel(2)*max(se, 0);
joc_prob = mean(P.joc_C4) - red(mean(s_int), mean(s_ext)) - joc_termic;
joc_rau  = P.joc_C4(1) - red(s_int(2), s_ext(2)) - joc_termic;
fprintf('Fus Ø22 k5: strângere %.0f...%.0f µm; inel exterior în bucșa Ø56 M7: %.0f...%.0f µm (negativ = joc)\n', ...
        s_int*um, s_ext*um);
fprintf('Jocul radial C4 %.0f...%.0f µm; rămas: probabil %.1f µm, în cazul cel mai rău %.1f µm\n', ...
        P.joc_C4*um, joc_prob*um, joc_rau*um);
verifica(joc_prob > 0, 'R3', sprintf('Rulmenții C4 rămân cu joc radial la ajustajele probabile: %.1f µm', joc_prob*um));
% Motivul bucșei: presat direct în aluminiu (S7), inelul își pierde strângerea la cald
pierdere = (P.alfa_carter - P.alfa_otel)*P.rul(2)*(P.T_carter - 20);
s_al = [P.tol_rul_D(1) - P.tol_S7_al(2), P.tol_rul_D(2) - P.tol_S7_al(1)];
verifica(s_al(1) - pierdere < 0, 'R4', sprintf( ...
         'Bucșa de oțel e necesară: presat direct în aluminiu (S7, %.0f...%.0f µm), la %d °C ar rămâne %.0f...%.0f µm', ...
         s_al*um, P.T_carter, (s_al - pierdere)*um));
