function I = isg_constante(P)
% ISG_CONSTANTE  Dimensionarea electrică și mecanică a mașinii de pe arbore.
% Regula aleasă: la turația de supraturare, tensiunea indusă între faze
% (vârf) nu depășește tensiunea MINIMĂ a bateriei. Atunci diodele invertorului
% nu conduc niciodată, chiar dacă invertorul pierde comanda.
I.V_min = P.n_cel*P.V_cel_min;
I.V_nom = P.n_cel*P.V_cel_nom;
I.V_max = P.n_cel*P.V_cel_max;
I.w_supra = 2*pi*P.n_supra/60;
% Tensiunea indusă de fază (vârf) = k * omega_mecanic, cu k = p * psi_m
I.k  = (I.V_min/sqrt(3))/I.w_supra;    % [V s/rad]
I.Kt = 1.5*I.k;                         % [N m / A vârf]
I.T_max = I.Kt*P.I_pk;
% Regula alternativă, respinsă: tensiunea indusă sub tensiunea MAXIMĂ a bateriei
I.k_alt = (I.V_max/sqrt(3))/I.w_supra;
I.T_max_alt = 1.5*I.k_alt*P.I_pk;
% Rotorul exterior: inelul de oțel plus presiunea centrifugă a magneților
v = I.w_supra*P.r_rot;
I.v_periferica = v;
r_m = P.r_rot - P.t_mag/2;
I.sigma = P.rho_otel*v^2 + P.rho_mag*P.t_mag*r_m*I.w_supra^2*P.r_rot/P.t_pahar;
I.CS = P.Re_otel/I.sigma;
end
