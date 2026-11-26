% RULEAZA_TOT  Rulează toate scripturile și scrie raportul de verificare.
% În MATLAB: deschide folderul și scrie ruleaza_tot în Command Window.
clear global VERIF; global VERIF; VERIF = [];
jurnal = fullfile('rezultate', 'jurnal.txt');
if ~exist('rezultate', 'dir'), mkdir('rezultate'); end
RT_fid = fopen(jurnal, 'w', 'n', 'UTF-8');   % jurnalul se scrie direct: diary rămâne gol când MATLAB e rulat din alt program
RT_scr = {'s01_cinematica', 's02_toba', 's03_variator', 's04_masina_electrica', 's05_volant_activ', 's06_segmenti', ...
          's07_export_fusion', 's08_tolerante', 's09_piston', 's10_ambielaj', 's11_chiulasa', 's12_echilibrare', ...
          's13_cinematica_fusion', 's14_carter', 's15_masina_electrica', 's16_compresor', 's17_racire', 's18_capac', 's19_vehicul', 's20_bilant_electric', 's21_sensibilitate'};
if ~exist('OCTAVE_VERSION', 'builtin')
    RT_scr = [RT_scr, {'s23_bilant_volum', 'm01_model_arbore', 'm02_multicorp'}];   % polyshape, Simulink și Simscape există doar în MATLAB
end
RT_txt = sprintf('Dizertație: grup propulsor 2T hibrid, controlat mecatronic\nRulare: %s\n', datestr(now));
fprintf('%s', RT_txt); fprintf(RT_fid, '%s', RT_txt);
for RT_k = 1:numel(RT_scr)
    RT_txt = evalc(RT_scr{RT_k});
    fprintf('%s', RT_txt); fprintf(RT_fid, '%s', RT_txt);
end
nr = numel(VERIF); ok = sum([VERIF.ok]);
RT_txt = sprintf('\n=== Rezumat: %d din %d verificări trecute ===\n', ok, nr);
for k = find(~[VERIF.ok])
    RT_txt = [RT_txt, sprintf('  PICAT: %s %s\n', VERIF(k).cod, VERIF(k).text)]; %#ok<AGROW>
end
fprintf('%s', RT_txt); fprintf(RT_fid, '%s', RT_txt); fclose(RT_fid);
