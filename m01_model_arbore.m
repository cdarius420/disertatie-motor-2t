% M01_MODEL_ARBORE  Primul model Simulink (MIL-1): dinamica arborelui și volantul activ.
% Construiește model_arbore.slx din script, îl simulează în timp și compară
% fluctuația turației cu metoda energiei pe unghi din s05 (simuleaza_arbore).
% Două metode independente trebuie să dea același rezultat.
%   d(omega)/dt = (Tg + Tisg - Tsarcina - m_rec*x'*x''*omega^2) / (J0 + m_rec*x'^2)
P = parametri(); I = isg_constante(P); T_isg = isg_geometrie(P).T_max(2); J_usor = J_volant_usor(P);
fprintf('\n=== M01 Modelul Simulink al arborelui (MIL-1) ===\n');
mdl = 'model_arbore';

% --- Datele: cuplul de gaze la ralanti, ca în s05 ---
n = P.n_ralanti; imep = 1.0e5; thEO = P.thEO_inchis;
[th, p0, V, dV] = presiune_cilindru(P, 0, thEO);
N = numel(th); h = 2*pi/N;
[~, dx, d2x] = cinematica(th, P);
[~, p1] = presiune_cilindru(P, 1, thEO);
W0 = sum(p0.*dV)*h; W1 = sum(p1.*dV)*h;
[~, p] = presiune_cilindru(P, (imep*P.Vd - W0)/(W1 - W0), thEO);
Tg = (p - P.p_cc)*P.Ap.*dx;
Tmean = sum(Tg)*h/(2*pi);
Tff = tabel_volant_activ(Tg, Tmean, T_isg);
per = @(v) [v; v(1)];                          % tabel periodic, închis la 2*pi
th_tab = [th; 360]*pi/180;

% --- Construcția modelului ---
% Poziții fixe [stânga sus dreapta jos], fluxul de la stânga la dreapta:
% unghi -> tabele pe unghi -> ecuația de mișcare -> integratoare -> înapoi la unghi.
nrev = 25; w_ref = 2*pi*n/60;
if bdIsLoaded(mdl), close_system(mdl, 0); end
if exist([mdl '.slx'], 'file'), delete([mdl '.slx']); end
new_system(mdl);
b = @(nume) [mdl '/' nume];
add_block('simulink/Sources/Constant', b('doi_pi'), 'Value', '2*pi', 'Position', [30 235 70 265]);
add_block('simulink/Math Operations/Math Function', b('unghi_pe_ciclu'), 'Operator', 'mod', 'Position', [120 190 170 240]);
tab = {'Tg', 'Tg_tab', 40; 'Tff', 'Tff_tab', 130; 'dx', 'dx_tab', 220; 'd2x', 'd2x_tab', 310};
for k = 1:size(tab, 1)
    add_block('simulink/Lookup Tables/1-D Lookup Table', b(tab{k,1}), ...
              'BreakpointsForDimension1', 'th_tab', 'Table', tab{k,2}, ...
              'Position', [240 tab{k,3} 310 tab{k,3}+50]);
end
add_block('simulink/Continuous/Transfer Fcn', b('raspuns_masina'), 'Numerator', '1', 'Denominator', '[tau 1]', ...
          'Position', [360 135 440 175]);
add_block('simulink/Math Operations/Gain', b('sarcina'), 'Gain', 'Tmean/w_ref', 'Position', [380 400 430 440]);
add_block('simulink/Signal Routing/Mux', b('mux'), 'Inputs', '6', 'Position', [500 30 506 450]);
add_block('simulink/User-Defined Functions/Fcn', b('dinamica'), ...
          'Expr', '(u(1)+u(2)-u(3)-m_rec*u(4)*u(5)*u(6)^2)/(J0+m_rec*u(4)^2)', 'Position', [560 220 700 260]);
add_block('simulink/Continuous/Integrator', b('omega'), 'InitialCondition', 'w0', 'Position', [750 220 780 260]);
add_block('simulink/Continuous/Integrator', b('theta'), 'InitialCondition', '0', 'Position', [840 220 870 260]);
add_block('simulink/Sinks/To Workspace', b('om_log'), 'VariableName', 'om_log', 'SaveFormat', 'Timeseries', ...
          'Position', [830 320 900 350]);
