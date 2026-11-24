% M02_MULTICORP  Modelul multicorp (Simscape Multibody) al mecanismului bielă-manivelă.
% Aceleași legături ca în Fusion (pasul 8): arborele se rotește față de cilindru, biela pe
% maneton, pistonul pe bolțul bielei, pistonul alunecă în cilindru pe Z. Masele, centrele de
% masă și inerțiile vin din Fusion (fusion/inertii_fusion.csv), geometria din STEP-urile
% scrise de Fusion (fusion/multicorp). Segmenții (s12) se adaugă la masa pistonului.
%
% Rularea: arborele are mișcarea impusă, turație constantă la limitator, o rotație, fără
% gaze și fără gravitație. Verific:
%   M2a  poziția pistonului = formula bielă-manivelă;
%   M2b  accelerația pistonului = formula;
%   M2c  forța totală a lumii pe mecanism (lagărul arborelui + cilindrul) = suma m*a,
%        calculată analitic cu aceleași mase (dinamica și convențiile de semn);
%   M2d  forța transversală rămasă = BF * m_rec * r * omega^2 din s12 (echilibrarea).
% Modelul rămâne salvat (model_multicorp.slx): deschis și rulat, arată mecanismul animat.
P = parametri();
E = echilibrare(P);
fprintf('\n=== M02 Modelul multicorp (Simscape Multibody) ===\n');
cale = fullfile('fusion', 'inertii_fusion.csv');
if ~exist(cale, 'file')
    error('Lipsește %s: rulează construieste în Fusion (pasul 8 scrie masele și STEP-urile).', cale);
end
fid = fopen(cale, 'r'); fgetl(fid);
C = textscan(fid, ['%s' repmat(' %f', 1, 10)], 'Delimiter', ',');
fclose(fid);
for k = 1:numel(C{1})
    I.(C{1}{k}) = struct('m', C{2}(k), 'G', [C{3}(k) C{4}(k) C{5}(k)], ...
                         'J', [C{6}(k) C{7}(k) C{8}(k)], 'Jp', [C{9}(k) C{10}(k) C{11}(k)]);
end
I.piston.m = I.piston.m + E.m_seg;                     % segmenții se mișcă odată cu pistonul
step = @(n) fullfile(pwd, 'fusion', 'multicorp', [n '.step']);

w = 2*pi*P.n_max/60; T = 2*pi/w;
mdl = 'model_multicorp';
if bdIsLoaded(mdl), close_system(mdl, 0); end
if exist([mdl '.slx'], 'file'), delete([mdl '.slx']); end
new_system(mdl);
blk = @(n) [mdl '/' n];
nou = @(lib, n, poz) add_block(lib, blk(n), 'Position', poz);
port = @(n, tip, k) subsref(get_param(blk(n), 'PortHandles'), struct('type', {'.', '()'}, 'subs', {tip, {k}}));
leaga = @(a, b) add_line(mdl, a, b, 'autorouting', 'on');
cadru = @(x, y) [x y x+60 y+40];

% Lumea, configurația, solverul
nou('sm_lib/Frames and Transforms/World Frame', 'Lume', cadru(20, 200));
nou('sm_lib/Utilities/Mechanism Configuration', 'Configuratie', cadru(20, 300));
set_param(blk('Configuratie'), 'UniformGravity', 'None');
nou('nesl_utility/Solver Configuration', 'Solver', cadru(20, 400));
leaga(port('Lume', 'RConn', 1), port('Configuratie', 'RConn', 1));
leaga(port('Lume', 'RConn', 1), port('Solver', 'RConn', 1));

