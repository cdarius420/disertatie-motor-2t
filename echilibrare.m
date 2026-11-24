function E = echilibrare(P)
% ECHILIBRARE  Contragreutatea brațelor pentru factorul de echilibrare P.BF.
% Masele pieselor mobile vin din Fusion: fusion/volume_fusion.csv are volumul și
% centrul de masă (la PMI, de la axa arborelui) ale fiecărei piese; masa = volum x
% densitate din parametri.m. Fișierul îl scrie scriptul construieste la fiecare rulare.
%
% Brațul: sector de contragreutate de rază R pe ±alfa în jurul direcției opuse
% manetonului, bosajul manetonului (raza P.R_bosaj) și două tangente între ele.
% Condiția de echilibru (momente statice față de axa arborelui, maneton în sus):
%   U_brate(alfa) + m_rot*r + BF*m_rec*r = 0
% Alfa este cel mai mic unghi care o îndeplinește: braț mai ușor, inerție mai mică.
% Biela se împarte în două mase după centrul ei de masă (d de la axa capului):
% m_rec = m*d/L la bolț, m_rot = m*(L-d)/L la maneton.
cale = fullfile('fusion', 'volume_fusion.csv');
if ~exist(cale, 'file')
    error('Lipsește %s: rulează construieste în Fusion, care scrie volumele pieselor.', cale);
end
fid = fopen(cale, 'r');
fgetl(fid);
C = textscan(fid, '%s %f %f %f', 'Delimiter', ',');
fclose(fid);
rol = C{1}; vol = C{2}*1e-6; zc = C{3}*1e-3;
masa = @(n) vol(strcmp(rol, n))*(strcmp(n, 'piston')*P.rho_piston + ~strcmp(n, 'piston')*P.rho_otel);
cota = @(n) zc(strcmp(rol, n));

E.m = struct();
for n = {'piston', 'bolt', 'sigurante', 'rulment_picior', 'biela', 'rulment_cap', 'saibe', 'maneton'}
    E.m.(n{1}) = masa(n{1});
end
E.d_biela = cota('biela') - P.r;                       % centrul de masă al bielei, de la axa capului
E.m_biela_rec = E.m.biela*E.d_biela/P.L;
E.m_biela_rot = E.m.biela - E.m_biela_rec;
E.m_seg = P.seg_rho*pi*((P.B - P.seg_t)*P.seg_t*sum(P.seg_h_ales) + (P.B - P.rac_t)*P.rac_t*P.rac_h);
E.m_rec = E.m.piston + E.m.bolt + E.m.sigurante + E.m.rulment_picior + E.m_seg + E.m_biela_rec;
E.m_rot = E.m.maneton + E.m.saibe + E.m.rulment_cap + E.m_biela_rot;

% Brațele
gol = P.b_picior + 2*P.saiba + P.joc_lat_cap;
E.t = (P.latime_amb - gol)/2;
E.R = P.h_comp + P.L - P.r - (P.S + P.joc_raclor + P.zona_raclor) - P.joc_cg;   % raza max. (s10)
a_gaura = pi/4*P.d_maneton^2;
U_gauri = -2*P.rho_otel*E.t*a_gaura*P.r;               % alezajele manetonului din brațe
U_cerut = E.m_rot*P.r + P.BF*E.m_rec*P.r;
U_brate = @(al) 2*P.rho_otel*E.t*arie_moment(contur(P, E.R, al));
f = @(al) U_brate(al) + U_gauri + U_cerut;

% Momentul static al conturului crește în modul până la un unghi, apoi scade
% (laturile sectorului ajung deasupra axei). Rădăcina utilă e pe ramura crescătoare.
al_min = 25*pi/180;
al_varf = fminbnd(@(al) arie_moment(contur(P, E.R, al)), al_min, 120*pi/180);
E.BF_max = (-(U_brate(al_varf) + U_gauri) - E.m_rot*P.r)/(E.m_rec*P.r);
E.atins = f(al_min) > 0 && f(al_varf) <= 0;
if E.atins
    E.alfa = fzero(f, [al_min al_varf]);
else
    E.alfa = al_varf;                                   % cel mai mult cât se poate (E1 pică)
end
E.contur = contur(P, E.R, E.alfa);
x = E.contur(:,1); z = E.contur(:,2);
E.BF = (-(U_brate(E.alfa) + U_gauri) - E.m_rot*P.r)/(E.m_rec*P.r);
E.perete_fus = min(hypot(x, z)) - P.d_fus/2;            % brațul rămas în jurul fusului

% Inerția arborelui față de axa lui: brațe, fusuri, maneton, șaibe; capul bielei și
% rulmentul lui ca mase concentrate pe raza manivelei
[~, ~, Jp] = arie_moment(E.contur);
J_brate = 2*P.rho_otel*E.t*(Jp - a_gaura*(P.d_maneton^2/8 + P.r^2));
L_fus = 2*(P.joc_rulment + P.rul(3)) + sum(P.capete);
m_fus = P.rho_otel*pi/4*P.d_fus^2*L_fus;
E.J = J_brate + m_fus*P.d_fus^2/8 + E.m.maneton*(P.d_maneton^2/8 + P.r^2) + ...
      E.m.saibe*((P.D_saiba^2 + P.d_maneton^2)/8 + P.r^2) + (E.m.rulment_cap + E.m_biela_rot)*P.r^2;
E.m_arbore = 2*P.rho_otel*E.t*(polyarea_s(E.contur) - a_gaura) + m_fus + E.m.maneton + E.m.saibe;
end

function xz = contur(P, R, al)
% Conturul brațului în planul XZ (maneton în sus), parcurs în sens trigonometric: [x z].
N = 4000;
th = linspace(-pi/2 - al, -pi/2 + al, N)';
x = R*cos(th); z = R*sin(th);
C = [0 P.r]; Rb = P.R_bosaj;
Tr = tangenta([x(end) z(end)], C, Rb, 1);
Tl = tangenta([x(1) z(1)], C, Rb, -1);
pr = atan2(Tr(2) - C(2), Tr(1)); pl = atan2(Tl(2) - C(2), Tl(1));
if pl < pr, pl = pl + 2*pi; end
ps = linspace(pr, pl, N)';
xz = [x z; C(1) + Rb*cos(ps) C(2) + Rb*sin(ps)];
end

function T = tangenta(E, C, Rb, parte)
% Punctul de tangență dinspre E pe cercul (C, Rb), pe partea dată (+1 dreapta, -1 stânga).
v = E - C; d = norm(v); fi = acos(Rb/d); a0 = atan2(v(2), v(1));
T1 = C + Rb*[cos(a0 + fi) sin(a0 + fi)];
T2 = C + Rb*[cos(a0 - fi) sin(a0 - fi)];
if parte*T1(1) > parte*T2(1), T = T1; else, T = T2; end
end

function [Az, A, Jp] = arie_moment(xz)
% Momentul static față de axa X (A*z_c), aria și momentul polar față de origine.
x = xz(:,1); z = xz(:,2);
x1 = circshift(x, -1); z1 = circshift(z, -1);
c = x.*z1 - x1.*z;
A = sum(c)/2;
Az = sum((z + z1).*c)/6;
Jp = sum(c.*(x.^2 + x.*x1 + x1.^2 + z.^2 + z.*z1 + z1.^2))/12;
end

function A = polyarea_s(xz)
[~, A] = arie_moment(xz);
end
