% s22_tunel_termic.m — bilanțul termic al tunelului de sub șa (Etapa 5, omagiul EZ-9)
%
% Întrebarea: dacă burta, conul invers și stingerul tobei stau ascunse într-un tunel
% de plastic sub șa (cum își ascundea EZ-9 toba-cutie), câtă căldură intră în tunel
% și cât aer trebuie să treacă prin el ca peretele de plastic să rămână sub limită?
%
% Model (o margine de sus, simplă, nu o simulare):
%   - peretele tobei la temperatura Tw, impusă pe scenarii (NU e măsurată: ipoteză);
%   - căldura iese prin convecție forțată (Churchill–Bernstein, cilindru în curent
%     transversal, proprietățile aerului la temperatura de film) și prin radiație
%     spre un mediu la temperatura aerului din tunel (marginea de sus: scutul nu
%     se încălzește);
%   - toată căldura ajunge, la regim staționar, în aerul tunelului;
%   - debitul de aer cerut = Q / (cp * dT_admis), dT_admis = T_plastic_max - T_intrare - marja.
% Ce lipsește intenționat: rezistența dinspre gaze (ar coborî Tw), amortizorul final
% (nedimensionat), conducția prin suporturi. Verificarea reală: termocuple pe banc.

clear; P = parametri; Tb = toba(P); W = racire(P);

% --- Geometria din toba.m: părțile care ar sta în tunel ---
A_burta   = pi*Tb.D2*Tb.L3;                                        % cilindru
s_con     = hypot(Tb.L4, (Tb.D2 - Tb.D3)/2);  A_con = pi*(Tb.D2 + Tb.D3)/2*s_con;   % trunchi de con
A_stinger = pi*Tb.D3*Tb.L5;
A_tunel   = A_burta + A_con + A_stinger;                           % [m2]
D_echiv   = Tb.D2;                                                 % diametrul pentru convecție (burta)

% --- Ipoteze (toate DE CONFIRMAT) ---
Tw_sc   = [300 400 500 600];   % peretele tobei [grade C]: ipoteze, până la măsurare
v_sc    = [2 4 8];             % viteza aerului în tunel [m/s]
eps_w   = 0.80;                % emisivitatea oțelului oxidat [-]                      [ESTIMARE]
T_pp    = 80;                  % plasticul (PP): temperatura de serviciu scurtă din fișă [grade C]
marja   = 10;                  % marja față de limita plasticului [K]
T_amb   = P.aer_radiator(3);                         % aerul exterior de proiectare [grade C]
T_rad   = P.aer_radiator(3) + P.aer_radiator(2);     % aerul ieșit din radiator [grade C]
cp_aer  = 1005; sigma = 5.670e-8;

% --- Aerul disponibil de la radiator (din racire.m) ---
mdot_rad = W.Q/(cp_aer*P.aer_radiator(2));           % [kg/s]

fprintf('Tunel: burta %.3f + con %.3f + stinger %.3f = %.3f m2 de perete\n', A_burta, A_con, A_stinger, A_tunel);
fprintf('Aerul radiatorului: %.0f grade C la ieșire, %.3f kg/s (din racire.m, căldura spre apă %.0f W)\n', T_rad, mdot_rad, W.Q);

for sursa = ["proaspat" "radiator"]
    if sursa == "proaspat", T_in = T_amb; else, T_in = T_rad; end
    dT_admis = T_pp - T_in - marja;
    fprintf('\nAer %s: intră la %.0f grade C, poate urca %.0f K\n', sursa, T_in, dT_admis);
    fprintf('  Tw [C] | v [m/s] | h_conv [W/m2K] | Q [W]  | debit cerut [kg/s] | cât din aerul radiatorului\n');
    for Tw = Tw_sc
        for v = v_sc
            Ta = T_in + max(dT_admis, 1)/2;                         % aerul mediu în tunel
            Tf = (Tw + Ta)/2 + 273.15;                              % temperatura de film [K]
            [k, nu, Pr] = aer(Tf);
            Re = v*D_echiv/nu;
            Nu = 0.3 + 0.62*Re^0.5*Pr^(1/3)/(1 + (0.4/Pr)^(2/3))^0.25*(1 + (Re/282000)^(5/8))^(4/5);
            h  = Nu*k/D_echiv;
            Q  = A_tunel*(h*(Tw - Ta) + eps_w*sigma*((Tw + 273.15)^4 - (Ta + 273.15)^4));
            if dT_admis > 0, mdot = Q/(cp_aer*dT_admis); else, mdot = Inf; end
            fprintf('  %6.0f | %7.0f | %14.1f | %6.0f | %18.3f | %6.1f x\n', Tw, v, h, Q, mdot, mdot/mdot_rad);
        end
    end
end

% Verificările (criteriile de acceptanță ale tunelului)
fprintf('\nT1 aerul radiatorului lasă cel puțin 20 K până la limita plasticului: %d\n', T_pp - T_rad - marja >= 20);
fprintf('T2 tunelul cere mai puțin aer decât trece prin radiator (Tw = 400 C, 4 m/s, aer proaspăt): ');
Ta = T_amb + (T_pp - T_amb - marja)/2; Tf = (400 + Ta)/2 + 273.15; [k, nu, Pr] = aer(Tf);
Re = 4*D_echiv/nu; Nu = 0.3 + 0.62*Re^0.5*Pr^(1/3)/(1 + (0.4/Pr)^(2/3))^0.25*(1 + (Re/282000)^(5/8))^(4/5);
Q = A_tunel*(Nu*k/D_echiv*(400 - Ta) + eps_w*sigma*((400 + 273.15)^4 - (Ta + 273.15)^4));
fprintf('%d (cere %.3f kg/s, radiatorul are %.3f kg/s)\n', Q/(cp_aer*(T_pp - T_amb - marja)) < mdot_rad, Q/(cp_aer*(T_pp - T_amb - marja)), mdot_rad);

function [k, nu, Pr] = aer(T)
% proprietățile aerului la presiune atmosferică, interpolate între 300 și 800 K (tabele standard de transfer termic)
Tt  = [300 400 500 600 700 800];
kt  = [26.3 33.8 40.7 46.9 52.4 57.3]*1e-3;          % [W/mK]
nut = [15.89 26.41 38.79 52.69 68.10 84.93]*1e-6;    % [m2/s]
Prt = [0.707 0.690 0.684 0.685 0.695 0.709];
T = min(max(T, 300), 800);
k = interp1(Tt, kt, T); nu = interp1(Tt, nut, T); Pr = interp1(Tt, Prt, T);
end
