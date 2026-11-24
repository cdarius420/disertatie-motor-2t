function T = toba(P)
% TOBA  Toba de rezonanță după regulile Jennings (Two-Stroke Tuner's Handbook, 1973, p. 55-73).
% Lungimea acordată se măsoară de la fereastra de evacuare până puțin peste jumătatea conului invers.
a = sqrt(P.gamma_ev*P.R_ev*(P.EGT_ref + 273.15));       % viteza undei [m/s]
T.th_e = 360 - 2*P.thEO_deschis;                        % durata evacuării [grade]
T.L0 = a*T.th_e/(12*P.n_putere);                        % lungimea acordată [m]
J = P.toba_jennings;
T.A_port = P.w_ev*(P.S - cinematica(P.thEO_deschis, P));  % fereastra de evacuare, supapa deschisă
T.D1 = sqrt(4*J(1)*T.A_port/pi);                        % colectorul: aria cu 10-15% peste fereastră
T.L1 = J(2)*T.D1;                                       % colectorul, de la fața pistonului
T.L_port = P.R_corp + P.flansa_ev(1) - P.B/2;           % fereastră -> fața flanșei (prin corpul cilindrului)
T.D2 = J(4)*T.D1;                                       % burta: aria de 6,25 ori colectorul
T.L2 = (T.D2 - T.D1)/(2*tand(J(3)/2));                  % difuzorul
T.D3 = J(6)*T.D1;                                       % țeava de ieșire
T.L4 = (T.D2 - T.D3)/(2*tand(J(5)/2));                  % conul invers
T.L5 = J(7)*T.D3;
T.L3 = T.L0 - T.L1 - T.L2 - J(8)*T.L4;                  % burta: ce rămâne din lungimea acordată
end
