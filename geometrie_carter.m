function G = geometrie_carter(P)
% GEOMETRIE_CARTER  Cotele carterului derivate din parametri.m (le folosesc s07 și s14).
% Coordonate: Y în lungul arborelui (+Y stânga, variatorul; -Y dreapta, mașina electrică), Z pe axa cilindrului.
G.R_brat = P.h_comp + P.L - P.r - (P.S + P.joc_raclor + P.zona_raclor) - P.joc_cg;   % raza contragreutăților
G.R_cav  = G.R_brat + P.joc_carter;                                  % cavitatea arborelui
G.y_cav  = P.latime_amb/2 + P.joc_carter_lat;                        % pereții cavității
G.y_ri   = P.latime_amb/2 + P.joc_rulment;                           % fața interioară a rulmentului
G.y_re   = G.y_ri + P.rul(3);                                        % fața exterioară
G.y_ext  = G.y_re + P.joc_simering + P.simering(3);                  % fața carterului = simeringul
G.D_bucsa = P.rul(2) + 2*P.t_bucsa;
G.D_bosaj = G.D_bucsa + 2*P.perete_bosaj_rul;
G.D_gura  = P.B + 2*P.t_perete + 2*P.joc_gura;
G.x_fanta = P.B/2 + P.joc_fanta;                                     % jumătatea fantei bielei
G.z_gura_jos = G.D_bosaj/2 + P.perete_min;                           % fundul gurii cilindrului
% Băile: în fața și în spatele arborelui, de la cel mai de jos punct al rotorului mașinii
% electrice până la axa arborelui; înăuntru, lățimea cavității (±y_cav)
G.R_ext  = G.R_cav + P.t_carter;                                     % exteriorul peretelui cavității
G.z_jos  = -(P.r_rot + P.t_pahar);                                   % fundul exterior = rotorul
G.x_i    = P.baie_x - P.t_carter;                                    % capetele interioare
G.z_fund = G.z_jos + P.t_carter;   G.z_tavan = -P.t_carter;
G.tes_i  = P.tesire - P.t_carter*(2 - sqrt(2));                      % teșiturile interioare
G.x_sicana = (G.R_ext + G.x_i)/2;                                    % șicanele, la mijlocul băilor
G.z_sorb = G.z_fund + 3e-3;                                          % sorbul, sub arbore (x = 0)
% Lamela: fereastra pe cavitate la unghi_lamela, sediul plan la R_ext + sa_lamela
u = P.unghi_lamela*pi/180;  n = [cos(u) sin(u)];  t = [-sin(u) cos(u)];
G.lamela_c = (G.R_ext + P.sa_lamela)*n;                              % centrul sediului (x, z)
G.lamela_sus = G.lamela_c(2) + abs(t(2))*(P.fereastra(2)/2 + 4e-3);  % muchia de sus a lamelei
% Aripioarele: orizontale (în lungul vântului), pe laturile băilor, până sub fața carterului
G.y_ar = G.y_ext - P.joc_capac;
na = floor((-G.z_jos - 2e-3 - P.aripioare(1)/2)/P.aripioare(2) + 1/2);
G.z_ar = -P.aripioare(2)*((1:na) - 1/2);
G.x_contur = @(z) P.baie_x - max(0, P.tesire(1) - (z - G.z_jos)) - max(0, P.tesire(2) + z);
% Uleiul: nivelul la repaus și volumul sub un plan z = z0 + k x (k = a/g)
Gv = G;
G.volum  = @(z0, k) volum_ulei(Gv, P, z0, k);
G.z_nivel = fzero(@(z) G.volum(z, 0) - P.V_ulei, [G.z_fund, G.z_tavan]);
% Prezoanele bazei cilindrului
G.prezoane = P.prezon_raza*[cosd(P.prezon_unghi) sind(P.prezon_unghi)];   % primul cadran; restul în oglindă
G.capete_libere = P.capete - (P.joc_simering + P.simering(3)) - [P.gerotor_joc + P.gerotor(4), 0];   % cât ies fusurile din carter (stânga: după capacul pompei)
end

function V = volum_ulei(G, P, z0, k)
% Uleiul sub planul z = z0 + k x, în cele două băi și în canalul de sub cavitate [m3]
x = linspace(-G.x_i, G.x_i, 4001);  dx = x(2) - x(1);
d = G.x_i - abs(x);                                                  % până la capătul băii
z_lo = G.z_fund + max(0, G.tes_i(1) - d);
z_hi = G.z_tavan - max(0, G.tes_i(2) - d);
disc = abs(x) < G.R_ext;
z_hi(disc) = min(z_hi(disc), -sqrt(G.R_ext^2 - x(disc).^2));         % sub peretele cavității
pl = z0 + k*x;
h = max(0, min(pl, z_hi) - z_lo);
sic = abs(abs(x) - G.x_sicana) < P.sicana(1)/2;                      % șicana: doar fantele sus și jos
h(sic) = max(0, min(pl(sic), G.z_fund + P.sicana(2)) - z_lo(sic)) + ...
         max(0, min(pl(sic), z_hi(sic)) - (G.z_tavan - P.sicana(2)));
V = 2*G.y_cav*sum(h)*dx;
end