% Corpurile: piese fixe (doar imagine) și piese mobile (inerția din Fusion)
fixe = {'10_Cilindru', '15_Chiulasa', '50_Carter_stanga', '51_Carter_dreapta', '60_Stator'};
for k = 1:numel(fixe)
    n = fixe(k);
    b = strrep(n{1}(4:end), '_', '');
    nou('sm_lib/Body Elements/File Solid', b, cadru(140, 60 + 80*(k - 1)));
    set_param(blk(b), 'ExtGeomFileName', step(n{1}), 'UnitType', 'FromFile', 'InertiaType', 'Custom', ...
        'Mass', '1', 'CenterOfMass', '[0 0 0]', 'MomentsOfInertia', '[1 1 1]*1e-3', 'ProductsOfInertia', '[0 0 0]');
    vis = get_param(blk(b), 'DialogParameters').GraphicVisPropType.Enum;
    set_param(blk(b), 'GraphicVisPropType', vis{end}, 'GraphicOpacity', '0.25');   % piesele fixe, transparente
    leaga(port('Lume', 'RConn', 1), port(b, 'RConn', 1));
end
mobile = {'Arbore', '40_Arbore', 'arbore', 600; 'Biela', '30_Biela', 'biela', 900; 'Piston', '20_Piston', 'piston', 1200};
for k = 1:size(mobile, 1)
    c = I.(mobile{k,3});
    nou('sm_lib/Body Elements/File Solid', mobile{k,1}, cadru(mobile{k,4}, 60));
    set_param(blk(mobile{k,1}), 'ExtGeomFileName', step(mobile{k,2}), 'UnitType', 'FromFile', 'InertiaType', 'Custom', ...
        'Mass', num2str(c.m, 12), 'MassUnits', 'kg', 'CenterOfMass', mat2str(c.G, 12), 'CenterOfMassUnits', 'm', ...
        'MomentsOfInertia', mat2str(c.J, 12), 'ProductsOfInertia', mat2str(c.Jp, 12), ...
        'MomentsOfInertiaUnits', 'kg*m^2', 'ProductsOfInertiaUnits', 'kg*m^2');
end

% Rotorul mașinii electrice e prins de arbore (conul și pana): același cadru de referință
c = I.rotor;
nou('sm_lib/Body Elements/File Solid', 'Rotor', cadru(600, 140));
set_param(blk('Rotor'), 'ExtGeomFileName', step('61_Rotor'), 'UnitType', 'FromFile', 'InertiaType', 'Custom', ...
    'Mass', num2str(c.m, 12), 'MassUnits', 'kg', 'CenterOfMass', mat2str(c.G, 12), 'CenterOfMassUnits', 'm', ...
    'MomentsOfInertia', mat2str(c.J, 12), 'ProductsOfInertia', mat2str(c.Jp, 12), ...
    'MomentsOfInertiaUnits', 'kg*m^2', 'ProductsOfInertiaUnits', 'kg*m^2');
leaga(port('Rotor', 'RConn', 1), port('Arbore', 'RConn', 1));

% Cadrele articulațiilor: rotite cu -90 grade în jurul lui X, ca axa Z a articulației să fie Y
% (axa arborelui); toate corpurile au cadrul de referință în originea de la PMI.
rot = {'RotationMethod', 'StandardAxis', 'RotationStandardAxis', '+X', 'RotationAngle', '-90', 'RotationAngleUnits', 'deg'};
cadre = {'C_lume_arbore', 'Lume', 0, 400; 'C_arbore', 'Arbore', 0, 520;
         'C_arbore_maneton', 'Arbore', P.r, 640; 'C_biela_maneton', 'Biela', P.r, 760;
         'C_biela_bolt', 'Biela', P.r + P.L, 880; 'C_piston_bolt', 'Piston', P.r + P.L, 1000};
for k = 1:size(cadre, 1)
    nou('sm_lib/Frames and Transforms/Rigid Transform', cadre{k,1}, cadru(cadre{k,4}, 220));
    set_param(blk(cadre{k,1}), rot{:}, 'TranslationMethod', 'Cartesian', ...
              'TranslationCartesianOffset', mat2str([0 0 cadre{k,3}], 12), 'TranslationCartesianOffsetUnits', 'm');
    leaga(port(cadre{k,2}, 'RConn', 1), port(cadre{k,1}, 'LConn', 1));
end

