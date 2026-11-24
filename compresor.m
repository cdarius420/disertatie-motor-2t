function C = compresor(P)
% COMPRESOR  Compresorul electric și admisia (s16, s07).
% Aerul cerut vine din PMI la sarcină plină; presiunea din galerie, din aria ferestrelor de
% transfer cât sunt deschise (curgere compresibilă prin orificiu); roata, din viteza specifică.
R = 287; cp = 1005; g = 1.4;
rho0 = P.p0/(R*P.T0);
% 1. Aerul: cât trebuie reținut în cilindru pentru PMI, cât trebuie livrat
C.m_ret = P.imep_plin*P.Vd/P.eta_i/P.LHV*P.AFR;       % aerul reținut pe ciclu [kg]
C.CE = C.m_ret/(rho0*P.Vd);                             % randamentul de umplere
C.DR = C.CE/P.TE;                                       % raportul de livrare
C.m_liv = C.DR*rho0*P.Vd;
C.mdot = C.m_liv*P.n_putere/60;                         % [kg/s]
% 2. Presiunea din galerie: tot aerul trece prin ferestrele de transfer cât sunt deschise
th = linspace(P.thTO, 360 - P.thTO, 2001);
xTO = cinematica(P.thTO, P);
A = P.w_tr*max(0, cinematica(th, P) - xTO);
C.A_tr_max = max(A);
om_m = P.n_putere*pi/30;
p_in = P.p0*(1 - P.dp_filtru);
T_ies = @(ps) P.T0*(1 + ((ps/p_in)^((g - 1)/g) - 1)/P.eta_c);
masa = @(ps) trapz(th*pi/180, P.Cd_tr*A*ps/sqrt(R*T_ies(ps))*psi(P.p_ev/ps, g))/om_m;
C.p_s = fzero(@(ps) masa(ps) - C.m_liv, [1.0001 3]*P.p0);
C.PR = C.p_s/p_in;
C.T_s = T_ies(C.p_s);
C.dT_vap = P.h_vap/P.AFR/cp;                            % răcirea prin vaporizarea benzinei (TPI)
C.dh_is = cp*P.T0*(C.PR^((g - 1)/g) - 1);
C.P_c = C.mdot*C.dh_is/P.eta_c;                         % puterea pe roată [W]
C.P_e = C.P_c/P.eta_em_c;                               % din baterie [W]
% 3. Roata
C.om = P.n_comp*pi/30;
C.Q1 = C.mdot/(p_in/(R*P.T0));
C.Ns = C.om*sqrt(C.Q1)/C.dh_is^0.75;                    % viteza specifică
C.u2 = sqrt(C.dh_is/P.eta_c/P.psi_c);
C.D2 = 2*C.u2/C.om;
C.D1 = P.roata(1)*C.D2;  C.D_butuc = P.roata(2)*C.D1;
C.b2 = P.roata(3)*C.D2;  C.L_roata = P.roata(4)*C.D2;
C.c1 = C.Q1/(pi/4*(C.D1^2 - C.D_butuc^2));              % viteza axială la intrare
C.M1 = sqrt(C.c1^2 + (C.om*C.D1/2)^2)/sqrt(g*R*P.T0);   % Mach relativ la vârful paletelor, la intrare
C.DN = P.d_ax_c*1e3*P.n_comp;
% Colectorul (inel de secțiune constantă, cât canalul spre galerie), turnat cu cilindrul în spatele lui:
% axa compresorului orizontală, în lungul motocicletei, la y = 0; inelul stă în plan vertical, cu
% ieșirea în punctul de jos, la înălțimea galeriei, și intră drept în galerie printre prezoane
C.R_sp = 1.15*C.D2/2 + P.D_admisie/2;                   % axa secțiunii inelului
C.R_sp_ext = C.R_sp + P.D_admisie/2 + P.t_carcasa_c;    % = lățimea pe fiecare parte
C.x_c = -(P.R_corp + P.joc_comp + P.D_admisie/2 + P.t_carcasa_c);   % planul inelului, la joc de cilindru și chiulasă
C.R_aer = sqrt((P.D_motor_c(1)/2)^2 + 1.2*((C.D1/2)^2 - (C.D_butuc/2)^2));   % intrarea pe lângă motor
C.lungime_spate = -C.x_c + P.D_admisie/2 + P.t_carcasa_c + 5e-3 + P.D_motor_c(2) - P.R_corp;   % cât iese în spatele cilindrului
% 4. Motorul compresorului: rotorul din forfecarea admisă, inerția, pornirea
C.T_n = C.P_c/C.om;
C.r_mot = (C.T_n/(2*pi*P.sigma_c*P.Lr_c))^(1/3);
C.L_mot = P.Lr_c*C.r_mot;
C.J = 0.5*P.rho_mag*pi*C.r_mot^4*C.L_mot + ...                                     % rotorul cu magnet
      0.5*(P.k_plin_roata*P.rho_al*pi*(C.D2/2)^2*C.L_roata/2)*(C.D2/2)^2;          % roata: disc plin pe jumătate
k = P.k_supra_c;                                        % J dw/dt = k T_n - T_n (w/w_n)^2, de la 0 la w_n
C.t_pornire = C.J*C.om^2/C.P_c/(2*sqrt(k))*log((sqrt(k) + 1)/(sqrt(k) - 1));
% 5. Corpul cilindrului: galeria și canalele
z_pmi = P.r + P.L + P.h_comp;
C.z_fer_jos = z_pmi - P.S;                              % ferestrele încep la coroana de la PME
C.z_TO = z_pmi - xTO;
C.R_cam = P.B/2 + P.t_perete;                           % cămașa
C.R_gal = P.R_corp - P.perete_cil;
C.z_g = [P.baza_cil + P.galerie_jos, C.z_fer_jos - P.perete_cil];
C.z_c = mean(C.z_g) + C.R_sp;                           % axa compresorului: ieșirea inelului la mijlocul galeriei
C.L_iesire = -C.x_c - (C.R_gal - 2e-3);                 % canalul turnat, din inel în galerie
C.r_bosaj = P.prezon_trecere/2 + P.perete_min;
C.V_gal = (pi*(C.R_gal^2 - C.R_cam^2) - 4*pi*C.r_bosaj^2)*diff(C.z_g);
C.R_canal = C.R_cam + P.canal_adancime;
C.A_canal = P.tr_latime*P.canal_adancime;               % A, B, C
C.A_fereastra = P.tr_latime*(P.S - xTO);
rho_s = C.p_s/(R*C.T_s);
C.v_admisie = C.mdot/rho_s/(pi/4*P.D_admisie^2);
end

function y = psi(pr, g)
pr = max(pr, (2/(g + 1))^(g/(g - 1)));                  % blocat la viteza sunetului
y = sqrt(2*g/(g - 1)*(pr.^(2/g) - pr.^((g + 1)/g)));
end
