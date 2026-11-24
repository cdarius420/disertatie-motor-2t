% RULEAZA_TOT  Rulează toate scripturile și scrie raportul de verificare.
% În MATLAB: deschide folderul și scrie ruleaza_tot în Command Window.
clear global VERIF; global VERIF; VERIF = [];
jurnal = fullfile('rezultate', 'jurnal.txt');
if ~exist('rezultate', 'dir'), mkdir('rezultate'); end
if exist(jurnal, 'file'), delete(jurnal); end
diary(jurnal);
fprintf('Dizertație: grup propulsor 2T hibrid, controlat mecatronic\n');
if exist('OCTAVE_VERSION', 'builtin')
    fprintf('Rulare: %s\n', datestr(now));
else
    fprintf('Rulare: %s\n', char(datetime('now')));
end
s01_cinematica; s02_toba; s03_variator; s04_masina_electrica; s05_volant_activ; s06_segmenti; s07_export_fusion; s08_tolerante; s09_piston; s10_ambielaj; s11_chiulasa; s12_echilibrare; s13_cinematica_fusion; s14_carter; s15_masina_electrica; s16_compresor; s17_racire; s18_capac;
if ~exist('OCTAVE_VERSION', 'builtin')
    m01_model_arbore;        % Simulink există doar în MATLAB
    m02_multicorp;           % Simscape Multibody: aceleași legături ca în Fusion
end
nr = numel(VERIF); ok = sum([VERIF.ok]);
fprintf('\n=== Rezumat: %d din %d verificări trecute ===\n', ok, nr);
for k = find(~[VERIF.ok])
    fprintf('  PICAT: %s %s\n', VERIF(k).cod, VERIF(k).text);
end
diary off;
