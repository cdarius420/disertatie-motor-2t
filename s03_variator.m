% S03_VARIATOR  Cinematica variatorului: raport, cursa servo-ului, reducția finală.
P = parametri();
fprintf('\n=== S03 Variatorul CVT ===\n');
Lb = lungime_curea(P.r1_min, P.r2_max, P.C);
r1 = linspace(P.r1_min, P.r1_max, 60)';
r2 = zeros(size(r1));
for k = 1:numel(r1)
    r2(k) = fzero(@(q) lungime_curea(r1(k), q, P.C) - Lb, [0.005 0.12]);
end
i_cvt = r2./r1;
fprintf('Lungimea curelei: %.0f mm\n', Lb*1e3);
fprintf('Raport: de la %.2f (pornire) la %.2f (viteză maximă); plaja %.2f\n', i_cvt(1), i_cvt(end), i_cvt(1)/i_cvt(end));

% Cursa axială a semifuliei mobile: dx = 2 * dr * tan(beta)
x_ax = 2*(r1 - P.r1_min)*tan(P.beta*pi/180);
fprintf('Cursa servo-ului pe semifulia conducătoare: %.1f mm\n', x_ax(end)*1e3);
fprintf('Cursa semifuliei conduse (arcul din spate): %.1f mm\n', 2*(r2(1) - r2(end))*tan(P.beta*pi/180)*1e3);

% Reducția finală care dă viteza maximă la turația de putere
w_r   = (P.v_max/3.6)/P.r_roata;
i_fin = (2*pi*P.n_putere/60)/w_r/i_cvt(end);
v_1   = (2*pi*P.n_putere/60)/(i_cvt(1)*i_fin)*P.r_roata*3.6;
fprintf('Reducția finală (cutie + lanț) pentru %d km/h la %d rot/min: %.2f\n', P.v_max, P.n_putere, i_fin);
fprintf('În modul dezlănțuit, motorul stă la %d rot/min de la %.0f km/h; sub această viteză patinează ambreiajul centrifugal\n', ...
        P.n_putere, v_1);

verifica(max(abs(lungime_curea(r1, r2, P.C) - Lb)) < 1e-9, 'V1c', 'Lungimea curelei rămâne constantă pe toată plaja');
verifica(all(diff(i_cvt) < 0), 'V2c', 'Raportul scade monoton când crește raza conducătoare');

% --- Grafice ---
f = figura_noua();
subplot(1,2,1); plot(x_ax*1e3, i_cvt, 'LineWidth', 1.5); grid on;
xlabel('cursa servo-ului [mm]'); ylabel('raportul variatorului [-]');
title('Raportul comandat de servo');
subplot(1,2,2); hold on;
v = linspace(0, 120, 200);
n_lung  = v/3.6/P.r_roata*i_cvt(1)*i_fin*60/(2*pi);
n_scurt = v/3.6/P.r_roata*i_cvt(end)*i_fin*60/(2*pi);
plot(v, n_lung, 'LineWidth', 1.5); plot(v, n_scurt, 'LineWidth', 1.5);
plot([v_1 P.v_max], [P.n_putere P.n_putere], 'k', 'LineWidth', 2);
ylim([0 13000]); grid on; xlabel('viteza [km/h]'); ylabel('turația motorului [rot/min]');
legend('raport de pornire', 'raport de viteză', 'dezlănțuit: turație ținută', 'Location', 'northwest');
title('Plaja de lucru a variatorului');
salveaza_figura(f, 's03_variator');
