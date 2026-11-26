% s23_bilant_volum.m — bilanțul de volum în vedere laterală, 2D la 1:1, în anvelopa EZ-9 (Etapa 5)
%
% Întrebarea: încap coloana, motorul, Roots, variatorul, radiatorul, toba (cu tunelul), filtrul,
% rezervorul de 5 L și bateria (s20) între roțile EZ-9, cu garda de 210 mm și șaua la 750 mm?
% Și la ce unghi al cilindrului? Fiecare organ e un contur în vedere laterală plus intervalul lui
% pe lățime (y, + = stânga); două organe se lovesc doar dacă se suprapun în ambele.
% Origine: axul roții spate pe sol; x înainte, z în sus [mm].
% Cotele motorului vin din raport.txt (C9f, C12a, C13a etc.); cele marcate [ESTIMARE] sunt ipoteze.

P = parametri; Tb = toba(P); C = compresor(P); W = racire(P); Bat = baterie(P);
warning('off', 'MATLAB:polyshape:repairedBySimplify'); warning('off', 'MATLAB:polyshape:boundary3Points');

% --- Anvelopa EZ-9 și deciziile, din parametri.m ---
E9 = P.ez9;  WB = E9.WB; rf = E9.D_f/2; rr = E9.D_s/2; caster = E9.caster; trail = E9.trail;
cursa_f = E9.cursa_f; cursa_s = E9.cursa_s; GC = E9.GC; sa = E9.sa; L_EZ = E9.L;
C_cvt = P.C*1e3;                            % variatorul scurt
V_rez = P.V_rez;                            % rezervorul [L] (decizia C)
bat = Bat.cutie*1e3;                        % cutia bateriei din baterie.m [mm]; orientarea și locul le caută plaseaza

% --- Ipoteze de integrare [ESTIMARE] ---
zc     = GC + 85.5 + 4.5;                   % axa arborelui: scutul la 85,5 mm sub ea (C14c), garda 214,5 mm
gros_sa = 80;  z_sub_sa = sa - gros_sa;     % grosimea șeii
D_col  = 60;                                % diametrul exterior al coloanei (interior >= 44, secțiunea 15)
joc_aripa = 15;                             % aripa peste anvelopă
manta  = 15 + 1;  joc_panou = 12;           % golul tobă-manta + tabla, golul manta-panou
joc_cald = 50;                              % rezervorul și bateria față de învelișul tobei
filtru = [150 150];  y_filtru = [50 200];   % în afara plăcii pivotului (±40), cu 10 mm joc   % cutia filtrului: lungime, înălțime; lățimea
rezervor = [200 V_rez*1.1e6/(200*140) 140];     % rezervorul: 200 x h x 140 mm, 10% perete și aer; orientarea și locul le caută plaseaza
y_corp = 225;                               % semilățimea caroseriei = marginea exterioară a tunelului tobei (simetric)
R_cot = 1.5*Tb.D1*1e3;                      % raza primului cot al colectorului, 1,5 D1 [ESTIMARE]
rad_lat = 300; rad_gros = 40;               % radiatorul: lățime, grosime
A_rad = W.Q/(1005*P.aer_radiator(2))/(1.13*P.aer_radiator(1))*1e6;   % aria miezului din debitul de aer (s17) [mm2]
rad_h = A_rad/rad_lat;

alfa_sc = [30 45 60];  xc_sc = 520:20:720;
S = struct('P', P, 'Tb', Tb, 'C', C, 'WB', WB, 'rf', rf, 'rr', rr, 'caster', caster, 'trail', trail, ...
    'cursa_f', cursa_f, 'cursa_s', cursa_s, 'GC', GC, 'zc', zc, 'C_cvt', C_cvt, 'z_sub_sa', z_sub_sa, 'D_col', D_col, ...
    'joc_aripa', joc_aripa, 'manta', manta, 'joc_panou', joc_panou, 'joc_cald', joc_cald, 'filtru', filtru, ...
    'y_filtru', y_filtru, 'rezervor', rezervor, 'y_corp', y_corp, 'R_cot', R_cot, 'bat', bat, 'rad_lat', rad_lat, 'rad_gros', rad_gros, ...
    'rad_h', rad_h, 'L_EZ', L_EZ, 'V_rez', V_rez);