% Articulațiile, ca în Fusion
art = {'Arbore_cilindru', 'C_lume_arbore', 'C_arbore', 480; 'Biela_maneton', 'C_arbore_maneton', 'C_biela_maneton', 700;
       'Biela_bolt', 'C_biela_bolt', 'C_piston_bolt', 940};
for k = 1:size(art, 1)
    nou('sm_lib/Joints/Revolute Joint', art{k,1}, cadru(art{k,4}, 340));
    leaga(port(art{k,2}, 'RConn', 1), port(art{k,1}, 'LConn', 1));
    leaga(port(art{k,1}, 'RConn', 1), port(art{k,3}, 'RConn', 1));
end
set_param(blk('Arbore_cilindru'), 'MotionActuationMode', 'InputMotion', 'TorqueActuationMode', 'ComputedTorque', ...
          'SenseTotalForce', 'on', 'CompositeWrenchDir', 'BaseOnFollower', 'CompositeWrenchFrame', 'BaseFrame');
nou('sm_lib/Joints/Prismatic Joint', 'Piston_cilindru', cadru(1200, 340));
set_param(blk('Piston_cilindru'), 'SensePosition', 'on', 'SenseAcceleration', 'on', 'SenseTotalForce', 'on', ...
          'CompositeWrenchDir', 'BaseOnFollower', 'CompositeWrenchFrame', 'BaseFrame');
leaga(port('Lume', 'RConn', 1), port('Piston_cilindru', 'LConn', 1));
leaga(port('Piston_cilindru', 'RConn', 1), port('Piston', 'RConn', 1));

% Mișcarea impusă: theta = omega*t, cu derivatele date exact
nou('simulink/Sources/Ramp', 'theta', cadru(200, 520));
set_param(blk('theta'), 'slope', num2str(w, 12), 'start', '0', 'InitialOutput', '0');
nou('simulink/Sources/Constant', 'omega', cadru(200, 580)); set_param(blk('omega'), 'Value', num2str(w, 12));
nou('simulink/Sources/Constant', 'epsilon', cadru(200, 640)); set_param(blk('epsilon'), 'Value', '0');
nou('nesl_utility/Simulink-PS Converter', 'S_PS_theta', cadru(320, 560));
set_param(blk('S_PS_theta'), 'Unit', 'rad', 'FilteringAndDerivatives', 'provide', 'UdotUserProvided', '2');
surse = {'theta', 'omega', 'epsilon'};
for k = 1:3
    leaga(port(surse{k}, 'Outport', 1), port('S_PS_theta', 'Inport', k));
end
leaga(port('S_PS_theta', 'RConn', 1), port('Arbore_cilindru', 'LConn', 2));

% Mărimile înregistrate
iesiri = {'F_arbore', 'Arbore_cilindru', 2, 'N'; 'z_piston', 'Piston_cilindru', 2, 'm';
          'a_piston', 'Piston_cilindru', 3, 'm/s^2'; 'F_piston', 'Piston_cilindru', 4, 'N'};
for k = 1:size(iesiri, 1)
    c = ['PS_S_' iesiri{k,1}];
    nou('nesl_utility/PS-Simulink Converter', c, cadru(1400, 460 + 70*k));
    set_param(blk(c), 'Unit', iesiri{k,4});
    leaga(port(iesiri{k,2}, 'RConn', iesiri{k,3}), port(c, 'LConn', 1));
    nou('simulink/Sinks/To Workspace', iesiri{k,1}, cadru(1500, 460 + 70*k));
    set_param(blk(iesiri{k,1}), 'VariableName', iesiri{k,1}, 'SaveFormat', 'Array');
    leaga(port(c, 'Outport', 1), port(iesiri{k,1}, 'Inport', 1));
end
nou('simulink/Sinks/To Workspace', 'th_sim', cadru(320, 460));
set_param(blk('th_sim'), 'VariableName', 'th_sim', 'SaveFormat', 'Array');
leaga(port('theta', 'Outport', 1), port('th_sim', 'Inport', 1));

