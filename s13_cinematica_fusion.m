% S13_CINEMATICA_FUSION  Rularea cinematică a ansamblului din Fusion față de formula analitică.
% Fusion rotește arborele prin legătura lui (pasul 8 din construieste) și scrie pozițiile
% pistonului și ale bielei în fusion/cinematica_fusion.csv. Aici le compar cu cinematica.m:
% poziția, unghiul bielei și accelerația derivată numeric din pozițiile Fusion.
P = parametri();
fprintf('\n=== S13 Cinematica ansamblului din Fusion ===\n');
cale = fullfile('fusion', 'cinematica_fusion.csv');
if ~exist(cale, 'file')
    error('Lipsește %s: rulează construieste în Fusion (pasul 8 face rularea cinematică).', cale);
end
fid = fopen(cale, 'r');
fgetl(fid);
C = textscan(fid, '%f %f %f %f %f', 'Delimiter', ',');
fclose(fid);
[th, i] = sort(C{1}); x = C{2}(i)*1e-3; psi = C{3}(i);
[xa, ~, d2xa] = cinematica(th, P);
ex = max(abs(x - xa));
eb = max(abs(psi + asind(P.r/P.L*sind(th))));
h = mean(diff(th))*pi/180;                                     % pas uniform, pe o rotație întreagă
d2_num = (circshift(x, -1) - 2*x + circshift(x, 1))/h^2;
ea = max(abs(d2_num - d2xa))/max(abs(d2xa));
fprintf('Fusion: %d poziții la %.0f grade; cursa %.4f mm\n', numel(th), h*180/pi, max(x)*1e3);

f = figura_noua();
subplot(2, 1, 1); plot(th, xa*1e3, 'k-', th, x*1e3, 'r.'); grid on
ylabel('x piston [mm]'); legend('formula', 'Fusion', 'Location', 'north');
title('Rularea cinematică din Fusion (legăturile pasului 8)');
subplot(2, 1, 2); plot(th, -asind(P.r/P.L*sind(th)), 'k-', th, psi, 'r.'); grid on
xlabel('unghiul arborelui [grade]'); ylabel('rotația bielei [grade]');
salveaza_figura(f, 's13_cinematica_fusion');

verifica(ex < 1e-7, 'N1', sprintf('Pistonul din Fusion = formula în %d poziții: abatere max. %.1e mm', numel(th), ex*1e3));
verifica(eb < 1e-4, 'N2', sprintf('Rotația bielei din Fusion = -arcsin(lambda sin theta): abatere max. %.1e grade', eb));
verifica(ea < 1e-3, 'N3', sprintf('Accelerația derivată din pozițiile Fusion = analitica: abatere %.3f%% din maxim', 100*ea));