rez_tab = [];  cel_bun = [];  ales = [];  lov_txt = {};
% faza 1: toate unghiurile și pozițiile, fără baterie și rezervor (rapid)
for alfa = alfa_sc
    for xc = xc_sc
        [ok, info] = configureaza(alfa, xc, S, false);
        rez_tab = [rez_tab; alfa xc ok info.gc info.z_jos info.spate info.lovituri]; %#ok<AGROW>
        lov_txt{size(rez_tab, 1)} = info.lov_txt; %#ok<SAGROW>
    end
end
% faza 2: pentru fiecare unghi, în pozițiile fără lovituri (garda și spatele tobei se raportează separat), în ordinea
% apropierii de 50% din ampatament, se caută loc pentru baterie și rezervor; se păstrează prima poziție în care încap amândouă
fprintf('unghi | x arbore | încape | garda min [mm] | colector, punctul de jos [mm] | spatele tobei [mm] | lovituri\n');
for i = 1:size(rez_tab, 1)
    fprintf('%5.0f | %8.0f | %6d | %14.0f | %29.0f | %18.0f | %d  %s\n', rez_tab(i, :), lov_txt{i});
end
fprintf('\nCu bateria și rezervorul:\nunghi | x arbore | încape tot | garda [mm] | spatele tobei [mm] | baterie | rezervor | vârful chiulasei z [mm] | centrul cilindru+chiulasă z [mm]\n');
for alfa = alfa_sc
    cand = rez_tab(rez_tab(:, 1) == alfa & rez_tab(:, 7) == 0, :);  [~, ord] = sort(abs(cand(:, 2)/WB - 0.5));  cand = cand(ord, :);
    r = [];
    for i = 1:size(cand, 1)
        [ok, info, el] = configureaza(alfa, cand(i, 2), S, true);
        if isempty(r) || (info.ok_b && info.ok_r), r = struct('alfa', alfa, 'xc', cand(i, 2), 'el', el, 'info', info, 'ok', ok); end
        if info.ok_b && info.ok_r, break, end
    end
    if isempty(r), fprintf('%5d | nicio poziție fără lovituri\n', alfa); continue, end
    q = r.info;
    fprintf('%5d | %8d | %10d | %10.0f | %18.0f | %7d | %8d | %23.0f | %32.0f\n', alfa, r.xc, r.ok, q.gc, q.spate, q.ok_b, q.ok_r, q.z_chi, q.zg_cil);
    lt = q.lov_txt;  if isempty(lt), lt = 'niciuna'; end
    fprintf('        %s\n        %s\n        lovituri: %s\n', q.txt_b, q.txt_r, lt);
    deseneaza(r, WB, rf, rr, GC, sa, L_EZ, sprintf('s23_bilant_volum_%d.png', alfa));
    if isempty(cel_bun) || (r.ok && ~cel_bun.ok), cel_bun = r; end
    if alfa == P.unghi_cil, ales = r; end
end
b = cel_bun;
fprintf('\nCea mai bună: unghi %d, arborele la x = %d mm (%.0f%% din ampatament), încape tot: %d\n', b.alfa, b.xc, 100*b.xc/WB, b.ok);
fprintf('%s\n', b.info.text);
deseneaza(b, WB, rf, rr, GC, sa, L_EZ, 's23_bilant_volum.png');

% verificările, la unghiul ales (P.unghi_cil)
if isempty(ales)
    verifica(false, 'VL1', sprintf('La %d de grade există o poziție a arborelui fără lovituri', P.unghi_cil));
