function paths = generate_heatmaps(grid_a, grid_b, Z, labels, out_dir, fname)
%GENERATE_HEATMAPS 2D heatmap for sweep results (e.g. timing vs peak speed).
% grid_a, grid_b: vectors; Z: numel(a) x numel(b); labels: {xlabel, ylabel, title}
if nargin < 6
    fname = 'heatmap';
end
ensure_dir(out_dir);
fh = figure('Visible', 'off');
imagesc(grid_b, grid_a, Z);
set(gca, 'YDir', 'normal');
colorbar;
xlabel(labels{1});
ylabel(labels{2});
title(labels{3});
pngp = fullfile(out_dir, [fname '.png']);
saveas(fh, pngp);
paths = struct('png', pngp);
try
    savefig(fh, fullfile(out_dir, [fname '.fig']));
    paths.fig = fullfile(out_dir, [fname '.fig']);
catch
    paths.fig = '';
end
close(fh);
end
