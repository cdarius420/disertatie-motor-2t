% S19_VEHICUL  Viteza maximă din puterea netă de la arbore (decizia D1: L3e-A1, 11 kW).
% Puterea netă = puterea efectivă minus puterea mecanică pe care ISG o ia de pe arbore
% ca să alimenteze compresorul. Rezistența la înaintare: aer + rulare, prin randamentul transmisiei.
P = parametri(); C = compresor(P);
fprintf('\n=== S19 Vehiculul ===\n');
P_comp = C.P_e/P.eta_em_c;                 % de pe arbore, prin ISG [W]
P_net  = P.P_ef - P_comp;
m = sum(P.m_veh); g = 9.81;
P_cer = @(v, CdA) (0.5*P.rho_aer*CdA*v.^3 + P.Crr*m*g*v)/P.eta_tr;
v_max = @(CdA) fzero(@(v) P_cer(v, CdA) - P_net, [5 80])*3.6;
fprintf('Puterea la arbore: %.1f kW efectiv - %.2f kW compresorul = %.1f kW net\n', P.P_ef/1e3, P_comp/1e3, P_net/1e3);
fprintf('Masa %d kg (motocicleta %d + pilot %d), Crr %.3f, randamentul transmisiei %.2f\n', m, P.m_veh(1), P.m_veh(2), P.Crr, P.eta_tr);
for CdA = [0.45 0.55 0.65 0.75]
    fprintf('   CdA %.2f m2: viteza maximă %3.0f km/h; la %d km/h trebuie %.1f kW la arbore\n', ...
            CdA, v_max(CdA), P.v_max, P_cer(P.v_max/3.6, CdA)/1e3);
end
v0 = v_max(P.CdA);
verifica(v0 >= P.v_max, 'G1', sprintf('Viteza maximă %.1f km/h >= ținta de %d km/h (CdA %.2f m2, %.1f kW net)', ...
         v0, P.v_max, P.CdA, P_net/1e3));
verifica(P.P_ef <= P.P_A1(1) && P.P_ef/P.m_veh(1) <= P.P_A1(2), 'G2', sprintf( ...
         'L3e-A1: %.1f kW <= %.0f kW; %.3f kW/kg <= %.1f kW/kg (masa în ordine de mers %d kg)', ...
         P.P_ef/1e3, P.P_A1(1)/1e3, P.P_ef/P.m_veh(1)/1e3, P.P_A1(2)/1e3, P.m_veh(1)));
fprintf('   Strategia: controlerul ține motorul + ISG <= %.0f kW; asistența ISG <= %.1f kW (P.P_asist_max). Regula de măsurare la hibrizi (Reg. 134/2014): de citit.\n', P.P_A1(1)/1e3, P.P_asist_max/1e3);
