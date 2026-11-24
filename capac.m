function D = capac(P)
% CAPAC  Capacul din dreapta: cotele în lungul arborelui, bosajele statorului, camera de apă și
% temperatura modulului de putere, prinderile pe cadru, scutul (s18, s07).
G = geometrie_carter(P);  M = isg_geometrie(P);  W = racire(P);  C = compresor(P);
% În lungul arborelui (spre dreapta, -Y), de la axa cilindrului
D.y_carter = G.y_ext;                                % fața semicarterului = inelul capacului
y_disc = G.y_ext + P.joc_con;                        % fața discului rotorului
D.y_urechi = y_disc + P.t_disc + P.joc_capete + M.capete + M.L;   % urechile statorului, fața spre capac
D.y_rotor = y_disc + M.L_pahar;                      % capătul deschis al paharului
D.y_bobine = D.y_urechi + M.capete;                  % capetele bobinelor
D.y_arbore = G.y_re + P.capete(2);                   % capătul fusului, cu piulița
D.y_int = D.y_bobine + P.joc_bobine_capac;           % fața interioară a capacului
D.y_ext = D.y_int + P.piele_capac(1) + P.apa_capac(3) + P.piele_capac(2);
D.R_int = M.R_pahar_ext + P.joc_rotor_capac;
D.R_ext = D.R_int + P.t_capac;
D.joc_axial = D.y_int - max(D.y_rotor, D.y_arbore);
D.L_filet = D.y_int - D.y_urechi;                    % filetul M5 din bosajul statorului
D.latime = D.y_ext + P.modul(3);                     % dreapta motorului, cu capacul modulului
% Modulul de putere: invertorul mașinii de pe arbore (generator continuu, alimentează compresorul) și
% al compresorului. Apa curge în lungul camerei, de la racordul din spate la cel din față.
a = P.apa_capac;
D.v_apa = W.Qv/(a(2)*a(3));
Dh = 2*a(2)*a(3)/(a(2) + a(3));
D.Re = P.rho_apa*D.v_apa*Dh/P.mu_apa;
Pr = P.cp_apa*P.mu_apa/P.k_apa;
f = (0.79*log(D.Re) - 1.64)^-2;                      % Gnielinski, 3000 < Re < 5e6
Nu = (f/8)*(D.Re - 1000)*Pr/(1 + 12.7*sqrt(f/8)*(Pr^(2/3) - 1));
D.h = Nu*P.k_apa/Dh;
A_m = P.modul(1)*P.modul(2);
D.R_placa = P.tim(1)/(P.tim(2)*A_m) + P.piele_capac(2)/(P.k_al*A_m) + 1/(D.h*A_m);
T_cont = M.T_max(2)*P.J_cont/P.J_max;
D.P_el = [T_cont*P.n_putere*pi/30, C.P_e];          % [mașina de pe arbore, compresorul] [W]
D.pierderi = (1 - P.eta_inv)*D.P_el;
D.dT_apa = sum(D.pierderi)/(W.mdot*P.cp_apa);
D.Tj = P.T_apa_modul + D.dT_apa + sum(D.pierderi)*D.R_placa + max(D.pierderi)*P.R_jc;
% Prinderile: urechile carterului deasupra băilor, urechea chiulasei deasupra cămășii de apă
d = P.prindere;  u = P.ureche_carter;
D.ureche_jos = u(2) - d(1)/2 - d(2);                 % fața de jos a urechii carterului
D.peste_baie = D.ureche_jos - 0;                     % tavanul exterior al băilor e la z = 0
D.perete_chiulasa = P.ureche_chiulasa(2) - d(1)/2;   % de la gaură la fața chiulasei
% Scutul: sub cel mai de jos punct
D.z_jos = -max(D.R_ext, -G.z_jos + P.nervura_sorb(2));            % capacul sau nervura sorbului de sub băi
D.z_scut = D.z_jos - P.scut(2);                      % fața de sus a scutului
end
