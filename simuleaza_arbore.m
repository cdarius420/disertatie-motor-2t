function [om, Tisg_log] = simuleaza_arbore(Tg, dx, P, J0, n_ref, Tmean, Tff, tau, nrev)
% SIMULEAZA_ARBORE  Dinamica arborelui pe unghi, metoda energiei:
%   d/dtheta( 1/2 * J(theta) * omega^2 ) = Tg + Tisg - Tsarcina
%   J(theta) = J0 + m_rec * (dx/dtheta)^2 include masele alternative.
% Tff: tabelul cuplului electric pe unghi (zero = volant pasiv). Mașina îl
% urmărește cu întârzierea de ordinul întâi tau.
N  = numel(Tg);
h  = 2*pi/N;
Jeq = J0 + P.m_rec*dx.^2;
w_ref = 2*pi*n_ref/60;
KE = 0.5*Jeq(1)*w_ref^2;
w  = w_ref; Tisg = Tff(1);
om = zeros(N*nrev, 1); Tisg_log = om;
for i = 1:N*nrev
    k  = mod(i - 1, N) + 1;
    kn = mod(i, N) + 1;
    Tisg = Tff(k) + (Tisg - Tff(k))*exp(-h/(tau*w));
    KE = KE + (Tg(k) + Tisg - Tmean*w/w_ref)*h;
    w  = sqrt(2*KE/Jeq(kn));
    om(i) = w; Tisg_log(i) = Tisg;
end
end