else
    q = ales.info;
    verifica(q.gc >= GC - 1e-6, 'VL1', sprintf('La %d de grade (arborele la %d mm) garda %.0f mm >= %d mm', P.unghi_cil, ales.xc, q.gc, GC));
    verifica(q.lovituri == 0, 'VL2', sprintf('Fără lovituri și cu jocul termic de %d mm la bateria și rezervorul de lângă tobă', joc_cald));
    verifica(q.ok_b && q.ok_r, 'VL3', sprintf('Bateria (%.0f x %.0f x %.0f mm) și rezervorul de %.0f L au loc', bat, V_rez));
    verifica(q.spate >= -(L_EZ - WB)/2, 'VL4', sprintf('Tunelul tobei se termină la x = %.0f mm, în lungimea EZ-9 (%.0f mm)', q.spate, -(L_EZ - WB)/2));
end

% ======================================================================
function [ok, info, el] = configureaza(alfa, xc, S, cu_plasare)
% construiește toate contururile pentru un unghi și o poziție a motorului și le verifică
P = S.P; Tb = S.Tb; C = S.C; WB = S.WB; rf = S.rf; rr = S.rr; caster = S.caster; trail = S.trail;
cursa_f = S.cursa_f; cursa_s = S.cursa_s; GC = S.GC; zc = S.zc; C_cvt = S.C_cvt; z_sub_sa = S.z_sub_sa;
D_col = S.D_col; joc_aripa = S.joc_aripa; manta = S.manta; joc_panou = S.joc_panou; joc_cald = S.joc_cald;
filtru = S.filtru; y_filtru = S.y_filtru; rezervor = S.rezervor; bat = S.bat; rad_lat = S.rad_lat;
rad_gros = S.rad_gros; rad_h = S.rad_h; L_EZ = S.L_EZ;