set_param(mdl, 'Solver', 'daessc', 'RelTol', '1e-9', 'AbsTol', '1e-10', 'MaxStep', num2str(T/720, 12), ...
          'StopTime', num2str(T, 12), 'OutputOption', 'SpecifiedOutputTimes', ...
          'OutputTimes', mat2str(linspace(0, T, 181), 12), 'ReturnWorkspaceOutputs', 'on', ...
          'SimMechanicsOpenEditorOnUpdate', 'off');
out = sim(mdl);
set_param(mdl, 'SimMechanicsOpenEditorOnUpdate', 'on');   % la rularea din model se vede animația
save_system(mdl); close_system(mdl, 0);

% Comparația cu analitica
th = out.th_sim(:); thg = th*180/pi;
[x, ~, d2x] = cinematica(thg, P);
zp = out.z_piston(:); ap = out.a_piston(:);
Fa = squeeze(out.F_arbore)'; Fp = squeeze(out.F_piston)';           % semnale 3x1 salvate ca 3x1xN
F_sim = [Fa(:,1) + Fp(:,1), Fa(:,3) + Fp(:,2), -Fa(:,2) + Fp(:,3)];   % în axele lumii (x, y, z)
a_mic = [zeros(size(th)), -d2x*w^2];                                   % bolțul (x, z)
a_mare = -w^2*P.r*[sin(th), cos(th)];                                  % manetonul
Ga = I.arbore.G; d = I.biela.G(3) - P.r;
a_arbore = -w^2*[Ga(1)*cos(th) + Ga(3)*sin(th), -Ga(1)*sin(th) + Ga(3)*cos(th)];
Gr = I.rotor.G;
a_rotor = -w^2*[Gr(1)*cos(th) + Gr(3)*sin(th), -Gr(1)*sin(th) + Gr(3)*cos(th)];
F_an = I.arbore.m*a_arbore + I.rotor.m*a_rotor + I.biela.m*((1 - d/P.L)*a_mare + d/P.L*a_mic) + I.piston.m*a_mic;
e_poz = max(abs(zp + x));
e_acc = max(abs(ap + d2x*w^2))/max(abs(d2x*w^2));
e_for = max(max(abs(F_sim(:, [1 3]) - F_an)))/max(abs(F_an(:)));
F_tr = max(abs(F_sim(:,1))); F_tr_s12 = P.BF*E.m_rec*P.r*w^2;
fprintf('La %d rot/min: forța totală pe carcasă %.2f kN pe axa cilindrului, %.2f kN transversal\n', ...
        P.n_max, max(abs(F_sim(:,3)))/1e3, F_tr/1e3);

f = figura_noua();
plot(thg, F_sim(:,1)/1e3, 'b-', thg, F_sim(:,3)/1e3, 'r-', thg, F_an(:,1)/1e3, 'b.', thg, F_an(:,2)/1e3, 'r.'); grid on
xlabel('unghiul arborelui [grade]'); ylabel('forța pe carcasă [kN]');
legend('transversal (Simscape)', 'pe axa cilindrului (Simscape)', 'transversal (analitic)', 'pe axa (analitic)', 'Location', 'best');
title(sprintf('Forțele de inerție la %d rot/min, factor de echilibrare %.2f', P.n_max, P.BF));
salveaza_figura(f, 'm02_forte_inertie');

verifica(e_poz < 1e-7, 'M2a', sprintf('Simscape: poziția pistonului = formula (abatere max. %.1e mm)', e_poz*1e3));
verifica(e_acc < 1e-4, 'M2b', sprintf('Simscape: accelerația pistonului = formula (abatere %.1e din maxim)', e_acc));
verifica(e_for < 1e-3, 'M2c', sprintf('Simscape: forța lumii pe mecanism = suma m*a cu masele din Fusion (abatere %.1e)', e_for));
verifica(abs(F_tr - F_tr_s12) < 0.01*F_tr_s12, 'M2d', sprintf( ...
         'Forța transversală din Simscape %.3f kN = BF*m_rec*r*omega^2 din s12 %.3f kN (în 1%%)', F_tr/1e3, F_tr_s12/1e3));
