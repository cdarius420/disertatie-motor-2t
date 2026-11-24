function G = isg_geometrie(P)
% ISG_GEOMETRIE  Dimensionarea mașinii electrice de pe arbore (rotor exterior, bobine pe dinți).
% Constanta de tensiune k vine din regula din isg_constante: la supraturare, tensiunea indusă
% nu trece de tensiunea minimă a bateriei. Regula se aplică cu magneții reci (20 °C), când
% tensiunea e cea mai mare; cuplul se dă cu magneții calzi (P.T_mag), când e cel mai mic.
% Fluxul fundamental pe pol: Phi = B1*D_g*L/p, deci k = N_s*k_w*B1*D_g*L.
% Spirele pe bobină: cel mai mare număr pentru care crestătura încape la J_max (pachet scurt).
I = isg_constante(P);
m = 3; Q = P.Q_isg; p = P.p_isg;
G.R_pahar_ext = P.r_rot + P.t_pahar;
G.R_mag_int = P.r_rot - P.t_mag;
G.R_s = G.R_mag_int - P.g_isg;                       % exteriorul statorului
G.D_g = 2*G.R_s + P.g_isg;                           % diametrul la mijlocul întrefierului
Br = @(T) P.Br20*(1 + P.alfa_Br*(T - 20));
Bg = @(T) Br(T)*P.t_mag/(P.t_mag + P.mu_rec*P.g_isg*P.k_Carter);
B1 = @(T) 4/pi*Bg(T)*sin(P.alfa_mag*pi/2);
G.Bg = [Bg(20) Bg(P.T_mag)];  G.B1 = [B1(20) B1(P.T_mag)];
[G.kw, G.faze] = infasurare(Q, p);

% Dinții (laturi paralele) și crestătura
tau_s = 2*pi*G.R_s/Q;
G.b_t = G.Bg(1)*tau_s/P.B_max(1);                    % lățimea dintelui: inducția admisă
G.R_varf = G.R_s - P.h_varf;                          % sub vârful dintelui
r0 = Q*G.b_t/(2*pi);                                  % unde crestătura s-ar închide
arie = @(R) pi/Q*(G.R_varf^2 - R.^2) - G.b_t*(G.R_varf - R);
I_rms = P.I_pk/sqrt(2);
G.N_c = 0;
for Nc = 6:-1:1
    A_nec = 2*Nc*(I_rms/P.J_max)/P.k_umplere;
    if A_nec <= 0.9*arie(r0)
        G.N_c = Nc; G.A_cresta = A_nec; break
    end
end
G.N_s = Q/m*G.N_c;                                    % spire în serie pe fază
G.L = floor(I.k/(G.N_s*G.kw*G.B1(1)*G.D_g)/P.tola)*P.tola;   % pachetul, multiplu de tole
G.R_fund = fzero(@(R) arie(R) - G.A_cresta, [r0 G.R_varf]);
% Jugul statorului și paharul rotorului: jumătate din fluxul unui pol
tau_p = pi*G.D_g/(2*p);
G.Phi_p = G.Bg(1)*P.alfa_mag*tau_p*G.L;
G.h_jug = G.Phi_p/(2*P.B_max(2)*G.L);
G.R_si = G.R_fund - G.h_jug;
G.t_pahar_nec = G.Phi_p/(2*P.B_max(3)*G.L);
% Constantele și cuplul
G.k_e = G.N_s*G.kw*G.B1*G.D_g*G.L;                    % [V s/rad], la 20 °C și cald
G.T_max = 1.5*G.k_e*P.I_pk;
G.J_cresta = 2*G.N_c*I_rms/(G.A_cresta*P.k_umplere);
G.f_supra = p*P.n_supra/60;
G.forfecare = G.T_max(2)/(2*pi*(G.D_g/2)^2*G.L);
% Demagnetizarea: câmpul reacției indusului, opus magnetului, la curentul de vârf
F_a = 1.5*4/pi*G.N_s*G.kw/(2*p)*P.I_pk;
G.H_a = F_a/(P.t_mag + P.mu_rec*P.g_isg*P.k_Carter);
G.Hcj = P.Hcj20*(1 + P.alfa_Hcj*(P.T_mag - 20));
% Lungimea axială: capetele bobinelor ies cu jumătate din lățimea crestăturii
G.capete = (2*pi*G.R_varf/Q - G.b_t)/2;
G.L_pahar = P.t_disc + P.joc_capete + G.capete + G.L + 1e-3;
G.L_gros = G.L + 2e-3;                                 % paharul gros: în dreptul magneților, +1 mm la capete
% Masa și inerția rotorului (pahar, disc, butuc pe con, magneți, șaibă, piuliță)
ro = P.rho_otel; inel = @(R1, R2, L) [pi*(R2^2 - R1^2)*L, pi/2*(R2^4 - R1^4)*L];
r_con = (P.con(1) - P.con(2)/(2*P.conicitate))/2;     % raza medie a conului
parti = [inel(P.r_rot, G.R_pahar_ext, G.L_gros)*ro;
         inel(P.r_rot, P.r_rot + P.t_pahar_subtire, G.L_pahar - G.L_gros)*ro;
         inel(P.R_butuc, P.r_rot, P.t_disc)*ro;
         inel(r_con, P.R_butuc, P.con(2))*ro;
         inel(G.R_mag_int, P.r_rot, G.L)*P.rho_mag*P.alfa_mag;
         inel(P.saiba_rotor(1)/2, P.saiba_rotor(2)/2, P.saiba_rotor(3))*ro];
Rh = P.piulita(1)/sqrt(3);                            % raza de colț a hexagonului
A_hex = 3*sqrt(3)/2*Rh^2 - pi*(P.d_filet/2)^2;
J_hex = (5*sqrt(3)/8*Rh^4 - pi/2*(P.d_filet/2)^4)*P.piulita(2)*ro;
parti = [parti; A_hex*P.piulita(2)*ro, J_hex];
G.m_rotor = sum(parti(:,1));  G.J_rotor = sum(parti(:,2));
G.m_magneti = parti(5,1);
end

function [kw, faze] = infasurare(Q, p)
% Steaua crestăturilor pentru bobine pe dinți: bobina k are faza tensiunii k*alfa (alfa =
% 2*pi*p/Q electric). Benzile de 60° în jurul axelor: A+ C- B+ A- C+ B-.
alfa = 360*p/Q;
fi = mod((0:Q-1)*alfa, 360);
banda = floor(mod(fi + 30 - 1e-9, 360)/60);           % 0..5
nume = {'A+', 'C-', 'B+', 'A-', 'C+', 'B-'};
faze = nume(banda + 1);
semn = 1 - 2*(banda >= 3);
A = (banda == 0 | banda == 3);
kp = abs(sin(pi*p/Q));                                % pasul bobinei: un dinte
kd = abs(sum(semn(A).*exp(1i*fi(A)*pi/180)))/sum(A);
kw = kp*kd;
end