a = deg2rad(alfa);
M = @(w, u) [xc + w*cos(a) + u*sin(a); zc - w*sin(a) + u*cos(a)];   % rama motorului -> lume
dr = @(w1, w2, u1, u2) polyshape(M([w1 w2 w2 w1], [u1 u1 u2 u2])');
cerc = @(c, r) polyshape(c(1) + r*cos(linspace(0, 2*pi, 48)'), c(2) + r*sin(linspace(0, 2*pi, 48)'));
el = struct('nume', {}, 'p', {}, 'y', {}, 'tip', {});
adauga = @(el, n, p, y, t) [el struct('nume', n, 'p', p, 'y', y, 'tip', t)];

% motorul (cotele din raport.txt)
% carterul: băile se refac pentru unghi (secțiunea 14), deci nimic nu coboară sub scut (85,5 mm sub axă, C14c)
el = adauga(el, 'carter', intersect(dr(-120, 120, -85.5, 62), dreptunghi(-1e4, 1e4, zc - 85.5, 1e4)), [-52.5 52.5], 'motor');   % C9f
el = adauga(el, 'cilindru', dr(-56, 56, 62, 164.25), [-56 56], 'motor');                     % C12a
el = adauga(el, 'chiulasa', dr(-56, 56, 164.25, 164.25 + P.H_chiulasa*1e3), [-56 56], 'motor');
el = adauga(el, 'roots',    dr(-56 - C.lungime_spate*1e3, -56, C.z_c*1e3 - C.R_sp_ext*1e3, C.z_c*1e3 + C.R_sp_ext*1e3), ...
            [-C.R_sp_ext C.R_sp_ext]*1e3, 'motor');                                            % C13a
el = adauga(el, 'isg',      cerc(M(0, 0), 75.5), [-110 -56.5], 'motor');                      % capacul ocolește cilindrul (C14a); lățimea [ESTIMARE]
cond = M(-C_cvt, 0);
el = adauga(el, 'variator', union(cerc(M(0, 0), 70), cerc(cond, 78)), [59 145], 'motor');     % de la capacul pompei (C14e); lățimea [ESTIMARE]
el(end).p = convhull(el(end).p);

% cadrul: axa de direcție prin solul aflat la trail în fața petei de contact
ax_x = @(z) WB + trail - z*tand(caster);
H = [ax_x(600); 600];  Pv = cond + [-120; 0];  E = [Pv(1) + 20; z_sub_sa - D_col/2 - 10];   % pivotul în spatele fuliei conduse; coloana sus, sub șa, deasupra motorului [ESTIMARE]
el = adauga(el, 'coloana', banda(H, E, D_col), [-D_col D_col]/2, 'cadru');
el = adauga(el, 'placa pivot', banda(E, Pv, 40), [-40 40], 'cadru');

% roțile cu cursa (aripa inclusă)
d = [-sind(caster); cosd(caster)];  rf_p = polyshape();
for s = linspace(0, cursa_f, 6), rf_p = union(rf_p, cerc([WB; rf] + s*d, rf + joc_aripa)); end
el = adauga(el, 'roata fata', rf_p, [-50 50], 'roata');
Ls = norm([0; rr] - Pv);  th0 = atan2(rr - Pv(2), -Pv(1));  dth = cursa_s/Ls;  rs_p = polyshape();
for t = linspace(0, dth, 6), rs_p = union(rs_p, cerc(Pv + Ls*[cos(th0 - t); sin(th0 - t)], rr + joc_aripa)); end
el = adauga(el, 'roata spate', rs_p, [-65 65], 'roata');
br = polyshape();     % brațul cu carcasa lanțului, pe toată cursa
for t = linspace(0, dth, 6), u_b = [cos(th0 - t); sin(th0 - t)]; br = union(br, banda(Pv + 80*u_b, Pv + Ls*u_b, 60)); end   % de la 80 mm de pivot: bosajul pivotului ține de cadru
el = adauga(el, 'brat + lant', br, [-100 100], 'roata');        % lățimea brațelor și a carcasei [ESTIMARE]

% radiatorul: în fața chiulasei, cât mai în față fără să atingă roata
z_r = zc + 140;  x_r = WB;
while x_r > xc && overlaps(dreptunghi(x_r - rad_gros, x_r, z_r - rad_h/2, z_r + rad_h/2), rf_p), x_r = x_r - 5; end
el = adauga(el, 'radiator', dreptunghi(x_r - rad_gros, x_r, z_r - rad_h/2, z_r + rad_h/2), [-rad_lat rad_lat]/2, 'aux');

% filtrul sub șa, imediat în spatele ieșirii coloanei, pe stânga
el = adauga(el, 'filtru', dreptunghi(E(1) - filtru(1) - 10, E(1) - 10, z_sub_sa - filtru(2), z_sub_sa), y_filtru, 'aux');

% toba: colectorul și difuzorul pe dreapta, apoi tunelul sub șa
f = [cos(a); -sin(a)];  port = M(56, 164.25 - 26.8 - 27.7/2);   % mijlocul ferestrei de evacuare, pe fața cilindrului (C2d, C12f)
% colectorul pornește de la fața flanșei (W1) spre înainte-jos (f) și cotește în jos: cotul de rază R_cot, înlocuit
% în linia frântă de colțul W2, aflat la R_cot*tan(theta/2) de flanșă (theta = unghiul dintre f și verticală)
L_drept = S.R_cot*tand((90 - alfa)/2);
W1 = port + 12*f;  W2 = W1 + L_drept*f;
h_tun = Tb.D2*1e3 + 2*(manta + joc_panou);  z_ax = z_sub_sa - h_tun/2;
L_cer = (Tb.L1 - Tb.L_port + Tb.L2)*1e3;                          % de la fața flanșei, ca în s07 și s22
raza = @(s) 1e3*(Tb.D1/2 + min(max(s/1e3 - (Tb.L1 - Tb.L_port), 0), Tb.L2)*(Tb.D2 - Tb.D1)/(2*Tb.L2)) + manta;   % cu manta, la s mm de flanșă
% difuzorul urcă pe dreapta, în afara capacului ISG; locul urcării se mută spre spate până când bucla de sub motor
% rămâne deasupra gărzii, cu lungimea colector + difuzor dată de toba.m. Deplasarea laterală spre dreapta (~150 mm)
% nu e numărată în lungime: bucla iese mai adâncă decât în realitate (conservativ pentru gardă)
for x_urc = xc:-10:Pv(1)
    lung = @(zj) L_drept + (W2(2) - zj) + abs(W2(1) - x_urc) + (z_ax - zj);
    if lung(W2(2)) >= L_cer                      % nu mai trebuie coborât: urcarea se pune unde lungimea iese exact
        x_urc = W2(1) - (L_cer - L_drept - (z_ax - W2(2)));  z_jos = W2(2);  break
    end
    z_jos = fzero(@(zj) lung(zj) - L_cer, [-500 W2(2)]);
    if z_jos - raza(lung(z_jos) - (z_ax - z_jos)) >= GC, break, end
end
r_jos = raza(lung(z_jos) - (z_ax - z_jos));      % raza la capătul de jos al buclei (cea mai mare de pe porțiunea de jos)
x_t0 = x_urc - 20;
traseu = [W1 W2 [W2(1); z_jos] [x_urc; z_jos] [x_urc; z_ax]];
s_cap = cumsum([0 vecnorm(diff(traseu, 1, 2))]);                % lungimea de la flanșă la fiecare colț
tub = cell(1, 4);
for k = 1:4, tub{k} = banda(traseu(:, k), traseu(:, k + 1), 2*raza(s_cap(k + 1))); end
% ieșirea stă în axa cilindrului (y = 0); în cotul din W2 țeava trece spre dreapta, în afara carterului și a capacului ISG;
% coborârea, bucla de sub motor și urcarea stau pe dreapta
el = adauga(el, 'colector (ieșire)', tub{1}, [-1 1]*raza(0), 'toba');
el = adauga(el, 'colector (cot spre dreapta)', intersect(cerc(W2, raza(L_drept)), dr(56 + 12, 2000, -2000, 2000)), [-175 raza(0)], 'toba');   % cotul nu trece în spatele flanșei
el = adauga(el, 'colector+difuzor (coborâre, buclă, urcare)', union(union(tub{2}, tub{3}), tub{4}), [-175 -120], 'toba');
L_tun = (Tb.L3 + Tb.L4 + Tb.L5)*1e3;
el = adauga(el, 'tunel (burta, con, stinger)', dreptunghi(x_t0 - L_tun, x_t0 + 20, z_ax - h_tun/2, z_ax + h_tun/2), [-225 -75], 'toba');   % lângă roata spate, nu deasupra ei

% bateria și rezervorul: bateria jos și la mijlocul ampatamentului, rezervorul sub șa, în spatele filtrului
ok_b = true; ok_r = true; txt_b = ''; txt_r = '';
if cu_plasare
    [el, ok_b, txt_b] = plaseaza(el, 'baterie', bat, [WB/2; GC], joc_cald, GC, z_sub_sa, ax_x, S.y_corp);
    [el, ok_r, txt_r] = plaseaza(el, sprintf('rezervor %.1f L', S.V_rez), rezervor, [E(1) - 300; z_sub_sa], joc_cald, GC, z_sub_sa, ax_x, S.y_corp);
end

% verificările
lov = {};
for i = 1:numel(el)
    for j = i + 1:numel(el)
        if strcmp(el(i).tip, el(j).tip) && any(strcmp(el(i).tip, {'roata', 'cadru', 'toba'})), continue, end   % piese legate între ele
        jl = 10*~strcmp(el(i).tip, el(j).tip);   % 10 mm joc lateral între organe diferite, ca la plasare [ESTIMARE]
        if el(i).y(1) < el(j).y(2) + jl && el(j).y(1) < el(i).y(2) + jl && area(intersect(el(i).p, el(j).p)) > 1
            lov{end + 1} = sprintf('%s / %s', el(i).nume, el(j).nume); %#ok<AGROW>
        end
        % jocul termic: bateria și rezervorul trebuie să stea la joc_cald de tobă pe cel puțin o axă (lateral sau în vedere laterală)
        rece = strcmp({el(i).tip, el(j).tip}, 'rece');  cald_ = strcmp({el(i).tip, el(j).tip}, 'toba');
        if any(rece) && any(cald_)
            gol_y = max(el(i).y(1) - el(j).y(2), el(j).y(1) - el(i).y(2));
            if gol_y < joc_cald && area(intersect(polybuffer(el(i).p, joc_cald), el(j).p)) > 1
                lov{end + 1} = sprintf('%s / %s (joc termic)', el(i).nume, el(j).nume); %#ok<AGROW>
            end
        end
    end
end
zmin = arrayfun(@(e) min(e.p.Vertices(:, 2)), el(~strcmp({el.tip}, 'roata')));
spate = x_t0 - L_tun;  lim_spate = -(L_EZ - WB)/2;
ch = strcmp({el.nume}, 'chiulasa');  [~, info.zg_cil] = centroid(union(el(strcmp({el.nume}, 'cilindru')).p, el(ch).p));  info.z_chi = max(el(ch).p.Vertices(:, 2));
info.ok_b = ok_b;  info.ok_r = ok_r;  info.txt_b = txt_b;  info.txt_r = txt_r;
info.gc = min(zmin);  info.z_jos = z_jos - r_jos;  info.L_drept = L_drept;  info.spate = spate;  info.lovituri = numel(lov);  info.lov_txt = strjoin(lov, '; ');
ok = info.gc >= GC - 1e-6 && isempty(lov) && ok_b && ok_r && spate >= lim_spate;
info.text = sprintf(['  garda minimă %.0f mm (cerut %d); colectorul coboară la %.0f mm\n' ...
    '  tunelul se termină la x = %.0f mm (limita EZ-9: %.0f mm în spatele axului spate)\n' ...
    '  radiatorul: miez %.0f x %.0f mm\n  %s\n  %s\n  lovituri: %s'], ...
    info.gc, GC, info.z_jos, spate, lim_spate, rad_lat, rad_h, txt_b, txt_r, strjoin([lov {'niciuna'}], ', '));
if ~isempty(lov), info.text = strrep(info.text, ', niciuna', ''); end
end

function p = dreptunghi(x1, x2, z1, z2)
p = polyshape([x1 x2 x2 x1], [z1 z1 z2 z2]);
end

function p = banda(A, B, w)
% bandă de lățime w între punctele A și B
n = [-(B(2) - A(2)); B(1) - A(1)];  n = n/norm(n)*w/2;
p = polyshape([A(1) + n(1), B(1) + n(1), B(1) - n(1), A(1) - n(1)], [A(2) + n(2), B(2) + n(2), B(2) - n(2), A(2) - n(2)]);
end

function [el, ok, txt] = plaseaza(el, nume, dims, tinta, joc_cald, GC, z_sus, ax_x, y_max)
% cutia cu laturile dims în poziția liberă cea mai apropiată de țintă (plus abaterea laterală), în toate cele 6 orientări,
% la poziții laterale din 20 în 20 mm, de la mijloc spre stânga (0 <= y, marginea <= y_max), numai în spatele axei de direcție (60 mm joc pentru virare).
% Obstacolele se rasterizează la 5 mm în vedere laterală, umflate cu un pas, și cu 10 mm joc lateral (conservativ). Față de tobă cutia are nevoie
% de joc_cald pe cel puțin o axă: două cutii sunt separate dacă sunt separate pe o axă.
h = 5;  [Xg, Zg] = meshgrid(-250:h:1300, GC:h:z_sus);  [nz, nx] = size(Xg);
blocat0 = Xg >= ax_x(Zg) - 60;
m = false(nz, nx, numel(el));  yk = zeros(numel(el), 2);
for k = 1:numel(el)
    j = h;  yk(k, :) = el(k).y + [-10 10];                    % 10 mm joc lateral față de orice organ [ESTIMARE]
    if strcmp(el(k).tip, 'toba'), j = h + joc_cald;  yk(k, :) = el(k).y + [-joc_cald joc_cald]; end
    m(:, :, k) = reshape(isinterior(polybuffer(el(k).p, j), Xg(:), Zg(:)), nz, nx);
end
O = unique(perms(dims), 'rows');  best = [Inf zeros(1, 6)];   % cost, x, z, lx, lz, y1, y2
for io = 1:size(O, 1)
    lx = O(io, 1); lz = O(io, 2); ly = O(io, 3);  ymx = y_max - ly/2;
    ni = ceil(lz/h);  nj = ceil(lx/h);                          % cutia acoperită de celule întregi (conservativ)
    if ymx < 0 || ni >= nz || nj >= nx, continue, end
    for yc = 0:20:ymx                      % la mijloc sau pe stânga: ce e rece stă pe stânga, toba pe dreapta (regula de plasare, Etapa 5)
        y = yc + [-ly ly]/2;  sel = y(1) < yk(:, 2) & yk(:, 1) < y(2);
        I = zeros(nz + 1, nx + 1);  I(2:end, 2:end) = cumsum(cumsum(blocat0 | any(m(:, :, sel), 3), 1), 2);
        ii = (1:nz - ni)';  jj = 1:nx - nj;
        sb = I(ii + ni + 1, jj + nj + 1) - I(ii, jj + nj + 1) - I(ii + ni + 1, jj) + I(ii, jj);   % celule blocate în cutie
        [r, c] = find(sb == 0);
        if isempty(r), continue, end
        x = Xg(1, c)';  z = Zg(r, 1);
        [cost, q] = min(hypot(x + lx/2 - tinta(1), z + lz/2 - tinta(2)) + abs(yc));
        if cost < best(1), best = [cost x(q) z(q) lx lz y]; end
    end
end
ok = isfinite(best(1));  txt = sprintf('%s: nu încape', nume);
if ok
    el(end + 1) = struct('nume', nume, 'p', dreptunghi(best(2), best(2) + best(4), best(3), best(3) + best(5)), 'y', best(6:7), 'tip', 'rece');
    txt = sprintf('%s: x %.0f..%.0f, z %.0f..%.0f, y %.0f..%.0f mm', nume, best(2), best(2) + best(4), best(3), best(3) + best(5), best(6), best(7));
end
end

function deseneaza(b, WB, rf, rr, GC, sa, L_EZ, fis)
fig = figure('Visible', 'off', 'Position', [100 100 1400 760]); hold on; axis equal; grid on;
culori = struct('motor', [0.45 0.45 0.45], 'cadru', [0.2 0.2 0.2], 'roata', [0.75 0.75 0.75], 'aux', [0.20 0.45 0.75], 'rece', [0.20 0.60 0.30], 'toba', [0.85 0.25 0.15]);
for e = b.el
    plot(e.p, 'FaceColor', culori.(e.tip), 'FaceAlpha', 0.25, 'EdgeColor', culori.(e.tip));
    [cx, cz] = centroid(e.p); text(cx, cz, e.nume, 'FontSize', 8, 'HorizontalAlignment', 'center');
end
yline(0, 'k'); yline(GC, '--', sprintf('garda %d mm', GC)); yline(sa, '--', sprintf('șaua %d mm', sa));
xline(-(L_EZ - WB)/2, ':', 'lungimea EZ-9 în spate'); xline(WB + (L_EZ - WB)/2, ':', 'lungimea EZ-9 în față');
title(sprintf('Bilanțul de volum: cilindrul la %d°, arborele la x = %d mm, încape tot = %d', b.alfa, b.xc, b.ok));
xlabel('x de la axul roții spate [mm]'); ylabel('z de la sol [mm]');
xlim([-400 1600]); ylim([0 900]);
if ~exist('rezultate', 'dir'), mkdir('rezultate'); end
exportgraphics(fig, fullfile('rezultate', fis), 'Resolution', 150); close(fig);
end
