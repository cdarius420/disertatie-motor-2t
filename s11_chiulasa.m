% S11_CHIULASA  Camera de ardere: banda de squish și bolul sferic.
% Volumul mort (s01, din raportul reținut) = alezaj x joc de squish + calota bolului.
% Viteza de squish după Blair: din volumele benzii și bolului, cu presiune uniformă,
% gazul împins din bandă trece prin cortina de la marginea bolului.
P = parametri();
fprintf('\n=== S11 Chiulasa și squish-ul ===\n');
mm = 1e3;
Ab = pi/4*P.B^2;
thEC = 360 - P.thEO_deschis;
[h_bol, R_bol, d_bol, Vc, V_cal] = camera_ardere(P);
fprintf('Volum mort %.2f cm3 = alezaj x squish %.2f cm3 + calota %.2f cm3\n', Vc*1e6, Ab*P.x_sq*1e6, V_cal*1e6);
fprintf('Banda de squish: %.0f%% din alezaj, bolul Ø%.2f mm, adânc de %.2f mm, sferă de rază %.2f mm\n', ...
        100*P.SAR, d_bol*mm, h_bol*mm, R_bol*mm);

% Viteza de squish de la închiderea evacuării până la PMI
Asq = P.SAR*Ab;
th = linspace(thEC, 360, 3000)';
x = cinematica(th, P);
hh = P.x_sq + x;
f = Asq*hh./(V_cal + Ab*hh);                           % fracția de masă din bandă
Vt = V_cal + Ab*hh;
msv = @(n) max(-Vt(1:end-1).*diff(f)./diff(th*pi/180)*(2*pi*n/60)./(pi*d_bol*hh(1:end-1)));
v_p = msv(P.n_putere); v_m = msv(P.n_max);
fprintf('Viteza maximă de squish: %.1f m/s la %d rot/min, %.1f m/s la limitator\n', v_p, P.n_putere, v_m);
verifica(v_p <= P.MSV_max, 'H1', sprintf('Squish de %.2f mm: %.1f m/s <= %.0f m/s la turația de putere (Blair)', ...
         P.x_sq*mm, v_p, P.MSV_max));
verifica(P.H_chiulasa - h_bol >= 6e-3, 'H2', sprintf('Deasupra bolului rămân %.1f mm de chiulasă (>= 6 mm) pentru bujie', ...
         (P.H_chiulasa - h_bol)*mm));
fprintf('   Raport de compresie geometric %.1f; reținut %.1f (YZ125 declară 8,2-10,1).\n', (P.Vd + Vc)/Vc, P.CRt);
