% s20_bilant_electric.m — bilanțul electric și dimensionarea bateriei (Etapa 5, decizia C)
%
% Bateria de 16 celule LFP n-avea capacitate stabilită. O dimensionează puterea, nu energia:
% vârful cerut la asistența de pornire (ISG la cuplul maxim) plus compresorul și consumatorii.
% Celula de referință: A123 / Lithium Werks ANR26650M1B, celulă de putere LFP
% (fișa 26650 Power Cell, 2022: https://lithiumwerks.com/wp-content/uploads/2022/08/26650-Power-Cell-080322.pdf).
%
% Strategia de asistență e o IPOTEZĂ până o decizi: ISG la cuplul maxim cel mult t_asist secunde,
% ca la Honda PCX Hybrid (asistența durează cel mult 4 s: https://global.honda/en/tech/Hybrid_System_PCX_HYBRID/).

P = parametri; B = baterie(P);   % valorile celulei și ipotezele stau în parametri.m

fprintf('Cererea la bornele bateriei: ISG %.1f kW mecanic (plafonul controlerului) / %.2f + Roots %.2f kW + consumatori %.0f W = %.1f kW\n', ...
        B.P_isg_mec/1e3, P.eta_isg, B.P_roots/1e3, sum(P.P_aux), B.P_varf/1e3);
fprintf('Curentul la %.1f V: %.0f A de vârf, %.0f A continuu (fără generare)\n', B.V_min, B.I_varf, B.I_cont);
fprintf('Pachet %ds%dp din ANR26650M1B: %.0f Wh, %.2f kg celule, cutie %.0f x %.0f x %.0f mm (%.1f L)\n', ...
        P.n_cel, P.n_par, B.E_Wh, B.m_cel, B.cutie*1e3, prod(B.cutie)*1e3);
fprintf('O asistență de %.0f s ia %.1f Wh (%.1f%% din pachet); cu DoD %.0f%%: %.0f asistențe pe încărcare\n', ...
        P.t_asist, B.E_asist_Wh, 100*B.E_asist_Wh/B.E_Wh, 100*P.DoD, floor(P.DoD*B.E_Wh/B.E_asist_Wh));
fprintf('Frânarea regenerativă admisă de celule: %.1f kW timp de %.0f s, %.1f kW continuu\n', B.P_regen/1e3, P.cel_t_puls, B.P_gen_cont/1e3);

verifica(B.I_varf <= P.n_par*P.cel_I_puls, 'BT1', sprintf('Vârful de %.0f A <= %d x %d A (descărcarea de %d s a celulei)', B.I_varf, P.n_par, P.cel_I_puls, P.cel_t_puls));
verifica(B.I_cont <= P.n_par*P.cel_I_cont, 'BT2', sprintf('Continuu %.0f A <= %d x %d A', B.I_cont, P.n_par, P.cel_I_cont));
verifica(B.V_cel_varf >= P.V_cel_min, 'BT4', sprintf('La vârf celula ține %.2f V >= %.2f V (minimul pentru care e calculat ISG); ar trebui %dp', ...
         B.V_cel_varf, P.V_cel_min, B.n_par_tensiune));
verifica(P.t_asist <= P.cel_t_puls, 'BT3', sprintf('Asistența de %.0f s <= %.0f s, durata vârfului din fișă', P.t_asist, P.cel_t_puls));
