% s20_bilant_electric.m — bilanțul electric și dimensionarea bateriei (Etapa 5, decizia C)
%
% Bateria de 16 celule LFP n-avea capacitate stabilită. O dimensionează puterea, nu energia:
% vârful cerut la asistența de pornire (ISG la cuplul maxim) plus compresorul și consumatorii.
% Celula de referință: A123 / Lithium Werks ANR26650M1B, celulă de putere LFP
% (fișa 26650 Power Cell, 2022: https://lithiumwerks.com/wp-content/uploads/2022/08/26650-Power-Cell-080322.pdf).
%
% Strategia de asistență e o IPOTEZĂ până o decizi: ISG la cuplul maxim cel mult t_asist secunde,
% ca la Honda PCX Hybrid (asistența durează cel mult 4 s: https://global.honda/en/tech/Hybrid_System_PCX_HYBRID/).

clear; P = parametri; I = isg_constante(P); C = compresor(P);

% --- Celula [catalog, fișa de mai sus] ---
cel.C_Ah   = 2.5;      % capacitatea nominală [Ah]
cel.V_nom  = 3.3;      % [V]
cel.I_cont = 52;       % descărcare continuă maximă [A]
cel.I_puls = 120;      % descărcare de vârf, 10 s [A]
cel.I_inc  = 10;       % încărcare continuă maximă [A]
cel.I_inc_puls = 26;   % încărcare de vârf, 10 s [A] (limitează frânarea regenerativă)
cel.m      = 0.076;    % [kg]
cel.D = 25.96e-3; cel.L = 65.15e-3;   % [m]
t_puls_max = 10;       % durata pentru care e dat curentul de vârf [s]

% --- Ipoteze (DE CONFIRMAT) ---
eta_isg = 0.90;        % ISG + invertor, motor sau generator [-]                   [ESTIMARE]
t_asist = 4;           % asistența la cuplul maxim [s] (reperul PCX Hybrid)         [ESTIMARE]
P_aux   = [50 60 40];  % pompa de apă 12 V (clasa CWA50), ventilatorul radiatorului, ECU + servo + lumini LED [W] [ESTIMARE]
DoD     = 0.8;         % adâncimea de descărcare folosită [-]                       [ESTIMARE]
joc_pachet = 15e-3;    % pe fiecare latură: BMS, bare, carcasă [m]                  [ESTIMARE]

% --- Cererea ---
n_asist = P.n_putere;                                      % asistența cea mai grea: la turația de putere
P_isg_mec = I.T_max*n_asist*2*pi/60;                       % [W] limita de sus, fără căderea inductivă (s04)
P_roots = C.P_e;                                           % [W] electric, din compresor.m
P_varf  = P_isg_mec/eta_isg + P_roots + sum(P_aux);        % la bornele bateriei [W]
P_cont  = P_roots + sum(P_aux);                            % dacă ISG nu generează [W]
I_varf  = P_varf/I.V_min;  I_cont = P_cont/I.V_min;        % la tensiunea minimă: curentul cel mai mare [A]

% --- Pachetul: 16 în serie, np în paralel ---
np = ceil(max(I_varf/cel.I_puls, I_cont/cel.I_cont));
E_Wh = P.n_cel*np*cel.C_Ah*cel.V_nom;                      % [Wh]
E_asist_Wh = P_varf*t_asist/3600;
m_cel = P.n_cel*np*cel.m;
% așezarea celulelor în picioare, într-un dreptunghi cât mai pătrat
N = P.n_cel*np;  nx = ceil(sqrt(N));  ny = ceil(N/nx);
cutie = [nx*cel.D, ny*cel.D, cel.L] + 2*joc_pachet;        % [m]
P_regen = np*cel.I_inc_puls*I.V_max;                       % frânarea regenerativă de vârf, 10 s [W]
P_gen_cont = np*cel.I_inc*I.V_max;                         % încărcarea continuă admisă [W]

fprintf('Cererea la bornele bateriei: ISG %.1f kW mecanic / %.2f + Roots %.2f kW + consumatori %.0f W = %.1f kW\n', ...
        P_isg_mec/1e3, eta_isg, P_roots/1e3, sum(P_aux), P_varf/1e3);
fprintf('Curentul la %.1f V: %.0f A de vârf, %.0f A continuu (fără generare)\n', I.V_min, I_varf, I_cont);
fprintf('Pachet 16s%dp din ANR26650M1B: %.0f Wh, %.2f kg celule, cutie %.0f x %.0f x %.0f mm (%.1f L)\n', ...
        np, E_Wh, m_cel, cutie*1e3, prod(cutie)*1e3);
fprintf('O asistență de %.0f s ia %.1f Wh (%.1f%% din pachet); cu DoD %.0f%%: %.0f asistențe pe încărcare\n', ...
        t_asist, E_asist_Wh, 100*E_asist_Wh/E_Wh, 100*DoD, floor(DoD*E_Wh/E_asist_Wh));
fprintf('Frânarea regenerativă admisă de celule: %.1f kW timp de 10 s, %.1f kW continuu\n', P_regen/1e3, P_gen_cont/1e3);

verifica(I_varf <= np*cel.I_puls, 'B1', sprintf('Vârful de %.0f A <= %d x %d A (descărcarea de 10 s a celulei)', I_varf, np, cel.I_puls));
verifica(I_cont <= np*cel.I_cont, 'B2', sprintf('Continuu %.0f A <= %d x %d A', I_cont, np, cel.I_cont));
verifica(t_asist <= t_puls_max, 'B3', sprintf('Asistența de %.0f s <= %.0f s, durata vârfului din fișă', t_asist, t_puls_max));
