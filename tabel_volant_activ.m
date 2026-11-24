function Tff = tabel_volant_activ(Tg, Tmean, Tmax)
% TABEL_VOLANT_ACTIV  Cuplul electric pe unghi pentru volantul activ.
% Opune fluctuația cuplului de gaze, tăiat la +-Tmax, cu medie zero pe
% ciclu: mașina doar mută energie în interiorul rotației, nu adaugă.
Tff = max(-Tmax, min(Tmax, -(Tg - Tmean)));
for k = 1:20                       % corectează media fără să iasă din limită
    Tff = max(-Tmax, min(Tmax, Tff - mean(Tff)));
end
end
