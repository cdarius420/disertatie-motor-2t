function U = ungere(P)
% UNGERE  Aripioarele băilor, pompa de ulei cu jeturile, aspirația și bilanțul termic al uleiului (s14, s17).
G = geometrie_carter(P);
% Aripioarele: turnabile (grosime, pas, înălțime) și cât scot la viteza și diferența de temperatură date
U.ta = P.aripioare(1);  U.gol = P.aripioare(2) - U.ta;  U.ha = G.y_ar - (G.y_cav + P.t_carter);
x_disc = @(z) (abs(z) < G.R_ext)*sqrt(max(G.R_ext^2 - z^2, 0));
L_ar = arrayfun(@(z) 2*max(0, G.x_contur(z) - x_disc(z)), G.z_ar);  % lungimea vizibilă (sub discul carterului)
A_ar = 2*sum(L_ar*(2*U.ha + U.ta));                                  % ambele părți
A_lat = 2*sum(L_ar)*P.aripioare(2);                                  % laturile băilor fără aripioare
U.raport_A = (A_ar + A_lat - 2*sum(L_ar)*U.ta)/A_lat;
v = P.aer_racire(1);  nu_aer = 1.6e-5;  k_aer = 0.027;  Lm = mean(L_ar)/2;   % o aripioară: jumătate de baie
h_c = 0.664*k_aer/Lm*sqrt(v*Lm/nu_aer)*0.71^(1/3);                  % placă plană, curgere laminară
mL = sqrt(2*h_c/(P.k_al*U.ta))*U.ha;  eta = tanh(mL)/mL;
U.Q_aripioare = h_c*(A_ar*eta + A_lat - 2*sum(L_ar)*U.ta)*P.aer_racire(2);
U.nr_aripioare = numel(G.z_ar);
% Jeturile: duze sub presiune, debitul din ecuația orificiului
U.Q_jet = P.Cd_jet*pi/4*P.jet_ulei.^2*sqrt(2*P.p_ulei/P.rho_ulei);
U.Q = sum(U.Q_jet);
U.dp = P.p_ulei + P.dp_ulei_traseu;
U.P_el = U.Q*U.dp/P.eta_pompa_ulei;
U.v_sorb = U.Q/(pi/4*P.galerie_sorb^2);
% Căldura în ulei: jetul de sub piston și rulmenții; o scot aripioarele, restul răcitorul ulei-apă
P_comb = P.imep_plin*P.Vd*P.n_putere/60/P.eta_i;
U.Q_ulei = P.f_ulei*P_comb + P.P_rulmenti;
U.dT_jet = U.Q_ulei/(U.Q*P.rho_ulei*P.cp_ulei);
U.Q_racitor = max(0, U.Q_ulei - U.Q_aripioare);
U.T_ulei = P.T_apa_modul + U.Q_racitor/P.UA_racitor;               % uleiul la ieșirea din răcitor
end
