function ok = verifica(conditie, cod, text)
% VERIFICA  Înregistrează și afișează un test: TRECUT sau PICAT.
global VERIF
ok = logical(conditie);
if ok
    stare = 'TRECUT';
else
    stare = 'PICAT ';
end
fprintf('  [%s] %-6s %s\n', stare, cod, text);
if isempty(VERIF)
    VERIF = struct('cod', {}, 'text', {}, 'ok', {});
end
VERIF(end+1) = struct('cod', cod, 'text', text, 'ok', ok);
end
