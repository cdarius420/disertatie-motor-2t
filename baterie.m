function B = baterie(P)
% BATERIE  Pachetul de P.n_cel celule LFP în serie și P.n_par în paralel (s20, s23).
% Cererea de vârf: ISG la cuplul maxim la turația de putere, prin randament, plus Roots și consumatorii,
% la tensiunea minimă a bateriei (curentul cel mai mare).
I = isg_constante(P); C = compresor(P);
B.P_isg_mec = I.T_max*P.n_putere*2*pi/60;                  % [W] limita de sus, fără căderea inductivă (s04)
B.P_roots = C.P_e;                                         % [W] electric, din compresor.m
B.P_varf = B.P_isg_mec/P.eta_isg + B.P_roots + sum(P.P_aux);   % la bornele bateriei [W]
B.P_cont = B.P_roots + sum(P.P_aux);                       % dacă ISG nu generează [W]
B.V_min = I.V_min;
B.I_varf = B.P_varf/I.V_min;  B.I_cont = B.P_cont/I.V_min;  % [A]
N = P.n_cel*P.n_par;
B.E_Wh = N*P.cel_C_Ah*P.V_cel_nom;
B.E_asist_Wh = B.P_varf*P.t_asist/3600;
B.m_cel = N*P.cel_m;
nx = ceil(sqrt(N));  ny = ceil(N/nx);                      % celulele în picioare, într-un dreptunghi cât mai pătrat
B.cutie = [nx*P.cel_D, ny*P.cel_D, P.cel_L] + 2*P.joc_pachet;   % [m]
B.P_regen = P.n_par*P.cel_I_inc_puls*I.V_max;              % frânarea regenerativă de vârf, P.cel_t_puls secunde [W]
B.P_gen_cont = P.n_par*P.cel_I_inc*I.V_max;                % încărcarea continuă admisă [W]
% tensiunea celulei la vârf, la capătul descărcării folosite (palierul LFP ~ V_cel_nom) [V]
B.V_cel_varf = P.V_cel_nom - B.I_varf/P.n_par*P.cel_R;
B.n_par_tensiune = ceil(B.I_varf*P.cel_R/(P.V_cel_nom - P.V_cel_min));   % paralelul care ține V_cel_min la vârf
end
