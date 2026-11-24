function W = racire(P)
% RACIRE  Circuitul de apă: căldura, debitul, cămașa cilindrului, trecerile spre chiulasă (s17, s07).
C = compresor(P);
W.P_i = P.imep_plin*P.Vd*P.n_putere/60;                % puterea indicată [W]
W.P_comb = W.P_i/P.eta_i;                               % puterea combustibilului [W]
W.Q = P.f_apa*W.P_comb;                                 % căldura spre apă [W]
W.mdot = W.Q/(P.cp_apa*P.dT_apa);                       % [kg/s]
W.Qv = W.mdot/P.rho_apa;                                % [m3/s]
% Cămașa cilindrului: inel deasupra ferestrelor, între R_apa_int și raza galeriei, întrerupt în față
z_pmi = P.r + P.L + P.h_comp;
z_ev = z_pmi - cinematica(P.thEO_deschis, P);
W.z_apa = [z_ev + P.perete_cil, z_pmi + P.deck - P.apa_sus];
W.R_apa = [P.R_apa_int, C.R_gal];
h = diff(W.z_apa);
W.A_ramura = diff(W.R_apa)*h;                           % secțiunea cămășii între coloane
bosaj = P.prezon_trecere/2 + P.perete_min;
W.A_coloana = (P.prezon_raza - bosaj - P.R_apa_int)*h;  % trecerea pe interiorul unei coloane
% Debitul pe fiecare porțiune a C-ului. Poziția în lungul C-ului: s = 0 în față, crește prin dreapta,
% spate, stânga. Apa intră pe dreapta; fiecare trecere spre chiulasă ia 1/n din debit.
s = @(u) mod(-u, 360);
W.unghi_intrare = P.unghi_intrare_apa;
si = s(W.unghi_intrare); sg = s(P.unghi_gauri_punte);
u_col = [P.prezon_unghi, -P.prezon_unghi, 180 - P.prezon_unghi, P.prezon_unghi - 180];
parte = @(sx) (sx > si)*sum(sg > sx) + (sx < si)*sum(sg < sx);     % trecerile de după sx, dinspre intrare
W.f_ramura = max(sum(sg > si), sum(sg < si))/P.n_gauri_punte;
W.f_coloana = max(arrayfun(parte, s(u_col)))/P.n_gauri_punte;
W.v_ramura = W.f_ramura*W.Qv/W.A_ramura;
W.v_coloana = W.f_coloana*W.Qv/W.A_coloana;
W.A_punte = P.n_gauri_punte*pi/4*P.d_gauri_punte^2;
W.v_punte = W.Qv/W.A_punte;
W.v_racord = W.Qv/(pi/4*P.D_racord_apa^2);
% Pereții: fanta și buzunarul ghilotinei (în plinul din față), cămașa cilindrului, conducta de evacuare
W.perete_fanta = P.apa_fata - P.lama_ev(4);
W.perete_camasa = P.R_apa_int - C.R_cam;
W.perete_evacuare = W.z_apa(1) - z_ev;
end
