function [th, p, V, dV] = presiune_cilindru(P, Qtot, thEO)
% PRESIUNE_CILINDRU  Presiunea pe un ciclu (360 de grade), model cu o zonă.
%   Qtot - căldura degajată pe ciclu [J] (0 = motor antrenat, fără ardere)
%   thEO - deschiderea evacuării [grade după PMI]
% Faza închisă (închiderea evacuării -> deschiderea evacuării, ciclul următor):
%   dp/dth = -gamma*p/V*dV/dth + (gamma-1)/V*dQ/dth, ardere după Wiebe.
% Faza deschisă: presiunea scade exponențial spre presiunea de evacuare.
dth = 0.1;                                   % pasul [grade]
th  = (0:dth:360-dth)';
h   = dth*pi/180;
thEC = 360 - thEO;
xEC0 = cinematica(360 - P.thEO_deschis, P);  % volumul mort e geometric: fix
Vc   = P.Ap*xEC0/(P.CRt - 1);
Vf  = @(t) Vc + P.Ap*cinematica(t, P);
dVf = @(t) P.Ap*nth_out(2, t, P);
dQf = @(t) Qtot*wiebe_deriv(t, P)*180/pi;     % [J/rad]
f   = @(t, p) -P.gamma*p./Vf(t).*dVf(t) + (P.gamma - 1)./Vf(t).*dQf(t);

tu = (thEC:dth:thEO + 360)';                 % unghiuri desfăcute ale fazei închise
pu = zeros(size(tu)); pu(1) = P.p_ev;
for k = 1:numel(tu) - 1
    t  = tu(k); pk = pu(k);
    k1 = f(t, pk);
    k2 = f(t + dth/2, pk + h/2*k1);
    k3 = f(t + dth/2, pk + h/2*k2);
    k4 = f(t + dth,   pk + h*k3);
    pu(k+1) = pk + h/6*(k1 + 2*k2 + 2*k3 + k4);
end
p = zeros(size(th));
tw = mod(tu, 360);
idx = round(tw/dth) + 1; idx(idx > numel(th)) = 1;
p(idx) = pu;
pEO = pu(end);
des = th > thEO & th < thEC;
p(des) = P.p_ev + (pEO - P.p_ev)*exp(-(th(des) - thEO)/15);
V  = Vf(th);
dV = dVf(th);
end

function y = nth_out(n, t, P)
[a, b, c] = cinematica(t, P); %#ok<ASGLU>
if n == 2
    y = b;
else
    y = c;
end
end

function d = wiebe_deriv(t, P)
% dx_b/dtheta [1/grad], ardere de la aprindere pe durata Wiebe
u = (t - P.thIGN)/P.wiebe_durata;
d = zeros(size(t));
m = u > 0 & u < 1.5;
d(m) = P.wiebe_a*(P.wiebe_m + 1)/P.wiebe_durata .* u(m).^P.wiebe_m .* exp(-P.wiebe_a*u(m).^(P.wiebe_m + 1));
end
