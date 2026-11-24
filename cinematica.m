function [x, dx, d2x] = cinematica(th_grade, P)
% CINEMATICA  Mecanismul bielă-manivelă, analitic.
%   x   - deplasarea pistonului față de PMI [m]
%   dx  - dx/dtheta [m/rad]
%   d2x - d2x/dtheta2 [m/rad^2]
% Viteza: v = dx*omega. Accelerația la turație constantă: a = d2x*omega^2.
th  = th_grade*pi/180;
lam = P.r/P.L;
D   = 1 - lam^2*sin(th).^2;
x   = P.r*(1 - cos(th)) + P.L*(1 - sqrt(D));
dx  = P.r*sin(th).*(1 + lam*cos(th)./sqrt(D));
d2x = P.r*cos(th) + P.r*lam*(cos(2*th)./sqrt(D) + lam^2*sin(2*th).^2./(4*D.^1.5));
end
