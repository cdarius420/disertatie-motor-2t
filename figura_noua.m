function f = figura_noua()
% FIGURA_NOUA  Figură vizibilă în MATLAB, ascunsă în Octave fără ecran.
if exist('OCTAVE_VERSION', 'builtin')
    graphics_toolkit('gnuplot');
    f = figure('visible', 'off');
else
    f = figure('Color', 'w');
end
end
