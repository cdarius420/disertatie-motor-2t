function v = evalueaza_fusion(nume, expr)
% EVALUEAZA_FUSION  Calculează în MATLAB expresiile scrise pentru Fusion.
% Fusion lucrează cu unghiuri în grade, deci sin, cos și tan sunt cele în grade.
% Lungimile sunt în mm. Fiecare parametru poate folosi parametrii de dinainte.
cos = @cosd; sin = @sind; tan = @tand; %#ok<NASGU>
PI = pi; %#ok<NASGU>                      % constanta lui Fusion
v = zeros(numel(nume), 1);
for k = 1:numel(nume)
    v(k) = eval(expr{k});
    eval([nume{k} ' = v(k);']);
end
end
