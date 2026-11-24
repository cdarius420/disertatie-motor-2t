function Lb = lungime_curea(r1, r2, C)
% LUNGIME_CUREA  Lungimea primitivă a unei curele deschise [m].
%   r1, r2 - razele primitive [m]; C - distanța dintre axe [m]
phi = asin((r2 - r1)/C);
Lb  = 2*C*cos(phi) + pi*(r1 + r2) + 2*phi.*(r2 - r1);
end
