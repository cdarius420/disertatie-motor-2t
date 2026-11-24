function [h, R, d, Vc, Vcal] = camera_ardere(P)
% CAMERA_ARDERE  Bolul sferic din chiulasă care dă volumul mort din raportul reținut.
% Volumul mort = alezaj x joc de squish + calota sferică peste bol.
% Întoarce adâncimea h, raza sferei R, diametrul bolului d, volumele [m, m3].
Ab = pi/4*P.B^2;
Vc = Ab*cinematica(360 - P.thEO_deschis, P)/(P.CRt - 1);
d = P.B*sqrt(1 - P.SAR); a = d/2;
Vcal = Vc - Ab*P.x_sq;
h = fzero(@(h) pi*h.*(3*a^2 + h.^2)/6 - Vcal, [1e-4 a]);
R = (a^2 + h^2)/(2*h);
end
