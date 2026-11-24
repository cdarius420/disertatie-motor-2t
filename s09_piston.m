% S09_PISTON  Pistonul și bolțul, pe baza pistonului YZ125.
% Verifică: clasele de piston = YZ125; bolțul la încovoiere; presiunea în bosaje;
% zona segmenților deasupra bosajelor; raclorul în zona lui; bolțul în piston.
P = parametri();
fprintf('\n=== S09 Pistonul și bolțul ===\n');
mm = 1e3;

% 1. Clasele de piston din s08 față de YZ125
pas = P.alezaj_tol/(P.n_clase - 0.5);
cls = [P.B - P.joc_piston(1) + pas/2 - diff(P.joc_piston), P.B + (P.n_clase - 1)*pas - P.joc_piston(1)];
fprintf('Pistonul pe clase: %.3f-%.3f mm; YZ125: %.3f-%.3f mm\n', cls*mm, P.piston_YZ125*mm);
verifica(all(abs(cls - P.piston_YZ125) < 0.5e-6), 'P1', 'Clasele de piston din s08 = plaja YZ125 din manual');

% 2. Bolțul la încovoiere: grindă pe două reazeme (centrele bosajelor), sarcina
%    distribuită pe lățimea piciorului bielei. M = F*(2*l - b)/8.
thEO = P.thEO_deschis;
[th, p0, V, dV] = presiune_cilindru(P, 0, thEO); h = 2*pi/numel(th);
[~, p1] = presiune_cilindru(P, 1, thEO);
W0 = sum(p0.*dV)*h; W1 = sum(p1.*dV)*h;
[~, p] = presiune_cilindru(P, (P.imep_plin*P.Vd - W0)/(W1 - W0), thEO);
F = (P.f_proiect*max(p) - P.p_cc)*P.Ap;
a = P.b_picior + 2*P.joc_ax_biela;                 % golul dintre bosaje
l_bos = (P.l_bolt - a)/2;                          % lungimea de sprijin în fiecare bosaj
l = a + l_bos;                                     % distanța dintre centrele bosajelor
M = F*(2*l - P.b_picior)/8;
W = pi*(P.d_bolt^4 - P.d_bolt_int^4)/(32*P.d_bolt);
sig = M/W;
fprintf('Forța de proiectare pe piston %.1f kN; bolț %.0f/%.0f x %.0f mm: moment %.1f N m, efort %.0f MPa\n', ...
        F/1e3, P.d_bolt*mm, P.d_bolt_int*mm, P.l_bolt*mm, M, sig/1e6);
verifica(sig <= P.Re_bolt/P.CS_bolt, 'P2', sprintf('Bolțul la încovoiere: %.0f MPa <= %.0f MPa (coeficient %.1f)', ...
         sig/1e6, P.Re_bolt/P.CS_bolt/1e6, P.CS_bolt));

% 3. Presiunea în bosaje
pb = F/(2*l_bos*P.d_bolt);
verifica(pb <= P.p_bosaj_adm, 'P3', sprintf('Presiunea în bosaje %.1f MPa <= %.0f MPa', pb/1e6, P.p_bosaj_adm/1e6));

% 4. Zona segmenților se termină deasupra bosajelor
hc = P.seg_h_ales + P.joc_lat_seg;                 % înălțimea canalelor
jos_seg = P.cap_sus + hc(1) + P.punte_seg + hc(2) + P.perete_canal;   % capătul centurii
sus_bos = P.h_comp - P.d_bosaj/2;
fprintf('Canalele segmenților: %.2f-%.2f și %.2f-%.2f mm sub coroană; bosajele încep la %.1f mm\n', ...
        P.cap_sus*mm, (P.cap_sus + hc(1))*mm, (P.cap_sus + hc(1) + P.punte_seg)*mm, ...
        (P.cap_sus + hc(1) + P.punte_seg + hc(2))*mm, sus_bos*mm);
fprintf('Centura segmenților: groasă de %.2f mm (canal %.2f + perete %.2f), până la %.2f mm sub coroană\n', ...
        (P.seg_t + P.joc_rad_seg + P.perete_canal)*mm, (P.seg_t + P.joc_rad_seg)*mm, P.perete_canal*mm, jos_seg*mm);
verifica(sus_bos - jos_seg >= 2e-3, 'P4', sprintf('Între centura segmenților și bosaje rămân %.1f mm (>= 2 mm)', ...
         (sus_bos - jos_seg)*mm));

% 5. Raclorul încape în zona lui de pe fustă, cu umăr dedesubt
hr = P.rac_h + P.joc_lat_seg;
verifica(hr <= P.zona_raclor - 1e-3, 'P5', sprintf('Canalul raclorului %.2f mm încape în zona de %.1f mm, cu umăr de 1 mm', ...
         hr*mm, P.zona_raclor*mm));

% 6. Bolțul încape în piston, cu loc pentru siguranțe (1,5 mm pe parte)
Dp = P.B - mean(P.joc_piston);
verifica(P.l_bolt + 2*1.5e-3 <= Dp, 'P6', sprintf('Bolțul de %.0f mm + siguranțele încap în pistonul de %.3f mm', ...
         P.l_bolt*mm, Dp*mm));
fprintf('   Diferență față de YZ125: segmentul lui are 1,0 mm și ține la turații mari; criteriul din s06\n');
fprintf('   presupune presiunea din carter sub segment, deci e prudent. Păstrăm 0,8 mm pentru ambii segmenți.\n');
