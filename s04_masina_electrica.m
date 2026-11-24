% S04_MASINA_ELECTRICA  Mașina de pe arbore: tensiune indusă, cuplu, rotor.
P = parametri();
I = isg_constante(P);
fprintf('\n=== S04 Mașina electrică pe arborele cotit ===\n');
fprintf('Baterie 16 celule LFP: %.1f V minim, %.1f V nominal, %.1f V maxim\n', I.V_min, I.V_nom, I.V_max);
fprintf('Regula: tensiunea indusă la %d rot/min <= %.1f V (tensiunea minimă)\n', P.n_supra, I.V_min);
fprintf('Constanta de cuplu: %.4f N m/A; cuplu la %d A: %.1f N m\n', I.Kt, P.I_pk, I.T_max);
fprintf('Cu regula respinsă (sub %.1f V) cuplul ar fi %.1f N m (+%.0f%%), dar diodele ar conduce\n', ...
        I.V_max, I.T_max_alt, 100*(I.T_max_alt/I.T_max - 1));
fprintf('   necontrolat ori de câte ori bateria e sub tensiunea indusă.\n');
fprintf('Rotor la %d rot/min: viteza periferică %.0f m/s, tensiune %.0f MPa, coeficient de siguranță %.1f\n', ...
        P.n_supra, I.v_periferica, I.sigma/1e6, I.CS);
w = 2*pi*[P.n_ralanti 6000 P.n_putere P.n_max]/60;
fprintf('Puterea mecanică la cuplul maxim: %s kW (limită superioară, fără căderea inductivă)\n', ...
        sprintf('%.1f ', I.T_max*w/1e3));

E_supra = sqrt(3)*I.k*I.w_supra;
verifica(E_supra <= I.V_min + 1e-9, 'E1', 'Tensiunea indusă la supraturare <= tensiunea minimă a bateriei');
verifica(I.CS >= 2, 'E2', sprintf('Rotorul la supraturare: coeficient de siguranță %.1f >= 2', I.CS));
