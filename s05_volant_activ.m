% S05_VOLANT_ACTIV  Fluctuația turației: volant clasic, volant ușor, volant activ.
% Verifică și pornirea cu mașina electrică și dimensionează cuplul ei.
P = parametri();
I = isg_constante(P);
G_isg = isg_geometrie(P); T_isg = G_isg.T_max(2);   % cuplul mașinii cu magneții calzi (s15)
J_usor = J_volant_usor(P);
fprintf('\n=== S05 Volantul activ și pornirea ===\n');
thEO = P.thEO_inchis;                 % modul docil: supapa de evacuare închisă
[th, p0, V, dV] = presiune_cilindru(P, 0, thEO);
N = numel(th); h = 2*pi/N;
[~, dx] = cinematica(th, P);

% --- Pornirea: motorul antrenat, fără ardere ---
Tg0 = (p0 - P.p_cc)*P.Ap.*dx;
T_rez = -min(Tg0);
comp = th >= 360 - thEO;
E_comp = -sum(Tg0(comp & Tg0 < 0))*h;
fprintf('Pornire: cuplul rezistent maxim la compresie %.1f N m; energia compresiei %.1f J\n', T_rez, E_comp);
fprintf('Mașina dă %.1f N m la %d A (magneți la %d °C): ', T_isg, P.I_pk, P.T_mag);
if T_isg >= T_rez
    fprintf('trece compresia direct.\n');
else
    fprintf('are nevoie de %.0f grade de elan înainte de compresie (rotire înapoi, apoi înainte).\n', ...
            E_comp/T_isg*180/pi);
end
fprintf('   (fără frecare și fără ungere rece: de măsurat pe motorul real)\n');

