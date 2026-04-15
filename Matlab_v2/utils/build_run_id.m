function id = build_run_id(prefix)
%BUILD_RUN_ID Short unique run id for output folders.
if nargin < 1
    prefix = 'run';
end
t = char(datetime('now', 'Format', 'yyyyMMdd_HHmmss'));
r = randi(1e6 - 1);
id = sprintf('%s_%s_%06d', prefix, t, r);
end
