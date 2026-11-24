% S21_SENSIBILITATE  Care estimări mută rezultatele cheie: fiecare parametru [ESTIMARE] variat cu ±20 %.
% Limită: se variază valoarea din P; cotele calculate în parametri.m din ea nu se recalculează.
P0 = parametri();
fprintf('\n=== S21 Sensibilitatea la estimări ===\n');
tok = regexp(fileread('parametri.m'), '(?m)^P\.(\w+)\s*=[^\n]*\[ESTIMARE\]', 'tokens');
nume = unique(cellfun(@(c) c{1}, tok, 'UniformOutput', false));
rez_nume = {'viteza maximă', 'puterea compresorului', 'aerul refulat', 'căldura în apă', 'uleiul', 'modulul ISG'};
r0 = rezultate(P0);
S = zeros(numel(nume), numel(r0));
for k = 1:numel(nume)
    for f = [0.8 1.2]
        P = P0; P.(nume{k}) = P0.(nume{k})*f;
        try
            S(k, :) = max(S(k, :), abs(rezultate(P) - r0)./abs(r0));
        catch
        end
    end
end
for j = 1:numel(r0)
    [s, i] = sort(S(:, j), 'descend');
    fprintf('   %-22s %8.1f: %s (%.0f%%), %s (%.0f%%), %s (%.0f%%)\n', rez_nume{j}, r0(j), ...
            nume{i(1)}, 100*s(1), nume{i(2)}, 100*s(2), nume{i(3)}, 100*s(3));
end
fprintf('   (%d parametri [ESTIMARE] variați cu ±20%%; în paranteză, schimbarea cea mai mare a rezultatului)\n', numel(nume));

function r = rezultate(P)
C = compresor(P); W = racire(P); U = ungere(P); D = capac(P);
P_net = P.P_ef - C.P_e/P.eta_em_c; m = sum(P.m_veh);
v = fzero(@(v) (0.5*P.rho_aer*P.CdA*v^3 + P.Crr*m*9.81*v)/P.eta_tr - P_net, [5 80])*3.6;
r = [v, C.P_e, C.T_s - 273.15, W.Q, U.T_ulei, max(D.Tj)];
end