L = {'dinamica/1','omega/1'; 'omega/1','theta/1'; 'theta/1','unghi_pe_ciclu/1'; 'doi_pi/1','unghi_pe_ciclu/2';
     'unghi_pe_ciclu/1','Tg/1'; 'unghi_pe_ciclu/1','Tff/1'; 'unghi_pe_ciclu/1','dx/1'; 'unghi_pe_ciclu/1','d2x/1';
     'Tff/1','raspuns_masina/1'; 'omega/1','sarcina/1';
     'Tg/1','mux/1'; 'raspuns_masina/1','mux/2'; 'sarcina/1','mux/3'; 'dx/1','mux/4'; 'd2x/1','mux/5'; 'omega/1','mux/6';
     'mux/1','dinamica/1'; 'omega/1','om_log/1'};
for k = 1:size(L, 1)
    add_line(mdl, L{k,1}, L{k,2}, 'autorouting', 'smart');
end
set_param(mdl, 'Solver', 'ode45', 'RelTol', '1e-8', 'AbsTol', '1e-8', 'MaxStep', '2e-5', 'StopTime', 'Tsim', ...
          'Description', ['Dinamica arborelui cotit cu volant activ (MIL-1). Generat de m01_model_arbore.m; ' ...
                          'datele vin din parametri.m. Nu se editează de mână.']);
% Datele stau în spațiul de lucru al modelului: modelul se deschide și rulează singur
% (cazul C, volant ușor activ). Simulările de mai jos suprascriu doar ce diferă.
date = {'th_tab', th_tab; 'Tg_tab', per(Tg); 'Tff_tab', per(Tff); 'dx_tab', per(dx); 'd2x_tab', per(d2x);
        'w0', w_ref; 'w_ref', w_ref; 'Tmean', Tmean; 'J0', J_usor; 'm_rec', P.m_rec; 'tau', P.tau_isg;
        'Tsim', nrev*60/n};
mw = get_param(mdl, 'ModelWorkspace');
for k = 1:size(date, 1)
    assignin(mw, date{k,1}, date{k,2});
end
save_system(mdl);
fprintf('Am construit %s.slx (se deschide și rulează singur: cazul C)\n', mdl);

% --- Simulare și comparație cu s05 ---
cazuri = {'A volant clasic', P.J_pasiv, 0; 'B volant ușor, pasiv', J_usor, 0; 'C volant ușor, activ', J_usor, 1};
for j = 1:size(cazuri, 1)
    J0 = cazuri{j,2}; act = cazuri{j,3};
    in = Simulink.SimulationInput(mdl);
    in = in.setVariable('J0', J0, 'Workspace', mdl);
    in = in.setVariable('Tff_tab', per(act*Tff), 'Workspace', mdl);
    out = sim(in);
    % Aceeași definiție pentru ambele metode: turația medie = rotații pe timp,
    % nu media vitezei pe unghi (la fluctuații mari, cele două diferă).
    t = out.om_log.Time; w = out.om_log.Data(:);
    s = t >= t(end) - 3*60/n;
    w_med = trapz(t(s), w(s))/(t(find(s, 1, 'last')) - t(find(s, 1)));
    n_sl = w_med*60/(2*pi);
    d_sl = (max(w(s)) - min(w(s)))/w_med*(n_sl/n)^2;
    om = simuleaza_arbore(Tg, dx, P, J0, n, Tmean, act*Tff, P.tau_isg, nrev);
    u2 = om(end - 3*N + 1:end);
    w_med2 = viteza_medie(u2);
    n_th = w_med2*60/(2*pi);
    d_th = (max(u2) - min(u2))/w_med2*(n_th/n)^2;
    fprintf('   %-22s Simulink %5.2f%% (%4.0f rot/min)   s05 %5.2f%% (%4.0f rot/min)\n', ...
            cazuri{j,1}, 100*d_sl, n_sl, 100*d_th, n_th);
    verifica(abs(d_sl - d_th)/d_th < 0.02 && abs(n_sl - n_th)/n_th < 0.005, sprintf('M1%c', 'a' + j - 1), ...
             sprintf('%s: Simulink = metoda pe unghi (fluctuație < 2%%, turație < 0,5%%)', cazuri{j,1}));
end
print(['-s' mdl], '-dpng', '-r150', fullfile('rezultate', 'm01_model_arbore.png'));
close_system(mdl, 0);