nume = {'A volant clasic', 'B volant ușor, pasiv', 'C volant ușor, activ', 'D activ, răspuns lent 2 ms'};
J0   = [P.J_pasiv J_usor J_usor J_usor];
act  = [0 0 1 1];
tau  = [P.tau_isg P.tau_isg P.tau_isg 2e-3];
cazuri_n = [P.n_ralanti 4000]; cazuri_imep = [1.0e5 3.0e5]; nrev = 25;
[~, p1] = presiune_cilindru(P, 1, thEO);
W0 = sum(p0.*dV)*h; W1 = sum(p1.*dV)*h;
for c = 1:2
    n = cazuri_n(c); imep = cazuri_imep(c); w = 2*pi*n/60;
    Q  = (imep*P.Vd - W0)/(W1 - W0);
    [~, p] = presiune_cilindru(P, Q, thEO);
    Tg = (p - P.p_cc)*P.Ap.*dx;
    W  = sum(p.*dV)*h;
    Tmean = sum(Tg)*h/(2*pi);
    fprintf('\n%d rot/min, PMI %.1f bar: căldură %.0f J/ciclu, presiune maximă %.1f bar\n', n, imep/1e5, Q, max(p)/1e5);
    fprintf('   cuplul de gaze: mediu %.2f N m, între %.1f și %.1f N m\n', Tmean, min(Tg), max(Tg));
    verifica(abs(W - imep*P.Vd)/(imep*P.Vd) < 0.005, sprintf('F%da', c), 'Presiunea medie indicată atinsă (abatere < 0,5%)');
    verifica(abs(sum(Tg)*h - W)/abs(W) < 0.005, sprintf('F%db', c), 'Lucrul din cuplu = lucrul din p dV (abatere < 0,5%)');

    E_g = cumsum((Tg - Tmean)*h);                 % estimarea analitică, volant clasic
    E_t = E_g - 0.5*P.m_rec*w^2*dx.^2;
    d_an = (max(E_t) - min(E_t))/(P.J_pasiv*w^2);

    delta = zeros(1,4); n_med = delta; OM = cell(1,4);
    for j = 1:4
        Tff = act(j)*tabel_volant_activ(Tg, Tmean, T_isg);
        om  = simuleaza_arbore(Tg, dx, P, J0(j), n, Tmean, Tff, tau(j), nrev);
        ult = om(end - 3*N + 1:end);
        w_med = viteza_medie(ult);
        n_med(j) = w_med*60/(2*pi);
        % fluctuația scade cu pătratul turației: o raportez la turația țintă,
        % ca să compar cazurile la aceeași turație (delta ~ dE/(J*omega^2))
        delta(j) = (max(ult) - min(ult))/w_med*(n_med(j)/n)^2;
        OM{j} = ult(end - N + 1:end)*60/(2*pi);
        fprintf('   %-26s fluctuație %5.2f%%   turație medie %5.0f rot/min\n', nume{j}, 100*delta(j), n_med(j));
    end
    fprintf('   (fluctuația e raportată la %d rot/min)\n', n);
    fprintf('   Estimarea analitică pentru A: %.2f%%\n', 100*d_an);
    verifica(abs(delta(1) - d_an)/d_an < 0.15, sprintf('F%dc', c), 'Simularea A = estimarea analitică (abatere < 15%)');
    verifica(all(abs(n_med(1:3) - n)/n < 0.03), sprintf('F%de', c), 'Turația medie rămâne la țintă (abatere < 3%)');
    fprintf('   Un răspuns lent (2 ms) schimbă turația medie cu %+.1f%%: cuplul electric trebuie să răspundă în <= 0,5 ms\n', ...
            100*(n_med(4) - n)/n);

    if c == 1
        verifica(delta(3) <= delta(1), 'V-VA', sprintf(['Ralanti: volantul ușor cu comandă activă e cel puțin ' ...
                 'la fel de liniștit ca volantul clasic (%.1f%% față de %.1f%%)'], 100*delta(3), 100*delta(1)));
        % Dimensionare: ce cuplu de vârf cere volantul activ
        Tv = [4 6 8 10 12 15 20]; red = zeros(size(Tv));
        for j = 1:numel(Tv)
            om  = simuleaza_arbore(Tg, dx, P, J_usor, n, Tmean, tabel_volant_activ(Tg, Tmean, Tv(j)), P.tau_isg, nrev);
            ult = om(end - 3*N + 1:end);
            wm  = viteza_medie(ult);
            red(j) = 1 - ((max(ult) - min(ult))/wm*(wm*60/(2*pi)/n)^2)/delta(2);
        end
        T50 = interp1(red, Tv, 0.5);
        TA  = interp1(red, Tv, 1 - delta(1)/delta(2));
        fprintf('   Dimensionare: 50%% reducere cere %.1f N m (%.0f A); ca volantul clasic cere %.1f N m (%.0f A)\n', ...
                T50, T50/I.Kt, TA, TA/I.Kt);
        f = figura_noua();
        plot(Tv, 100*red, 'o-', 'LineWidth', 1.5); hold on;
        plot([Tv(1) Tv(end)], 100*(1 - delta(1)/delta(2))*[1 1], 'k--'); plot([T_isg T_isg], [0 100], 'r--'); grid on;
        xlabel('cuplul electric de vârf [N m]'); ylabel('reducerea fluctuației la ralanti [%]');
        legend('volant ușor, activ', 'nivelul volantului clasic', sprintf('mașina dimensionată (%d A)', P.I_pk), 'Location', 'southeast');
        title('Cât cuplu cere volantul activ');
        salveaza_figura(f, 's05_dimensionare_volant_activ');

        f = figura_noua(); hold on;
        for j = 1:3
            plot(th, OM{j}, 'LineWidth', 1.5);
        end
        grid on; xlim([0 360]); xlabel('unghiul arborelui [grade de la PMI]'); ylabel('turația [rot/min]');
        legend(nume{1:3}, 'Location', 'southwest');
        title(sprintf('Ralanti %d rot/min: turația pe o rotație', n));
        salveaza_figura(f, 's05_volant_activ');

        f = figura_noua();
        plot(th, p/1e5, 'LineWidth', 1.5); hold on; plot(th, p0/1e5, '--', 'LineWidth', 1.5); grid on;
        xlim([0 360]); xlabel('unghiul arborelui [grade de la PMI]'); ylabel('presiunea [bar]');
        legend('cu ardere, ralanti', 'antrenat, fără ardere'); title('Presiunea în cilindru, modelul cu o zonă');
        salveaza_figura(f, 's05_presiune');
    end
end
