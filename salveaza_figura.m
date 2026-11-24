function salveaza_figura(f, nume)
% SALVEAZA_FIGURA  Salvează figura ca PNG în folderul rezultate.
if ~exist('rezultate', 'dir')
    mkdir('rezultate');
end
fis = fullfile('rezultate', [nume '.png']);
if exist('OCTAVE_VERSION', 'builtin')
    print(f, '-dpngcairo', '-r110', fis);
    close(f);
else
    exportgraphics(f, fis, 'Resolution', 150);
end
end
